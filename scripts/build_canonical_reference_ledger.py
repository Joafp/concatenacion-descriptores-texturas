#!/usr/bin/env python3
"""Generador del Libro Mayor de Referencias Canónicas de 22 Bloques (Hito P0).

Construye un artefacto nuevo e inmutable:
- results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.json
- results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv

Garantías metodológicas de P0 (Plan 1.2):
1. Mapeo inequívoco de particiones externas a outer_fold:
   - DTD (10 conds): outer_fold = condition - 1 (0..9)
   - FMD (5 conds): outer_fold = condition (0..4)
   - CUReT (2 conds): 'a_to_b' -> outer_fold 0; 'b_to_a' -> outer_fold 1
   - Outex13Official1360 (1 cond): outer_fold = condition - 1 = 0
   - SoilOriginal (5 conds): outer_fold = condition (0..4)
   - KTHTIPS2b (4 conds): outer_fold = condition - 1 (0..3), usando variante canónica 3->1 con agrupación interna por muestra física.
2. Rutas directas a CSVs de origen fijados con SHA-256 (sin búsquedas difusas con glob).
3. Cobertura completa 27/27 para Completa-22 y GFS-22.
4. Declaración explícita de ausencias verificadas (e.g. Top-k en KTH bajo protocolo agrupado).
5. No altera resultados históricos ni sobreescribe JSONs de corridas anteriores.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
OUTPUT_JSON = REPO / "results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.json"
OUTPUT_CSV = REPO / "results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv"


def sha256_file(path: Path) -> str:
    """Calcula el hash SHA-256 de un archivo en disco."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# Especificación explícita de fuentes confirmativas auditadas (ngram22_beitv2)
DATASET_CANONICAL_SOURCES = {
    "DTD": {
        "main_csv": REPO / "results/confirmatory/ngram22_beitv2/nested_fold_results.csv",
        "topk_csv": REPO / "results/confirmatory/ngram22_beitv2/topk_individual_control/nested_fold_results.csv",
        "protocol": "official_splits",
        "fold_mapping": lambda c: int(c) - 1,
    },
    "FMD": {
        "main_csv": REPO / "results/confirmatory/ngram22_beitv2/nested_fold_results.csv",
        "topk_csv": REPO / "results/confirmatory/ngram22_beitv2/topk_individual_control/nested_fold_results.csv",
        "protocol": "stratified_group_kfold",
        "fold_mapping": lambda c: int(c),
    },
    "CUReT": {
        "main_csv": REPO / "results/confirmatory/ngram22_beitv2/nested_fold_results.csv",
        "topk_csv": REPO / "results/confirmatory/ngram22_beitv2/topk_individual_control/nested_fold_results.csv",
        "protocol": "halves",
        "fold_mapping": lambda c: 0 if str(c) == "a_to_b" else 1,
    },
    "Outex13Official1360": {
        "main_csv": REPO / "results/extensions/outex13_official1360/ngram22_beitv2/nested_fold_results.csv",
        "topk_csv": REPO / "results/extensions/outex13_official1360/ngram22_beitv2/topk_individual_control/nested_fold_results.csv",
        "protocol": "official_splits",
        "fold_mapping": lambda c: int(c) - 1,
    },
    "SoilOriginal": {
        "main_csv": REPO / "results/extensions/soil_original/ngram22_beitv2/nested_fold_results.csv",
        "topk_csv": REPO / "results/extensions/soil_original/ngram22_beitv2/topk_individual_control/nested_fold_results.csv",
        "protocol": "stratified_group_kfold",
        "fold_mapping": lambda c: int(c),
    },
    "KTHTIPS2b": {
        "main_csv": REPO / "results/extensions/kth_tips2b/ngram22_beitv2_innergrp_sample_v1/nested_fold_results.csv",
        "topk_csv": REPO / "results/extensions/kth_tips2b/ngram22_beitv2_innergrp_sample_v1/topk_individual_control/nested_fold_results.csv",
        "protocol": "official_splits_inverted_radam_innergrp_sample",
        "fold_mapping": lambda c: int(c) - 1,
    },
}

CONDITIONS_MANIFEST = [
    # DTD (10)
    *[{"dataset": "DTD", "condition": i} for i in range(1, 11)],
    # FMD (5)
    *[{"dataset": "FMD", "condition": i} for i in range(5)],
    # CUReT (2)
    {"dataset": "CUReT", "condition": "a_to_b"},
    {"dataset": "CUReT", "condition": "b_to_a"},
    # Outex (1)
    {"dataset": "Outex13Official1360", "condition": 1},
    # Soil (5)
    *[{"dataset": "SoilOriginal", "condition": i} for i in range(5)],
    # KTH (4)
    *[{"dataset": "KTHTIPS2b", "condition": i} for i in range(1, 5)],
]


def build_ledger() -> Dict[str, Any]:
    """Extrae y valida cada una de las 27 entradas de referencia."""
    ledger_entries = []
    source_hashes = {}

    for spec in CONDITIONS_MANIFEST:
        ds_name = spec["dataset"]
        cond = spec["condition"]
        cfg = DATASET_CANONICAL_SOURCES[ds_name]
        
        main_csv = cfg["main_csv"]
        topk_csv = cfg["topk_csv"]
        outer_fold = cfg["fold_mapping"](cond)

        if str(main_csv) not in source_hashes:
            source_hashes[str(main_csv)] = sha256_file(main_csv)
        if topk_csv.exists() and str(topk_csv) not in source_hashes:
            source_hashes[str(topk_csv)] = sha256_file(topk_csv)

        full_22_entry: Optional[Dict[str, Any]] = None
        gfs_22_entry: Optional[Dict[str, Any]] = None
        topk_22_entry: Optional[Dict[str, Any]] = None

        # 1. Extraer Completa-22 y GFS-22 del CSV principal
        with open(main_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if (
                    r["dataset"].lower() == ds_name.lower()
                    and r["classifier"] == "svm"
                    and int(r["outer_fold"]) == outer_fold
                    and int(r.get("seed", 42)) == 42
                ):
                    method = r["method"]
                    f1 = float(r["macro_f1"])
                    acc = float(r["accuracy"])
                    k = int(r.get("k", 0))

                    if method == "full_concat" and k == 22:
                        full_22_entry = {
                            "macro_f1": f1,
                            "accuracy": acc,
                            "k": 22,
                            "selected": r.get("selected", ""),
                        }
                    elif method == "gfs":
                        gfs_22_entry = {
                            "macro_f1": f1,
                            "accuracy": acc,
                            "k": k,
                            "selected": r.get("selected", ""),
                        }

        # 2. Extraer Top-k 22 del CSV de control
        if topk_csv.exists():
            with open(topk_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if (
                        r["dataset"].lower() == ds_name.lower()
                        and r["classifier"] == "svm"
                        and int(r["outer_fold"]) == outer_fold
                        and int(r.get("seed", 42)) == 42
                        and r["method"] == "topk_individual"
                    ):
                        topk_22_entry = {
                            "macro_f1": float(r["macro_f1"]),
                            "accuracy": float(r["accuracy"]),
                            "k": int(r.get("k", 0)),
                            "selected": r.get("selected", ""),
                        }

        entry_data = {
            "dataset": ds_name,
            "condition": str(cond),
            "outer_fold": int(outer_fold),
            "protocol": cfg["protocol"],
            "seed": 42,
            "classifier": "svm",
            "source_main_csv": str(main_csv.relative_to(REPO)),
            "source_main_sha256": source_hashes[str(main_csv)],
            "source_topk_csv": str(topk_csv.relative_to(REPO)) if topk_csv.exists() else None,
            "source_topk_sha256": source_hashes.get(str(topk_csv)),
            "Reference_Full_22": full_22_entry,
            "Reference_GFS_22": gfs_22_entry,
            "Reference_Topk_22": topk_22_entry,
            "absence_flags": {
                "topk_absent_in_innergrp_sample": topk_22_entry is None,
            },
        }
        ledger_entries.append(entry_data)

    ledger_payload = {
        "schema_version": "canonical_22_reference_ledger_v1",
        "description": "Libro mayor inmutable de referencias confirmativas históricas de 22 bloques con emparejamiento auditado P0",
        "total_conditions": len(ledger_entries),
        "source_hashes": source_hashes,
        "coverage_summary": {
            "full_22_count": sum(1 for e in ledger_entries if e["Reference_Full_22"] is not None),
            "gfs_22_count": sum(1 for e in ledger_entries if e["Reference_GFS_22"] is not None),
            "topk_22_count": sum(1 for e in ledger_entries if e["Reference_Topk_22"] is not None),
        },
        "entries": ledger_entries,
    }

    return ledger_payload


def save_ledger(payload: Dict[str, Any]):
    """Escribe los archivos JSON y CSV del libro mayor."""
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Exportar CSV plano
    csv_rows = []
    for e in payload["entries"]:
        row = {
            "dataset": e["dataset"],
            "condition": e["condition"],
            "outer_fold": e["outer_fold"],
            "protocol": e["protocol"],
            "seed": e["seed"],
            "full_22_macro_f1": e["Reference_Full_22"]["macro_f1"] if e["Reference_Full_22"] else None,
            "full_22_accuracy": e["Reference_Full_22"]["accuracy"] if e["Reference_Full_22"] else None,
            "gfs_22_macro_f1": e["Reference_GFS_22"]["macro_f1"] if e["Reference_GFS_22"] else None,
            "gfs_22_accuracy": e["Reference_GFS_22"]["accuracy"] if e["Reference_GFS_22"] else None,
            "gfs_22_k": e["Reference_GFS_22"]["k"] if e["Reference_GFS_22"] else None,
            "topk_22_macro_f1": e["Reference_Topk_22"]["macro_f1"] if e["Reference_Topk_22"] else None,
            "topk_22_accuracy": e["Reference_Topk_22"]["accuracy"] if e["Reference_Topk_22"] else None,
            "topk_22_k": e["Reference_Topk_22"]["k"] if e["Reference_Topk_22"] else None,
            "source_main_csv": e["source_main_csv"],
            "source_main_sha256": e["source_main_sha256"][:12],
        }
        csv_rows.append(row)

    if csv_rows:
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)


def main():
    print("Construyendo Libro Mayor Canónico de Referencias de 22 Bloques (P0)...")
    payload = build_ledger()
    cov = payload["coverage_summary"]
    print(f"Total condiciones: {payload['total_conditions']}")
    print(f"  - Completa-22 (Full_22): {cov['full_22_count']} / 27")
    print(f"  - GFS-22:                {cov['gfs_22_count']} / 27")
    print(f"  - Top-k 22:              {cov['topk_22_count']} / 27 (ausencias explícitas en KTH)")

    assert cov["full_22_count"] == 27, f"Faltan condiciones en Completa-22: {cov['full_22_count']}"
    assert cov["gfs_22_count"] == 27, f"Faltan condiciones en GFS-22: {cov['gfs_22_count']}"

    save_ledger(payload)
    print(f"Artefactos generados exitosamente:")
    print(f"  - JSON: {OUTPUT_JSON}")
    print(f"  - CSV:  {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
