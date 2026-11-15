#!/usr/bin/env python3
"""Prepare E1/E2 inputs without fitting, predicting, extracting or benchmarking.

Checks the existing fixed-four ranking, archives, cached labels, NPY shapes,
outer/inner partitions and component-cost coverage. Writes to a new folder.
The receipt is input preparation, not a runnable worker or completed experiment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from run_confirmatory_nested import audit_gate, canonical_labels, load_manifest, manifest_groups
from run_train_selected_topk_cascade import outer_split
from report_cost_aware_topk import DEFAULT_KTH_COST, DEFAULT_PROXY_COST, component_costs

DATASETS = {
    "DTD": ("dtd", "dtd", "embeddings", 10),
    "FMD": ("fmd", "fmd", "embeddings_confirmatory", 5),
    "CUReT": ("curet", "curet", "embeddings_confirmatory", 2),
    "Outex13Official1360": ("outex13_official1360", "outex13", "embeddings_extensions", 1),
    "SoilOriginal": ("soil_original", "soil_original", "embeddings_extensions", 5),
    "KTHTIPS2b": ("kth_tips2b", "kth_tips2b", "embeddings_extensions", 4),
}
CHEAP = ["resnet50", "siglip_base", "beitv2_base_final", "convnext_v2_t"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fixed_four(rows: list[dict], dataset: str) -> dict[int, list[str]]:
    """Use the saved selection only; never choose blocks by external F1."""
    result = {}
    for row in rows:
        if row["dataset"] != dataset or row["classifier"] != "svm":
            continue
        if int(row["seed"]) != 42 or int(row["k"]) != 4:
            continue
        fold = int(row["outer_fold"])
        blocks = row["selected"].split("+")
        if fold in result:
            raise ValueError(f"duplicate fixed-four condition: {dataset}/{fold}")
        if len(blocks) != 4 or len(set(blocks)) != 4 or not all(blocks):
            raise ValueError(f"exactly four unique blocks required: {dataset}/{fold}")
        if "rgb_ngram_svd" in blocks:
            raise ValueError("E1 uses the existing no-N-gram sweep, not E5")
        result[fold] = blocks
    return result


def disjoint_indices(train: np.ndarray, test: np.ndarray, size: int,
                     excluded: list[int] | None = None) -> None:
    train_ids, test_ids = set(map(int, train)), set(map(int, test))
    if len(train_ids) != len(train) or len(test_ids) != len(test):
        raise ValueError("duplicate row in split")
    if not train_ids or not test_ids or train_ids & test_ids:
        raise ValueError("empty or overlapping split")
    excluded_ids = set(excluded or [])
    if excluded_ids & (train_ids | test_ids) or not excluded_ids.issubset(range(size)):
        raise ValueError("invalid declared exclusions")
    if train_ids | test_ids | excluded_ids != set(range(size)):
        raise ValueError("split does not cover all rows and declared exclusions")


def duplicate_exclusions(rows: list[dict], protocol: str) -> list[int]:
    """Account for the existing official-split duplicate-content purge exactly."""
    if not protocol.startswith("official"):
        return []
    split = int(protocol.removeprefix("official").split("_")[0])
    column = f"split_{split}" if f"split_{split}" in rows[0] else "official_split"
    test_groups = {r["group"] for r in rows if r[column] == "test"}
    return [i for i, row in enumerate(rows)
            if row[column] in {"train", "val"} and row["group"] in test_groups]


def cost_coverage(blocks: list[str], costs: dict[str, float]) -> tuple[dict, list[str]]:
    """Keep missing costs explicit; never replace them with a different profile."""
    return {b: costs.get(b) for b in sorted(set(blocks))}, sorted(set(blocks) - costs.keys())


def prepare(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"Preparation already exists: {output}")
    sources = {}

    def record(path: Path) -> Path:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in sources:
            sources[relative] = {"sha256": sha256(path), "bytes": path.stat().st_size}
        return path

    source_files = [Path(__file__), ROOT / "tests/test_prepare_top4_fixed_cascade.py",
                    ROOT / "src/run_confirmatory_nested.py",
                    ROOT / "src/run_topk_individual_control.py",
                    ROOT / "src/singleton_ranking.py",
                    ROOT / "scripts/run_train_selected_topk_cascade.py",
                    ROOT / "scripts/run_cheap_stage_selected_cascade.py",
                    ROOT / "scripts/report_cost_aware_topk.py",
                    ROOT / "carlos/EXPERIMENTOS_PENDIENTES.md"]
    for path in source_files:
        record(path)
    kth_costs = component_costs(record(DEFAULT_KTH_COST))
    proxy_costs = component_costs(record(DEFAULT_PROXY_COST))
    if "vit_b16" not in proxy_costs and "vit_b16" in kth_costs:
        proxy_costs["vit_b16"] = kth_costs["vit_b16"]

    conditions, dataset_counts = [], {}
    for dataset, (archive_dir, sweep_dir, embedding_root, expected) in DATASETS.items():
        root = (ROOT / "results/confirmatory" if dataset in {"DTD", "FMD", "CUReT"}
                else ROOT / "results/extensions" / archive_dir)
        record(root / "data_audit.csv")
        audit_gate(root, dataset)
        manifest = record(root / "sample_manifests" / f"{dataset}.csv")
        sweep = record(ROOT / "results/exploratory/k_sweep" / sweep_dir / "k_sweep.csv")
        with sweep.open(newline="", encoding="utf-8") as handle:
            selections = fixed_four(list(csv.DictReader(handle)), dataset)
        if len(selections) != expected:
            raise ValueError(f"{dataset}: expected {expected} fixed-four rows, got {len(selections)}")
        cheap = ["resnet50", "beitv2_base_final"] if dataset == "KTHTIPS2b" else CHEAP[:]
        costs = kth_costs if dataset == "KTHTIPS2b" else proxy_costs
        cache_dir = ROOT / embedding_root / ("KTH-TIPS2-b" if dataset == "KTHTIPS2b" else dataset)
        needed = sorted(set(cheap).union(*map(set, selections.values())))
        y = None
        dimensions = {}
        for block in needed:
            feature_path = record(cache_dir / f"{block}.npy")
            labels_path = record(cache_dir / f"{block}_labels.npy")
            labels = canonical_labels(np.load(labels_path, allow_pickle=False))
            if y is None:
                y = labels
            elif not np.array_equal(y, labels):
                raise ValueError(f"{dataset}/{block}: label partition mismatch")
            features = np.load(feature_path, allow_pickle=False, mmap_mode="r")
            if features.ndim != 2 or len(features) != len(labels) or features.shape[1] < 1:
                raise ValueError(f"{dataset}/{block}: invalid NPY shape")
            dimensions[block] = int(features.shape[1])
            del features
        groups, rows = load_manifest(root, dataset, y)
        archives = sorted((ROOT / "results/exploratory/topk_cascade" / archive_dir /
                           "exact_archive").glob("*_topk_cascade.json"))
        if len(archives) != expected:
            raise ValueError(f"{dataset}: expected {expected} archives, got {len(archives)}")
        seen = set()
        for path in archives:
            entry = json.loads(record(path).read_text(encoding="utf-8"))
            fold = int(entry["outer_fold"])
            if entry["dataset"] != dataset or int(entry["seed"]) != 42 or fold in seen:
                raise ValueError(f"invalid or duplicate archive: {path}")
            seen.add(fold)
            top4 = selections[fold]
            train, test = outer_split(entry, y, groups, rows)
            excluded = duplicate_exclusions(rows, entry["protocol"])
            disjoint_indices(train, test, len(y), excluded)
            if len(train) != entry["n_train"] or len(test) != entry["n_test"]:
                raise ValueError(f"{dataset}/{fold}: split counts differ from archived protocol")
            if set(groups[train]) & set(groups[test]):
                raise ValueError(f"{dataset}/{fold}: outer group leakage")
            inner_column = "sample" if dataset == "KTHTIPS2b" else entry["inner_group_column"]
            inner_groups = groups if inner_column == "group" else manifest_groups(rows, inner_column)
            if dataset == "KTHTIPS2b" and set(inner_groups[train]) & set(inner_groups[test]):
                raise ValueError("KTH outer physical samples overlap")
            n_splits = min(4, len(np.unique(inner_groups[train])))
            if n_splits < 2:
                raise ValueError(f"{dataset}/{fold}: fewer than two inner groups")
            splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=43)
            inner_folds = []
            labels_train = set(map(int, y[train]))
            for rel_fit, rel_val in splitter.split(np.zeros(len(train)), y[train], inner_groups[train]):
                fit_ids, val_ids = train[rel_fit], train[rel_val]
                if set(inner_groups[fit_ids]) & set(inner_groups[val_ids]):
                    raise ValueError("inner group leakage")
                if set(map(int, y[fit_ids])) != labels_train:
                    raise ValueError("inner fitting partition lacks a class")
                inner_folds.append({"fit_indices": fit_ids.tolist(), "validation_indices": val_ids.tolist()})
            measured_costs, missing_costs = cost_coverage(top4 + cheap, costs)
            conditions.append({
                "id": f"{dataset}_svm_s42_f{fold}", "dataset": dataset,
                "classifier": "svm", "seed": 42, "outer_fold": fold,
                "protocol": entry["protocol"], "top4_blocks": top4,
                "top4_dimensions": sum(dimensions[b] for b in top4),
                "cheap_candidates": cheap, "inner_group_column": inner_column,
                "inner_folds": inner_folds, "train_indices": train.tolist(), "test_indices": test.tolist(),
                "purged_duplicate_indices": excluded,
                "sweep_source": sweep.relative_to(ROOT).as_posix(),
                "archive_source": path.relative_to(ROOT).as_posix(),
                "manifest_source": manifest.relative_to(ROOT).as_posix(),
                "embedding_directory": cache_dir.relative_to(ROOT).as_posix(),
                "component_costs_ms": measured_costs,
                "missing_component_costs": missing_costs,
                "measurement_status": "not_executed",
            })
        if seen != set(selections):
            raise ValueError(f"{dataset}: archive and sweep folds differ")
        dataset_counts[dataset] = expected
        print(f"{dataset}: {expected} condiciones e inputs estructurales verificados", flush=True)

    cost_gaps = [{"id": c["id"], "dataset": c["dataset"], "blocks": c["missing_component_costs"]}
                 for c in conditions if c["missing_component_costs"]]
    recipe = {
        "stage": "input_preparation_only", "experiment_status": "not_executed",
        "execution_ready": False,
        "remaining_work": ["Implement and test the fixed-four runner",
                           "Resolve recorded component-cost gaps before cost-based selection"],
        "study_status": "exploratory_previously_observed_external_tests",
        "classifier": "svm", "seed": 42, "fixed_k": 4,
        "normalization": "existing l2_rows per block, float32, epsilon 1e-12",
        "quantiles": [0.25, 0.5, 0.75], "f1_tolerance": 0.005,
        "route_selection": "existing training-only OOF eligibility and projected-cost rule",
        "random_control_repetitions": 100,
        "e2_gates": ["margin", "maximum_score", "softmax_entropy_temperature_1"],
        "e2_selection": "thresholds from OOF only; report actual test request fractions and ties",
        "costs": "historical component projections; no new online latency measured",
        "required_new_outputs": ["class_order", "train_test_indices", "oof_fold_indices",
                                 "all_candidate_oof_and_test_scores", "all_candidate_predictions",
                                 "top4_direct_predictions", "random_controls", "selection_pretest",
                                 "results", "input_and_output_hashes", "errors"],
        "cpu_threads": 2, "fits_or_inference_in_this_preparation": 0,
        "gpu_benchmark_in_this_preparation": False,
    }
    versions = {}
    for package in ("numpy", "scipy", "scikit-learn", "pandas", "torch"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not_installed"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    summary = {"status": "structural_inputs_checked_cost_gaps_execution_not_started" if cost_gaps
               else "inputs_checked_execution_not_started", "conditions": len(conditions),
               "datasets": dataset_counts, "source_files_hashed": len(sources),
               "hashed_bytes": sum(v["bytes"] for v in sources.values()),
               "conditions_with_complete_cost_profile": len(conditions) - len(cost_gaps),
               "missing_component_costs": cost_gaps,
               "execution_ready": False, "scientific_experiments_run": 0,
               "limitations": ["NPY shape and label partition checked; no feature-finiteness scan",
                               "Input checks do not replace runner tests or a scientific result"]}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (("recipe.json", recipe), ("conditions.json", conditions),
                       ("summary.json", summary),
                       ("provenance.json", {"git_head": commit, "python": sys.version,
                                            "versions": versions, "sources": sources,
                                            "threads": {k: os.environ.get(k) for k in
                                                        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}})):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# Preparación de E1 y E2\n\n"
        "Se verificaron 27 condiciones de seis datasets, cuatro bloques por condición, "
        "etiquetas, formas NPY, particiones externas/internas y costos disponibles. "
        "KTH agrupa por muestra física. Entradas identificadas con SHA-256.\n\n"
        f"**Perfil de costos incompleto en {len(cost_gaps)} condiciones.** "
        "Los bloques faltantes figuran en `summary.json`; no se sustituyeron con otro dataset.\n\n"
        "**No se ejecutó E1 ni E2.** Falta implementar y probar el ejecutor Top-4 fijo; "
        "el script histórico usa la selección de tamaño variable y no guarda todos los scores. "
        "Esta carpeta contiene una receta candidata e inputs preparados, no resultados nuevos "
        "ni un worker listo para lanzar. Los costos siguen siendo proyecciones históricas.\n\n"
        "- `conditions.json`: bloques e índices de cada condición.\n"
        "- `recipe.json`: controles y salidas requeridas.\n"
        "- `provenance.json`: hashes y versiones del entorno.\n"
        "- `summary.json`: cobertura de esta preparación.\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
