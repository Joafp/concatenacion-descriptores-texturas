#!/usr/bin/env python3
"""Recalculate matched Carlos controls and frozen-route color ablations."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

from run_rescue_nested_selection import REPO, sha256_file
from run_diversity_lottery import draw_subset
from run_weighted_lottery_selection import rank_weights
from fsc_tex.utility import compute_margins

ROOT = REPO / "results/exploratory/integration_v6"
OUT = REPO / "results/analysis/integration_v6/p2_controls_20261021"


def verify_sources(meta):
    for source, digest in meta["provenance"]["source_sha256"].items():
        assert sha256_file(REPO / source) == digest, f"source drift: {source}"


def recalculate(path, dataset, variant):
    pred, results = pd.read_csv(path / "predictions.csv"), pd.read_csv(path / "results.csv")
    rows = []
    for _, row in results.iterrows():
        group = pred[pred.policy == row.policy]
        assert group.row_index.is_unique
        assert abs(f1_score(group.label, group.prediction, average="macro", zero_division=0) - row.macro_f1_oof) < 1e-12
        assert abs(accuracy_score(group.label, group.prediction) - row.accuracy_oof) < 1e-12
        assert abs(group.projected_ms.mean() - row.projected_ms) < 1e-9
        rows.append({"dataset": dataset, "variant": variant, **row.to_dict()})
    return pred, rows


def main():
    table, receipts = [], {}
    for folder in ("carlos_fmd22_20261021", "carlos_outex22_20261021"):
        path = ROOT / folder
        meta = json.loads((path / "metadata.json").read_text())
        assert meta["status"] == "complete"
        verify_sources(meta)
        ref = Path(meta["reference_run"])
        reference = json.loads((ref / "metadata.json").read_text())
        assert sha256_file(ref / "metadata.json") == meta["reference_metadata_sha256"]
        arrays = np.load(path / "validation_scores.npz", allow_pickle=False)
        folds = json.loads((path / "folds.json").read_text())
        pred, rows = recalculate(path, meta["dataset"], "carlos_controls22")
        table.extend(rows)
        latency = meta["provenance"]["cost_profile"]["per_descriptor_latency_ms"]
        config = meta["archived_config"]
        expected_rows = set()
        for fold in folds:
            number = fold["producer_fold"]
            source = json.loads((ref / f"fold{number}.json").read_text())
            assert fold["fit_indices"] == source["fit_indices"]
            assert fold["validation_indices"] == source["validation_indices"]
            val = np.asarray(fold["validation_indices"])
            expected_rows.update(val)
            assert np.array_equal(arrays[f"fold{number}_rows"], val)
            library = fold["library_order"]
            cka_array = np.asarray(fold["cka_matrix"])
            assert np.isfinite(cka_array).all() and np.allclose(cka_array, cka_array.T)
            assert np.min(cka_array) >= -1e-12 and np.max(cka_array) <= 1 + 1e-12
            cka = {(a, b): float(cka_array[i, j]) for i, a in enumerate(library) for j, b in enumerate(library)}
            ranking, order = source["ranking"], source["ranked_blocks"]
            lo, hi = min(ranking.values()), max(ranking.values())
            relevance = {n: (v - lo) / ((hi - lo) or 1) for n, v in ranking.items()}
            seed = fold["nested_seed"]
            rng = np.random.default_rng(seed + int(config["lottery_beta"] * 2))
            lottery = [sorted(order[i] for i in rng.choice(len(order), size=4, replace=False,
                        p=rank_weights(order, config["lottery_beta"]))) for _ in range(15)]
            rng = np.random.default_rng(seed + int(config["diversity_lambda"] * 7) + int(config["diversity_beta"]))
            diversity = [draw_subset(sorted(library), relevance, cka, config["diversity_lambda"],
                                     config["diversity_beta"], 4, rng) for _ in range(15)]
            assert lottery == fold["lottery_members"] and diversity == fold["diversity_members"]
            score_map = dict(zip(map(tuple, fold["unique_subset_order"]), arrays[f"fold{number}_scores"]))
            labels = np.unique(pred.label)
            for name, members in (("carlos_lottery15", lottery), ("carlos_diversity15", diversity)):
                values = np.stack([score_map[tuple(member)] for member in members])
                soft = labels[np.argmax(values.mean(axis=0), axis=1)]
                votes = np.argmax(values, axis=2)
                hard = labels[[np.bincount(votes[:, i], minlength=len(labels)).argmax() for i in range(len(val))]]
                union = {block for subset in members for block in subset}
                for mode, expected in (("soft", soft), ("hard", hard)):
                    cell = pred[(pred.producer_fold == number) & (pred.policy == f"{name}_{mode}")].set_index("row_index").loc[val]
                    assert np.array_equal(cell.prediction, expected)
                    assert np.allclose(cell.projected_ms, sum(latency[n] for n in union), atol=1e-9, rtol=0)
                    assert cell.unique_classifier_calls.eq(len({tuple(s) for s in members})).all()
        assert hashlib.sha256(np.asarray(sorted(expected_rows), dtype="<i8").tobytes()).hexdigest() == reference["outer_train_indices_sha256"]
        audits = json.loads((path / "ngram_transforms.json").read_text())
        for audit in audits:
            a, b = set(audit["train_indices"]), set(audit["evaluation_indices"])
            assert not a.intersection(b) and (a | b).issubset(expected_rows)
        receipts[folder] = {"status": "ANALYZED", "folds": len(folds), "policies": len(rows),
                            "ngram_projections": len(audits), "score_aggregation_recalculated": True}

    path = ROOT / "outex_fixed_no_ngram_20261021_final"
    meta = json.loads((path / "metadata.json").read_text())
    verify_sources(meta)
    ref = Path(meta["reference_run"])
    assert sha256_file(ref / "metadata.json") == meta["reference_metadata_sha256"]
    reference = json.loads((ref / "metadata.json").read_text())
    latency = reference["provenance"]["cost_profile"]["per_descriptor_latency_ms"]
    overhead = reference["provenance"]["cost_profile"]["policy_overhead_ms"]
    original_pred = pd.read_csv(ref / "predictions.csv")
    arrays = np.load(path / "validation_scores.npz", allow_pickle=False)
    pred, rows = recalculate(path, meta["dataset"], "fixed_route_without_ngram")
    table.extend(rows)
    decisions = json.loads((path / "decisions.json").read_text())
    for decision in decisions:
        if not decision["eligible"]:
            continue
        fold, policy = decision["producer_fold"], decision["policy"]
        val = arrays[f"fold{fold}_rows"]
        subsets = [tuple(json.loads(value)) for value in arrays[f"fold{fold}_subset_json"]]
        values = dict(zip(subsets, arrays[f"fold{fold}_scores"]))
        base = decision["base"]
        margin = compute_margins(values[(base,)])
        members = decision["ablated_members"]
        assert members == [[n for n in subset if n != "rgb_ngram_svd"] for subset in decision["original_members"]]
        base_pred = np.unique(pred.label)[np.argmax(values[(base,)], axis=1)]
        gate = margin < decision["threshold"] if members else np.zeros(len(val), dtype=bool)
        rescue = (np.unique(pred.label)[np.argmax(np.mean([values[tuple(sorted(s))] for s in members], axis=0), axis=1)]
                  if members else base_pred)
        cell = pred[(pred.producer_fold == fold) & (pred.policy == policy)].set_index("row_index").loc[val]
        original = original_pred[(original_pred.producer_fold == fold) & (original_pred.policy == policy)].set_index("row_index").loc[val]
        assert np.array_equal(cell.prediction, np.where(gate, rescue, base_pred))
        assert np.array_equal(cell.escalated, original.escalated)
        assert np.allclose(cell.base_margin, original.base_margin, atol=1e-10, rtol=1e-10)
        union = {n for subset in members for n in subset}
        cost = (latency[base] + overhead + gate * sum(latency[n] for n in union - {base})
                if members else np.full(len(val), latency[base]))
        assert np.allclose(cell.projected_ms, cost, atol=1e-9, rtol=0)
        color = any("rgb_ngram_svd" in subset for subset in decision["original_members"])
        assert np.allclose(original.projected_ms - cell.projected_ms,
                           gate * latency["rgb_ngram_svd"] * color, atol=1e-9, rtol=0)
    receipts[path.name] = {"status": "ANALYZED", "policy_fold_decisions": len(decisions),
                           "route_and_color_cost_difference_recalculated": True}
    for folder, variant in (("budget_outex21_20261021", "reselected21"),):
        path = ROOT / folder
        meta = json.loads((path / "metadata.json").read_text())
        _, rows = recalculate(path, meta["dataset"], variant)
        table.extend(rows)
    for folder in ("budget_pilot_fmd_20261021", "budget_pilot_outex_20261021"):
        path = REPO / "results/exploratory/integration_v5" / folder
        meta = json.loads((path / "metadata.json").read_text())
        _, rows = recalculate(path, meta["dataset"], "budget22_reference")
        table.extend(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(table).to_csv(OUT / "comparison.csv", index=False)
    for folder in ("carlos_fmd22_20261021", "carlos_outex22_20261021", "outex_fixed_no_ngram_20261021_final", "budget_outex21_20261021"):
        path = ROOT / folder
        receipts.setdefault(folder, {"status": "ANALYZED"})["input_sha256"] = {
            file.name: sha256_file(file) for file in path.iterdir() if file.is_file()}
    (OUT / "summary.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print("matched Carlos policies recalculated: 8; frozen-route decisions: 24; comparison rows:", len(table))


if __name__ == "__main__":
    main()
