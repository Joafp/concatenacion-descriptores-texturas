#!/usr/bin/env python3
"""Build the final 22-descriptor paper tables and statistical audit.

The matrix contains the same five strategies for 47 external conditions per
classifier across DTD, FMD, CUReT, Outex, Soil and KTH-TIPS2-b.  SCI2S is run
separately for SVM and ResMLP, with one block per dataset.
"""
from __future__ import annotations

import json
import re
import subprocess
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/articulo/borrador_profesor/generated"
NP_OUT = ROOT / "results/primary22_beitv2/nonparametric"
SOURCES_22 = [
    ROOT / "results/confirmatory/ngram22_beitv2",
    ROOT / "results/extensions/outex13_official1360/ngram22_beitv2",
    ROOT / "results/extensions/soil_original/ngram22_beitv2",
    ROOT / "results/extensions/kth_tips2b/ngram22_beitv2",
]
SOURCES_21 = [
    ROOT / "results/confirmatory/ngram21",
    ROOT / "results/extensions/outex13_official1360/ngram21",
    ROOT / "results/extensions/soil_original/ngram21",
    ROOT / "results/extensions/kth_tips2b/ngram21_radam_3train",
]
DATASETS = ["DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"]
COUNTS = {"DTD": 10, "FMD": 15, "CUReT": 2, "Outex13Official1360": 1,
          "SoilOriginal": 15, "KTHTIPS2b": 4}
METHODS = ["best_individual", "full_concat", "topk_individual", "gfs", "homogeneous"]
LABELS = ["Individual", "Completa", r"Top-$k$", "GFS", "Homogénea"]
DESCRIPTOR_LABELS = {
    "beitv2_base_final": "BEiTv2-B",
    "rgb_ngram_svd": "RGB N-gramas + SVD",
    "dinov2_large": "DINOv2-L",
    "dinov2_small": "DINOv2-S",
    "siglip_base": "SigLIP-B",
    "eva02_base": "EVA-02 base",
    "convnext_v2_t": "ConvNeXt V2-T",
    "mae_base": "MAE-B",
    "vit_b16": "ViT-B/16",
    "swin_t": "Swin-T",
}


def display_dataset(name: str) -> str:
    return {"Outex13Official1360": "Outex", "SoilOriginal": "Soil",
            "KTHTIPS2b": "KTH-TIPS2-b"}.get(name, name)


def number(value: float, digits: int = 4) -> str:
    if abs(value) < 0.5 * 10 ** (-digits):
        value = 0.0
    return f"{value:.{digits}f}".replace(".", "{,}")


def tex_text(value: str) -> str:
    """Escape descriptor identifiers that are emitted as ordinary LaTeX text."""
    return value.replace("\\", r"\textbackslash{}").replace("_", r"\_")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tex_table(filename: str, caption: str, label: str, columns: str,
              header: str, rows: list[str], note: str = "") -> None:
    content = [
        r"\begin{resulttable}",
        r"\centering\fontsize{8}{10}\selectfont\setlength{\tabcolsep}{3.0pt}",
        f"\\caption{{{caption}}}", f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{@{{}}{columns}@{{}}}}", r"\toprule",
        header + r" \\", r"\midrule",
        *[row + r" \\" for row in rows],
        r"\bottomrule", r"\end{tabular}",
    ]
    if note:
        content.append(r"\par\smallskip{\footnotesize " + note + "}")
    content += [r"\end{resulttable}", r"\FloatBarrier", ""]
    (OUT / filename).write_text("\n".join(content), encoding="utf-8")


def load_sources(sources: list[Path], library_size: int) -> pd.DataFrame:
    chunks = []
    for source in sources:
        chunks.append(pd.read_csv(source / "nested_fold_results.csv"))
        chunks.append(pd.read_csv(source / "topk_individual_control/nested_fold_results.csv"))
    df = pd.concat(chunks, ignore_index=True)
    df["method"] = df.method.str.replace(r"^best_homogeneous_.*", "homogeneous", regex=True)
    df = df[df.dataset.isin(DATASETS)].copy()
    keys = ["dataset", "classifier", "seed", "outer_fold", "method"]
    if df.duplicated(keys).any():
        raise RuntimeError("duplicate external condition/method")
    numeric = df[["macro_f1", "accuracy", "dimensions", "k"]].to_numpy()
    if not np.isfinite(numeric).all():
        raise RuntimeError("non-finite required metric")
    for dataset in DATASETS:
        for classifier in ("svm", "resmlp"):
            rows = df[(df.dataset == dataset) & (df.classifier == classifier)]
            expected = {method: COUNTS[dataset] for method in METHODS}
            actual = rows.groupby("method").size().to_dict()
            if actual != expected:
                raise RuntimeError(f"incomplete {dataset}/{classifier}: {actual}")
            full = rows[rows.method == "full_concat"]
            if not full.k.eq(library_size).all():
                raise RuntimeError(f"wrong library size in {dataset}/{classifier}")
    return df


def parse_java(control: str, multiple: str) -> tuple[dict, dict, list[tuple[str, float, float]]]:
    rankings = {}
    globals_ = {}
    for test in ("Friedman", "Aligned Friedman", "Quade"):
        chunk = control.split(f"Average Rankings of the algorithms ({test})")[1].split(r"\end{tabular}")[0]
        rankings[test] = {name.strip(): float(value) for name, value in
                          re.findall(r"^([^&\n]+)&([0-9.]+)\\\\", chunk, re.M)}
        globals_[test] = float(re.search(r"P-value computed by " + test +
                                         r" Test: ([0-9.Ee+-]+)", control)[1].rstrip("."))
    globals_["Iman--Davenport"] = float(re.search(
        r"P-value computed by Iman and Daveport Test: ([0-9.Ee+-]+)", control
    )[1].rstrip("."))
    pairs = []
    body = multiple.split("i&hypothesis&unadjusted")[1]
    for line in body.splitlines():
        fields = line.rstrip("\\").split("&")
        if len(fields) == 7 and fields[0].isdigit():
            pairs.append((fields[1].replace("vs .", "vs. "), float(fields[2]), min(1.0, float(fields[4]))))
    if len(pairs) != 10:
        raise RuntimeError("SCI2S did not return ten pairwise comparisons")
    return rankings, globals_, pairs


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    NP_OUT.mkdir(parents=True, exist_ok=True)
    df = load_sources(SOURCES_22, 22)
    old = load_sources(SOURCES_21, 21)
    condition_keys = ["dataset", "classifier", "seed", "outer_fold"]
    old_full_keys = set(map(tuple, old.loc[old.method == "full_concat", condition_keys].to_numpy()))
    new_full_keys = set(map(tuple, df.loc[df.method == "full_concat", condition_keys].to_numpy()))
    if old_full_keys != new_full_keys:
        raise RuntimeError("21- and 22-descriptor full concatenations use different external conditions")
    summary = df.groupby(["dataset", "classifier", "method"])[
        ["macro_f1", "accuracy", "dimensions", "k"]].agg(["mean", "std"])

    for metric, filename, label, title in [
        ("macro_f1", "baseline_f1.tex", "tab:resultados-confirmatorios", "Macro-F1 externo"),
        ("accuracy", "baseline_accuracy.tex", "tab:accuracy", "Exactitud externa"),
    ]:
        rows = []
        for dataset in DATASETS:
            for classifier in ("svm", "resmlp"):
                values = [summary.loc[(dataset, classifier, method), (metric, "mean")] for method in METHODS]
                cells = []
                for value in values:
                    cell = number(value)
                    if np.isclose(value, max(values), rtol=0, atol=5e-8):
                        cell = r"\mathbf{" + cell + "}"
                    cells.append("$" + cell + "$")
                rows.append(" & ".join([display_dataset(dataset),
                                        "SVM" if classifier == "svm" else "ResMLP", *cells]))
        tex_table(filename,
                  title + " de cinco estrategias con la biblioteca común de 22 descriptores, incluidos RGB N-gramas + SVD y BEiTv2-B. Se muestran medias entre condiciones externas; Outex tiene un único split oficial.",
                  label, "llccccc", "Dataset & Clasif. & " + " & ".join(LABELS), rows)

    rows = []
    for dataset in DATASETS:
        for classifier in ("svm", "resmlp"):
            cells = [number(summary.loc[(dataset, classifier, method), ("dimensions", "mean")], 1)
                     for method in METHODS]
            rows.append(" & ".join([display_dataset(dataset),
                                    "SVM" if classifier == "svm" else "ResMLP",
                                    *["$" + cell + "$" for cell in cells]]))
    tex_table("dimensions_primary.tex",
              "Dimensión media de las representaciones usadas en la evaluación externa con 22 descriptores.",
              "tab:dimensiones", "llrrrrr", "Dataset & Clasif. & " + " & ".join(LABELS), rows,
              "Completa tiene siempre 20.652 coordenadas; las otras estrategias pueden elegir subconjuntos distintos entre particiones.")

    identity_rows = []
    for dataset in DATASETS:
        for classifier in ("svm", "resmlp"):
            x = df[(df.dataset == dataset) & (df.classifier == classifier) &
                   (df.method == "best_individual")]
            selected = "; ".join(
                f"{tex_text(DESCRIPTOR_LABELS.get(name, name))} ({count}/{len(x)})"
                for name, count in x.selected.value_counts().items()
            )
            identity_rows.append(" & ".join([display_dataset(dataset),
                                             "SVM" if classifier == "svm" else "ResMLP", selected]))
    tex_table("individual_identity.tex",
              "Descriptor Individual seleccionado mediante validación interna. La frecuencia indica en cuántas condiciones externas fue elegido.",
              "tab:individual-identidad", "lll", "Dataset & Clasif. & Descriptor (frecuencia)", identity_rows)

    effect_rows = []
    effect_tests = {}
    old_full = old[old.method == "full_concat"].groupby(["dataset", "classifier"]).macro_f1.mean()
    new_full = df[df.method == "full_concat"].groupby(["dataset", "classifier"]).macro_f1.mean()
    for dataset in DATASETS:
        for classifier in ("svm", "resmlp"):
            before = old_full.loc[(dataset, classifier)]
            after = new_full.loc[(dataset, classifier)]
            effect_rows.append(" & ".join([display_dataset(dataset),
                                           "SVM" if classifier == "svm" else "ResMLP",
                                           "$" + number(before) + "$", "$" + number(after) + "$",
                                           "$" + number(after - before) + "$"]))
    for classifier in ("svm", "resmlp"):
        delta = (new_full.xs(classifier, level="classifier").loc[DATASETS] -
                 old_full.xs(classifier, level="classifier").loc[DATASETS])
        test = wilcoxon(delta, alternative="two-sided", method="exact")
        effect_tests[classifier] = {"mean_delta": float(delta.mean()), "statistic": float(test.statistic),
                                    "p": float(test.pvalue), "positive": int((delta > 0).sum())}
    tex_table("beitv2_effect.tex",
              "Efecto pareado de añadir BEiTv2-B a la concatenación completa: macro-F1 con 21 y 22 bloques sobre las mismas condiciones externas.",
              "tab:beitv2-effect", "llrrr", r"Dataset & Clasif. & Completa-21 & Completa-22 & $\Delta$", effect_rows,
              "Las diferencias son descriptivas por dataset. El contraste global exploratorio usa Wilcoxon exacto bilateral sobre seis medias emparejadas por clasificador.")

    # Descriptive literature comparison. Compare externally averaged
    # configurations, never the maximum score of one test fold. Soil is
    # excluded: the cited paper uses an augmented corpus and a fixed split.
    electronics = {"DTD": .820, "FMD": .967, "KTHTIPS2b": .968}
    jimaging = {"DTD": .791, "FMD": .909, "Outex13Official1360": .916, "KTHTIPS2b": .937}
    own_means = df.groupby(["dataset", "classifier", "method"]).accuracy.mean()
    own_best = own_means.groupby(level="dataset").max()
    literature_rows = []
    for dataset in ("DTD", "FMD", "Outex13Official1360", "KTHTIPS2b"):
        literature_rows.append(" & ".join([
            display_dataset(dataset),
            "$" + number(own_best.loc[dataset]) + "$",
            "---" if dataset not in electronics else "$" + number(electronics[dataset]) + "$",
            "---" if dataset not in jimaging else "$" + number(jimaging[dataset]) + "$",
        ]))
    tex_table("literature_comparison.tex",
              "Comparación descriptiva de exactitud media con BEiTv2 en los datasets compartidos. Este trabajo muestra el mayor promedio externo entre sus configuraciones; los otros valores proceden de Neshov et al. y Scabini et al.",
              "tab:literature-comparison", "lrrr",
              "Dataset & Este trabajo & Neshov et al. & Scabini et al.", literature_rows,
              "El mayor promedio del presente trabajo se identificó tras observar los tests externos, por lo que la tabla es sólo contextual. Los protocolos, clasificadores y agregaciones difieren; Scabini et al. promedian KNN, LDA y SVM. Soil se excluye porque el corpus y la partición de Neshov et al. son distintos.")

    sci2s_dir = NP_OUT / "classifier_specific"
    sci2s_dir.mkdir(parents=True, exist_ok=True)
    java_root = ROOT / ".tools/nonparametric"
    ranking_rows, global_rows, holm_rows = [], [], []
    sensitivity_rows = []
    complete_by_classifier = {}
    global_tests_by_classifier = {}
    for classifier, display in (("svm", "SVM"), ("resmlp", "ResMLP")):
        matrix = (df[df.classifier == classifier].groupby(["dataset", "method"]).macro_f1.mean()
                  .unstack("method")[METHODS].loc[DATASETS])
        complete_by_classifier[classifier] = matrix.full_concat
        java_input = matrix.rename(columns=dict(zip(METHODS, LABELS))).copy()
        java_input.insert(0, "Data-set", [display_dataset(dataset) for dataset in java_input.index])
        csv_path = sci2s_dir / f"{classifier}_by_dataset.csv"
        java_input.to_csv(csv_path, index=False, float_format="%.12f")
        outputs = {}
        for tool_name, suffix in (("controlTest", "controltest"), ("multipleTest", "multipletest")):
            result = subprocess.run(["java", "Friedman", str(csv_path)], cwd=java_root / tool_name,
                                    capture_output=True, text=True, check=True)
            if r"\end{document}" not in result.stdout:
                raise RuntimeError(f"SCI2S {tool_name} incomplete for {classifier}")
            path = sci2s_dir / f"{classifier}_{suffix}.tex"
            path.write_text(result.stdout, encoding="utf-8")
            outputs[suffix] = result.stdout
        rankings, globals_, pairs = parse_java(outputs["controltest"], outputs["multipletest"])
        global_tests_by_classifier[classifier] = globals_
        for strategy in LABELS:
            ranking_rows.append(" & ".join([display, strategy,
                                             number(rankings["Friedman"][strategy], 3),
                                             number(rankings["Aligned Friedman"][strategy], 3),
                                             number(rankings["Quade"][strategy], 3)]))
        for test in ("Friedman", "Iman--Davenport", "Aligned Friedman", "Quade"):
            p = globals_[test]
            test_label = "Friedman alineado" if test == "Aligned Friedman" else test
            global_rows.append(" & ".join([display, test_label, "$" + number(p) + "$",
                                            "Rechazo" if p < .05 else "No rechazo"]))
        for comparison, raw, adjusted in pairs:
            holm_rows.append(" & ".join([display, comparison, "$" + number(raw) + "$",
                                          "$" + number(adjusted) + "$"]))
        delta = matrix.full_concat - matrix.best_individual
        test = wilcoxon(delta, alternative="two-sided", method="exact")
        sensitivity_rows.append(" & ".join([display, "$" + number(delta.mean()) + "$",
                                             f"{int((delta > 0).sum())}/6", "$" + number(test.statistic, 0) + "$",
                                             "$" + number(test.pvalue) + "$"]))

    tex_table("classifier_rankings.tex",
              "Rankings medios de macro-F1 según Friedman, Friedman alineado y Quade con 22 descriptores. Seis datasets por clasificador; menor ranking indica mejor desempeño relativo dentro de cada prueba.",
              "tab:classifier-rankings", "llrrr", "Clasif. & Estrategia & Friedman & F. alineado & Quade", ranking_rows)
    tex_table("classifier_global.tex",
              r"Pruebas globales por clasificador sobre cinco estrategias y seis datasets con la biblioteca de 22 descriptores. Nivel nominal $\alpha=0{,}05$.",
              "tab:classifier-global", "llrl", "Clasif. & Prueba & $p$ & Decisión", global_rows)
    tex_table("classifier_holm.tex",
              "Comparaciones por pares basadas en rangos de Friedman. Holm corrige los diez pares dentro de cada clasificador.",
              "tab:classifier-holm", "llrr", "Clasif. & Comparación & $p$ sin ajustar & $p$ Holm", holm_rows)
    tex_table("classifier_sensitivity.tex",
              "Sensibilidad: Completa menos Individual mediante Wilcoxon exacto bilateral sobre seis datasets. V indica datasets con diferencia positiva y $W$ la menor suma de rangos.",
              "tab:classifier-sensitivity", "lrrrr", r"Clasif. & $\Delta$ medio & V/6 & $W$ & $p$", sensitivity_rows)

    classifier_delta = complete_by_classifier["resmlp"] - complete_by_classifier["svm"]
    classifier_test = wilcoxon(classifier_delta, alternative="two-sided", method="exact")
    validation = {
        "library_size": 22,
        "datasets": [display_dataset(dataset) for dataset in DATASETS],
        "conditions_per_classifier": sum(COUNTS.values()),
        "conditions_total": 2 * sum(COUNTS.values()),
        "result_rows": len(df),
        "duplicates": int(df.duplicated(["dataset", "classifier", "seed", "outer_fold", "method"]).sum()),
        "full_concat_21_22_external_keys_match": old_full_keys == new_full_keys,
        "source_csv_sha256": {
            str(path.relative_to(ROOT)): sha256(path)
            for source in SOURCES_21 + SOURCES_22
            for path in (source / "nested_fold_results.csv",
                         source / "topk_individual_control/nested_fold_results.csv")
        },
        "global_tests": global_tests_by_classifier,
        "beitv2_effect": effect_tests,
        "complete_resmlp_minus_svm": {
            "mean_delta": float(classifier_delta.mean()), "statistic": float(classifier_test.statistic),
            "p": float(classifier_test.pvalue), "resmlp_wins": int((classifier_delta > 0).sum()),
        },
    }
    df.to_csv(OUT / "primary22_beitv2_source_rows.csv", index=False)
    validation["canonical_470_rows_sha256"] = sha256(OUT / "primary22_beitv2_source_rows.csv")
    (NP_OUT / "validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
