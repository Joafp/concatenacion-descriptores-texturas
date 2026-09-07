"""Consolida el control top-k y lo compara de forma pareada con GFS."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
base = pd.concat(
    [
        pd.read_csv(ROOT / "results/confirmatory/nested_fold_results.csv"),
        pd.read_csv(
            ROOT
            / "results/extensions/outex13_official1360/nested_fold_results.csv"
        ),
    ],
    ignore_index=True,
)
topk = pd.concat(
    [
        pd.read_csv(
            ROOT
            / "results/confirmatory/topk_individual_control/nested_fold_results.csv"
        ),
        pd.read_csv(
            ROOT
            / "results/extensions/outex13_official1360/topk_individual_control/nested_fold_results.csv"
        ),
    ],
    ignore_index=True,
)
keys = ["dataset", "classifier", "seed", "outer_fold"]
paired = base[base["method"] == "gfs"].merge(
    topk, on=keys, suffixes=("_gfs", "_topk"), validate="one_to_one"
)
if len(paired) != 56:
    raise RuntimeError(f"expected 56 paired conditions, found {len(paired)}")
paired["delta_gfs_topk"] = paired["macro_f1_gfs"] - paired["macro_f1_topk"]
paired["dimension_delta"] = paired["dimensions_gfs"] - paired["dimensions_topk"]

summary = (
    paired.groupby(["dataset", "classifier"], as_index=False)
    .agg(
        n=("delta_gfs_topk", "size"),
        gfs_mean=("macro_f1_gfs", "mean"),
        topk_mean=("macro_f1_topk", "mean"),
        delta_mean=("delta_gfs_topk", "mean"),
        gfs_wins=("delta_gfs_topk", lambda x: int((x > 1e-12).sum())),
        ties=("delta_gfs_topk", lambda x: int((x.abs() <= 1e-12).sum())),
        topk_wins=("delta_gfs_topk", lambda x: int((x < -1e-12).sum())),
        gfs_dimensions=("dimensions_gfs", "mean"),
        topk_dimensions=("dimensions_topk", "mean"),
    )
)
out = ROOT / "results/topk_individual_control"
out.mkdir(parents=True, exist_ok=True)
paired.to_csv(out / "paired_gfs_vs_topk.csv", index=False)
summary.to_csv(out / "summary.csv", index=False)
print(summary.to_string(index=False))
