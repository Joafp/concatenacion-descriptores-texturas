#!/usr/bin/env python3
"""Rebuild the primary 21-descriptor analysis with SoilOriginal and KTH-TIPS2-b.

Every dataset uses the same 21 descriptor blocks, including RGB N-grams + SVD. SoilOriginal is
therefore a primary dataset, not an appendix or a separately pooled fold.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata, wilcoxon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/articulo/borrador_profesor/generated"
NP_OUT = ROOT / "results/primary20_soil/nonparametric"
SOURCES = [
    (ROOT / "results/confirmatory/ngram21", ROOT / "results/confirmatory/ngram21/topk_individual_control"),
    (ROOT / "results/extensions/outex13_official1360/ngram21", ROOT / "results/extensions/outex13_official1360/ngram21/topk_individual_control"),
    (ROOT / "results/extensions/soil_original/ngram21", ROOT / "results/extensions/soil_original/ngram21/topk_individual_control"),
    (
        ROOT / "results/extensions/kth_tips2b/ngram21_radam_3train",
        ROOT / "results/extensions/kth_tips2b/ngram21_radam_3train/topk_individual_control",
    ),
]
DATASETS = ["DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"]
COUNTS = {"DTD": 10, "FMD": 15, "CUReT": 2, "Outex13Official1360": 1, "SoilOriginal": 15, "KTHTIPS2b": 4}
METHODS = ["best_individual", "full_concat", "topk_individual", "gfs", "homogeneous"]
LABELS = ["Individual", "Completa", r"Top-$k$", "GFS", "Homogénea"]


def display_dataset(name: str) -> str:
    return {"Outex13Official1360": "Outex", "SoilOriginal": "Soil", "KTHTIPS2b": "KTH-TIPS2-b"}.get(name, name)


def number(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}".replace(".", "{,}")


def load() -> pd.DataFrame:
    parts = []
    for source, topk_source in SOURCES:
        parts += [
            pd.read_csv(source / "nested_fold_results.csv"),
            pd.read_csv(topk_source / "nested_fold_results.csv"),
        ]
    df = pd.concat(parts, ignore_index=True)
    df["method"] = df["method"].str.replace(r"^best_homogeneous_.*", "homogeneous", regex=True)
    df = df[df.dataset.isin(DATASETS)].copy()
    keys = ["dataset", "classifier", "seed", "outer_fold", "method"]
    if df.duplicated(keys).any():
        raise RuntimeError("Duplicate external condition in primary matrix")
    for dataset in DATASETS:
        for classifier in ("svm", "resmlp"):
            rows = df[(df.dataset == dataset) & (df.classifier == classifier)]
            expected = {method: COUNTS[dataset] for method in METHODS}
            if rows.groupby("method").size().to_dict() != expected:
                raise RuntimeError(f"Incomplete {dataset}/{classifier}: {rows.groupby('method').size().to_dict()}")
    return df


def tex_table(filename: str, caption: str, label: str, columns: str, header: str, rows: list[str]) -> None:
    content = "\n".join([
        r"\begin{resulttable}", r"\centering\fontsize{8}{10}\selectfont\setlength{\tabcolsep}{3.0pt}",
        f"\\caption{{{caption}}}", f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{@{{}}{columns}@{{}}}}", r"\toprule", header + r" \\", r"\midrule",
        *[row + r" \\" for row in rows], r"\bottomrule", r"\end{tabular}", r"\end{resulttable}", r"\FloatBarrier", "",
    ])
    (OUT / filename).write_text(content, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    NP_OUT.mkdir(parents=True, exist_ok=True)
    df = load()
    summary = df.groupby(["dataset", "classifier", "method"])[["macro_f1", "accuracy", "dimensions"]].agg(["mean", "std"])
    for metric, filename, label, title in [
        ("macro_f1", "baseline_f1.tex", "tab:resultados-confirmatorios", "Macro-F1 externo"),
        ("accuracy", "baseline_accuracy.tex", "tab:accuracy", "Exactitud externa"),
    ]:
        rows = []
        for dataset in DATASETS:
            for classifier in ("svm", "resmlp"):
                vals = [summary.loc[(dataset, classifier, method), (metric, "mean")] for method in METHODS]
                cells = []
                for method, value in zip(METHODS, vals):
                    cell = number(value)
                    if value == max(vals):
                        cell = r"\mathbf{" + cell + "}"
                    cells.append("$" + cell + "$")
                rows.append(" & ".join([display_dataset(dataset), "SVM" if classifier == "svm" else "ResMLP", *cells]))
        tex_table(filename, title + " de cinco estrategias con la biblioteca común de 21 descriptores, incluido RGB N-grams + SVD. Se presenta la media externa por condición; Outex usa un único split oficial.", label, "llccccc", "Dataset & Clasif. & " + " & ".join(LABELS), rows)
    rows = []
    for dataset in DATASETS:
        for classifier in ("svm", "resmlp"):
            cells = [number(summary.loc[(dataset, classifier, method), ("dimensions", "mean")], 1) for method in METHODS]
            rows.append(" & ".join([display_dataset(dataset), "SVM" if classifier == "svm" else "ResMLP", *["$" + cell + "$" for cell in cells]]))
    tex_table("dimensions_primary.tex", "Dimensión media de las representaciones usadas para la evaluación externa con 21 descriptores.", "tab:dimensiones", "llrrrrr", "Dataset & Clasif. & " + " & ".join(LABELS), rows)

    means = df.groupby(["dataset", "classifier", "method"]).macro_f1.mean().unstack("method")[METHODS]
    primary = means.groupby(level="dataset").mean().loc[DATASETS]
    named = primary.rename(columns=dict(zip(METHODS, LABELS)))
    named.insert(0, "Data-set", [display_dataset(dataset) for dataset in named.index])
    named.to_csv(NP_OUT / "primary_by_dataset.csv", index=False, float_format="%.12f")
    values = primary.to_numpy()
    statistic, p_value = friedmanchisquare(*[values[:, index] for index in range(values.shape[1])])
    ranks = np.vstack([rankdata(-row, method="average") for row in values]).mean(axis=0)
    stat_rows = [" & ".join([label, "$" + number(rank, 3) + "$"]) for label, rank in zip(LABELS, ranks)]
    tex_table("rankings_primary.tex", "Rankings medios de Friedman en macro-F1, con un bloque por cada uno de los seis datasets. Menor ranking indica mejor desempeño relativo.", "tab:friedman-primary", "lr", "Estrategia & Ranking", stat_rows)
    tex_table("global_primary.tex", "Contraste global de Friedman para la biblioteca común de 21 descriptores y seis datasets.", "tab:global-primary", "lrrl", "Prueba & Estadístico & $p$ & Decisión ($\\alpha=0{,}05$)", ["Friedman & $" + number(statistic) + "$ & $" + number(p_value) + "$ & " + ("No rechazo" if p_value >= .05 else "Rechazo")])

    # Planned classifier-specific contrasts.  A classifier is never averaged
    # with the other one: each dataset contributes exactly one paired block.
    comparisons = []
    for classifier, display in (("svm", "SVM"), ("resmlp", "ResMLP")):
        by_dataset = (df[df.classifier.eq(classifier)]
                      .groupby(["dataset", "method"]).macro_f1.mean()
                      .unstack("method")[METHODS].loc[DATASETS])
        delta = by_dataset["full_concat"] - by_dataset["best_individual"]
        _, contrast_p = wilcoxon(delta, alternative="greater", method="exact")
        comparisons.append((
            f"Completa -- Individual ({display})", delta.mean(),
            f"{int((delta > 0).sum())}--{int((delta < 0).sum())}", contrast_p,
            "Rechazo" if contrast_p < .05 else "No rechazo",
        ))
    resmlp = (df[df.classifier.eq("resmlp")].groupby(["dataset", "method"])
              .macro_f1.mean().unstack("method").loc[DATASETS, "full_concat"])
    svm = (df[df.classifier.eq("svm")].groupby(["dataset", "method"])
           .macro_f1.mean().unstack("method").loc[DATASETS, "full_concat"])
    delta = resmlp - svm
    _, contrast_p = wilcoxon(delta, alternative="two-sided", method="exact")
    comparisons.append((
        "ResMLP -- SVM (Completa)", delta.mean(),
        f"{int((delta > 0).sum())}--{int((delta < 0).sum())}", contrast_p,
        "Rechazo" if contrast_p < .05 else "No rechazo",
    ))
    comparison_rows = [
        " & ".join([name, "$" + number(delta) + "$", wins_losses,
                      "$" + number(p, 4) + "$", decision])
        for name, delta, wins_losses, p, decision in comparisons
    ]
    tex_table("classifier_contrasts.tex",
              "Contrastes pareados de macro-F1 por clasificador, con un bloque por dataset. Completa--Individual usa Wilcoxon exacto unilateral ($H_1$: Completa $>$ Individual); ResMLP--SVM usa prueba bilateral.",
              "tab:classifier-contrasts", "lrrrr",
              "Contraste & $\\Delta$ medio & V--D & $p$ & Decisión", comparison_rows)

    # SCI2S/Java audit: one valid dataset-level matrix for each classifier.
    # These outputs are kept as raw, reproducible supplementary evidence; they
    # are not pooled because SVM and ResMLP are trained on the same datasets.
    sci2s_dir = NP_OUT / "classifier_specific"
    sci2s_dir.mkdir(parents=True, exist_ok=True)
    java_root = ROOT / ".tools/nonparametric"
    for classifier in ("svm", "resmlp"):
        matrix = (df[df.classifier.eq(classifier)]
                  .groupby(["dataset", "method"]).macro_f1.mean()
                  .unstack("method")[METHODS].loc[DATASETS])
        java_input = matrix.rename(columns=dict(zip(METHODS, LABELS))).copy()
        java_input.insert(0, "Data-set", [display_dataset(dataset) for dataset in java_input.index])
        csv_path = sci2s_dir / f"{classifier}_by_dataset.csv"
        java_input.to_csv(csv_path, index=False, float_format="%.12f")
        for tool_name, suffix in (("controlTest", "controltest"), ("multipleTest", "multipletest")):
            result = subprocess.run(
                ["java", "Friedman", str(csv_path)], cwd=java_root / tool_name,
                capture_output=True, text=True, check=True,
            )
            if r"\end{document}" not in result.stdout:
                raise RuntimeError(f"SCI2S {tool_name} did not complete for {classifier}")
            (sci2s_dir / f"{classifier}_{suffix}.tex").write_text(result.stdout, encoding="utf-8")
    df.to_csv(OUT / "primary21_soil_source_rows.csv", index=False)

    # KTH-TIPS2-b extension under the same RADAM 3-train/1-test protocol.
    # BEiTv2 is kept outside the common 21-descriptor comparison: adding it
    # creates a 22-block ablation and must not silently redefine the primary
    # library used by the other five datasets.
    beit_path = ROOT / "results/extensions/kth_tips2b/beitv2_full_concat_radam_3train/nested_fold_results.csv"
    beit = pd.read_csv(beit_path)
    if len(beit) != 16 or beit.duplicated(["classifier", "outer_fold", "method"]).any():
        raise RuntimeError("Incomplete or duplicated KTH-TIPS2-b BEiTv2 extension")
    kth_base = df[(df.dataset == "KTHTIPS2b") & (df.method == "full_concat")].copy()
    extension = pd.concat([
        kth_base.assign(variant="Completa-21"),
        beit.assign(variant=beit.method.map({
            "full21_plus_beitv2_base_final": "Completa-21 + BEiTv2 final",
            "full21_plus_beitv2_base_multilayer": "Completa-21 + BEiTv2 multicapas",
        })),
    ], ignore_index=True)
    extension.to_csv(OUT / "kth_beit_extension_source_rows.csv", index=False)
    ext_summary = extension.groupby(["classifier", "variant"])[["macro_f1", "accuracy", "dimensions"]].agg(["mean", "std"])
    extension_rows = []
    variant_order = ["Completa-21", "Completa-21 + BEiTv2 final", "Completa-21 + BEiTv2 multicapas"]
    for classifier, display in (("svm", "SVM"), ("resmlp", "ResMLP")):
        base_f1 = ext_summary.loc[(classifier, "Completa-21"), ("macro_f1", "mean")]
        for variant in variant_order:
            mean_f1 = ext_summary.loc[(classifier, variant), ("macro_f1", "mean")]
            std_f1 = ext_summary.loc[(classifier, variant), ("macro_f1", "std")]
            mean_acc = ext_summary.loc[(classifier, variant), ("accuracy", "mean")]
            std_acc = ext_summary.loc[(classifier, variant), ("accuracy", "std")]
            dims = int(round(ext_summary.loc[(classifier, variant), ("dimensions", "mean")]))
            extension_rows.append(" & ".join([
                display,
                variant,
                f"${number(mean_f1)} \\pm {number(std_f1)}$",
                f"${number(mean_acc)} \\pm {number(std_acc)}$",
                f"${number(mean_f1 - base_f1)}$",
                f"${dims}$",
            ]))
    tex_table(
        "kth_beit_extension.tex",
        "Ablación externa en KTH-TIPS2-b con el protocolo de tres muestras físicas para entrenamiento y una para prueba. BEiTv2 se agrega como bloque 22 a Completa-21; la dispersión es la desviación estándar entre las cuatro particiones.",
        "tab:kth-beit-extension", "llrrrr",
        "Clasif. & Representación & Macro-F1 & Exactitud & $\\Delta$ F1 vs. 21 & Dim.",
        extension_rows,
    )
    (NP_OUT / "validation.json").write_text(json.dumps({"library_size": 21, "datasets": [display_dataset(d) for d in DATASETS], "conditions_per_classifier": sum(COUNTS.values()), "friedman_chi_square": statistic, "friedman_p": p_value, "mean_ranks": dict(zip(LABELS, ranks))}, indent=2), encoding="utf-8")
    print(f"Validated {len(df)} result rows across six primary datasets.")


if __name__ == "__main__":
    main()
