"""Audit finished E1/E2 calls; aggregate only datasets with complete coverage."""
from pathlib import Path
import argparse
import gzip
import itertools
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_top4_fixed_e1_e2 import METRICS, metrics
from prepare_top4_fixed_cascade import sha256
from build_accuracy_primary_thesis_20261115_v3 import exact_signed_rank, holm, PRETTY
from build_topk_margin_thesis_20261113 import table, number


def complete_datasets(conditions, states):
    expected = {}
    for c in conditions:
        expected.setdefault(c["dataset"], []).append(c["id"])
    return [ds for ds, ids in expected.items() if all(states.get(i) == "complete" for i in ids)]


def consolidate(folder, output, generated):
    if output.exists() or generated.exists():
        raise FileExistsError("new audit folders required")
    state = json.loads((folder / "status.json").read_text())
    if state["status"] == "running" or len(state["states"]) != 27:
        raise RuntimeError("worker has not closed all conditions")
    frozen = json.loads((folder / "protocol_frozen.json").read_text())
    if sha256(folder / "protocol_frozen.json") != state["protocol_sha256"]:
        raise ValueError("protocol hash changed")
    for name, expected in frozen["sources"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"frozen source changed: {name}")
    rows, e2, bases, sources = [], [], [], {}
    for c in frozen["conditions"]:
        path = folder / "conditions" / c["id"]
        status = json.loads((path / "status.json").read_text())
        sources[str((path / "status.json").relative_to(ROOT))] = sha256(path / "status.json")
        if status["status"] != "complete":
            continue
        for name, expected in status["sha256"].items():
            if sha256(path / name) != expected:
                raise ValueError(f"condition output changed: {path/name}")
        result = json.loads((path / "result.json").read_text())
        for block in c["cheap_candidates"]:
            bases.append({"id": c["id"], "dataset": c["dataset"], "base": block,
                          **result["metrics"][block]})
        with gzip.open(path / "scores_predictions.json.gz", "rt") as handle:
            predictions = json.load(handle)
        y, labels = np.asarray(predictions["y_true"]), np.asarray(predictions["class_order"])
        for name, pred in predictions["predictions"].items():
            actual = metrics(y, np.asarray(pred), labels)
            reported = result["metrics"][name] if name in result["metrics"] else result[name]["metrics"]
            if any(not np.isclose(actual[m], reported[m], rtol=0, atol=1e-12) for m in METRICS):
                raise ValueError(f"metric replay mismatch: {c['id']}/{name}")
        direct = np.asarray(predictions["predictions"]["top4_direct"])
        conditional = np.asarray(predictions["predictions"]["selected_cascade"])
        mask = np.asarray(predictions["request_masks"]["selected_cascade"], bool)
        if not np.array_equal(direct[mask], conditional[mask]):
            raise ValueError("rescue predictions differ")
        row = {"id": c["id"], "dataset": c["dataset"], "request_fraction": float(mask.mean()),
               "direct_projected_ms": result["direct_projected_component_ms"],
               "cascade_projected_ms": result["selected_cascade"]["projected_component_ms"],
               "random_accuracy": result["random_selected_route"]["accuracy"]["mean"]}
        for name, reported in [("direct", result["metrics"]["top4_direct"]), ("cascade", result["selected_cascade"]["metrics"])]:
            row.update({f"{name}_{m}": reported[m] for m in METRICS})
        base = result["selected_cascade"]["cheap"]
        row["cheap"] = base
        if base:
            row.update({f"cheap_{m}": result["metrics"][base][m] for m in METRICS})
        rows.append(row)
        for r in json.loads((path / "e2.json").read_text()):
            r = r.copy()
            r.update(r.pop("metrics"))
            e2.append(r)
    complete = complete_datasets(frozen["conditions"], state["states"])
    frame, gates = pd.DataFrame(rows), pd.DataFrame(e2)
    means = frame[frame.dataset.isin(complete)].groupby("dataset").mean(numeric_only=True)
    gate_means = gates[gates.dataset.isin(complete)].groupby(["dataset", "mode", "q", "gate"])[METRICS + ["request_fraction", "projected_component_ms"]].mean().reset_index()
    stats = []
    for mode in gate_means["mode"].unique():
        for metric in METRICS:
            pairs = []
            for q in (.25, .5, .75):
                matrix = gate_means[gate_means["mode"].eq(mode) & gate_means.q.eq(q)].pivot(index="dataset", columns="gate", values=metric)
                for a, b in itertools.combinations(["margin", "maximum_score", "softmax_entropy"], 2):
                    difference = matrix[a] - matrix[b]
                    pairs.append(dict(mode=mode, metric=metric, q=q, a=a, b=b, datasets=len(matrix),
                                      mean_difference=float(difference.mean()), p_exact=exact_signed_rank(difference.to_numpy())))
            for p, adjusted in zip(pairs, holm([p["p_exact"] for p in pairs])):
                p["p_holm_family9"] = adjusted
                stats.append(p)
    output.mkdir(parents=True)
    generated.mkdir(parents=True)
    frame.to_csv(output / "e1_conditions.csv", index=False)
    pd.DataFrame(bases).to_csv(output / "e1_cheap_candidate_test_metrics.csv", index=False)
    means.to_csv(output / "e1_complete_dataset_means.csv")
    gates.to_csv(output / "e2_conditions.csv", index=False)
    gate_means.to_csv(output / "e2_complete_dataset_means.csv", index=False)
    pd.DataFrame(stats).to_csv(output / "e2_statistics.csv", index=False)
    summary = {"status": "audited_with_requires_review_cases", "primary_metric": "accuracy", "expected_conditions": 27,
               "completed_conditions": len(rows), "complete_datasets": complete,
               "states": state["states"], "complete_dataset_mean_accuracy_direct": float(means.direct_accuracy.mean()),
               "complete_dataset_mean_accuracy_cascade": float(means.cascade_accuracy.mean()),
               "incomplete_dataset_averages_reported": False,
               "all_escalated_predictions_match_direct": True, "costs_are_projections": True,
               "paired_accuracy_p_exact": exact_signed_rank((means.cascade_accuracy-means.direct_accuracy).to_numpy())}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    rows = [[PRETTY[ds], number(r.direct_accuracy, 6), number(r.cascade_accuracy, 6), number(r.random_accuracy, 6), number(100*(r.cascade_accuracy-r.direct_accuracy), 3), number(100*r.request_fraction, 2)] for ds, r in means.iterrows()]
    (generated / "e1_accuracy.tex").write_text(table("E1 nuevo: Top-4 fijo directo frente a activación por margen, datasets completos.", "tab:e1-fixed4-accuracy", ["Dataset", "Directo Acc", "Margen Acc", "Sorteo Acc", r"$\Delta$ pp", r"Rescate \%"], rows, "KTH no tiene cobertura completa y no integra estas medias. Mismos cuatro bloques por condición y clasificador SVM; sorteo de igual cantidad de imágenes, 100 repeticiones. Selección histórica por macro-F1 OOF; reporte principal accuracy.", size=8))
    b=pd.DataFrame(bases)
    b=b[b.dataset.isin(complete)].groupby(['dataset','base']).accuracy.mean().unstack()
    rows=[[PRETTY[ds]]+[number(b.loc[ds,name],6) for name in ['resnet50','siglip_base','beitv2_base_final','convnext_v2_t']] for ds in complete]
    (generated/'e1_bases.tex').write_text(table('E1: accuracy en test de cada etapa barata sola.', 'tab:e1-bases-test', ['Dataset','ResNet-50','SigLIP','BEiTv2','ConvNeXt'], rows,'Modelos ajustados con el entrenamiento externo; son resultados de test, distintos de sus métricas OOF.',size=8))
    rows = [[PRETTY[ds], number(r.direct_projected_ms, 2), number(r.cascade_projected_ms, 2), number(100*(1-r.cascade_projected_ms/r.direct_projected_ms), 2)] for ds,r in means.iterrows()]
    (generated / "e1_costos.tex").write_text(table("E1: adquisición por componentes proyectada en datasets completos.", "tab:e1-fixed4-costs", ["Dataset", "Directo ms", "Margen ms", r"Reducción \%"], rows, "No es una nueva medición online de latencia de políticas completas."))
    rows = [[PRETTY[ds]] + [number(r[f"{route}_{m}"], 4) for m in ["precision_macro", "recall_macro", "macro_f1"] for route in ["direct", "cascade"]] for ds,r in means.iterrows()]
    (generated / "e1_secundarias.tex").write_text(table("E1: métricas complementarias de las mismas predicciones.", "tab:e1-secondary", ["Dataset", "Prec. D", "Prec. M", "Recall D", "Recall M", "F1 D", "F1 M"], rows, "D: directo; M: margen. Medias macro por clase y después por condición.", size=8))
    overall_gates = gate_means[gate_means["mode"].eq("oof_quantile")].groupby(["q", "gate"]).mean(numeric_only=True)
    rows = [[str(q).replace('.',','), gate.replace('_', r'\_'), number(r.accuracy, 6), number(100*r.request_fraction, 2)] for (q,gate),r in overall_gates.iterrows()]
    (generated / "e2_accuracy.tex").write_text(table("E2: compuertas con umbral OOF; media equiponderada de datasets completos.", "tab:e2-confidence", ["q", "Compuerta", "Accuracy", r"Rescate real \%"], rows, "Igual cuantil OOF no implica igual fracción en test. El control con igual cantidad de imágenes en test se informa por separado como diagnóstico por lote, no como política individual online.", size=8))
    outputs = {str(p.relative_to(ROOT)): sha256(p) for directory in (output,generated) for p in directory.iterdir() if p.is_file()}
    (output / "provenance.json").write_text(json.dumps({"condition_status_sources":sources, "outputs":outputs,
        "run_protocol_sha256":sha256(folder/'protocol_frozen.json'), "script_sha256":sha256(Path(__file__))},indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--folder",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--generated",type=Path,required=True)
    a=p.parse_args()
    consolidate(a.folder.resolve(),a.output.resolve(),a.generated.resolve())
