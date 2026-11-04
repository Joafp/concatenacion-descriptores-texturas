"""Check added manuscript details against saved sources, without model fitting.

Requires the existing structural checker output and refuses to overwrite reports.
Algebraic cases check the acquisition-cost identity, not empirical speedups.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HYBRID = ROOT / "results/exploratory/integration_v8/carlos_hybrid_outex22_20261021"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structural-report", type=Path, required=True)
    parser.add_argument("--revision-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    base = json.loads(args.structural_report.read_text())
    for name, expected in base["sha256"].items():
        assert digest(ROOT / name) == expected, ("stale structural report", name)

    meta = json.loads((HYBRID / "metadata.json").read_text())
    for name, expected in meta["provenance"]["source_sha256"].items():
        assert digest(ROOT / name) == expected, ("implementation drift", name)
    with (HYBRID / "results.csv").open() as stream:
        hybrid = {r["policy"]: r for r in csv.DictReader(stream)}
    text = (ROOT / "paper/chapters/05_resultados.tex").read_text()
    labels = {"Completo como rescate": "full", "Podado marginal": "pruned_marginal",
              "Podado relevancia": "pruned_relevance"}
    policies = []
    for line in text.splitlines():
        fields = [s.strip().rstrip(chr(92)) for s in line.split("&")]
        if len(fields) != 4:
            continue
        if fields[0] == "Diversidad15 permanente":
            policy = "carlos_diversity15_always"
        elif fields[0] in labels:
            policy = labels[fields[0]] + "_B" + fields[1]
        else:
            continue
        row = hybrid[policy]
        assert float(fields[2].replace(",", ".")) == round(float(row["macro_f1_oof"]), 6)
        assert float(fields[3].replace(",", ".")) == round(float(row["projected_ms"]), 3)
        policies.append(policy)
    assert len(policies) == 13 and len(set(policies)) == 13

    appendix = (ROOT / "paper/chapters/B_procedencia.tex").read_text()
    folds = []
    for number in range(3):
        source = json.loads((HYBRID / f"fold{number}.json").read_text())
        values = [number, len(source["fit_indices"]), len(source["validation_indices"]),
                  len(source["members"]), len({tuple(m) for m in source["members"]})]
        printed = re.search("^" + str(number) + r" & ([0-9]+) & ([0-9]+) & ([0-9]+) & ([0-9]+)",
                            appendix, re.M)
        assert printed and values[1:] == [int(x) for x in printed.groups()]
        folds.append(values)

    costs = meta["provenance"]["cost_profile"]["per_descriptor_latency_ms"]
    gabor_share = 100 * costs["gabor"] / sum(costs.values())
    assert round(gabor_share, 1) == 60.3
    reference = hybrid["carlos_diversity15_always"]
    point = hybrid["pruned_relevance_B60"]
    saving = 100 * (1 - float(point["projected_ms"]) / float(reference["projected_ms"]))
    delta = float(point["macro_f1_oof"]) - float(reference["macro_f1_oof"])
    assert round(saving, 2) == 85.4 and round(delta, 6) == -0.003646
    assert float(point["macro_f1_oof"]) > float(hybrid["pruned_relevance_B120"]["macro_f1_oof"])
    assert float(point["projected_ms"]) < float(hybrid["pruned_relevance_B120"]["projected_ms"])

    # Fixed deterministic cases, including bases inside and outside the rescue union.
    algebra_cases = 0
    for rescue_cost in (3.0, 13.0, 60.0):
        for base_cost in (1.0, 2.0):
            for shared_base in (False, True):
                additional = rescue_cost - (base_cost if shared_base else 0)
                boundary = (rescue_cost - base_cost - 0.45) / additional
                for rate in (0, 0.1, 0.5, 0.9, 1):
                    conditional = base_cost + 0.45 + rate * additional
                    assert (conditional < rescue_cost) == (rate < boundary)
                    algebra_cases += 1
    extra = [args.revision_record, Path(__file__), args.structural_report,
             ROOT / "paper/revision_mejora_integral_20261025_before.tar.gz"]
    extra += [HYBRID / f"fold{n}.json" for n in range(3)]
    extra += [ROOT / "docs/referencias" / name for name in
              ("electronics-14-04779 (1).pdf", "jimaging-11-00304 (1).pdf")]
    result = {
        "scope": "Local manuscript arithmetic, source-preservation and algebra checks; no model fitting",
        "formal_ars_authorization_certification": False,
        "structural_checks": {k: v for k, v in base.items() if k != "sha256"},
        "hybrid_table_policies_checked": len(policies),
        "producer_fold_table_checked": folds,
        "algebraic_cost_cases_checked": algebra_cases,
        "gabor_share_percent": gabor_share,
        "projected_saving_percent": saving,
        "macro_f1_delta_B60_vs_always": delta,
        "sha256": {**base["sha256"], **{
            str(p.resolve().relative_to(ROOT)): digest(p) for p in extra}},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + chr(10))
    print({k: v for k, v in result.items() if k not in ("sha256", "structural_checks")})


if __name__ == "__main__":
    main()
