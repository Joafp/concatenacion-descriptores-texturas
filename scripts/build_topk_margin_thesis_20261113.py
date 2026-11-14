"""Audit saved Top-k experiments and render the rewritten thesis artifacts.

No fitting, extraction, new predictions or timing. Historical F1, analytical
costs and physical timings remain separate. The output audit is exclusive-create.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"]
PRETTY = dict(zip(ORDER, ["DTD", "FMD", "CUReT", "Outex-13", "Soil", "KTH-TIPS2b"]))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value, digits=4):
    return f"{float(value):.{digits}f}".replace(".", ",")


def table(caption, label, header, rows, note="", size=9):
    columns = "@{}l" + "r" * (len(header) - 1) + "@{}"
    return "\n".join([
        r"\begin{table}[!htbp]\centering",
        rf"\fontsize{{{size}}}{{{size+2}}}\selectfont\setlength{{\tabcolsep}}{{4pt}}",
        rf"\caption{{{caption}}}\label{{{label}}}",
        rf"\begin{{tabular}}{{{columns}}}\toprule",
        " & ".join(header) + r"\\\midrule",
        *[" & ".join(map(str, row)) + r"\\" for row in rows],
        r"\bottomrule\end{tabular}",
        (r"\par\smallskip\begin{minipage}{0.98\textwidth}\footnotesize " + note + r"\end{minipage}") if note else "",
        r"\end{table}", "",
    ])


def build(audit_dir, generated):
    if audit_dir.exists():
        raise FileExistsError(f"Audit already exists: {audit_dir}")
    sources = {}

    def source(relative):
        path = ROOT / relative
        sources[path.relative_to(ROOT).as_posix()] = digest(path)
        return path

    curves, top4_rows, classifier_summaries = [], [], []
    for clf, prefix in [("svm", "results/exploratory/k_sweep"),
                        ("resmlp", "results/exploratory/resmlp/k_sweep")]:
        paths = sorted((ROOT / prefix).glob("*/k_sweep.csv"))
        assert len(paths) == 6
        frame = pd.concat([pd.read_csv(source(p.relative_to(ROOT))) for p in paths], ignore_index=True)
        frame = frame[frame.classifier.eq(clf)]
        assert not frame.duplicated(["dataset", "seed", "outer_fold", "k"]).any()
        assert set(frame.k) == set(range(1, 22))
        assert frame.groupby("k").size().eq(47).all()
        assert not frame.selected.str.contains("rgb_ngram", regex=False).any()
        by_dataset = frame.groupby(["dataset", "k"])[["macro_f1", "pct_dimensions"]].mean()
        curve = by_dataset.groupby("k").mean()
        saved = json.loads(source(f"results/analysis/selection_tables/{clf}.json").read_text())
        for row in saved["curve"]:
            assert np.isclose(curve.loc[row["k"], "macro_f1"], row["macro_f1"], atol=1e-12, rtol=0)
        for k, row in curve.iterrows():
            curves.append({"classifier": clf, "k": int(k), "macro_f1": float(row.macro_f1),
                           "pct_dimensions_vs_21": float(row.pct_dimensions), "conditions": 47})
        for ds in ORDER:
            archived = saved["per_dataset"][ds]
            top4_rows.append({"classifier": clf, "dataset": ds,
                "conditions": int(archived["conditions"]),
                "top4": float(by_dataset.loc[(ds, 4), "macro_f1"]),
                "full21": float(by_dataset.loc[(ds, 21), "macro_f1"]),
                "full22": float(archived["full22_macro_f1"]),
                "pct_dimensions_vs_21": float(by_dataset.loc[(ds, 4), "pct_dimensions"])})
        classifier_summaries.append({"classifier": clf, "rows": len(frame),
            "peak_k": int(curve.macro_f1.idxmax()), "peak_f1": float(curve.macro_f1.max()),
            "top4_f1": float(curve.loc[4, "macro_f1"]),
            "top4_pct_dimensions": float(curve.loc[4, "pct_dimensions"])})

    folder = ROOT / "results/exploratory/topk_cascade/cheap_stage_selected_primary22"
    rows = pd.read_csv(source(folder.relative_to(ROOT) / "rows.csv"))
    assert len(rows) == 27 and not rows.duplicated(["dataset", "protocol"]).any()
    assert rows.groupby("dataset").size().to_dict() == {
        "DTD": 10, "FMD": 5, "CUReT": 2, "Outex13Official1360": 1, "SoilOriginal": 5, "KTHTIPS2b": 4}
    audited = []
    for _, row in rows.iterrows():
        stem = f"{row.dataset}_{row.protocol}".replace(":", "__")
        result = json.loads(source(folder.relative_to(ROOT) / f"{stem}_result.json").read_text())
        pred = json.loads(source(folder.relative_to(ROOT) / f"{stem}_predictions.json").read_text())
        pretest = json.loads(source(folder.relative_to(ROOT) / f"{stem}_selection_pretest.json").read_text())
        assert (result["dataset"], result["protocol"]) == (row.dataset, row.protocol)
        assert (pred["dataset"], pred["protocol"]) == (row.dataset, row.protocol)
        y = np.asarray(pred["y_true"])
        n = len(y)
        assert len(pred["test_indices"]) == len(set(pred["test_indices"])) == pred["n_test_samples"] == n
        values = {}
        for name, column, expected in [
            ("conditional", "y_pred_adaptive_cascade", row.new_f1),
            ("direct", "y_pred_topk_direct", row.topk_f1),
            ("resnet", "y_pred_resnet50_cascade", row.resnet_f1),
        ]:
            p = np.asarray(pred[column])
            assert len(p) == n
            f1 = float(f1_score(y, p, labels=np.unique(y), average="macro", zero_division=0))
            assert np.isclose(f1, expected, atol=1e-12, rtol=0), (stem, name)
            values[name + "_f1"] = f1
            values[name + "_accuracy"] = float(accuracy_score(y, p))
        req = np.asarray(pred["requested_topk_adaptive"], dtype=bool)
        assert len(req) == n
        assert np.isclose(req.mean(), result["selected_cheap_stage"]["request_fraction"], atol=1e-12, rtol=0)
        assert pretest["selected_cheap_stage"]["selected"]["route"] == result["selected_cheap_stage"]["route"]
        archive_path = Path(result["source_archive"]["path"])
        assert digest(archive_path) == result["source_archive"]["sha256"]
        source(archive_path.relative_to(ROOT.resolve()))
        archive = json.loads(archive_path.read_text())
        assert result["topk_blocks"] == archive["expensive_blocks"]
        p_direct = np.asarray(pred["y_pred_topk_direct"])
        p_cond = np.asarray(pred["y_pred_adaptive_cascade"])
        assert np.array_equal(p_cond[req], p_direct[req])
        if row.new_route == "topk_direct":
            assert req.all() and np.array_equal(p_cond, p_direct)
        audited.append({"dataset": row.dataset, "protocol": row.protocol,
            "n_test": n, "k": len(result["topk_blocks"]), "route": row.new_route,
            "base": None if pd.isna(row.new_cheap) else row.new_cheap,
            "request_fraction": float(req.mean()), "direct_projected_ms": float(row.topk_ms),
            "conditional_projected_ms": float(row.new_ms),
            "corrected_vs_direct": int(((p_cond == y) & (p_direct != y)).sum()),
            "harmed_vs_direct": int(((p_cond != y) & (p_direct == y)).sum()),
            "changed_predictions": int((p_cond != p_direct).sum()), **values})

    reference = pd.read_csv(source("results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv"))
    external = reference[reference.classifier.eq("svm") & reference.local_method.eq("Top-4")].copy()
    assert len(external) == 23  # DeepLumina/DTD has no complete dataset mean.
    for ds in ORDER:
        group = external[external.dataset.eq(ds)]
        assert group.local_mean_split_f1.nunique() == group.local_mean_ms.nunique() == 1

    audit_dir.mkdir(parents=True)
    generated.mkdir(parents=True, exist_ok=False)
    curve_frame, top4_frame, cascade_frame = map(pd.DataFrame, (curves, top4_rows, audited))
    for name, frame in [("curves.csv", curve_frame), ("top4_by_dataset.csv", top4_frame),
                        ("paired_cascade_audit.csv", cascade_frame), ("external_top4.csv", external)]:
        frame.to_csv(audit_dir / name, index=False)
    summary = {"status": "ANALYZED", "title": "Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen",
        "date": "2026-11-13", "new_fits": 0, "new_predictions": 0, "new_timings": 0,
        "classifiers": classifier_summaries, "paired_cascade_conditions": len(audited),
        "paired_test_observations": sum(r["n_test"] for r in audited),
        "replayed_routes": cascade_frame.route.value_counts().to_dict(),
        "coverage_scope": "exploratory historical archives; cascade k inherited from GFS, not fixed k=4",
        "kth_reserved": True, "deeplumina_requires_review": True, "source_sha256": sources}
    (audit_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n")

    selected = [1, 2, 3, 4, 5, 10, 21]
    curve_rows = []
    for k in selected:
        a = curve_frame[curve_frame.k.eq(k)].set_index("classifier")
        curve_rows.append([k, number(a.loc["svm", "macro_f1"], 6), number(a.loc["resmlp", "macro_f1"], 6),
                           number(a.loc["svm", "pct_dimensions_vs_21"], 2)])
    (generated / "curva_k.tex").write_text(table(
        "Barrido exploratorio ampliado: medias equiponderadas de seis datasets, con 47 condiciones por tamaño y clasificador.",
        "tab:tm-curva", ["k", "Macro-F1 SVM", "Macro-F1 ResMLP", r"\% dimensiones SVM"], curve_rows,
        "La referencia dimensional son los 21 bloques del barrido, sin N-gramas. El máximo observado no es un tamaño óptimo confirmado."))
    for clf in ("svm", "resmlp"):
        rs = []
        for ds in ORDER:
            r = top4_frame[top4_frame.classifier.eq(clf) & top4_frame.dataset.eq(ds)].iloc[0]
            rs.append([PRETTY[ds], int(r.conditions), number(r.top4), number(r.full21), number(r.full22), number(r.top4-r.full22)])
        (generated / f"top4_{clf}.tex").write_text(table(
            f"Top-4 y concatenaciones completas en el archivo exploratorio ({'SVM' if clf=='svm' else 'ResMLP'}).",
            f"tab:tm-top4-{clf}", ["Dataset", "Cond.", "Top-4", "21 sin Ng", "22 con Ng", r"$\Delta$ a 22"], rs,
            "Top-4 selecciona cuatro bloques de la biblioteca sin N-gramas. Los resultados KTH conservan su variante archivada. Esta tabla no es el panel online."))

    means = cascade_frame.groupby("dataset").mean(numeric_only=True)
    rs = []
    for ds in ORDER:
        r = means.loc[ds]
        ks = sorted(set(cascade_frame.loc[cascade_frame.dataset.eq(ds), "k"].astype(int)))
        rs.append([PRETTY[ds], "/".join(map(str, ks)), number(r.direct_f1), number(r.conditional_f1),
                   number(r.conditional_f1-r.direct_f1), number(100*r.request_fraction, 1)])
    (generated / "cascada_calidad.tex").write_text(table(
        "Uso directo y activación por margen del mismo Top-k: auditoría de las 27 condiciones guardadas, SVM.",
        "tab:tm-cascada", ["Dataset", "k observados", "Directo F1", "Margen F1", r"$\Delta$ F1", r"Rescate \%"], rs,
        "Se conserva el Top-k específico de cada condición; k no es siempre cuatro. KTH mantiene la reserva de procedencia y no integra inferencia conjunta. La tasa incluye Top-k directo cuando esa fue la ruta seleccionada."))
    rs = []
    for ds in ORDER:
        r = means.loc[ds]
        rs.append([PRETTY[ds], number(r.direct_projected_ms, 2), number(r.conditional_projected_ms, 2),
                   number(100*(1-r.conditional_projected_ms/r.direct_projected_ms), 1)])
    (generated / "cascada_costos.tex").write_text(table(
        "Costos de extracción proyectados de las rutas históricas. No son latencias online por dataset.",
        "tab:tm-costos", ["Dataset", "Directo (ms)", "Margen (ms)", r"Reducción \%"], rs,
        "Cociente de medias por dataset; perfiles históricos por componente. No incluye una nueva medición física ni valida las discrepancias de representación."))

    for metric, field, own in [("f1", "reference_mean_split_f1", "local_mean_split_f1"),
                               ("ms", "reference_mean_ms", "local_mean_ms")]:
        rs = []
        for ds in ORDER:
            g = external[external.dataset.eq(ds)].set_index("reference_method")
            row = [PRETTY[ds], number(g.iloc[0][own], 4 if metric=="f1" else 2)]
            for method in ("Neshov", "HyTex", "CellNN", "DeepLumina"):
                row.append(number(g.loc[method, field], 4 if metric=="f1" else 2) + (r"$^\dagger$" if method=="DeepLumina" else "") if method in g.index else "incompleto")
            rs.append(row)
        caption = ("Macro-F1 de Top-4/SVM y adaptaciones externas en el panel online auditado." if metric=="f1" else
                   "Latencia media observada por imagen (ms) de las mismas llamadas que sustentan la tabla de macro-F1.")
        (generated / f"externos_{metric}.tex").write_text(table(caption, f"tab:tm-externos-{metric}",
            ["Dataset", "Top-4", "Neshov", "HyTex", "CellNN", "DeepLumina"], rs,
            r"$^\dagger$ DeepLumina conserva avisos de no convergencia; DTD no tiene media completa. Los tiempos de métodos distintos provienen de fechas/estados de hardware diferentes y son descriptivos. KTH y DTD conservan sus reservas físicas/protocolares.", size=8))

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    for clf, color, marker in [("svm", "#126e82", "o"), ("resmlp", "#a94d25", "s")]:
        g = curve_frame[curve_frame.classifier.eq(clf)]
        axes[0].plot(g.k, g.macro_f1, marker=marker, markersize=3, color=color, label=clf.upper())
        axes[1].plot(g.pct_dimensions_vs_21, g.macro_f1, marker=marker, markersize=3, color=color, label=clf.upper())
        point = g[g.k.eq(4)].iloc[0]
        axes[0].scatter([4], [point.macro_f1], s=85, facecolors="none", edgecolors=color, linewidths=1.8)
        axes[1].scatter([point.pct_dimensions_vs_21], [point.macro_f1], s=85, facecolors="none", edgecolors=color, linewidths=1.8)
    axes[0].set(xlabel="Número de bloques k", ylabel="Macro-F1 medio por dataset", xticks=[1,4,8,12,16,21])
    axes[1].set(xlabel="Dimensiones respecto de 21 bloques (%)", ylabel="Macro-F1 medio por dataset")
    for ax in axes:
        ax.grid(alpha=.2); ax.legend(frameon=False)
    fig.savefig(generated / "curva_k.pdf"); fig.savefig(generated / "curva_k.png", dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), constrained_layout=True)
    for ax, field, xlabel in [(axes[0], "direct_f1", "Top-k directo: macro-F1"),
                               (axes[1], "direct_projected_ms", "Top-k directo: costo proyectado (ms)")]:
        target = "conditional_f1" if field=="direct_f1" else "conditional_projected_ms"
        xs, ys = means.loc[ORDER,field].to_numpy(), means.loc[ORDER,target].to_numpy()
        ax.scatter(xs,ys,color="#126e82",s=38)
        offsets = ({"DTD": (7, -12), "SoilOriginal": (7, 8),
                    "Outex13Official1360": (7, -12)} if field == "direct_f1" else
                   {"DTD": (6, 17), "CUReT": (6, -16), "Outex13Official1360": (8, 0),
                    "FMD": (-18, -18), "SoilOriginal": (-20, 12), "KTHTIPS2b": (-36, -18)})
        for ds,x,y in zip(ORDER,xs,ys):
            ax.annotate(PRETTY[ds], (x,y), xytext=offsets.get(ds,(5,6)),
                        textcoords="offset points", fontsize=8)
        lo,hi=min(xs.min(),ys.min()),max(xs.max(),ys.max())
        padding=max((hi-lo)*.16, .006 if field=="direct_f1" else 10)
        ax.plot([lo-padding,hi+padding],[lo-padding,hi+padding],ls="--",color=".6",lw=1)
        ax.set(xlabel=xlabel,ylabel="Margen: macro-F1" if field=="direct_f1" else "Margen: costo proyectado (ms)",xlim=(lo-padding,hi+padding),ylim=(lo-padding,hi+padding))
        ax.grid(alpha=.2)
    fig.savefig(generated / "directo_margen.pdf"); fig.savefig(generated / "directo_margen.png",dpi=170); plt.close(fig)
    provenance={"audit_summary_sha256":digest(audit_dir/'summary.json'),"source_sha256":sources,
                "generated_sha256":{p.name:digest(p) for p in sorted(generated.iterdir())}}
    (generated/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({"status":"ANALYZED","curves":len(curves),"paired_conditions":len(audited),"sources":len(sources),
                      "audit":str(audit_dir.relative_to(ROOT)),"generated":str(generated.relative_to(ROOT))}))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit",type=Path,default=ROOT/'results/analysis/topk_margin_rewrite_20261113_v1')
    parser.add_argument("--generated",type=Path,default=ROOT/'paper/generated_topk_margin')
    args=parser.parse_args()
    build(args.audit.resolve(),args.generated.resolve())
