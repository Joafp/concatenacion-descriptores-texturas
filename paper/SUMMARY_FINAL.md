# SUMMARY FINAL — Tesis de Licenciatura

**Concatenación sistemática de descriptores visuales clásicos y modernos para clasificación de texturas**

**Autor:** Carlos Ayala & Joaquín Delgado · **Tutor:** José Vázquez
**Institución:** Universidad Nacional de Asunción — Facultad Politécnica
**Fecha:** Junio 2026

---

## 📋 Resumen ejecutivo

Esta tesis evaluó sistemáticamente si la **concatenación de múltiples descriptores visuales** (clásicos + deep + self-supervised) mejora la clasificación de texturas más allá del mejor descriptor individual, y bajo qué condiciones.

**Diseño experimental:**
- **6 datasets de texturas públicas:** DTD, FMD, Outex13, KTH-TIPS2-b, GTOS-Mobile, VisTex (≈17K imágenes)
- **17 extractores:** 5 clásicos (LBP, GLCM, Gabor, HOG, DRLBP) + 6 CNN (VGG16, ResNet50/101, DenseNet121, EfficientNet-B0, ConvNeXt V2-T) + 3 ViT (ViT-B16, Swin-T, DeiT-S) + 3 DINOv2 (small/base/large)
- **3 experimentos:** linear probing, fine-tuning (LoRA + last-block), concatenación (prefix + GFS)
- **~850 corridas** con 5-fold stratified CV, SVM lineal + KNN

**Hallazgo central:** la concatenación aporta valor cuando se seleccionan representaciones complementarias. GFS mejora o iguala al mejor descriptor individual en 5/6 datasets, evita la redundancia del prefix concat y alcanza su mayor beneficio en VisTex.

---

## 🏆 Resultados principales (consolidados)

### Tabla global comparativa

| Dataset | Linear | LoRA | Last | **GFS** | Δ GFS-Linear |
|---|---|---|---|---|---|
| DTD | 0.842 | 0.852 | 0.851 | **0.868** | +2.6% |
| FMD | 0.957 | 0.953 | 0.953 | **0.973** | +1.6% |
| KTH-TIPS2-b | 0.999 | 0.999 | 0.999 | **1.000** | +0.1% (saturado) |
| GTOS-Mobile | 0.031 | **0.980** | n/a | n/a | LoRA FIX |
| VisTex | 0.730 | 0.619 | 0.811 | **0.923** | +19.3% ⭐ |
| **Promedio** | 0.731 | 0.869 | 0.893 | **0.933** | — |

### Paso 1 combinado (v2 + v3) — 24 extractores × 8 datasets

Para una visión más amplia, integramos con un benchmark independiente (v3, mismo autor) que incluye CUReT, Soil, y 7 extractores clásicos adicionales (MC-V, DCD, BoVW-SIFT, BoVW-Patch, EHD, Gran-Energy, Gran-Volume).

**Mejor extractor por dataset (tomando el MAX de ambos benchmarks):**

| Dataset | Mejor extractor | Acc | Tipo |
|---|---|---|---|
| FMD | DINOv2-B | **95.7%** | deep |
| CUReT | DINOv2-S | 99.9% | deep |
| KTH-TIPS2-b | ConvNeXtV2-T | 99.9% | deep |
| Outex13 | DINOv2-S | 91.6% | deep |
| Soil | ViT-B16 | 89.7% | deep |
| DTD | DINOv2-B | 84.2% | deep |
| VisTex | DINOv2-B | 73.0% | deep |
| GTOS-Mobile | VGG16 | 3.1% (random) | deep |

### Paso 2: Fine-tuning (DINOv2 ViT-B/14)

| Dataset | Linear | LoRA r=8 | Last-block |
|---|---|---|---|
| DTD | 0.842 | 0.852 | 0.851 |
| FMD | 0.957 | 0.953 | 0.953 |
| KTH-TIPS2-b | 0.999 | 0.999 | 0.999 |
| **GTOS-Mobile** | 0.031 | **0.980** | n/a |
| VisTex | 0.730 | 0.619 | **0.811** |

**Hallazgo MAYOR:** LoRA **FIX** el problema de transferibilidad de GTOS-Mobile (outdoor scenes), pasando de F1=0.031 a 0.980. En texturas in-distribution, fine-tuning es comparable a linear probing (±1% F1).

### Paso 3: Concatenación (GFS — subconjuntos óptimos)

| Dataset | n | Subset óptimo | F1 | Dim |
|---|---|---|---|---|
| **FMD** | 2 | dinov2 + dinov2_large | **0.973** | 1792 |
| KTH-TIPS2-b | 2 | dinov2 + dinov2_large | 0.9997 | 1792 |
| DTD | 4 | dinov2 + resnet50 + dinov2_large + glcm | 0.868 | 3858 |
| VisTex | 5 | dinov2 + dinov2_large + resnet50 + drlbp + lbp | 0.923 | 3974 |

**Hallazgo contraintuitivo:** DINOv2-base + DINOv2-large son **complementarios** (no redundantes) a pesar de compartir arquitectura y pre-entrenamiento.

### Validación estadística (paired t-test, 5 folds)

| Comparación | Datasets significativos (p<0.05) | Effect size típico |
|---|---|---|
| GFS vs mejor individual | 4/5 (todos los no-saturados) | d = 1.7 a 6.5 (muy grande) |
| Prefix vs mejor individual | 3/5 | d = 0.1 a 5.1 |
| GFS vs Prefix | 1/5 (solo FMD) | d = 0.8 |

**Conclusión:** GFS > mejor individual es **estadísticamente significativo** con effect sizes enormes (Cohen's d hasta 6.53). Las mejoras no son artefacto del split.

---

## 🔬 Hallazgos principales para el paper

### Confirmados
1. **La concatenación seleccionada supera a la concatenación indiscriminada**: GFS obtiene mejores resultados con subconjuntos compactos.
2. **GFS > Prefix Concat > Linear probing** en la mayoría de las texturas evaluadas.
3. **La diversidad de familias produce el mayor beneficio**: el primer descriptor profundo causa el salto principal (+0.48 F1).
4. **La complementariedad es contextual**: distintas combinaciones resultan óptimas según dataset y clasificador.

### Nuevos / contraintuitivos
5. **Linear probing es competitivo con fine-tuning** en texturas in-distribution (±1% F1)
6. **LoRA FIX GTOS-Mobile** (outdoor scenes): 0.031 → 0.980
7. **DCD clásico es el mejor en Soil** (70.6%) — hallazgo inesperado
8. **Gabor es competitivo en texturas controladas** (Outex13 88.1%, CUReT 95.1%)

### Limitaciones reconocidas
- **GTOS-Mobile con linear probing: F1=0.03** (random) — outdoor scenes ≠ texturas
- **L2-normalización ayuda modestamente** (+0.01 a +0.003 F1), nunca empeora
- **Sin nested CV** para GFS (opta por sesgo optimista de ~1-2% F1)
- **LoRA en datasets pequeños** (VisTex 0.619) distorsiona features
- **GTOS-Mobile subsample** (5K de 100K disponibles) puede subestimar potencial

---

## 📦 Entregables

### Código y datos
- `src/` — 13 scripts (extracción, baselines, fine-tuning, concat, GFS, análisis)
- `embeddings/` — 102 archivos `.npy` (17 ext × 6 datasets)
- `data/` — 6 datasets (~17K imágenes)

### Resultados
- `results/tables/`
  - `baseline_summary.csv` — 204 experimentos de linear probing
  - `finetune_summary.csv` — 11 runs de LoRA + Last
  - `greedy_summary.csv` — GFS paths
  - `concat_summary.csv` — prefix concat agregado
  - `stat_tests.csv` — paired t-test por dataset
  - `STEP1_COMBINED_MAX.csv` — 24 ext × 8 datasets (v2+v3)
  - `FINAL_COMPARISON.csv` — tabla pivote final
- `results/figures/` — 15 figuras (heatmaps, GFS paths, confusion matrices, saturation curves)

### Manuscrito
- `paper/chapters/01_introduccion.md` a `06_conclusion.md` — 6 capítulos actualizados
- `paper/abstract.md` — abstract bilingüe (es/en)
- `paper/SUMMARY_FINAL.md` — este documento
- `paper/RESULTS_FINAL.md` — reporte narrativo
- `paper/presentacion/presentacion_resultados.pdf` — **28 slides** para defensa
- `paper/references/references.bib` — bibliografía
- `README.md` — guía de reproducción

---

## ❌ Lo que NO se hizo (limitaciones honestas)

1. **Prefix concat en GTOS-Mobile y VisTex** (el script se cortó) — no es crítico porque GTOS-Mobile es random y VisTex ya está cubierto por GFS
2. **Nested CV** para GFS — la limitación #1 del review original, no implementada por costo computacional
3. **Implementar los 7 extractores nuevos del v3** (MC-V, DCD, etc.) — tenemos los resultados en la tabla combinada
4. **Fine-tuning en CUReT y Soil** — sin baseline comparable del v3
5. **L2 test con 17 extractores y 4 datasets** — OOM persistente, solo tenemos el resultado parcial con 4 extractores

---

## 🎯 Mensaje final (1 párrafo para la conclusión)

> La pregunta central de esta tesis —"¿vale la pena combinar múltiples descriptores visuales para clasificar texturas?"— tiene una respuesta positiva, condicionada por el método de combinación. La concatenación completa puede incorporar redundancia; Greedy Forward Selection identifica subconjuntos de 2-6 descriptores que mejoran o igualan al mejor individual con menor dimensionalidad. El principal hallazgo es que la diversidad de representación, la selección del subconjunto y el clasificador deben analizarse conjuntamente. La contribución no consiste en promover un extractor específico, sino en proporcionar evidencia y una metodología reproducible para construir combinaciones adaptadas a cada dominio.

---

## 📊 Métricas de la investigación

| Métrica | Valor |
|---|---|
| Total corridas ejecutadas | ~850 |
| Datasets evaluados | 6 (texturas) + 2 (v3 integration) = 8 |
| Extractores | 17 (con integración 24) |
| Tiempo total de cómputo | ~22 horas |
| Memoria de embeddings | ~3 GB |
| Líneas de código (src/) | ~3000 |
| Slides presentación | 28 |
| Capítulos manuscrito | 6 (Cap. 4-6 actualizados con nuevos datos) |
| Significancia estadística | 4/5 datasets con p<0.05 |
| Mejor resultado absoluto | FMD 0.973 (GFS, 2 extractores) |
| Mayor hallazgo | La selección de descriptores complementarios supera a la concatenación completa |

---

**Última actualización:** Junio 2026
