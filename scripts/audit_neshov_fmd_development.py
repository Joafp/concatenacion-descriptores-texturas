"""Replay saved MLP heads and compare frozen controls on the same FMD rows."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def audit(run, output):
    import numpy as np
    import pandas as pd
    import torch
    from neshov_beit_reference import ReferenceMLP
    from matched_reference_quality import aligned_quality
    from neshov_reference_training import validate_partition_panel

    run, output = Path(run).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    report = read(run / "status.json")
    assert report["status"] == "development_pilot_complete"
    assert not report["external_test_evaluated"] and not report["physical_latency_published"]
    assert report["recipe"]["epoch_selection"] == "final; no early stopping"
    for group in ("source_sha256", "input_sha256"):
        for name, expected in report[group].items():
            assert digest(ROOT / name) == expected, name
    for name, expected in report["output_sha256"].items():
        assert digest(run / name) == expected, name
    protocol = ROOT / "docs/fsc_tex/PROTOCOLO_PILOTO_NESHOV_FMD_2026-10-28.md"
    assert digest(protocol) == report["protocol_sha256"]
    archive = ROOT / "results/exploratory/integration_v11/replication_20261026/FMD_s42"
    folds = [read(archive / "paired" / f"fold{i}.json") for i in range(3)]
    expected_rows = validate_partition_panel(folds)
    data = np.load(run / "features.npz", allow_pickle=False)
    rows, features = data["rows"], data["features"]
    assert np.array_equal(rows, expected_rows) and features.shape == (800, 3072)
    lookup = {int(row): pos for pos, row in enumerate(rows)}
    predictions = pd.read_csv(run / "predictions.csv")
    assert len(predictions) == predictions.row_index.nunique() == 800
    torch.set_num_threads(2)
    replayed = 0
    for f, fold in enumerate(folds):
        cached = np.load(run / f"fold{f}_logits.npz", allow_pickle=False)
        ids = np.array(fold["validation_indices"])
        assert np.array_equal(cached["rows"], ids)
        head = ReferenceMLP(3072, 10)
        head.load_state_dict(torch.load(run / f"fold{f}_head.pt", map_location="cpu", weights_only=True), strict=True)
        with torch.inference_mode():
            logits = head.eval()(torch.from_numpy(features[[lookup[int(i)] for i in ids]])).numpy()
        assert np.array_equal(logits, cached["logits"]), f"logit replay differs in fold {f}"
        saved = predictions[predictions.producer_fold == f].set_index("row_index").loc[ids]
        assert np.array_equal(logits.argmax(axis=1), saved.prediction)
        replayed += len(ids)
    quality = aligned_quality(predictions, predictions)
    assert abs(quality["macro_f1"] - report["pooled_macro_f1"]) < 1e-12
    assert abs(quality["accuracy"] - report["pooled_accuracy"]) < 1e-12
    controls = ROOT / "results/exploratory/integration_v12/matched_concat_20261026/FMD_s42/controls"
    specs = [
        ("Individual", "SVM", archive / "paired/predictions.csv", "best_individual"),
        ("Completa-22", "SVM", archive / "paired/predictions.csv", "full_library"),
        ("Top-k", "SVM", controls / "predictions.csv", "topk_gfs_size"),
        ("Top-4", "SVM", archive / "paired/predictions.csv", "top4"),
        ("GFS", "SVM", controls / "predictions.csv", "gfs"),
        ("Ensamble permanente", "SVM", archive / "hybrid/predictions.csv", "carlos_diversity15_always"),
        ("Ensamble diversidad, voto hard", "SVM", archive / "carlos/predictions.csv", "carlos_diversity15_hard"),
        ("Ensamble tombola, voto hard", "SVM", archive / "carlos/predictions.csv", "carlos_lottery15_hard"),
        ("Ensamble tombola, voto soft", "SVM", archive / "carlos/predictions.csv", "carlos_lottery15_soft"),
        ("Ensamble estatico", "SVM", archive / "static_recovery/predictions.csv", "static_B60"),
        ("Seleccion y margen, pool previo", "SVM", archive / "paired/predictions.csv", "relevance_B60"),
        ("Seleccion y margen, diversidad", "SVM", archive / "hybrid/predictions.csv", "pruned_relevance_B60"),
    ]
    expected_hashes = {}
    audit_paths = [ROOT / "results/analysis/mesa_replication_20261026/FMD_s42.json",
                   ROOT / "results/analysis/matched_concat_20261026/FMD_s42.json"]
    for path in audit_paths:
        a = read(path)
        assert a["status"] == "ANALYZED"
        for name, value in a["input_sha256"].items():
            assert name not in expected_hashes or expected_hashes[name] == value
            expected_hashes[name] = value
    panel = [{"method": "Neshov BEiTv2 adaptado", "classifier": "MLP (64)", **quality}]
    source_paths = [run / "status.json", protocol, *audit_paths]
    for name, classifier, path, policy in specs:
        assert digest(path) == expected_hashes[str(path.relative_to(ROOT))], str(path)
        frame = pd.read_csv(path)
        selected = frame[frame.policy == policy]
        panel.append({"method": name, "classifier": classifier, **aligned_quality(predictions, selected)})
        source_paths.append(path)
    output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(panel).to_csv(output / "matched_quality.csv", index=False)
    summary = {"status": "ANALYZED", "condition": "FMD_s42", "datasets": 1,
               "split_seeds": 1, "producer_folds": 3, "development_images": 800,
               "head_predictions_replayed": replayed, "logits_exactly_replayed": True,
               "backbone_features_independently_reextracted": False,
               "source_author_predictions_available": False,
               "original_paper_scores_reproduced": False,
               "external_test_evaluated": False, "physical_latency_published": False,
               "new_inferential_tests": 0,
               "scope": "Descriptive quality on identical development rows/folds; MLP and SVM are different complete systems",
               "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in set(source_paths)},
               "audit_script_sha256": digest(__file__),
               "matched_quality_sha256": digest(output / "matched_quality.csv")}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(pd.DataFrame(panel).to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    audit(args.run, args.output)
