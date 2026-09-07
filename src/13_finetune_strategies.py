"""
13_finetune_strategies.py
==========================
Exp 2: Fine-tuning del mejor extractor (DINOv2) sobre los 6 datasets de texturas.
Compara 3 estrategias:
  - "full":    descongela todos los pesos, entrena todo
  - "last":    descongela solo el último bloque ViT + cabeza
  - "lora":    aplica LoRA (r=8) sobre attention layers, entrena solo adapters

Modelos soportados:
  - DINOv2 ViT-B/14 (vit_base_patch14_dinov2.lvd142m) @ 224×224
  - DINOv2 ViT-L/14 (vit_large_patch14_dinov2.lvd142m) @ 224×224

Datasets: DTD, FMD, KTH-TIPS2-b, GTOS-Mobile (5K subsample), VisTex

Output: results/tables/finetune_{model}_{strategy}_{dataset}.csv
        + results/tables/finetune_summary.csv
"""

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

warnings.filterwarnings("ignore")

TABLES_DIR = Path("results/tables")
TABLES_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "DTD": ("data/DTD/dtd/images", "subdirs"),
    "FMD": ("data/FMD", "recursive"),
    "CUReT": ("data/CUReT", "subdirs"),
    "Soil": ("data/Soil", "subdirs"),
    "VisTex": ("data/VisTex_clean", "subdirs"),
}

MODELS = {
    "dinov2": {
        "timm_name": "vit_base_patch14_dinov2.lvd142m",
        "input_size": 224,
        "embed_dim": 768,
    },
    "dinov2_large": {
        "timm_name": "vit_large_patch14_dinov2.lvd142m",
        "input_size": 224,
        "embed_dim": 1024,
    },
}

CV_SPLITS = 5
CV_SEED = 42
EPOCHS = 5
BATCH_SIZE = 4           # reducido para evitar OOM con DINOv2 224x224 en RTX 4060 8GB
LR_FULL = 1e-5
LR_LAST = 1e-5
LR_LORA = 1e-4


# ---------------- Dataset ----------------
class ImgListDS(Dataset):
    def __init__(self, paths, labels, transform):
        self.paths = paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        img = Image.open(self.paths[i]).convert("RGB")
        return self.transform(img), int(self.labels[i])


def discover_paths(dataset_name, dataset_dir, mode, max_samples=None):
    """Same logic as 01_extract_features.py"""
    sys.path.insert(0, "src")
    import importlib.util
    spec = importlib.util.spec_from_file_location("extract", "src/01_extract_features.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    paths, classes, labels = m.discover_images(
        dataset_dir=dataset_dir, mode=mode,
    )
    if max_samples and len(paths) > max_samples:
        # Stratified subsample
        from collections import defaultdict
        rng = np.random.RandomState(CV_SEED)
        by_class = defaultdict(list)
        for p, l in zip(paths, labels):
            by_class[l].append(p)
        per_class = max(1, max_samples // len(by_class))
        new_paths, new_labels = [], []
        for l, plist in by_class.items():
            rng.shuffle(plist)
            take = plist[:per_class]
            new_paths.extend(take)
            new_labels.extend([l] * len(take))
        paths, labels = new_paths, new_labels
    return paths, labels, classes


# ---------------- LoRA ----------------
class LoRAAdapter(nn.Module):
    """LoRA adapter: y = x + (B @ A) @ x, donde A: (r, in), B: (out, r)"""
    def __init__(self, in_dim, out_dim, r=8, alpha=16):
        super().__init__()
        self.A = nn.Parameter(torch.randn(r, in_dim) * 0.01)
        self.B = nn.Parameter(torch.zeros(out_dim, r))
        self.scale = alpha / r

    def forward(self, x):
        # x: (B, in_dim) for qkv projection
        delta = (x @ self.A.t()) @ self.B.t() * self.scale  # (B, out_dim)
        return delta


def apply_lora_to_vit(model, r=8, alpha=16):
    """Aplica LoRA a las proyecciones QKV del último bloque del ViT.
    Reemplaza nn.Linear con un wrapper que suma LoRA al output del lineal base.
    """
    # Buscar el último bloque (asumiendo timm ViT structure: model.blocks[-1])
    if hasattr(model, "blocks"):
        last_block = model.blocks[-1]
    else:
        raise ValueError("Modelo no tiene atributo blocks (no es ViT-like)")

    # Las qkv projections están dentro de cada block.attn
    if hasattr(last_block, "attn") and hasattr(last_block.attn, "qkv"):
        qkv = last_block.attn.qkv  # nn.Linear
        in_dim = qkv.in_features
        out_dim = qkv.out_features
        lora = LoRAAdapter(in_dim, out_dim, r=r, alpha=alpha)
        # Wrap: nueva linear con LoRA sumado
        original_linear = qkv
        class LoRALinear(nn.Module):
            def __init__(self, base, lora):
                super().__init__()
                self.base = base
                self.lora = lora
            def forward(self, x):
                return self.base(x) + self.lora(x)
        wrapped = LoRALinear(original_linear, lora)
        # Congelar base, entrenar LoRA
        for p in original_linear.parameters():
            p.requires_grad = False
        for p in lora.parameters():
            p.requires_grad = True
        last_block.attn.qkv = wrapped
        return [p for p in lora.parameters()]
    raise ValueError("No se pudo encontrar qkv en último bloque")


def freeze_all_but_last_block(model):
    """Congela todos los pesos excepto el último bloque."""
    for p in model.parameters():
        p.requires_grad = False
    if hasattr(model, "blocks"):
        for p in model.blocks[-1].parameters():
            p.requires_grad = True
    if hasattr(model, "head"):
        for p in model.head.parameters():
            p.requires_grad = True
    return [p for p in model.parameters() if p.requires_grad]


def freeze_all(model):
    for p in model.parameters():
        p.requires_grad = False
    if hasattr(model, "head"):
        for p in model.head.parameters():
            p.requires_grad = True
    return [p for p in model.parameters() if p.requires_grad]


# ---------------- Modelo wrapper ----------------
class ViTClassifier(nn.Module):
    def __init__(self, vit_model, num_classes, embed_dim):
        super().__init__()
        self.vit = vit_model
        self.head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        feats = self.vit(x)  # (B, embed_dim)
        return self.head(feats)


# ---------------- Training loop ----------------
def train_one_fold(model, train_loader, val_loader, device, epochs, lr, params):
    optimizer = torch.optim.AdamW(params, lr=lr)
    criterion = nn.CrossEntropyLoss()
    use_amp = (device == "cuda")
    scaler = torch.amp.GradScaler('cuda') if use_amp else None
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        n_batches = 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            if use_amp:
                with torch.amp.autocast('cuda', dtype=torch.bfloat16):
                    logits = model(imgs)
                    loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()
            else:
                logits = model(imgs)
                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()
            total_loss += loss.item()
            n_batches += 1
    # Eval
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs = imgs.to(device)
            if use_amp:
                with torch.amp.autocast('cuda', dtype=torch.bfloat16):
                    logits = model(imgs)
            else:
                logits = model(imgs)
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())
    f1 = f1_score(all_labels, all_preds, average="macro")
    acc = accuracy_score(all_labels, all_preds)
    return f1, acc, total_loss / max(n_batches, 1)


def run_finetune(model_name, strategy, dataset_name):
    import timm
    cfg = MODELS[model_name]
    ds_dir, ds_mode = DATASETS[dataset_name][:2]
    max_samples = DATASETS[dataset_name][2] if len(DATASETS[dataset_name]) > 2 else None

    print(f"\n=== {model_name} / {strategy} / {dataset_name} ===")
    paths, labels, classes = discover_paths(dataset_name, ds_dir, ds_mode, max_samples)
    n_classes = len(classes)
    print(f"  N={len(paths)}, n_classes={n_classes}")

    # Transforms (timm data_config)
    vit = timm.create_model(cfg["timm_name"], pretrained=True, num_classes=0)
    data_cfg = timm.data.resolve_model_data_config(vit)
    train_tf = transforms.Compose([
        transforms.Resize(data_cfg["input_size"][1:]),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.1, 0.1, 0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=data_cfg["mean"], std=data_cfg["std"]),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(data_cfg["input_size"][1:]),
        transforms.CenterCrop(data_cfg["input_size"][1:]),
        transforms.ToTensor(),
        transforms.Normalize(mean=data_cfg["mean"], std=data_cfg["std"]),
    ])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    y = np.array(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    fold_f1s, fold_accs = [], []
    t0 = time.time()

    for fold, (tr_idx, te_idx) in enumerate(skf.split(np.zeros(len(y)), y)):
        # Crear nuevo modelo para cada fold
        vit = timm.create_model(cfg["timm_name"], pretrained=True, num_classes=0)
        # Activar gradient checkpointing para ahorrar VRAM
        try:
            vit.set_grad_checkpointing(True)
        except AttributeError:
            pass
        if strategy == "full":
            params = [p for p in vit.parameters() if p.requires_grad]
            for p in params:
                p.requires_grad = True
            lr = LR_FULL
        elif strategy == "last":
            params = freeze_all_but_last_block(vit)
            lr = LR_LAST
        elif strategy == "lora":
            params = apply_lora_to_vit(vit, r=8, alpha=16)
            params += [p for p in vit.head.parameters() if p.requires_grad] if hasattr(vit, "head") else []
            lr = LR_LORA
        else:
            raise ValueError(strategy)
        # Wrap con clasificador
        model = ViTClassifier(vit, n_classes, cfg["embed_dim"]).to(device)
        # Marcar requires_grad en head
        for p in model.head.parameters():
            p.requires_grad = True
        params = list(params) + list(model.head.parameters())
        # Loaders
        tr_paths = [paths[i] for i in tr_idx]
        te_paths = [paths[i] for i in te_idx]
        tr_ds = ImgListDS(tr_paths, y[tr_idx].tolist(), train_tf)
        te_ds = ImgListDS(te_paths, y[te_idx].tolist(), val_tf)
        tr_loader = DataLoader(tr_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)
        te_loader = DataLoader(te_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
        # Train
        f1, acc, _ = train_one_fold(model, tr_loader, te_loader, device, EPOCHS, lr, params)
        fold_f1s.append(f1)
        fold_accs.append(acc)
        elapsed = time.time() - t0
        print(f"  fold {fold+1}/{CV_SPLITS}: f1={f1:.3f}, acc={acc:.3f} ({elapsed:.0f}s)", flush=True)
        # Cleanup
        del model, vit
        torch.cuda.empty_cache()

    elapsed = time.time() - t0
    return {
        "model": model_name,
        "strategy": strategy,
        "dataset": dataset_name,
        "n_samples": len(paths),
        "n_classes": n_classes,
        "mean_f1": float(np.mean(fold_f1s)),
        "std_f1": float(np.std(fold_f1s)),
        "mean_acc": float(np.mean(fold_accs)),
        "std_acc": float(np.std(fold_accs)),
        "elapsed_s": round(elapsed, 1),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["dinov2"])
    parser.add_argument("--strategies", nargs="+", default=["lora", "last", "full"])
    parser.add_argument("--datasets", nargs="+",
                        default=["DTD", "FMD", "KTH-TIPS2-b", "GTOS-Mobile", "VisTex"])
    args = parser.parse_args()

    all_results = []
    for model_name in args.models:
        for strategy in args.strategies:
            for ds_name in args.datasets:
                t0 = time.time()
                try:
                    r = run_finetune(model_name, strategy, ds_name)
                    all_results.append(r)
                    # Guardar incrementalmente
                    df = pd.DataFrame(all_results)
                    df.to_csv(TABLES_DIR / "finetune_summary.csv", index=False)
                except Exception as e:
                    print(f"  ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                print(f"  Total time so far: {(time.time()-t0):.0f}s")

    if all_results:
        df = pd.DataFrame(all_results)
        print("\n=== Summary ===")
        print(df.pivot_table(index=["dataset"], columns=["model", "strategy"], values="mean_f1").round(3))
        df.to_csv(TABLES_DIR / "finetune_summary.csv", index=False)


if __name__ == "__main__":
    main()
