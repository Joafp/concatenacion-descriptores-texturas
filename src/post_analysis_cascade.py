"""
post_analysis_cascade.py
=========================
A partir de los datos ya calculados:
  - baseline_summary.csv  (Exp 1, individual)
  - perfold_all.jsonl     (Exp 1, per-fold)
  - concat_summary.csv    (Exp 3, prefix concat)
  - perfold_concat_*.jsonl (Exp 3, per-fold concat)
  - exp4_best_per_dataset_clf.csv (Exp 4)

Hace:
  #1 Mejor combinación (k óptimo) por (dataset, clf)
  #2 Curvas de saturación por dataset/clf
  #3 Análisis por familia (classical/CNN/ViT/DINOv2)
  #5 Comparación final: mejor individual vs mejor concat

Genera:
  - results/tables/cascade_best_concat.csv
  - results/tables/cascade_family_analysis.csv
  - results/tables/cascade_final_comparison.csv
  - results/figures/saturation_{dataset}.png
  - Imprime reporte en consola
"""
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

TABLES = Path("results/tables")
FIGURES = Path("results/figures")
FIGURES.mkdir(parents=True, exist_ok=True)

DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]
CLFS = ["svm", "knn", "rf", "resmlp"]

# Familias (en el orden canónico del prefix concat)
FAMILIES = {
    "classical": ["lbp", "glcm", "gabor", "hog", "drlbp"],
    "cnn":       ["vgg16", "resnet50", "resnet101", "densenet121", "convnext_v2_t", "efficientnet_b0"],
    "vit":       ["vit_b16", "swin_t", "deit_s"],
    "dinov2":    ["dinov2_small", "dinov2", "dinov2_large"],
}
CANONICAL_ORDER = [
    "lbp", "glcm", "gabor", "hog", "drlbp",
    "vgg16", "resnet50", "resnet101", "densenet121", "convnext_v2_t", "efficientnet_b0",
    "vit_b16", "swin_t", "deit_s",
    "dinov2_small", "dinov2", "dinov2_large",
]


def load_perfold_combined():
    """Combina todos los perfold_*.jsonl (individuals) en un dict."""
    out = {}
    for ds in DATASETS:
        p = TABLES / f"perfold_{ds}.jsonl"
        if not p.exists():
            continue
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out[(r["dataset"], r["clf"], r["extractor"])] = np.array(r["per_fold_f1"])
    return out


def load_perfold_concat():
    """Carga perfold_concat_*.jsonl."""
    out = {}
    for ds in DATASETS:
        p = TABLES / f"perfold_concat_{ds}.jsonl"
        if not p.exists():
            continue
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out[(r["dataset"], r["clf"], r["k"])] = np.array(r["per_fold_f1"])
    return out


def cohens_d_paired(a, b):
    diff = a - b
    return diff.mean() / (diff.std(ddof=1) + 1e-12)


def holm_bonferroni(p_values):
    n = len(p_values)
    if n == 0:
        return []
    order = np.argsort(p_values)
    sorted_p = np.array(p_values)[order]
    adj = np.zeros(n)
    running_max = 0.0
    for i in range(n):
        val = sorted_p[i] * (n - i)
        running_max = max(running_max, val)
        adj[i] = min(running_max, 1.0)
    result = np.zeros(n)
    for i, oi in enumerate(order):
        result[oi] = adj[i]
    return result.tolist()


def section(title):
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


# ============================================================
# #1 Mejor combinación (k óptimo)
# ============================================================
def best_concat(concat_df, perfold_concat):
    rows = []
    for ds in DATASETS:
        sub = concat_df[concat_df.dataset == ds]
        for clf in CLFS:
            sub2 = sub[sub.clf == clf]
            if sub2.empty:
                continue
            # Encontrar k con max mean_f1
            best_idx = sub2["mean_f1"].idxmax()
            best = sub2.loc[best_idx]
            best_f1 = perfold_concat.get((ds, clf, int(best["k"])))
            rows.append({
                "dataset": ds, "clf": clf,
                "best_k": int(best["k"]),
                "best_subset": best["extractors"],
                "best_dim": int(best["dim"]),
                "best_mean_f1": float(best["mean_f1"]),
                "best_std_f1": float(best["std_f1"]),
                "k_at_saturation_1pct": _find_saturation(sub2, best["mean_f1"], threshold=0.01),
            })
    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "cascade_best_concat.csv", index=False)
    return df


def _find_saturation(sub, peak, threshold=0.01):
    """Encuentra el k más pequeño donde F1 está a 'threshold' del peak."""
    sub_sorted = sub.sort_values("k")
    saturated = sub_sorted[sub_sorted["mean_f1"] >= peak - threshold]
    if saturated.empty:
        return None
    return int(saturated.iloc[0]["k"])


# ============================================================
# #2 Curvas de saturación
# ============================================================
def plot_saturation(concat_df):
    for ds in DATASETS:
        sub = concat_df[concat_df.dataset == ds]
        if sub.empty:
            continue
        fig, ax = plt.subplots(figsize=(10, 6))
        for clf in CLFS:
            sub2 = sub[sub.clf == clf].sort_values("k")
            ks = sub2["k"].values
            f1s = sub2["mean_f1"].values
            stds = sub2["std_f1"].values
            ax.plot(ks, f1s, marker="o", label=clf, linewidth=2, markersize=5)
            ax.fill_between(ks, f1s - stds, f1s + stds, alpha=0.12)
        # Marcar familia
        ax.axvline(5, color="gray", linestyle="--", alpha=0.4, label="fin classical" if ds == DATASETS[0] else None)
        ax.axvline(11, color="gray", linestyle=":", alpha=0.4, label="fin CNN" if ds == DATASETS[0] else None)
        ax.axvline(14, color="gray", linestyle="-.", alpha=0.4, label="fin ViT" if ds == DATASETS[0] else None)
        ax.set_xlabel("k (nº de extractores concatenados)")
        ax.set_ylabel("macro-F1 (5-fold CV)")
        ax.set_title(f"Saturación por concatenación: {ds}")
        ax.set_xticks(range(1, 18))
        ax.set_xticklabels([f"{i+1}\n{CANONICAL_ORDER[i].split('_')[0]}" for i in range(17)],
                            rotation=0, fontsize=7)
        ax.legend(loc="lower right")
        ax.grid(True, alpha=0.3)
        if sub["mean_f1"].max() < 1.0:
            ax.set_ylim(0, min(1.05, sub["mean_f1"].max() + 0.1))
        plt.tight_layout()
        out = FIGURES / f"saturation_{ds}.png"
        plt.savefig(out, dpi=120)
        plt.close()
    return [str(FIGURES / f"saturation_{ds}.png") for ds in DATASETS]


# ============================================================
# #3 Análisis por familia
# ============================================================
def family_analysis(concat_df):
    """Para cada (dataset, clf), reporta F1 al final de cada familia del prefix concat."""
    rows = []
    for ds in DATASETS:
        sub = concat_df[concat_df.dataset == ds]
        for clf in CLFS:
            sub2 = sub[sub.clf == clf]
            row = {"dataset": ds, "clf": clf}
            # k=5 (fin classical)
            r5 = sub2[sub2.k == 5]
            row["f1_classical_only_k5"] = float(r5["mean_f1"].iloc[0]) if not r5.empty else None
            # k=11 (fin CNN)
            r11 = sub2[sub2.k == 11]
            row["f1_+cnn_k11"] = float(r11["mean_f1"].iloc[0]) if not r11.empty else None
            # k=14 (fin ViT)
            r14 = sub2[sub2.k == 14]
            row["f1_+vit_k14"] = float(r14["mean_f1"].iloc[0]) if not r14.empty else None
            # k=17 (todo)
            r17 = sub2[sub2.k == 17]
            row["f1_+dinov2_k17"] = float(r17["mean_f1"].iloc[0]) if not r17.empty else None
            # Deltas (aporte marginal de cada familia)
            row["delta_cnn"]    = row["f1_+cnn_k11"]    - row["f1_classical_only_k5"] if row["f1_classical_only_k5"] else None
            row["delta_vit"]    = row["f1_+vit_k14"]    - row["f1_+cnn_k11"]         if row["f1_+cnn_k11"]         else None
            row["delta_dinov2"] = row["f1_+dinov2_k17"] - row["f1_+vit_k14"]         if row["f1_+vit_k14"]         else None
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "cascade_family_analysis.csv", index=False)
    return df


# ============================================================
# #5 Comparación final: mejor individual vs mejor concat
# ============================================================
def final_comparison(perfold_indiv, perfold_concat, best_concat_df, best_indiv_df):
    rows = []
    for ds in DATASETS:
        for clf in CLFS:
            best_c = best_concat_df[(best_concat_df.dataset == ds) & (best_concat_df.clf == clf)]
            best_i = best_indiv_df[(best_indiv_df.dataset == ds) & (best_indiv_df.clf == clf)]
            if best_c.empty or best_i.empty:
                continue
            best_c = best_c.iloc[0]
            best_i = best_i.iloc[0]
            f1_concat = perfold_concat.get((ds, clf, int(best_c["best_k"])))
            f1_indiv = perfold_indiv.get((ds, clf, best_i["best_extractor"]))
            if f1_concat is None or f1_indiv is None or len(f1_concat) != len(f1_indiv):
                continue
            t_stat, p_val = stats.ttest_rel(f1_concat, f1_indiv)
            d = cohens_d_paired(f1_concat, f1_indiv)
            rows.append({
                "dataset": ds, "clf": clf,
                "best_individual": best_i["best_extractor"],
                "best_individual_f1": float(f1_indiv.mean()),
                "best_concat_k": int(best_c["best_k"]),
                "best_concat_subset": best_c["best_subset"],
                "best_concat_dim": int(best_c["best_dim"]),
                "best_concat_f1": float(f1_concat.mean()),
                "delta": float(f1_concat.mean() - f1_indiv.mean()),
                "t_stat": float(t_stat),
                "p_value": float(p_val),
                "cohens_d": float(d),
                "concat_better": bool(f1_concat.mean() > f1_indiv.mean()),
                "significant_05": bool(p_val < 0.05),
            })
    df = pd.DataFrame(rows)
    # Holm-Bonferroni
    if len(df) > 0:
        df["p_value_holm"] = holm_bonferroni(df["p_value"].tolist())
        df["significant_holm_05"] = df["p_value_holm"] < 0.05
    df.to_csv(TABLES / "cascade_final_comparison.csv", index=False)
    return df


# ============================================================
# Main
# ============================================================
def main():
    section("CARGANDO DATOS")
    perfold_indiv = load_perfold_combined()
    perfold_concat = load_perfold_concat()
    concat_df = pd.read_csv(TABLES / "concat_summary.csv")
    best_indiv_df = pd.read_csv(TABLES / "exp4_best_per_dataset_clf.csv")
    print(f"  perfold_indiv:  {len(perfold_indiv)} corridas (extractor individual)")
    print(f"  perfold_concat: {len(perfold_concat)} corridas (concat k)")
    print(f"  concat_summary: {len(concat_df)} filas")

    section("#1 — MEJOR COMBINACIÓN (k óptimo) POR (dataset, clf)")
    bc = best_concat(concat_df, perfold_concat)
    print(bc[["dataset", "clf", "best_k", "best_dim", "best_mean_f1", "best_std_f1", "k_at_saturation_1pct"]].to_string(index=False))

    section("#2 — CURVAS DE SATURACIÓN")
    figs = plot_saturation(concat_df)
    print(f"  Generadas {len(figs)} figuras:")
    for f in figs:
        print(f"    - {f}")

    section("#3 — ANÁLISIS POR FAMILIA (F1 en cada 'frontera' de familia)")
    fa = family_analysis(concat_df)
    cols_show = ["dataset", "clf",
                 "f1_classical_only_k5", "f1_+cnn_k11", "f1_+vit_k14", "f1_+dinov2_k17",
                 "delta_cnn", "delta_vit", "delta_dinov2"]
    print(fa[cols_show].round(3).to_string(index=False))

    section("#5 — COMPARACIÓN FINAL: mejor individual vs mejor concat")
    fc = final_comparison(perfold_indiv, perfold_concat, bc, best_indiv_df)
    cols5 = ["dataset", "clf", "best_individual", "best_individual_f1",
             "best_concat_k", "best_concat_f1", "delta", "p_value", "p_value_holm",
             "cohens_d", "significant_holm_05"]
    print(fc[cols5].round(4).to_string(index=False))

    section("RESUMEN EJECUTIVO")
    n_better = int(fc["concat_better"].sum()) if len(fc) else 0
    n_total = len(fc)
    n_sig = int(fc["significant_holm_05"].sum()) if "significant_holm_05" in fc.columns else 0
    print(f"  Casos (dataset × clf) totales:           {n_total}")
    print(f"  Concat supera al mejor individual:      {n_better}/{n_total} ({100*n_better/max(1,n_total):.0f}%)")
    print(f"  Significativos (Holm p<0.05):           {n_sig}/{n_total} ({100*n_sig/max(1,n_total):.0f}%)")
    if n_better:
        mean_delta = float(fc.loc[fc["concat_better"], "delta"].mean())
        max_delta = float(fc["delta"].max())
        max_ds_clf = fc.loc[fc["delta"].idxmax(), ["dataset", "clf"]].to_dict()
        print(f"  Δ F1 medio (cuando concat gana):       {mean_delta:+.3f}")
        print(f"  Δ F1 máximo:                            {max_delta:+.3f}  ({max_ds_clf})")

    section("ARCHIVOS GENERADOS")
    for f in ["cascade_best_concat.csv", "cascade_family_analysis.csv", "cascade_final_comparison.csv"]:
        p = TABLES / f
        if p.exists():
            print(f"  ✓ {f}  ({p.stat().st_size:,} bytes)")
    print(f"  ✓ results/figures/saturation_*.png  (6 figuras)")

    print()


if __name__ == "__main__":
    main()
