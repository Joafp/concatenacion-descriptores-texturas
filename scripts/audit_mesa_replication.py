"""Incrementally audit completed replication conditions without changing them.

Replays static choices and predictions, hybrid gates/rescue scores, and metrics.
All metrics remain descriptive development estimates; no new p-values or GPU.
"""
import argparse
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
from run_confirmatory_nested import canonical_labels
from run_topk_individual_control import outer_indices
from static_budget_control import select_static_ensembles


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_bindings(meta, root):
    for key in ("source_sha256", "input_sha256"):
        for name, expected in meta.get(key, {}).items():
            path = Path(name)
            assert digest(path if path.is_absolute() else root / path) == expected, name


def recovery_inputs(path):
    """Accept a new static output only with the approved, source-bound receipt."""
    state = json.loads((path / "state.json").read_text())
    assert state["status"] == "failed" and state["failed_stage"] == "static"
    assert all(stage["status"] == "complete" for stage in state["stages"][:-1])
    receipt_path = path.parent / "static_recovery_authorization.json"
    receipt = json.loads(receipt_path.read_text())
    check_bindings(receipt, ROOT)
    recovery_path = path / "static_recovery_state.json"
    recovery = json.loads(recovery_path.read_text())
    assert recovery["status"] == "complete_pending_audit" and recovery["returncode"] == 0
    assert recovery["authorization_sha256"] == digest(receipt_path)
    assert recovery["command"] in receipt["commands"]
    command = recovery["command"]
    assert Path(command[command.index("--output") + 1]) == path / "static_recovery"
    assert Path(command[command.index("--hybrid-run") + 1]) == path / "hybrid"
    assert digest(path / "static/decisions.json") == digest(path / "static_recovery/decisions.json")
    return [receipt_path, recovery_path, path / "state.json", path / "static/decisions.json", path / "static.log"]


def audit_condition(path, condition, frozen, recovered_static=False):
    expected = condition["expected_development_images"]
    roots = {name: path / name for name in ("paired", "carlos", "hybrid", "static")}
    evidence = recovery_inputs(path) if recovered_static else []
    if recovered_static:
        roots["static"] = path / "static_recovery"
    metas = {name: json.loads((p / "metadata.json").read_text()) for name, p in roots.items()}
    predictions = {name: pd.read_csv(p / "predictions.csv") for name, p in roots.items()}
    sources = evidence
    for name, p in roots.items():
        meta = metas[name]
        assert meta["status"] == "complete" and meta["dataset"] == condition["dataset"]
        assert not meta.get("external_test_evaluated", False)
        assert not meta.get("official_test_evaluated", False)
        check_bindings(meta, ROOT)
        check_bindings(meta.get("provenance", {}), ROOT)
        for file, expected_hash in meta.get("output_sha256", {}).items():
            assert digest(p / file) == expected_hash, file
        sources += list(p.glob("*.json")) + list(p.glob("*.csv")) + list(p.glob("*.npz"))
    m = metas["hybrid"]
    for key in ("outer_train_indices_sha256", "external_test_indices_sha256"):
        assert metas["paired"][key] == metas["carlos"][key] == m[key]
    with (ROOT / condition["manifest_root"] / "sample_manifests" / f"{condition['dataset']}.csv").open() as stream:
        manifest = list(csv.DictReader(stream))
    y = canonical_labels(np.asarray([row["label"] for row in manifest]))
    groups = np.array([row["group"] for row in manifest])
    labels = np.unique(y)
    inner = np.load(roots["paired"] / "selection_oof_scores.npz", allow_pickle=False)
    hscores = np.load(roots["hybrid"] / "scores.npz", allow_pickle=False)
    cscores = np.load(roots["carlos"] / "validation_scores.npz", allow_pickle=False)
    sscores = np.load(roots["static"] / "validation_scores.npz", allow_pickle=False)
    carlos = {f["producer_fold"]: f for f in json.loads((roots["carlos"] / "folds.json").read_text())}
    static = json.loads((roots["static"] / "decisions.json").read_text())
    selections = json.loads((roots["hybrid"] / "selections.json").read_text())
    costs = m["provenance"]["cost_profile"]["per_descriptor_latency_ms"]
    overhead = m["provenance"]["cost_profile"]["policy_overhead_ms"]
    indices, static_count, gate_count, p0 = [], 0, 0, []
    for f in range(3):
        rf = json.loads((roots["paired"] / f"fold{f}.json").read_text())
        hf = json.loads((roots["hybrid"] / f"fold{f}.json").read_text())
        fit, val = np.array(rf["fit_indices"]), np.array(rf["validation_indices"])
        indices.extend(val.tolist())
        assert rf["fit_indices"] == hf["fit_indices"] == carlos[f]["fit_indices"]
        assert rf["validation_indices"] == hf["validation_indices"] == carlos[f]["validation_indices"]
        assert not set(groups[fit]).intersection(groups[val])
        assert len(rf["selection_splits"]) == 3
        for split in rf["selection_splits"]:
            a, b = set(split["fit_indices"]), set(split["validation_indices"])
            assert not a.intersection(b) and a | b == set(fit)
            assert not set(groups[list(a)]).intersection(groups[list(b)])
        assert np.array_equal(y[fit], inner[f"fold{f}_labels"])
        single = {(n,): inner[f"fold{f}_single_scores"][i] for i, n in enumerate(rf["library_order"])}
        pool = {tuple(member): hscores[f"fold{f}_member_scores"][i] for i, member in enumerate(hf["candidate_order"])}
        replay = select_static_ensembles({**single, **pool}, y[fit], labels, costs,
                                          frozen["config"]["budgets_ms"], max_members=3)
        assert replay == static[f]["budget_selections"]
        order = [tuple(json.loads(str(k))) for k in sscores[f"fold{f}_candidate_order"]]
        static_scores = dict(zip(order, sscores[f"fold{f}_scores"]))
        for choice in replay.values():
            s, budget = choice["selected"], choice["budget_ms"]
            part = predictions["static"][(predictions["static"].producer_fold == f) &
                                          (predictions["static"].policy == f"static_B{budget:g}")]
            pred = labels[np.argmax(np.sum([static_scores[tuple(member)] for member in s["members"]], axis=0), axis=1)]
            assert np.array_equal(part.row_index, val) and np.array_equal(part.prediction, pred)
            assert s["projected_ms"] <= budget + 1e-10
            assert np.allclose(part.projected_ms, sum(costs[n] for n in s["blocks"]))
            assert np.allclose(part.classifier_calls, len(s["members"]))
            static_count += 1
        member_scores = {tuple(member): cscores[f"fold{f}_scores"][i]
                         for i, member in enumerate(carlos[f]["unique_subset_order"])}
        bases = {str(n): hscores[f"fold{f}_validation_base_scores"][i]
                 for i, n in enumerate(hscores[f"fold{f}_validation_base_order"])}
        for decision in (d for d in selections if d["producer_fold"] == f):
            assert decision["feasible"]
            s, name = decision["selected"], decision["policy"]
            part = predictions["hybrid"][(predictions["hybrid"].producer_fold == f) &
                                          (predictions["hybrid"].policy == name)]
            assert np.array_equal(part.row_index, val)
            score = np.sort(np.asarray(bases[s["base"]], dtype=np.float32), axis=1)
            margin = score[:, -1] - score[:, -2]
            gate = margin < s["threshold"] if s["members"] else np.zeros(len(val), dtype=bool)
            bp = labels[np.argmax(bases[s["base"]], axis=1)]
            rp = labels[np.argmax(np.mean([member_scores[tuple(member)] for member in s["members"]], axis=0), axis=1)] if s["members"] else bp
            assert np.array_equal(part.base_prediction, bp) and np.array_equal(part.rescue_prediction, rp)
            assert np.array_equal(part.escalated, gate)
            assert np.array_equal(part.prediction, np.where(gate, rp, bp))
            union = {n for member in s["members"] for n in member}
            conditional_cost = costs[s["base"]] + (overhead + gate * sum(costs[n] for n in union - {s["base"]})
                                                        if s["members"] else np.zeros(len(val)))
            assert np.allclose(part.projected_ms, conditional_cost)
            assert np.allclose(part.classifier_calls, 1 + gate * len({tuple(member) for member in s["members"]}))
            permanent = sum(costs[n] for n in union) if s["members"] else costs[s["base"]]
            for i, index in enumerate(val):
                p0.append({"row_index": int(index), "label": int(y[index]), "policy": name,
                           "rescue_prediction": int(rp[i]), "permanent_ms": permanent})
            gate_count += 1
    assert len(indices) == len(set(indices)) == expected
    allowed = set(indices)
    cfg = metas["paired"]["provenance"]["arguments"]
    outer_train, outer_test = outer_indices(condition["dataset"], condition["seed"], cfg["fold"],
                                            y, groups, manifest, cfg["official_split"],
                                            cfg["curet_direction"], cfg["invert_official_split"])
    assert allowed == set(outer_train) and not allowed.intersection(outer_test)
    for root in (roots["paired"], roots["carlos"], roots["hybrid"]):
        for a in json.loads((root / "ngram_transforms.json").read_text()):
            train, evaluate = set(a["train_indices"]), set(a["evaluation_indices"])
            assert not train.intersection(evaluate) and train | evaluate <= allowed
    rows = []
    for stage, frame in predictions.items():
        results = pd.read_csv(roots[stage] / "results.csv").set_index("policy")
        for policy, part in frame.groupby("policy", sort=True):
            assert len(part) == part.row_index.nunique() == expected and set(part.row_index) == allowed
            assert np.array_equal(part.label.to_numpy(), y[part.row_index.to_numpy()])
            f1 = f1_score(part.label, part.prediction, average="macro", zero_division=0)
            accuracy = accuracy_score(part.label, part.prediction)
            source = results.loc[policy]
            assert abs(f1 - source.get("macro_f1_oof", source.get("macro_f1"))) < 1e-12
            assert abs(accuracy - source.get("accuracy_oof", source.get("accuracy"))) < 1e-12
            assert abs(part.projected_ms.mean() - source.projected_ms) < 1e-9
            rows.append({"condition": condition["id"], "dataset": condition["dataset"], "seed": condition["seed"],
                         "stage": stage, "policy": policy, "n": len(part), "macro_f1": f1,
                         "accuracy": accuracy, "projected_ms": part.projected_ms.mean()})
    assert static_count == 12 and gate_count == 36
    permanent_rows = []
    for policy, part in pd.DataFrame(p0).groupby("policy"):
        permanent_rows.append({"condition": condition["id"], "policy": policy,
            "permanent_macro_f1": f1_score(part.label, part.rescue_prediction, average="macro"),
            "permanent_ms": part.permanent_ms.mean()})
    sources += [ROOT / condition["manifest_root"] / "sample_manifests" / f"{condition['dataset']}.csv", Path(__file__)]
    return {"status": "ANALYZED", "condition": condition, "static_recovered": recovered_static,
            "scope": "Prediction/selection replay and index checks; no independent image extraction or physical timing",
            "development_images": expected, "classes": len(labels), "static_choices_replayed": static_count,
            "hybrid_routes_replayed": gate_count, "metrics": rows, "p0": permanent_rows,
            "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    suite, out = args.suite.resolve(), args.output.resolve()
    frozen = json.loads((suite / "frozen_protocol.json").read_text())
    check_bindings(frozen, ROOT)
    out.mkdir(parents=True, exist_ok=True)
    overview, metrics, p0 = [], [], []
    for condition in frozen["config"]["conditions"]:
        source = suite / condition["id"]
        state = json.loads((source / "state.json").read_text()) if (source / "state.json").is_file() else {"status": "queued"}
        target = out / f"{condition['id']}.json"
        recovery_path = source / "static_recovery_state.json"
        recovered = (recovery_path.is_file() and
                     json.loads(recovery_path.read_text()).get("status") == "complete_pending_audit")
        if state["status"] == "complete_pending_audit" or recovered:
            if target.is_file():
                result = json.loads(target.read_text())
                check_bindings(result, ROOT)
            else:
                result = audit_condition(source, condition, frozen, recovered_static=recovered)
                target.write_text(json.dumps(result, indent=2) + "\n")
            overview.append({"condition": condition["id"], "status": "audited", "static_recovered": recovered})
            metrics += result["metrics"]
            p0 += result["p0"]
        else:
            overview.append({"condition": condition["id"], "status": state["status"],
                             "stage": state.get("stages", [{}])[-1].get("stage")})
    pd.DataFrame(metrics).to_csv(out / "metrics.csv", index=False)
    pd.DataFrame(p0).to_csv(out / "p0.csv", index=False)
    summary = {"status": "ANALYZED" if all(x["status"] == "audited" for x in overview) else "PARTIAL",
               "conditions": overview, "audited": sum(x["status"] == "audited" for x in overview),
               "expected": len(overview), "source_protocol_sha256": digest(suite / "frozen_protocol.json")}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
