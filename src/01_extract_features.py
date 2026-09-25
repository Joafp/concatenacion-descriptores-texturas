"""
01_extract_features.py
=======================
Extrae embeddings de imágenes usando modelos preentrenados.

Modelos soportados (smoke test):
  - vit_b16:  google/vit-base-patch16-224  (HF transformers)
  - (más modelos se agregan después: resnet50, efficientnet_b0, swin_t, deit_s, convnext_v2_t)

Por extractor: produce en embeddings/{dataset}/{extractor}.npy con shape (N, D),
y embeddings/{dataset}/{extractor}_labels.npy con shape (N,) de class indices,
más un embeddings/{dataset}/{extractor}_classes.json con la lista de nombres de clase.
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import ViTImageProcessor, ViTModel


# ---------------- Configuración ----------------
DATASETS = {
    "DTD": {
        "path": "data/DTD/dtd/images",
        "mode": "subdirs",         # 47 clases, ~5,640 imgs
    },
    "FMD": {
        "path": "data/FMD",
        "mode": "recursive",       # 10 clases, 1,000 imgs (train+test combined)
        "image_subdir": None,
    },
    "CUReT": {
        "path": "data/CUReT",       # Columbia-Utrecht Reflectance and Texture Database
        "mode": "subdirs",         # 61 clases, ~3,000 imgs
        "notes": "Descargar de https://www.robots.ox.ac.uk/~vgg/data/datasheets/curet.html y extraer a data/CUReT/<clase>/<imagen>.png",
    },
    "Soil": {
        "path": "data/Soil",        # Soil texture dataset
        "mode": "subdirs",         # Varias clases según subdataset
        "notes": "Verificar estructura según subdataset específico (Soil_Type, Soil_Texture, etc.)",
    },
    "KTH-TIPS2-b": {
        "path": "results/confirmatory/recovery/kth/staging/KTH-TIPS2-b",
        "mode": "two_level",  # 11 classes × 4 physical samples; all 4,752 images
    },
    "GTOS-Mobile": {
        "path": "data/GTOS-Mobile_jpg",       # 31 clases, 100k imgs (post-conversion parquet→jpg)
        "mode": "subdirs",
        "max_samples_recommended": 5000,     # subsamplear para Exp 1; usar 5000 ≈ 161/clase
    },
    "VisTex": {
        "path": "data/VisTex_clean",          # 19 clases principales, 484 imgs (Reference subset)
        "mode": "subdirs",
    },
}

EXTRACTORS = {
    # --- Vision Transformers (Fase 1: ViTs) ---
    "vit_b16": {
        "type": "huggingface",
        "model_name": "google/vit-base-patch16-224",
        "embedding_dim": 768,
    },
    "swin_t": {
        "type": "huggingface",
        "model_name": "microsoft/swin-tiny-patch4-window7-224",
        "embedding_dim": 768,
    },
    "deit_s": {
        "type": "huggingface",
        "model_name": "facebook/deit-small-patch16-224",
        "embedding_dim": 384,
    },
    # --- Self-supervised ViT (DINOv2) ---
    "dinov2_small": {
        "type": "timm",
        "model_name": "vit_small_patch14_dinov2.lvd142m",
        "embedding_dim": 384,
    },
    "dinov2": {
        "type": "timm",
        "model_name": "vit_base_patch14_dinov2.lvd142m",
        "embedding_dim": 768,
    },
    "dinov2_large": {
        "type": "timm",
        "model_name": "vit_large_patch14_dinov2.lvd142m",
        "embedding_dim": 1024,
    },
    # --- CNN (Fase 2) ---
    "vgg16": {
        "type": "timm",
        "model_name": "vgg16.tv_in1k",
        "embedding_dim": 4096,
    },
    "resnet50": {
        "type": "timm",
        "model_name": "resnet50.a1_in1k",
        "embedding_dim": 2048,
    },
    "resnet101": {
        "type": "timm",
        "model_name": "resnet101.a1_in1k",
        "embedding_dim": 2048,
    },
    "densenet121": {
        "type": "timm",
        "model_name": "densenet121.tv_in1k",
        "embedding_dim": 1024,
    },
    "efficientnet_b0": {
        "type": "timm",
        "model_name": "efficientnet_b0.ra_in1k",
        "embedding_dim": 1280,
    },
    "convnext_v2_t": {
        "type": "timm",
        "model_name": "convnextv2_tiny.fcmae_ft_in22k_in1k",
        "embedding_dim": 768,
    },
    # --- 3er paradigma (Fase 3) ---
    # "vmamba_t":       {"type": "timm",        "model_name": "vmamba_tiny", "embedding_dim": 768},
    # --- Clásicos (Fase 4) ---
    "lbp": {
        "type": "classical",
        "method": "lbp_multiscale",
        "image_size": 256,
        "scales": [(8, 1), (16, 2), (24, 3)],   # (P, R)
        "embedding_dim": 54,                     # (P+2) sum = 10+18+26 = 54
    },
    "glcm": {
        "type": "classical",
        "method": "glcm",
        "image_size": 256,
        "distances": [1, 2, 3],
        "angles_deg": [0, 45, 90, 135],
        "embedding_dim": 18,                     # 3 distances × 6 properties
    },
    "gabor": {
        "type": "classical",
        "method": "gabor",
        "image_size": 256,
        "frequencies": [0.1, 0.2, 0.4, 0.8],
        "orientations_deg": [0, 30, 60, 90, 120, 150],
        "embedding_dim": 48,                     # 4 freqs × 6 orients × 2 stats
    },
    "hog": {
        "type": "classical",
        "method": "hog",
        "image_size": 128,
        "pixels_per_cell": (16, 16),
        "cells_per_block": (2, 2),
        "orientations": 9,
        "embedding_dim": 1764,                   # 7×7×36 — bloque 2×2 normalizado
    },
    "drlbp": {
        "type": "classical",
        "method": "drlbp",
        "image_size": 256,
        "P": 8,
        "R": 1,
        "n_rotations": 8,
        "embedding_dim": 80,                     # (P+2)=10 bins × 8 rotaciones = 80
    },
}

# ---------------- Utilidades ----------------

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def discover_images(dataset_dir: str, mode: str = "subdirs",
                    csv_path: str = None, image_subdir: str = None,
                    class_regex: str = None) -> tuple[list[str], list[str], list[int]]:
    """Devuelve (image_paths, class_names_sorted, labels_per_image).

    Modes:
      - "subdirs":    dataset_dir/<class>/*.jpg (e.g. DTD, HVD_glaucoma)
      - "recursive":  dataset_dir/<split>/<class>/*.jpg → clase=último dir (e.g. FMD train/test)
      - "csv":        imágenes en dataset_dir/<image_subdir>/, labels desde CSV
                      CSV debe tener columnas Image_name, Label (e.g. ocular_toxoplasmosis)
      - "filename":   clase extraída del nombre de archivo vía regex (e.g. BreaKHis embebido)
    """
    IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".ppm"}

    if mode == "subdirs":
        dataset_dir = Path(dataset_dir)
        class_names = sorted([p.name for p in dataset_dir.iterdir() if p.is_dir()])
        cls_to_idx = {c: i for i, c in enumerate(class_names)}
        paths, labels = [], []
        for cls in class_names:
            for p in sorted((dataset_dir / cls).iterdir()):
                if p.suffix.lower() in IMG_EXTS:
                    paths.append(str(p))
                    labels.append(cls_to_idx[cls])
        return paths, class_names, labels

    elif mode == "recursive":
        dataset_dir = Path(dataset_dir)
        # Encontrar todos los directorios hoja que contienen imágenes
        leaf_dirs = set()
        for p in dataset_dir.rglob("*"):
            if p.is_dir():
                # Es hoja si no tiene subdirs (o si los subdirs no tienen imágenes)
                has_img_child = any(c.suffix.lower() in IMG_EXTS for c in p.iterdir() if c.is_file())
                if has_img_child:
                    leaf_dirs.add(p)
        if not leaf_dirs:
            raise RuntimeError(f"No leaf dirs with images found under {dataset_dir}")
        # Clase = nombre del leaf dir
        class_names = sorted({p.name for p in leaf_dirs})
        cls_to_idx = {c: i for i, c in enumerate(class_names)}
        paths, labels = [], []
        for leaf in sorted(leaf_dirs):
            for p in sorted(leaf.iterdir()):
                if p.suffix.lower() in IMG_EXTS:
                    paths.append(str(p))
                    labels.append(cls_to_idx[leaf.name])
        return paths, class_names, labels

    elif mode == "two_level":
        """Estructura: dataset_dir/<class>/<sample>/*.png -> clase=parent del leaf (e.g. KTH-TIPS2)"""
        dataset_dir = Path(dataset_dir)
        leaf_dirs = set()
        for p in dataset_dir.rglob("*"):
            if p.is_dir():
                has_img_child = any(c.suffix.lower() in IMG_EXTS for c in p.iterdir() if c.is_file())
                if has_img_child:
                    leaf_dirs.add(p)
        if not leaf_dirs:
            raise RuntimeError(f"No leaf dirs with images found under {dataset_dir}")
        # Clase = parent dir del leaf
        class_names = sorted({p.parent.name for p in leaf_dirs})
        cls_to_idx = {c: i for i, c in enumerate(class_names)}
        paths, labels = [], []
        for leaf in sorted(leaf_dirs):
            for p in sorted(leaf.iterdir()):
                if p.suffix.lower() in IMG_EXTS:
                    paths.append(str(p))
                    labels.append(cls_to_idx[leaf.parent.name])
        return paths, class_names, labels

    elif mode == "csv":
        import csv as _csv
        dataset_dir = Path(dataset_dir)
        img_root = dataset_dir / image_subdir if image_subdir else dataset_dir
        # Leer CSV
        with open(csv_path) as f:
            reader = _csv.DictReader(f)
            rows = list(reader)
        # Determinar clases únicas (ordenadas)
        class_names = sorted({r["Label"] for r in rows})
        cls_to_idx = {c: i for i, c in enumerate(class_names)}
        paths, labels = [], []
        for r in rows:
            img_name = r["Image_name"]
            img_path = img_root / img_name
            if img_path.exists() and img_path.suffix.lower() in IMG_EXTS:
                paths.append(str(img_path))
                labels.append(cls_to_idx[r["Label"]])
        return paths, class_names, labels

    elif mode == "filename":
        import re
        dataset_dir = Path(dataset_dir)
        pattern = re.compile(class_regex)
        paths, raw_classes = [], []
        for p in sorted(dataset_dir.iterdir()):
            if p.suffix.lower() in IMG_EXTS and p.is_file():
                m = pattern.match(p.name)
                if m:
                    paths.append(str(p))
                    raw_classes.append(m.group("cls"))
        class_names = sorted(set(raw_classes))
        cls_to_idx = {c: i for i, c in enumerate(class_names)}
        labels = [cls_to_idx[c] for c in raw_classes]
        return paths, class_names, labels

    elif mode == "outex":
        raise RuntimeError(
            "El modo Outex heredado está deshabilitado. Use "
            "src/prepare_outex13_official.py y el manifiesto "
            "Outex13Official1360 para preservar etiquetas y split oficiales."
        )

    else:
        raise ValueError(f"Mode desconocido: {mode}")


def sample_subset(paths, labels, n: int, seed: int = 42) -> tuple[list[str], list[int]]:
    """Toma n imágenes estratificadas por clase, o todas si n >= len."""
    if n is None or n >= len(paths):
        return paths, labels
    rng = random.Random(seed)
    by_class = {}
    for p, l in zip(paths, labels):
        by_class.setdefault(l, []).append(p)
    sampled_paths = []
    sampled_labels = []
    per_class = max(1, n // len(by_class))
    for cls, cls_paths in sorted(by_class.items()):
        rng.shuffle(cls_paths)
        take = min(per_class, len(cls_paths))
        sampled_paths.extend(cls_paths[:take])
        sampled_labels.extend([cls] * take)
    rng.shuffle(sampled_paths)
    # Reasignar labels tras shuffle
    path_to_label = {p: l for p, l in zip(sampled_paths, sampled_labels)}
    sampled_labels = [path_to_label[p] for p in sampled_paths]
    return sampled_paths, sampled_labels


# ---------------- Extractores ----------------

class HuggingFaceExtractor:
    """Extractor genérico para modelos de HuggingFace (ViT, DeiT, Swin, ConvNeXt, ResNet)."""

    def __init__(self, model_name: str, device: str = "cuda"):
        self.device = device
        from transformers import AutoModel, AutoImageProcessor
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(device)
        self.model.eval()

    @torch.no_grad()
    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        all_feats = []
        n = len(image_paths)
        t0 = time.time()
        for i in range(0, n, batch_size):
            batch_paths = image_paths[i:i + batch_size]
            imgs = [Image.open(p).convert("RGB") for p in batch_paths]
            inputs = self.processor(images=imgs, return_tensors="pt").to(self.device)
            outputs = self.model(**inputs)
            # Para ViT, el [CLS] token es outputs.last_hidden_state[:, 0, :]
            # Para ConvNeXt, el modelo expone 'pooler_output' directamente
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                feats = outputs.pooler_output
            else:
                feats = outputs.last_hidden_state[:, 0, :]
            all_feats.append(feats.cpu().numpy())
            elapsed = time.time() - t0
            done = min(i + batch_size, n)
            print(f"  [HF] {done}/{n} imgs  ({elapsed:.1f}s, {done / max(elapsed, 0.01):.1f} img/s)", flush=True)
        return np.concatenate(all_feats, axis=0)


def get_extractor(name: str, device: str = "cuda"):
    cfg = EXTRACTORS[name]
    if cfg["type"] == "huggingface":
        return HuggingFaceExtractor(cfg["model_name"], device=device)
    if cfg["type"] == "timm":
        return TimmExtractor(cfg["model_name"], device=device)
    if cfg["type"] == "classical":
        return ClassicalExtractor(cfg)
    raise NotImplementedError(f"Extractor type no soportado: {cfg['type']}")


class ClassicalExtractor:
    """Extractor para descriptores clásicos de textura (LBP, GLCM, Gabor, HOG, DRLBP).

    Trabaja en grayscale. Imágenes se redimensionan a image_size antes de extraer.
    """

    def __init__(self, cfg: dict):
        from skimage.feature import local_binary_pattern, graycomatrix, graycoprops, hog
        from skimage.filters import gabor as sk_gabor
        from skimage.transform import rotate
        from skimage.util import img_as_ubyte
        self.cfg = cfg
        self.method = cfg["method"]
        self.image_size = cfg["image_size"]
        # Atributos prefijados _sk_ para evitar colisión con métodos
        self._sk_lbp = local_binary_pattern
        self._sk_graycomatrix = graycomatrix
        self._sk_graycoprops = graycoprops
        self._sk_gabor = sk_gabor
        self._sk_hog = hog
        self._sk_rotate = rotate
        self._sk_img_as_ubyte = img_as_ubyte

    def _load_gray(self, path: str) -> np.ndarray:
        from skimage.color import rgb2gray
        img = Image.open(path).convert("RGB")
        img = img.resize((self.image_size, self.image_size), Image.BILINEAR)
        gray = rgb2gray(np.array(img))
        return (gray * 255).astype(np.uint8)

    def _lbp_multiscale(self, gray: np.ndarray) -> np.ndarray:
        feats = []
        for P, R in self.cfg["scales"]:
            lbp = self._sk_lbp(gray, P=P, R=R, method="uniform")
            # bins = P+2 para uniform
            hist, _ = np.histogram(lbp, bins=P + 2, range=(0, P + 2), density=True)
            feats.append(hist)
        return np.concatenate(feats)

    def _glcm(self, gray: np.ndarray) -> np.ndarray:
        angles_rad = [np.deg2rad(a) for a in self.cfg["angles_deg"]]
        glcm = self._sk_graycomatrix(
            gray, distances=self.cfg["distances"], angles=angles_rad,
            levels=256, symmetric=True, normed=True,
        )
        props = ["contrast", "dissimilarity", "homogeneity", "energy", "correlation", "ASM"]
        feats = []
        for prop in props:
            vals = self._sk_graycoprops(glcm, prop)  # shape (n_dist, n_angles)
            feats.append(vals.mean(axis=1))  # mean over angles, keep distances
        return np.concatenate(feats)  # (n_dist * n_props,)

    def _gabor(self, gray: np.ndarray) -> np.ndarray:
        feats = []
        for freq in self.cfg["frequencies"]:
            for theta_deg in self.cfg["orientations_deg"]:
                theta = np.deg2rad(theta_deg)
                real, _ = self._sk_gabor(gray.astype(np.float64), frequency=freq, theta=theta)
                feats.append(real.mean())
                feats.append(real.std())
        return np.array(feats)

    def _hog(self, gray: np.ndarray) -> np.ndarray:
        return self._sk_hog(
            gray, orientations=self.cfg["orientations"],
            pixels_per_cell=self.cfg["pixels_per_cell"],
            cells_per_block=self.cfg["cells_per_block"],
            block_norm="L2-Hys", feature_vector=True,
        )

    def _drlbp(self, gray: np.ndarray) -> np.ndarray:
        # DRLBP: LBP rotation-invariant + concat sobre n_rotations rotaciones
        P, R = self.cfg["P"], self.cfg["R"]
        all_hists = []
        for i in range(self.cfg["n_rotations"]):
            if i == 0:
                rot = gray
            else:
                rot = self._sk_rotate(gray, angle=(360 / self.cfg["n_rotations"]) * i, preserve_range=True).astype(np.uint8)
            lbp = self._sk_lbp(rot, P=P, R=R, method="ror")
            # ror: max value = P+1 (rotationally invariant, P+1 classes... pero en realidad son P+2 en skimage)
            hist, _ = np.histogram(lbp, bins=P + 2, range=(0, P + 2), density=True)
            all_hists.append(hist)
        return np.concatenate(all_hists)

    @torch.no_grad()
    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        method_fn = {
            "lbp_multiscale": self._lbp_multiscale,
            "glcm": self._glcm,
            "gabor": self._gabor,
            "hog": self._hog,
            "drlbp": self._drlbp,
        }[self.method]

        n = len(image_paths)
        t0 = time.time()
        # Paralelizar con joblib (skimage/numpy son CPU-bound)
        from joblib import Parallel, delayed
        import os
        n_jobs = max(1, min(8, (os.cpu_count() or 4) - 1))

        def _process_one(path):
            gray = self._load_gray(path)
            return method_fn(gray)

        all_feats = Parallel(n_jobs=n_jobs, verbose=10)(
            delayed(_process_one)(p) for p in image_paths
        )
        elapsed = time.time() - t0
        print(f"  [classical/{self.method}] {n}/{n}  ({elapsed:.1f}s, {n / max(elapsed, 0.01):.1f} img/s, n_jobs={n_jobs})", flush=True)
        return np.stack(all_feats, axis=0)


class TimmExtractor:
    """Extractor para modelos de timm (ConvNeXt V2, EfficientNet, ResNet, etc.).
    Usa num_classes=0 para obtener features pre-clasificador.
    """

    def __init__(self, model_name: str, device: str = "cuda"):
        import timm
        from torchvision import transforms
        self.device = device
        self.model = timm.create_model(model_name, pretrained=True, num_classes=0).to(device)
        self.model.eval()
        # Obtener la config de preprocesamiento del modelo
        cfg = timm.data.resolve_model_data_config(self.model)
        self.transform = transforms.Compose([
            transforms.Resize(cfg["input_size"][1:]),
            transforms.CenterCrop(cfg["input_size"][1:]),
            transforms.ToTensor(),
            transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
        ])

    @torch.no_grad()
    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        all_feats = []
        n = len(image_paths)
        t0 = time.time()
        for i in range(0, n, batch_size):
            batch_paths = image_paths[i:i + batch_size]
            imgs = []
            for p in batch_paths:
                img = Image.open(p).convert("RGB")
                imgs.append(self.transform(img))
            imgs = torch.stack(imgs).to(self.device)
            feats = self.model(imgs)  # (B, D)
            all_feats.append(feats.cpu().numpy())
            elapsed = time.time() - t0
            done = min(i + batch_size, n)
            print(f"  [timm] {done}/{n} imgs  ({elapsed:.1f}s, {done / max(elapsed, 0.01):.1f} img/s)", flush=True)
        return np.concatenate(all_feats, axis=0)


# ---------------- Main ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=list(DATASETS.keys()))
    parser.add_argument("--extractor", required=True, choices=list(EXTRACTORS.keys()))
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Subsamplear el dataset (None = todos)")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--out-dir", default="embeddings")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--suffix", default="",
                        help="Sufijo para el nombre del archivo (ej. _smoke)")
    args = parser.parse_args()

    set_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # 1. Descubrir imágenes
    ds_cfg = DATASETS[args.dataset]
    print(f"Discovering images in {ds_cfg['path']} (mode={ds_cfg['mode']})...")
    image_paths, classes, image_labels = discover_images(
        dataset_dir=ds_cfg["path"],
        mode=ds_cfg["mode"],
        csv_path=ds_cfg.get("csv_path"),
        image_subdir=ds_cfg.get("image_subdir"),
        class_regex=ds_cfg.get("class_regex"),
    )

    print(f"  Found {len(image_paths)} images across {len(classes)} classes")

    # 2. Subsamplear
    if args.max_samples:
        image_paths, image_labels = sample_subset(image_paths, image_labels, args.max_samples, seed=args.seed)
        print(f"  Subsampled to {len(image_paths)} images")

    # 3. Extraer
    extractor = get_extractor(args.extractor, device=device)
    t0 = time.time()
    embeddings = extractor.extract(image_paths, batch_size=args.batch_size)
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s. Shape: {embeddings.shape}")

    # 4. Verificar
    assert not np.isnan(embeddings).any(), "NaN detectado en embeddings"
    assert not np.isinf(embeddings).any(), "Inf detectado en embeddings"
    assert embeddings.shape[0] == len(image_paths), "Shape mismatch: embeddings vs paths"
    print(f"  Verificación OK: sin NaN/Inf, shape consistente")

    # 5. Guardar
    out_dir = Path(args.out_dir) / args.dataset
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = args.suffix
    np.save(out_dir / f"{args.extractor}{suffix}.npy", embeddings)
    np.save(out_dir / f"{args.extractor}{suffix}_labels.npy", np.array(image_labels))
    with open(out_dir / f"{args.extractor}{suffix}_classes.json", "w") as f:
        json.dump(classes, f, indent=2)
    print(f"  Saved to {out_dir}/{args.extractor}{suffix}.npy")
    print(f"  Classes: {len(classes)}, Embedding dim: {embeddings.shape[1]}")


if __name__ == "__main__":
    main()
