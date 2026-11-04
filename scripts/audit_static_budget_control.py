"""Replay static-control selections/predictions and render the full comparison."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from static_budget_control import select_static_ensembles

RUN = ROOT / "results/exploratory/integration_v10/static_budget_outex22_20261025"
HYBRID = ROOT / "results/exploratory/integration_v8/carlos_hybrid_outex22_20261021"
OUT = ROOT / "results/analysis/mesa_grado_20261025_r2/static_control"
TEX = ROOT / "paper/generated_mesa_r2"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def num(value, digits=6):
    return f"{float(value):.{digits}f}".replace(".", ",")


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    TEX.mkdir(exist_ok=True)
    meta = json.loads((RUN / "metadata.json").read_text())
    assert meta["status"] == "complete" and not meta["official_test_evaluated"]
    for name, expected in meta["input_sha256"].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in meta["output_sha256"].items():
        assert digest(RUN / name) == expected, name
    assert digest(RUN / "decisions.json") == meta["frozen_decisions_sha256"]
    hm = json.loads((HYBRID / "metadata.json").read_text())
    ref = Path(hm["reference_run"])
    inner = np.load(ref / "selection_oof_scores.npz", allow_pickle=False)
    members = np.load(HYBRID / "scores.npz", allow_pickle=False)
    validation = np.load(RUN / "validation_scores.npz", allow_pickle=False)
    decisions = json.loads((RUN / "decisions.json").read_text())
    predictions = pd.read_csv(RUN / "predictions.csv")
    data = pd.read_csv(RUN / "results.csv").set_index("budget_ms")
    original_predictions = pd.read_csv(HYBRID / "predictions.csv")
    hybrid = pd.read_csv(HYBRID / "results.csv").set_index("policy")
    costs = meta["cost_profile"]["per_descriptor_latency_ms"]
    replayed = 0
    for d in decisions:
        f = d["producer_fold"]
        fold = json.loads((HYBRID / f"fold{f}.json").read_text())
        rf = json.loads((ref / f"fold{f}.json").read_text())
        scores = {(n,): inner[f"fold{f}_single_scores"][i] for i, n in enumerate(rf["library_order"])}
        scores.update({tuple(m): members[f"fold{f}_member_scores"][i] for i, m in enumerate(fold["candidate_order"])})
        y = inner[f"fold{f}_labels"]
        assert select_static_ensembles(scores, y, np.unique(y), costs, meta["budgets_ms"],
                                       meta["member_limit"]) == d["budget_selections"]
        order = [tuple(json.loads(str(s))) for s in validation[f"fold{f}_candidate_order"]]
        val_scores = dict(zip(order, validation[f"fold{f}_scores"]))
        for choice in d["budget_selections"].values():
            point, budget = choice["selected"], choice["budget_ms"]
            sample = predictions[(predictions.producer_fold == f) &
                                 (predictions.policy == f"static_B{budget:g}")]
            assert np.array_equal(sample.row_index, validation[f"fold{f}_rows"])
            pred = np.unique(y)[np.argmax(np.sum([val_scores[tuple(m)] for m in point["members"]], axis=0), axis=1)]
            assert np.array_equal(sample.prediction, pred)
            assert np.isclose(sum(costs[n] for n in point["blocks"]), point["projected_ms"])
            assert np.allclose(sample.projected_ms, point["projected_ms"])
            assert np.allclose(sample.classifier_calls, len(point["members"]))
            assert point["projected_ms"] <= budget + 1e-10
            replayed += 1
    comparisons, lines = [], []
    for budget in meta["budgets_ms"]:
        p = predictions[predictions.policy == f"static_B{budget:g}"]
        assert len(p) == p.row_index.nunique() == 680
        static = data.loc[budget]
        assert abs(f1_score(p.label, p.prediction, average="macro") - static.macro_f1) < 1e-12
        assert abs(accuracy_score(p.label, p.prediction) - static.accuracy) < 1e-12
        assert abs(p.projected_ms.mean() - static.projected_ms) < 1e-10
        for variant in ("full", "pruned_marginal", "pruned_relevance"):
            name = f"{variant}_B{budget:g}"
            hp = original_predictions[original_predictions.policy == name]
            joined = p.merge(hp, on="row_index", suffixes=("_static", "_hybrid"), validate="one_to_one")
            assert len(joined) == 680 and np.array_equal(joined.label_static, joined.label_hybrid)
            h = hybrid.loc[name]
            comparisons.append({"budget_ms": budget, "hybrid_policy": name,
                "static_macro_f1": static.macro_f1, "static_ms": static.projected_ms,
                "hybrid_macro_f1": h.macro_f1_oof, "hybrid_ms": h.projected_ms,
                "delta_f1_hybrid_minus_static": h.macro_f1_oof - static.macro_f1,
                "same_predictions": int((joined.prediction_static == joined.prediction_hybrid).sum())})
            if variant == "pruned_relevance":
                lines.append(" & ".join([num(budget, 0), num(static.macro_f1), num(static.projected_ms, 3),
                    num(h.macro_f1_oof), num(h.projected_ms, 3), num(h.macro_f1_oof - static.macro_f1)]) + r"\\")
    table = [r"\begin{table}[!htbp]", r"\centering\fontsize{8}{10}\selectfont",
        r"\caption{Control estático optimizado dentro del pool visitado, con hasta tres miembros, frente al híbrido por relevancia bajo el mismo presupuesto. Macro-F1 OOF de desarrollo sobre 680 imágenes; $C$ es adquisición media proyectada en ms. $\Delta$ es híbrido menos estático.}",
        r"\label{tab:estatico-presupuesto}", r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
        r"$B$ & F1 estático & $C$ estático & F1 híbrido & $C$ híbrido & $\Delta$F1\\", r"\midrule",
        *lines, r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    target = TEX / "estatico_presupuesto.tex"
    target.write_text("\n".join(table) + "\n")
    pd.DataFrame(comparisons).to_csv(OUT / "comparisons.csv", index=False)
    inputs = [RUN / "metadata.json", RUN / "predictions.csv", RUN / "results.csv",
              RUN / "decisions.json", RUN / "validation_scores.npz", HYBRID / "results.csv",
              HYBRID / "predictions.csv", HYBRID / "scores.npz", ref / "selection_oof_scores.npz",
              ROOT / "src/static_budget_control.py", Path(__file__)]
    summary = {"status": "ANALYZED", "scope": "Saved-score selection and prediction replay; not independent RGB extraction",
               "decisions_replayed": replayed, "policies": 4, "images_per_policy": 680,
               "hybrid_comparisons": 12, "classifier_fits": meta["fresh_producer_fits"],
               "all_static_fold_budgets_satisfied": True,
               "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
               "output_sha256": {str(target.relative_to(ROOT)): digest(target)}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (TEX / "static_control_provenance.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith("sha256")}, indent=2))


if __name__ == "__main__":
    main()
