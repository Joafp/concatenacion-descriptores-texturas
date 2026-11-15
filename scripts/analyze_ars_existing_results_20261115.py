#!/usr/bin/env python3
"""ARS REV-05/06: observed variation and static sensitivity, using saved data only.

No fits, feature extractions, model predictions, timing, population confidence
intervals or independent-fold assumptions. Canonical six-dataset results stay
untouched; exclusions are explicitly labeled sensitivity analyses.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_accuracy_primary_thesis_20261115_v3 import static_statistics, exact_signed_rank
from build_topk_margin_thesis_20261113 import table, number

STATIC = Path("results/analysis/thesis_accuracy_primary_20261115_v3")
E1 = Path("results/analysis/top4_fixed_kth_completion_audit_20261115_v1")
ORDER = ["DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"]
NAMES = dict(zip(ORDER, ["DTD", "FMD", "CUReT", "Outex13", "Soil", "KTH-TIPS2b"]))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def observed_variation(frame):
    required = {"id", "dataset", "direct_accuracy", "cascade_accuracy"}
    if not required.issubset(frame.columns) or frame.id.duplicated().any():
        raise ValueError("missing fields or duplicate condition")
    frame = frame.copy()
    frame["accuracy_difference_pp"] = 100 * (frame.cascade_accuracy-frame.direct_accuracy)
    rows = []
    for ds, group in frame.groupby("dataset", sort=False):
        x = group.accuracy_difference_pp.to_numpy()
        if not np.isfinite(x).all():
            raise ValueError("nonfinite observed difference")
        q = np.quantile(x, [.25, .5, .75], method="linear")
        rows.append(dict(dataset=ds, conditions=len(x), mean_difference_pp=float(x.mean()),
                         min_difference_pp=float(x.min()), q25_difference_pp=float(q[0]),
                         median_difference_pp=float(q[1]), q75_difference_pp=float(q[2]),
                         max_difference_pp=float(x.max()), gains=int((x>0).sum()),
                         ties=int((x==0).sum()), losses=int((x<0).sum())))
    means = frame.groupby("dataset")[["direct_accuracy", "cascade_accuracy"]].mean()
    lodo = []
    for excluded in [None, *means.index]:
        selected = means if excluded is None else means.drop(index=excluded)
        delta = selected.cascade_accuracy-selected.direct_accuracy
        lodo.append(dict(excluded_dataset=excluded or "none", datasets=len(selected),
                         direct_accuracy=float(selected.direct_accuracy.mean()),
                         cascade_accuracy=float(selected.cascade_accuracy.mean()),
                         mean_difference_pp=float(100*delta.mean()),
                         paired_p_exact=exact_signed_rank(delta.to_numpy())))
    return frame, pd.DataFrame(rows), pd.DataFrame(lodo)


def sensitivity_statistics(matrix):
    if list(matrix.columns) != ["Individual", "Completa-22", "Top-4"]:
        raise ValueError("preserve the original three-method comparison")
    if set(matrix.index) != set(ORDER) or not np.isfinite(matrix.to_numpy()).all():
        raise ValueError("expected all six complete dataset means")
    result = {}
    for name, exclusions in [("all_six", []), ("without_kth", ["KTHTIPS2b"]),
                              ("without_outex", ["Outex13Official1360"]),
                              ("without_kth_and_outex", ["KTHTIPS2b", "Outex13Official1360"])]:
        selected = matrix.drop(index=exclusions)
        stats = static_statistics(selected)
        stats["included_datasets"] = selected.index.tolist()
        stats["excluded_datasets"] = exclusions
        result[name] = stats
    return result


def build(output, generated):
    if output.exists() or generated.exists():
        raise FileExistsError("new output and generated folders required")
    inputs = [ROOT/E1/"e1_conditions.csv", ROOT/E1/"summary.json",
              ROOT/STATIC/"static_accuracy_svm.csv", ROOT/STATIC/"static_accuracy_resmlp.csv",
              ROOT/STATIC/"statistics.json", Path(__file__),
              ROOT/"scripts/build_accuracy_primary_thesis_20261115_v3.py"]
    sources = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    e1 = pd.read_csv(ROOT/E1/"e1_conditions.csv", float_precision="round_trip")
    if len(e1) != 27 or set(e1.dataset) != set(ORDER):
        raise ValueError("E1 coverage changed")
    frame, ranges, lodo = observed_variation(e1)
    old = json.loads((ROOT/STATIC/"statistics.json").read_text())
    statistics = {}
    pair_rows, friedman_rows = [], []
    for classifier in ["svm", "resmlp"]:
        matrix = pd.read_csv(ROOT/STATIC/f"static_accuracy_{classifier}.csv", index_col="dataset", float_precision="round_trip")
        statistics[classifier] = sensitivity_statistics(matrix)
        full = statistics[classifier]["all_six"]
        if full["friedman_p_exact"] != old[classifier]["friedman_p_exact"]:
            raise ValueError("original exact Friedman result not reproduced")
        for current, reference in zip(full["pairs"], old[classifier]["pairs"], strict=True):
            if current["p_exact"] != reference["p_exact"] or current["p_holm"] != reference["p_holm"]:
                raise ValueError("original exact Wilcoxon/Holm family not reproduced")
        for scope, stats in statistics[classifier].items():
            friedman_rows.append(dict(classifier=classifier, scope=scope, datasets=stats["datasets"],
                                      permutations=stats["permutations"], statistic=stats["friedman_chi2"],
                                      p_exact=stats["friedman_p_exact"]))
            pair_rows.extend(dict(classifier=classifier, scope=scope, datasets=stats["datasets"], **row) for row in stats["pairs"])
    output.mkdir(parents=True, exist_ok=False)
    generated.mkdir(parents=True, exist_ok=False)
    frame.to_csv(output/"e1_condition_differences.csv", index=False)
    ranges.to_csv(output/"e1_dataset_observed_ranges.csv", index=False)
    lodo.to_csv(output/"e1_leave_one_dataset_out.csv", index=False)
    pd.DataFrame(pair_rows).to_csv(output/"static_accuracy_sensitivity_pairs.csv", index=False)
    pd.DataFrame(friedman_rows).to_csv(output/"static_accuracy_sensitivity_friedman.csv", index=False)
    (output/"static_accuracy_sensitivity.json").write_text(json.dumps(statistics, indent=2)+"\n")
    r = ranges.set_index("dataset")
    rows = [[NAMES[ds], int(r.loc[ds,"conditions"])] + [number(r.loc[ds,k+"_difference_pp"],3)
             for k in ["min","q25","median","q75","max"]] for ds in ORDER]
    (generated/"e1_observed_ranges.tex").write_text(table(
        "Variación observada de la diferencia de accuracy margen menos directo en E1.",
        "tab:ars-e1-variation", ["Dataset","Cond.","Mín.","Q1","Mediana","Q3","Máx."], rows,
        "Diferencias en puntos porcentuales; cuantiles lineales de las condiciones observadas. No son intervalos de confianza ni réplicas independientes. Las particiones y semillas reutilizan imágenes.", size=8))
    rows = [["Ninguno" if row.excluded_dataset=="none" else NAMES[row.excluded_dataset], int(row.datasets),
             number(row.direct_accuracy,6), number(row.cascade_accuracy,6), number(row.mean_difference_pp,3),
             number(row.paired_p_exact,4)] for row in lodo.itertuples()]
    (generated/"e1_dataset_sensitivity.tex").write_text(table(
        "E1: sensibilidad descriptiva al excluir un dataset de la media equiponderada.",
        "tab:ars-e1-lodo", ["Exclusión","D","Directo Acc","Margen Acc",r"$\Delta$ pp",r"$p$ exacto"], rows,
        "El cierre canónico conserva los seis datasets. Las exclusiones cambian el conjunto objetivo; no son intervalos poblacionales ni nuevas confirmaciones. Los p bilaterales son diagnósticos de sensibilidad, sin selección de una exclusión favorable.", size=8))
    rows = [[clf.upper(), stats["datasets"], number(stats["friedman_chi2"],4),
             number(stats["friedman_p_exact"],4), stats["permutations"]]
            for clf in ["svm","resmlp"] for stats in [statistics[clf]["without_kth"]]]
    (generated/"static_accuracy_without_kth.tex").write_text(table(
        "Sensibilidad del contraste estático principal de accuracy sin KTH archivado.",
        "tab:ars-static-no-kth", ["Clasificador","D",r"Friedman $\chi^2$",r"$p$ exacto","Permut."], rows,
        "Mismos tres comparadores: Individual, Completa-22 y Top-4. DTD, FMD, CUReT, Outex y Soil; las bibliotecas y medias originales se conservan. No corresponde al cierre E1 ni modifica sus cuatro condiciones KTH.", size=8))
    rows = [[clf.upper(), pair["a"]+" / "+pair["b"], number(pair["mean_difference"],6),
             number(pair["p_exact"],4), number(pair["p_holm"],4)] for clf in ["svm","resmlp"]
            for pair in statistics[clf]["without_kth"]["pairs"]]
    (generated/"static_accuracy_without_kth_pairs.tex").write_text(table(
        "Pares de accuracy sin KTH: misma familia de Holm por clasificador.",
        "tab:ars-static-no-kth-pairs", ["Clasif.","Par A/B",r"$\Delta$ A-B",r"$p$ exacto",r"$p$ Holm"], rows,
        "Tres pares por clasificador, una media por dataset y Wilcoxon bilateral exacto. La no significación no prueba equivalencia. Se mantienen las restricciones de procedencia del archivo estático.", size=8))
    summary = {"status":"complete_saved_data_analysis", "new_fits":0,"new_extractions":0,
               "new_model_predictions":0,"new_timing_calls":0,"primary_metric":"accuracy",
               "e1_conditions":27,"e1_datasets":6,"confidence_intervals_reported":False,
               "uncertainty_scope":"Observed condition ranges and dataset-exclusion sensitivity only; overlapping partitions are not independent population replicates.",
               "e1_full_mean_difference_pp":float(lodo.iloc[0].mean_difference_pp),
               "e1_lodo_difference_pp_min":float(lodo[lodo.excluded_dataset.ne("none")].mean_difference_pp.min()),
               "e1_lodo_difference_pp_max":float(lodo[lodo.excluded_dataset.ne("none")].mean_difference_pp.max()),
               "static_without_kth":{clf:statistics[clf]["without_kth"] for clf in ["svm","resmlp"]},
               "optional_outex_sensitivities":"Diagnostic only; do not establish a data defect or replace canonical six-dataset results.",
               "canonical_sources_unchanged":all(sha(ROOT/p)==h for p,h in sources.items())}
    if not summary["canonical_sources_unchanged"]:
        raise ValueError("an input changed during analysis")
    (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    outputs={str(p.relative_to(ROOT)):sha(p) for folder in [output,generated] for p in folder.iterdir() if p.is_file()}
    (output/"provenance.json").write_text(json.dumps({"sources":sources,"outputs":outputs},indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--generated",type=Path,required=True)
    args=parser.parse_args()
    build(args.output.resolve(),args.generated.resolve())
