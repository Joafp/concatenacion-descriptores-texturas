#!/usr/bin/env python3
"""Check the stored Outex13 ViT-B/16 and DeiT-S embeddings against their images.

Both blocks return the Hugging Face ``pooler_output``, ``tanh(W cls + b)``, and
the checkpoints carry no ``W`` and ``b``: they are initialised at random, so a
new extraction cannot reproduce the stored vectors.  If the stored vectors come
from the same images, ``atanh(stored)`` is an exact affine function of the CLS
token of a new extraction, with one ``W`` and ``b`` for every row.  The fit is
made twice, the second time without the rows the first one could not explain;
the rows that still do not fit are compared with every image of the dataset.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from time_extraction import DATASETS, build, image_path, read_images, stored_sha256  # noqa: E402


def unit(m):
    return m / np.linalg.norm(m, axis=1, keepdims=True)


def main() -> None:
    image_root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "data/confirmatory_sources/Outex13"
    manifest, embeddings, _ = DATASETS["Outex13Official1360"]
    with (REPO / manifest).open(newline="", encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["row_id"]))
    images, _, _ = read_images([image_path(r, image_root) for r in rows],
                               [stored_sha256(r) for r in rows])
    for name in ("vit_b16", "deit_s"):
        torch.manual_seed(42)
        model, transform, _ = build(name, "cuda")
        with torch.inference_mode():
            cls = np.concatenate([
                model(pixel_values=torch.stack([transform(Image.fromarray(im))
                                                for im in images[i:i + 32]]).cuda())
                .last_hidden_state[:, 0].float().cpu().numpy()
                for i in range(0, len(images), 32)]).astype(np.float64)
        stored = np.load(REPO / embeddings / f"{name}.npy").astype(np.float64)
        a = np.hstack([cls, np.ones((len(cls), 1))])
        keep = np.ones(len(a), bool)
        for threshold in (0.99, 0.9999):
            coef, *_ = np.linalg.lstsq(a[keep], np.arctanh(stored[keep]), rcond=None)
            rebuilt = np.tanh(a @ coef)
            cos = (unit(rebuilt) * unit(stored)).sum(1)
            keep = cos > threshold
        print(f"{name}: {keep.sum()} filas encajan (coseno mínimo {cos[keep].min():.5f}); "
              f"no encajan: {np.flatnonzero(~keep).tolist()}")
        for i in np.flatnonzero(~keep):
            sim = unit(stored[i:i + 1]) @ unit(rebuilt).T
            print(f"  fila {i}: coseno con su imagen {sim[0, i]:.3f}, "
                  f"máximo con cualquier imagen {sim.max():.3f} (fila {sim.argmax()})")
        del model
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
