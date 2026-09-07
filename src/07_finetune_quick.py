"""
07_finetune_quick.py
=====================
Fine-tuning rápido (224x224) de modelos preentrenados sobre datasets específicos.

Compara linear probing vs fine-tuning parcial (último bloque + head) para:
  - DINOv2 (ViT-B/14) @ 224x224 (resize from 518)
  - ResNet-50 @ 224x224
  - ConvNeXt V2-T @ 224x224

Sobre 2 datasets: DTD (texturas, 5640 imgs) y ocular (médico, 412 imgs).

Output: results/tables/finetune_summary.csv con comparación linear vs FT.
"""

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "DTD": ("data/DTD/dtd/images", "subdirs"),
    "ocular_toxoplasmosis": ("data/medical/ocular_toxoplasmosis", "csv"),
}

# Modelos a fine-tunear
MODELS = {
    "dinov2": {"timm_name": "vit_base_patch14_dinov2.lvd142m", "input_size": 224},
    "resnet50": {"timm_name": "resnet50.a1_in1k", "input_size": 224},
    "convnext_v2_t": {"timm_name": "convnextv2_tiny.fcmae_ft_in22k_in1k", "input_size": 224},
}


class ImgListDS(Dataset):
    def __init__(self, paths, labels, transform):
        self.paths = paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        img = Image.open(self.paths[i]).convert("RGB")
        return self.transform(img), self.labels[i]


def discover_paths(dataset_name):
    if dataset_name == "DTD":
        ds_dir = "data/DTD/dtd/images"
        IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
        ds = Path(ds_dir)
        classes = sorted([p.name for p in ds.iterdir() if p.is_dir()])
        cls2idx = {c: i for i, c in enumerate(classes)}
        paths, labels = [], []
        for c in classes:
            for p in sorted((ds / c).iterdir()):
                if p.suffix.lower() in IMG_EXTS:
                    paths.append(str(p))
                    labels.append(cls2idx[c])
        return paths, labels, classes
    elif dataset_name == "ocular_toxoplasmosis":
        import csv as _csv
        ds_dir = Path("data/medical/ocular_toxoplasmosis")
        img_root = ds_dir / "images"
        with open(ds_dir / "dataset_labels.csv") as f:
            rows = list(_csv.DictReader(f))
        classes = sorted({r["Label"] for r in rows})
        cls2idx = {c: i for i, c in enumerate(classes)}
        paths, labels = [], []
        for r in rows:
            img_path = img_root / r["Image_name"]
            if img_path.exists():
                paths.append(str(img_path))
                labels.append(cls2idx[r["Label"]])
        return paths, labels, classes


def get_head_params(model):
    """Encuentra los parámetros de la cabeza de clasificación (compatible con varios modelos timm)."""
    for attr in ["head", "fc", "classifier"]:
        if hasattr(model, attr):
            mod = getattr(model, attr)
            if isinstance(mod, nn.Module):
                return list(mod.parameters())
    # Fallback: buscar Linear final
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear) and "head" in name.lower() or (isinstance(module, nn.Linear) and name == "fc"):
            return list(module.parameters())
    raise RuntimeError("No head found in model")


def build_model(timm_name, n_classes, device, freeze_backbone=True):
    import timm
    model = timm.create_model(timm_name, pretrained=True, num_classes=n_classes).to(device)
    if freeze_backbone:
        for p in model.parameters():
            p.requires_grad = False
        for p in get_head_params(model):
            p.requires_grad = True
        # Unfreeze last block si existe
        for attr in ["blocks", "layers", "stages"]:
            if hasattr(model, attr):
                last = getattr(model, attr)[-1]
                for p in last.parameters():
                    p.requires_grad = True
                break
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_total = sum(p.numel() for p in model.parameters())
    return model, n_trainable, n_total


def get_transforms(input_size, train=True):
    if train:
        return transforms.Compose([
            transforms.Resize((input_size, input_size)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(0.2, 0.2, 0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ])
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])


def train_eval_fold(paths, labels, n_classes, train_idx, val_idx, model_cfg, device,
                    epochs=4, batch_size=16, lr=1e-4):
    model, n_train, n_total = build_model(model_cfg["timm_name"], n_classes, device, freeze_backbone=True)

    head_params = get_head_params(model)
    head_ids = {id(p) for p in head_params}
    bb_params = [p for p in model.parameters() if p.requires_grad and id(p) not in head_ids]
    groups = []
    if bb_params: groups.append({"params": bb_params, "lr": lr})
    if head_params: groups.append({"params": head_params, "lr": lr * 10})
    optimizer = torch.optim.AdamW(groups, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss()

    train_paths = [paths[i] for i in train_idx]
    train_labels = [labels[i] for i in train_idx]
    val_paths = [paths[i] for i in val_idx]
    val_labels = [labels[i] for i in val_idx]

    input_size = model_cfg["input_size"]
    train_ds = ImgListDS(train_paths, train_labels, get_transforms(input_size, train=True))
    val_ds = ImgListDS(val_paths, val_labels, get_transforms(input_size, train=False))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    for epoch in range(epochs):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            loss = criterion(logits, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        scheduler.step()

    model.eval()
    all_preds, all_y = [], []
    with torch.no_grad():
        for x, y in val_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.append(preds)
            all_y.append(y.cpu().numpy())
    all_preds = np.concatenate(all_preds)
    all_y = np.concatenate(all_y)
    return f1_score(all_y, all_preds, average="macro"), accuracy_score(all_y, all_preds), n_train, n_total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["DTD", "ocular_toxoplasmosis"])
    parser.add_argument("--models", nargs="+", default=list(MODELS.keys()))
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}\n")

    all_results = []
    # Cargar baseline (linear probing) de las tablas existentes
    baseline = pd.read_csv(TABLES_DIR / "baseline_summary.csv") if (TABLES_DIR / "baseline_summary.csv").exists() else pd.DataFrame()

    for dataset in args.datasets:
        print(f"=== {dataset} ===")
        paths, labels, classes = discover_paths(dataset)
        n_classes = len(classes)
        print(f"  {len(paths)} imgs, {n_classes} classes")

        for model_name in args.models:
            model_cfg = MODELS[model_name]
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            f1s, accs = [], []
            n_train, n_total = 0, 0
            t0 = time.time()
            for fold, (tr, va) in enumerate(skf.split(paths, labels)):
                ft0 = time.time()
                f1, acc, nt, ntot = train_eval_fold(
                    paths, labels, n_classes, tr, va, model_cfg, device,
                    epochs=args.epochs, batch_size=args.batch_size,
                )
                f1s.append(f1)
                accs.append(acc)
                n_train, n_total = nt, ntot
                elapsed = time.time() - ft0
                print(f"    fold {fold+1}/5  f1={f1:.3f}  ({elapsed:.0f}s)", flush=True)
            elapsed = time.time() - t0
            mean_f1 = float(np.mean(f1s))
            mean_acc = float(np.mean(accs))
            std_f1 = float(np.std(f1s))
            # Comparar con linear probing baseline
            linear_f1 = None
            if not baseline.empty:
                row_b = baseline[(baseline.dataset == dataset) & (baseline.extractor == model_name) & (baseline.clf == "svm")]
                if not row_b.empty:
                    linear_f1 = float(row_b["mean_f1"].iloc[0])
            delta = (mean_f1 - linear_f1) if linear_f1 is not None else None
            row = {
                "dataset": dataset,
                "model": model_name,
                "mean_f1": mean_f1,
                "std_f1": std_f1,
                "mean_acc": mean_acc,
                "linear_f1": linear_f1,
                "delta_f1": delta,
                "n_trainable": n_train,
                "n_total_params": n_total,
                "epochs": args.epochs,
                "time_s": round(elapsed, 1),
            }
            all_results.append(row)
            if linear_f1 is not None:
                print(f"  {model_name:15s}  FT f1={mean_f1:.3f}±{std_f1:.3f}  Linear f1={linear_f1:.3f}  Δ={delta:+.3f}  ({elapsed:.0f}s)")
            else:
                print(f"  {model_name:15s}  FT f1={mean_f1:.3f}±{std_f1:.3f}  ({elapsed:.0f}s)")
        print()

    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "finetune_summary.csv", index=False)
        print("=== Summary: results/tables/finetune_summary.csv ===\n")
        for r in all_results:
            delta_str = f"  Δ={r['delta_f1']:+.3f}" if r['delta_f1'] is not None else ""
            print(f"  {r['dataset']:25s} {r['model']:15s}  FT={r['mean_f1']:.3f}  Linear={r['linear_f1']:.3f}{delta_str}")


if __name__ == "__main__":
    main()
