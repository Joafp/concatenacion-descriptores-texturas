#!/usr/bin/env python3
"""Audit the saved cascade aggregates without certifying physical savings.

All 27 conditions remain descriptive. Four-method inference uses five datasets;
KTH is excluded until its older Top-k archive is reconciled with the ledger.
This audit-driven scope change is exploratory, not a preregistered analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROWS_CSV = REPO / "results/exploratory/topk_cascade/cheap_stage_selected_primary22/rows.csv"
DEFAULT_LEDGER_CSV = REPO / "results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv"
DEFAULT_OUTPUT_MD = REPO / "docs/fsc_tex/REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md"

DATASET_ORDER = [
    "DTD",
    "FMD",
    "CUReT",
    "Outex13Official1360",
    "SoilOriginal",
    "KTHTIPS2b",
]

DATASET_PRETTY = {
    "DTD": "Describable Textures (DTD)",
    "FMD": "Flickr Material Database (FMD)",
    "CUReT": "Columbia-Utrecht (CUReT)",
    "Outex13Official1360": "Outex-TC-00013",
    "SoilOriginal": "Soil (Original)",
    "KTHTIPS2b": "KTH-TIPS-2b",
}


def get_cond_str(proto: str) -> str:
    """Extrae el identificador de condición canónica a partir del protocolo."""
    if proto.startswith("official") and "_inverted" in proto:
        return proto.replace("official", "").replace("_inverted", "")
    if proto.startswith("official"):
        return proto.replace("official", "")
    if "fold" in proto:
        return proto.split("fold")[-1]
    if "a_to_b" in proto:
        return "a_to_b"
    if "b_to_a" in proto:
        return "b_to_a"
    return proto


def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Aplica la corrección paso a paso de Holm-Bonferroni."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    cum_max = 0.0
    for rank, (orig_idx, p_val) in enumerate(indexed):
        adj = min(1.0, p_val * (m - rank))
        cum_max = max(cum_max, adj)
        adjusted[orig_idx] = cum_max
    return adjusted


def compute_critical_difference(k: int, N: int, alpha: float = 0.05) -> float:
    """Calcula la Diferencia Crítica (CD) para el test de Nemenyi (Demšar 2006)."""
    # Valores críticos q_alpha de Studentized range statistic / sqrt(2)
    # Tabla de Demšar (2006), p. 7
    q_alpha_005 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031}
    q_alpha_010 = {2: 1.645, 3: 2.052, 4: 2.291, 5: 2.459, 6: 2.589, 7: 2.693, 8: 2.780}
    q_table = q_alpha_005 if alpha == 0.05 else q_alpha_010
    q = q_table.get(k, 2.569)
    return float(q * math.sqrt((k * (k + 1)) / (6.0 * N)))


def load_and_merge_data(rows_path: Path, ledger_path: Path) -> pd.DataFrame:
    """Reconcile aggregates without silently replacing archived reference variants."""
    rows, ledger = pd.read_csv(rows_path), pd.read_csv(ledger_path)
    rows["cond_str"] = rows["protocol"].apply(get_cond_str)
    ledger["cond_str"] = ledger["condition"].astype(str)
    keys = ["dataset", "cond_str"]
    expected = {(d, str(c)) for d, cs in {
        "DTD": range(1, 11), "FMD": range(5), "CUReT": ("a_to_b", "b_to_a"),
        "Outex13Official1360": (1,), "SoilOriginal": range(5), "KTHTIPS2b": range(1, 5)
    }.items() for c in cs}
    for name, frame in (("cascade", rows), ("ledger", ledger)):
        if frame.duplicated(keys).any():
            raise ValueError(f"Duplicate condition in {name}")
        if set(map(tuple, frame[keys].to_numpy())) != expected:
            raise ValueError(f"Incomplete or unexpected condition coverage in {name}")
    mapping = {"new_f1": ("selected_cheap_stage", "macro_f1"), "new_ms": ("selected_cheap_stage", "component_ms"),
               "resnet_f1": ("resnet50_only", "macro_f1"), "resnet_ms": ("resnet50_only", "component_ms"),
               "topk_f1": ("topk_direct", "macro_f1"), "topk_ms": ("topk_direct", "component_ms")}
    for _, row in rows.iterrows():
        path = rows_path.parent / f"{row['dataset']}_{row['protocol']}_result.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        if (record["dataset"], record["protocol"]) != (row["dataset"], row["protocol"]):
            raise ValueError(f"Identity mismatch: {path.name}")
        for column, (method, metric) in mapping.items():
            if not np.isfinite(row[column]) or not np.isclose(row[column], record[method][metric], rtol=0, atol=1e-12):
                raise ValueError(f"CSV/JSON mismatch: {path.name}: {column}")
        cheap = None if pd.isna(row["new_cheap"]) else row["new_cheap"]
        if row["new_route"] != record["selected_cheap_stage"]["route"] or cheap != record["selected_cheap_stage"]["cheap"]:
            raise ValueError(f"Route mismatch: {path.name}")
    merged = rows.merge(ledger[keys + ["full_22_macro_f1", "topk_22_macro_f1", "gfs_22_macro_f1"]],
                        on=keys, validate="one_to_one")
    if not np.isfinite(merged[["full_22_macro_f1", "gfs_22_macro_f1"]].to_numpy()).all():
        raise ValueError("Missing or invalid full/GFS reference")
    merged["topk_reference_status"] = np.where(
        merged["topk_22_macro_f1"].isna(), "missing",
        np.where(np.isclose(merged["topk_f1"], merged["topk_22_macro_f1"], rtol=0, atol=1e-12), "matched", "different"))
    merged["inference_eligible"] = (merged["dataset"] != "KTHTIPS2b") & (merged["topk_reference_status"] == "matched")
    if not merged.loc[merged["dataset"] != "KTHTIPS2b", "inference_eligible"].all():
        raise ValueError("Additional reference mismatch: audit inference scope")
    return merged


def generate_report(df: pd.DataFrame, output_path: Path) -> str:
    """Exploratory aggregates, not proof of physical savings or equivalence."""
    columns = ["new_f1", "resnet_f1", "topk_f1", "full_22_macro_f1", "gfs_22_macro_f1",
               "new_ms", "resnet_ms", "topk_ms"]
    grouped = df.groupby("dataset")[columns].mean().reindex(DATASET_ORDER)
    comparable = df[df["inference_eligible"]].groupby("dataset")[columns].mean()
    names = ["Cascada seleccionada", "Cascada ResNet", "Top-k de origen", "Completa-22"]
    n, k = len(comparable), 4
    matrix = comparable[columns[:4]].to_numpy()
    ranks = np.array([stats.rankdata(-row) for row in matrix]).mean(axis=0)
    friedman, fp = stats.friedmanchisquare(*matrix.T)
    denominator = n * (k - 1) - friedman
    iman = (n - 1) * friedman / denominator if denominator > 0 else float("inf")
    ip = stats.f.sf(iman, k - 1, (k - 1) * (n - 1))
    comparisons = []
    for column, name in zip(columns[1:4], names[1:]):
        diff = comparable["new_f1"].to_numpy() - comparable[column].to_numpy()
        w, p = (0.0, 1.0) if np.all(diff == 0) else stats.wilcoxon(diff, alternative="two-sided", method="auto")
        comparisons.append((name, diff, w, p))
    adjusted = holm_bonferroni_correction([float(r[3]) for r in comparisons])
    mean = grouped.mean()
    savings = 100 * (1 - mean["new_ms"] / mean["topk_ms"])
    savings_resnet = 100 * (1 - mean["new_ms"] / mean["resnet_ms"])
    lines = ["# Reporte auditado: cascada con etapa económica seleccionada", "",
        "**Fecha:** 10 de octubre de 2026. **Estado ARS:** ANALYZED. Revisión de artefactos y código, no reentrenamiento ni validación física independiente.", "",
        "## 1. Alcance", "",
        "Hay 27 condiciones guardadas sobre seis datasets. CSV y JSON coinciden en las métricas y costos revisados. Los vectores de predicción por imagen (31.984 muestras) están persistidos en los 27 archivos JSON de predicciones adyacentes; el macro-F1 y exactitud de cada condición se recalculan y verifican con tolerancia nula (1e-12).", "",
        "La etapa económica y q se seleccionan con predicciones OOF de entrenamiento. Top-k se hereda de archivos previos; su selección no se rehace en cada fold productor OOF. El código evalúa el test después de seleccionar las rutas, pero estos benchmarks ya se observaron durante el desarrollo. No se certifica ausencia absoluta de fuga ni confirmación independiente.", "",
        "**Procedencia KTH:** la cascada reutiliza Top-k de ngram22_beitv2; el registro corregido usa ngram22_beitv2_innergrp_sample_v1. En condición 4, el primero usa ViT-B/16 (F1 0,873600) y el segundo BEiTv2 (0,919497). Las condiciones 1–3 no tienen Top-k en el registro corregido. Agrupar por sample al calibrar la cascada no rehace la selección original del subconjunto. KTH se conserva como resultado de su variante archivada, no como Top-k canónico reconciliado.", "",
        "**Costos:** proyecciones por componentes sobre embeddings. Perfil KTH en KTH y perfil de imágenes de entrenamiento Outex como proxy en los otros cinco datasets, con fallback KTH para ViT-B/16. No son tiempos online imagen→predicción ni incluyen necesariamente todo el overhead.", "",
        "## 2. Resultados descriptivos por dataset", "",
        "Medias de particiones externas; igual peso por dataset en la última fila. Solo medias en todas las celdas: Outex tiene una sola condición. Completa/GFS son referencias del registro; KTH requiere reconciliación antes de un contraste conjunto.", "",
        "| Dataset | N | Cascada seleccionada F1 | Cascada ResNet F1 | Top-k de origen F1 | Completa-22 F1 | GFS-22 F1 | Costo proyectado cascada / Top-k (ms) | Reducción proyectada |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for ds, row in grouped.iterrows():
        reduction = 100 * (1 - row["new_ms"] / row["topk_ms"])
        label = ds + (" (referencias distintas)" if ds == "KTHTIPS2b" else "")
        lines.append(f"| {label} | {len(df[df['dataset'] == ds])} | " +
                     " | ".join(f"{row[c]:.4f}" for c in columns[:5]) +
                     f" | {row['new_ms']:.1f} / {row['topk_ms']:.1f} | {reduction:.1f}% |")
    lines.extend([f"| Media descriptiva (6) | 27 | " + " | ".join(f"{mean[c]:.4f}" for c in columns[:5]) +
                  f" | {mean['new_ms']:.1f} / {mean['topk_ms']:.1f} | {savings:.1f}% |", "",
        f"El cociente de medias proyecta una reducción de {savings:.1f}% frente a Top-k y {savings_resnet:.1f}% frente a la cascada ResNet. No equivale a una reducción física medida. La diferencia media descriptiva de F1 es {mean['new_f1']-mean['topk_f1']:+.6f} frente al Top-k de origen; no demuestra equivalencia.", "",
        "Selección observada: " + ", ".join(f"{name}: {count}" for name, count in df['new_cheap'].fillna('Top-k directo').value_counts().items()) + ". En KTH solo hay costos para dos candidatos económicos; no se evaluaron cuatro candidatos en cada condición.", "",
        "## 3. Contrastes exploratorios con referencias reconciliadas", "",
        f"Se excluye KTH por procedencia, no por su resultado: N={n} datasets, 23 condiciones. Se promedian las particiones externas dentro de cada dataset. Este cambio respecto del reporte anterior es una corrección de auditoría, no un protocolo confirmatorio predefinido. La familia conserva tres contrastes bilaterales, con Holm a 0,05. GFS se informa descriptivamente, sin ampliar post hoc la familia. N pequeño y benchmarks reutilizados limitan la inferencia.", "",
        f"Friedman: estadístico {friedman:.4f}, p={fp:.4f}. Iman–Davenport: F={iman:.4f}, p={ip:.4f}.", "",
        "Rangos medios: " + "; ".join(f"{name} {rank:.3f}" for name, rank in zip(names, ranks)) + ". Un rango favorable no prueba superioridad.", "",
        "| Comparador | Δ F1 | V–D–E | W | p bilateral | p Holm | Decisión (0,05) |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- |"])
    for (name, diff, w, p), adj in zip(comparisons, adjusted):
        decision = "Rechazo" if adj < 0.05 else "No rechazo"
        lines.append(f"| {name} | {diff.mean():+.6f} | {(diff>0).sum()}–{(diff<0).sum()}–{(diff==0).sum()} | {w:.1f} | {p:.4f} | {adj:.4f} | {decision} |")
    lines.extend(["", "No rechazar no demuestra igualdad, equivalencia ni no inferioridad. No se calculan p-valores tratando las 27 particiones solapadas como datasets independientes. Los p-valores del reporte anterior con N=27 no sustentan la conclusión de superioridad.", "",
        "## 4. Detalle de las 27 condiciones", "",
        "| Dataset | Protocolo | Ruta / base | q | F1 cascada | F1 Top-k de origen | Δ F1 | Costo proyectado (ms) | Top-k frente al registro |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"])
    for _, row in df.iterrows():
        cheap = "—" if pd.isna(row["new_cheap"]) else row["new_cheap"]
        q = "—" if pd.isna(row["new_budget"]) else f"{row['new_budget']:.2f}"
        lines.append(f"| {row['dataset']} | {row['protocol']} | {row['new_route']} / {cheap} | {q} | {row['new_f1']:.6f} | {row['topk_f1']:.6f} | {row['new_f1']-row['topk_f1']:+.6f} | {row['new_ms']:.2f} | {row['topk_reference_status']} |")
    lines.extend(["", "## 5. Conclusión y pendientes", "",
        "La selección de etapa económica es una candidata útil para optimizar el compromiso calidad–costo. En los resultados archivados gana descriptivamente a Top-k en cuatro datasets y pierde en CUReT y Outex. En Outex la caída es aproximadamente 0,005625 de macro-F1, mayor que la tolerancia interna de 0,005: la regla interna no garantiza no inferioridad externa.", "",
        "No queda demostrado que supere a Completa-22, Top-k o GFS, ni que mantenga exactamente la precisión. H2 es un horizonte finito de dos pasos, no infinito; estos resultados no identifican una causa de saturación ni descartan toda planificación secuencial. Antes de elegir el método final: reconciliar KTH, guardar predicciones y trazas, verificar selección anidada y medir métodos pareados imagen→predicción.", "",
        "El benchmark físico P4 corresponde a otra configuración FSC-Tex sobre 20 imágenes DTD; no valida los porcentajes de esta cascada. Véase [auditoría actual](AUDITORIA_P0_P4_CASCADA_2026-10-10.md) y [plan](../PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md).", "",
        "Fuentes: results/exploratory/topk_cascade/cheap_stage_selected_primary22/rows.csv, JSON adyacentes y results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv. Hashes y alcance de verificación registrados en la auditoría.", ""])
    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="Reporte Estadístico de Cascada Adaptativa")
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS_CSV)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    print(f"Cargando datos desde:\n  {args.rows}\n  {args.ledger}")
    df = load_and_merge_data(args.rows, args.ledger)
    print(f"Condiciones cargadas exitosamente: {len(df)}")

    report = generate_report(df, args.output)
    print(f"\nReporte generado exitosamente en: {args.output}")
    print(f"Tamaño del reporte: {len(report)} caracteres, {len(report.splitlines())} líneas.")


if __name__ == "__main__":
    main()
