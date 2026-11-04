#!/usr/bin/env python3
"""Evaluate archived lottery/diversity recipes on the budget pilot's producer folds.

Reuses Carlos's sampling functions with corrected frozen training-score scales.
The nested producer protocol and optional 22nd block are explicit adaptations,
so these controls are not claimed to reproduce archived external metrics.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

from run_confirmatory_nested import load_dataset, load_manifest
from run_diversity_lottery import draw_subset
from run_weighted_lottery_selection import rank_weights
from run_rescue_nested_selection import (
    REPO, COMMON_21, fit_scores, block_matrices, load_existing_ngram,
    sha256_file, launch_provenance,
)
from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS as LATENCIES


def gram_similarities(matrices):
    """Exact linear CKA in row-Gram space, avoiding repeated feature Gram products."""
    grams = {}
    for name, values in matrices.items():
        x = np.asarray(values, dtype=np.float64)
        x = x - x.mean(axis=0, keepdims=True)
        grams[name] = x @ x.T
    norms = {name: np.linalg.norm(gram, ord="fro") for name, gram in grams.items()}
    return {(a, b): float(np.sum(grams[a] * grams[b]) / (norms[a] * norms[b]))
            if norms[a] * norms[b] > 0 else 0.
            for a in grams for b in grams}


def ensemble_predictions(scores, members, labels):
    soft = np.mean([scores[tuple(member)] for member in members], axis=0)
    soft_pred = labels[np.argmax(soft, axis=1)]
    votes = np.stack([np.argmax(scores[tuple(member)], axis=1) for member in members])
    hard_pred = labels[np.asarray([np.bincount(votes[:, i], minlength=len(labels)).argmax()
                                   for i in range(votes.shape[1])])]
    return soft_pred, hard_pred


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ref = (REPO / args.reference_run).resolve() if not args.reference_run.is_absolute() else args.reference_run
    output = (REPO / args.output).resolve() if not args.output.is_absolute() else args.output
    if output.exists() and any(output.iterdir()):
        parser.error("choose an empty output directory")
    reference = json.loads((ref / "metadata.json").read_text())
    if reference["status"] != "complete":
        parser.error("reference run is not complete")
    for source, digest in reference["provenance"]["source_sha256"].items():
        if sha256_file(REPO / source) != digest:
            parser.error(f"reference source drift: {source}")
    cfg = reference["provenance"]["arguments"]
    def resolve(value):
        if value is None:
            return None
        value = Path(value)
        return (REPO / value).resolve() if not value.is_absolute() else value
    cache, y = load_dataset(REPO, reference["dataset"], resolve(cfg["embedding_root"]))
    cache = {name: cache[name] for name in COMMON_21}
    manifest_root = resolve(cfg["manifest_root"])
    groups, rows = load_manifest(manifest_root, reference["dataset"], y)
    ngram, ng_provenance = (load_existing_ngram(rows, resolve(cfg["ngram_count_cache"]), 256, 8192, cfg["seed"])
                           if len(reference["library"]) == 22 else (None, None))
    library, labels = reference["library"], np.unique(y)
    archive = REPO / "results/analysis/selection_tables/svm.json"
    archive_config = json.loads(archive.read_text())["ensemble_configuration"]
    beta, lam = archive_config["diversity_beta"], archive_config["diversity_lambda"]
    lottery_beta, k, draws = archive_config["lottery_beta"], 4, 15
    started = time.perf_counter()
    provenance = launch_provenance(args, manifest_root / "sample_manifests" / f"{reference['dataset']}.csv",
                                   cache, y, {"per_descriptor_latency_ms": LATENCIES})
    for key in ("manifest_sha256", "labels_sha256", "embedding_array_sha256"):
        if provenance[key] != reference["provenance"][key]:
            raise ValueError(f"reference input drift: {key}")
    if ng_provenance != reference["provenance"]["ngram_count_cache"]:
        raise ValueError("reference N-gram cache/configuration drift")
    for file in (Path(__file__), REPO / "src/run_diversity_lottery.py"):
        provenance["source_sha256"][str(file.relative_to(REPO))] = sha256_file(file)
    provenance["ngram_count_cache"] = ng_provenance
    metadata = {"status": "running", "dataset": reference["dataset"], "library": library,
                "reference_metadata_sha256": sha256_file(ref / "metadata.json"),
                "reference_run": str(ref), "archived_config": archive_config,
                "archive_config_file_sha256": sha256_file(archive),
                "members": draws, "subset_size": k, "provenance": provenance,
                "scope": "nested static controls adapted to the matched pilot library; no external evaluation",
                "outer_train_indices_sha256": reference["outer_train_indices_sha256"],
                "external_test_indices_sha256": reference["external_test_indices_sha256"],
                "classifier_latency_included": False}
    output.mkdir(parents=True, exist_ok=True)
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    predictions, score_arrays, fold_records = [], {}, []
    for file in sorted(ref.glob("fold*.json")):
        fold = json.loads(file.read_text())
        number = fold["producer_fold"]
        fit, val = np.asarray(fold["fit_indices"]), np.asarray(fold["validation_indices"])
        if set(groups[fit]).intersection(groups[val]):
            raise AssertionError("source group overlap")
        mats = {name: block_matrices(cache, [name], fit, val, ngram)[0] for name in library}
        cka = gram_similarities(mats)
        del mats
        ranking = fold["ranking"]
        lo, hi = min(ranking.values()), max(ranking.values())
        relevance = {name: (value - lo) / ((hi - lo) or 1.) for name, value in ranking.items()}
        rank_order = fold["ranked_blocks"]
        nested_seed = cfg["seed"] * 100000 + cfg["fold"] * 1000 + number * 10
        rng = np.random.default_rng(nested_seed + int(lottery_beta * 2))
        lottery = [sorted(rank_order[i] for i in rng.choice(
            len(rank_order), size=k, replace=False, p=rank_weights(rank_order, lottery_beta)))
                   for _ in range(draws)]
        rng = np.random.default_rng(nested_seed + int(lam * 7) + int(beta))
        diversity = [draw_subset(sorted(library), relevance, cka, lam, beta, k, rng) for _ in range(draws)]
        all_subsets = sorted({tuple(s) for s in lottery + diversity})
        scores, scales = {}, {}
        for subset in all_subsets:
            value, _, scale = fit_scores(cache, list(subset), fit, val, y, labels, cfg["seed"], ngram)
            scores[subset], scales[subset] = value, scale
        for name, members in (("carlos_lottery15", lottery), ("carlos_diversity15", diversity)):
            soft, hard = ensemble_predictions(scores, members, labels)
            union = sorted({block for subset in members for block in subset})
            cost = sum(LATENCIES[block] for block in union)
            unique = len({tuple(s) for s in members})
            for mode, prediction in (("soft", soft), ("hard", hard)):
                for pos, row_index in enumerate(val):
                    predictions.append({"row_index": int(row_index), "label": int(y[row_index]),
                        "producer_fold": number, "policy": f"{name}_{mode}",
                        "prediction": int(prediction[pos]), "projected_ms": cost,
                        "unique_classifier_calls": unique})
        score_arrays[f"fold{number}_rows"] = val
        score_arrays[f"fold{number}_scores"] = np.stack([scores[subset] for subset in all_subsets])
        fold_records.append({"producer_fold": number, "fit_indices": fit.tolist(),
            "validation_indices": val.tolist(), "library_order": library,
            "cka_matrix": [[cka[(a, b)] for b in library] for a in library],
            "lottery_members": lottery, "diversity_members": diversity,
            "unique_subset_order": [list(s) for s in all_subsets],
            "training_score_scales": [float(scales[s]) for s in all_subsets],
            "nested_seed": nested_seed})
        print(f"completed matched Carlos controls fold {number}: {len(all_subsets)} unique models", flush=True)
    pred = pd.DataFrame(predictions)
    results = [{"policy": name, "n_rows": len(frame),
                "macro_f1_oof": f1_score(frame.label, frame.prediction, average="macro", zero_division=0),
                "accuracy_oof": accuracy_score(frame.label, frame.prediction),
                "projected_ms": frame.projected_ms.mean(),
                "unique_classifier_calls": frame.unique_classifier_calls.mean()}
               for name, frame in pred.groupby("policy")]
    pred.to_csv(output / "predictions.csv", index=False)
    pd.DataFrame(results).to_csv(output / "results.csv", index=False)
    (output / "folds.json").write_text(json.dumps(fold_records, indent=2) + "\n")
    np.savez_compressed(output / "validation_scores.npz", **score_arrays)
    audits = ngram.transformation_audits() if ngram else []
    allowed = {row for fold in fold_records for row in fold["validation_indices"]}
    for audit in audits:
        a, b = set(audit["train_indices"]), set(audit["evaluation_indices"])
        if a.intersection(b) or not (a | b).issubset(allowed):
            raise AssertionError("N-gram projection outside outer training")
    (output / "ngram_transforms.json").write_text(json.dumps(audits, indent=2) + "\n")
    metadata.update(status="complete", elapsed_seconds=time.perf_counter() - started)
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()
