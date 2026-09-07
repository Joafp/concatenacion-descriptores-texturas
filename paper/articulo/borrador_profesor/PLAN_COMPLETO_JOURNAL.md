# Plan Completo Journal — Todos los cambios sin medias
**Paper:** `main.tex` 772 líneas, 30 págs (v4) → objetivo 850+ líneas, 32-33 págs, `Accept` directo
**Fecha:** 2026-08-20 — Sesión única, ejecución total
**Principio:** Cero "en curso" al final. Cada tabla/figura citada debe tener números medidos, no estimados.

---

## Inventario de TODO lo dicho (ARS + Deep Research)

| # | Cambio | Fuente | Ubicación tex | Estado v4 | Para completar |
|---|--------|--------|---------------|-----------|----------------|
| 1 | Re-enmarcar Highlights/Abstract/Intro/Conclusión (falsación 26-26-4) | ARS R1 | `61,69,99,633` | Hecho | Verificar tono final |
| 2 | Apéndice A top-k autónomo + Tabla | ARS R1 | `640` `tab:topk-autonomo` | Hecho | — |
| 3 | Apéndice B costo 640 vs 80 vs 40 | ARS R1/R3 | `660` `tab:costo-busqueda` | Hecho estimado | Medir wall-clock real (P6) |
| 4 | Outex lenguaje IC+p | ARS R1/DA | `423,429,609` | Hecho | — |
| 5 | Disclaimer Tabla 2 | ARS R1 | `360` | Hecho | — |
| 6 | Guía práctica Tabla | Deep G1 | `591` `tab:guia-practica` | Hecho | — |
| 7 | Boxplot randoms Fig | Deep C | `495` `fig:random-boxplot` | Hecho (54/56 condiciones) | Añadir Outex box (n=1) nota |
| 8 | TOST + potencia texto | Deep P0 | `340,500` | Texto hecho | **Falta Tabla TOST por configuración** |
| 9 | §5.4 Group Lasso discusión | Deep P1 | `608` | Texto hecho | **Falta Tabla 56/56 completa con números medidos** |
| 10 | Apéndice C Group Lasso Tabla 50/56 | Deep P1 | `683` `tab:group-lasso` | Preliminar 50/56 | **Completar 56/56 CUReT+Outex** |
| 11 | Pareto FLOPs Fig | Deep P2 | `fig:pareto-flops` | Estimado literatura | **Medir FLOPs thop + ms/imagen reales** |
| 12 | §5.5 mRMR/CCA texto | Deep P3 | `608` | Texto hecho | **Falta Fig heatmap correlación + tabla mRMR** |
| 13 | §5.6 Ablación color FMD | ARS R2 | `608` `sec:ablacion-color` | Piloto 20 imgs | **Completar 15 folds FMD RGB vs gris** |
| 14 | Stability Jaccard 100 bootstraps | Deep P4 | `app:roadmap` | Mencionado | **Falta Tabla stability** |
| 15 | Roadmap Apéndice `app:roadmap` | Deep | `683` `tab:roadmap` | Hecho | — |
| 16 | Referencias `lui2026` `gao2016` | Deep | `references.bib:494` | Hecho | — |
| 17 | Pareto cost-aware knapsack (opcional) | Deep P6 | — | No iniciado | Dejar para journal si piden |

**Total a completar en esta sesión:** 8 tablas/figuras con números medidos (8,10,11,12,13,14). Todo lo demás ya está.

---

## Plan de ejecución en esta sesión (orden por dependencias, sin bloqueos)

### Fase A — Rápido (<30 min, sin cómputo pesado, sobre datos ya existentes)
- **A1 TOST Tabla:** Calcular TOST por configuración DTD/FMD (n=10/15, Δ=0.01, SD de `nested_summary.csv`) + potencia Outex (n=680). Genera `tab:tost` en § Análisis estadístico.
- **A2 mRMR/CCA Heatmap:** Sobre embeddings DTD/FMD ya cargados (19k-d), calcular correlación inter-bloque (6 bloques top: DINOv2-L, SigLIP, EVA-02, DenseNet121, DINOv2, lbp) → matriz 6×6, plot heatmap `figures/ccm_heatmap.pdf` + tabla mRMR.
- **A3 Stability Table:** 100 bootstraps sobre `selected_subsets.jsonl` + `random_subset_summary.csv` → Jaccard 0.43→0.48 ya preliminar, ahora con IC y tabla por dataset.

### Fase B — Medio (30-90 min, cómputo moderado, sin re-extracción)
- **B1 Group Lasso completo 56/56:** Ya tenemos 50/56 (DTD/FMD). Falta CUReT 4 + Outex 2. Usar proxy L1+group thresholding (saga, 600 samples, 3-fold) que es 10× más rápido que `group-lasso` nativo y pasó piloto. 6 condiciones × 10 α × 3 folds = 180 fits, ~15 min. Rellenar `tab:group-lasso` con 56/56 y recalcular Jaccard.
- **B2 Pareto FLOPs+ms reales:** Medir FLOPs con `thop` sobre 1 forward por modelo (20 bloques, sin re-entrenar) + wall-clock ms/imagen con `time` sobre 100 imágenes por bloque (batch 1, CPU). 20 bloques × 100 fwd <20 min. Actualizar `tab:costo-busqueda` (FLOPs reales, no estimados) y regenerar `fig:pareto-flops` con ms reales.

### Fase C — Pesado (60-120 min, requiere imágenes)
- **C1 Ablación color FMD 15 folds:** Re-extraer LBP/HOG RGB para 1000 imágenes FMD (3 canales → 80+1764 dims por bloque) con `skimage` (ya instalado `group-lasso`, falta `scikit-image` ~5 min pip). Luego 15 folds × 2 métodos (gris vs RGB) × SVM lineal = 30 fits, ~30 min. Tabla `tab:ablacion-color` con Δ macro-F1 por fold + test pareado.

**Dependencias:** C1 independiente de B1/B2, puede ir en paralelo. A1/A2/A3 preceden B1 (para reutilizar correlaciones).

---

## Cronograma esta sesión (max 4h wall-clock)

| Hora | Tarea | Artefacto |
|------|-------|-----------|
| 0:00-0:30 | A1 TOST + A2 heatmap + A3 stability (paralelo) | `tab:tost`, `figures/ccm_heatmap.pdf`, `tab:stability` |
| 0:30-1:30 | B1 Group Lasso 56/56 (6 conds) | `tab:group-lasso` completa 56/56 |
| 1:30-2:30 | B2 FLOPs+ms + figura Pareto real | `tab:costo-busqueda` actualizada, `fig:pareto-flops` v2 |
| 2:30-3:30 | C1 Ablación color FMD | `tab:ablacion-color` |
| 3:30-4:00 | Integrar todo en `main.tex`, `bibtex+pdflatex x3`, verificar 850 líneas/33 págs, re-ejecutar ARS | `main.pdf` final |

**Criterio de parada:** Cero "preliminar/en curso" en tablas citadas. Si algo falla (ej. `thop` no disponible), se deja estimado pero se declara explícitamente como estimado y se baja a `Minor` — no se oculta.

---

## Checklist final (Accept directo)

- [ ] `tab:tost` con p_TOST y potencia Outex
- [ ] `tab:group-lasso` 56/56 con Jaccard 0.48 vs 0.43 y Δ dentro ±0.01
- [ ] `tab:costo-busqueda` con FLOPs thop + ms/imagen medidos (no estimados)
- [ ] `fig:pareto-flops` v2 con frontera ms reales
- [ ] `figures/ccm_heatmap.pdf` + `tab:mrmr` (CCA >0.75)
- [ ] `tab:ablacion-color` FMD 15 folds (Δ RGB-gris)
- [ ] `tab:stability` 100 bootstraps
- [ ] `main.tex` 850 líneas, 32-33 págs, 0 referencias undefined, 0 "en curso"
- [ ] ARS v5 = `Accept` (todos ≥75)

*Si completamos Fase A+B (sin C1), ya es `Minor` sólido defendible; con C1 es `Accept`.*
