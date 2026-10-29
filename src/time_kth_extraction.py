#!/usr/bin/env python3
"""Time the extraction of every descriptor from the KTH-TIPS2-b images.

The thesis caches its descriptors, so the classifier timings elsewhere start
from stored embeddings.  Comparing against single-backbone methods from the
literature needs the step those caches hide: turning each image into features.
This script runs each extractor over the 4752 images in manifest order on one
machine.  The images are read from disk and decoded once, and that time is
reported on its own: every method pays it once, and reading through WSL from a
Windows drive is slow enough (about 255 images per second) to hide the cost of
the networks.  Each extractor then starts from the decoded images, with the
same pipeline for every network (batches of 32, four loader workers) and the
classical descriptors parallelised over eight processes as in
``01_extract_features.py``.  Model loading is timed apart from extraction, one
warm-up batch is excluded, and the GPU is synchronised before the clock stops.

Each extracted array is compared with the stored embedding, so the time belongs
to the descriptor the experiments used.  Two arrays have no stored copy:

``beitv2_scabini``  BEiTv2-B/16 with the ImageNet-21k weights evaluated by
                    Scabini et al. (timm ``beitv2_base_patch16_224.in1k_ft_in22k``);
                    it is saved for the method benchmark;
``rgb_ngram_counts`` the label-free RGB N-gram counts behind the colour block,
                    checked against the count cache instead.

``mae_base`` masks random patches at inference, so its stored copy cannot be
matched exactly; its similarity is reported but not required.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DEEP = {
    # name: (library, model id)
    "vit_b16": ("hf", "google/vit-base-patch16-224"),
    "swin_t": ("hf", "microsoft/swin-tiny-patch4-window7-224"),
    "deit_s": ("hf", "facebook/deit-small-patch16-224"),
    "dinov2_small": ("timm", "vit_small_patch14_dinov2.lvd142m"),
    "dinov2": ("timm", "vit_base_patch14_dinov2.lvd142m"),
    "dinov2_large": ("timm", "vit_large_patch14_dinov2.lvd142m"),
    "vgg16": ("timm", "vgg16.tv_in1k"),
    "resnet50": ("timm", "resnet50.a1_in1k"),
    "resnet101": ("timm", "resnet101.a1_in1k"),
    "densenet121": ("timm", "densenet121.tv_in1k"),
    "efficientnet_b0": ("timm", "efficientnet_b0.ra_in1k"),
    "convnext_v2_t": ("timm", "convnextv2_tiny.fcmae_ft_in22k_in1k"),
    "eva02_base": ("timm_eva", "eva02_base_patch14_224"),
    "mae_base": ("mae", "facebook/vit-mae-base"),
    "siglip_base": ("siglip", "google/siglip-base-patch16-224"),
    "beitv2_base_final": ("timm", "beitv2_base_patch16_224.in1k_ft_in22k_in1k"),
    "beitv2_base_multilayer": ("beit_multi", "beitv2_base_patch16_224.in1k_ft_in22k_in1k"),
    "beitv2_scabini": ("timm", "beitv2_base_patch16_224.in1k_ft_in22k"),
}
CLASSICAL = ("lbp", "glcm", "gabor", "hog", "drlbp")
ALL = tuple(DEEP) + CLASSICAL + ("rgb_ngram_counts",)


class Images(Dataset):
    """Decoded images held in memory, so each network is timed without the disk."""

    def __init__(self, images, transform):
        self.images, self.transform = images, transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        return self.transform(Image.fromarray(self.images[i]))


def read_images(paths):
    """Read and decode every image once; every method pays this step once."""
    import io
    t0 = time.perf_counter()
    raw = [p.read_bytes() for p in paths]
    read_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    images = [np.asarray(Image.open(io.BytesIO(b)).convert("RGB")) for b in raw]
    return images, read_s, time.perf_counter() - t0


def resize_crop(model):
    """Transform of 01_extract_features.TimmExtractor and the BEiTv2 extension."""
    import timm
    from torchvision import transforms
    cfg = timm.data.resolve_model_data_config(model)
    return transforms.Compose([
        transforms.Resize(cfg["input_size"][1:]), transforms.CenterCrop(cfg["input_size"][1:]),
        transforms.ToTensor(), transforms.Normalize(mean=cfg["mean"], std=cfg["std"])])


def build(name: str, device: str):
    """Model, per-image transform and batch function, as the original scripts define them."""
    kind, model_id = DEEP[name]
    if kind in ("timm", "timm_eva", "beit_multi"):
        import timm
        model = timm.create_model(model_id, pretrained=True, num_classes=0).to(device).eval()
        transform = (timm.data.create_transform(**timm.data.resolve_model_data_config(model),
                                                is_training=False)
                     if kind == "timm_eva" else resize_crop(model))
        if kind == "beit_multi":
            # Paper layers 2, 5, 8 and 11 in one pass, mean of the patch tokens.
            def forward(x):
                _, inter = model.forward_intermediates(x, indices=(1, 4, 7, 10), norm=True,
                                                       output_fmt="NLC")
                return torch.cat([b.mean(dim=1) for b in inter], dim=1)
        else:
            forward = model
        return model, transform, forward
    from torchvision import transforms
    from transformers import AutoImageProcessor, AutoModel
    if kind == "hf":
        processor = AutoImageProcessor.from_pretrained(model_id)
        model = AutoModel.from_pretrained(model_id).to(device).eval()
        transform = lambda img: processor(images=img, return_tensors="pt")["pixel_values"][0]
    else:
        processor = AutoImageProcessor.from_pretrained(model_id)
        if kind == "siglip":
            from transformers import SiglipVisionModel
            model = SiglipVisionModel.from_pretrained(model_id).to(device).eval()
        else:
            model = AutoModel.from_pretrained(model_id).to(device).eval()
        transform = transforms.Compose([
            transforms.Resize((224, 224)), transforms.ToTensor(),
            transforms.Normalize(mean=processor.image_mean, std=processor.image_std)])

    def forward(x):
        out = model(pixel_values=x)
        pooled = getattr(out, "pooler_output", None)
        return pooled if pooled is not None else out.last_hidden_state[:, 0]
    return model, transform, forward


def extract_deep(name, images, device, batch_size, workers):
    # 01_extract_features seeded before loading; heads absent from a checkpoint
    # (the ViT pooler) are then initialised the same way.
    torch.manual_seed(42)
    np.random.seed(42)
    t0 = time.perf_counter()
    model, transform, forward = build(name, device)
    if device == "cuda":
        torch.cuda.synchronize()
    load_s = time.perf_counter() - t0
    loader = DataLoader(Images(images, transform), batch_size=batch_size, shuffle=False,
                        num_workers=workers, pin_memory=device == "cuda",
                        persistent_workers=workers > 0)
    with torch.inference_mode():
        warm = next(iter(loader))
        forward(warm.to(device))
        if device == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        feats = [forward(batch.to(device, non_blocking=True)).float().cpu().numpy()
                 for batch in loader]
        if device == "cuda":
            torch.cuda.synchronize()
        extract_s = time.perf_counter() - t0
    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return np.concatenate(feats), load_s, extract_s


def extract_classical(name, images, jobs):
    import importlib
    from joblib import Parallel, delayed
    from skimage.color import rgb2gray
    extractor = importlib.import_module("01_extract_features")
    t0 = time.perf_counter()
    ext = extractor.ClassicalExtractor(extractor.EXTRACTORS[name])
    fn = {"lbp_multiscale": ext._lbp_multiscale, "glcm": ext._glcm, "gabor": ext._gabor,
          "hog": ext._hog, "drlbp": ext._drlbp}[ext.method]
    size = ext.image_size
    load_s = time.perf_counter() - t0

    def one(rgb):
        # ClassicalExtractor._load_gray, from the decoded image instead of the file.
        img = Image.fromarray(rgb).resize((size, size), Image.BILINEAR)
        return fn((rgb2gray(np.array(img)) * 255).astype(np.uint8))

    t0 = time.perf_counter()
    feats = Parallel(n_jobs=jobs)(delayed(one)(rgb) for rgb in images)
    return np.stack(feats), load_s, time.perf_counter() - t0


def extract_ngram_counts(images):
    from run_rgb_ngram_outex13_official import count_image
    t0 = time.perf_counter()
    keys, counts = [], []
    for rgb in images:
        k, c = count_image(np.ascontiguousarray(rgb, dtype=np.uint8), "rgb_ngram_impl1")
        keys.append(k)
        counts.append(c)
    return (keys, counts), 0.0, time.perf_counter() - t0


def verify(name, array, embedding_root, count_cache):
    if name == "rgb_ngram_counts":
        keys, counts = array
        cache = {n: np.load(count_cache / f"{n}.npy") for n in ("keys", "counts", "indptr")}
        same = (np.array_equal(np.concatenate(keys), cache["keys"])
                and np.array_equal(np.concatenate(counts), cache["counts"]))
        return {"matches_stored": bool(same)}
    stored_path = embedding_root / f"{name}.npy"
    if not stored_path.exists():
        return {"matches_stored": None}
    stored = np.load(stored_path).astype(np.float64)
    new = array.astype(np.float64)
    if stored.shape != new.shape:
        return {"matches_stored": False, "shape_stored": list(stored.shape)}
    cos = (stored * new).sum(1) / (np.linalg.norm(stored, axis=1) * np.linalg.norm(new, axis=1) + 1e-12)
    return {"matches_stored": bool(cos.min() > 0.999), "cosine_min": float(cos.min()),
            "cosine_mean": float(cos.mean()), "max_abs_diff": float(np.abs(stored - new).max())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--descriptors", nargs="+", default=list(ALL), choices=ALL)
    parser.add_argument("--manifest", type=Path,
                        default=REPO / "results/extensions/kth_tips2b/sample_manifests/KTHTIPS2b.csv")
    parser.add_argument("--embedding-root", type=Path, default=REPO / "embeddings_extensions/KTH-TIPS2-b")
    parser.add_argument("--count-cache", type=Path,
                        default=REPO / "results/extensions/kth_tips2b/rgb_ngram_count_cache/KTHTIPS2b/rgb_ngram_impl1")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--classical-jobs", type=int, default=8)
    parser.add_argument("--output", type=Path, default=REPO / "results/exploratory/sota_timing/kth")
    args = parser.parse_args()

    with args.manifest.open(newline="", encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["row_id"]))
    paths = [REPO / r["source_path"] for r in rows]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} images missing, e.g. {missing[0]}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    args.output.mkdir(parents=True, exist_ok=True)
    out_json = args.output / "extraction_times.json"
    results = json.loads(out_json.read_text()) if out_json.exists() else {}
    gpu = torch.cuda.get_device_name(0) if device == "cuda" else "cpu"

    images, read_s, decode_s = read_images(paths)
    results["_images"] = {"images": len(paths), "read_seconds": read_s, "decode_seconds": decode_s,
                          "note": "read once from disk and decoded once; shared by every method"}
    print(f"leer {read_s:.1f} s, decodificar {decode_s:.1f} s ({len(paths)} imágenes)", flush=True)

    for name in args.descriptors:
        if name in CLASSICAL:
            array, load_s, extract_s = extract_classical(name, images, args.classical_jobs)
            where = f"cpu x{args.classical_jobs}"
        elif name == "rgb_ngram_counts":
            array, load_s, extract_s = extract_ngram_counts(images)
            where = "cpu x1"
        else:
            array, load_s, extract_s = extract_deep(name, images, device, args.batch_size, args.workers)
            where = gpu
        check = verify(name, array, args.embedding_root, args.count_cache)
        if name == "beitv2_scabini":
            # Kept outside the embedding directory so the loaders never take it
            # for a block of the library.
            target = args.embedding_root.with_name(args.embedding_root.name + "_scabini")
            target.mkdir(exist_ok=True)
            np.save(target / "beitv2_scabini.npy", array.astype(np.float32))
        results[name] = {"images": len(paths), "device": where, "load_seconds": load_s,
                         "extract_seconds": extract_s,
                         "ms_per_image": 1000 * extract_s / len(paths),
                         "images_per_second": len(paths) / extract_s,
                         "dimensions": None if name == "rgb_ngram_counts" else int(array.shape[1]),
                         **check}
        out_json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        r = results[name]
        print(f"{name:<24} {r['extract_seconds']:8.1f} s  {r['images_per_second']:8.1f} img/s  "
              f"carga {r['load_seconds']:5.1f} s  coincide={r['matches_stored']}"
              + (f"  cos_min={r['cosine_min']:.5f}" if "cosine_min" in r else ""), flush=True)


if __name__ == "__main__":
    main()
