#!/usr/bin/env python3
"""Rebuild the primary 20-descriptor analysis with SoilOriginal included.

Every dataset uses the same 20 frozen descriptor blocks.  SoilOriginal is
therefore a primary dataset, not an appendix or a separately pooled fold.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/articulo/borrador_profesor/generated"
NP_OUT = ROOT / "results/primary20_soil/nonparametric"
SOURCES = [
    ROOT / "results/confirmatory",
    ROOT / "results/extensions/outex13_official1360",
    ROOT / "results/extensions/soil_original",
]
DATASETS = ["DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal"]
COUNTS = {"DTD": 10, "FMD": 15, "CUReT": 2, "Outex13Official1360": 1, "SoilOriginal": 15}
METHODS = ["best_individual", "full_concat", "topk_individual", "gfs", "homogeneous"]
LABELS = ["Individual", "Completa", r"Top-$k$", "GFS", "Homogénea"]


def display_dataset(name: str) -> str:
    return {"Outex13Official1360": "Outex", "SoilOriginal": "Soil"}.get(name, name)


def number(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}".replace(".", "{,}")


def load() -> pd.DataFrame:
    parts = []
    for source in SOURCES:
        parts += [
            pd.read_csv(source / "nested_fold_results.csv"),
            pd.read_csv(source / "topk_individual_control/nested_fold_results.csv"),
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
                    if COUNTS[dataset] > 1:
                        cell += r"\,\pm\," + number(summary.loc[(dataset, classifier, method), (metric, "std")])
                    cells.append("$" + cell + "$")
                rows.append(" & ".join([display_dataset(dataset), "SVM" if classifier == "svm" else "ResMLP", *cells]))
        tex_table(filename, title + " de cinco estrategias con la biblioteca común de 20 descriptores. Media y desviación estándar entre particiones; Outex tiene un único split.", label, "llccccc", "Dataset & Clasif. & " + " & ".join(LABELS), rows)
    rows = []
    for dataset in DATASETS:
        for classifier in ("svm", "resmlp"):
            cells = [number(summary.loc[(dataset, classifier, method), ("dimensions", "mean")], 1) for method in METHODS]
            rows.append(" & ".join([display_dataset(dataset), "SVM" if classifier == "svm" else "ResMLP", *["$" + cell + "$" for cell in cells]]))
    tex_table("dimensions_primary.tex", "Dimensión media de las representaciones usadas para la evaluación externa con 20 descriptores.", "tab:dimensiones", "llrrrrr", "Dataset & Clasif. & " + " & ".join(LABELS), rows)

    means = df.groupby(["dataset", "classifier", "method"]).macro_f1.mean().unstack("method")[METHODS]
    primary = means.groupby(level="dataset").mean().loc[DATASETS]
    named = primary.rename(columns=dict(zip(METHODS, LABELS)))
    named.insert(0, "Data-set", [display_dataset(dataset) for dataset in named.index])
    named.to_csv(NP_OUT / "primary_by_dataset.csv", index=False, float_format="%.12f")
    values = primary.to_numpy()
    statistic, p_value = friedmanchisquare(*[values[:, index] for index in range(values.shape[1])])
    ranks = np.vstack([rankdata(-row, method="average") for row in values]).mean(axis=0)
    stat_rows = [" & ".join([label, "$" + number(rank, 3) + "$"]) for label, rank in zip(LABELS, ranks)]
    tex_table("rankings_primary.tex", "Rankings medios de Friedman en macro-F1, con un bloque por cada uno de los cinco datasets. Menor ranking indica mejor desempeño relativo.", "tab:friedman-primary", "lr", "Estrategia & Ranking", stat_rows)
    tex_table("global_primary.tex", "Contraste global de Friedman para la biblioteca común de 20 descriptores y cinco datasets.", "tab:global-primary", "lrrl", "Prueba & Estadístico & $p$ & Decisión ($\\alpha=0{,}05$)", ["Friedman & $" + number(statistic) + "$ & $" + number(p_value) + "$ & " + ("No rechazo" if p_value >= .05 else "Rechazo")])
    df.to_csv(OUT / "primary20_soil_source_rows.csv", index=False)
    (NP_OUT / "validation.json").write_text(json.dumps({"library_size": 20, "datasets": [display_dataset(d) for d in DATASETS], "conditions_per_classifier": sum(COUNTS.values()), "friedman_chi_square": statistic, "friedman_p": p_value, "mean_ranks": dict(zip(LABELS, ranks))}, indent=2), encoding="utf-8")
    print(f"Validated {len(df)} result rows across five primary datasets.")


if __name__ == "__main__":
    main()
