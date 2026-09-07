"""
compile_results_v2.py
=====================
Compila los resultados de los 3 experimentos en una tabla final.

Lee:
  - results/tables/baseline_summary.csv       (Exp 1: linear probing)
  - results/tables/finetune_summary.csv      (Exp 2: lora + last)
  - results/tables/greedy_summary.csv        (Exp 3: GFS)

Genera:
  - results/tables/FINAL_COMPARISON.csv       (tabla pivote de los 3 experimentos)
  - paper/RESULTS_FINAL.md                    (reporte narrativo en markdown)
"""

from pathlib import Path
import pandas as pd
import numpy as np

TABLES = Path("results/tables")


def load_table(name):
    f = TABLES / name
    if not f.exists():
        print(f"  [WARN] {f} no existe")
        return None
    return pd.read_csv(f)


def main():
    print("=" * 70)
    print("COMPILACIÓN FINAL — 3 EXPERIMENTOS")
    print("=" * 70)

    # Load
    baseline = load_table("baseline_summary.csv")
    finetune = load_table("finetune_summary.csv")
    gfs = load_table("greedy_summary.csv")
    if gfs is not None:
        print(f"GFS columns: {list(gfs.columns)}")

    # Build pivot table: dataset x (linear, lora, last, gfs)
    rows = []
    datasets = ["DTD", "FMD", "KTH-TIPS2-b", "GTOS-Mobile", "VisTex"]

    for ds in datasets:
        row = {"dataset": ds}

        # Linear probing (svm)
        if baseline is not None:
            sub = baseline[(baseline["dataset"] == ds) & (baseline["clf"] == "svm")]
            if len(sub) > 0:
                best_idx = sub["mean_f1"].idxmax()
                row["linear_best_extractor"] = sub.loc[best_idx, "extractor"]
                row["linear_F1"] = sub.loc[best_idx, "mean_f1"]
            else:
                row["linear_best_extractor"] = "n/a"
                row["linear_F1"] = None
        # LoRA
        if finetune is not None:
            sub = finetune[(finetune["dataset"] == ds) & (finetune["strategy"] == "lora")]
            if len(sub) > 0:
                row["lora_F1"] = sub["mean_f1"].iloc[0]
            else:
                row["lora_F1"] = None
        # Last
        if finetune is not None:
            sub = finetune[(finetune["dataset"] == ds) & (finetune["strategy"] == "last")]
            if len(sub) > 0:
                row["last_F1"] = sub["mean_f1"].iloc[0]
            else:
                row["last_F1"] = None
        # GFS
        if gfs is not None:
            sub = gfs[gfs["dataset"] == ds]
            if len(sub) > 0:
                best_idx = sub["f1"].idxmax()
                row["gfs_F1"] = sub.loc[best_idx, "f1"]
                # Extract the path (selected extractors)
                if "selected" in sub.columns:
                    row["gfs_subset"] = sub.loc[best_idx, "selected"][:80]
                else:
                    row["gfs_subset"] = "n/a"
            else:
                row["gfs_F1"] = None
                row["gfs_subset"] = "n/a"
        rows.append(row)

    df = pd.DataFrame(rows)
    out = TABLES / "FINAL_COMPARISON.csv"
    df.to_csv(out, index=False)
    print(f"\n[OK] {out}")
    print("\n" + "=" * 90)
    print("TABLA COMPARATIVA FINAL")
    print("=" * 90)
    print(df.to_string(index=False))

    # Hallazgos
    print("\n" + "=" * 90)
    print("HALLAZGOS PRINCIPALES")
    print("=" * 90)
    if df["linear_F1"].notna().any():
        linear_avg = df["linear_F1"].mean()
        lora_avg = df["lora_F1"].mean()
        last_avg = df["last_F1"].mean()
        gfs_avg = df["gfs_F1"].mean()
        print(f"\nF1 promedio por experimento (6 datasets):")
        print(f"  Linear probing: {linear_avg:.3f}")
        print(f"  LoRA fine-tune: {lora_avg:.3f}")
        print(f"  Last-block FT:  {last_avg:.3f}")
        print(f"  GFS concat:     {gfs_avg:.3f}")

    # Per-dataset winner
    print("\nMejor método por dataset:")
    for _, r in df.iterrows():
        methods = {
            "linear": r.get("linear_F1", 0) or 0,
            "lora": r.get("lora_F1", 0) or 0,
            "last": r.get("last_F1", 0) or 0,
            "gfs": r.get("gfs_F1", 0) or 0,
        }
        best = max(methods, key=methods.get)
        print(f"  {r['dataset']:15s} → {best:8s} ({methods[best]:.3f})")


if __name__ == "__main__":
    main()
