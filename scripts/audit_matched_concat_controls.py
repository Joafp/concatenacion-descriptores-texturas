"""Replay completed matched concatenation controls without changing experiments."""
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
from run_budgeted_rescue_paired import index_hash
from static_concat_controls import greedy_selection, inherited_topk, budget_prefix, cost_of


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bindings(payload):
    for key in ("input_sha256", "source_sha256"):
        for file, expected in payload.get(key, {}).items():
            assert digest(ROOT / file) == expected, file


def audit(path, condition):
    meta = json.loads((path / "metadata.json").read_text())
    assert meta["status"] == "complete" and not meta["external_test_evaluated"]
    assert meta["dataset"] == condition["dataset"] and meta["seed"] == condition["seed"]
    assert meta["expected_development_images"] == condition["expected_images"]
    bindings(meta)
    bindings(meta["provenance"])
    for file, expected in meta["output_sha256"].items():
        assert digest(path / file) == expected, file
    ref = Path(meta["reference_run"])
    parent = json.loads((ref / "metadata.json").read_text())
    assert meta["library"] == parent["library"] and len(meta["library"]) == 22
    bindings(parent["provenance"])
    assert not parent["external_test_evaluated"]
    for key in ("outer_train_indices_sha256", "external_test_indices_sha256"):
        assert parent[key] == meta[key]
    with (ROOT / meta["provenance"]["manifest_path"]).open() as stream:
        manifest = list(csv.DictReader(stream))
    y = canonical_labels(np.array([row["label"] for row in manifest]))
    groups = np.array([row["group"] for row in manifest])
    cfg = parent["provenance"]["arguments"]
    outer_train, external = outer_indices(meta["dataset"], cfg["seed"], cfg["fold"], y, groups, manifest,
        cfg["official_split"], cfg["curet_direction"], cfg["invert_official_split"])
    assert index_hash(outer_train) == meta["outer_train_indices_sha256"]
    assert index_hash(external) == meta["external_test_indices_sha256"]
    labels = np.unique(y)
    costs = meta["provenance"]["cost_profile"]["per_descriptor_latency_ms"]
    decisions = json.loads((path / "decisions.json").read_text())
    assert digest(path / "decisions.json") == meta["decisions_sha256"]
    inner = np.load(path / "selection_oof_scores.npz", allow_pickle=False)
    validation = np.load(path / "validation_scores.npz", allow_pickle=False)
    predictions = pd.read_csv(path / "predictions.csv")
    results = pd.read_csv(path / "results.csv").set_index("policy")
    all_rows, expected_pairs, checked = [], set(), 0
    for f, record in enumerate(decisions):
        original = json.loads((ref / f"fold{f}.json").read_text())
        for key in ("fit_indices", "validation_indices", "selection_splits", "ranked_blocks"):
            assert record[key] == original[key]
        fit, val = np.array(record["fit_indices"]), np.array(record["validation_indices"])
        assert not set(groups[fit]).intersection(groups[val])
        assert np.array_equal(inner[f"fold{f}_rows"], fit)
        assert np.array_equal(inner[f"fold{f}_labels"], y[fit])
        assert np.array_equal(validation[f"fold{f}_rows"], val)
        all_rows.extend(val.tolist())
        expected_pairs.add((tuple(sorted(fit)), tuple(sorted(val))))
        masks = []
        for split in record["selection_splits"]:
            a, b = np.array(split["fit_indices"]), np.array(split["validation_indices"])
            assert not set(a).intersection(b) and set(a) | set(b) == set(fit)
            assert not set(groups[a]).intersection(groups[b])
            expected_pairs.add((tuple(sorted(a)), tuple(sorted(b))))
            masks.append(np.isin(fit, b))
        assert len(masks) == 3 and np.all(np.sum(masks, axis=0) == 1)
        order = [tuple(json.loads(str(s))) for s in inner[f"fold{f}_candidate_order"]]
        scores = dict(zip(order, inner[f"fold{f}_scores"]))
        def evaluate(subset):
            value = scores[subset]
            assert value.shape == (len(fit), len(labels)) and np.isfinite(value).all()
            pred = labels[np.argmax(value, axis=1)]
            return float(np.mean([f1_score(y[fit][mask], pred[mask], average="macro", zero_division=0) for mask in masks]))
        replay = {"gfs": greedy_selection(meta["library"], evaluate, costs)}
        replay["topk_gfs_size"] = inherited_topk(record["ranked_blocks"], replay["gfs"], evaluate, costs)
        for budget in (15, 30, 60, 120):
            replay[f"gfs_budget_B{budget}"] = greedy_selection(meta["library"], evaluate, costs, budget=budget)
            replay[f"top_prefix_budget_B{budget}"] = budget_prefix(record["ranked_blocks"], evaluate, costs, budget)
        assert replay == record["choices"]
        vorder = [tuple(json.loads(str(s))) for s in validation[f"fold{f}_candidate_order"]]
        vscores = dict(zip(vorder, validation[f"fold{f}_scores"]))
        for policy, choice in replay.items():
            part = predictions[(predictions.policy == policy) & (predictions.producer_fold == f)]
            if not choice["feasible"]:
                assert len(part) == 0
                checked += 1
                continue
            chosen = choice["selected"]
            value = vscores[tuple(chosen["blocks"])]
            assert value.shape == (len(val), len(labels)) and np.isfinite(value).all()
            pred = labels[np.argmax(value, axis=1)]
            assert np.array_equal(part.row_index, val) and np.array_equal(part.label, y[val])
            assert np.array_equal(part.prediction, pred) and np.all(part.k == chosen["k"])
            cost = cost_of(chosen["blocks"], costs)
            assert np.allclose(part.projected_ms, cost) and np.all(part.classifier_calls == 1)
            if choice["budget_ms"] is not None:
                assert cost <= choice["budget_ms"] + 1e-10
            checked += 1
    assert checked == 30
    assert len(all_rows) == len(set(all_rows)) == condition["expected_images"]
    allowed = set(all_rows)
    assert allowed == set(outer_train) and not allowed.intersection(external)
    for transform in json.loads((path / "ngram_transforms.json").read_text()):
        pair = (tuple(sorted(transform["train_indices"])), tuple(sorted(transform["evaluation_indices"])))
        assert pair in expected_pairs
    metrics = []
    for policy, source in results.iterrows():
        part = predictions[predictions.policy == policy]
        complete = len(part) == part.row_index.nunique() == condition["expected_images"]
        assert bool(source.complete_oof_coverage) == complete and source.n == len(part)
        assert source.feasible_producer_folds == sum(d["choices"][policy]["feasible"] for d in decisions)
        f1, accuracy, cost = None, None, None
        if complete:
            assert set(part.row_index) == allowed
            f1 = f1_score(part.label, part.prediction, average="macro", zero_division=0)
            accuracy = accuracy_score(part.label, part.prediction)
            cost = part.projected_ms.mean()
            assert abs(f1 - source.macro_f1) < 1e-12 and abs(accuracy - source.accuracy) < 1e-12
            assert abs(cost - source.projected_ms) < 1e-9
        else:
            assert pd.isna(source.macro_f1) and pd.isna(source.projected_ms)
        metrics.append({"condition": condition["id"], "dataset": condition["dataset"], "seed": condition["seed"],
                        "policy": policy, "complete": complete, "n": len(part), "macro_f1": f1,
                        "accuracy": accuracy, "projected_ms": cost})
    files = [*path.glob("*.json"), *path.glob("*.csv"), *path.glob("*.npz"), Path(__file__),
             ROOT / "src/static_concat_controls.py", ROOT / meta["provenance"]["manifest_path"]]
    return {"status": "ANALYZED", "scope": "Selection/prediction replay, not independent extraction or timing",
            "condition": condition, "decisions_replayed": checked, "metrics": metrics,
            "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in files}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    suite, out = args.suite.resolve(), args.output.resolve()
    frozen = json.loads((suite / "frozen_protocol.json").read_text())
    bindings(frozen)
    out.mkdir(parents=True, exist_ok=True)
    overview, metrics = [], []
    for condition in frozen["config"]["conditions"]:
        path = suite / condition["id"]
        state = json.loads((path / "state.json").read_text()) if (path / "state.json").is_file() else {"status": "queued"}
        if state["status"] == "complete_pending_audit":
            target = out / f"{condition['id']}.json"
            if target.exists():
                result = json.loads(target.read_text())
                bindings(result)
            else:
                result = audit(path / "controls", condition)
                target.write_text(json.dumps(result, indent=2) + "\n")
            metrics += result["metrics"]
            overview.append({"condition": condition["id"], "status": "audited"})
        else:
            overview.append({"condition": condition["id"], "status": state["status"]})
    pd.DataFrame(metrics).to_csv(out / "metrics.csv", index=False)
    summary = {"status": "ANALYZED" if all(c["status"] == "audited" for c in overview) else "PARTIAL",
               "conditions": overview, "audited": sum(c["status"] == "audited" for c in overview),
               "expected": len(overview), "frozen_protocol_sha256": digest(suite / "frozen_protocol.json")}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
