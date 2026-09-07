"""
gfs_vs_prefix_diff_sig.py
==========================
Compara GFS vs Prefix concat (k=17) y vs mejor individual, con diff sig + Holm-Bonferroni.
También genera figuras: GFS paths, GFS vs Prefix concat, GFS vs best individual.

Lee:
  - perfold_*.jsonl              (individuals)
  - perfold_concat_*.jsonl        (prefix concat)
  - perfold_greedy_*.jsonl        (GFS)

Guarda:
  - results/tables/gfs_vs_prefix_diff_sig.csv
  - results/tables/gfs_comparison_summary.csv
  - results/figures/gfs_paths_{dataset}.png
  - results/figures/gfs_vs_prefix_bar.png
  - results/figures/gfs_vs_best_individual_bar.png
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


def load_perfold(prefix):
    """Carga perfold_*.jsonl, perfold_concat_*.jsonl, o perfold_greedy_*.jsonl según prefix."""
    out = {}
    for ds in DATASETS:
        if prefix:
            p = TABLES / f"perfold_{prefix}_{ds}.jsonl"
        else:
            p = TABLES / f"perfold_{ds}.jsonl"
        if not p.exists():
            continue
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            # Key strategy-specific
            if prefix == "concat":
                key = (r["dataset"], r["clf"], r["k"])
            elif prefix == "greedy":
                key = (r["dataset"], r["clf"], r["step"])
            else:
                key = (r["dataset"], r["clf"], r["extractor"])
            out[key] = np.array(r["per_fold_f1"])
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
# Comparación GFS vs Prefix concat (k=17) y vs Best individual
# ============================================================
def diff_sig_comparison(perfold_indiv, perfold_concat, perfold_greedy, gfs_summary):
    rows = []
    for ds in DATASETS:
        for clf in CLFS:
            # GFS best
            g = gfs_summary[(gfs_summary.dataset == ds) & (gfs_summary.clf == clf)]
            if g.empty:
                continue
            g = g.iloc[0]
            gfs_step = int(g["best_step"])
            gfs_f1 = perfold_greedy.get((ds, clf, gfs_step))
            if gfs_f1 is None:
                continue
            # Prefix concat k=17
            prefix_f1 = perfold_concat.get((ds, clf, 17))
            # Best individual
            from collections import defaultdict
            indiv_index = {}
            for (d, c, e), f1 in perfold_indiv.items():
                if d == ds and c == clf:
                    indiv_index[e] = f1
            if indiv_index:
                best_e = max(indiv_index, key=lambda e: indiv_index[e].mean())
                best_i_f1 = indiv_index[best_e]
            else:
                best_e, best_i_f1 = None, None

            # GFS vs Prefix concat k=17
            if prefix_f1 is not None and len(prefix_f1) == len(gfs_f1):
                t, p = stats.ttest_rel(gfs_f1, prefix_f1)
                d = cohens_d_paired(gfs_f1, prefix_f1)
                rows.append({
                    "dataset": ds, "clf": clf,
                    "comparison": "GFS_vs_Prefix_k17",
                    "method_a": f"GFS_step{gfs_step} ({g['best_subset'][:50]})",
                    "method_b": "Prefix_concat_k17",
                    "mean_a": float(gfs_f1.mean()),
                    "mean_b": float(prefix_f1.mean()),
                    "delta": float(gfs_f1.mean() - prefix_f1.mean()),
                    "t_stat": float(t), "p_value": float(p),
                    "cohens_d": float(d),
                    "a_better": bool(gfs_f1.mean() > prefix_f1.mean()),
                })
            # GFS vs Best individual
            if best_i_f1 is not None and len(best_i_f1) == len(gfs_f1):
                t, p = stats.ttest_rel(gfs_f1, best_i_f1)
                d = cohens_d_paired(gfs_f1, best_i_f1)
                rows.append({
                    "dataset": ds, "clf": clf,
                    "comparison": "GFS_vs_BestIndividual",
                    "method_a": f"GFS_step{gfs_step} ({g['best_subset'][:50]})",
                    "method_b": f"Individual_{best_e}",
                    "mean_a": float(gfs_f1.mean()),
                    "mean_b": float(best_i_f1.mean()),
                    "delta": float(gfs_f1.mean() - best_i_f1.mean()),
                    "t_stat": float(t), "p_value": float(p),
                    "cohens_d": float(d),
                    "a_better": bool(gfs_f1.mean() > best_i_f1.mean()),
                })

    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df
    # Holm-Bonferroni por 'comparison'
    df["p_value_holm"] = np.nan
    df["significant_05"] = False
    df["significant_01"] = False
    df["significant_001"] = False
    for comp, grp in df.groupby("comparison"):
        idx = grp.index
        adj = holm_bonferroni(grp["p_value"].tolist())
        df.loc[idx, "p_value_holm"] = adj
        df.loc[idx, "significant_05"] = (np.array(adj) < 0.05)
        df.loc[idx, "significant_01"] = (np.array(adj) < 0.01)
        df.loc[idx, "significant_001"] = (np.array(adj) < 0.001)
    df.to_csv(TABLES / "gfs_vs_prefix_diff_sig.csv", index=False)
    return df


# ============================================================
# Summary tabla comparativa
# ============================================================
def build_summary(gfs_summary, prefix_concat_df, best_indiv_df, diff_sig_df):
    rows = []
    for _, g in gfs_summary.iterrows():
        ds, clf = g["dataset"], g["clf"]
        # Prefix concat k=17
        p = prefix_concat_df[(prefix_concat_df.dataset == ds) & (prefix_concat_df.clf == clf) & (prefix_concat_df.k == 17)]
        prefix_f1 = float(p["mean_f1"].iloc[0]) if not p.empty else None
        # Best individual
        b = best_indiv_df[(best_indiv_df.dataset == ds) & (best_indiv_df.clf == clf)]
        ind_f1 = float(b["best_mean_f1"].iloc[0]) if not b.empty else None
        ind_ext = b["best_extractor"].iloc[0] if not b.empty else None
        # Diff sig
        gv = diff_sig_df[(diff_sig_df.dataset == ds) & (diff_sig_df.clf == clf) & (diff_sig_df.comparison == "GFS_vs_Prefix_k17")]
        sig_prefix = bool(gv["significant_05"].iloc[0]) if not gv.empty else None
        gi = diff_sig_df[(diff_sig_df.dataset == ds) & (diff_sig_df.clf == clf) & (diff_sig_df.comparison == "GFS_vs_BestIndividual")]
        sig_indiv = bool(gi["significant_05"].iloc[0]) if not gi.empty else None
        rows.append({
            "dataset": ds, "clf": clf,
            "gfs_step": int(g["best_step"]),
            "gfs_subset": g["best_subset"],
            "gfs_dim": int(g["best_dim"]),
            "gfs_f1": float(g["best_mean_f1"]),
            "prefix_k17_f1": prefix_f1,
            "delta_vs_prefix": (float(g["best_mean_f1"]) - prefix_f1) if prefix_f1 else None,
            "sig_vs_prefix": sig_prefix,
            "best_indiv": ind_ext,
            "best_indiv_f1": ind_f1,
            "delta_vs_indiv": (float(g["best_mean_f1"]) - ind_f1) if ind_f1 else None,
            "sig_vs_indiv": sig_indiv,
        })
    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "gfs_comparison_summary.csv", index=False)
    return df


# ============================================================
# Figuras
# ============================================================
def plot_gfs_paths(perfold_greedy, gfs_summary):
    """Una figura por dataset, 4 subplots (uno por clf)."""
    for ds in DATASETS:
        fig, axes = plt.subplots(1, 4, figsize=(20, 4), sharey=False)
        for ax, clf in zip(axes, CLFS):
            # Path
            steps = sorted(k for (d, c, k) in perfold_greedy if d == ds and c == clf)
            if not steps:
                ax.set_title(f"{clf} (sin datos)")
                continue
            means = [perfold_greedy[(ds, clf, s)].mean() for s in steps]
            stds = [perfold_greedy[(ds, clf, s)].std(ddof=1) for s in steps]
            ax.plot(steps, means, marker="o", linewidth=2, markersize=7, color="C0")
            ax.fill_between(steps,
                            [m - s for m, s in zip(means, stds)],
                            [m + s for m, s in zip(means, stds)],
                            alpha=0.2, color="C0")
            # Marcar el best step
            g = gfs_summary[(gfs_summary.dataset == ds) & (gfs_summary.clf == clf)]
            if not g.empty:
                best_step = int(g["best_step"].iloc[0])
                best_f1 = float(g["best_mean_f1"].iloc[0])
                ax.axhline(best_f1, color="red", linestyle="--", alpha=0.4, label=f"best={best_f1:.3f}@k={best_step}")
                ax.scatter([best_step], [best_f1], color="red", s=100, zorder=5)
            ax.set_xlabel("step k")
            ax.set_ylabel("macro-F1")
            ax.set_title(f"{ds} - {clf}")
            ax.grid(True, alpha=0.3)
            ax.legend(loc="lower right", fontsize=8)
        plt.suptitle(f"GFS paths — {ds}", fontsize=14, fontweight="bold")
        plt.tight_layout()
        out = FIGURES / f"gfs_paths_{ds}.png"
        plt.savefig(out, dpi=120)
        plt.close()
    return [str(FIGURES / f"gfs_paths_{ds}.png") for ds in DATASETS]


def plot_gfs_vs_prefix_bars(summary_df):
    """Bar plot comparativo: GFS vs Prefix k=17 vs Best individual."""
    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(summary_df))
    width = 0.27
    # Colores por clf
    colors = {"svm": "C0", "knn": "C1", "rf": "C2", "resmlp": "C3"}
    for i, clf in enumerate(CLFS):
        sub = summary_df[summary_df.clf == clf]
        if sub.empty:
            continue
        idx = [summary_df.index.get_loc(i) for i in sub.index]
        ax.bar([j + (i - 1.5) * width for j in idx], sub["gfs_f1"], width,
               label=f"GFS ({clf})", color=colors[clf], alpha=0.85)
    # Prefix k=17 y Best indiv como líneas por dataset
    for ds in DATASETS:
        sub = summary_df[summary_df.dataset == ds]
        if sub.empty:
            continue
        xpos = [summary_df.index.get_loc(i) for i in sub.index]
        prefix_f1 = sub["prefix_k17_f1"].mean()
        ax.axhline(prefix_f1, color="gray", linestyle="--", alpha=0.3, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['dataset']}\n{r['clf']}" for _, r in summary_df.iterrows()],
                       rotation=0, fontsize=8)
    ax.set_ylabel("macro-F1")
    ax.set_title("GFS (barras coloreadas) vs Prefix k=17 (línea gris)")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    out = FIGURES / "gfs_vs_prefix_bar.png"
    plt.savefig(out, dpi=120)
    plt.close()
    return str(out)


def plot_gfs_vs_best_individual(summary_df):
    """Scatter GFS vs Best individual, color por dataset."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ds_colors = {"DTD": "C0", "FMD": "C1", "CUReT": "C3", "Soil": "C4", "VisTex": "C5"}
    markers = {"svm": "o", "knn": "s", "rf": "^", "resmlp": "D"}
    for _, r in summary_df.iterrows():
        if r["best_indiv_f1"] is None or r["gfs_f1"] is None:
            continue
        ax.scatter(r["best_indiv_f1"], r["gfs_f1"],
                   c=ds_colors.get(r["dataset"], "k"),
                   marker=markers.get(r["clf"], "o"),
                   s=80, alpha=0.7, edgecolor="black", linewidth=0.5)
    # Diagonal y=y
    lims = [0.5, 1.0]
    ax.plot(lims, lims, "k--", alpha=0.3, label="y=x (igualdad)")
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_xlabel("F1 mejor individual")
    ax.set_ylabel("F1 GFS")
    ax.set_title("GFS vs Mejor individual (color=dataset, marker=clf)")
    # Leyendas
    from matplotlib.lines import Line2D
    legend1 = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=10, label=ds)
               for ds, c in ds_colors.items()]
    legend2 = [Line2D([0], [0], marker=m, color='w', markerfacecolor='gray', markersize=10, label=clf)
               for clf, m in markers.items()]
    ax.legend(handles=legend1 + legend2, loc="lower right", fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = FIGURES / "gfs_vs_best_individual_scatter.png"
    plt.savefig(out, dpi=120)
    plt.close()
    return str(out)


# ============================================================
# Main
# ============================================================
def main():
    section("CARGANDO DATOS")
    perfold_indiv = load_perfold("")
    perfold_concat = load_perfold("concat")
    perfold_greedy = load_perfold("greedy")
    gfs_summary = pd.read_csv(TABLES / "greedy_summary.csv")
    prefix_concat_df = pd.read_csv(TABLES / "concat_summary.csv")
    best_indiv_df = pd.read_csv(TABLES / "exp4_best_per_dataset_clf.csv")
    print(f"  perfold_indiv:    {len(perfold_indiv)}")
    print(f"  perfold_concat:   {len(perfold_concat)}")
    print(f"  perfold_greedy:   {len(perfold_greedy)}")

    section("DIFF SIG: GFS vs Prefix concat (k=17) y vs Best individual")
    diff_df = diff_sig_comparison(perfold_indiv, perfold_concat, perfold_greedy, gfs_summary)
    print(f"  Total comparaciones: {len(diff_df)}")
    print(f"  Significativas (Holm p<0.05): {int(diff_df['significant_05'].sum())}")
    print(f"  Significativas (Holm p<0.01): {int(diff_df['significant_01'].sum())}")
    print(f"  Significativas (Holm p<0.001): {int(diff_df['significant_001'].sum())}")
    print()
    print("Por comparación:")
    for comp, grp in diff_df.groupby("comparison"):
        n_better = int(grp["a_better"].sum())
        n_sig = int(grp["significant_05"].sum())
        mean_delta = float(grp["delta"].mean())
        print(f"  {comp:30s}  n={len(grp):2d}  GFS_better={n_better}  sig={n_sig}  Δ_mean={mean_delta:+.3f}")

    section("TABLA COMPARATIVA CONSOLIDADA")
    summary_df = build_summary(gfs_summary, prefix_concat_df, best_indiv_df, diff_df)
    cols_show = ["dataset", "clf", "gfs_step", "gfs_dim", "gfs_f1",
                 "prefix_k17_f1", "delta_vs_prefix", "sig_vs_prefix",
                 "best_indiv_f1", "delta_vs_indiv", "sig_vs_indiv"]
    print(summary_df[cols_show].round(3).to_string(index=False))

    section("FIGURAS: GFS paths")
    paths = plot_gfs_paths(perfold_greedy, gfs_summary)
    print(f"  Generadas {len(paths)} figuras")
    for f in paths:
        print(f"    - {f}")

    section("FIGURAS: GFS vs Prefix concat (bar plot)")
    bar1 = plot_gfs_vs_prefix_bars(summary_df)
    print(f"  - {bar1}")

    section("FIGURAS: GFS vs Best individual (scatter)")
    bar2 = plot_gfs_vs_best_individual(summary_df)
    print(f"  - {bar2}")

    section("ARCHIVOS GENERADOS")
    for f in ["gfs_vs_prefix_diff_sig.csv", "gfs_comparison_summary.csv"]:
        p = TABLES / f
        if p.exists():
            print(f"  ✓ {f}  ({p.stat().st_size:,} bytes)")
    print(f"  ✓ results/figures/gfs_paths_*.png  (6 figuras)")
    print(f"  ✓ {bar1}")
    print(f"  ✓ {bar2}")
    print()


if __name__ == "__main__":
    main()
