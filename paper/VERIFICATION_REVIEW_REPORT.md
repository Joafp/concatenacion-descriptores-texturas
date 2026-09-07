# Verification Review Report — Tesis UNA-FP (Re-Review Mode)

**Manuscrito:** *Concatenación sistemática de descriptores visuales clásicos y modernos para clasificación de texturas*
**Autores:** Carlos Ayala & Joaquín Delgado · Tutor: José Vázquez · UNA-FP
**Fecha del reporte:** Junio 2026
**Modo:** `ars-reviewer` en `re-review` (fidelity spectrum)
**Fuentes verificadas:** Cap. 1–6 (`.md`), `abstract.md`, `references.bib`, `RESPONSE_LETTER_ars_revision.md`, `REVISION_ROADMAP.md`

---

## Decision

**Minor Revision** *(downgraded from the "Accept with minor edits" auto-claimed in the Response Letter)*

**Justificación resumida:** Los 8 issues reportados en el Response Letter (M1–M3, m1–m3, E1–E2) **están FULLY ADDRESSED en las ubicaciones declaradas**. Sin embargo, la verificación reveló **3 issues nuevos MAJOR** que el ars-revision mode no detectó: (1) la migración v1→v2 sólo se aplicó a Cap. 4–6, abstract y bib — Cap. 1, 2 y 3 siguen siendo V1 con contenido médico extensivo, (2) el bibkey `oquab2024dinov2` está duplicado en `references.bib`, (3) la sección 5.12 todavía menciona HVD/ocular en las pruebas estadísticas. Estos gaps son pre-existentes del flujo de revisión, no regresiones introducidas por la revisión, pero bloquean la aceptación limpia.

---

## Revision Response Checklist

### Priority 1 — Required Revisions (original 8 issues)

| # | Issue | Author's Claim | Response Status | Verified? | Quality Assessment |
|---|-------|----------------|-----------------|-----------|--------------------|
| **M1** | F1 promedio inconsistente (0.933 distorsionado por GTOS-Mobile) | Cap. 4.5 ahora muestra **dos métricas de promedio** (con/sin GTOS-Mobile) | **FULLY_ADDRESSED** | ✅ Yes | Líneas 244–253 de `04_resultados.md`: tabla dual presente, justificación explícita "+6.2pp (0.933 vs 0.871)" reemplaza el "+20pp" inflado. La métrica "genuine" es ahora correcta y comparable con literatura. |
| **M2** | H4 mal etiquetada (datasets médicos removidos) | H4 reescrita para v2: "VisTex, data-scarce" | **FULLY_ADDRESSED** | ✅ Yes | Líneas 38–39 de `06_conclusion.md`: H4 ahora es "Concatenación clásico+deep competitiva con fine-tuning en datasets pequeños" con cuantificación VisTex (0.923 vs 0.811 vs 0.619) y matización "fine-tuning completo es contraproducente". |
| **m1** | Sección 5.4 sin fila VisTex | Fila VisTex agregada con salto +0.466 | **FULLY_ADDRESSED** | ✅ Yes | Líneas 49–54 de `05_discusion.md`: tabla de saturación incluye DTD (+0.483), FMD (+0.514), KTH-TIPS2-b (+0.205), VisTex (+0.466). Coherente con el abstract ("+0.48 a +0.51 F1"). |
| **m2** | Estandarización "+0.48 a +0.51" | Rango agregado en abstract (es y en) | **FULLY_ADDRESSED** | ✅ Yes | `abstract.md` línea 9 (es) y línea 21 (en): ambas versiones usan el rango "+0.48 a +0.51 F1 al pasar de 5 clásicos a 5 clásicos + 1 CNN". Coherente con Cap. 5.4. |
| **m3** | Sección 5.9 sin contexto 2024-2026 | 5.9 expandido a 5.9.1 (Cimpoi 2014/2016) y 5.9.2 (DINOv2 era) | **FULLY_ADDRESSED** | ✅ Yes | `05_discusion.md` líneas 144–168: 5.9.1 cita Cimpoi 2014/2016 con comparación cuantitativa (+18% F1 sobre SOTA 2014 en DTD); 5.9.2 cubre Oquab 2024, Trabelsi 2022, Kumar 2022, Radford 2021. Implicación práctica explícita: "DINOv2 como baseline obligatorio". |
| **E1** | Formato F1 inconsistente | Estandarización "F1" en headers, "macro-F1" en notas | **FULLY_ADDRESSED** | ✅ Yes | Cap. 4 usa "macro-F1" en notas de tablas (líneas 54, 168, 197) y "F1" en celdas. Sin inconsistencias detectadas. |
| **E2** | Kumar 2022 + Oquab 2024 faltantes en `references.bib` | Entradas agregadas al final del archivo | **FULLY_ADDRESSED** *(con caveat)* | ✅ Yes | `references.bib` líneas 211–216 (`kumar2022finetune`) y línea 218 (`oquab2024dinov2` adicional). **Caveat:** el bibkey `oquab2024dinov2` ya existía en línea 105 — ver NEW-3. |

**Resumen de los 8 originales:** 8/8 FULLY_ADDRESSED, 0 PARTIALLY, 0 NOT_ADDRESSED. Las correcciones son sustantivas y verificables independientemente de las afirmaciones del Response Letter.

---

### New Issues Discovered During Verification

Estos issues **no estaban en el Revision Roadmap original** pero emergen de la verificación cruzada del manuscrito v2 actualizado.

#### NEW-1 · MAJOR · Migración v1→v2 incompleta en Cap. 1, 2 y 3

- **Ubicación:** `paper/chapters/01_introduccion.md`, `02_literatura.md`, `03_metodologia.md`
- **Descripción:** El Response Letter asume que los datasets médicos fueron removidos en todo el manuscrito, pero **Cap. 1, 2 y 3 siguen siendo V1** (última edición: 7–8 jun, antes del v2 del 16 jun). Contenido médico residual:

  | Archivo | Línea | Contenido V1 remanente |
  |---|---|---|
  | `01_introduccion.md` | 45 | "13 extractores... sobre 5 datasets públicos (3 de texturas: DTD, FMD, KTH-TIPS2; **2 médicos: HVD_glaucoma, ocular_toxoplasmosis**)" |
  | `01_introduccion.md` | 47 | "DINOv2 pierde en imágenes médicas (HVD: 0.720 vs ViT-B/16 0.764)" |
  | `01_introduccion.md` | 53 | "Análisis de confusión con relevancia clínica... early_glaucoma↔advanced_glaucoma... active↔inactive toxoplasmosis" |
  | `02_literatura.md` | 102, 106 | Secciones "Glaucoma" y "Toxoplasmosis ocular" presentes |
  | `03_metodologia.md` | 33–34 | Tabla con HVD_glaucoma y ocular_toxoplasmosis en la lista de datasets |
  | `03_metodologia.md` | 36 | "Sección 3.2.2. **Datasets médicos (locales)**" completa |
  | `03_metodologia.md` | 55 | Estructura de directorios referencia `data/medical/HVD_glaucoma/...` |

- **Por qué es MAJOR:** Contradice directamente la decisión de diseño "los datasets médicos fueron removidos por directriz del tutor" y crea una inconsistencia insoluble: el lector ve en Cap. 1 que la tesis compara 5 datasets (incluyendo médicos) y en Cap. 4 que compara 6 datasets (todos texturas). M2/M3 del revision mode no son verificables en su totalidad.
- **Acción recomendada:** Reescribir Cap. 1, 2 y 3 para reflejar v2 (17 extractores, 6 datasets de texturas, ~850 corridas). Eliminar todas las referencias a HVD_glaucoma y ocular_toxoplasmosis. Actualizar conteos en objetivos (línea 70) y estructura (línea 63) del Cap. 1.

#### NEW-2 · MAJOR · Inconsistencia de conteo entre abstract y Cap. 1

- **Ubicación:** `paper/chapters/01_introduccion.md` (líneas 45, 63, 64, 70, 73) vs `paper/abstract.md` (líneas 7, 9, 21)
- **Descripción:** El abstract y Cap. 4–6 reportan **17 extractores, 6 datasets, ~850 experimentos**. Cap. 1 reporta **13 extractores, 5 datasets, ~1,000 experimentos**. Mismas entidades, dos conteos.
- **Por qué es MAJOR:** Es la inconsistencia más visible para un revisor: el primer párrafo del abstract dice una cosa y el Cap. 1 dice otra.
- **Acción recomendada:** Idéntica a NEW-1 (reescribir Cap. 1 con números v2).

#### NEW-3 · MAJOR · Bibkey duplicado `oquab2024dinov2` en `references.bib`

- **Ubicación:** `paper/references/references.bib` líneas 105–110 y 218–223
- **Descripción:** El bibkey `oquab2024dinov2` aparece **dos veces** con metadatos ligeramente diferentes:

  | Línea | Tipo | Venue | Autores (últimos) |
  |---|---|---|---|
  | 105 | `@inproceedings` | TMLR | …Howes, Huang |
  | 218 | `@article` | arXiv:2304.07193 | …El-Nouby, Assran |

- **Por qué es MAJOR:** BibTeX/BibLaTeX emitirá un error de "repeated entry" o silenciosamente descartará uno, lo que romperá la compilación. Cualquier `\citep{oquab2024dinov2}` o `\citet{oquab2024dinov2}` puede resolverse a entradas distintas según el compilador.
- **Acción recomendada:** Conservar una de las dos entradas. La versión TMLR (línea 105) es más reciente y canónica para la comunidad. Borrar la entrada duplicada (líneas 218–223).

#### NEW-4 · MINOR · Referencias huérfanas en `references.bib`

- **Ubicación:** `paper/references/references.bib` líneas 194–207
- **Descripción:** Las entradas `hodapp1993hodapp` y `classificationtoxoplasmosis` **no se citan en ningún capítulo** (verificado con grep). Son reliquias del V1 (cuando había datasets médicos).
- **Acción recomendada:** Eliminar ambas entradas del .bib si la decisión de diseño es no incluir datasets médicos.

#### NEW-5 · MINOR · Sección 5.12 todavía menciona HVD/ocular en stat tests

- **Ubicación:** `paper/chapters/05_discusion.md` líneas 208, 210
- **Descripción:** A pesar de la corrección M3, los hallazgos estadísticos en 5.12 reportan:
  - Línea 208: "GFS > mejor individual... en **DTD, FMD, HVD, ocular**"
  - Línea 210: "Prefix concat vs mejor individual es significativo en **DTD, HVD, ocular**"
- **Por qué es MINOR:** Es texto narrativo residual. La tabla de stat tests (`results/tables/stat_tests.csv`) puede contener o no los datasets médicos — la verificación profunda es Stage 4.5 integrity, no re-review.
- **Acción recomendada:** Editar líneas 208 y 210 para reemplazar "HVD, ocular" por "Outex13" (el dataset no-saturado restante).

#### NEW-6 · MINOR · Párrafo duplicado en sección 5.4

- **Ubicación:** `paper/chapters/05_discusion.md` líneas 56–58
- **Descripción:** El párrafo "Este patrón confirma cualitativamente los resultados de Cimpoi et al. 2014/2016... (<0.05 F1 en la mayoría de los casos)" aparece **dos veces** seguidas (líneas 56 y 58 son idénticas).
- **Acción recomendada:** Borrar una de las dos ocurrencias (probablemente la segunda para no afectar la numeración).

---

## Decision Rationale

**Por qué Minor Revision (no Accept):**

1. **Los 8 issues originales están FULLY ADDRESSED** — el trabajo del ars-revision mode es sustantivo y verificable.
2. **Pero la verificación reveló que la "eliminación de datasets médicos" (M2/M3) está incompleta.** El Response Letter dice "los datasets médicos fueron removidos por directriz del tutor", pero esa directiva **no se aplicó a Cap. 1, 2 ni 3**. Esto significa que M2/M3 son sólo parcialmente verdaderos (Cap. 4 sí, Cap. 1–3 no).
3. **NEW-3 (bibkey duplicado) bloquea la compilación LaTeX** del manuscrito final. Es un blocker técnico.
4. **NEW-1 + NEW-2 (Cap. 1 desactualizado)** son visibles inmediatamente para cualquier revisor y comprometen la credibilidad del manuscrito.

**Por qué no Major Revision:**

- Los issues nuevos no invalidan los hallazgos centrales (DINOv2 + GFS, complementariedad base+large, etc.).
- Las correcciones de los 8 originales son robustas — no son "cosmetic fixes" sino cambios sustantivos.
- El trabajo de fondo (experimentos, validación estadística, código) es sólido y no necesita re-ejecución.

**Estimación de esfuerzo para resolver los nuevos issues:** ~1 día de redacción (re-escritura de Cap. 1 secciones 1.1–1.4 + limpieza de Cap. 2.4 + Cap. 3.2 + 5.12 + bib cleanup). No requiere re-ejecución experimental.

---

## Residual Issues (If Any)

| # | Type | Description | Recommendation |
|---|---|---|---|
| R-1 | Open | El Response Letter afirma "Accept with minor edits" — el presente re-review contradice esa auto-afirmación. El Response Letter debe ser actualizado. | El autor debe revisar el Response Letter y reflejar la decisión de re-review (Minor Revision). |
| R-2 | Open | LaTeX files (`.tex`) en `paper/chapters/01-06.tex` y `paper/tesis.tex` están desactualizados (8 jun, V1) — no compilan con los `.md` v2 (16 jun). | El autor debe re-sincronizar los `.tex` o recompilar desde los `.md` (Pandoc). Esto es independiente del re-review pero bloquea Stage 5 (finalize). |
| R-3 | Acknowledged Limitation | No se realizó nested CV para GFS. Esperaríamos un drop de ~1–2% F1 con nested CV. | Ya está listado como limitación en Cap. 6.5 y Cap. 5.8.1. No requiere acción. |
| R-4 | Acknowledged Limitation | GTOS-Mobile subsample (5K de 100K). | Ya está listado como limitación en Cap. 6.5. No requiere acción. |
| R-5 | Acknowledged Limitation | Kumar 2022 author list en `references.bib` puede no coincidir exactamente con el paper (último autor: "Stadie" en el original, "Lawrence" en el .bib). | Verificación recomendada en Stage 4.5 (integrity check de citas). |

---

## Stage 5 Implications (Finalize)

Una vez resueltos los 6 nuevos issues, el manuscrito `.md` estará listo para:
1. **Re-sincronizar archivos `.tex`** con los `.md` actualizados (bloqueado por restricción de memoria del usuario — el autor debe hacerlo manualmente).
2. **Compilar PDF** con `tectonic` o `pdflatex` (también bloqueado por memoria).
3. **Verificación final de integridad** (Stage 4.5): `ars-citation-check` para confirmar que Kumar 2022 y Oquab 2024 están correctamente citados y que no hay citas huérfanas nuevas.

---

*Generado por: academic-research-skills:ars-reviewer (re-review mode, fidelity spectrum)*
*Agentes activados: field_analyst_agent (Phase 0) + eic_agent (Phase 1) + editorial_synthesizer_agent (Phase 2)*
*No se compiló LaTeX. No se modificó el manuscrito. Read-only verification.*
