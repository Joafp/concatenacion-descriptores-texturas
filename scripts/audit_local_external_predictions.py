"""Replay a completed external panel image by image from its saved heads.

Uses cached embeddings, not online image extractors. No fitting of heads or
new model selection; N-gram projection is reconstructed from training rows.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    import joblib
    import numpy as np
    import pandas as pd
    import torch
    from sklearn.metrics import f1_score, accuracy_score
    from ensemble_scoring import decision_scores
    from frozen_ensemble_route import evaluate_route
    from run_confirmatory_nested import load_dataset, load_manifest
    from run_rescue_nested_selection import load_existing_ngram

    torch.set_num_threads(2)
    run_dir = args.run.resolve()
    status = json.loads((run_dir / "status.json").read_text())
    if status["status"] != "external_quality_complete_timing_pending":
        raise ValueError("run is not complete")
    for name, expected in status["output_sha256"].items():
        if digest(run_dir / name) != expected:
            raise ValueError(f"output drift: {name}")
    if digest(run_dir / "frozen_decisions.json") != status["frozen_decisions_sha256"]:
        raise ValueError("frozen decision drift")
    cfg_path = Path(status["provenance"]["arguments"]["reference_config"])
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    if digest(cfg_path) != status["reference_config_sha256"]:
        raise ValueError("configuration drift")
    cfg = json.loads(cfg_path.read_text())["provenance"]["arguments"]

    def resolve(path):
        p = Path(path)
        return p if p.is_absolute() else ROOT / p

    frozen = json.loads((run_dir / "frozen_decisions.json").read_text())
    heads = joblib.load(run_dir / "fitted_heads.joblib")
    fit, test = np.asarray(status["training_indices"]), np.asarray(status["external_indices"])
    if set(fit) & set(test) or not np.array_equal(fit, heads["training_indices"]) or not np.array_equal(test, heads["external_indices"]):
        raise ValueError("partition overlap or drift")
    validation_rows = []
    for split in frozen["inner_splits"]:
        a, b = set(split["fit_indices"]), set(split["validation_indices"])
        if a & b or a | b != set(fit):
            raise ValueError("selection split is not training-only")
        validation_rows += split["validation_indices"]
    if sorted(validation_rows) != sorted(fit.tolist()):
        raise ValueError("incomplete/repeated OOF coverage")
    cache, y = load_dataset(ROOT, status["dataset"], resolve(cfg["embedding_root"]))
    _, rows = load_manifest(resolve(cfg["manifest_root"]), status["dataset"], y)
    ng, _ = load_existing_ngram(rows, resolve(cfg["ngram_count_cache"]), 256, 8192, cfg["seed"])
    _, ng_test, _ = ng.transform(fit, test)
    archived = pd.read_csv(run_dir / "predictions.csv")
    metrics = pd.read_csv(run_dir / "metrics.csv").set_index("policy")
    rows_out, methods = [], []
    for policy, recipe in frozen["recipes"].items():
        recorded = archived[archived.policy == policy].set_index("row_index")
        if recorded.index.has_duplicates or set(recorded.index) != set(test):
            raise ValueError("prediction coverage mismatch")
        predictions = []
        for position, idx in enumerate(test):
            def acquire(name):
                return ng_test[position] if name == ng.name else cache[name][idx]

            def score(member, x):
                model, scale = heads["models"][member]
                return decision_scores(model, x, scale)

            result = evaluate_route(recipe, acquire, score, heads["labels"])
            # evaluate_route calls any unconditional static member evaluation
            # "escalated". In this panel escalation means a conditional rescue.
            if not recipe.get("base"):
                result["escalated"] = False
            row = recorded.loc[idx]
            if result["prediction"] != row.prediction or result["escalated"] != bool(row.escalated) or row.label != y[idx]:
                raise ValueError(f"prediction or gate mismatch: {policy}/{idx}")
            predictions.append(result["prediction"])
            rows_out.append({"policy": policy, "row_index": int(idx), **result})
        f1 = float(f1_score(y[test], predictions, labels=heads["labels"], average="macro", zero_division=0))
        accuracy = float(accuracy_score(y[test], predictions))
        if abs(f1 - metrics.loc[policy, "macro_f1"]) > 1e-12 or abs(accuracy - metrics.loc[policy, "accuracy"]) > 1e-12:
            raise ValueError("metric mismatch")
        methods.append({"policy": policy, "macro_f1": f1, "accuracy": accuracy, "rows": len(test)})
        print(f"Replayed {policy}: {len(test)} classes/gates match", flush=True)
    args.output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(rows_out).to_csv(args.output / "replayed_predictions.csv", index=False)
    report = {"status": "CACHED_HEAD_PREDICTIONS_REPLAYED", "physical_latency_validated": False,
        "online_extractor_parity_validated": False, "new_head_fits": 0,
        "source_status_sha256": digest(run_dir / "status.json"), "source_sha256": digest(__file__),
        "prediction_rows_replayed": len(rows_out), "methods": methods}
    (args.output / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
