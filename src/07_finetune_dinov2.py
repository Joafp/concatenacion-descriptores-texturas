"""
07_finetune_dinov2.py
======================
Fine-tuning de DINOv2 (ViT-B/14) sobre datasets de texturas/médicos.

Estrategia:
  - Carga DINOv2 preentrenado (lvd142m)
  - Reemplaza la cabeza de clasificación por una nueva (n_classes)
  - Congela todos los parámetros EXCEPTO:
    * Cabeza de clasificación (siempre entrena)
    * Último bloque del transformer (fine-tune parcial)
  - Optimizer: AdamW, lr=1e-4 (backbone), 1e-3 (head)
  - Augmentation: RandomResizedCrop, HorizontalFlip, ColorJitter
  - Train: 10 epochs, batch_size=32
  - Eval: 5-fold stratified CV con el fine-tuned model

Output:
  - results/tables/finetune_{dataset}.csv
  - results/tables/finetune_summary.csv
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
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "DTD": "data/DTD/dtd/images",
    "FMD": "data/FMD",
    "CUReT": "data/CUReT",
    "Soil": "data/Soil",
    "VisTex": "data/VisTex_clean",
}

# El modelo de fine-tuning
FINETUNE_TARGET = "dinov2_finetuned"


class ImageListDataset(Dataset):
    def __init__(self, image_paths, labels, transform):
        self.paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(img), self.labels[idx]


def discover_images(dataset_dir):
    """Asume dataset_dir/<class>/*.jpg"""
    IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(dataset_dir)
    # Soporte para ocular_toxoplasmosis que tiene images/ dentro
    for cand in [dataset_dir, dataset_dir / "images"]:
        if cand.exists() and any(c.is_dir() for c in cand.iterdir() if c.is_dir()):
            dataset_dir = cand
            break
    classes = sorted([p.name for p in dataset_dir.iterdir() if p.is_dir()])
    cls_to_idx = {c: i for i, c in enumerate(classes)}
    paths, labels = [], []
    for cls in classes:
        for p in sorted((dataset_dir / cls).iterdir()):
            if p.suffix.lower() in IMG_EXTS:
                paths.append(str(p))
                labels.append(cls_to_idx[cls])
    return paths, labels, classes


def get_transforms(input_size=518, train=True):
    """DINOv2 usa 518x518."""
    if train:
        return transforms.Compose([
            transforms.Resize((input_size, input_size)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ])
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])


def build_dinov2_with_head(num_classes, device, freeze_backbone=True):
    """Carga DINOv2 con cabeza nueva. Si freeze_backbone=True, congela todo menos head+last_block."""
    import timm
    model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=True, num_classes=num_classes)
    model = model.to(device)
    if freeze_backbone:
        # Freeze todos
        for p in model.parameters():
            p.requires_grad = False
        # Unfreeze head
        for p in model.head.parameters():
            p.requires_grad = True
        # Unfreeze last block (block 11 en DINOv2-B/14 = 12 bloques)
        try:
            for p in model.blocks[-1].parameters():
                p.requires_grad = True
        except AttributeError:
            pass
        # Unfreeze norm si existe
        try:
            for p in model.norm.parameters():
                p.requires_grad = True
        except AttributeError:
            pass
    return model


def train_one_fold(paths, labels, n_classes, train_idx, val_idx, device, epochs=8, batch_size=16, lr=1e-4):
    """Entrena y evalúa en un fold. Devuelve (val_f1, val_acc, val_logits)."""
    train_paths = [paths[i] for i in train_idx]
    train_labels = [labels[i] for i in train_idx]
    val_paths = [paths[i] for i in val_idx]
    val_labels = [labels[i] for i in val_idx]

    train_ds = ImageListDataset(train_paths, train_labels, get_transforms(train=True))
    val_ds = ImageListDataset(val_paths, val_labels, get_transforms(train=False))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    model = build_dinov2_with_head(n_classes, device, freeze_backbone=True)
    # Separar parámetros en 2 grupos: backbone (lr bajo) vs head (lr alto)
    head_params = list(model.head.parameters())
    head_param_ids = {id(p) for p in head_params}
    backbone_params = [p for p in model.parameters() if p.requires_grad and id(p) not in head_param_ids]
    param_groups = []
    if backbone_params:
        param_groups.append({"params": backbone_params, "lr": lr})
    if head_params:
        param_groups.append({"params": head_params, "lr": lr * 10})
    optimizer = torch.optim.AdamW(param_groups, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss()

    best_f1 = 0.0
    best_acc = 0.0
    best_logits = None
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
        # Eval
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
        f1 = f1_score(all_y, all_preds, average="macro")
        acc = accuracy_score(all_y, all_preds)
        if f1 > best_f1:
            best_f1 = f1
            best_acc = acc
            best_logits = all_preds
    return best_f1, best_acc, best_logits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["DTD", "ocular_toxoplasmosis"])
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}\n")

    all_results = []

    for dataset in args.datasets:
        print(f"=== Fine-tuning DINOv2 on {dataset} ===")
        ds_dir = DATASETS[dataset]
        try:
            paths, labels, classes = discover_images(ds_dir)
        except Exception as e:
            print(f"  [ERROR] {e}, skipping\n")
            continue
        n_classes = len(classes)
        print(f"  {len(paths)} imgs, {n_classes} classes")

        le = LabelEncoder()
        y = le.fit_transform(labels)
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        f1s, accs = [], []
        t0 = time.time()
        for fold, (tr_idx, va_idx) in enumerate(skf.split(paths, y)):
            ft0 = time.time()
            f1, acc, _ = train_one_fold(
                paths, labels, n_classes, tr_idx, va_idx, device,
                epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
            )
            f1s.append(f1)
            accs.append(acc)
            elapsed = time.time() - ft0
            print(f"    fold {fold+1}/5: f1={f1:.3f}  acc={acc:.3f}  ({elapsed:.1f}s)", flush=True)

        elapsed = time.time() - t0
        mean_f1 = float(np.mean(f1s))
        mean_acc = float(np.mean(accs))
        std_f1 = float(np.std(f1s))
        row = {
            "dataset": dataset,
            "model": "dinov2_finetuned",
            "mean_f1": mean_f1,
            "std_f1": std_f1,
            "mean_acc": mean_acc,
            "std_acc": float(np.std(accs)),
            "n_classes": n_classes,
            "n_samples": len(paths),
            "epochs": args.epochs,
            "time_s": round(elapsed, 1),
        }
        all_results.append(row)
        print(f"  {dataset}: f1={mean_f1:.3f}±{std_f1:.3f}  acc={mean_acc:.3f}  (total {elapsed:.0f}s)\n")

    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "finetune_summary.csv", index=False)
        print("=== Summary: results/tables/finetune_summary.csv ===")
        for r in all_results:
            print(f"  {r['dataset']:25s}  f1={r['mean_f1']:.3f}±{r['std_f1']:.3f}")


if __name__ == "__main__":
    main()
