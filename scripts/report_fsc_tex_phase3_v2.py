#!/usr/bin/env python3
"""Generador de Reporte y Análisis Estadístico Riguroso para FSC-Tex Fase 3 v2 (Hito R6).

Lee los 7 artefactos auditados de las condiciones ejecutadas en:
results/exploratory/fsc_tex/phase3_v2_suite/

Genera:
1. docs/fsc_tex/FASE_3_V2_REPORTE_SUITE_COMPLETA.md
2. Tablas desagregadas por dataset y agregadas globalmente.
3. Contrastes de hipótesis no paramétricos según directrices de Demšar (2006):
   - Contrastes pareados por dataset (N=6 agregados independientes).
   - Corrección de multiplicidad de Holm-Bonferroni.
   - Diagnóstico descriptivo de margen de calidad; no es una prueba de no inferioridad.
4. Divulgación honesta de alcances: Full_Fusion_6 vs Canonical_22, victorias y derrotas.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from sklearn.metrics import accuracy_score, f1_score

REPO = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO / "results/exploratory/fsc_tex/phase3_v2_suite"
DEFAULT_OUTPUT_MD = REPO / "docs/fsc_tex/FASE_3_V2_REPORTE_SUITE_COMPLETA.md"

DATASET_ORDER = [
    "DTD",
    "FMD",
    "CUReT",
    "Outex13Official1360",
    "SoilOriginal",
    "KTHTIPS2b",
]

CORE_METHODS = [
    "Base_resnet50",
    "Best_Individual_Internal",
    "Static_Pair_ResNet_SigLIP",
    "Cascade_TopK_Prospective",
    "FSC_Tex_H1_Myopic",
    "FSC_Tex_H2_Bellman",
    "FSC_Tex_H2_Enriched_State",
    "Full_Fusion_6",
]

METHOD_PRETTY_NAMES = {
    "Base_resnet50": "Base (ResNet-50)",
    "Best_Individual_Internal": "Mejor individual interno (6 candidatos)",
    "Static_Pair_ResNet_SigLIP": "Par Estático (ResNet+SigLIP)",
    "Cascade_TopK_Prospective": "Cascada base + 1 aumentador",
    "FSC_Tex_H1_Myopic": "FSC-Tex H1 (Miope)",
    "FSC_Tex_H2_Bellman": "FSC-Tex H2 (Bellman)",
    "FSC_Tex_H2_Enriched_State": "FSC-Tex H2 (Enriquecido)",
    "Full_Fusion_6": "Fusión Completa-6",
    "Completa-22": "Ref. Completa-22 (Auditada)",
    "GFS-22": "Ref. GFS-22 (Auditada)",
    "Topk-22": "Ref. Topk-22 (Auditada)",
}


def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """Aplica el ajuste secuencial de Holm-Bonferroni a una lista de p-values."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    cum_max = 0.0
    for rank, (orig_idx, p_val) in enumerate(indexed):
        adj = min(1.0, p_val * (m - rank))
        cum_max = max(cum_max, adj)
        adjusted[orig_idx] = cum_max
    return adjusted


def load_all_suite_results(results_dir: Path) -> List[Dict[str, Any]]:
    """Carga todos los resultados de metrics.json disponibles."""
    all_runs = []
    if not results_dir.exists():
        return all_runs

    for ds_path in sorted(results_dir.iterdir()):
        if not ds_path.is_dir():
            continue
        ds_name = ds_path.name
        for cond_path in sorted(ds_path.iterdir()):
            if not cond_path.is_dir() or not cond_path.name.startswith("condition_"):
                continue
            metrics_file = cond_path / "metrics.json"
            if not metrics_file.exists():
                raise ValueError(f"Condición incompleta: {cond_path}")
            try:
                for artifact in ("run_manifest.json", "splits.json", "state_graph.json", "traces.jsonl", "predictions.json", "audit.json"):
                    if not (cond_path / artifact).is_file() or (cond_path / artifact).stat().st_size == 0:
                        raise ValueError(f"Falta artefacto no vacío: {cond_path / artifact}")
                with open(metrics_file, "r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
                predictions = json.loads((cond_path / "predictions.json").read_text(encoding="utf-8"))
                manifest = json.loads((cond_path / "run_manifest.json").read_text(encoding="utf-8"))
                for method in CORE_METHODS:
                    for metric, value in (
                        ("macro_f1", f1_score(predictions["y_true"], predictions[method], average="macro")),
                        ("accuracy", accuracy_score(predictions["y_true"], predictions[method])),
                    ):
                        if not np.isclose(value, metrics_data[method][metric], rtol=0, atol=1e-12):
                            raise ValueError(f"Métrica no reproducible: {cond_path}, {method}, {metric}")
                cond_val = cond_path.name.replace("condition_", "")
                
                # Cargar ablaciones y gate assessment si existen
                ablations = {}
                gate = {}
                audit = {}
                abl_file = cond_path / "ablations_summary.json"
                gate_file = cond_path / "gate_assessment.json"
                audit_file = cond_path / "audit.json"
                if abl_file.exists():
                    with open(abl_file, "r", encoding="utf-8") as f:
                        ablations = json.load(f)
                if gate_file.exists():
                    with open(gate_file, "r", encoding="utf-8") as f:
                        gate = json.load(f)
                if audit_file.exists():
                    with open(audit_file, "r", encoding="utf-8") as f:
                        audit = json.load(f)

                all_runs.append({
                    "dataset": ds_name,
                    "condition": cond_val,
                    "metrics": metrics_data,
                    "ablations": ablations,
                    "gate": gate,
                    "audit": audit,
                    "manifest": manifest,
                })
            except Exception as e:
                raise ValueError(f"No se puede reportar {cond_path}: {e}") from e

    return all_runs


def compute_statistics_and_report(
    runs: List[Dict[str, Any]],
    output_md: Path,
) -> str:
    """Calcula agregaciones por dataset, pruebas estadísticas de Demšar y genera reporte."""
    if not runs:
        return "No hay corridas disponibles para generar el reporte."

    datasets_present = [d for d in DATASET_ORDER if any(r["dataset"] == d for r in runs)]

    # 1. Agregados por Dataset
    ds_summaries: Dict[str, Dict[str, Dict[str, float]]] = {}
    for ds in datasets_present:
        ds_runs = [r for r in runs if r["dataset"] == ds]
        ds_summaries[ds] = {}
        for m in CORE_METHODS:
            f1s = [r["metrics"][m]["macro_f1"] for r in ds_runs if m in r["metrics"] and "macro_f1" in r["metrics"][m]]
            accs = [r["metrics"][m]["accuracy"] for r in ds_runs if m in r["metrics"] and "accuracy" in r["metrics"][m]]
            lats = [r["metrics"][m]["mean_latency_ms"] for r in ds_runs if m in r["metrics"] and r["metrics"][m].get("mean_latency_ms") is not None]
            p95s = [r["metrics"][m]["p95_latency_ms"] for r in ds_runs if m in r["metrics"] and r["metrics"][m].get("p95_latency_ms") is not None]

            if f1s:
                ds_summaries[ds][m] = {
                    "macro_f1": float(np.mean(f1s)),
                    "macro_f1_std": float(np.std(f1s)),
                    "accuracy": float(np.mean(accs)),
                    "mean_latency_ms": float(np.mean(lats)) if lats else 0.0,
                    "p95_latency_ms": float(np.mean(p95s)) if p95s else 0.0,
                    "n": len(f1s),
                }

    # 2. Análisis comparativo pareado por Dataset (N=len(datasets_present))
    # Demšar (2006): La unidad independiente para probar superioridad entre clasificadores
    # es el dataset, no los pliegues de validación cruzada.
    comparisons = [
        ("Base_resnet50", "Base (ResNet-50)"),
        ("Best_Individual_Internal", "Mejor individual interno (6)"),
        ("Static_Pair_ResNet_SigLIP", "Par Estático (ResNet+SigLIP)"),
        ("Cascade_TopK_Prospective", "Cascada base + 1 aumentador"),
        ("FSC_Tex_H1_Myopic", "FSC-Tex H1 (Miope)"),
        ("Full_Fusion_6", "Fusión Completa-6"),
    ]

    stat_results = []
    raw_p_values = []

    f1_h2_by_ds = [ds_summaries[ds]["FSC_Tex_H2_Bellman"]["macro_f1"] for ds in datasets_present if "FSC_Tex_H2_Bellman" in ds_summaries[ds]]
    lat_h2_by_ds = [ds_summaries[ds]["FSC_Tex_H2_Bellman"]["mean_latency_ms"] for ds in datasets_present if "FSC_Tex_H2_Bellman" in ds_summaries[ds]]

    for comp_m, comp_label in comparisons:
        f1_comp = []
        lat_comp = []
        valid_ds = []
        for ds in datasets_present:
            if "FSC_Tex_H2_Bellman" in ds_summaries[ds] and comp_m in ds_summaries[ds]:
                f1_comp.append(ds_summaries[ds][comp_m]["macro_f1"])
                lat_comp.append(ds_summaries[ds][comp_m]["mean_latency_ms"])
                valid_ds.append(ds)

        if len(valid_ds) < 3:
            continue

        f1_h2_arr = np.array([ds_summaries[ds]["FSC_Tex_H2_Bellman"]["macro_f1"] for ds in valid_ds])
        lat_h2_arr = np.array([ds_summaries[ds]["FSC_Tex_H2_Bellman"]["mean_latency_ms"] for ds in valid_ds])
        f1_comp_arr = np.array(f1_comp)
        lat_comp_arr = np.array(lat_comp)

        diffs_f1 = f1_h2_arr - f1_comp_arr
        mean_delta_f1 = float(np.mean(diffs_f1))
        wins = int(np.sum(diffs_f1 > 0))
        losses = int(np.sum(diffs_f1 < 0))
        ties = int(np.sum(diffs_f1 == 0))

        # Latency savings
        mean_lat_h2 = float(np.mean(lat_h2_arr))
        mean_lat_comp = float(np.mean(lat_comp_arr))
        lat_savings_pct = float((mean_lat_comp - mean_lat_h2) / mean_lat_comp * 100) if mean_lat_comp > 0 else 0.0

        # Wilcoxon test (Demšar)
        if np.all(diffs_f1 == 0):
            p_val = 1.0
        else:
            res_w = stats.wilcoxon(diffs_f1, alternative="two-sided")
            p_val = float(res_w.pvalue)

        raw_p_values.append(p_val)
        stat_results.append({
            "comparator_key": comp_m,
            "comparator_label": comp_label,
            "n_datasets": len(valid_ds),
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "mean_delta_f1": mean_delta_f1,
            "lat_savings_pct": lat_savings_pct,
            "p_val_raw": p_val,
        })

    # Corrección Holm
    adj_p_values = holm_bonferroni_correction(raw_p_values)
    for res, adj_p in zip(stat_results, adj_p_values):
        res["p_val_holm"] = adj_p

    # 3. Construcción del Documento Markdown
    md = []
    md.append(f"# FSC-Tex Fase 3 v2: reporte exploratorio ({len(runs)} condiciones)")
    md.append("")
    md.append("**Revisión del reporte:** 10 de octubre de 2026. Resultados de las corridas originales conservados.")
    md.append("")
    md.append("**Autores:** Joaquín Delgado & Carlos Ayala  ")
    md.append("**Tutor:** Prof. José Vázquez (FP-UNA)  ")
    md.append("**Marco de Trabajo:** FSC-Tex (*Sequential Cost-Aware Feature Acquisition for Textures*)  ")
    md.append("**Artefactos:** `results/exploratory/fsc_tex/phase3_v2_suite/`. Métricas recalculadas desde predicciones; no se reentrenaron los modelos.")
    md.append("")
    md.append("**Estado ARS: ANALYZED**, no reproducción integral ni revisión independiente. Véase [auditoría del 10 de octubre](AUDITORIA_FASE3_V2_2026-10-10.md).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Alcance y limitaciones")
    md.append("")
    md.append("La v2 incorpora correcciones de presupuesto, objetivos de continuación y selección interna. Los hitos R0–R6 no están íntegramente cerrados: completar archivos no demuestra todas las hipótesis del plan.")
    md.append("")
    md.append("1. **Selección interna:** el código ajusta lambda, q y aumentador dentro de entrenamiento. Los benchmarks ya se observaron durante el desarrollo; esto no es generalización ciega. Los booleanos de `audit.json` no certifican por sí solos ausencia de filtración de toda la tubería.")
    md.append("2. **Costos estimados:** todos los ms y ahorros de las tablas provienen de sumas de constantes de `HardwareCostModel`, incluido overhead supuesto de 0.45 ms por bloque. No son latencias end-to-end medidas de FSC-Tex; el p95 guardado también es de costos modelados.")
    budgets = sorted({r["manifest"]["prospective_tuning"]["target_budget_ms"] for r in runs})
    md.append(f"3. **Presupuestos guardados:** {budgets} ms modelados. Con base ResNet y los cinco candidatos de esta suite, la ruta mínima con dos adquisiciones adicionales cuesta 37.19 ms. A 35 ms no es factible: H1/H2 no aísla planificación multietapa, aunque el objetivo H2 ya utiliza valores predichos en lugar del mínimo de pérdidas futuras reales.")
    md.append("4. **Controles:** mejor individual entre seis bloques, par fijo ResNet+SigLIP y cascada ResNet más un aumentador. El identificador histórico `Cascade_TopK_Prospective` no representa Top-k22. La cascada se calibra por costo medio y puede exceder 35 ms por imagen; H2 restringe cada ruta. No son presupuestos duros equiparables.")
    md.append("5. **Referencias históricas de v2 en cuarentena:** el importador usado para estos artefactos confundía `condition` con `outer_fold` y las direcciones CUReT. P0 corrigió después el código y generó un registro trazable (Completa/GFS 27/27; Top-k 24/27). Eso no reescribe las referencias antiguas guardadas en v2 ni las convierte en controles validados de esta tabla.")
    md.append("6. **Online:** después de v2 apareció P4 sobre 20 imágenes DTD, con límites de representatividad, paridad y temporización. No es un benchmark físico pareado de esta suite que respalde sus porcentajes. Véase [auditoría posterior P0–P4/cascada](AUDITORIA_P0_P4_CASCADA_2026-10-10.md).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Tabla Consolidada por Dataset (Medias en Particiones Externas)")
    md.append("")
    md.append("Cada celda indica macro-F1 y costo **estimado** medio en ms. El promedio final da el mismo peso a cada dataset; las condiciones no son réplicas independientes. Un mayor F1 no implica significancia.")
    md.append("")
    md.append("| Dataset | Condiciones | Base (`resnet50`) | Mejor individual (6) | Par estático | Cascada base + 1 | FSC-Tex H2 | Completa-6 |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for ds in datasets_present:
        m = ds_summaries[ds]
        n_cond = m["Base_resnet50"]["n"] if "Base_resnet50" in m else 1
        b_f1 = f"{m['Base_resnet50']['macro_f1']:.4f} ({m['Base_resnet50']['mean_latency_ms']:.1f}ms)" if "Base_resnet50" in m else "N/A"
        ind_f1 = f"{m['Best_Individual_Internal']['macro_f1']:.4f} ({m['Best_Individual_Internal']['mean_latency_ms']:.1f}ms)" if "Best_Individual_Internal" in m else "N/A"
        pair_f1 = f"{m['Static_Pair_ResNet_SigLIP']['macro_f1']:.4f} ({m['Static_Pair_ResNet_SigLIP']['mean_latency_ms']:.1f}ms)" if "Static_Pair_ResNet_SigLIP" in m else "N/A"
        casc_f1 = f"{m['Cascade_TopK_Prospective']['macro_f1']:.4f} ({m['Cascade_TopK_Prospective']['mean_latency_ms']:.1f}ms)" if "Cascade_TopK_Prospective" in m else "N/A"
        h2_f1 = f"{m['FSC_Tex_H2_Bellman']['macro_f1']:.4f} ({m['FSC_Tex_H2_Bellman']['mean_latency_ms']:.1f}ms)" if "FSC_Tex_H2_Bellman" in m else "N/A"
        f6_f1 = f"{m['Full_Fusion_6']['macro_f1']:.4f} ({m['Full_Fusion_6']['mean_latency_ms']:.1f}ms)" if "Full_Fusion_6" in m else "N/A"

        md.append(f"| **{ds}** | {n_cond} | {b_f1} | {ind_f1} | {pair_f1} | {casc_f1} | {h2_f1} | {f6_f1} |")

    # Fila de promedio global
    mean_b_f1 = np.mean([ds_summaries[d]["Base_resnet50"]["macro_f1"] for d in datasets_present if "Base_resnet50" in ds_summaries[d]])
    mean_b_lat = np.mean([ds_summaries[d]["Base_resnet50"]["mean_latency_ms"] for d in datasets_present if "Base_resnet50" in ds_summaries[d]])
    mean_ind_f1 = np.mean([ds_summaries[d]["Best_Individual_Internal"]["macro_f1"] for d in datasets_present if "Best_Individual_Internal" in ds_summaries[d]])
    mean_ind_lat = np.mean([ds_summaries[d]["Best_Individual_Internal"]["mean_latency_ms"] for d in datasets_present if "Best_Individual_Internal" in ds_summaries[d]])
    mean_pair_f1 = np.mean([ds_summaries[d]["Static_Pair_ResNet_SigLIP"]["macro_f1"] for d in datasets_present if "Static_Pair_ResNet_SigLIP" in ds_summaries[d]])
    mean_pair_lat = np.mean([ds_summaries[d]["Static_Pair_ResNet_SigLIP"]["mean_latency_ms"] for d in datasets_present if "Static_Pair_ResNet_SigLIP" in ds_summaries[d]])
    mean_casc_f1 = np.mean([ds_summaries[d]["Cascade_TopK_Prospective"]["macro_f1"] for d in datasets_present if "Cascade_TopK_Prospective" in ds_summaries[d]])
    mean_casc_lat = np.mean([ds_summaries[d]["Cascade_TopK_Prospective"]["mean_latency_ms"] for d in datasets_present if "Cascade_TopK_Prospective" in ds_summaries[d]])
    mean_h2_f1 = np.mean([ds_summaries[d]["FSC_Tex_H2_Bellman"]["macro_f1"] for d in datasets_present if "FSC_Tex_H2_Bellman" in ds_summaries[d]])
    mean_h2_lat = np.mean([ds_summaries[d]["FSC_Tex_H2_Bellman"]["mean_latency_ms"] for d in datasets_present if "FSC_Tex_H2_Bellman" in ds_summaries[d]])
    mean_f6_f1 = np.mean([ds_summaries[d]["Full_Fusion_6"]["macro_f1"] for d in datasets_present if "Full_Fusion_6" in ds_summaries[d]])
    mean_f6_lat = np.mean([ds_summaries[d]["Full_Fusion_6"]["mean_latency_ms"] for d in datasets_present if "Full_Fusion_6" in ds_summaries[d]])

    md.append(
        f"| **PROMEDIO (Datasets)** | **{len(datasets_present)}** | "
        f"{mean_b_f1:.4f} ({mean_b_lat:.1f}ms) | "
        f"{mean_ind_f1:.4f} ({mean_ind_lat:.1f}ms) | "
        f"{mean_pair_f1:.4f} ({mean_pair_lat:.1f}ms) | "
        f"{mean_casc_f1:.4f} ({mean_casc_lat:.1f}ms) | "
        f"{mean_h2_f1:.4f} ({mean_h2_lat:.1f}ms) | "
        f"{mean_f6_f1:.4f} ({mean_f6_lat:.1f}ms) |"
    )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Contrastes Estadísticos No Paramétricos Pareados (Demšar, 2006)")
    md.append("")
    md.append(f"Wilcoxon bilateral sobre una media por dataset (N={len(datasets_present)}), con Holm sobre los seis contrastes mostrados. No se tratan folds como datasets independientes. Análisis exploratorio de baja potencia; no significancia no implica equivalencia. La familia de contrastes es la del reporte v2, sin afirmar prerregistro.")
    md.append("")
    md.append("| Contraste (H2 vs.) | Datasets | Victorias-Derrotas-Empates | Delta macro-F1 | Ahorro estimado | p crudo | p Holm | Decisión (0.05) |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for s in stat_results:
        verdict = "**Significativo**" if s["p_val_holm"] < 0.05 else "No significativo"
        md.append(
            f"| **vs. {s['comparator_label']}** | {s['n_datasets']} | "
            f"{s['wins']}-{s['losses']}-{s['ties']} | "
            f"{s['mean_delta_f1']:+.4f} | "
            f"{s['lat_savings_pct']:+.1f}% | "
            f"{s['p_val_raw']:.4f} | "
            f"**{s['p_val_holm']:.4f}** | "
            f"{verdict} |"
        )

    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Diagnóstico descriptivo de calidad y costo")
    md.append("")
    md.append("Se comprueba el margen práctico del plan sobre estimaciones puntuales. **No se ha ejecutado una prueba formal de no inferioridad ni calculado su intervalo de confianza.** La eficiencia física queda pendiente.")
    md.append("")
    md.append("- **Margen de no inferioridad:** $\\epsilon = 0.005$ (pérdida máxima admisible de 0.5 puntos porcentuales de Macro-F1).")
    md.append("- **Meta futura:** ahorro de al menos 20% en latencia real frente a una referencia equiparable. El cálculo actual solo es una proyección del modelo de costos.")
    md.append("")
    
    # Evaluar frente a Fusión Completa-6
    delta_f1_vs_f6 = mean_h2_f1 - mean_f6_f1
    lat_savings_vs_f6 = (mean_f6_lat - mean_h2_lat) / mean_f6_lat * 100
    non_inf_f6 = delta_f1_vs_f6 >= -0.005
    eff_f6 = lat_savings_vs_f6 >= 20.0

    # Evaluar frente a Cascada
    delta_f1_vs_casc = mean_h2_f1 - mean_casc_f1
    lat_savings_vs_casc = (mean_casc_lat - mean_h2_lat) / mean_casc_lat * 100

    md.append(f"- **FSC-Tex H2 frente a Fusión Completa-6:**")
    md.append(f"  - $\\Delta$ Macro-F1: `{delta_f1_vs_f6:+.4f}` (Margen $\\ge -0.005$: **{'CUMPLE' if non_inf_f6 else 'NO CUMPLE'}**)")
    md.append(f"  - Ahorro **estimado**: `{lat_savings_vs_f6:.1f}%`. No demuestra cumplimiento de la meta física.")
    md.append(f"- **FSC-Tex H2 frente a cascada base + 1 aumentador:**")
    md.append(f"  - $\\Delta$ Macro-F1: `{delta_f1_vs_casc:+.4f}`")
    md.append(f"  - Ahorro estimado relativo: `{lat_savings_vs_casc:+.1f}%`")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 5. Resumen de Ablaciones del Marco FSC-Tex")
    md.append("")
    md.append("Comparaciones descriptivas: H1 y el estado enriquecido reutilizan lambda seleccionado para H2; no tienen ajuste independiente equivalente. Las cifras siguientes son costos estimados, no cronometraje físico.")
    md.append("")
    
    mean_h1_f1 = np.mean([ds_summaries[d]["FSC_Tex_H1_Myopic"]["macro_f1"] for d in datasets_present if "FSC_Tex_H1_Myopic" in ds_summaries[d]])
    mean_h1_lat = np.mean([ds_summaries[d]["FSC_Tex_H1_Myopic"]["mean_latency_ms"] for d in datasets_present if "FSC_Tex_H1_Myopic" in ds_summaries[d]])
    mean_enr_f1 = np.mean([ds_summaries[d]["FSC_Tex_H2_Enriched_State"]["macro_f1"] for d in datasets_present if "FSC_Tex_H2_Enriched_State" in ds_summaries[d]])
    mean_enr_lat = np.mean([ds_summaries[d]["FSC_Tex_H2_Enriched_State"]["mean_latency_ms"] for d in datasets_present if "FSC_Tex_H2_Enriched_State" in ds_summaries[d]])

    md.append(f"1. **Comparación H2 vs H1 (no identifica no miopía con este presupuesto):**")
    md.append(f"   - H1 (Miope): Macro-F1 = `{mean_h1_f1:.4f}` | Latencia = `{mean_h1_lat:.2f} ms`")
    md.append(f"   - H2 (Bellman): Macro-F1 = `{mean_h2_f1:.4f}` | Latencia = `{mean_h2_lat:.2f} ms`")
    md.append(f"   - Diferencia H2–H1: `{(mean_h2_f1 - mean_h1_f1):+.6f}` de macro-F1; no atribuirla a dos adquisiciones que aquí no son factibles.")
    md.append("")
    md.append(f"2. **Ablación 2: Representación Enriquecida del Estado (Incertidumbre + PCA de Contenido):**")
    md.append(f"   - H2 Incertidumbre: Macro-F1 = `{mean_h2_f1:.4f}` | Latencia = `{mean_h2_lat:.2f} ms`")
    md.append(f"   - H2 Enriquecido: Macro-F1 = `{mean_enr_f1:.4f}` | Latencia = `{mean_enr_lat:.2f} ms`")
    md.append(f"   - Ganancia por proyectar contenido: `{(mean_enr_f1 - mean_h2_f1):+.4f}` de Macro-F1.")
    md.append("")
    md.append(f"3. **Política adaptativa vs. par estático (costos no exactamente igualados):**")
    md.append(f"   - Par Estático (`resnet50 + siglip_base`): Macro-F1 = `{mean_pair_f1:.4f}` | Latencia fija = `{mean_pair_lat:.2f} ms`")
    md.append(f"   - FSC-Tex H2: Macro-F1 = `{mean_h2_f1:.4f}` | Latencia adaptativa = `{mean_h2_lat:.2f} ms`")
    md.append(f"   - Ventaja adaptativa: `{(mean_h2_f1 - mean_pair_f1):+.4f}` de Macro-F1.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 6. Conclusión y trabajo pendiente")
    md.append("")
    md.append("**Veredicto: evidencia insuficiente para declarar superioridad de la propuesta.** Los archivos permiten reproducir las métricas, pero no cerrar las afirmaciones multietapa, físicas o relativas a la biblioteca de 22 bloques.")
    md.append("")
    md.append(f"H2 difiere de Completa-6 en {delta_f1_vs_f6 * 100:+.3f} puntos porcentuales de macro-F1. El margen puntual de 0.5 p.p. {'se satisface' if non_inf_f6 else 'no se satisface'}; ello no constituye una prueba formal. Contrastes con p Holm < 0.05: {sum(s['p_val_holm'] < 0.05 for s in stat_results)}/{len(stat_results)}.")
    md.append("")
    md.append("Conservar v2 como exploración, sin sobrescribir sus predicciones. P0 y los pilotos posteriores ya avanzaron respecto de este corte: el estado vigente y los pendientes de KTH, validación interna, puerta y tiempo físico están en la [auditoría P0–P4/cascada](AUDITORIA_P0_P4_CASCADA_2026-10-10.md) y en el plan v1.3.")

    content = "\n".join(md) + "\n"
    output_md.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(content)

    return content


def main():
    parser = argparse.ArgumentParser(description="Generador de Reporte FSC-Tex Fase 3 v2")
    parser.add_argument("--results_dir", type=Path, default=RESULTS_DIR, help="Directorio con los artefactos de la suite")
    parser.add_argument("--output_md", type=Path, default=DEFAULT_OUTPUT_MD, help="Archivo markdown de salida")
    args = parser.parse_args()

    print(f"Cargando artefactos desde: {args.results_dir}")
    runs = load_all_suite_results(args.results_dir)
    print(f"Total de condiciones cargadas: {len(runs)}")

    content = compute_statistics_and_report(runs, args.output_md)
    print(f"Reporte generado exitosamente en: {args.output_md}")


if __name__ == "__main__":
    main()
