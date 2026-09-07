"""
final_summary.py
================
Genera el reporte final de los 3 experimentos:
  - Exp 1: 17 extractores × 4 clfs × 6 datasets (individual)
  - Exp 3: prefix concat k=1..17 con diff sig vs cada individual
  - Exp 4: diff sig dentro de Exp 1 (mejor extractor por dataset/clf)
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

TABLES = Path("results/tables")
DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]
EXTRACTORS = [
    "vit_b16", "swin_t", "deit_s",
    "dinov2_small", "dinov2", "dinov2_large",
    "vgg16", "resnet50", "resnet101", "densenet121",
    "efficientnet_b0", "convnext_v2_t",
    "lbp", "glcm", "gabor", "hog", "drlbp",
]
CLFS = ["svm", "knn", "rf", "resmlp"]


def section(title):
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def main():
    section("DATASETS EXPERIMENTADOS")
    for i, ds in enumerate(DATASETS, 1):
        print(f"  {i}. {ds}")

    section("EXTRACTORES PROBADOS (17)")
    print("  Clásicos (5): lbp, glcm, gabor, hog, drlbp")
    print("  CNN (6):      vgg16, resnet50, resnet101, densenet121, efficientnet_b0, convnext_v2_t")
    print("  ViT (3):      vit_b16, swin_t, deit_s")
    print("  DINOv2 (3):   dinov2_small, dinov2, dinov2_large")

    section("CLASIFICADORES (4)")
    for c in CLFS:
        print(f"  - {c}")

    section("EXPERIMENTO 1: 17 extractores individuales × 4 clfs × 6 datasets (408 corridas)")
    p = TABLES / "exp4_best_per_dataset_clf.csv"
    if p.exists():
        df = pd.read_csv(p)
        print(df.to_string(index=False))
    else:
        print("  (no ejecutado aún)")

    section("EXPERIMENTO 3: prefix concat (k=1..17) + diff sig vs cada individual (Holm-Bonferroni)")
    p = TABLES / "diff_sig_vs_individual.csv"
    if p.exists():
        df = pd.read_csv(p)
        n_total = len(df)
        n_sig05 = int(df["significant_05"].sum()) if "significant_05" in df.columns else 0
        n_sig01 = int(df["significant_01"].sum()) if "significant_01" in df.columns else 0
        n_sig001 = int(df["significant_001"].sum()) if "significant_001" in df.columns else 0
        print(f"  Total comparaciones (combination × individual): {n_total}")
        print(f"  Significativas (Holm p<0.05):  {n_sig05}")
        print(f"  Significativas (Holm p<0.01):  {n_sig01}")
        print(f"  Significativas (Holm p<0.001): {n_sig001}")
        # Top 5 combinaciones más significativas
        if n_sig001 > 0:
            top = df[df["significant_001"]].nsmallest(5, "p_value_holm")
            print("\n  Top 5 comparaciones más significativas (p<0.001):")
            for _, r in top.iterrows():
                print(f"    {r['dataset']:8s} {r['clf']:6s} k=?={r['combination_subset'][:30]:30s}  vs {r['comparison_extractor']:14s}  Δ={r['delta']:+.3f}  d={r['cohens_d']:+.2f}")
        # Resumen por dataset
        print("\n  Resumen por dataset:")
        summary = df.groupby("dataset").agg(
            n_total=("p_value", "count"),
            n_sig_05=("significant_05", "sum"),
            n_sig_001=("significant_001", "sum"),
        )
        print(summary.to_string())
    else:
        print("  (no ejecutado aún)")

    section("EXPERIMENTO 4: diff sig dentro de Exp 1 (mejor por dataset/clf vs cada individual)")
    p = TABLES / "exp4_significance_matrix.csv"
    if p.exists():
        df = pd.read_csv(p)
        n_total = len(df)
        n_sig05 = int(df["significant_05"].sum()) if "significant_05" in df.columns else 0
        n_sig001 = int(df["significant_001"].sum()) if "significant_001" in df.columns else 0
        print(f"  Total comparaciones (mejor vs 16 otros): {n_total}")
        print(f"  Significativas (Holm p<0.05):  {n_sig05}")
        print(f"  Significativas (Holm p<0.001): {n_sig001}")
    else:
        print("  (no ejecutado aún)")

    section("ARCHIVOS GENERADOS")
    outputs = [
        "baseline_summary.csv", "perfold_all.jsonl",
        "exp4_best_per_dataset_clf.csv", "exp4_significance_matrix.csv",
        "concat_summary.csv", "diff_sig_vs_individual.csv",
    ]
    for f in outputs:
        p = TABLES / f
        if p.exists():
            sz = p.stat().st_size
            print(f"  ✓ {f}  ({sz:,} bytes)")
        else:
            print(f"  ✗ {f}  (falta)")

    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
