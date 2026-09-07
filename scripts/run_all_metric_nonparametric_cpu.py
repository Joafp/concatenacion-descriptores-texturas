"""Run SCI2S ControlTest/MultipleTest for every available metric (CPU results)."""
from pathlib import Path
import subprocess
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results/confirmatory/extended_metrics/nested_fold_metrics.csv"
OUT = ROOT / "results/confirmatory/nonparametric/metrics_cpu"
JAVA = ROOT / ".tools/nonparametric"
METRICS = {
    "accuracy": "accuracy",
    "balanced_accuracy": "balanced_accuracy",
    "precision_macro": "precision_macro",
    "recall_macro": "recall_macro",
    "macro_f1": "macro_f1",
    "roc_auc_ovr_macro": "auc_roc_ovr_macro",
}
METHODS = ["gfs", "topk_individual", "full_concat", "best_individual",
           "best_homogeneous_self_supervised"]
LABELS = {
    "gfs": "GFS", "topk_individual": "Top-k", "full_concat": "Completa",
    "best_individual": "Individual", "best_homogeneous_self_supervised": "Homogenea",
}

def run_java(kind: str, csv: Path, tex: Path) -> None:
    work = JAVA / kind
    with tex.open("w", encoding="utf-8") as fh:
        subprocess.run(["java", "Friedman", str(csv)], cwd=work, stdout=fh,
                       stderr=subprocess.PIPE, text=True, check=True)

def main() -> None:
    df = pd.read_csv(SRC)
    df["dataset_label"] = df["dataset"].replace({"Outex13Official1360": "Outex"})
    for source_metric, label in METRICS.items():
        if df[source_metric].isna().any():
            raise ValueError(f"missing values in {source_metric}")
        metric_dir = OUT / label
        metric_dir.mkdir(parents=True, exist_ok=True)
        # Sensitivity: one row per dataset-classifier, averaging repetitions if present.
        sens = (df.groupby(["dataset_label", "classifier", "method"], as_index=False)[source_metric]
                  .mean().pivot(index=["dataset_label", "classifier"], columns="method", values=source_metric))
        sens = sens.reindex(columns=METHODS).reset_index()
        sens.insert(0, "Data-set", sens.pop("dataset_label") + "-" + sens.pop("classifier").str.upper())
        sens = sens.rename(columns=LABELS)
        sens_csv = metric_dir / "sensitivity_dataset_classifier.csv"
        sens.to_csv(sens_csv, index=False, float_format="%.12g")
        # Primary: mean of classifiers within each dataset.
        prim = (df.groupby(["dataset_label", "method"], as_index=False)[source_metric]
                  .mean().pivot(index="dataset_label", columns="method", values=source_metric))
        prim = prim.reindex(columns=METHODS).reset_index().rename(columns={"dataset_label": "Data-set", **LABELS})
        prim_csv = metric_dir / "primary_by_dataset.csv"
        prim.to_csv(prim_csv, index=False, float_format="%.12g")
        for scope, csv in [("primary", prim_csv), ("sensitivity", sens_csv)]:
            run_java("controlTest", csv, metric_dir / f"{scope}_controltest.tex")
            run_java("multipleTest", csv, metric_dir / f"{scope}_multipletest.tex")
        print(f"completed {label}")

if __name__ == "__main__":
    main()
