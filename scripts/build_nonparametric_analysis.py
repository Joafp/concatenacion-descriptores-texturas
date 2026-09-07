#!/usr/bin/env python3
"""Build the SCI2S nonparametric-test inputs from canonical result tables.

Two analysis units are emitted:

* primary_by_dataset.csv: one independent block per dataset, averaging the
  two pre-specified classifiers (primary analysis).
* sensitivity_dataset_classifier.csv: one block per dataset-classifier pair
  (sensitivity analysis; blocks sharing a dataset are not independent).

The script also writes a JSON validation record computed with SciPy.  The
official CONTROLTEST and MULTIPLETEST Java outputs are produced separately so
their original stdout is preserved verbatim.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "confirmatory" / "nonparametric"

SOURCES = {
    "confirmatory_summary": ROOT / "results/confirmatory/nested_summary.csv",
    "confirmatory_topk": ROOT
    / "results/confirmatory/topk_individual_control/nested_fold_results.csv",
    "outex_summary": ROOT
    / "results/extensions/outex13_official1360/nested_summary.csv",
    "outex_topk": ROOT
    / "results/extensions/outex13_official1360/topk_individual_control/nested_fold_results.csv",
}

METHODS = {
    "GFS": "gfs",
    "Top-k": "topk_individual",
    "Completa": "full_concat",
    "Individual": "best_individual",
    "Homogenea": "best_homogeneous_self_supervised",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_matrix() -> pd.DataFrame:
    summaries = pd.concat(
        [
            pd.read_csv(SOURCES["confirmatory_summary"]),
            pd.read_csv(SOURCES["outex_summary"]),
        ],
        ignore_index=True,
    )
    summaries["dataset"] = summaries["dataset"].replace(
        {"Outex13Official1360": "Outex"}
    )

    topk = pd.concat(
        [
            pd.read_csv(SOURCES["confirmatory_topk"]),
            pd.read_csv(SOURCES["outex_topk"]),
        ],
        ignore_index=True,
    )
    topk["dataset"] = topk["dataset"].replace(
        {"Outex13Official1360": "Outex"}
    )
    topk_mean = (
        topk.groupby(["dataset", "classifier"], sort=True)["macro_f1"]
        .mean()
        .rename("topk_individual")
    )

    matrix = summaries.pivot(
        index=["dataset", "classifier"],
        columns="method",
        values="macro_f1_mean",
    ).join(topk_mean)
    required = list(METHODS.values())
    missing = [column for column in required if column not in matrix.columns]
    if missing:
        raise RuntimeError(f"Missing methods in canonical tables: {missing}")
    if matrix[required].isna().any().any():
        raise RuntimeError("The canonical matrix contains missing values")
    return matrix[required].sort_index()


def sci2s_frame(matrix: pd.DataFrame, labels: list[str]) -> pd.DataFrame:
    renamed = matrix.rename(columns={value: key for key, value in METHODS.items()})
    renamed = renamed[list(METHODS.keys())].copy()
    renamed.insert(0, "Data-set", labels)
    return renamed.reset_index(drop=True)


def validation(name: str, frame: pd.DataFrame) -> dict:
    values = frame[list(METHODS.keys())]
    statistic, p_value = friedmanchisquare(
        *(values[column].to_numpy() for column in values.columns)
    )
    ranks = np.vstack(
        [rankdata(-row, method="average") for row in values.to_numpy()]
    )
    n, k = values.shape
    kendalls_w = float(statistic / (n * (k - 1)))
    return {
        "analysis": name,
        "n_blocks": n,
        "k_strategies": k,
        "friedman_chi_square": float(statistic),
        "friedman_df": k - 1,
        "friedman_asymptotic_p": float(p_value),
        "kendalls_w": kendalls_w,
        "mean_ranks": {
            column: float(value)
            for column, value in zip(values.columns, ranks.mean(axis=0))
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = load_matrix()

    sensitivity_labels = [f"{dataset}-{classifier.upper()}" for dataset, classifier in matrix.index]
    sensitivity = sci2s_frame(matrix, sensitivity_labels)

    primary_matrix = matrix.groupby(level="dataset", sort=True).mean()
    primary = sci2s_frame(primary_matrix, list(primary_matrix.index))

    primary_path = OUT / "primary_by_dataset.csv"
    sensitivity_path = OUT / "sensitivity_dataset_classifier.csv"
    primary.to_csv(primary_path, index=False, float_format="%.12f")
    sensitivity.to_csv(sensitivity_path, index=False, float_format="%.12f")

    record = {
        "schema": "nonparametric-analysis-validation/1",
        "metric": "external_test_macro_f1",
        "higher_is_better": True,
        "strategies": list(METHODS.keys()),
        "source_sha256": {name: sha256(path) for name, path in SOURCES.items()},
        "analyses": [
            validation("primary_by_dataset", primary),
            validation("sensitivity_dataset_classifier", sensitivity),
        ],
        "interpretation_boundary": (
            "The primary analysis uses one block per dataset. The sensitivity "
            "analysis duplicates each dataset across classifiers and therefore "
            "does not satisfy between-block independence; it is descriptive only."
        ),
    }
    (OUT / "validation.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(primary.to_string(index=False))
    print()
    print(sensitivity.to_string(index=False))
    print()
    print(json.dumps(record["analyses"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
