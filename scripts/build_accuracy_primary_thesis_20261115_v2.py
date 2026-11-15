"""Reconstruct accuracy-primary thesis evidence from saved calls and CSVs.

No fitting, extraction, new predictions, or timing. Preserves historical
macro-F1 ranking/selection and explicitly dates the reporting-metric change.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_topk_margin_thesis_20261113 import table, number
from prepare_top4_fixed_cascade import sha256
from run_top4_fixed_e1_e2 import metrics

ORDER = ["DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"]
PRETTY = dict(zip(ORDER, ["DTD", "FMD", "CUReT", "Outex-13", "Soil", "KTH-TIPS2b"]))
METRICS = ["accuracy", "precision_macro", "recall_macro", "macro_f1"]


def holm(values):
    order = np.argsort(values)
    adjusted = np.empty(len(values))
    running = 0.
    for i, index in enumerate(order):
        running = max(running, min(1., (len(values) - i) * values[index]))
        adjusted[index] = running
    return adjusted.tolist()


def exact_signed_rank(differences):
    differences = np.asarray(differences)
    differences = differences[differences != 0]
    if not len(differences):
        return 1.
    ranks = rankdata(np.abs(differences))
    observed = min(ranks[differences > 0].sum(), ranks[differences < 0].sum())
    sums = [float(ranks[np.array(bits, dtype=bool)].sum())
            for bits in itertools.product((0, 1), repeat=len(ranks))]
    return float(np.mean([min(s, ranks.sum() - s) <= observed + 1e-12 for s in sums]))


def static_statistics(matrix):
    values = matrix.to_numpy()
    ranks = rankdata(-values, axis=1)
    n, k = ranks.shape
    observed = float(np.square(ranks.sum(axis=0)).sum())
    alternatives = [list(itertools.permutations(row)) for row in ranks]
    count = sum(float(np.square(np.sum(choice, axis=0)).sum()) >= observed - 1e-10
                for choice in itertools.product(*alternatives))
    total = int(np.prod([len(x) for x in alternatives]))
    statistic, asymptotic = friedmanchisquare(*values.T)
    pairs = []
    for a, b in itertools.combinations(matrix.columns, 2):
        difference = matrix[a] - matrix[b]
        pairs.append(dict(a=a, b=b, mean_difference=float(difference.mean()),
                          p_exact=exact_signed_rank(difference.to_numpy())))
    for pair, adjusted in zip(pairs, holm([p["p_exact"] for p in pairs])):
        pair["p_holm"] = adjusted
    return {"metric": "accuracy", "datasets": n, "methods": list(matrix.columns),
            "friedman_chi2": float(statistic), "friedman_p_asymptotic": float(asymptotic),
            "friedman_p_exact": count / total, "permutations": total, "pairs": pairs}


def build(audit, generated):
    if audit.exists() or generated.exists():
        raise FileExistsError("choose new audit and generated folders")
    sources = {}

    def source(path):
        path = ROOT / path if not Path(path).is_absolute() else Path(path)
        sources[str(path.relative_to(ROOT))] = sha256(path)
        return path

    source(Path(__file__))
    curves, per_dataset, top4, static_frames, summaries = [], [], [], [], []
    full_sources = ["results/confirmatory/ngram22_beitv2/nested_fold_results.csv",
                    "results/extensions/outex13_official1360/ngram22_beitv2/nested_fold_results.csv",
                    "results/extensions/soil_original/ngram22_beitv2/nested_fold_results.csv",
                    "results/extensions/kth_tips2b/ngram22_beitv2/nested_fold_results.csv"]
    baseline = pd.concat([pd.read_csv(source(p)) for p in full_sources], ignore_index=True)
    for clf, base in [("svm", "results/exploratory/k_sweep"), ("resmlp", "results/exploratory/resmlp/k_sweep")]:
        raw = pd.concat([pd.read_csv(source(p)) for p in sorted((ROOT / base).glob("*/k_sweep.csv"))])
        assert len(raw) == 987 and not raw.duplicated(["dataset", "seed", "outer_fold", "k"]).any()
        assert raw.groupby("k").size().eq(47).all() and raw.classifier.eq(clf).all()
        by_ds = raw.groupby(["dataset", "k"])[["accuracy", "macro_f1", "pct_dimensions"]].mean().reset_index()
        by_ds["classifier"] = clf
        per_dataset.append(by_ds)
        curve = by_ds.groupby("k")[["accuracy", "macro_f1", "pct_dimensions"]].mean().reset_index()
        curve["classifier"] = clf
        curve["gain_pp"] = curve.accuracy.diff() * 100
        curves.append(curve)
        first, four, peak = curve.iloc[0], curve[curve.k.eq(4)].iloc[0], curve.loc[curve.accuracy.idxmax()]
        summaries.append({"classifier": clf, "accuracy_k1": float(first.accuracy),
            "accuracy_k4": float(four.accuracy), "peak_k": int(peak.k), "peak_accuracy": float(peak.accuracy),
            "gain_1_to_4_pp": float((four.accuracy-first.accuracy)*100),
            "gap_4_to_peak_pp": float((peak.accuracy-four.accuracy)*100),
            "fraction_gain_at4": float((four.accuracy-first.accuracy)/(peak.accuracy-first.accuracy)),
            "dimensions_pct_k4": float(four.pct_dimensions), "dimensions_pct_peak": float(peak.pct_dimensions)})
        for ds in ORDER:
            d = by_ds[by_ds.dataset.eq(ds)]
            at4, at21 = d[d.k.eq(4)].iloc[0], d[d.k.eq(21)].iloc[0]
            full = baseline[baseline.dataset.eq(ds) & baseline.classifier.eq(clf) & baseline.method.eq("full_concat")]
            individual = baseline[baseline.dataset.eq(ds) & baseline.classifier.eq(clf) & baseline.method.eq("best_individual")]
            expected = int(len(raw[raw.dataset.eq(ds) & raw.k.eq(4)]))
            if len(full) != expected or len(individual) != expected:
                raise ValueError(f"static coverage mismatch: {ds}/{clf}")
            top4.append(dict(dataset=ds, classifier=clf, conditions=expected, accuracy_top4=float(at4.accuracy),
                accuracy_full21=float(at21.accuracy), accuracy_full22=float(full.accuracy.mean()),
                accuracy_individual=float(individual.accuracy.mean()), peak_k=int(d.loc[d.accuracy.idxmax(), "k"]),
                macro_f1_top4=float(at4.macro_f1)))
    curves, per_dataset, top4 = map(lambda x: pd.concat(x, ignore_index=True) if isinstance(x[0], pd.DataFrame) else pd.DataFrame(x),
                                   [curves, per_dataset, top4])
    historical = []
    cascade_folder = ROOT / "results/exploratory/topk_cascade/cheap_stage_selected_primary22"
    old_rows = pd.read_csv(source(cascade_folder / "rows.csv"))
    for _, row in old_rows.iterrows():
        stem = f"{row.dataset}_{row.protocol}".replace(":", "__")
        pred = json.loads(source(cascade_folder / f"{stem}_predictions.json").read_text())
        truth = np.asarray(pred["y_true"])
        direct, conditional = np.asarray(pred["y_pred_topk_direct"]), np.asarray(pred["y_pred_adaptive_cascade"])
        mask = np.asarray(pred["requested_topk_adaptive"], bool)
        if not np.array_equal(direct[mask], conditional[mask]):
            raise ValueError("conditional rescue differs from direct")
        entry = dict(dataset=row.dataset, protocol=row.protocol, request_fraction=float(mask.mean()),
                     direct_projected_ms=row.topk_ms, conditional_projected_ms=row.new_ms)
        for name, prediction in [("direct", direct), ("conditional", conditional)]:
            entry.update({f"{name}_{m}": v for m, v in metrics(truth, prediction, np.unique(truth)).items()})
        historical.append(entry)
    cascade = pd.DataFrame(historical)
    local_rows = []
    manifest = pd.read_csv(source("results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv"))
    for row in manifest.itertuples():
        path = source(row.calls_csv)
        if sha256(path) != row.sha256:
            raise ValueError("canonical call CSV changed")
        calls = pd.read_csv(path)
        for policy, group in calls.groupby("policy"):
            local_rows.append(dict(dataset=row.dataset, classifier=row.classifier, id=row.id, policy=policy,
                mean_ms=float(group.ms.mean()), **metrics(group.label, group.prediction, np.unique(group.label))))
    local = pd.DataFrame(local_rows)
    assert len(local) == 470
    online = local.groupby(["dataset", "classifier", "policy"])[METRICS + ["mean_ms"]].mean().reset_index()
    external = json.loads(source("results/analysis/reconciliation_full_panel_20261104_v1/reference_results.json").read_text())
    ng_old = pd.read_csv(source("paper/articulo/borrador_profesor/generated/reference20_source_rows.csv"))
    ng_new = pd.read_csv(source("paper/articulo/borrador_profesor/generated/ngram21_source_rows.csv"))
    keys = ["dataset", "classifier", "seed", "outer_fold", "method", "run_mode"]
    ng = ng_old.merge(ng_new, on=keys, suffixes=("_20", "_21"), validate="one_to_one")
    assert len(ng) == 280
    audit.mkdir(parents=True)
    generated.mkdir(parents=True)
    for name, frame in [("curves", curves), ("per_dataset_curves", per_dataset), ("top4", top4),
                        ("historical_cascade", cascade), ("online_condition_metrics", local), ("online_means", online), ("ngram_paired", ng)]:
        frame.to_csv(audit / f"{name}.csv", index=False)
    stats = {}
    for clf in ("svm", "resmlp"):
        d = top4[top4.classifier.eq(clf)].set_index("dataset").loc[ORDER]
        matrix = d[["accuracy_individual", "accuracy_full22", "accuracy_top4"]].copy()
        matrix.columns = ["Individual", "Completa-22", "Top-4"]
        matrix.to_csv(audit / f"static_accuracy_{clf}.csv")
        stats[clf] = static_statistics(matrix)
    (audit / "statistics.json").write_text(json.dumps(stats, indent=2) + "\n")
    selected_k = [1, 2, 3, 4, 5, 10, 21]
    rows = []
    for k in selected_k:
        g = curves[curves.k.eq(k)].set_index("classifier")
        rows.append([k, number(g.loc["svm", "accuracy"], 6), number(g.loc["resmlp", "accuracy"], 6), number(g.loc["svm", "pct_dimensions"], 2)])
    (generated / "curva_k.tex").write_text(table("Exactitud del barrido ampliado: media equiponderada de seis datasets, 47 condiciones por tamaño y clasificador.", "tab:tm-curva", ["k", "Accuracy SVM", "Accuracy ResMLP", r"\% dimensiones"], rows, "Ranking histórico seleccionado por macro-F1 interno; reporte principal por accuracy desde el 15-11-2026. No es una nueva selección de bloques."))
    for clf in ("svm", "resmlp"):
        d = top4[top4.classifier.eq(clf)].set_index("dataset")
        rows = [[PRETTY[ds], int(d.loc[ds, "conditions"]), number(d.loc[ds, "accuracy_top4"]), number(d.loc[ds, "accuracy_full21"]), number(d.loc[ds, "accuracy_full22"]), number(d.loc[ds, "accuracy_top4"]-d.loc[ds, "accuracy_full22"])] for ds in ORDER]
        (generated / f"top4_{clf}.tex").write_text(table(f"Accuracy de Top-4 y concatenaciones completas ({clf.upper()}).", f"tab:tm-top4-{clf}", ["Dataset", "Cond.", "Top-4", "21 sin Ng", "22 con Ng", r"$\Delta$ a 22"], rows, "Archivo estático; biblioteca y variante KTH identificadas. No combinar estas cifras con tiempos online posteriores."))
    means = cascade.groupby("dataset").mean(numeric_only=True)
    rows = [[PRETTY[ds], number(means.loc[ds, "direct_accuracy"], 6), number(means.loc[ds, "conditional_accuracy"], 6), number(means.loc[ds, "conditional_accuracy"]-means.loc[ds, "direct_accuracy"], 6), number(100*means.loc[ds, "request_fraction"], 1)] for ds in ORDER]
    (generated / "cascada_calidad.tex").write_text(table("Accuracy del mismo Top-k directo y por margen: archivo histórico de 27 condiciones SVM.", "tab:tm-cascada", ["Dataset", "Directo Acc", "Margen Acc", r"$\Delta$ Acc", r"Rescate \%"], rows, "Top-k de tamaño heredado, no Top-4 fijo. KTH descriptivo y excluido de inferencia conjunta histórica."))
    rows = [[PRETTY[ds]] + [number(means.loc[ds, f"{route}_{metric}"], 4) for metric in ["precision_macro", "recall_macro", "macro_f1"] for route in ["direct", "conditional"]] for ds in ORDER]
    (generated / "cascada_secundarias.tex").write_text(table("Métricas complementarias de las mismas predicciones históricas.", "tab:accuracy-secondary-cascade", ["Dataset", "Prec. D", "Prec. M", "Recall D", "Recall M", "F1 D", "F1 M"], rows, "Promedios macro por clase, después por condición. D: directo; M: margen.", size=8))
    subset = json.loads(source("results/analysis/topk_margin_rewrite_20261113_v1/top4_margin_subset.json").read_text())
    rows = []
    for r in subset:
        x = cascade[cascade.dataset.eq(r["dataset"]) & cascade.protocol.eq(r["protocol"])].iloc[0]
        short = r["protocol"].replace("stratified_group_kfold5_", "").replace("curet_half_indices:", "")
        rows.append([PRETTY[r["dataset"]] + " / " + short, number(x.direct_accuracy, 6), number(x.conditional_accuracy, 6), number(x.conditional_accuracy-x.direct_accuracy, 6), number(100*x.request_fraction, 2)])
    (generated / "top4_margin_subset.tex").write_text(table("Cinco condiciones históricas con los mismos bloques que Top-4: accuracy.", "tab:tm-fixed4-margin", ["Condición", "Directo Acc", "Margen Acc", r"$\Delta$ Acc", r"Rescate \%"], rows, "Evidencia parcial de tres datasets, anterior a E1. Coincidencia de bloques no acredita identidad de todos los ajustes."))
    rows = []
    for ds in ORDER:
        own = online[online.dataset.eq(ds) & online.classifier.eq("svm") & online.policy.eq("Top-4")].iloc[0]
        rows.append([PRETTY[ds], number(own.accuracy)] + [number(external[ds][method].get("mean_split_accuracy", external[ds][method].get("accuracy"))) + (r"$^\dagger$" if method == "DeepLumina" else "") if method in external[ds] else "incompleto" for method in ["Neshov", "HyTex", "CellNN", "DeepLumina"]])
    (generated / "externos_accuracy.tex").write_text(table("Accuracy de Top-4/SVM y adaptaciones externas: mismas llamadas que las latencias archivadas.", "tab:tm-externos-accuracy", ["Dataset", "Top-4", "Neshov", "HyTex", "CellNN", "DeepLumina"], rows, r"$^\dagger$ No convergencia; DTD sin media completa. Adaptaciones, no reproducción fiel de porcentajes. Reservas KTH/DTD y hardware se conservan.", size=8))
    rows = []
    for r in online[online.policy.eq("Top-4")].itertuples():
        rows.append([PRETTY[r.dataset], r.classifier.upper(), number(r.accuracy), number(r.precision_macro), number(r.recall_macro), number(r.macro_f1)])
    (generated / "online_secundarias.tex").write_text(table("Accuracy y métricas complementarias de Top-4 online.", "tab:accuracy-online-metrics", ["Dataset", "Clasif.", "Accuracy", "Prec. macro", "Recall macro", "Macro-F1"], rows, "Todas se reconstruyen de las mismas predicciones y llamadas del panel canónico.", size=8))
    method_names = {"best_individual": "Individual", "full_concat": "Completa", "topk_individual": r"Top-$k$", "gfs": "GFS", "homogeneous": "Homogénea"}
    for clf in ("svm", "resmlp"):
        rows = []
        for ds in ORDER[:4]:
            for method, name in method_names.items():
                d = ng[ng.dataset.eq(ds) & ng.classifier.eq(clf) & ng.method.eq(method)]
                if d.empty:
                    continue
                rows.append([PRETTY[ds], name, number(d.accuracy_20.mean()), number(d.accuracy_21.mean()), number((d.accuracy_21-d.accuracy_20).mean())])
        (generated / f"ngram_{clf}.tex").write_text(table(f"Accuracy con 20 frente a 21 bloques con N-gramas ({clf.upper()}).", f"tab:ngram-accuracy-{clf}", ["Dataset", "Estrategia", "Acc. (20)", "Acc. (21)", r"$\Delta$ Acc."], rows, "Control histórico emparejado; biblioteca anterior a BEiT-v2. No es Top-4 más N-gramas.", size=8))
    rows = [[clf.upper(), number(stats[clf]["friedman_chi2"], 4), number(stats[clf]["friedman_p_exact"], 4)] for clf in ("svm", "resmlp")]
    (generated / "estadistica_accuracy.tex").write_text(table("Contraste principal de accuracy: Individual, Completa-22 y Top-4.", "tab:accuracy-statistics", ["Clasificador", r"Friedman $\chi^2$", r"$p$ exacto"], rows, "Seis medias por dataset, 46.656 permutaciones; el no rechazo no acredita equivalencia. Los tres pares Wilcoxon exactos y Holm constan en el archivo de análisis."))
    rows = [[clf.upper(), p["a"] + " / " + p["b"], number(p["mean_difference"], 6), number(p["p_exact"], 4), number(p["p_holm"], 4)] for clf in ("svm", "resmlp") for p in stats[clf]["pairs"]]
    (generated / "estadistica_pares.tex").write_text(table("Comparaciones pareadas de accuracy y ajuste de Holm.", "tab:accuracy-pairs", ["Clasif.", "Par (A/B)", r"$\Delta$ A-B", r"$p$ exacto", r"$p$ Holm"], rows, "Una observación por dataset; familia de tres pares por clasificador. Selección y cambio de métrica tienen carácter exploratorio.", size=8))
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    colors = {"svm": "#176c84", "resmlp": "#b76b20"}
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4), layout="constrained")
    for clf in colors:
        d = curves[curves.classifier.eq(clf)]
        axes[0].plot(d.k, d.accuracy*100, ".-", color=colors[clf], label=clf.upper())
        axes[1].bar(d.k.iloc[1:] + (-.18 if clf == "svm" else .18), d.gain_pp.iloc[1:], width=.35, color=colors[clf], label=clf.upper())
        four = d[d.k.eq(4)].iloc[0]
        axes[0].scatter([4], [100*four.accuracy], facecolor="white", edgecolor=colors[clf], s=65, zorder=5)
    for ax in axes:
        ax.axvline(4, color=".4", ls="--", lw=.8)
        ax.set(xlabel="Número de descriptores k", xticks=[1, 4, 5, 10, 15, 21])
        ax.grid(axis="y", alpha=.2)
        ax.legend(frameon=False)
    axes[0].set(ylabel="Accuracy media (%)", title="Calidad de la concatenación")
    axes[1].set(ylabel="Cambio de accuracy (puntos porcentuales)", title="Ganancia de cada bloque adicional")
    axes[1].axhline(0, color=".4", lw=.8)
    for extension in ("pdf", "png"):
        fig.savefig(generated / f"ganancias_k.{extension}", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(10.4, 6.5), layout="constrained")
    for ax, ds in zip(axes.flat, ORDER):
        for clf in colors:
            d = per_dataset[per_dataset.dataset.eq(ds) & per_dataset.classifier.eq(clf)]
            ax.plot(d.k, d.accuracy*100, ".-", color=colors[clf], label=clf.upper(), ms=3)
        ax.axvline(4, color=".4", ls="--", lw=.8)
        ax.set(title=PRETTY[ds], xlabel="k descriptores", ylabel="Accuracy (%)", xticks=[1,4,10,15,21])
        ax.grid(alpha=.2)
    axes[0,0].legend(frameon=False)
    for extension in ("pdf", "png"):
        fig.savefig(generated / f"curvas_por_dataset.{extension}", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4), layout="constrained")
    for ax, metric in zip(axes, ["accuracy", "projected_ms"]):
        xs, ys = means.loc[ORDER, f"direct_{metric}"], means.loc[ORDER, f"conditional_{metric}"]
        ax.scatter(xs, ys, color=colors["svm"])
        for ds, x, y in zip(ORDER, xs, ys):
            ax.annotate(PRETTY[ds], (x,y), xytext=(5, 5), textcoords="offset points", fontsize=7)
        lo, hi = min(xs.min(),ys.min()), max(xs.max(),ys.max())
        pad = max((hi-lo)*.18, .005)
        ax.plot([lo-pad,hi+pad], [lo-pad,hi+pad], "--", color=".6")
        ax.set(xlim=(lo-pad,hi+pad), ylim=(lo-pad,hi+pad),
               xlabel="Directo: " + ("accuracy" if metric == "accuracy" else "costo proyectado (ms)"),
               ylabel="Margen: " + ("accuracy" if metric == "accuracy" else "costo proyectado (ms)"))
    for extension in ("pdf", "png"):
        fig.savefig(generated / f"directo_margen.{extension}", dpi=170)
    plt.close(fig)
    summary = {"date": "2026-11-15", "primary_metric": "accuracy", "secondary_metrics": METRICS[1:],
               "metric_change_after_observing_historical_tests": True, "historical_selection_metric": "macro_f1",
               "new_fits": 0, "new_predictions": 0, "new_timings": 0, "curve_statistics": summaries,
               "top4_per_dataset": top4.to_dict("records"), "historical_cascade_means": means.reset_index().to_dict("records"),
               "statistics": stats, "online_condition_method_rows": len(local), "source_sha256": sources}
    (audit / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    outputs = {str(p.relative_to(ROOT)): sha256(p) for directory in (audit, generated) for p in directory.iterdir() if p.is_file()}
    (audit / "provenance.json").write_text(json.dumps({"sources": sources, "outputs": outputs}, indent=2) + "\n")
    print(json.dumps({"curve_statistics": summaries, "statistics": stats, "sources": len(sources)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    args = parser.parse_args()
    build(args.audit.resolve(), args.generated.resolve())
