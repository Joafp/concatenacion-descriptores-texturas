#!/usr/bin/env python3
"""Extract reproducible BEiTv2 feature blocks for a verified extension dataset.

Writes two aligned frozen descriptors:
  * ``beitv2_base_final``: final-layer pooled representation (768 dimensions);
  * ``beitv2_base_multilayer``: mean-pooled patch tokens from paper layers 2,
    5, 8, and 11 concatenated (3072 dimensions).

The image order and labels are copied from an already-audited embedding in the
target directory.  This is deliberate: it prevents a new extractor from
silently changing the row ordering used by the sample manifest.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path

import numpy as np
import timm
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms


MODEL_NAME = "beitv2_base_patch16_224.in1k_ft_in22k_in1k"
# Electronics labels transformer layers 1..12. Timm exposes blocks 0..11.
# Thus paper layers [2, 5, 8, 11] are timm block indices [1, 4, 7, 10].
DEFAULT_LAYERS = (1, 4, 7, 10)


class OrderedImages(Dataset):
    def __init__(self, paths: list[Path], transform):
        self.paths, self.transform = paths, transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, index):
        image = Image.open(self.paths[index]).convert("RGB")
        return self.transform(image), index


def paths_in_reference_order(data_root: Path, classes: list[str], labels: np.ndarray) -> list[Path]:
    """Reproduce the class then pathname order used for KTH extension embeddings."""
    by_class: dict[str, list[Path]] = {}
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".ppm"}
    for cls in classes:
        candidates = [p for p in (data_root / cls).rglob("*")
                      if p.is_file() and p.suffix.lower() in image_extensions]
        by_class[cls] = sorted(candidates)
    positions = {cls: 0 for cls in classes}
    paths: list[Path] = []
    for label in labels:
        cls = classes[int(label)]
        pos = positions[cls]
        if pos >= len(by_class[cls]):
            raise RuntimeError(f"missing image while aligning class {cls}")
        paths.append(by_class[cls][pos])
        positions[cls] += 1
    if any(positions[c] != len(by_class[c]) for c in classes):
        raise RuntimeError("reference labels do not cover the discovered image partition")
    return paths


def paths_from_manifest(manifest: Path, repo: Path, labels: np.ndarray) -> list[Path]:
    """Load image paths in audited row_id order, independent of directory layout."""
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda row: int(row["row_id"]))
    if [int(row["row_id"]) for row in rows] != list(range(len(labels))):
        raise RuntimeError("manifest row_id does not exactly cover reference embedding order")
    paths = []
    for row in rows:
        value = row.get("source_path") or row.get("path")
        if not value:
            raise RuntimeError("manifest requires source_path or path")
        path = Path(value)
        if not path.is_absolute():
            path = repo / path
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--embedding-root", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data-root", type=Path)
    source.add_argument("--manifest", type=Path,
                        help="audited CSV with row_id and source_path/path")
    parser.add_argument("--reference-extractor", default="dinov2")
    parser.add_argument("--layers", type=int, nargs="+", default=DEFAULT_LAYERS,
                        help="zero-based timm block indices; use 1 4 7 10 for paper layers 2 5 8 11")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--final-only", action="store_true",
                        help="write only the 768-dimensional final-layer descriptor")
    args = parser.parse_args()
    if tuple(args.layers) != tuple(sorted(set(args.layers))) or min(args.layers) < 0 or max(args.layers) > 11:
        parser.error("--layers must be unique, ascending BEiTv2 block indices from 0 through 11")

    target = args.embedding_root / args.dataset
    labels_path = target / f"{args.reference_extractor}_labels.npy"
    classes_path = target / f"{args.reference_extractor}_classes.json"
    if not labels_path.exists() or not classes_path.exists():
        raise FileNotFoundError("reference labels/classes are required to preserve manifest row order")
    labels = np.load(labels_path, allow_pickle=False)
    classes = json.loads(classes_path.read_text())
    paths = (paths_from_manifest(args.manifest, Path(__file__).resolve().parents[1], labels)
             if args.manifest is not None
             else paths_in_reference_order(args.data_root, classes, labels))
    if len(paths) != len(labels):
        raise AssertionError("path/label alignment mismatch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = timm.create_model(MODEL_NAME, pretrained=True, num_classes=0).to(device).eval()
    config = timm.data.resolve_model_data_config(model)
    transform = transforms.Compose([
        transforms.Resize(config["input_size"][1:]),
        transforms.CenterCrop(config["input_size"][1:]),
        transforms.ToTensor(),
        transforms.Normalize(mean=config["mean"], std=config["std"]),
    ])
    loader = DataLoader(OrderedImages(paths, transform), batch_size=args.batch_size,
                        shuffle=False, num_workers=args.num_workers, pin_memory=device == "cuda")
    final_chunks, multi_chunks = [], []
    began = time.time()
    with torch.inference_mode():
        for images, _ in loader:
            images = images.to(device, non_blocking=True)
            final = model(images)
            final_chunks.append(final.cpu().numpy().astype(np.float32, copy=False))
            if not args.final_only:
                # Timm returns NLC patch-token tensors with the prefix token removed.
                _, intermediate = model.forward_intermediates(
                    images, indices=args.layers, norm=True, output_fmt="NLC"
                )
                multi = torch.cat([block.mean(dim=1) for block in intermediate], dim=1)
                multi_chunks.append(multi.cpu().numpy().astype(np.float32, copy=False))
            done = sum(len(chunk) for chunk in final_chunks)
            print(f"{done}/{len(paths)} images ({done / max(time.time() - began, .01):.1f} img/s)", flush=True)
    final = np.concatenate(final_chunks)
    multi = None if args.final_only else np.concatenate(multi_chunks)
    if final.shape != (len(labels), 768):
        raise AssertionError(f"unexpected BEiTv2 final shape: {final.shape}")
    if multi is not None and multi.shape != (len(labels), 768 * len(args.layers)):
        raise AssertionError(f"unexpected BEiTv2 multilayer shape: {multi.shape}")
    if not np.isfinite(final).all() or (multi is not None and not np.isfinite(multi).all()):
        raise AssertionError("non-finite BEiTv2 feature")
    arrays = [("beitv2_base_final", final)]
    if multi is not None:
        arrays.append(("beitv2_base_multilayer", multi))
    for name, array in arrays:
        np.save(target / f"{name}.npy", array)
        np.save(target / f"{name}_labels.npy", labels)
        (target / f"{name}_classes.json").write_text(json.dumps(classes, indent=2) + "\n")
    metadata = {
        "model": MODEL_NAME, "timm_block_indices": args.layers,
        "paper_layer_numbers": [index + 1 for index in args.layers],
        "pooling": "mean over patch tokens",
        "final_dimensions": int(final.shape[1]),
        "multilayer_dimensions": None if multi is None else int(multi.shape[1]),
        "final_only": args.final_only,
        "dataset": args.dataset, "n_images": int(len(labels)),
    }
    (target / "beitv2_extension_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
