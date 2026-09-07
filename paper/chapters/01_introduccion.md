# Capítulo 1 — Introducción

## 1.1. Contexto: clasificación de texturas y su relevancia

La **clasificación de texturas** es una tarea fundamental en visión por computador con aplicaciones en dominios diversos: recuperación de imágenes por contenido (CBIR), inspección industrial de materiales, teledetección, dermatología automatizada, oftalmología diagnóstica, e histopathología computacional. A pesar de más de cinco décadas de investigación, la elección del descriptor de características sigue siendo un problema abierto: no existe un único extractor que domine universalmente sobre todos los tipos de texturas y dominios.

Históricamente, el problema se abordó con **descriptores handcrafted** como Local Binary Patterns (LBP, Ojala et al. 2002), Gray-Level Co-occurrence Matrices (GLCM, Haralick 1979), bancos de filtros Gabor, y Histogram of Oriented Gradients (HOG, Dalal & Triggs 2005). Estos métodos son interpretables, computacionalmente eficientes, y producen vectores de dimensionalidad moderada. Sin embargo, su capacidad representacional es limitada: capturan estadísticas locales predefinidas que pueden no capturar la complejidad de texturas naturales con alta variabilidad intra-clase.

Desde 2012, las **redes neuronales convolucionales profundas** (CNNs) como AlexNet, VGG, ResNet, y EfficientNet, preentrenadas en ImageNet, revolucionaron la visión por computador y se convirtieron en la opción por defecto para extraer features. Más recientemente, los **Vision Transformers** (ViT, Swin-T, DeiT) y los modelos **auto-supervisados** (DINOv2, MAE) han desplazado el estado del arte. La pregunta natural es: **¿cuál de estos extractores es el mejor para texturas?** Y más importante aún: **¿se complementan entre sí?**

## 1.2. La hipótesis de complementariedad

La intuición detrás de la **fusión de features** (feature fusion) es que diferentes extractores capturan diferentes aspectos de la información visual. Por ejemplo, un descriptor LBP captura micro-texturas locales, mientras que un CNN preentrenado en ImageNet captura patrones semánticos globales. La **concatenación** de ambos embeddings produce un vector combinado que, en principio, contiene más información discriminativa que cualquiera de los dos por separado.

Esta intuición ha sido validada empíricamente en la literatura de texturas desde hace más de una década (Cimpoi et al. 2014, Sánchez et al. 2013), pero la pregunta sigue abierta en 2026: **con el advenimiento de modelos self-supervised como DINOv2 que dominan benchmarks, ¿la concatenación clásico+deep sigue aportando valor, o los modelos modernos ya capturan toda la señal relevante?**

## 1.3. Brecha en la literatura

La mayoría de los trabajos previos sobre feature fusion en texturas se limitan a **2-3 extractores** (típicamente LBP + CNN), usan **orden canónico fijo** para la concatenación (prefix concat), y reportan resultados en **1-2 datasets**. Hasta donde sabemos, no existe un estudio sistemático que:

1. Compare **10+ extractores heterogéneos** (clásicos + CNN + ViT + self-supervised + SOTA 2024) en el mismo marco experimental.
2. Evalúe **estrategias de selección de subconjuntos** (más allá de la concatenación completa o predefinida).
3. Cuantifique el **beneficio marginal** de agregar cada extractor (curvas de saturación).
4. Evalúe la **transferibilidad** entre tipos de texturas (naturales, controladas, outdoor scenes, data-scarce).
5. Documente **explícitamente qué NO funciona** (PCA, fine-tuning, MLP head, fusion alternatives, MLP).
6. Compare con **SOTA 2024** (EVA-02, MAE, SigLIP) en el mismo marco experimental.

## 1.4. Pregunta de investigación e hipótesis

**Pregunta central:** ¿La concatenación sistemática de múltiples descriptores visuales (clásicos + deep) mejora la clasificación de texturas más allá del mejor extractor individual, y bajo qué condiciones?

**Hipótesis principal (H1):** La concatenación de un subconjunto cuidadosamente seleccionado de extractores complementarios supera al mejor extractor individual, con un beneficio cuantificable y explicable.

**Sub-hipótesis:**
- **H2 (DTD):** La concatenación de extractores clásicos con deep mejora F1 en ≥2 puntos sobre el mejor individual.
- **H3 (FMD):** El primer extractor deep (después de los clásicos) produce el mayor salto en F1, mientras que extractores deep adicionales aportan mejoras marginales.
- **H4 (VisTex, data-scarce):** En datasets muy pequeños con muchas clases, la concatenación clásico+deep es competitiva o superior al fine-tuning de modelos grandes, a una fracción del costo computacional.
- **H5 (Selección):** La selección greedy de subconjuntos (GFS) supera al prefix concat con orden canónico fijo, encontrando subconjuntos más compactos con F1 igual o mejor.
- **H6 (SOTA 2024):** Los modelos SOTA 2024 (EVA-02, MAE, SigLIP) ofrecen diversidad complementaria que mejora marginalmente los subsets GFS pero no desplazan a DINOv2 como baseline.

**Predicción nula (H0):** La concatenación no aporta mejora significativa sobre el mejor extractor individual — los modelos modernos ya capturan toda la señal relevante.

## 1.5. Contribuciones de esta tesis

Esta tesis contribuye a la literatura con los siguientes hallazgos originales:

1. **Comparación sistemática a escala:** se evaluaron **20 extractores** (5 clásicos: LBP multi-escala, GLCM, Gabor, HOG, DRLBP; 6 CNN: VGG16, ResNet-50, ResNet-101, DenseNet-121, EfficientNet-B0, ConvNeXt V2-T; 3 ViT: ViT-B/16, Swin-T, DeiT-S; 3 DINOv2: small/base/large; 3 SOTA 2024: EVA-02, MAE, SigLIP) sobre **6 datasets públicos de texturas** (DTD, FMD, Outex13, CUReT, Soil, VisTex), con 5-fold stratified cross-validation y ~1200 corridas controladas.

2. **Caracterización del efecto de la estrategia de combinación:** se demuestra que concatenar todos los descriptores no garantiza el mejor resultado. La concatenación prefix puede introducir redundancia o perjudicar el desempeño, mientras que la selección guiada conserva los componentes informativos.

3. **Greedy Forward Selection (GFS) como estrategia de selección de descriptores:** la búsqueda greedy encuentra subconjuntos compactos de 2-5 extractores, reduce en 84% la cantidad de componentes respecto de k=17 y alcanza un macro-F1 igual o superior al mejor individual en 5/6 datasets. La mejora promedio es +0.022 frente al linear probing y +0.011 frente al prefix concat; 6/24 comparaciones con el mejor individual son significativas después de la corrección de Holm.

4. **Evidencia de complementariedad dependiente del dominio:** los subconjuntos seleccionados combinan familias diferentes y cambian entre datasets y clasificadores. Las variantes DINOv2-base y DINOv2-large aparecen juntas en 9/24 subconjuntos, pero este patrón es un caso particular del resultado general: representaciones incluso cercanas arquitectónicamente pueden aportar información no redundante bajo determinadas condiciones.

5. **Caracterización de domain shift (V1, 5 datasets):** GTOS-Mobile (outdoor scenes) revelaba los límites del linear probing: F1=0.031 (random) con todos los extractores frozen. **LoRA fine-tuning FIX el problema** (0.031 → 0.980), demostrando que linear probing con modelos pre-entrenados NO es universalmente suficiente. (En la iteración actual, GTOS-Mobile fue removido del scope por decisión del tutor.)

6. **Documentación rigurosa de aproximaciones que NO funcionan:** se probaron y reportaron como resultados negativos: PCA antes de concatenar (sin cambio), MLP head en concat (peor que SVM lineal), estrategias de fusión alternativas como sum y weighted_sum (peor que concat), LoRA en datasets data-scarce (distorsiona features), prefix concat con orden canónico en VisTex knn (empeora vs best individual — FIX con GFS). Esta transparencia experimental es parte de la contribución.

## 1.6. Estructura de la tesis

La tesis se organiza en 6 capítulos:

- **Capítulo 1 (este):** Introducción, motivación, pregunta de investigación, contribuciones.
- **Capítulo 2:** Revisión de la literatura sobre descriptores de texturas (clásicos, CNN, ViT, self-supervised), estrategias de fusión de features, y aplicaciones en clasificación.
- **Capítulo 3:** Metodología: descripción detallada de los 20 extractores, los 6 datasets, el protocolo experimental, y la implementación del algoritmo GFS.
- **Capítulo 4:** Resultados: baseline por extractor, curvas de saturación con prefix concat, GFS sobre los 6 datasets, comparación de estrategias (incluyendo SOTA 2024 y GFS con 20 extractores), y análisis de confusión por clase.
- **Capítulo 5:** Discusión: análisis cuantitativo del balance costo-beneficio, validación de las hipótesis, comparación con el estado del arte, y reporte de aproximaciones exploradas que no funcionaron.
- **Capítulo 6:** Conclusión: resumen de contribuciones, limitaciones, y líneas de trabajo futuro.

## 1.7. Resumen ejecutivo

La presente tesis responde una pregunta aparentemente simple pero técnicamente profunda: **¿vale la pena combinar múltiples descriptores visuales para clasificar texturas?** La respuesta, basada en ~1200 experimentos controlados sobre 6 datasets, 20 extractores (5 clásicos + 6 CNN + 3 ViT + 3 DINOv2 + 3 SOTA 2024), 4 clasificadores, y 3 estrategias (linear probing, prefix concat, GFS), es matizada:

- **Sí**, cuando se seleccionan cuidadosamente los extractores (GFS).
- **El beneficio es genuino** (+0.022 F1 promedio sobre el mejor individual, +0.172 F1 pico en VisTex-svm) y **consistente** en 5 de 6 datasets.
- **El costo en dimensionalidad** (84% reducción vs prefix concat k=17) **es favorable** para la mayoría de las aplicaciones.
- **Los descriptores auto-supervisados proporcionan una base individual fuerte**, pero las mejores soluciones se explican por su combinación con representaciones complementarias.
- **La composición óptima no es universal**: depende del dataset, del clasificador y del equilibrio entre información adicional y dimensionalidad.
- **ResMLP es competitivo con SVM lineal** (F1 promedio 0.902 vs 0.863), ganando en datasets pequeños.
- **Los modelos pre-entrenados con linear probing** son competitivos o superiores al fine-tuning en texturas estándar, confirmando hallazgos recientes de la literatura SSL (Kumar et al. 2022). La excepción importante es el domain shift fuerte (outdoor scenes en V1), donde LoRA es necesario.

Los capítulos siguientes desarrollan los resultados cuantitativos, los experimentos negativos y el análisis de las condiciones bajo las cuales la concatenación resulta beneficiosa.
