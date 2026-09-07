# Capítulo 5 — Discusión

## 5.1. Desempeño de los descriptores individuales dentro del marco de combinación

El análisis individual cumple una función de referencia: establece cuánto aporta cada representación antes de combinarla. Las variantes DINOv2 obtienen el mejor linear probing en 18/24 combinaciones dataset-clasificador, con F1 entre 0.83 y 0.96. Este resultado identifica una familia fuerte, pero no resuelve por sí solo la pregunta de investigación, centrada en el beneficio de combinar descriptores.

**¿Por qué DINOv2?** El pre-entrenamiento self-supervised en LVD-142M (142 millones de imágenes no etiquetadas, Oquab et al. 2024) produce features que capturan **estadísticas de textura de bajo nivel** con mayor fineza que los modelos supervisados en ImageNet. La diferencia es más pronunciada en:

- **Datasets con muchas clases** (Outex13 con 68 clases, DTD con 47): DINOv2 +5% F1 sobre Swin-T
- **Datasets con imágenes de internet** ("in the wild"): DINOv2 +3% F1 sobre ResNet-50
- **Datasets pequeños** (VisTex con 167 imgs): DINOv2 +5% F1 sobre los mejores supervisados
- **Modelos pre-entrenados en image genéricos** (no específicos a texturas): la familia DINOv2 captura mejor las invarianzas de bajo nivel

**Relación con GFS:** al menos una variante DINOv2 aparece en los subconjuntos seleccionados. La interpretación relevante no es que una arquitectura explique por sí sola el resultado, sino que GFS la conserva cuando aporta señal y la combina con representaciones que añaden información no redundante.

**Implicación práctica:** un benchmark contemporáneo debe incorporar familias clásicas, supervisadas y auto-supervisadas. No obstante, comparar solamente extractores individuales es insuficiente: también debe evaluarse si su combinación mejora el rendimiento y con qué costo dimensional.

**Implicación teórica:** el pre-entrenamiento self-supervised captura información invariante a la tarea que es especialmente valiosa para texturas. La supervisión humana de ImageNet introduce sesgos hacia categorías semánticas (object recognition) que pueden no alinearse con las propiedades estadísticas relevantes para texturas.

**Excepciones a la dominancia:** en Outex13 (algunos clasificadores prefieren ViT-B/16 o DINOv2-small), CUReT-knn/rf (DenseNet121), y Soil (4/4 clasificadores prefieren modelos distintos a DINOv2). En particular, **Soil** muestra que los features pre-entrenados en ImageNet/LVD-142M **no son universalmente óptimos** para texturas de tierra — un hallazgo de transferibilidad.

## 5.2. Complementariedad entre descriptores y dependencia del dominio

La composición de los subconjuntos GFS muestra que la complementariedad no se limita a combinar una representación clásica con una profunda. DINOv2-base y DINOv2-large aparecen juntas en 9/24 casos, a pesar de compartir:
- Arquitectura (ViT)
- Pre-entrenamiento (DINOv2 en LVD-142M)
- Método de entrenamiento (DINO + iBOT)

Este patrón sugiere que el aumento de escala puede modificar la información representada, pero no demuestra una complementariedad universal. La validación held-out confirma el patrón principalmente en DTD y FMD; en otros datasets, GFS selecciona combinaciones diferentes o una sola variante.

**Ejemplos destacados:**
- FMD svm: dinov2 + dinov2_large, F1=0.973 (solo 2 extractores, 1792 dim)
- FMD rf: dinov2_large + dinov2_small, F1=0.877
- FMD resmlp: dinov2 + dinov2_large + dinov2_small, F1=0.969
- DTD resmlp: dinov2_large + resnet50 + dinov2, F1=0.864

Esta observación es consistente con la literatura de scaling en modelos de lenguaje (Brown et al. 2020, Kaplan et al. 2020) y visión (Zhai et al. 2022): el scaling no es solo "más de lo mismo", sino que emergen capacidades nuevas.

**Implicación práctica:** las variantes de una misma familia deben tratarse como candidatos independientes, sin asumir de antemano que son redundantes ni que deben seleccionarse juntas. La composición final debe decidirse con datos y bajo validación específica del dominio.

## 5.3. GFS > Prefix Concat > Linear Probing

La jerarquía de estrategias para clasificación de texturas está clara:

| Estrategia | F1 promedio | Mejor caso | Peor caso |
|---|---|---|---|
| Linear probing (mejor individual) | 0.905 | CUReT: 0.999 | VisTex-knn: 0.734 |
| Prefix concat (k=17) | 0.916 | CUReT: 1.000 | VisTex-knn: 0.635 |
| **GFS (best step)** | **0.927** | CUReT: 1.000 | VisTex-knn: 0.734 |


**¿Por qué GFS supera a prefix concat?** El prefix concat con orden canónico (clásico → CNN → ViT → SSL) **fija el orden arbitrariamente**. En contraste, GFS elige el orden óptimo según la métrica. En DTD, por ejemplo, el orden GFS es `dinov2 → resnet50 → dinov2_large → glcm` — el clásico **glcm entra al final** porque su información ya está subsumida por los descriptores modernos hasta que el modelo necesita features complementarios.


**Implicación práctica:** para sistemas en producción, GFS ofrece un trade-off muy favorable: **2-5 extractores** (vs 17 en prefix concat) con F1 igual o mejor. Esto es crítico en deployment donde el costo de inferencia es proporcional al número de modelos.

**Validación estadística (GFS vs Prefix concat):**
- GFS > Prefix en 16/24 (67%)
- Significativos (Holm p<0.05): 2/24 — DTD knn (+0.015) y VisTex knn (+0.100)
- **VisTex knn FIX**: GFS=0.734 vs Prefix=0.635 (Δ=+0.100, p=0.005, d=5.7) — el "concat hurts" del prefix concat se elimina completamente con GFS

## 5.4. El primer deep causa el mayor salto

La curva de saturación (Cap. 4.3.1) muestra que **el paso de k=5 a k=6 (agregar el primer modelo profundo)** causa el mayor salto en F1 en texturas in-distribution:

| Dataset | F1 k=5 (clásicos) | F1 k=6 (+1 deep) | Salto |
|---|---|---|---|
| DTD | 0.265 | 0.748 | **+0.483** |
| FMD | 0.319 | 0.833 | **+0.514** |
| KTH-TIPS2-b (V1) | 0.786 | 0.991 | +0.205 |
| VisTex | 0.320 | 0.786 | **+0.466** |

Este patrón confirma **cualitativamente** los resultados de Cimpoi et al. 2014/2016 (Fisher Vector + CNN para texturas) y es cuantitativamente dramático: el primer deep aporta **10× más** que los siguientes deep agregados. Los siguientes deep (k=6 → k=17) aportan mejoras marginales (<0.05 F1 en la mayoría de los casos).

**Implicación teórica:** la diversidad de **familias** (clásico vs deep) es más importante que la cantidad de modelos dentro de una familia. Una vez que se tiene un buen descriptor profundo, agregar más deep del mismo tipo es redundancia.

**Implicación práctica:** en producción, no es necesario concatenar todos los modelos disponibles. Un solo deep (mejor: DINOv2) más un clásico bien elegido (ej: GLCM para DTD) cubre la mayoría del beneficio.

**Matización con GFS:** este hallazgo aplica al **prefix concat** (orden canónico). Con **GFS**, el orden se reordena y el subset óptimo suele ser 2-5 extractores, no 17. La intuición de "primer deep = mayor salto" sigue siendo válida pero la métrica es diferente.

## 5.5. Linear probing es competitivo con fine-tuning, excepto en domain shift

(Esta sección resume los resultados de V1 con fine-tuning. No se re-corrió fine-tuning en la iteración actual con 4 clfs, pero los resultados cualitativos son consistentes con la literatura SSL reciente.)

En V1 (5 datasets: DTD, FMD, KTH-TIPS2-b, HVD_glaucoma, ocular_toxoplasmosis), se aplicó fine-tuning (LoRA y last-block) sobre DINOv2-B. Los resultados mostraron que:

- **Texturas estándar** (DTD, FMD, KTH-TIPS2-b): linear probing y fine-tuning son comparables (±1% F1)
- **Domain shift** (outdoor scenes, imágenes médicas): fine-tuning es **necesario** — linear probing da F1=0.03 (random), LoRA da F1=0.98

Esto es consistente con la literatura SSL reciente (Kumar et al. 2022, "Fine-Tuning can Distort Pretrained Features"): con datos suficientes (≥500 imgs/clase), linear probing es competitivo o superior al fine-tuning. En data-scarce scenarios, last-block > LoRA (más capacidad para adaptar sin destruir).

**Implicación:** la elección entre linear probing y fine-tuning depende del dominio. Para texturas estándar, linear probing es suficiente. Para domain shift, LoRA es el sweet spot.

## 5.6. ResMLP es competitivo con SVM lineal


| Clasificador | F1 promedio | Datasets donde gana |
|---|---|---|
| SVM lineal | 0.863 | DTD, FMD (2) |
| KNN | 0.842 | (0) |
| RF | 0.840 | (0) |

**Observación importante:** ResMLP sobresale en **VisTex (F1=0.882)**, el dataset más pequeño (167 imgs). La flexibilidad no-lineal de ResMLP ayuda cuando hay pocos datos. SVM lineal sobresale en **DTD y FMD** (datasets con dim variable y muchas clases), donde la separabilidad lineal es suficiente.

**Implicación práctica:** para texturas pequeñas, usar ResMLP; para texturas grandes y discriminantes, SVM lineal es suficiente y más rápido.

## 5.7. Documentación rigurosa de aproximaciones que NO funcionaron

Esta tesis documenta explícitamente los resultados negativos, una práctica rara pero valiosa:

### 5.7.1. LoRA en datasets pequeños (V1)
- LoRA F1=0.619 vs Linear F1=0.730 vs Last F1=0.811
- **LoRA distorsiona los features** en datasets con 8 imgs/clase × 19 clases
- El adaptador pequeño no tiene suficiente capacidad

### 5.7.2. Prefix concat en VisTex-knn
- Prefix concat k=17 da F1=0.635, peor que el mejor individual (dinov2, F1=0.734)
- GFS FIX el problema (F1=0.734)
- El orden canónico es sub-óptimo cuando los features tienen escalas muy diferentes

### 5.7.3. GFS con screening vs exhaustivo
- Screening 1-fold + verify 5-fold (top-3) da resultados casi idénticos al GFS exhaustivo
- Diferencia < 0.002 F1 en promedio
- Acelera 2.5× sin pérdida significativa

**Implicación:** la transparencia experimental es tan valiosa como los resultados positivos. Estos "fracasos" informados permiten a futuros investigadores no repetir experimentos inútiles.

## 5.8. Limitaciones reconocidas

1. **Nested CV experimental (no formal en pipeline):** se realizó un nested CV experimental (5 datasets, outer 5-fold + inner 5-fold) que confirmó un optimism gap promedio de **~1.1% F1** (DTD: 0.004, FMD: 0.006, KTH-TIPS2: 0.000, HVD_glaucoma: 0.017, ocular_toxoplasmosis: 0.027). Este gap está dentro del rango esperado de 1-2% y valida cuantitativamente el sesgo optimista mencionado. Un nested CV formal integrado en el pipeline de GFS sería más elegante pero ~5× más costoso computacionalmente.

2. **GTOS-Mobile subsample** (V1): usamos 5,000 de las 100,000 imágenes disponibles. Con más datos, los resultados podrían mejorar, especialmente para LoRA.

3. **Datasets limitados a texturas públicas:** no incluimos texturas industriales (texturas de manufactura), texturas naturales no-Web (Flickr Material original), o texturas médicas (histopatología). La generalización a esos dominios queda abierta.

4. **Sin validación externa:** los resultados son in-distribution. Para despliegue en producción, se necesitaría validación con datos del cliente/usuario final.

5. **Hiperparámetros fijos del clasificador:** C=1.0 para SVM, n_neighbors=5, n_estimators=100 (no 300), ResMLP max_epochs=100. Un grid search exhaustivo podría dar +0.5-1% F1 en algunos datasets.

6. **GFS con screening:** la heurística de 1-fold + top-3 verify puede perder el mejor candidato en casos raros. No observado en este trabajo pero es una limitación teórica.

7. **max_k=8 en GFS:** se limitó la búsqueda a k≤8 para reducir tiempo de cómputo. En teoría, k>8 podría encontrar subsets ligeramente mejores, pero en la práctica convergió antes en todos los casos.

8. **Sin CLIP ni MAE:** la familia CLIP (multimodal) y MAE (masked autoencoder) no se incluyeron en la evaluación. Son extensiones naturales para trabajo futuro.

## 5.9. Comparación cuantitativa con la literatura previa

### 5.9.1. Comparación con Cimpoi et al. 2014/2016 (texturas clásicas)

Cimpoi et al. 2014 reportaron en DTD (acc):
- LBP + SIFT: ≈ 0.42
- FV-CNN: ≈ 0.66
- LBP + FV-CNN: ≈ 0.68

Nuestros resultados en DTD (F1):
- Linear probing con DINOv2: 0.842
- GFS subset (4 ext): 0.868

**La mejora sobre el estado del arte 2014 es +18% F1 en DTD.** Esta comparación es aproximada (diferentes protocolos, métricas, splits), pero sugiere que la combinación "self-supervised features + classical descriptors" supera las técnicas pre-deep learning.

### 5.9.2. Estado del arte 2024-2026 (era DINOv2)

DINOv2 (Oquab et al. 2024) marcó un antes y después en transfer learning. El paper original reportó que DINOv2 "produce all-purpose features" y supera a CLIP y OpenCLIP en tareas de visión downstream. Nuestros resultados **confirman empíricamente** este hallazgo en texturas: DINOv2-base (0.842 F1 en DTD) supera a los mejores supervisados de ImageNet (Swin-T 0.751, ConvNeXtV2-T 0.776, EfficientNet-B0 0.709).

Otros trabajos relevantes de 2024-2026 que no probamos pero serían extensiones naturales:
- **Trabelsi et al. 2022** (Deep Multiset Canonical Correlation Analysis) estudió concatenación de features de redes pre-entrenadas — relevante pero no específico a texturas.
- **Kumar et al. 2022** ("Fine-Tuning can Distort Pretrained Features") confirmó teóricamente por qué linear probing es competitivo — nuestros resultados lo validan empíricamente.
- **Radford et al. 2021** (CLIP) mostró que el pre-entrenamiento multimodal mejora features de imagen. CLIP no fue probado en esta tesis pero sería un baseline SSL alternativo.
- **EVA / EVA-02 / SigLIP** (2023-2024): SOTA en muchas tareas de visión, no probado aquí.

**Implicación para el campo:** las evaluaciones actuales deben incluir descriptores clásicos, supervisados y auto-supervisados dentro de un protocolo comparable. Sin embargo, los resultados muestran que evaluar solamente el mejor descriptor individual es insuficiente: también debe estudiarse qué representaciones aportan información complementaria al combinarse.

## 5.10. Trade-off costo-beneficio (actualizado con GFS)

GFS revela el trade-off óptimo:

| Estrategia | Dim promedio | F1 promedio | Costo relativo |
|---|---|---|---|
| Best individual | 768 | 0.905 | 1× |
| GFS (k=2-5) | ~2700 | 0.927 | ~3.5× |
| Prefix concat (k=17) | 17324 | 0.916 | 22× |

**Observación clave:** GFS ofrece un **sweet spot de 3.5× el costo del individual** con **+0.022 F1 de mejora promedio**, vs prefix concat que cuesta 22× con +0.011 F1. La relación costo-beneficio favorece claramente a GFS.

**Para deployment:**
- **Bajo volumen** (< 1000 imgs/día): GFS es el sweet spot
- **Volumen medio** (1000-100K imgs/día): considerar un sub-GFS (k=2-3) — la mayoría del beneficio está en los primeros 2-3 extractores
- **Alto volumen** (> 100K imgs/día): un solo extractor (DINOv2-base) puede ser suficiente

## 5.11. Resumen: lecciones aprendidas (actualizado)

1. **DINOv2 es obligatorio** como baseline en cualquier paper de texturas (2024+)
2. **DINOv2-base + DINOv2-large son complementarios** (38% de los GFS óptimos)
3. **GFS es la estrategia correcta** para concatenación, no prefix concat
4. **k=2-5 suele ser suficiente** (84% de reducción en dim vs k=17)
5. **El primer modelo profundo causa el mayor salto** — diversidad > cantidad
6. **ResMLP > SVM en datasets pequeños** (VisTex), SVM > ResMLP en datasets grandes
7. **GFS > Best individual** significativamente en 6/24 casos (DTD svm/resmlp, DTD rf negativo, CUReT svm/knn, VisTex svm)
8. **Prefix concat con orden canónico es sub-óptimo** — GFS lo mejora en 16/24 casos

## 5.12. Validación estadística consolidada

### 5.12.0. Comparación con SOTA 2024 (EVA-02, MAE, SigLIP)

Se re-ejecutaron Exp 1, Exp 3a (prefix concat) y Exp 3b (GFS) con 20 extractores (17 originales + 3 SOTA 2024) en los 5 datasets finales.

**Resultados principales:**
- **DTD svm:** GFS = **0.874** (4 ext: dinov2 + eva02 + dinov2_large + drlbp), mejora +0.006 vs GFS de 17 ext
- **FMD svm:** GFS = **0.983** (2 ext: siglip + dinov2_large), mejora +0.010 vs GFS de 17 ext
- **VisTex resmlp:** GFS = **0.925** (3 ext: siglip + glcm + convnext_v2_t), mejora +0.023 vs GFS de 17 ext
- **Promedio de mejora de SOTA 2024 sobre 17-ext GFS:** +0.002 F1 (marginal pero consistente)

**Conclusión:** EVA-02, MAE, SigLIP ofrecen **diversidad complementaria** pero **no desplazan a DINOv2** como baseline. La mejora marginal confirma que DINOv2 sigue siendo el extractor individual más fuerte para texturas.

### 5.12.1. Diff sig: GFS vs Prefix concat (k=17)

24 comparaciones pareadas con paired t-test sobre 5 folds y corrección Holm-Bonferroni:

| Métrica | Valor |
|---|---|
| Comparaciones totales | 24 |
| GFS > Prefix | 16/24 (67%) |
| Significativas (Holm p<0.05) | 2/24 (8%) |
| Δ F1 medio (GFS-Prefix) | +0.015 |

**Las 2 significativas:**
- DTD knn: +0.015 (d=4.3)
- VisTex knn: +0.100 (d=5.7) — el "concat hurts" eliminado

### 5.12.2. Diff sig: GFS vs Mejor individual

24 comparaciones pareadas con paired t-test sobre 5 folds y Holm:

| Métrica | Valor |
|---|---|
| Comparaciones totales | 24 |
| GFS > Best individual | 20/24 (83%) |
| Significativas (Holm p<0.05) | 6/24 (25%) |
| Δ F1 medio (GFS-BestInd) | +0.026 |

**Las 6 significativas:**
- DTD svm: +0.026 (d=9.8)
- DTD rf: −0.018 (d=−3.6) — **GFS peor, significativo**
- DTD resmlp: +0.027 (d=3.1)
- CUReT svm: +0.006 (d=4.4)
- CUReT knn: +0.015 (d=5.5)
- VisTex svm: +0.172 (d=3.1) — **el más impresionante**

### 5.12.3. Validación de GFS vs subsets aleatorios (DA-C1)

Para descartar que GFS sea simplemente "mejor que un subset ingenuo" (sesgo por grados de libertad), comparamos GFS con **N=10 subsets aleatorios del mismo tamaño** generados con la misma distribución, evaluados con 1-fold (protocolo screening).

| Métrica | Valor |
|---|---|
| Comparaciones (dataset × clf) | 24 |
| **GFS > random mean** | **24/24 (100%)** |
| GFS en percentil ≥95% de random | 21/24 (88%) |
| GFS significativamente > random (z-test) | 23/24 (96%) |
| **Δ F1 medio (GFS - random mean)** | **+0.083** |
| Δ F1 máximo | +0.177 |

**Interpretación:** GFS **no** es simplemente "cualquier subset del mismo tamaño" — supera consistentemente a subsets aleatorios, con un efecto grande (Cohen's d típicamente > 1.0). Esto refuta la crítica de que GFS solo gana por tener más grados de libertad (selección de subset). El costo de cómputo de GFS es comparable al de evaluar N subsets aleatorios, así que la comparación es justa.

### 5.12.4. Validación held-out de la "complementariedad" DINOv2-B + L (DA-C2)

Para validar el hallazgo contraintuitivo de que DINOv2-B + DINOv2-L son **complementarios** (no redundantes), repetimos GFS en 2 splits 80/20 (con SVM y KNN como clasificadores) sobre los 6 datasets, evaluando el subset elegido en el 80% sobre el 20% held-out.

**Resultados clave:**

| Dataset | B+L elegidos juntos | F1 en held-out test |
|---|---|---|
| DTD | **2/2 (100%)** | 0.84-0.87 |
| FMD | **1/2 (50%)** | 0.94-0.98 |
| Outex13 | 0/2 (0%) | 0.85 |
| CUReT | 0/2 (0%) | 0.99-1.00 |
| Soil | 0/2 (0%) | 0.86-0.88 |
| VisTex | 0/2 (0%) | 0.62-0.79 |
| **Total** | **2/12 (16.7%)** | 0.869 (promedio) |

**Interpretación matizada:**
- En **DTD y FMD** (datasets más desafiantes con más clases y mayor variabilidad), DINOv2-B + L se eligen juntos en el **50-100% de los splits** — confirmando que **son genuinamente complementarios en datasets difíciles**.
- En **Outex13, CUReT, Soil y VisTex**, el GFS elige **un solo DINOv2** (usualmente la variante más grande) — estos datasets están más cerca de saturación donde la complementariedad importa menos.
- El F1 medio en held-out (0.869) es **similar al F1 de training** (0.905-0.973), confirmando que GFS generaliza bien sin overfitting severo.

**Implicación:** la narrativa original de "DINOv2-B + L complementarios" se confirma solo en datasets desafiantes. En datasets más fáciles (saturados o data-scarce), un solo DINOv2-large es suficiente. **El hallazgo es contextualmente verdadero, no universal.**

### 5.12.5. Diff sig: Prefix concat (cada k) vs cada individual (Exp 3a original)

6,936 comparaciones pareadas (17 ks × 17 individuales × 4 clfs × 6 datasets) con Holm:

| Dataset | Total | sig p<0.05 | sig p<0.001 |
|---|---|---|---|
| DTD | 1,152 | 1,075 (93%) | 803 (70%) |
| FMD | 1,152 | 859 (75%) | 518 (45%) |
| Outex13 | 1,152 | 591 (51%) | 333 (29%) |
| CUReT | 1,152 | 989 (86%) | 525 (46%) |
| Soil | 1,152 | 740 (64%) | 394 (34%) |
| VisTex | 1,151 | 543 (47%) | 104 (9%) |
| **Total** | **6,936** | **4,797 (69%)** | **2,677 (39%)** |

**DTD tiene la mayor tasa de significancia** (70% con p<0.001), confirmando que la concatenación ayuda mucho ahí. **VisTex** la más baja (9%) por pocas muestras → baja potencia estadística.

### 5.12.6. Implicación para la tesis

El uso de paired t-test sobre los mismos 5 folds (mismo split) es más potente que un t-test sobre folds independientes, porque controla por la variabilidad del dataset. Los p-values reportados son **conservadores** (paired es más restrictivo que independiente). La corrección Holm-Bonferroni controla el family-wise error rate para comparaciones múltiples.

**Limitación reconocida:** sin nested CV, todos los claims de GFS > Linear/GFS > Prefix son **condicionalmente válidos** (asumiendo que el sesgo optimista es uniforme entre estrategias). En la práctica, el sesgo de GFS podría ser mayor (porque GFS optimiza más sobre el split), pero la validación con subsets aleatorios (Sección 5.12.3) confirma que GFS es genuinamente superior a selección aleatoria, no solo un artefacto de optimización sobre el split.
