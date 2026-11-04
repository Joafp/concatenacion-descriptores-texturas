"""Fixed FMD/42 development adaptation, three paired producer folds, no external test."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def index_hash(values):
    import numpy as np
    return hashlib.sha256(np.asarray(values, dtype="<i8").tobytes()).hexdigest()


def run(output, protocol):
    import numpy as np
    import pandas as pd
    import torch
    from PIL import Image
    from sklearn.metrics import f1_score, accuracy_score
    from neshov_beit_reference import load_offline_backbone, preprocessing, FrozenLayerAggregation
    from neshov_reference_training import validate_partition_panel, fit_fixed_head

    output, protocol = Path(output).resolve(), Path(protocol).resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preflight", "dataset": "FMD", "seed": 42,
              "scope": "Reimplementation adapted to common development folds; not original-paper replication",
              "external_test_evaluated": False, "physical_latency_published": False,
              "new_inferential_tests": 0, "device": "cpu", "cpu_threads": 2,
              "protocol_sha256": digest(protocol),
              "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
                    [Path(__file__), ROOT / "src/neshov_beit_reference.py", ROOT / "src/neshov_reference_training.py"]},
              "recipe": {"layers_one_based": [2, 5, 8, 11], "cls_excluded": True,
                         "dimensions": 3072, "head_hidden": 64, "head_dropout": .2,
                         "epochs": 100, "head_batch": 32, "extraction_batch": 8,
                         "adam_lr": .001, "adam_weight_decay": .0001,
                         "adam_betas": [.9, .999], "epoch_selection": "final; no early stopping",
                         "feature_l2_normalization": False}}

    def save():
        (output / "status.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    try:
        torch.set_num_threads(2)
        torch.manual_seed(42)
        torch.use_deterministic_algorithms(True)
        audit_path = ROOT / "results/analysis/mesa_replication_20261026/FMD_s42.json"
        audit = read(audit_path)
        assert audit["status"] == "ANALYZED"
        suite = ROOT / "results/exploratory/integration_v11/replication_20261026/FMD_s42"
        ref = suite / "paired"
        fold_paths = [ref / f"fold{i}.json" for i in range(3)]
        manifest = ROOT / "results/confirmatory/sample_manifests/FMD.csv"
        metadata = ref / "metadata.json"
        sources = fold_paths + [manifest, metadata]
        for p in sources:
            assert digest(p) == audit["input_sha256"][str(p.relative_to(ROOT))], str(p)
        folds = [read(p) for p in fold_paths]
        rows = validate_partition_panel(folds)
        assert len(rows) == 800 and index_hash(rows) == read(metadata)["outer_train_indices_sha256"]
        with manifest.open(newline="") as stream:
            records = list(csv.DictReader(stream))
        assert len(records) == 1000 and all(int(r["row_id"]) == i for i, r in enumerate(records))
        external = sorted(set(range(1000)) - set(rows.tolist()))
        assert len(external) == 200 and index_hash(external) == read(metadata)["external_test_indices_sha256"]
        y = np.array([int(records[i]["label"]) for i in rows])
        assert np.array_equal(np.unique(y), np.arange(10))
        lookup = {int(i): p for p, i in enumerate(rows)}
        for f in folds:
            fit_groups = {records[i]["group"] for i in f["fit_indices"]}
            assert not fit_groups & {records[i]["group"] for i in f["validation_indices"]}
        report.update(status="recipe_and_indices_frozen_before_extraction",
                      rows=rows.tolist(), external_rows_not_evaluated=len(external),
                      producer_folds=3, development_images=800,
                      input_sha256={str(p.relative_to(ROOT)): digest(p) for p in sources + [audit_path]})
        save()
        backbone, checkpoint = load_offline_backbone()
        extractor, transform = FrozenLayerAggregation(backbone).eval(), preprocessing()
        report.update(status="extracting", weights=checkpoint,
                      checkpoint_sha256=digest(checkpoint["local_weight_path"]),
                      torch_version=torch.__version__)
        save()
        chunks, image_hashes = [], {}
        for start in range(0, len(rows), 8):
            images = []
            for idx in rows[start:start + 8]:
                record = records[int(idx)]
                path = Path(record["path"])
                if not path.is_absolute():
                    path = ROOT / path
                actual = digest(path)
                assert actual == record["sha256"], str(path)
                image_hashes[str(int(idx))] = actual
                with Image.open(path) as image:
                    images.append(transform(image.convert("RGB")))
            chunk = extractor(torch.stack(images)).numpy()
            assert chunk.shape == (len(images), 3072) and np.isfinite(chunk).all()
            chunks.append(chunk)
            report["extracted_rows"] = start + len(images)
            save()
            if start == 0 or (start + len(images)) % 80 == 0:
                print(f"Extracted {start + len(images)}/800 development images", flush=True)
        features = np.concatenate(chunks)
        np.savez_compressed(output / "features.npz", rows=rows, features=features)
        (output / "image_sha256.json").write_text(json.dumps(image_hashes, indent=2) + "\n")
        del extractor, backbone
        predictions, fold_metrics, history = [], [], []
        for number, fold in enumerate(folds):
            fit = np.array([lookup[i] for i in fold["fit_indices"]])
            val = np.array([lookup[i] for i in fold["validation_indices"]])
            report.update(status="training_head", producer_fold=number, epochs_per_head=100)
            save()
            head, losses = fit_fixed_head(features[fit], y[fit], 10)
            with torch.inference_mode():
                logits = head(torch.from_numpy(features[val])).numpy()
            pred = logits.argmax(axis=1)
            for offset, position in enumerate(val):
                predictions.append({"row_index": int(rows[position]), "producer_fold": number,
                                    "label": int(y[position]), "prediction": int(pred[offset])})
            np.savez_compressed(output / f"fold{number}_logits.npz", rows=rows[val], logits=logits)
            torch.save(head.state_dict(), output / f"fold{number}_head.pt")
            history += [{"producer_fold": number, **r} for r in losses]
            fold_metrics.append({"producer_fold": number, "n_fit": len(fit), "n_validation": len(val),
                                 "macro_f1": float(f1_score(y[val], pred, labels=np.arange(10), average="macro", zero_division=0)),
                                 "accuracy": float(accuracy_score(y[val], pred))})
            print(f"Head fold {number}: 100 fixed epochs complete", flush=True)
        frame = pd.DataFrame(predictions).sort_values("row_index")
        assert len(frame) == frame.row_index.nunique() == 800 and np.array_equal(frame.row_index, rows)
        assert np.array_equal(frame.label, y)
        frame.to_csv(output / "predictions.csv", index=False)
        pd.DataFrame(history).to_csv(output / "training_history.csv", index=False)
        pd.DataFrame(fold_metrics).to_csv(output / "fold_metrics.csv", index=False)
        report.update(status="development_pilot_complete",
                      pooled_macro_f1=float(f1_score(y, frame.prediction, labels=np.arange(10), average="macro", zero_division=0)),
                      pooled_accuracy=float(accuracy_score(y, frame.prediction)),
                      mean_producer_fold_f1=float(np.mean([m["macro_f1"] for m in fold_metrics])),
                      head_trained=True, fitted_heads=3, out_of_fold_predictions=800,
                      limitations=["One dataset and one split seed, not six datasets",
                                   "Adapted producer folds, not the paper's 10x10 FMD protocol",
                                   "Layer/CLS/interpolation/software decisions documented before execution",
                                   "No inference latency measured; no statistical significance claim"])
        report["output_sha256"] = {p.name: digest(p) for p in output.iterdir() if p.name != "status.json"}
        save()
        print(json.dumps({k: report[k] for k in ["status", "pooled_macro_f1", "pooled_accuracy", "out_of_fold_predictions"]}), flush=True)
    except Exception as exc:
        report.update(status="FAILED_NO_AUTOMATIC_RETRY", error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    args = p.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args.output, args.protocol)
