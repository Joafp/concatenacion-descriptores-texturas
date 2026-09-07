"""
extract_sota_2024.py
====================
Extrae embeddings de 3 modelos SOTA 2024:
  - EVA-02 (timm, ViT-B/14 pre-entrenado con MIM)
  - MAE (transformers, ViT-B/16 pre-entrenado con masked autoencoding)
  - SigLIP (transformers, ViT-B/16 pre-entrenado con sigmoid loss)

Para 5 datasets: DTD, FMD, CUReT, Soil y VisTex.
Total: 3 × 5 = 15 archivos .npy.
"""
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import torch
import timm
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from transformers import AutoModel, AutoImageProcessor

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]
NEW_EXTRACTORS = ["eva02_base", "mae_base", "siglip_base"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 32
IMG_SIZE = 224


class ImageFolderDataset(Dataset):
    def __init__(self, paths, transform):
        self.paths = paths
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        path = self.paths[idx]
        img = Image.open(path).convert("RGB")
        return self.transform(img), idx


def discover_images_and_labels(dataset: str):
    """Encuentra todas las imágenes y sus labels para un dataset.

    Usa el labels file de un extractor existente (dinov2) como referencia
    del orden. Las imágenes se descubren por globbing y se matchean.
    """
    base = EMBEDDINGS_ROOT / dataset
    sample_ext = "dinov2"
    classes = json.load(open(base / f"{sample_ext}_classes.json"))
    labels_existing = np.load(base / f"{sample_ext}_labels.npy")
    n_expected = len(labels_existing)
    # Mapear nombre de dataset a path de data (algunos difieren)
    data_subdir = {
        "DTD": "data/DTD",
        "FMD": "data/FMD",
        "CUReT": "data/CUReT",
        "Soil": "data/Soil",
        "VisTex": "data/VisTex_clean",
    }.get(dataset, f"data/{dataset}")
    # Glob todas las imágenes del dataset
    all_imgs = []
    for ext_img in ["jpg", "jpeg", "png", "bmp", "ppm", "tif", "JPG", "JPEG", "PNG"]:
        all_imgs.extend(sorted(Path(data_subdir).glob(f"**/*.{ext_img}")))

    def _resolve(p):
        s = str(p)
        return s if os.path.isabs(s) else os.path.abspath(s)

    # Quitar duplicados manteniendo orden
    seen = set()
    unique_imgs = []
    for p in all_imgs:
        s = _resolve(p)
        if s not in seen:
            seen.add(s)
            unique_imgs.append(p)
    all_imgs = unique_imgs
    # Para cada path, inferir label del nombre del directorio padre
    img_label_pairs = []
    for p in all_imgs:
        label = p.parent.name
        img_label_pairs.append((str(p), label))
    by_label = {}
    for path, label in img_label_pairs:
        by_label.setdefault(label, []).append(path)
    for k in by_label:
        by_label[k].sort()
    if sum(len(v) for v in by_label.values()) != n_expected:
        print(f"  WARN {dataset}: imágenes={sum(len(v) for v in by_label.values())} vs expected={n_expected}")
    img_paths = []
    labels = []
    for lbl_idx in labels_existing:
        lbl_name = classes[int(lbl_idx)]
        if lbl_name in by_label and by_label[lbl_name]:
            img_paths.append(by_label[lbl_name].pop(0))
            labels.append(lbl_name)
    return img_paths, labels, classes


def load_model_and_transform(name: str):
    """Carga modelo + preprocessing."""
    if name == "eva02_base":
        model = timm.create_model("eva02_base_patch14_224", pretrained=True, num_classes=0)
        model.eval().to(DEVICE)
        cfg = timm.data.resolve_model_data_config(model)
        transform = timm.data.create_transform(**cfg, is_training=False)
        return model, transform, "timm"

    elif name == "mae_base":
        # MAE from facebook
        model = AutoModel.from_pretrained("facebook/vit-mae-base")
        model.eval().to(DEVICE)
        processor = AutoImageProcessor.from_pretrained("facebook/vit-mae-base")
        transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=processor.image_mean, std=processor.image_std),
        ])
        return model, transform, "transformers"

    elif name == "siglip_base":
        # SigLIP es multimodal; usar solo el vision_model
        from transformers import SiglipVisionModel
        model = SiglipVisionModel.from_pretrained("google/siglip-base-patch16-224")
        model.eval().to(DEVICE)
        processor = AutoImageProcessor.from_pretrained("google/siglip-base-patch16-224")
        transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=processor.image_mean, std=processor.image_std),
        ])
        return model, transform, "transformers_vision"

    raise ValueError(name)


def extract_embeddings(model, transform, img_paths, model_kind: str):
    """Extrae embeddings usando el modelo cargado."""
    dataset = ImageFolderDataset(img_paths, transform)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
    feats = []
    with torch.no_grad():
        for batch, _ in loader:
            batch = batch.to(DEVICE)
            if model_kind == "timm":
                f = model(batch)
            elif model_kind == "transformers":
                out = model(pixel_values=batch)
                f = out.pooler_output if hasattr(out, "pooler_output") and out.pooler_output is not None else out.last_hidden_state[:, 0]
            elif model_kind == "transformers_vision":
                out = model(pixel_values=batch)
                f = out.pooler_output if out.pooler_output is not None else out.last_hidden_state[:, 0]
            feats.append(f.cpu().numpy())
    return np.concatenate(feats, axis=0)


def main():
    print(f"Extrayendo SOTA 2024 embeddings: {NEW_EXTRACTORS}")
    print(f"Para {len(DATASETS)} datasets. Device: {DEVICE}\n")

    for ext_name in NEW_EXTRACTORS:
        print(f"\n=== {ext_name} ===")
        model, transform, kind = load_model_and_transform(ext_name)
        for ds in DATASETS:
            out_emb = EMBEDDINGS_ROOT / ds / f"{ext_name}.npy"
            if out_emb.exists():
                print(f"  {ds}: ya existe, skip")
                continue
            out_labels = EMBEDDINGS_ROOT / ds / f"{ext_name}_labels.npy"
            out_classes = EMBEDDINGS_ROOT / ds / f"{ext_name}_classes.json"
            t0 = time.time()
            img_paths, labels, classes = discover_images_and_labels(ds)
            if not img_paths:
                print(f"  {ds}: sin imágenes")
                continue
            feats = extract_embeddings(model, transform, img_paths, kind)
            np.save(out_emb, feats)
            np.save(out_labels, np.array(labels))
            with open(out_classes, "w") as f:
                json.dump(classes, f)
            elapsed = time.time() - t0
            print(f"  {ds}: {feats.shape}  t={elapsed:.0f}s")


if __name__ == "__main__":
    main()
