#!/usr/bin/env python3
"""Combine extraction and classifier timings into one table per method and dataset.

Inputs, all from results/exploratory/sota_timing/<dataset>:
``extraction_times.json``  seconds to extract each descriptor from every image
                           of the dataset, plus reading and decoding them once
                           (time_extraction.py; replicate_hytexnet.py adds the
                           HyTex histograms);
``method_runs.csv``        KTH-TIPS2-b only: the literature methods and ours on
                           each split (benchmark_kth_methods.py);
``sota_runs.csv``          the literature methods on the protocol of the papers
                           (benchmark_sota_methods.py);
``hytexnet_runs.csv``      HyTexNet (replicate_hytexnet.py).

Per method and classifier, averaged over the evaluations of the protocol:

``train``    read and decode every image once, extract every descriptor the
             method needs to be trained (Top-4 and the ensemble rank all 21
             blocks, so they extract all of them), then select and fit;
``predict``  milliseconds for one new image: read and decode it, extract only
             the descriptors the trained method uses, and classify.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SLUG = {"KTHTIPS2b": "kth", "DTD": "dtd", "FMD": "fmd", "Outex13Official1360": "outex13"}
LIBRARY = ["beitv2_base_final", "convnext_v2_t", "deit_s", "densenet121", "dinov2",
           "dinov2_large", "dinov2_small", "drlbp", "efficientnet_b0", "eva02_base", "gabor",
           "glcm", "hog", "lbp", "mae_base", "resnet101", "resnet50", "siglip_base", "swin_t",
           "vgg16", "vit_b16"]
TRAINING_BLOCKS = {"scabini": ["beitv2_scabini"], "neshov": ["beitv2_base_multilayer"],
                   "neshov_train": ["beitv2_base_multilayer"], "hytexnet": ["hytex"],
                   "top4": LIBRARY, "diversidad": LIBRARY,
                   "completa22": LIBRARY + ["rgb_ngram_counts"]}
LABEL = {"scabini": "Scabini 2025", "neshov": "Neshov 2025",
         "neshov_train": "Neshov 2025 (solo train)", "hytexnet": "HyTexNet 2026",
         "top4": "Top-4", "diversidad": "Ens. diversidad", "completa22": "Completa-22"}
# Accuracy each paper reports for the method it proposes or recommends.
PUBLISHED = {("scabini", "media3"): {"KTHTIPS2b": 0.937, "DTD": 0.791, "FMD": 0.909,
                                     "Outex13Official1360": 0.916},
             ("neshov", "mlp"): {"KTHTIPS2b": 0.968, "DTD": 0.820, "FMD": 0.967},
             ("neshov_train", "mlp"): {"DTD": 0.820},
             ("hytexnet", "mlp"): {"DTD": 0.732}}


def load_runs(root: Path) -> pd.DataFrame:
    frames = []
    for name in ("method_runs.csv", "sota_runs.csv", "hytexnet_runs.csv"):
        if (root / name).exists():
            frame = pd.read_csv(root / name, dtype={"split": str})
            if frames:  # a method already measured by an earlier file is not repeated
                seen = set(pd.concat(frames).method)
                frame = frame[~frame.method.isin(seen)]
            frames.append(frame)
    runs = pd.concat(frames, ignore_index=True)
    if "n_test" not in runs:
        runs["n_test"] = np.nan
    runs["n_test"] = runs["n_test"].fillna(1188)  # the four KTH test samples
    return runs


def summarize(dataset: str) -> pd.DataFrame:
    root = REPO / "results/exploratory/sota_timing" / SLUG[dataset]
    ext = json.loads((root / "extraction_times.json").read_text(encoding="utf-8"))
    images = ext["_images"]["images"]
    io_s = ext["_images"]["read_seconds"] + ext["_images"]["decode_seconds"]
    io_ms = 1000 * io_s / images
    runs = load_runs(root)

    rows = []
    for (method, clf), g in runs.groupby(["method", "classifier"], sort=False):
        extract_train = sum(ext[b]["extract_seconds"] for b in TRAINING_BLOCKS[method])
        per_image = [io_ms + sum(ext[b]["ms_per_image"] for b in blocks.split("+"))
                     + 1000 * p / n for blocks, p, n in zip(g.blocks, g.predict_seconds, g.n_test)]
        rows.append({
            "method": method, "classifier": clf, "runs": len(g), "accuracy": g.accuracy.mean(),
            "accuracy_sd": g.accuracy.std(), "macro_f1": g.macro_f1.mean(),
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
    by_clf = sc.groupby("classifier")
    per_split = sc.groupby("split").accuracy.mean()
    table = pd.concat([table, pd.DataFrame([{
        "method": "scabini", "classifier": "media3", "runs": sc.split.nunique(),
        "accuracy": by_clf.accuracy.mean().mean(), "accuracy_sd": per_split.std(),
        "macro_f1": by_clf.macro_f1.mean().mean(),
        "blocks_at_prediction": 1.0, "read_decode_s": io_s,
        "extract_train_s": ext["beitv2_scabini"]["extract_seconds"], "select_s": 0.0,
        "fit_s": by_clf.fit_seconds.mean().sum(),
        "train_total_s": io_s + ext["beitv2_scabini"]["extract_seconds"]
                         + by_clf.train_seconds.mean().sum(),
        "predict_ms_per_image": io_ms + ext["beitv2_scabini"]["ms_per_image"]
                                + 1000 * (sc.predict_seconds / sc.n_test).groupby(sc.classifier)
                                .mean().sum()}])],
        ignore_index=True)
    table.insert(0, "label", table.method.map(LABEL))
    # Reading through WSL dominates the light methods; this is their own cost.
    table["predict_ms_without_reading"] = table.predict_ms_per_image - io_ms
    table["published"] = [PUBLISHED.get((m, c), {}).get(dataset, np.nan)
                          for m, c in zip(table.method, table.classifier)]
    table.to_csv(root / "timing_table.csv", index=False)
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", choices=[*SLUG, "all"], default="KTHTIPS2b",
                        help="'all' also writes timing_all.csv over the datasets measured")
    args = parser.parse_args()
    root = REPO / "results/exploratory/sota_timing"
    names = ([d for d in SLUG if (root / SLUG[d] / "extraction_times.json").exists()]
             if args.dataset == "all" else [args.dataset])
    tables = [summarize(d).assign(dataset=d) for d in names]
    table = pd.concat(tables, ignore_index=True)
    if args.dataset == "all":
        table.insert(0, "dataset", table.pop("dataset"))
        table.to_csv(root / "timing_all.csv", index=False)
    with pd.option_context("display.width", 220):
        print(table.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
