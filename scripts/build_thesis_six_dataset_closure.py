#!/usr/bin/env python3
"""Generate thesis tables from the closed E1/E2 audit, without executing models."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pandas as pd
from build_topk_margin_thesis_20261113 import table, number
from prepare_top4_fixed_cascade import sha256

AUDIT = ROOT / "results/analysis/top4_fixed_kth_completion_audit_20261115_v1"


def build(output, evidence):
    if output.exists() or evidence.exists():
        raise FileExistsError("Use new output/evidence directories")
    summary = json.loads((AUDIT / "summary.json").read_text())
    if summary["completed_conditions"] != 27 or len(summary["complete_datasets"]) != 6:
        raise ValueError("six-dataset coverage is not complete")
    inputs = [AUDIT / name for name in ["summary.json", "e1_complete_dataset_means.csv",
              "e1_conditions.csv", "e1_cheap_candidate_test_metrics.csv", "e2_complete_dataset_means.csv",
              "e2_statistics.csv", "direct_reference_comparison.csv", "provenance.json"]]
    provenance = json.loads((AUDIT / "provenance.json").read_text())
    for name, expected in provenance["outputs"].items():
        if sha256(AUDIT / name) != expected:
            raise ValueError(f"closed audit changed: {name}")
    means = pd.read_csv(AUDIT / "e1_complete_dataset_means.csv").set_index("dataset")
    cases = pd.read_csv(AUDIT / "e1_conditions.csv")
    gates = pd.read_csv(AUDIT / "e2_complete_dataset_means.csv")
    bases = pd.read_csv(AUDIT / "e1_cheap_candidate_test_metrics.csv")
    order = ["DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"]
    pretty = dict(zip(order, ["DTD", "FMD", "CUReT", "Outex13", "SoilOriginal", "KTH-TIPS2b"]))
    output.mkdir(parents=True, exist_ok=False)
    evidence.mkdir(parents=True, exist_ok=False)

    def emit(name, caption, label, headers, rows, note, size=8):
        (output / name).write_text(table(caption, label, headers, rows, note, size=size))

    emit("e1_accuracy.tex", "E1 cerrado: Top-4 fijo directo y por margen en seis datasets.", "tab:e1-fixed4-accuracy",
         ["Dataset", "Directo Acc", "Margen Acc", "Sorteo Acc", r"$\Delta$ pp", r"Rescate \%"],
         [[pretty[d], number(means.loc[d, "direct_accuracy"], 6), number(means.loc[d, "cascade_accuracy"], 6),
           number(means.loc[d, "random_accuracy"], 6), number(100*(means.loc[d, "cascade_accuracy"]-means.loc[d, "direct_accuracy"]), 3),
           number(100*means.loc[d, "request_fraction"], 2)] for d in order],
         "27 condiciones SVM/42; KTH incluye sus cuatro particiones. Sorteo de igual cantidad, 100 repeticiones. Selección por macro-F1 OOF; accuracy principal.")
    emit("e1_secundarias.tex", "E1: métricas complementarias de las mismas predicciones, seis datasets.", "tab:e1-secondary",
         ["Dataset", "Prec. D", "Prec. M", "Recall D", "Recall M", "F1 D", "F1 M"],
         [[pretty[d]]+[number(means.loc[d, f"{route}_{m}"], 4) for m in ["precision_macro", "recall_macro", "macro_f1"]
                      for route in ["direct", "cascade"]] for d in order],
         "D: directo; M: margen. Promedios macro por clase y después por condición.")
    bm = bases.groupby(["dataset", "base"]).accuracy.mean()
    emit("e1_bases.tex", "E1: accuracy de cada base sola en test.", "tab:e1-bases-test",
         ["Dataset", "ResNet-50", "SigLIP", "BEiTv2", "ConvNeXt"],
         [[pretty[d]]+[number(bm.get((d, name), float("nan")), 6) if (d, name) in bm.index else "--"
                      for name in ["resnet50", "siglip_base", "beitv2_base_final", "convnext_v2_t"]] for d in order],
         "En KTH las candidatas son ResNet-50 y BEiTv2; los guiones identifican bases no evaluadas, no accuracy cero. Métricas de test, distintas de OOF.")
    emit("e1_costos.tex", "E1: adquisición proyectada por componentes, seis datasets.", "tab:e1-fixed4-costs",
         ["Dataset", "Directo ms", "Margen ms", r"Reducción \%"],
         [[pretty[d], number(means.loc[d, "direct_projected_ms"], 2), number(means.loc[d, "cascade_projected_ms"], 2),
           number(100*(1-means.loc[d, "cascade_projected_ms"]/means.loc[d, "direct_projected_ms"]), 2)] for d in order],
         "No es latencia online de políticas completas. Los componentes KTH proceden de sesiones explícitamente distintas.")
    kth = cases[cases.dataset == "KTHTIPS2b"].sort_values("outer_fold")
    emit("kth_status.tex", "E1: cuatro particiones KTH completas tras la validación autorizada.", "tab:e1-kth-state",
         ["Partición", "Estado", "Directo Acc", "Margen Acc"],
         [[int(r.outer_fold)+1, "Completada", number(r.direct_accuracy, 6), number(r.cascade_accuracy, 6)] for r in kth.itertuples()],
         "Solo 1 y 3 se ajustaron en la continuación. Se conservaron 2 y 4, las otras 23 condiciones y los registros fallidos originales.")
    names = {"margin": "Margen", "maximum_score": "Máximo", "softmax_entropy": "Entropía softmax"}
    for mode, file, label, caption in [
        ("oof_quantile", "e2_accuracy_legible.tex", "tab:e2-confidence-readable", "E2: umbrales OOF y activación real en seis datasets."),
        ("matched_test_count_diagnostic", "e2_matched_count.tex", "tab:e2-matched", "E2: diagnóstico por lote con igual cantidad derivada.")]:
        group = gates[gates["mode"] == mode].groupby(["q", "gate"]).mean(numeric_only=True)
        emit(file, caption, label, ["q", "Compuerta", "Accuracy", r"Rescate real \%"],
             [[str(q).replace(".", ","), names[gate], number(r.accuracy, 6), number(100*r.request_fraction, 2)]
              for (q, gate), r in group.iterrows()],
             "Media equiponderada de seis datasets. Mismo cuantil OOF no implica igual activación externa." if mode == "oof_quantile" else
             "Igual cantidad que el margen por condición, ordenada sin etiquetas de test. Es diagnóstico por lote, no política individual online.")
    receipt = {"status": "generated_from_closed_audit_no_new_models", "sources": {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
               "script_sha256": sha256(Path(__file__)), "summary": summary,
               "outputs": {str(p.relative_to(ROOT)): sha256(p) for p in output.iterdir()}}
    (evidence / "tables_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"tables": len(receipt["outputs"]), "random_mean_accuracy": float(means.random_accuracy.mean())}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve(), args.evidence.resolve())
