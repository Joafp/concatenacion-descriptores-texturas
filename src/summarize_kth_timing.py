#!/usr/bin/env python3
"""Combine extraction and classifier timings into one table per method (KTH-TIPS2-b).

Inputs, both from results/exploratory/sota_timing/kth:
``extraction_times.json``  seconds to extract each descriptor from the 4752
                           images, plus reading and decoding them once
                           (time_kth_extraction.py);
``method_runs.csv``        accuracy and training/prediction seconds of each
                           method on each split (benchmark_kth_methods.py).

Per method and classifier, averaged over the four splits:

``train``    read and decode every image once, extract every descriptor the
             method needs to be trained (Top-4 and the ensemble rank all 21
             blocks, so they extract all of them), then select and fit;
``predict``  milliseconds for one new image: read and decode it, extract only
             the descriptors the trained method uses, and classify.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "results/exploratory/sota_timing/kth"
LIBRARY = ["beitv2_base_final", "convnext_v2_t", "deit_s", "densenet121", "dinov2",
           "dinov2_large", "dinov2_small", "drlbp", "efficientnet_b0", "eva02_base", "gabor",
           "glcm", "hog", "lbp", "mae_base", "resnet101", "resnet50", "siglip_base", "swin_t",
           "vgg16", "vit_b16"]
TRAINING_BLOCKS = {"scabini": ["beitv2_scabini"], "neshov": ["beitv2_base_multilayer"],
                   "top4": LIBRARY, "diversidad": LIBRARY,
                   "completa22": LIBRARY + ["rgb_ngram_counts"]}
LABEL = {"scabini": "Scabini 2025", "neshov": "Neshov 2025", "top4": "Top-4",
         "diversidad": "Ens. diversidad", "completa22": "Completa-22"}


def main() -> None:
    ext = json.loads((ROOT / "extraction_times.json").read_text(encoding="utf-8"))
    images = ext["_images"]["images"]
    io_s = ext["_images"]["read_seconds"] + ext["_images"]["decode_seconds"]
    runs = pd.read_csv(ROOT / "method_runs.csv")
    test_images = 1188

    rows = []
    for (method, clf), g in runs.groupby(["method", "classifier"], sort=False):
        extract_train = sum(ext[b]["extract_seconds"] for b in TRAINING_BLOCKS[method])
        per_image = [1000 * io_s / images
                     + sum(ext[b]["ms_per_image"] for b in blocks.split("+"))
                     + 1000 * p / test_images
                     for blocks, p in zip(g.blocks, g.predict_seconds)]
        rows.append({
            "method": method, "classifier": clf, "accuracy": g.accuracy.mean(),
            "macro_f1": g.macro_f1.mean(),
            "blocks_at_prediction": float(np.mean([len(b.split("+")) for b in g.blocks])),
            "read_decode_s": io_s, "extract_train_s": extract_train,
            "select_s": g.selection_seconds.mean(), "fit_s": g.fit_seconds.mean(),
            "train_total_s": io_s + extract_train + g.train_seconds.mean(),
            "predict_ms_per_image": float(np.mean(per_image)),
        })
    table = pd.DataFrame(rows)
    # Scabini reports the mean accuracy of its three classifiers: the features
    # are extracted once and all three are trained and applied.
    sc = runs[runs.method.eq("scabini")]
    shared_ms = 1000 * io_s / images + ext["beitv2_scabini"]["ms_per_image"]
    table = pd.concat([table, pd.DataFrame([{
        "method": "scabini", "classifier": "media3",
        "accuracy": sc.groupby("classifier").accuracy.mean().mean(),
        "macro_f1": sc.groupby("classifier").macro_f1.mean().mean(),
        "blocks_at_prediction": 1.0, "read_decode_s": io_s,
        "extract_train_s": ext["beitv2_scabini"]["extract_seconds"], "select_s": 0.0,
        "fit_s": sc.groupby("classifier").fit_seconds.mean().sum(),
        "train_total_s": io_s + ext["beitv2_scabini"]["extract_seconds"]
                         + sc.groupby("classifier").train_seconds.mean().sum(),
        "predict_ms_per_image": shared_ms + 1000 * sc.groupby("classifier").predict_seconds
                                .mean().sum() / test_images}])],
        ignore_index=True)
    table.insert(0, "label", table.method.map(LABEL))
    table.to_csv(ROOT / "timing_table.csv", index=False)
    with pd.option_context("display.width", 200):
        print(table.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
