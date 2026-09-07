"""
compile_final_tables.py
=======================
Consolida TODOS los resultados de los 3 experimentos (solitarios, prefix concat, GFS)
para los 8 datasets en un solo CSV pivote, listo para el manuscrito.

Lee:
  - results/tables/perfold_*.jsonl (solitarios per-fold)
  - results/tables/perfold_concat_*.jsonl (prefix concat per-fold)
  - results/tables/perfold_greedy_*.jsonl (GFS per-fold)

Genera:
  - results/tables/FINAL_COMPARISON.csv (tabla pivote principal)
  - results/tables/FINAL_GFS_PATHS.csv (paths de GFS por dataset/clf)
  - results/tables/FINDINGS_TABLE.csv (5 hallazgos centrales)
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np


TABLES = Path("results/tables")


def load_perfold(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    datasets = ["DTD", "FMD", "KTH-TIPS2-b", "GTOS-Mobile", "VisTex", "CUReT", "Soil"]
    clfs = ["svm", "knn", "rf", "mlp", "resmlp"]

    rows = []
    for ds in datasets:
        for clf in clfs:
            # Solitarios
            for r in load_perfold(TABLES / f"perfold_{ds}.jsonl"):
                if r["clf"] != clf:
                    continue
                rows.append({
                    "dataset": ds,
                    "clf": clf,
                    "strategy": "individual",
                    "extractors": r["extractor"],
                    "n_extractors": 1,
                    "dim": None,
                    "mean_f1": float(np.mean(r["per_fold_f1"])),
                    "std_f1": float(np.std(r["per_fold_f1"])),
                    "per_fold_f1": r["per_fold_f1"],
                })
            # Prefix concat
            for r in load_perfold(TABLES / f"perfold_concat_{ds}.jsonl"):
                if r["clf"] != clf:
                    continue
                rows.append({
                    "dataset": ds,
                    "clf": clf,
                    "strategy": "prefix_concat",
                    "extractors": r.get("extractors", ""),
                    "n_extractors": r.get("k", 0),
                    "dim": None,
                    "mean_f1": float(np.mean(r["per_fold_f1"])),
                    "std_f1": float(np.std(r["per_fold_f1"])),
                    "per_fold_f1": r["per_fold_f1"],
                })
            # GFS
            for r in load_perfold(TABLES / f"perfold_greedy_{ds}.jsonl"):
                if r["clf"] != clf:
                    continue
                rows.append({
                    "dataset": ds,
                    "clf": clf,
                    "strategy": "gfs",
                    "extractors": r.get("selected", r.get("extractors", "")),
                    "n_extractors": r.get("step", 0),
                    "dim": None,
                    "mean_f1": float(np.mean(r["per_fold_f1"])),
                    "std_f1": float(np.std(r["per_fold_f1"])),
                    "per_fold_f1": r["per_fold_f1"],
                })

    if not rows:
        print("Sin datos.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "FINAL_FULL.csv", index=False)
    print(f"Guardado FINAL_FULL.csv con {len(df)} filas")

    # Tabla pivote: mejor F1 por (dataset, strategy) y clf
    best_per_group = df.loc[df.groupby(["dataset", "clf", "strategy"])["mean_f1"].idxmax()]
    pivot = best_per_group.pivot_table(
        index=["dataset", "clf"],
        columns="strategy",
        values="mean_f1",
    ).round(4)
    pivot.to_csv(TABLES / "FINAL_COMPARISON.csv")
    print("Guardado FINAL_COMPARISON.csv")
    print()
    print(pivot.to_string())

    # GFS paths (qué extractores se eligieron)
    gfs = df[df["strategy"] == "gfs"].copy()
    gfs["best_for_dataset_clf"] = gfs.groupby(["dataset", "clf"])["mean_f1"].transform("max") == gfs["mean_f1"]
    best_gfs = gfs[gfs["best_for_dataset_clf"]][["dataset", "clf", "n_extractors", "extractors", "mean_f1"]]
    best_gfs.to_csv(TABLES / "FINAL_GFS_PATHS.csv", index=False)
    print()
    print("Mejor GFS path por dataset × clf:")
    print(best_gfs.to_string(index=False))


if __name__ == "__main__":
    main()
