"""Build manuscript tables only from the five audited development conditions."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDS = ("FMD_s42", "FMD_s123", "FMD_s2026", "Outex_s123", "Outex_s2026")
BUDGETS = (15, 30, 60, 120)
RULES = ("full", "pruned_marginal", "pruned_relevance")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def number(value, places=6):
    return f"{value:.{places}f}".replace(".", ",")


def pair(f1, cost):
    return f"{number(f1)} / {number(cost, 3)}"


def table(caption, label, header, rows, compact=False):
    cols = "@{}" + "l" + "r" * (len(header) - 1) + "@{}"
    head = " & ".join(header) + r"\\"
    body = [" & ".join(map(str, row)) + r"\\" for row in rows]
    style = r"\fontsize{8}{10}\selectfont\setlength{\tabcolsep}{3pt}" if compact else r"\small"
    return "\n".join([r"\begin{table}[!htbp]\centering" + style, r"\caption{" + caption + "}",
        r"\label{" + label + "}", r"\begin{tabular}{" + cols + "}",
        r"\toprule", head, r"\midrule", *body, r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])


def build(source, output):
    inputs = [source / "summary.json", source / "metrics.csv", source / "p0.csv", Path(__file__)]
    summary = json.loads(inputs[0].read_text())
    assert summary["status"] == "ANALYZED" and summary["audited"] == summary["expected"] == 5
    assert {x["condition"] for x in summary["conditions"]} == set(IDS)
    for name in IDS:
        path = source / f"{name}.json"
        result = json.loads(path.read_text())
        assert result["status"] == "ANALYZED"
        for relative, expected in result["input_sha256"].items():
            assert digest(ROOT / relative) == expected, relative
        inputs.append(path)
    metrics = pd.read_csv(source / "metrics.csv")
    p0 = pd.read_csv(source / "p0.csv")
    assert len(metrics) == 170 and len(p0) == 60
    assert not metrics.duplicated(["condition", "stage", "policy"]).any()
    assert not p0.duplicated(["condition", "policy"]).any()

    def point(condition, stage, policy):
        found = metrics[(metrics.condition == condition) & (metrics.stage == stage) & (metrics.policy == policy)]
        assert len(found) == 1
        return found.iloc[0]

    means, curves, refs, ablations = [], [], [], []
    for dataset, names in (("FMD", IDS[:3]), ("Outex", IDS[3:])):
        for budget in BUDGETS:
            hybrid = [point(c, "hybrid", f"pruned_relevance_B{budget}") for c in names]
            static = [point(c, "static", f"static_B{budget}") for c in names]
            means.append([f"{dataset} ({len(names)})", budget,
                pair(sum(r.macro_f1 for r in hybrid) / len(names), sum(r.projected_ms for r in hybrid) / len(names)),
                pair(sum(r.macro_f1 for r in static) / len(names), sum(r.projected_ms for r in static) / len(names))])
        for rule, title in zip(RULES, ("Completo", "Marginal", "Relevancia")):
            for budget in BUDGETS:
                hybrid = [point(c, "hybrid", f"{rule}_B{budget}") for c in names]
                permanent = p0[p0.condition.isin(names) & (p0.policy == f"{rule}_B{budget}")]
                assert len(permanent) == len(names)
                ablations.append([dataset, title, budget,
                    pair(permanent.permanent_macro_f1.mean(), permanent.permanent_ms.mean()),
                    pair(sum(r.macro_f1 for r in hybrid) / len(names), sum(r.projected_ms for r in hybrid) / len(names))])
    for condition in IDS:
        title = condition.replace("_s", "/")
        for budget in BUDGETS:
            points = [point(condition, "hybrid", f"{rule}_B{budget}") for rule in RULES]
            points.append(point(condition, "static", f"static_B{budget}"))
            curves.append([title, budget, *[pair(r.macro_f1, r.projected_ms) for r in points]])
        for stage, policy, title_policy in (("paired", "best_individual", "Individual interno"),
                ("paired", "top3", "Top-3 fijo"), ("paired", "top4", "Top-4 fijo"),
                ("paired", "top5", "Top-5 fijo"), ("paired", "full_library", "Completa-22"),
                ("hybrid", "carlos_diversity15_always", "Diversidad permanente")):
            r = point(condition, stage, policy)
            refs.append([title, title_policy, number(r.macro_f1), number(r.projected_ms, 3)])
    contents = {
        "replica_medias.tex": table(
            r"Réplica de desarrollo: media entre semillas nuevas de macro-F1 / costo proyectado (ms). El número entre paréntesis es el de semillas, no datasets independientes. $B$ restringe el costo interno medio; no es el costo medido. Outex/42 no integra estas medias.",
            "tab:replica-medias", ["Dataset", "$B$", "Híbrido relevancia", "Estático presupuestado"], means),
        "replica_barrido.tex": table(
            r"Barrido de la réplica por dataset/semilla: macro-F1 / costo proyectado (ms). Las tres reglas híbridas y el control estático mantienen los cuatro presupuestos. Las filas comparten imágenes; no representan dominios independientes.",
            "tab:replica-barrido", ["Condición", "$B$", "Completo", "Marginal", "Relevancia", "Estático"], curves, True),
        "replica_referencias.tex": table(
            r"Referencias del mismo desarrollo productor. Top-3/4/5 tienen tamaño fijo y no equivalen al Top-$k$ heredado de GFS del benchmark. Costos proyectados, no latencias físicas.",
            "tab:replica-referencias", ["Condición", "Referencia", "Macro-F1", "Costo ms"], refs, True),
        "replica_p0.tex": table(
            r"Mismo rescate permanente frente a condicional en la réplica: macro-F1 / costo proyectado (ms), media de tres semillas FMD y dos Outex. La referencia permanente conserva los miembros seleccionados para la ruta condicional y no se reoptimiza bajo $B$. Incluye los casos sin rescate.",
            "tab:replica-p0", ["Dataset", "Regla", "$B$", "Permanente", "Condicional"], ablations, True),
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, text in contents.items():
        (output / name).write_text(text)
    provenance = {"scope": "Audited development estimates; no new fitting, inferential tests or physical timing",
        "conditions": list(IDS), "metric_rows": len(metrics), "p0_rows": len(p0),
        "table_rows": {"means": len(means), "curves": len(curves), "references": len(refs), "p0": len(ablations)},
        "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
        "output_sha256": {name: digest(output / name) for name in contents}}
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance["table_rows"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "results/analysis/mesa_replication_20261026")
    parser.add_argument("--output", type=Path, default=ROOT / "paper/generated_replication")
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())
