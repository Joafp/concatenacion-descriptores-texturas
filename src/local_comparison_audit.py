"""Audit archived reference F1 without silently dropping duplicate conditions.

This module does not manufacture adaptive results or infer latency from fit time.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

KEYS = ["dataset", "seed", "outer_fold"]
METHODS = ["Completa-22", "Ens-diversidad", "Ens-tombola", "Top-4"]


def unique_conditions(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    if frame.empty or frame.duplicated(KEYS).any():
        raise ValueError(f"{label}: empty or duplicate condition keys")
    values = pd.to_numeric(frame["macro_f1"], errors="raise")
    if not np.isfinite(values).all() or not values.between(0, 1).all():
        raise ValueError(f"{label}: invalid macro-F1")
    return frame.set_index(KEYS).sort_index()


def paired_frames(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    checked = {name: unique_conditions(frame, name) for name, frame in frames.items()}
    expected = next(iter(checked.values())).index
    if any(not value.index.equals(expected) for value in checked.values()):
        raise ValueError("Reference methods do not cover identical conditions")
    return pd.DataFrame({name: frame["macro_f1"] for name, frame in checked.items()})


def audit(root: Path) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    sources: dict[str, str] = {}

    def read(path):
        sources[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return pd.read_csv(path)

    def read_many(pattern):
        paths = sorted(root.glob(pattern))
        if not paths:
            raise FileNotFoundError(pattern)
        return pd.concat([read(path) for path in paths], ignore_index=True)

    full = read(root / "paper/articulo/borrador_profesor/generated/primary22_beitv2_source_rows.csv")
    detailed, coverage, libraries = [], [], []
    for classifier in ("svm", "resmlp"):
        prefix = "results/exploratory" + ("/resmlp" if classifier == "resmlp" else "")
        sweep = read_many(prefix + "/k_sweep/*/k_sweep.csv")
        diversity = read_many(prefix + "/k4/diversity/*/diversity_rows.csv")
        lottery = read_many(prefix + "/k4/lottery/*/lottery_rows.csv")
        frames = {
            "Completa-22": full[(full.classifier == classifier) & (full.run_mode == "full") & (full.method == "full_concat")],
            "Top-4": sweep[(sweep.classifier == classifier) & (sweep.k == 4)],
            "Ens-diversidad": diversity[(diversity.classifier == classifier) & (diversity.k == 4)
                & (diversity.variant == "ensemble_soft") & (diversity["lambda"] == .25) & (diversity.beta == 8)],
            "Ens-tombola": lottery[(lottery.classifier == classifier) & (lottery.k == 4)
                & (lottery.variant == "ensemble_soft") & (lottery.beta == 8)],
        }
        paired = paired_frames(frames)
        archived = read(root / f"results/analysis/selection_stats/{classifier}_metodos.csv").set_index("Data-set")
        short = {"KTHTIPS2b": "KTH-TIPS2-b", "Outex13Official1360": "Outex", "SoilOriginal": "Soil"}
        for dataset, group in paired.groupby(level="dataset"):
            for method in METHODS:
                mean = float(group[method].mean())
                error = abs(mean - float(archived.loc[short.get(dataset, dataset), method]))
                if error > 1e-9:
                    raise ValueError(f"Archived table mismatch: {classifier}/{dataset}/{method}: {error}")
                coverage.append({"classifier": classifier, "dataset": dataset, "method": method,
                    "conditions": len(group), "archived_macro_f1": mean,
                    "table_abs_error": error, "measured_ms_per_image": None,
                    "quality_status": "archived_condition_metrics_reaggregated_not_predictions_replayed",
                    "latency_status": "not_measured_for_this_panel"})
            coverage.append({"classifier": classifier, "dataset": dataset, "method": "Adaptive-selection-margin",
                "conditions": len(group), "archived_macro_f1": None, "table_abs_error": None,
                "measured_ms_per_image": None, "quality_status": "matched_external_evaluation_pending",
                "latency_status": "not_measured_for_this_panel"})
        rows = paired.reset_index()
        rows.insert(0, "classifier", classifier)
        detailed.append(rows)
        for family, pattern in (("diversity", "k4/diversity/*/*_diversity.json"),
                                ("lottery", "k4/lottery/*/*_lottery.json")):
            records = []
            for path in sorted(root.glob(prefix + "/" + pattern)):
                value = json.loads(path.read_text())
                if value.get("classifier") != classifier:
                    continue
                key = (value["dataset"], value["seed"], value["outer_fold"])
                if key not in paired.index:
                    continue
                sources[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
                members = (next(c for c in value["cells"] if c["lambda"] == .25 and c["beta"] == 8)["subsets"]
                           if family == "diversity" else
                           [d["subset"] for d in next(c for c in value["betas"] if c["beta"] == 8)["draws"]])
                if len(members) != 15 or any(len(m) != 4 or len(set(m)) != 4 for m in members):
                    raise ValueError(f"Unexpected ensemble recipe: {path}")
                union = sorted({b for member in members for b in member})
                ranking = value.get("ranking")
                candidate_names = [v["block"] for v in ranking] if ranking else None
                records.append(key)
                libraries.append({"classifier": classifier, "family": family,
                    "dataset": key[0], "seed": key[1], "outer_fold": key[2],
                    "n_candidates": value["n_candidates"], "draws": len(members),
                    "distinct_members": len({tuple(m) for m in members}),
                    "union_blocks": len(union), "union_contains_ngram": "rgb_ngram_svd" in union,
                    "candidate_contains_ngram": ("rgb_ngram_svd" in candidate_names if candidate_names is not None else None),
                    "score_normalization": value.get("score_normalization", "not_recorded"),
                    "training_score_scales_recorded": ("member_score_scales" in next(
                        c for c in value["cells"] if c["lambda"] == .25 and c["beta"] == 8)
                        if family == "diversity" else all("score_scale" in d for d in next(
                            c for c in value["betas"] if c["beta"] == 8)["draws"])),
                    "source": str(path.relative_to(root))})
            if len(records) != len(paired) or len(set(records)) != len(records):
                raise ValueError(f"JSON recipe coverage mismatch: {classifier}/{family}")
    report = {"status": "ARCHIVED_METRICS_REAGGREGATED", "predictions_replayed": False,
        "physical_latency_published": False, "adaptive_external_results_available_in_this_panel": False,
        "reference_condition_rows": sum(len(d) for d in detailed),
        "source_sha256": sources, "recipe_library_audit": libraries,
        "warning": "Same condition keys do not prove image, class, or prediction parity; reconcile manifests before new evaluation."}
    return report, pd.concat(detailed, ignore_index=True), pd.DataFrame(coverage)
