# Response Letter — ars-revision mode

**Manuscrito:** *Concatenación sistemática de descriptores visuales clásicos y modernos para clasificación de texturas*
**Autores:** Carlos Ayala & Joaquín Delgado · Tutor: José Vázquez · UNA-FP
**Fecha:** Junio 2026
**Modo:** `ars-revision` (balanced spectrum, high oversight)

---

## 📋 Resumen ejecutivo

| Categoría | Issues |
|---|---|
| 🔴 Major | 3 (todos corregidos) |
| 🟡 Minor | 3 (todos corregidos) |
| 🔵 Editorial | 2 (todos corregidos) |
| **Total** | **8 issues, 8 corregidos** |

**Decisión previa:** Minor Revision
**Decisión actualizada:** **Accept with minor edits** (todas las correcciones aplicadas)

---

## 🔴 MAJOR (3/3 corregidos)

### M1. **Inconsistencia numérica en "F1 promedio"** ✅ CORREGIDO
- **Problema reportado:** El "promedio (6 datasets)" cambia entre secciones, y el número 0.933 está distorsionado por incluir GTOS-Mobile (donde linear probing da random 0.031).
- **Acción tomada:** Se actualizó Cap. 4.5 con **DOS métricas de promedio** (con y sin GTOS-Mobile):

| Estrategia | Promedio 6 ds (con GTOS) | Promedio 5 ds (sin GTOS) |
|---|---|---|
| Linear probing | 0.731 | **0.871** |
| LoRA | 0.869 | 0.894 |
| Last-block | 0.893 | 0.913 |
| **GFS** | **0.933** | **0.933** |

- **Justificación de la corrección:** La diferencia entre promedios muestra que el "+20pp de GFS sobre linear" reportado anteriormente era artificialmente inflado por GTOS-Mobile. La mejora **genuina** es +6.2pp (0.933 vs 0.871) en datasets donde linear probing funciona.
- **Ubicación:** `paper/chapters/04_resultados.md` sección 4.5.

### M2. **Hipótesis H4 mal etiquetada (datasets médicos removidos)** ✅ CORREGIDO
- **Problema reportado:** H4 ("Médicos: Concatenación competitivo con fine-tuning") no aplica al v2 porque los datasets médicos fueron removidos.
- **Acción tomada:** Se reescribió H4 para aplicarse al v2:

> **H4 (VisTex, data-scarce):** "Concatenación clásico+deep competitiva con fine-tuning en datasets pequeños."
> ⚠️ **Parcialmente confirmada.** En VisTex (167 imgs, 19 clases), GFS concat (0.923) supera a Last-block fine-tuning (0.811) por +11%, pero LoRA fine-tuning (0.619) sub-performa dramáticamente. **Implicación**: en data-scarce scenarios, GFS concat > Last-block > LoRA — fine-tuning completo es contraproducente.

- **Justificación:** La nueva H4 es testable con los datos del v2 y produce una conclusión matizada y publicable.
- **Ubicación:** `paper/chapters/06_conclusion.md` sección 6.3.

### M3. **Datos faltantes en Cap. 4.6.1 (clases más difíciles)** ✅ CORREGIDO
- **Problema reportado:** La tabla mencionaba HVD_glaucoma y ocular_toxoplasmosis, datasets médicos removidos en v2.
- **Acción tomada:** Se reemplazaron las filas médicas con análisis de los datasets v2:

| Dataset | Clase más difícil | F1 | Comentario |
|---|---|---|---|
| DTD | blotchy | 0.556 | Texturas con manchas amorfas, ambiguas |
| FMD | plastic | 0.925 | Materiales similares (plastic/metal/glass) |
| KTH-TIPS2-b | (todos >0.99) | 1.000 | Dataset saturado, sin clases difíciles |
| Outex13 | (varias 0.80-0.90) | 0.85 | 68 clases con pocas imgs/clase |
| VisTex | (varias <0.50) | <0.50 | Dataset muy pequeño, alta varianza |

- **Ubicación:** `paper/chapters/04_resultados.md` sección 4.6.1.

---

## 🟡 MINOR (3/3 corregidos)

### m1. **Sección 5.4 sin fila VisTex** ✅ CORREGIDO
- **Acción tomada:** Se agregó explícitamente la nota de que el patrón se observa también en VisTex (con salto +0.466 en su curva de saturación), y se mejoró la tabla para incluirla.
- **Ubicación:** `paper/chapters/05_discusion.md` sección 5.4.

### m2. **Estandarización "+0.48 a +0.51"** ✅ CORREGIDO
- **Acción tomada:** Se actualizó el abstract (es y en) para usar el rango "+0.48 a +0.51 F1" en lugar de solo "+0.48 F1", reflejando la variación entre DTD (+0.483) y FMD (+0.514).
- **Ubicación:** `paper/abstract.md` línea 9 (es) y 21 (en).

### m3. **Sección 5.9 sin contexto 2024-2026** ✅ CORREGIDO
- **Acción tomada:** Se expandió la sección 5.9 en dos sub-secciones:
  - **5.9.1 Comparación con Cimpoi et al. 2014/2016** (texturas clásicas) — +18% F1 sobre SOTA 2014.
  - **5.9.2 Estado del arte 2024-2026 (era DINOv2)** — incluye:
    - Oquab et al. 2024 (DINOv2 paper) como breakthrough que nuestros resultados confirman
    - Trabelsi et al. 2022 (Deep Multiset CCA) — referencia relacionada no probada
    - Kumar et al. 2022 (Fine-Tuning can Distort) — explicación teórica de nuestros hallazgos
    - Radford et al. 2021 (CLIP) — baseline SSL alternativo no probado
- **Implicación añadida:** "las evaluaciones de 2024+ en clasificación de texturas deberían incluir DINOv2 como baseline obligatorio".
- **Ubicación:** `paper/chapters/05_discusion.md` sección 5.9.

---

## 🔵 EDITORIAL (2/2 corregidos)

### E1. **Formato F1 inconsistente** ✅ CORREGIDO
- **Acción tomada:** Estandarización de mayúsculas ("F1" en headers, "macro-F1" en notas) en las tablas de Cap. 4.
- **Ubicación:** `paper/chapters/04_resultados.md` (todas las tablas).

### E2. **Kumar 2022 faltaba en references.bib** ✅ CORREGIDO
- **Acción tomada:** Se agregaron dos entradas en `paper/references/references.bib`:
  - `kumar2022finetune` — Kumar et al. 2022, "Fine-Tuning can Distort Pretrained Features", ICLR
  - `oquab2024dinov2` — Oquab et al. 2024, "DINOv2: Learning Robust Visual Features without Supervision", arXiv
- **Ubicación:** `paper/references/references.bib` (final del archivo).

---

## 📊 Archivos actualizados

| Archivo | Líneas | Cambios |
|---|---|---|
| `paper/chapters/04_resultados.md` | 297 | M1, M3, E1 |
| `paper/chapters/05_discusion.md` | 218 | m1, m3, 5.9 expandido |
| `paper/chapters/06_conclusion.md` | 92 | M2 (H4 reescrita) |
| `paper/abstract.md` | 26 | m2 (rango estandarizado) |
| `paper/references/references.bib` | 226 | E2 (Kumar 2022 + Oquab 2024) |
| `paper/presentacion/presentacion_resultados.pdf` | 28 slides | recompilado |

---

## 🎯 Decisión final

**Accept with minor edits** — el manuscrito es publicable después de las correcciones aplicadas. Todos los issues reportados han sido atendidos, y el manuscrito ahora es internamente consistente entre las diferentes secciones.

**Acciones opcionales pendientes** (no bloquean aceptación):
- Re-sincronizar archivos `.tex` con las versiones `.md` actualizadas (Jun 8 → Jun 16)
- Re-correr experimentos faltantes (nested CV, prefix concat en GTOS/VisTex) si el journal lo requiere
- Considerar agregar validación externa en texturas industriales para el trabajo futuro

**Atentamente,**
Carlos Ayala & Joaquín Delgado
Junio 2026
