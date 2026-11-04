"""Validate frozen P0 predictions and render the two thesis tables.

No fitting, source-result mutation, significance tests or physical timing.
Only files in paper/generated_p0 are written. Their manifest is a local
data/rendering check, not an ARS authorization or scientific certification.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/analysis/integration_v9/p0_gate_ablation_outex22_20261025"
HYBRID = ROOT / "results/exploratory/integration_v8/carlos_hybrid_outex22_20261021"
OUT = ROOT / "paper/generated_p0"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def number(value, digits=6):
    return f"{float(value):.{digits}f}".replace(".", ",")


def main():
    source_manifest = json.loads((SOURCE / "artifact_manifest.json").read_text())
    # Editorial files in this historical manifest may intentionally change.
    # Numeric P0 source artifacts must remain byte-identical.
    bound_sources = {
        name: expected for name, expected in source_manifest["sha256"].items()
        if name.startswith(str(SOURCE.relative_to(ROOT)) + "/")
    }
    assert len(bound_sources) == 4
    for name, expected in bound_sources.items():
        assert digest(ROOT / name) == expected, ("changed P0 source", name)
    results = {r["policy"]: r for r in rows(SOURCE / "results.csv")}
    views = rows(SOURCE / "prediction_views.csv")
    original = {r["policy"]: r for r in rows(HYBRID / "results.csv")}
    producer_indices = [json.loads((HYBRID / f"fold{fold}.json").read_text())["validation_indices"]
                        for fold in range(3)]
    expected_indices = sorted(index for fold in producer_indices for index in fold)
    assert len(expected_indices) == len(set(expected_indices)) == 680
    assert len(results) == 12 and len(views) == 8160
    checked_fields = 0
    nonempty, worse, identical = 0, 0, 0
    for policy, result in results.items():
        selected = sorted((v for v in views if v["policy"] == policy),
                          key=lambda v: int(v["row_index"]))
        assert len(selected) == 680
        assert len({v["row_index"] for v in selected}) == 680
        assert sorted(int(v["row_index"]) for v in selected) == expected_indices
        y = [int(v["label"]) for v in selected]
        assert len(set(y)) == 68 and all(y.count(label) == 10 for label in set(y))
        actual = {}
        for prefix, column in (("base", "base_prediction"),
                               ("always", "same_rescue_always_prediction"),
                               ("conditional", "conditional_prediction")):
            prediction = [int(v[column]) for v in selected]
            actual[prefix + "_f1"] = f1_score(y, prediction, average="macro", zero_division=0)
            actual[prefix + "_accuracy"] = accuracy_score(y, prediction)
        for field, column in (("base_ms", "base_cost_ms"),
                              ("always_ms", "same_rescue_always_cost_ms"),
                              ("forced_ms", "forced_path_cost_ms"),
                              ("conditional_ms", "conditional_cost_ms"),
                              ("always_calls", "same_rescue_always_calls"),
                              ("forced_calls", "forced_path_calls"),
                              ("conditional_calls", "conditional_calls")):
            actual[field] = math.fsum(float(v[column]) for v in selected) / 680
        for field, value in actual.items():
            assert math.isclose(value, float(result[field]), abs_tol=1e-10), (policy, field)
            checked_fields += 1
        routed = sum(v["escalated"] == "True" for v in selected)
        changed = sum(v["conditional_prediction"] != v["same_rescue_always_prediction"]
                      for v in selected)
        assert routed == int(result["routed"])
        assert changed == int(result["prediction_disagreements"])
        assert math.isclose(actual["conditional_f1"], float(original[policy]["macro_f1_oof"]), abs_tol=1e-12)
        assert math.isclose(actual["conditional_ms"], float(original[policy]["projected_ms"]), abs_tol=1e-10)
        if int(result["empty_rescue_folds"]) < 3:
            nonempty += 1
            worse += actual["conditional_f1"] < actual["always_f1"]
            identical += changed == 0
        else:
            assert changed == 0 and routed == 0
    assert checked_fields == 156 and (nonempty, worse, identical) == (8, 7, 1)

    point = results["pruned_relevance_B60"]
    full = original["carlos_diversity15_always"]
    main_rows = [
        ("Ensamble completo permanente", full["macro_f1_oof"], full["projected_ms"], full["classifier_calls"]),
        ("Mismo rescate podado permanente", point["always_f1"], point["always_ms"], point["always_calls"]),
        ("Mismo rescate, ruta forzada", point["always_f1"], point["forced_ms"], point["forced_calls"]),
        ("Ruta condicional", point["conditional_f1"], point["conditional_ms"], point["conditional_calls"]),
    ]
    main_lines = [r"\begin{table}[!htbp]", r"\centering\small",
        r"\caption{Control de poda y compuerta en relevancia/B60. Macro-F1 OOF sobre las mismas 680 imágenes; costo medio de adquisición proyectado y llamadas a clasificadores únicos por imagen. No son tiempos físicos.}",
        r"\label{tab:p0-b60}", r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
        r"Vista & Macro-F1 & Costo ms & Llamadas\\", r"\midrule"]
    for label, f1, cost, calls in main_rows:
        main_lines.append(" & ".join((label, number(f1), number(cost, 3), number(calls, 3))) + r"\\")
    main_lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    sweep_lines = [r"\begin{table}[!htbp]", r"\centering\fontsize{8}{10}\selectfont",
        r"\caption{Barrido completo del control de rescate fijo en desarrollo Outex. F1 es macro-F1 OOF; $C$ es adquisición media proyectada en ms. Permanente utiliza el mismo rescate que la política condicional, sin reselección estática.}",
        r"\label{tab:p0-barrido}", r"\begin{tabular}{@{}lr rrr rr@{}}", r"\toprule",
        r"Rescate & $B$ & F1 base & F1 perm. & F1 cond. & $C$ perm. & $C$ cond.\\", r"\midrule"]
    for prefix, label in (("full", "Completo"), ("pruned_marginal", "Podado marginal"),
                          ("pruned_relevance", "Podado relevancia")):
        for budget in (15, 30, 60, 120):
            item = results[f"{prefix}_B{budget}"]
            sweep_lines.append(" & ".join([label, str(budget)] +
                [number(item[k]) for k in ("base_f1", "always_f1", "conditional_f1")] +
                [number(item[k], 3) for k in ("always_ms", "conditional_ms")]) + r"\\")
    sweep_lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    OUT.mkdir(exist_ok=True)
    outputs = {"descomposicion_b60.tex": main_lines, "barrido_p0.tex": sweep_lines}
    for name, lines in outputs.items():
        (OUT / name).write_text("\n".join(lines) + "\n")
    inputs = [ROOT / name for name in bound_sources]
    inputs += [SOURCE / "artifact_manifest.json", HYBRID / "results.csv", Path(__file__)]
    inputs += [HYBRID / f"fold{fold}.json" for fold in range(3)]
    manifest = {
        "scope": "Saved P0 prediction validation and thesis table rendering only",
        "formal_ars_certification": False,
        "numeric_fields_recomputed": checked_fields,
        "configurations": len(results), "unique_images": 680, "derived_rows": len(views),
        "nonempty_configurations": nonempty, "lower_conditional_f1": worse,
        "identical_predictions_nonempty": identical,
        "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
        "output_sha256": {str((OUT / name).relative_to(ROOT)): digest(OUT / name) for name in outputs},
    }
    (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print({k: v for k, v in manifest.items() if not k.endswith("sha256")})


if __name__ == "__main__":
    main()
