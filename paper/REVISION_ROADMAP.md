# Revision Roadmap — Self-Review of Tesis (Generada por ars-revision-coach)

> **Modo:** `revision-coach` (balanced spectrum, medium oversight)
> **Origen de los comentarios:** self-review generado el 2026-06-05
> **Estado del manuscrito al momento de revisión:** Cap. 1, 4, 5, 6 escritos; Cap. 2, 3 pendientes; bibliografía y LaTeX pendientes

---

## Overview

- **Decisión implícita (si esto fuera una submission real):** **Major Revision**
- **Total comentarios:** 21
- **Por tipo:** 9 Major / 9 Minor / 3 Editorial / 0 Positive
- **Esfuerzo estimado:** **Substantial** (requiere escribir Cap. 2 y 3 desde cero, agregar análisis estadístico, refinar narrativa)

> ⚠️ **Nota crítica:** Aproximadamente el 30% de los comentarios (R1-1, R1-2, E-2, E-3) se deben a **secciones faltantes** del manuscrito. Estos son triviales de "resolver" — solo requiere escribir el contenido que falta.

---

## P1: Must Fix (address these first)

| # | Comment Summary | Reviewer | Type | Section | Suggested Action | Commitments |
|---|---|---|---|---|---|---|
| R1-1 | Cap. 2 (Lit Review) missing — work is in a vacuum | R1 | Major | Lit Review | Escribir Cap. 2 cubriendo: descriptores clásicos, CNN, ViT, SSL, feature fusion, GFS/feature selection | [add_citation, add_section] → new_section |
| R1-2 | Cap. 3 (Methodology) missing — not reproducible | R1 | Major | Methodology | Escribir Cap. 3 con descripción detallada de los 13 extractores, 5 datasets, protocolo CV, L2-norm, métricas, GFS algorithm | [add_section, add_methods_paragraph] → new_section |
| R1-3 | 5-fold CV without nested CV overestimates GFS | R1 | Major | Methodology (Sec. 3) | Implementar nested CV: outer 5-fold para evaluación final, inner 5-fold para GFS. Reportar ambos resultados | [add_experiment, add_methods_paragraph] → new_table |
| R1-7 | Statistical significance missing — +1.6% could be noise | R1 | Major | Results (Cap. 4) | Agregar paired t-test o Wilcoxon test sobre los 5 folds para cada comparación reportada | [add_analysis] → new_table |
| R2-1 | DINOv2 "best" claim based on only 3 datasets — small sample | R2 | Major | Results (Cap. 4) | Matizar el claim: "En los 3 datasets de texturas evaluados..." en vez de "siempre el mejor". Idealmente agregar ≥2 datasets más | [add_clarification, add_experiment] → discussion_paragraph |
| R2-5 | No SOTA comparison table — contribution hard to evaluate | R2 | Major | Results (Cap. 4) | Agregar Tabla 4.X: paper/año/método/dataset/F1, comparando con literatura reciente (Cimpoi 2014, Sánchez 2013, etc.) | [add_analysis, add_citation] → new_table |
| R3-1 | Medical datasets insufficiently described — no ethics, source, annotation | R3 | Major | Methodology (Cap. 3) | Agregar: fuente, protocolo de adquisición, aprobación ética, anotación de expertos, inter-annotator agreement | [add_clarification] → methods_paragraph |
| R3-3 | "Suitable for clinical screening" claim overstated — no clinical validation | R3 | Major | Discussion (Sec. 5.6bis) | Matizar: "research tool que necesita validación clínica adicional", remover "suitable for clinical screening" | [add_clarification] → discussion_paragraph |
| E-2 | Bibliography missing — no proper citations | Editor | Major | References | Crear paper/references/references.bib con todos los papers citados (DINOv2, ConvNeXt V2, Swin, LBP, GLCM, etc.) | [add_citation] → new_citation |
| E-3 | Abstract missing — no way to find the paper | Editor | Major | Front matter | Escribir abstract bilingüe (zh-TW/EN o es/EN) de 150-300 palabras | [add_section] → new_section |

**Total P1: 10 items (≈1-2 weeks de trabajo si no se re-corre todo)**

---

## P2: Should Fix (address after P1)

| # | Comment Summary | Reviewer | Type | Section | Suggested Action | Commitments |
|---|---|---|---|---|---|---|
| R1-4 | DINOv2 takes 17min/dataset — use 224×224 instead | R1 | Minor | Methodology | Documentar por qué 518×518 vs 224×224; o re-extraer con 224×224 y comparar | [add_clarification, add_experiment] → discussion_paragraph |
| R1-5 | PCA_k for fusion alternatives was too small (18) | R1 | Minor | Methodology (Sec. 5.11) | Re-correr sum/weighted_sum con PCA_k adaptativo por extractor (128 por extractor, no 18); reportar resultados | [add_experiment] → new_table |
| R1-6 | DTD confusion matrix (47 classes) hard to read | R1 | Minor | Results (Sec. 4.8) | Agregar tabla de top-10 pares confundidos para DTD (además de la heatmap) | [add_analysis] → new_table |
| R2-2 | FMD small (100/class) — high F1 could be split-dependent | R2 | Minor | Results (Cap. 4) | Reportar std del F1 across 5 folds y/o correr con otro random_state | [add_analysis] → prose_edit |
| R2-3 | "DINOv2 best" narrative unbalanced (ViT-B/16 wins HVD) | R2 | Minor | Discussion (Cap. 5) | Reescribir la narrativa: "DINOv2 es el mejor en texturas, Swin-T/ViT-B/16 en médicos" | [add_clarification] → discussion_paragraph |
| R2-4 | Clinical interpretation needs citations (Hodapp-Parrish-Anderson) | R2 | Minor | Discussion (Sec. 5.6bis) | Citar guía clínica para staging de glaucoma, y referencia para clasificación de toxoplasmosis activa/inactiva | [add_citation] → new_citation |
| R2-6 | "Negative results" sections feel tacked on — consolidate | R2 | Editorial | Discussion (Cap. 5) | Consolidar PCA, fine-tuning, MLP, fusion alternatives en una sola sección "5.X. Aproximaciones exploradas que no funcionaron" | [restructure] → new_section |
| R3-2 | Class imbalance in ocular not discussed enough | R3 | Minor | Results (Cap. 4) | Agregar tabla per-class precision/recall en main text, no solo appendix | [add_analysis] → new_table |
| R3-4 | 'early_glaucoma' is smallest class — report w/o it | R3 | Minor | Results (Cap. 4) | Reportar F1 con y sin 'early_glaucoma' para evaluar su impacto en HVD_glaucoma | [add_experiment] → new_table |
| R3-5 | DRLBP implementation is simplified approximation | R3 | Minor | Methodology (Cap. 3) | Documentar explícitamente que es aproximación, no la implementación original de [ref] | [add_clarification] → methods_paragraph |

**Total P2: 10 items (≈3-5 días de trabajo)**

---

## P3: Consider (address if time permits)

| # | Comment Summary | Reviewer | Type | Section | Suggested Action |
|---|---|---|---|---|---|
| E-1 | Too many figures — combine into multi-panel | Editor | Editorial | All | Combinar 5 saturation plots en una figura multi-panel |
| E-4 | Section numbering inconsistent | Editor | Editorial | All | Re-numerar y verificar consistencia (Cap. 4 salta de 4.9 a 4.10) |
| E-5 | AI disclosure should appear in camera-ready | Editor | Editorial | Front matter | Verificar política de la venue; asegurar que el AI_DISCLOSURE.md aparece en la versión final |

**Total P3: 3 items (≈1 día de trabajo)**

---

## Cross-Reviewer Patterns

| Pattern | Reviewers | Implication |
|---|---|---|
| **Secciones faltantes** (Cap. 2, 3, bibliography) | R1, E | Bloqueante. Sin Cap. 2 y 3, la tesis no es publicable. **Prioridad #1.** |
| **Significancia estadística ausente** | R1 | El reviewer técnico R1 lo pide explícitamente. Importante para credibilidad. |
| **Comparación con SOTA** | R2 | R2 (Results) lo pide. Sin esto, las contribuciones se ven "en el vacío". |
| **Matización de claims clínicos** | R2, R3 | Múltiples reviewers piden no sobre-claimar. Quitar "suitable for clinical screening". |

---

## Suggested Revision Order

1. **Escribir Cap. 2 y Cap. 3 (R1-1, R1-2):** esto desbloquea la mayoría de los otros items. Estimado: 2-3 días.
2. **Agregar abstract y bibliography (E-2, E-3):** necesarios para la submission. 1 día.
3. **Implementar nested CV y statistical tests (R1-3, R1-7):** crítico para credibilidad. 1-2 días de cómputo + redacción.
4. **Re-correr fusion alternatives con PCA_k fijo (R1-5):** corrige un experimento. 30 min de cómputo + redacción.
5. **Re-escribir narrativa de discusión (R2-3, R2-6, R3-3):** consolidar negative results, matizar claims. 1 día.
6. **Agregar SOTA comparison (R2-5):** tabla nueva. 0.5 día de búsqueda + redacción.
7. **Detalles médicos y de datasets (R3-1, R3-2, R3-4, R3-5):** completar metadata y reportar. 1 día.
8. **Editorial (E-1, E-4, E-5):** formato y consistencia. 0.5 día.

**Esfuerzo total estimado:** ~10-12 días de trabajo para Major Revision completa.

---

## Effort Estimation Summary

| Categoría | Esfuerzo |
|---|---|
| Secciones faltantes (Cap. 2, 3) | 2-3 días |
| Análisis estadístico | 1-2 días |
| Re-correr experimentos | 0.5-1 día |
| Redacción (re-writing, matización) | 2-3 días |
| Tablas y figuras nuevas | 1 día |
| Bibliografía y formato | 1 día |
| **TOTAL** | **~10-12 días (~2 semanas)** |

---

## Response Letter Skeleton

```
Dear Editor and Reviewers,

Thank you for the constructive and detailed feedback on our manuscript 
"Concatenación de descriptores visuales clásicos y modernos para clasificación 
de texturas: un estudio empírico con 13 extractores y 5 datasets" 
(Manuscript ID: [TBD]).

We have carefully addressed all 21 comments. Below we provide a 
point-by-point response. Major changes are highlighted in the revised 
manuscript.

## Response to Reviewer 1

### Comment R1-1: Literature review (Cap. 2) is missing
**Original comment:** "The paper lacks a literature review (Cap. 2)..."
**Response:** We have added a comprehensive literature review (Chapter 2, 
[XX] pages) covering [classical descriptors / CNNs / ViTs / SSL / 
feature fusion / GFS / applications].
**Changes made:** New section in Cap. 2. Added [N] references.

### Comment R1-2: Methodology (Cap. 3) is missing
**Original comment:** "The methodology (Cap. 3) is missing..."
**Response:** We have added a detailed methodology chapter (Chapter 3, 
[XX] pages) with: dataset descriptions, exact extractor configs, 
CV protocol, L2-normalization, metrics, GFS algorithm pseudocode, 
hardware/software specs.
**Changes made:** New section in Cap. 3. Reproducibility info added.

### Comment R1-3: 5-fold CV without nested CV overestimates GFS
[PLACEHOLDER — to be filled after running nested CV experiments]

### Comment R1-7: Statistical significance missing
[PLACEHOLDER — to be filled after running t-tests]

[... comments R1-4 through R1-6 similarly ...]

## Response to Reviewer 2

### Comment R2-1: DINOv2 "best" claim based on only 3 datasets
[PLACEHOLDER — to be filled with revised narrative]

### Comment R2-5: SOTA comparison missing
[PLACEHOLDER — to be filled after building SOTA table]

[... comments R2-2, R2-3, R2-4, R2-6 similarly ...]

## Response to Reviewer 3

### Comment R3-1: Medical datasets insufficiently described
[PLACEHOLDER — to be filled with dataset metadata]

### Comment R3-3: "Suitable for clinical screening" claim overstated
**Response:** We have revised the wording throughout the manuscript to 
remove the "suitable for clinical screening" claim. The model is now 
presented as a research tool that requires further clinical validation.
**Changes made:** Cap. 5, Sec. 5.6bis.5 — replaced "suitable for clinical 
screening" with "research tool that needs further clinical validation 
before deployment."

[... comments R3-2, R3-4, R3-5 similarly ...]

## Response to Editor

### Comment E-2: Bibliography missing
**Response:** We have added a complete bibliography in BibTeX format 
(paper/references/references.bib) with all [N] cited works.
**Changes made:** New file paper/references/references.bib.

### Comment E-3: Abstract missing
**Response:** We have added a bilingual abstract (es/EN, ~250 words each).
**Changes made:** New front-matter section.

[... comments E-1, E-4, E-5 similarly ...]

## Summary of Major Changes

1. **Added 2 new chapters** (Cap. 2 Literature Review, Cap. 3 Methodology)
2. **Added bibliography** ([N] references in BibTeX)
3. **Added abstract** (bilingual, es/EN)
4. **Implemented nested CV** (new results in Cap. 4)
5. **Added statistical tests** (paired t-tests, p-values, in Cap. 4)
6. **Added SOTA comparison table** (new table in Cap. 4)
7. **Revised clinical claims** (removed "suitable for clinical screening")
8. **Re-ran fusion alternatives** (with proper PCA_k, updated Cap. 5)
9. **Consolidated negative results** (one section instead of four)
10. **Editorial cleanup** (figure consolidation, section numbering)

We believe these revisions significantly strengthen the manuscript and 
address all reviewer concerns. We look forward to your decision.

Sincerely,
[Author Name]
[Affiliation]
[Date]
```

---

## Revision Tracking Template (pre-filled)

Para tracking del progreso:

| # | Tipo | Status | Action taken |
|---|---|---|---|
| R1-1 | Major (P1) | ⬜ Pendiente | Escribir Cap. 2 |
| R1-2 | Major (P1) | ⬜ Pendiente | Escribir Cap. 3 |
| R1-3 | Major (P1) | ⬜ Pendiente | Implementar nested CV |
| R1-4 | Minor (P2) | ⬜ Pendiente | Documentar DINOv2 518×518 vs 224×224 |
| R1-5 | Minor (P2) | ⬜ Pendiente | Re-correr fusion alternatives con PCA_k fijo |
| R1-6 | Minor (P2) | ⬜ Pendiente | Tabla top-10 confusion DTD |
| R1-7 | Major (P1) | ⬜ Pendiente | Paired t-tests |
| R2-1 | Major (P1) | ⬜ Pendiente | Matizar DINOv2 claim |
| R2-2 | Minor (P2) | ⬜ Pendiente | Reportar std across folds FMD |
| R2-3 | Minor (P2) | ⬜ Pendiente | Reescribir narrativa discusión |
| R2-4 | Minor (P2) | ⬜ Pendiente | Citar guías clínicas |
| R2-5 | Major (P1) | ⬜ Pendiente | SOTA comparison table |
| R2-6 | Editorial (P2) | ⬜ Pendiente | Consolidar negative results |
| R3-1 | Major (P1) | ⬜ Pendiente | Metadata datasets médicos |
| R3-2 | Minor (P2) | ⬜ Pendiente | Per-class P/R en main text |
| R3-3 | Major (P1) | ⬜ Pendiente | Quitar "suitable for clinical screening" |
| R3-4 | Minor (P2) | ⬜ Pendiente | F1 sin early_glaucoma |
| R3-5 | Minor (P2) | ⬜ Pendiente | Documentar DRLBP simplificación |
| E-1 | Editorial (P3) | ⬜ Pendiente | Combinar figuras |
| E-2 | Major (P1) | ⬜ Pendiente | Crear references.bib |
| E-3 | Major (P1) | ⬜ Pendiente | Escribir abstract |
| E-4 | Editorial (P3) | ⬜ Pendiente | Re-numerar secciones |
| E-5 | Editorial (P3) | ⬜ Pendiente | Verificar AI disclosure en final |

---

*Generado por: academic-research-skills:ars-revision-coach*
*Modo: full (revision-coach con self-review)*
*Origen de comentarios: self-review generado (no reviewers reales)*
*Próximo paso recomendado: abordar R1-1 y R1-2 (Cap. 2 y 3) que son los más impactantes*
