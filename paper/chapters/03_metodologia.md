# Capítulo 3 — Metodología

## 3.1. Resumen del pipeline experimental

El pipeline experimental se compone de tres etapas secuenciales:

1. **Extracción de embeddings** (Cap. 3.3): para cada uno de los 17 extractores, se procesan los 6 datasets y se cachean los embeddings en disco (`embeddings/{dataset}/{extractor}.npy`).
2. **Baseline por extractor** (Cap. 3.4): cada embedding se evalúa independientemente con 2 clasificadores principales (SVM lineal, KNN) en 5-fold CV.
3. **Concatenación y selección** (Cap. 3.5): los embeddings se concatenan en orden canónico y se evalúan con GFS para encontrar el subconjunto óptimo.

Las implementaciones completas están en `src/` y los resultados en `results/`.

## 3.2. Conjuntos de datos

Se utilizan **6 datasets públicos de texturas** para asegurar reproducibilidad y comparabilidad con la literatura previa. Los datasets médicos que formaban parte de la versión V1 del manuscrito fueron removidos por directriz del tutor, dado que la presente tesis se enfoca en texturas naturales y controladas.

### 3.2.1. Datasets de texturas (6 datasets públicos)

| Dataset | Clases | Imágenes | Resolución | Fuente | Tipo |
|---|---|---|---|---|---|
| **DTD** (Cimpoi et al. 2014) | 47 | 5,640 | ~640×640 | Web ("in the wild") | Texturas naturales |
| **FMD** (Sharan et al. 2013) | 10 | 1,000 | variable | Flickr | Materiales |
| **Outex13** (Ojala et al. 2002) | 68 | 1,360 | 128×128 (bmp) | Benchmark estándar | Texturas controladas |
| **KTH-TIPS2-b** (Mallikarjuna et al. 2005) | 11 | 3,564 | 200×200 | KTH (4 samples/clase) | Texturas controladas multi-scale |
| **GTOS-Mobile** (Xue et al. 2017) | 31 | 4,991 (subsample 5K) | 256×256 | Mobile phone | Outdoor scenes |
| **VisTex** (MIT) | 19 | 167 | 512×512 | MIT VisTex Reference | Texturas naturales |

**DTD** (Describable Textures Dataset) es el benchmark estándar de texturas naturales desde 2014. Las imágenes se recolectaron de la web y se categorizaron en 47 clases describibles (banded, blotchy, braided, etc.). Aproximadamente 120 imágenes por clase. Es el dataset más desafiante de la evaluación (F1 máximo ≈ 0.87 incluso con GFS).

**FMD** (Flickr Material Dataset) contiene imágenes de materiales (fabric, foliage, glass, leather, metal, paper, plastic, stone, water, wood) recolectadas de Flickr. Tiene 100 imágenes por clase, balanceado. Es más desafiante que DTD en complejidad semántica pero más fácil en variabilidad visual.

**Outex13** (Outex Texture Benchmark, suite 13) es un benchmark estándar de texturas controladas con 68 clases y aproximadamente 20 imágenes por clase (1,360 en total). Las imágenes son capturas de laboratorio en condiciones controladas (iluminación, escala, rotación). Se incluye como benchmark discriminante por su alto número de clases y bajo número de imágenes por clase.

**KTH-TIPS2-b** (KTH Textures under varying Illumination, Pose and Scale, 2nd version, variante b) es un dataset capturado en laboratorio con condiciones controladas: 11 materiales, 4 muestras físicas por material, 9 escalas, 3 iluminaciones, 3 poses. La variante "b" incluye las 4 muestras por material. Las imágenes son 200×200 píxeles. Está saturado (F1 ≈ 1.0 con todos los métodos serios).

**GTOS-Mobile** (Google Landmarks / Terrain Outdoor Scenes) es un dataset de **outdoor scenes** (grass, asphalt, dirt, etc.), originalmente para reconocimiento de terreno desde dispositivos móviles. Lo incluimos como **test de transferibilidad a escenas del mundo real**, no como benchmark de texturas en sentido estricto. Se usó un subsample estratificado de 5,000 imágenes (160/clase) para mantener tiempos de cómputo manejables.

**VisTex** (MIT VisTex Reference) es el dataset más pequeño (167 imágenes, 19 clases) — útil para stress-testing de los métodos en data-scarce scenarios. Clases pequeñas (2-3 imgs) fueron excluidas de los análisis de 5-fold para evitar folds degenerados.

**Total:** ≈17,000 imágenes, ~3 GB en disco.

### 3.2.2. Estructura de los directorios

Todos los datasets se almacenan en `data/<DATASET>/` con la siguiente estructura:

```
data/
|-- DTD/dtd/images/<clase>/<imagen>.jpg
|-- FMD/{train,test}/<clase>/<imagen>.jpg
|-- Outex13/Outex-TC-00013/images/<imagen>.bmp
|-- KTH-TIPS2/KTH-TIPS2-b/<clase>/sample_<a-d>/<imagen>.png
|-- GTOS-Mobile/<clase>/<imagen>.jpg
\-- VisTex/<clase>/<imagen>.ppm
```

## 3.3. Extractores de características (17 en total)

### 3.3.1. Descriptores clásicos (5)

Implementados con scikit-image 0.26. Imágenes convertidas a grayscale y redimensionadas a 256×256 (128×128 para HOG).

| Descriptor | Configuración | Dim |
|---|---|---|
| **LBP multi-escala** | scales=[(8,1), (16,2), (24,3)], method='uniform' | 54 |
| **GLCM** | distances=[1,2,3], angles=[0,45,90,135], 6 props | 18 |
| **Gabor** | 4 frecuencias × 6 orientaciones, mean+std | 48 |
| **HOG** | 16×16 cells, 2×2 blocks, 9 orientations | 1,764 |
| **DRLBP** | P=8, R=1, 8 rotaciones, method='ror' | 80 |

**LBP (Local Binary Patterns, Ojala et al. 2002):** se computan en 3 escalas para capturar micro-texturas a diferentes resoluciones. Cada escala produce un histograma de 10 bins (uniform) o 18 bins (P=16) o 26 bins (P=24), totalizando 54 dimensiones.

**GLCM (Gray-Level Co-occurrence Matrix, Haralick 1979)** \cite{haralick1979glcm}: se computa la matriz de co-ocurrencia para 3 distancias y 4 ángulos. Para cada matriz, se extraen 6 propiedades de Haralick (contrast, dissimilarity, homogeneity, energy, correlation, ASM). Se promedia sobre los 4 ángulos, dando 3×6 = 18 dimensiones.

**Gabor:** banco de filtros de Gabor con 4 frecuencias (0.1, 0.2, 0.4, 0.8 ciclos/pixel) y 6 orientaciones (0, 30, 60, 90, 120, 150 grados). Para cada filtro, se calcula la media y la desviación estándar de la respuesta, dando 4×6×2 = 48 dimensiones.

**HOG (Histogram of Oriented Gradients, Dalal & Triggs 2005)** \cite{dalal2005hog}: se computa sobre imágenes 128×128 con celdas de 16×16 y bloques de 2×2. Con 9 orientaciones, cada bloque tiene 2×2×9 = 36 features. Con 7×7 bloques (para 128/16=8 celdas, 8-1=7 bloques), se obtienen 7×7×36 = 1,764 dimensiones.

**DRLBP (Dominant Rotated LBP, simplificado)** \cite{mehta2011drlbp}: implementación simplificada que aplica LBP rotation-invariant (`method='ror'`) a 8 rotaciones de la imagen y concatena los histogramas. La implementación original de Mehta & Egiazarian (2011) usa técnicas más sofisticadas; la nuestra es una aproximación. Para cada rotación, se obtiene un histograma de 10 bins (P=8 ror), totalizando 8×10 = 80 dimensiones.

### 3.3.2. CNNs (6)

Implementados con timm 1.0.27, preentrenados en ImageNet, con linear probing.

| CNN | Variante timm | Dim |
|---|---|---|
| **VGG16** | `vgg16.tv_in1k` | 4,096 |
| **ResNet-50** | `resnet50.a1_in1k` | 2,048 |
| **ResNet-101** | `resnet101.a1_in1k` | 2,048 |
| **DenseNet-121** | `densenet121.ra_in1k` | 1,024 |
| **EfficientNet-B0** | `efficientnet_b0.ra_in1k` | 1,280 |
| **ConvNeXt V2-T** | `convnextv2_tiny.fcmae_ft_in22k_in1k` | 768 |

**VGG16 (Simonyan & Zisserman 2015):** arquitectura clásica de 16 capas con bloques convolucionales pequeños (3×3). Preentrenada en ImageNet1k. Mayor dimensionalidad de embedding (4,096d) que las alternativas modernas.

**ResNet-50 (He et al. 2016):** arquitectura clásica de 50 capas con conexiones residuales. Preentrenada con receta "a1" (variante mejorada del recipe original).

**ResNet-101 (He et al. 2016):** versión más profunda de ResNet, con 101 capas. Misma dimensionalidad de embedding que ResNet-50 (2,048d) pero mayor capacidad representacional.

**DenseNet-121 (Huang et al. 2017):** arquitectura con conexiones densas entre capas (cada capa recibe input de todas las anteriores). Embedding de 1,024d, compacto y eficiente.

**EfficientNet-B0 (Tan & Le 2019):** arquitectura optimizada por compound scaling (depth + width + resolution). Preentrenada con recipe "ra" (ResNet-style augmentation).

**ConvNeXt V2-T (Woo et al. 2023):** arquitectura ConvNet modernizada, preentrenada con FCMAE (Fully Convolutional Masked Autoencoder). Integra convoluciones con self-supervisión, intentando cerrar la brecha con ViTs.

**Pre-procesamiento para todos los CNN:** resize a 224×224, normalización ImageNet (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]).

### 3.3.3. Vision Transformers (3)

| ViT | Variante (HuggingFace) | Dim |
|---|---|---|
| **ViT-B/16** | `google/vit-base-patch16-224` | 768 |
| **Swin-T** | `microsoft/swin-tiny-patch4-window7-224` | 768 |
| **DeiT-S** | `facebook/deit-small-patch16-224` | 384 |

**ViT-B/16 (Dosovitskiy et al. 2021):** Vision Transformer base con patches de 16×16, 12 bloques transformer, 768 dim. Preentrenado en ImageNet1k supervisado.

**Swin-T (Liu et al. 2021):** Swin Transformer tiny con ventanas jerárquicas. Preentrenado en ImageNet1k. La arquitectura usa shifted windows que permiten atención local eficiente.

**DeiT-S (Touvron et al. 2021):** Data-efficient Image Transformer small, entrenado con destilación de un modelo teacher (RegNet). 384 dim (más pequeño que ViT-B/16).

### 3.3.4. Self-supervised — DINOv2 (3)

| Modelo | Variante (timm) | Dim | Input |
|---|---|---|---|
| **DINOv2-S** | `vit_small_patch14_dinov2.lvd142m` | 384 | 518×518 |
| **DINOv2-B** | `vit_base_patch14_dinov2.lvd142m` | 768 | 518×518 |
| **DINOv2-L** | `vit_large_patch14_dinov2.lvd142m` | 1,024 | 518×518 |

**DINOv2 (Oquab et al. 2024):** familia de Vision Transformers preentrenados con self-supervisión sobre LVD-142M (142 millones de imágenes). Usa un recipe combinado de DINO + iBOT. **No usa linear probing tradicional** sino features directamente de la cabeza [CLS] del encoder.

**DINOv2-S:** variante pequeña (ViT-S/14), 22M parámetros, embedding 384d. Más rápido de extraer y competitivo en texturas controladas (CUReT, KTH-TIPS2-b).

**DINOv2-B:** variante base (ViT-B/14), 86M parámetros, embedding 768d. **Es el ganador en 4/6 datasets de texturas** evaluados (DTD, FMD, KTH-TIPS2-b, VisTex).

**DINOv2-L:** variante large (ViT-L/14), 304M parámetros, embedding 1,024d. Mayor capacidad representacional. Complementa a DINOv2-B (ver Cap. 5.2).

**Pre-procesamiento:** resize a 518×518 (input nativo de DINOv2), normalización ImageNet. La extracción es más lenta (~5 img/s vs 100+ img/s de los ViT) por el input grande. La variante 224×224 (no probada en esta tesis) sería ~5× más rápida pero podría perder features de alta frecuencia; los autores de DINOv2 recomiendan 518×518 para máxima calidad.

### 3.3.5. Implementación

Todos los extractores están implementados en `src/01_extract_features.py`. La función principal `get_extractor(name, device)` retorna un objeto extractor con método `.extract(image_paths) → np.ndarray`. Los embeddings se guardan como `embeddings/{dataset}/{extractor}.npy` y las etiquetas como `embeddings/{dataset}/{extractor}_labels.npy`.

## 3.4. Clasificadores

### 3.4.1. SVM lineal (clasificador principal)

```python
SVC(kernel="linear", C=1.0, random_state=42)
```

- **Kernel:** lineal (sin parámetros gamma).
- **C:** 1.0 (regularización estándar).
- **Justificación:** SVM lineal es robusto a altas dimensiones y produce excelentes resultados en embeddings de redes preentrenadas (Radford et al. 2021).

### 3.4.2. KNN

```python
KNeighborsClassifier(n_neighbors=5, weights="distance")
```

### 3.4.3. Random Forest

```python
RandomForestClassifier(n_estimators=100, max_depth=None, random_state=42, n_jobs=1)
```

- En este trabajo se utiliza `n_estimators=100` (en lugar del valor más común de 300) para mantener el tiempo de cómputo manejable con embeddings de alta dimensión. La diferencia de F1 entre 100 y 300 árboles es < 0.005 en todos los datasets evaluados (validado en piloto).

### 3.4.4. ResMLP (Residual Multi-Layer Perceptron)

```python
ResMLPClassifier(hidden_dim=256, n_blocks=3, dropout=0.1,
                  max_epochs=100, patience=10, batch_size=256)
```

- Implementación propia estilo Touvron et al. 2021 (ver `src/resmlp_classifier.py`).
- Arquitectura: Proyección inicial (Linear + LayerNorm + GELU) + 3 bloques residuales [Linear-GELU-Dropout] + cabeza de clasificación.
- Optimizador: AdamW con `lr=1e-3`, `weight_decay=1e-4`.
- Early stopping con `patience=10` épocas.

### 3.4.5. Por qué 4 clasificadores y no más

Esta tesis evalúa **4 clasificadores** (SVM lineal, KNN, RF, ResMLP) en lugar de los 5 que se probaron en la versión V1 del manuscrito (que incluía además `MLPClassifier` de scikit-learn). La decisión se justifica porque:

1. **SVM, KNN, RF** cubren el espectro clásico (lineal, instance-based, ensemble).
2. **ResMLP** es un MLP-style moderno con normalización y conexiones residuales, comparable a las cabezas de clasificación de los modelos pre-entrenados.
3. **MLP-256 de sklearn** fue excluido por tener performance similar a ResMLP (≤ 0.01 F1 de diferencia) pero con implementación menos robusta (sensibilidad a la inicialización, sin early stopping por defecto).

La comparación entre los 4 clasificadores en la Sección 4.5 muestra que **SVM lineal es consistentemente competitivo** (gana en 16/24 casos), seguido de ResMLP (gana en 6/24). KNN y RF pierden en la mayoría pero ganan en configuraciones específicas (KNN con embeddings pequeños, RF en CUReT y Soil).

## 3.5. Protocolo de evaluación

### 3.5.1. L2-normalización

**CRÍTICO:** antes de cualquier clasificación (SVM, MLP, KNN, RF), cada embedding se **L2-normaliza per-imagen**:

$$x_i^{norm} = \frac{x_i}{\|x_i\|_2}$$

Esta normalización es **esencial** porque los embeddings tienen escalas muy diferentes (LBP ≈ 0.7, GLCM ≈ 715). Sin normalización, los embeddings de alta magnitud dominarían la función de decisión.

**Cuándo se aplica:** en cada fold, **separadamente** para train y test, **dentro** del bucle de cross-validation. Esto evita data leakage.

### 3.5.2. K-fold Stratified Cross-Validation

- **K = 5** (5 folds)
- **Estratificado** por clase (preserva la distribución de clases en cada fold)
- **Random state = 42** (reproducibilidad)
- **Métricas:** macro-F1 (principal), accuracy (secundaria), matriz de confusión (análisis cualitativo)

```python
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

### 3.5.3. Pipeline de evaluación (5-fold)

```
for fold in 1..5:
    1. Train idx, Test idx = skf.split(X, y)
    2. X_train = concatenate([L2_norm(e[train_idx]) for e in embeddings_list])
    3. X_test = concatenate([L2_norm(e[test_idx]) for e in embeddings_list])
    4. clf.fit(X_train, y_train)
    5. y_pred = clf.predict(X_test)
    6. f1 = f1_score(y_test, y_pred, average='macro')
    7. Save per-fold f1
```

## 3.6. Greedy Forward Selection (GFS)

### 3.6.1. Algoritmo

```
Input: lista de N extractores E, etiquetas y, clasificador clf, max_steps=N
Output: subset optimo S subset E

S = empty
remaining = E
best_f1 = 0
history = []

for step in 1..max_steps:
    best_cand = None
    best_f1_cand = -inf

    # Evaluar todos los candidatos restantes (en paralelo)
    parallel:
        for cand in remaining:
            S_cand = S union {cand}
            emb_list_cand = [e for e in S_cand]
            f1_cand = cv_5fold(emb_list_cand, y, clf)
            if f1_cand > best_f1_cand:
                best_f1_cand = f1_cand
                best_cand = cand

    S = S union {best_cand}
    remaining = remaining - {best_cand}
    history.append({step, best_cand, f1_cand, ...})

    if step > 1 and (f1_cand - best_f1) < 1e-4:
        break  # Convergencia

    best_f1 = f1_cand

return S, history
```

### 3.6.2. Orden canónico (no afecta a GFS, sí al prefix concat)

Para los experimentos de prefix concat, el orden canónico es:

```
clásicos → CNN → ViT
= [LBP, GLCM, Gabor, HOG, DRLBP,
   ResNet-50, ConvNeXt V2-T, EfficientNet-B0,
   ViT-B/16, Swin-T, DeiT-S, DINOv2, DINOv2-large]
```

La narrativa es: de **simple a complejo**, de **handcrafted a learned**, de **supervisado a self-supervised**.

### 3.6.3. Implementación

GFS implementado en `src/run_gfs_fast.py`. Para acelerar la búsqueda en este trabajo se usa una **estrategia de screening en 2 fases**:

1. **Fase 1 (screening rápido):** para cada candidato restante, se evalúa con **1 fold** (el primero de los 5 del CV estratificado) y se ordena por F1.
2. **Fase 2 (verificación):** solo los **top-3 candidatos** del screening se evalúan con los **5 folds completos**, y se elige el ganador.

Esta heurística reduce el costo de cada step en ~2.5× con un impacto mínimo en la calidad del subset encontrado (validado: la diferencia entre GFS con screening y GFS exhaustivo es < 0.002 F1 en promedio). Adicionalmente, se aplica **early stopping**: si la mejora de F1 en un step es menor que `threshold=0.005`, GFS termina. Esto permite converger en 2-5 steps en la mayoría de los casos (vs. hasta 17 sin early stopping).

## 3.7. Análisis estadístico

Para validar la significancia de las mejoras, se realizó un **paired t-test** sobre los 5 folds (mismo split para todas las estrategias comparadas). Se reportan p-values y Cohen's d (effect size). Ver `src/11_statistical_tests.py`.

Implementación:
```python
from scipy import stats
t_stat, p_val = stats.ttest_rel(f1_strategy_A, f1_strategy_B)
d = (np.array(f1_A) - np.array(f1_B)).mean() / (np.array(f1_A) - np.array(f1_B)).std()
```

## 3.8. Recursos computacionales

- **Hardware:** 1× NVIDIA RTX 4060 (8 GB VRAM), 8-core CPU
- **Software:** Python 3.14, PyTorch 2.12, transformers 5.9, timm 1.0.27, scikit-learn 1.8, scikit-image 0.26, pandas 3.0
- **Reproducibilidad:** `random_state=42` en todos los componentes estocásticos (CV, modelos)
- **Tiempo total de extracción:** ~6 horas (mayormente dominado por DINOv2 y DINOv2-large a 518×518)
- **Tiempo total de evaluación (Exp 1, 3, 4 + GFS):** ~6 horas (1,200+ experimentos)
  - Exp 1 (individual, 4 clfs × 17 ext × 6 ds): ~1.5 h
  - Exp 3 (prefix concat k=1..17, 4 clfs × 6 ds): ~3.5 h
  - Exp 4 (diff sig sobre Exp 1): < 1 min
  - GFS (4 clfs × 6 ds): ~75 min
- **Storage total:** ~15 GB de embeddings cacheados

## 3.9. Limitaciones del pipeline

1. **Sin nested CV** (parcialmente resuelto en Round 3): el GFS actual puede sobreajustar al split particular. Una versión con outer/inner CV sería más rigurosa.
2. **Sin fine-tuning** de los modelos preentrenados: se usa linear probing exclusivamente. Fine-tuning podría mejorar resultados (explorado en Sección 5.11.2, fue negativo en datasets pequeños).
3. **Hiperparámetros fijos del clasificador** (C=1.0, n_neighbors=5, n_estimators=300): un grid search más exhaustivo podría mejorar marginalmente.
4. **Orden canónico fijo** en prefix concat: un análisis de sensibilidad al orden podría revelar que otros órdenes son equivalentes o mejores.
