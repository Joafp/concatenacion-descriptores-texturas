#!/usr/bin/env python3
"""Build exact SCI2S inputs for external-test accuracy from canonical tables."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/confirmatory/nonparametric/accuracy"
METHODS = {
    "GFS": "gfs",
    "Top-k": "topk_individual",
    "Completa": "full_concat",
    "Individual": "best_individual",
    "Homogenea": "best_homogeneous_self_supervised",
}


def load_matrix() -> pd.DataFrame:
    main = pd.read_csv(ROOT / "results/confirmatory/nested_fold_results.csv")
    main_topk = pd.read_csv(ROOT / "results/confirmatory/topk_individual_control/nested_fold_results.csv")
    outex = pd.read_csv(ROOT / "results/extensions/outex13_official1360/nested_fold_results.csv")
    outex_topk = pd.read_csv(ROOT / "results/extensions/outex13_official1360/topk_individual_control/nested_fold_results.csv")
    raw = pd.concat([main, main_topk, outex, outex_topk], ignore_index=True)
    raw = raw[raw["run_mode"].eq("full")].copy()
    raw["dataset"] = raw["dataset"].replace({"Outex13Official1360": "Outex"})
    per_classifier = raw.groupby(["dataset", "classifier", "method"], sort=True)["accuracy"].mean()
    matrix = per_classifier.unstack("method")
    required = list(METHODS.values())
    if matrix[required].isna().any().any():
        raise RuntimeError("Missing canonical accuracy values")
    return matrix[required].sort_index()


def make_frame(matrix: pd.DataFrame, labels: list[str]) -> pd.DataFrame:
    data = matrix.rename(columns={value: key for key, value in METHODS.items()})
    data = data[list(METHODS)].copy()
    data.insert(0, "Data-set", labels)
    return data.reset_index(drop=True)


def validate(name: str, frame: pd.DataFrame) -> dict:
    values = frame[list(METHODS)]
    stat, p = friedmanchisquare(*(values[c].to_numpy() for c in values))
    ranks = np.vstack([rankdata(-row, method="average") for row in values.to_numpy()])
    return {
        "analysis": name,
        "n_blocks": len(values),
        "k_strategies": len(METHODS),
        "friedman_chi_square": float(stat),
        "friedman_df": len(METHODS) - 1,
        "friedman_asymptotic_p": float(p),
        "kendalls_w": float(stat / (len(values) * (len(METHODS) - 1))),
        "mean_ranks": {c: float(v) for c, v in zip(values.columns, ranks.mean(axis=0))},
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = load_matrix()
    sensitivity = make_frame(matrix, [f"{d}-{c.upper()}" for d, c in matrix.index])
    primary_matrix = matrix.groupby(level="dataset", sort=True).mean()
    primary = make_frame(primary_matrix, list(primary_matrix.index))
    primary.to_csv(OUT / "primary_by_dataset.csv", index=False, float_format="%.12f")
    sensitivity.to_csv(OUT / "sensitivity_dataset_classifier.csv", index=False, float_format="%.12f")
    record = {
        "schema": "nonparametric-analysis-validation/1",
        "metric": "external_test_accuracy",
        "higher_is_better": True,
        "strategies": list(METHODS),
        "analyses": [validate("primary_by_dataset", primary), validate("sensitivity_dataset_classifier", sensitivity)],
        "interpretation_boundary": "Primary: one independent block per dataset. Sensitivity duplicates datasets across classifiers and is descriptive only.",
    }
    (OUT / "validation.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
