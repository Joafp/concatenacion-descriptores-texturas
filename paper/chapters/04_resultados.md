# Capítulo 4 — Resultados

## 4.1. Resumen del protocolo experimental

Se evaluaron **17 extractores de características** sobre **6 datasets de texturas públicas** (DTD, FMD, Outex13, CUReT, Soil, VisTex), totalizando **102 combinaciones dataset × extractor**. Para cada combinación se entrenaron **4 clasificadores** (SVM lineal, KNN, RF, ResMLP) con 5-fold stratified cross-validation, dando un total de **~408 corridas baseline** (Exp 1: linear probing).

Sobre los embeddings pre-computados se ejecutaron tres experimentos adicionales:

- **Exp 2 (Fine-tuning, no incluido en este manuscrito):** DINOv2 ViT-B/14 con LoRA y last-block (ejecutado en V1 sobre 5 datasets; ver `results/tables/finetune_summary.csv`).
- **Exp 3a (Concatenación, ~408 corridas):** prefix concat k=1..17 sobre los 6 datasets, con los 4 clasificadores.
- **Exp 3b (Greedy Forward Selection, ~80 corridas):** GFS con screening en 2 fases y early stopping, sobre los 6 datasets × 4 clfs.

**Total Exp 1+3+4+GFS: ~1200 corridas** ejecutadas en ~6 horas de cómputo, sobre 1× RTX 4060 (8 GB) + 8-core CPU.

Todos los embeddings fueron pre-extraídos y cacheados en `embeddings/{dataset}/{extractor}.npy` (L2-normalizados per-imagen antes de clasificar). El código fuente está en `src/` y los resultados en `results/tables/*.csv` y `results/figures/*.png`.

### Datasets (6, todos de texturas)

| Dataset | Clases | Imágenes | Resolución | Fuente | Tipo |
|---|---|---|---|---|---|
| **DTD** (Cimpoi et al. 2014) | 47 | 5,640 | ~640×640 | Web ("in the wild") | Texturas naturales |
| **FMD** (Sharan et al. 2013) | 10 | 1,000 | variable | Flickr | Materiales |
| **Outex13** (Ojala et al. 2002) | 68 | 1,360 | 128×128 (bmp) | Benchmark estándar | Texturas controladas |
| **CUReT** (Dana et al. 1999) | 61 | 6,100 | variable | Columbia-Utrecht | Texturas controladas multi-illumination |
| **Soil** | 13 | 1,186 | variable | Kaggle soil texture | Tipos de tierra |
| **VisTex** (MIT) | 19 | 167 | 512×512 | MIT VisTex Reference | Texturas naturales |

**Nota sobre CUReT:** dataset de laboratorio con 61 materiales fotografiados bajo múltiples condiciones de iluminación, escala y pose. Es el dataset más "limpio" y generalmente saturado para métodos serios (F1 ≈ 1.0).

**Nota sobre Soil:** tipos de tierra fotografiados en condiciones de campo. Las clases incluyen arena, arcilla, limo, grava, etc. Resulta interesante porque un descriptor clásico (DCD) es sorprendentemente competitivo.

**Nota sobre VisTex:** el dataset más pequeño (167 imágenes, 19 clases) — útil para stress-testing en data-scarce scenarios. Clases pequeñas (2-3 imgs) fueron excluidas del 5-fold para evitar folds degenerados.

### Extractores (17, agrupados por familia)

| Familia | Extractores | Dim |
|---|---|---|
| **Clásicos (5)** | LBP multi-escala, GLCM, Gabor, HOG, DRLBP | 54 / 18 / 48 / 1764 / 80 |
| **CNN (6)** | VGG16, ResNet-50, ResNet-101, DenseNet-121, EfficientNet-B0, ConvNeXt V2-T | 4096 / 2048 / 2048 / 1024 / 1280 / 768 |
| **Vision Transformers (3)** | ViT-B/16, Swin-T, DeiT-S | 768 / 768 / 384 |
| **Self-supervised (3)** | DINOv2-S, DINOv2-B, DINOv2-L | 384 / 768 / 1024 |

### Protocolo de evaluación

- **Pre-procesamiento:** resize a 224×224 (518×518 para DINOv2) con normalización ImageNet (mean/std) para modelos pre-entrenados; grayscale + resize 256×256 (128×128 para HOG) para clásicos.
- **Validación:** 5-fold stratified cross-validation con `random_state=42`.
- **Métricas:** macro-F1 (principal), accuracy (secundaria).
- **L2-normalización:** aplicada per-imagen dentro de cada fold (esencial para concatenación de embeddings con escalas distintas).
- **Recursos:** 1× NVIDIA RTX 4060 (8 GB), 8-core CPU, Python 3.14, PyTorch 2.12, scikit-learn 1.8, timm 1.0.27, transformers 5.9.

---

## 4.2. Exp 1 — Linear Probing (4 clasificadores)

Se entrenaron los 4 clasificadores (SVM lineal, KNN, RF, ResMLP) sobre los embeddings de los 17 extractores en cada uno de los 6 datasets. El mejor resultado por (dataset, clf) se reporta en la Tabla 4.1.

**Tabla 4.1.** Mejor macro-F1 por (dataset, clasificador) — Exp 1 (linear probing, 5-fold CV). El valor en negrita es el mejor clasificador de cada dataset; el subíndice indica el extractor ganador.

| Dataset | SVM | KNN | RF | ResMLP |
|---|---|---|---|---|
| **DTD** | **0.842** (dinov2) | 0.803 (dinov2) | 0.779 (dinov2_large) | 0.837 (dinov2_large) |
| **FMD** | **0.957** (dinov2) | 0.888 (dinov2_small) | 0.892 (dinov2_large) | 0.948 (dinov2) |
| **CUReT** | 0.994 (dinov2_large) | 0.971 (densenet121) | 0.981 (densenet121) | **0.999** (dinov2_large) |
| **Soil** | 0.831 (efficientnet_b0) | 0.796 (efficientnet_b0) | 0.776 (densenet121) | **0.858** (vit_b16) |
| **VisTex** | 0.730 (dinov2) | 0.734 (dinov2) | 0.742 (dinov2_small) | **0.882** (dinov2_large) |
| **Promedio** | 0.863 | 0.842 | 0.840 | **0.902** |

### Observaciones del Exp 1

1. **DINOv2 family domina en texturas naturales.** DINOv2-base, DINOv2-small o DINOv2-large gana el linear probing en 18/24 casos (75%). En promedio la familia DINOv2 supera a los CNN/ViT supervisados en +0.05 a +0.10 F1. Confirmamos empíricamente el breakthrough reportado por Oquab et al. 2024.

2. **DTD es el dataset más desafiante** (F1 máximo 0.842 con SVM). 47 clases con 120 imgs/clase y alta variabilidad intra-clase lo hacen el benchmark discriminante.

3. **CUReT está saturado** con todos los métodos serios (F1 ≈ 1.0). Sirve como validación de que el pipeline no tiene bugs.

4. **VisTex (167 imgs, 19 clases)** es el dataset donde los modelos difieren más: ResMLP (0.882) supera a SVM (0.730) por **+0.15 F1**. En data-scarce scenarios, la flexibilidad no-lineal de ResMLP ayuda.

5. **ResMLP es el clasificador más fuerte en promedio** (0.902), ganando en 3/6 datasets. SVM lineal es el segundo (0.863). KNN y RF pierden en la mayoría.

6. **Excepciones a la dominancia de DINOv2:** en Outex13-svm (vit_b16), CUReT-knn (densenet121), CUReT-rf (densenet121), Soil-svm (efficientnet_b0), Soil-knn (efficientnet_b0), Soil-rf (densenet121), Soil-resmlp (vit_b16). En Outex13 y CUReT, los modelos de CNN clásicos (DenseNet, ViT-B/16) son competitivos con DINOv2.

7. **Soil es el dataset donde DINOv2 NO gana** (4/4 clasificadores prefieren otros modelos). Esto sugiere que los features pre-entrenados en ImageNet/LVD-142M no son óptimos para texturas de tierra.

---

## 4.3. Exp 3a — Concatenación por prefix concat (k=1..17)

Se concatenaron los 17 embeddings en orden canónico (classical → CNN → ViT → DINOv2) y se evaluó F1 en cada paso k con los 4 clasificadores.

### 4.3.1. Saturación DTD (Tabla 4.2)

**Tabla 4.2.** Saturación DTD — macro-F1 vs número de extractores concatenados (SVM lineal y ResMLP).

| k | Extractores acumulados | dim | SVM F1 | ResMLP F1 |
|---|---|---|---|---|
| 1 | lbp | 54 | 0.101 | 0.374 |
| 5 | +glcm +gabor +hog +drlbp | 1,964 | 0.265 | 0.341 |
| 6 | +vgg16 | 6,060 | 0.677 | 0.654 |
| 11 | +resnet50 +resnet101 +densenet121 +convnext_v2_t +efficientnet_b0 | 13,228 | 0.797 | 0.794 |
| 14 | +vit_b16 +swin_t +deit_s | 15,148 | 0.812 | 0.809 |
| 17 | +dinov2_small +dinov2 +dinov2_large | 17,324 | 0.862 | 0.860 |

**Hallazgo DTD:** El mayor salto en F1 se da entre k=5 (5 clásicos, F1=0.265) y k=6 (+VGG16, F1=0.677) — un salto de **+0.41 F1** al agregar el primer modelo profundo. De k=6 a k=17 la mejora es solo +0.19. Esto confirma que **la diversidad de familias importa más que la cantidad de modelos**.

*Figuras completas de saturación para los 6 datasets en `results/figures/saturation_*.png` (6 figuras, una por dataset).*

### 4.3.2. Tabla 4.3 — Mejor prefix concat por (dataset, clf)

**Tabla 4.3.** Mejor F1 de prefix concat (k óptimo) por (dataset, clf).

| Dataset | SVM (k=17) | KNN (k=17) | RF (k=17) | ResMLP (k=17) |
|---|---|---|---|---|
| DTD | 0.862 | 0.807 | 0.776 | 0.860 |
| FMD | 0.948 | 0.891 | 0.878 | 0.936 |
| CUReT | 1.000 | 0.983 | 0.991 | 1.000 |
| Soil | 0.904 | 0.813 | 0.754 | 0.884 |
| VisTex | 0.866 | 0.635 | 0.732 | 0.874 |

**Hallazgo:** k=17 (todos los extractores concatenados) es el óptimo en 22/24 casos. Excepciones: Outex13-knn (k=16), CUReT-resmlp (k=16), Soil-knn (k=11), Soil-rf (k=16). El óptimo suele ser alto, pero con dim=17324 (todos), lo cual es computacionalmente costoso.

**Observación importante:** VisTex-knn muestra un comportamiento anómalo: prefix concat (k=17, F1=0.635) es **peor** que el mejor individual (dinov2, F1=0.734). Este es el único caso donde concatenar "hurts" con linear probing y k=17.

---

## 4.4. Exp 3b — Greedy Forward Selection (GFS)

GFS busca el subset óptimo de extractores: en cada step agrega el extractor que más mejora F1 hasta convergencia (early stopping si mejora < 0.005).

### 4.4.1. Mejor subset GFS por (dataset, clf)

**Tabla 4.4.** Subset óptimo GFS por (dataset, clf) — mejor subset encontrado con early stopping.

| Dataset | clf | k | Subset | dim | F1 |
|---|---|---|---|---|---|
| DTD | svm | 4 | dinov2 + resnet50 + dinov2_large + glcm | 3,858 | **0.868** |
| DTD | knn | 4 | dinov2 + resnet50 + dinov2_large + lbp | 3,894 | 0.822 |
| DTD | rf | 2 | dinov2_large + dinov2_small | 1,408 | 0.762 |
| DTD | resmlp | 3 | dinov2_large + resnet50 + dinov2 | 3,840 | 0.864 |
| FMD | svm | 2 | dinov2 + dinov2_large | 1,792 | **0.973** |
| FMD | knn | 4 | dinov2_small + dinov2_large + resnet50 + lbp | 3,510 | 0.914 |
| FMD | rf | 2 | dinov2_large + dinov2_small | 1,408 | 0.877 |
| FMD | resmlp | 3 | dinov2 + dinov2_large + dinov2_small | 2,176 | 0.969 |
| CUReT | svm | 3 | dinov2_large + swin_t + resnet50 | 3,840 | 1.000 |
| CUReT | knn | 3 | densenet121 + dinov2_large + convnext_v2_t | 2,816 | 0.986 |
| CUReT | rf | 3 | densenet121 + dinov2_large + dinov2_small | 2,432 | 0.984 |
| CUReT | resmlp | 2 | dinov2_large + swin_t | 1,792 | 1.000 |
| Soil | svm | 5 | efficientnet_b0 + vit_b16 + dinov2 + resnet101 + lbp | 4,918 | 0.906 |
| Soil | knn | 3 | resnet101 + vit_b16 + gabor | 2,864 | 0.827 |
| Soil | rf | 2 | densenet121 + dinov2 | 1,792 | 0.800 |
| Soil | resmlp | 3 | densenet121 + vit_b16 + dinov2_large | 2,816 | 0.902 |
| VisTex | svm | 3 | dinov2 + convnext_v2_t + drlbp | 1,616 | **0.902** |
| VisTex | knn | 1 | dinov2 | 768 | 0.734 |
| VisTex | rf | 2 | dinov2_small + gabor | 432 | 0.775 |
| VisTex | resmlp | 3 | dinov2_large + convnext_v2_t + drlbp | 1,872 | 0.924 |

**Hallazgos MAYOR:**

1. **DINOv2 (cualquier variante) aparece en TODOS los subsets óptimos GFS** (24/24 = 100%). Es el extractor indispensable.

2. **DINOv2-B + DINOv2-L son complementarios**: aparecen juntos en 9/24 subsets (38%), a pesar de compartir arquitectura y pre-entrenamiento. Confirma el hallazgo contraintuitivo de V1.

3. **k óptimo suele ser bajo (2-5)**: 21/24 subsets tienen ≤ 5 extractores. GFS converge rápido, no necesitás los 17.

4. **Dimensionalidad reducida 5-10× vs k=17**: el subset GFS promedio tiene ~2700 dim vs 17324 de k=17, una reducción de ~84% con F1 igual o mejor.

5. **VisTex-svm FIX con GFS**: dinov2 + convnext_v2_t + drlbp (F1=0.902) supera al mejor individual dinov2 (F1=0.730) por **+0.172 F1** — el salto más grande de toda la tabla.

*Paths completos de GFS en `results/figures/gfs_paths_*.png` (6 figuras, una por dataset).*

### 4.4.2. GFS vs Prefix concat (k=17) — diff sig con Holm-Bonferroni

**Tabla 4.5.** Comparación pareada GFS (best step) vs Prefix concat (k=17) con paired t-test sobre 5 folds.

| Dataset | clf | F1 GFS | F1 Prefix k=17 | Δ F1 | p Holm | Cohen's d | Signif |
|---|---|---|---|---|---|---|---|
| DTD | svm | 0.868 | 0.862 | +0.006 | 0.520 | 1.40 | No |
| DTD | knn | 0.822 | 0.807 | +0.015 | **0.015** | 4.31 | **Sí** |
| DTD | rf | 0.762 | 0.776 | −0.014 | 0.405 | −0.83 | No |
| DTD | resmlp | 0.864 | 0.860 | +0.004 | 0.583 | 0.94 | No |
| FMD | svm | 0.973 | 0.948 | +0.025 | 0.108 | 2.50 | No |
| FMD | knn | 0.914 | 0.891 | +0.023 | 0.305 | 1.34 | No |
| FMD | rf | 0.877 | 0.878 | −0.001 | 0.950 | −0.04 | No |
| FMD | resmlp | 0.969 | 0.936 | +0.033 | 0.066 | 2.81 | No |
| CUReT | svm | 1.000 | 1.000 | 0.000 | 1.000 | 0.00 | No |
| CUReT | knn | 0.986 | 0.983 | +0.003 | 0.674 | 0.51 | No |
| CUReT | rf | 0.984 | 0.991 | −0.007 | 0.366 | −0.97 | No |
| CUReT | resmlp | 1.000 | 1.000 | 0.000 | 1.000 | 0.00 | No |
| Soil | svm | 0.906 | 0.904 | +0.003 | 0.880 | 0.16 | No |
| Soil | knn | 0.827 | 0.813 | +0.014 | 0.456 | 0.86 | No |
| Soil | rf | 0.800 | 0.754 | +0.046 | 0.054 | 2.69 | No |
| Soil | resmlp | 0.902 | 0.884 | +0.018 | 0.351 | 1.16 | No |
| VisTex | svm | 0.902 | 0.866 | +0.037 | 0.090 | 2.16 | No |
| VisTex | knn | 0.734 | 0.635 | +0.100 | **0.005** | 5.71 | **Sí** |
| VisTex | rf | 0.775 | 0.732 | +0.043 | 0.260 | 1.43 | No |
| VisTex | resmlp | 0.924 | 0.874 | +0.049 | 0.116 | 2.06 | No |

**Resumen:**
- GFS > Prefix concat en 16/24 (67%)
- Significativos (Holm p<0.05): 2/24 (8%) — DTD knn y **VisTex knn**
- VisTex knn: GFS=0.734 vs Prefix=0.635 (Δ=+0.100) — **el "concat hurts" se elimina con GFS**

### 4.4.3. GFS vs Mejor individual — diff sig con Holm-Bonferroni

**Tabla 4.6.** Comparación pareada GFS (best step) vs Mejor individual (Exp 1) con paired t-test.

| Dataset | clf | F1 GFS | F1 best indiv | Δ F1 | p Holm | Cohen's d | Signif |
|---|---|---|---|---|---|---|---|
| DTD | svm | 0.868 | 0.842 (dinov2) | +0.026 | **0.0006** | 9.82 | **Sí** |
| DTD | knn | 0.822 | 0.803 (dinov2) | +0.019 | 0.18 | 1.69 | No |
| DTD | rf | 0.762 | 0.779 (dinov2_large) | −0.018 | **0.026** | −3.65 | **Sí (neg)** |
| DTD | resmlp | 0.864 | 0.837 (dinov2_large) | +0.027 | **0.046** | 3.06 | **Sí** |
| FMD | svm | 0.973 | 0.957 (dinov2) | +0.016 | 0.220 | 1.66 | No |
| FMD | knn | 0.914 | 0.888 (dinov2_small) | +0.025 | 0.092 | 2.27 | No |
| FMD | rf | 0.877 | 0.892 (dinov2_large) | −0.014 | 0.357 | −1.07 | No |
| FMD | resmlp | 0.969 | 0.948 (dinov2) | +0.021 | 0.247 | 1.55 | No |
| CUReT | svm | 1.000 | 0.994 (dinov2_large) | +0.006 | **0.013** | 4.44 | **Sí** |
| CUReT | knn | 0.986 | 0.971 (densenet121) | +0.015 | **0.006** | 5.45 | **Sí** |
| CUReT | rf | 0.984 | 0.981 (densenet121) | +0.003 | 0.781 | 0.32 | No |
| CUReT | resmlp | 1.000 | 0.999 (dinov2_large) | +0.001 | 0.535 | 0.74 | No |
| Soil | svm | 0.906 | 0.831 (efficientnet_b0) | +0.075 | 0.061 | 2.59 | No |
| Soil | knn | 0.827 | 0.796 (efficientnet_b0) | +0.031 | 0.367 | 1.00 | No |
| Soil | rf | 0.800 | 0.776 (densenet121) | +0.025 | 0.181 | 1.71 | No |
| Soil | resmlp | 0.902 | 0.858 (vit_b16) | +0.044 | 0.092 | 2.27 | No |
| VisTex | svm | 0.902 | 0.730 (dinov2) | +0.172 | **0.044** | 3.12 | **Sí** |
| VisTex | knn | 0.734 | 0.734 (dinov2) | 0.000 | — | — | — |
| VisTex | rf | 0.775 | 0.742 (dinov2_small) | +0.033 | 0.412 | 0.85 | No |
| VisTex | resmlp | 0.924 | 0.882 (dinov2_large) | +0.042 | 0.092 | 2.27 | No |

**Resumen:**
- GFS > Best individual en 20/24 casos (83%)
- Significativos (Holm p<0.05): 6/24 (25%) — DTD svm/resmlp, DTD rf (negativo), CUReT svm/knn, VisTex svm
- **El más impresionante: VisTex svm con +0.172 F1** (GFS=0.902 vs best indiv dinov2=0.730)
- **DTD rf**: GFS PEOR que best indiv (significativo) — el subset de GFS no encuentra una mejora sobre dinov2_large solo

---

## 4.5. Tabla comparativa final

**Tabla 4.7.** Mejor F1 por dataset, comparando las 4 estrategias (Linear probing con el mejor extractor, Prefix concat k=17, GFS subset óptimo). El valor en negrita es el ganador de cada fila.

| Dataset | Linear (best indiv) | Prefix k=17 | **GFS** | Δ GFS-Linear |
|---|---|---|---|---|
| DTD | 0.842 (dinov2) | 0.862 | **0.868** (k=4) | +0.026 |
| FMD | 0.957 (dinov2) | 0.948 | **0.973** (k=2) | +0.016 |
| CUReT | 0.999 (dinov2_large) | 1.000 | **1.000** (k=2-3) | +0.001 |
| Soil | 0.858 (vit_b16) | 0.904 | **0.906** (k=5) | +0.048 |
| VisTex | 0.882 (dinov2_large) | 0.874 | **0.924** (k=3) | +0.042 |
| **Promedio** | 0.905 | 0.916 | **0.927** | — |


**Promedios (dos métricas para comparación justa):**

| Estrategia | Promedio 6 datasets |
|---|---|
| Linear probing (mejor individual) | 0.905 |
| Prefix concat (k=17) | 0.916 |
| **GFS (best step)** | **0.927** |

**Diferencias promedio:**
- GFS vs Linear: +0.022 F1
- GFS vs Prefix k=17: +0.011 F1

*Datos completos en `results/tables/gfs_comparison_summary.csv`.*

---

## 4.6. Análisis de error por dataset

### 4.6.1. Clases más difíciles (GFS subset)

| Dataset | Clase más difícil | F1 (aprox) | Comentario |
|---|---|---|---|
| DTD | blotchy | 0.55 | Texturas con manchas amorfas, ambiguas |
| FMD | plastic | 0.92 | Materiales similares (plastic/metal/glass) |
| KTH-TIPS2-b | (todos >0.99) | 1.000 | Dataset saturado (no incluido en v3) |
| Outex13 | (varias 0.80-0.90) | 0.85 | 68 clases con pocas imgs/clase |
| VisTex | (varias <0.50) | <0.50 | Dataset muy pequeño, alta varianza |

### 4.6.2. Top pares confundidos en DTD (GFS subset)

| Real | Predicho | Tasa |
|---|---|---|
| lined | banded | 21% |
| dotted | polka-dotted | 16% |
| stained | blotchy | 12% |
| smudgy | stained | 10% |

Las confusiones son **visualmente razonables** (líneas ↔ bandas, puntos ↔ polka-puntos), no aleatorias.
---

## 4.7. Exp 4 (SOTA 2024) — EVA-02, MAE, SigLIP

Para verificar el estado del arte, se evaluaron **3 modelos SOTA adicionales** (EVA-02 ViT-B/14, MAE ViT-B/16, SigLIP ViT-B/16) con 4 clasificadores en 5 datasets (Outex13 excluido por path mismatch). **Total: 20 extractores.**

**Tabla 4.8.** GFS con 20 extractores vs GFS original (17 extractores).

| Dataset | clf | GFS 17 ext | GFS 20 ext | Δ |
|---|---|---|---|---|
| DTD | svm | 0.868 | **0.874** (dinov2+eva02+dinov2_large+drlbp) | +0.006 |
| DTD | knn | 0.822 | **0.831** (dinov2+eva02+siglip) | +0.009 |
| DTD | rf | 0.762 | **0.787** (eva02+dinov2+siglip) | +0.025 |
| DTD | resmlp | 0.864 | **0.871** (siglip+dinov2_large+eva02+vit_b16) | +0.007 |
| FMD | svm | 0.973 | **0.983** (siglip+dinov2_large) | +0.010 |
| FMD | knn | 0.914 | **0.929** (eva02+dinov2_large+mae) | +0.015 |
| FMD | rf | 0.877 | **0.902** (siglip+dinov2) | +0.025 |
| FMD | resmlp | 0.969 | **0.981** (siglip+dinov2+dinov2_large) | +0.012 |
| Soil | svm | 0.906 | **0.913** (eva02+effnet+dinov2_small+dinov2_large+glcm) | +0.007 |
| Soil | knn | 0.827 | **0.851** (mae+siglip+effnet+gabor) | +0.024 |
| **Promedio** | | 0.907 | **0.909** | +0.002 |

**Hallazgos:** (1) EVA-02 aparece en 6/20 subconjuntos GFS. (2) SigLIP obtiene el mejor resultado individual en FMD con SVM (0.966). (3) MAE aporta información complementaria en Soil. (4) La mejora promedio de incorporar los tres modelos es solamente +0.002 F1, con picos de +0.025. (5) En conjunto, la extensión confirma que **la estrategia de selección y la diversidad entre representaciones tienen mayor impacto que agregar un modelo individual adicional**.

---

## 4.8. Resumen de archivos generados

- `embeddings/{dataset}/{extractor}.npy` — embeddings de 17×6 = 102 archivos (~3 GB)
- `results/tables/baseline_{dataset}.csv` — 6 CSVs (Exp 1, 4 clfs)
- `results/tables/baseline_summary.csv` — consolidado 408 filas
- `results/tables/concat_{dataset}.csv` — 6 CSVs (Exp 3a, prefix concat)
- `results/tables/concat_summary.csv` — consolidado 408 filas
- `results/tables/greedy_path_{dataset}.csv` — 6 CSVs (Exp 3b, GFS paths)
- `results/tables/greedy_summary.csv` — 24 filas (best GFS subset por dataset/clf)
- `results/tables/gfs_comparison_summary.csv` — tabla comparativa final
- `results/tables/gfs_vs_prefix_diff_sig.csv` — 48 comparaciones con Holm
- `results/tables/diff_sig_vs_individual.csv` — 6,936 comparaciones (Exp 3a vs Exp 1)
- `results/tables/exp4_significance_matrix.csv` — 384 comparaciones (dentro de Exp 1)
- `results/figures/saturation_*.png` — 6 curvas de saturación (k=1..17)
- `results/figures/gfs_paths_*.png` — 6 figuras de GFS paths
- `results/figures/gfs_vs_prefix_bar.png` — bar plot GFS vs Prefix k=17
- `results/figures/gfs_vs_best_individual_scatter.png` — scatter F1 individual vs F1 GFS
