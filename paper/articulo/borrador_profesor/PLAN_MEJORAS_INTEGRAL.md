# Plan Integral de Mejoras — Borrador Profesor
**Paper:** Selección y concatenación de descriptores heterogéneos para clasificación de texturas (Ayala & Delgado, UNA-FP)
**Versión base:** `main.tex` 635 líneas → 732 líneas (post R1-R5) → objetivo 800+ líneas
**Fecha:** 2026-08-20
**Motivación:** Consolidar críticas ARS reviewer (Major Revision) + deep-research lit-review (9 papers 2022-2026) en un único roadmap ejecutable, sin ampliar biblioteca ni hacer fine-tuning.

---

## 1. Diagnóstico consolidado

| Fuente | Hallazgo crítico | Estado |
|--------|------------------|--------|
| ARS EIC/R1/DA | Framing vendía GFS como ganador, evidencia muestra empate 26-26-4 vs top-k y Outex IC incluye 0 | **Corregido** R1 (Highlights/Abstract/Conclusión re-enmarcados) |
| ARS R1 | Top-k heredaba k de GFS (circular) | **Corregido** Apéndice A `app:topk-autonomo` Tabla `tab:topk-autonomo` |
| ARS R1/R3 | Costo búsqueda 640 vs 80 fits no reportado; ahorro solo dimensional | **Corregido** Apéndice B `sec:costo-busqueda` Tabla `tab:costo-busqueda` + cita en Discusión |
| ARS R2 | Asimetría gris vs RGB sin cuantificar | **Pendiente** ablation color FMD (0.5 día) — no bloquea tesis, sí journal |
| Deep-research G1 | Falta benchmark de compresión (no accuracy) | **Corregido** framing + Tabla guía práctica `tab:guia-practica` |
| Deep-research G2 | Sin Pareto FLOPs/latencia | **Parcial** Tabla costo + Fig boxplot randoms; falta Fig Pareto FLOPs (P2) |
| Deep-research G3 | Sin baseline Group Lasso | **Pendiente** P1 (1-2 días) — mayor ROI |
| Deep-research G5 | Sin explicabilidad mRMR/CCA | **Pendiente** P3 (0.5 día) |

---

## 2. Plan por fases (esfuerzo sobre embeddings ya persistidos)

### Fase 0 — Críticos (ya aplicados, verificar compilación)
- [x] R1 Re-enmarcar narrativa (Abstract `main.tex:69`, Highlights `61`, Intro `99`, Conclusión `633`)
- [x] R4 Uniformizar Outex `main.tex:423,429,565,609` (IC + p)
- [x] R5 Disclaimer Tabla 2 `main.tex:360`
- [x] Apéndice A top-k autónomo `640`
- [x] Apéndice B costo búsqueda `660`
- [x] B Guía práctica `580` Tabla `tab:guia-practica`
- [x] C Boxplot randoms `485` Fig `fig:random-boxplot` (`figures/random_percentile_boxplot.pdf`)
- [x] E7 TOST + potencia Outex `340,500`
- [x] Roadmap futuro `637` + Apéndice `app:roadmap` Tabla `tab:roadmap`
- [ ] Verificar `bibtex + pdflatex x3` sin warnings (28 págs, 649KB)

### Fase 1 — Alto ROI tesis (≤3 días, sin GPU, defendible)
| ID | Extensión | Ubicación tex | Esfuerzo | Entregable |
|----|-----------|---------------|----------|------------|
| **P1** | Group Lasso por bloque (Yuan2006) vs GFS | Nueva subsec. `5.4` + Apéndice `app:group-lasso` Tabla Panel A/B | 1-2 días | Grid alpha 10 valores, 4 folds inner, métricas Δ macro-F1 ±0.01, k medio, Jaccard, sparsity pattern |
| **P2** | Pareto FLOPs/latencia por bloque | Fig. Pareto `figures/pareto_flops.pdf` + texto Discusión | 1 día | FLOPs `thop`, ms/imagen CPU/GPU, curva k=1..8 GFS/top-k/Group Lasso/completa |
| **P3** | mRMR/CCA + permutación SHAP | Subsec. `5.5` Fig. heatmap correlación | 0.5 día | CCA DINOv2-L↔SigLIP, mRMR score, Δ permutación |
| **P0** | TOST ya hecho, solo añadir tabla TOST por configuración | Tabla `tab:tost` | 4h | p_TOST por DTD/FMD, declaración equivalencia ±0.01 |

**No hacer en Fase 1:** gating, transfer, cost-aware knapsack, ampliar biblioteca, fine-tuning.

### Fase 2 — Journal (recomendada, 1-2 sem, si P1≈GFS)
- [ ] E3 Gating/attention ligera (MLP 20→20, 400 params) — si +0.01 en DTD/FMD, añade sección fusión aprendida; si no, reporta negative result
- [ ] E8 Stability selection (bootstrap 100× subsampling 50%) — identifica core estable 2-3 bloques
- [ ] A Ablación color FMD 1 dataset (LBP/HOG RGB) — cierra limitación #8 R2

### Fase 3 — Opcional (solo si reviewers lo piden)
- [ ] E4 Transfer cross-dataset DTD→FMD + corruptions ImageNet-C
- [ ] E6 Cost-aware knapsack (λ·FLOPs)

---

## 3. Modificaciones textuales a aplicar en este sprint

1. **Añadir subsección 5.4** `Discusión: Selección dispersa por bloque` con placeholder Group Lasso (metodología, sin resultados finales aún, con expectativa basada en Lui2026)
2. **Añadir subsección 5.5** `Redundancia inter-bloque` con placeholder mRMR/CCA
3. **Añadir Apéndice C** `app:group-lasso` con tabla comparativa GFS vs Group Lasso vs top-k (estructura idéntica a Tabla 2, filas vacías marcadas `en curso`)
4. **Generar Fig. Pareto FLOPs** placeholder (si no hay medición real, usar dims como proxy FLOPs con nota)
5. **Actualizar Conclusión** para citar nuevas subsecciones
6. **Actualizar referencias.bib** ya tiene `lui2026lassoflexnet` — verificar `gao2016compact` y `woo2023convnextv2` existen

---

## 4. Criterios de parada

- **Tesis defendible:** Fase 0 completa + P1 con resultado dentro ±0.01 (aunque sea negativo) — demuestra que "ranking basta" con 8× menos costo.
- **Journal enviable:** Fase 1 completa con Pareto + mRMR — paper pasa de "GFS wrapper" a "benchmark de compresión" (claim menos atacable que SOTA).
- **No parar por SOTA absoluto:** requiere pre-training LVD-142M, fuera de alcance.

---

## 5. Checklist de verificación post-modificación

- [ ] `bibtex main && pdflatex x3` sin undefined citations/references
- [ ] `figures/random_percentile_boxplot.pdf` incluido y referenciado `fig:random-boxplot`
- [ ] Nuevas tablas `tab:guia-practica`, `tab:roadmap`, `tab:group-lasso-placeholder` numeradas
- [ ] Apéndices A/B/C compilados (top-k autónomo, costo, group-lasso, roadmap+reproducibilidad)
- [ ] Re-ejecutar ARS reviewer full sobre `main.tex` 800 líneas y comparar decisión Major→Minor

---

*Generado por deep-research + ARS reviewer synthesis, 2026-08-20. Reporte lit-review completo: `paper/lit_review_out/reporte_lit_review_three_way_scan.md`*
