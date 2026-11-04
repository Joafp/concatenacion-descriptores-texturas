import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import run_matched_concat_controls as runner

ROOT = Path(__file__).resolve().parents[1]


def test_queue_is_exactly_six_parent_conditions_and_new_outputs():
    spec = importlib.util.spec_from_file_location("concat_queue", ROOT / "scripts/run_matched_concat_queue.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "scripts"))
    spec.loader.exec_module(module)
    cfg = json.loads((ROOT / "configs/fsc_tex/matched_concat_20261026.json").read_text())
    assert {(c["dataset"], c["seed"]) for c in cfg["conditions"]} == {
        (dataset, seed) for dataset in ("FMD", "Outex13Official1360") for seed in (42, 123, 2026)}
    for condition in cfg["conditions"]:
        target = ROOT / cfg["output_root"] / condition["id"] / "controls"
        command = module.command_for(cfg, condition, target)
        assert command[-1] == str(target)
        assert "integration_v12" in str(target) and condition["reference"] not in str(target)


@pytest.mark.parametrize("prefix_feasible", [True, False])
def test_runner_freezes_all_choices_before_any_producer_evaluation(tmp_path, monkeypatch, prefix_feasible):
    monkeypatch.setattr(runner, "REPO", tmp_path)
    fake_script = tmp_path / "src/run_matched_concat_controls.py"
    fake_script.parent.mkdir()
    for name in ("run_matched_concat_controls.py", "static_concat_controls.py", "run_budgeted_rescue_paired.py"):
        (fake_script.parent / name).write_text("# fixture\n")
    monkeypatch.setattr(runner, "__file__", str(fake_script))
    ref, out = tmp_path / "reference", tmp_path / "new_controls"
    ref.mkdir()
    protocol = tmp_path / "protocol.md"
    protocol.write_text("frozen fixture protocol")
    manifest_path = tmp_path / "manifest/sample_manifests/FMD.csv"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("label,group\n" + "".join(f"{i%2},{i}\n" for i in range(8)))
    names = list(runner.COMMON_21) + ["rgb_ngram_svd"]
    y = np.tile([0, 1], 4)
    groups, train, external = np.arange(8), np.arange(6), np.arange(6, 8)
    provenance = {"source_sha256": {}, "embedding_array_sha256": {}, "labels_sha256": "labels",
                  "manifest_sha256": "manifest", "cost_profile_sha256": "cost",
                  "manifest_path": "manifest/sample_manifests/FMD.csv"}
    profile = {"per_descriptor_latency_ms": dict.fromkeys(names, 2), "policy_overhead_ms": .45}
    if not prefix_feasible:
        profile["per_descriptor_latency_ms"][sorted(names)[0]] = 150
    cfg = {"producer_folds": 3, "selection_folds": 3, "budgets_ms": [15, 30, 60, 120],
           "embedding_root": "emb", "manifest_root": "manifest", "inner_group_column": None,
           "ngram_count_cache": "counts", "seed": 42, "fold": 0, "official_split": None,
           "curet_direction": None, "invert_official_split": False}
    ng_prov = {"fixture": True}
    parent = {"status": "complete", "dataset": "FMD", "external_test_evaluated": False,
              "library": names, "provenance": {**provenance, "arguments": cfg, "cost_profile": profile,
                                                 "ngram_count_cache": ng_prov},
              "outer_train_indices_sha256": runner.index_hash(train),
              "external_test_indices_sha256": runner.index_hash(external)}
    (ref / "metadata.json").write_text(json.dumps(parent))
    score = lambda indices: np.eye(2)[y[indices]]
    arrays = {}
    split_logs = {}
    for fold in range(3):
        val = train[2*fold:2*fold+2]
        fit = train[~np.isin(train, val)]
        splits = []
        for part in np.array_split(fit, 3):
            splits.append({"fold": len(splits), "fit_indices": fit[~np.isin(fit, part)].tolist(),
                           "validation_indices": part.tolist()})
        split_logs[tuple(fit)] = splits
        record = {"fit_indices": fit.tolist(), "validation_indices": val.tolist(),
                  "selection_splits": splits, "library_order": names, "candidate_order": [],
                  "ranking": dict.fromkeys(names, 1.0), "ranked_blocks": sorted(names)}
        (ref / f"fold{fold}.json").write_text(json.dumps(record))
        arrays[f"fold{fold}_rows"], arrays[f"fold{fold}_labels"] = fit, y[fit]
        arrays[f"fold{fold}_single_scores"] = np.stack([score(fit)] * 22)
        arrays[f"fold{fold}_member_scores"] = np.empty((0, len(fit), 2))
    np.savez_compressed(ref / "selection_oof_scores.npz", **arrays)
    monkeypatch.setattr(runner, "load_dataset", lambda *a: (dict.fromkeys(runner.COMMON_21, np.ones((8, 2))), y))
    monkeypatch.setattr(runner, "load_manifest", lambda *a: (groups, []))
    monkeypatch.setattr(runner, "outer_indices", lambda *a: (train, external))
    monkeypatch.setattr(runner, "launch_provenance", lambda *a: dict(provenance, cost_profile=profile))
    ng = SimpleNamespace(transformation_audits=lambda: [])
    monkeypatch.setattr(runner, "load_existing_ngram", lambda *a: (ng, ng_prov))
    def fake_oof(cache, subsets, fit, *args):
        assert set(fit) <= set(train)
        return {s: score(fit) for s in subsets}, split_logs[tuple(fit)]
    monkeypatch.setattr(runner, "oof_scores", fake_oof)
    def producer_fit(cache, subset, fit, val, *args):
        frozen = json.loads((out / "decisions.json").read_text())
        assert len(frozen) == 3 and all(len(f["choices"]) == 10 for f in frozen)
        assert not set(fit).intersection(val) and set(fit) | set(val) == set(train)
        return score(val), y[val], 1.0
    monkeypatch.setattr(runner, "fit_scores", producer_fit)
    monkeypatch.setattr(sys, "argv", ["runner", "--reference-run", str(ref), "--expected-images", "6",
                                     "--protocol", str(protocol), "--output", str(out)])
    runner.main()
    meta = json.loads((out / "metadata.json").read_text())
    assert meta["status"] == "complete" and not meta["external_test_evaluated"]
    results = pd.read_csv(out / "results.csv")
    assert len(results) == 10
    prefix = results.policy.str.startswith("top_prefix_budget_")
    assert (results.loc[prefix, "complete_oof_coverage"] == prefix_feasible).all()
    complete = results.complete_oof_coverage
    assert (results.loc[complete, "macro_f1"] == 1).all()
    assert (results.loc[~complete, "n"] == 0).all()
    assert results.loc[~complete, "macro_f1"].isna().all()
    predictions = pd.read_csv(out / "predictions.csv")
    assert set(predictions.row_index) == set(train)
    spec = importlib.util.spec_from_file_location("matched_audit", ROOT / "scripts/audit_matched_concat_controls.py")
    audit_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_module)
    monkeypatch.setattr(audit_module, "ROOT", tmp_path)
    fake_auditor = tmp_path / "scripts/audit_matched_concat_controls.py"
    fake_auditor.parent.mkdir()
    fake_auditor.write_text("# audit fixture\n")
    monkeypatch.setattr(audit_module, "__file__", str(fake_auditor))
    monkeypatch.setattr(audit_module, "outer_indices", lambda *a: (train, external))
    audited = audit_module.audit(out, {"dataset": "FMD", "seed": 42, "expected_images": 6, "id": "toy"})
    assert audited["decisions_replayed"] == 30 and len(audited["metrics"]) == 10
