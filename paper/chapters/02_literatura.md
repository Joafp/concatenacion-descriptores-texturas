# Capítulo 2 — Revisión de la Literatura

## 2.1. Clasificación de texturas: historia y enfoques

La clasificación de texturas ha sido un problema central en visión por computador desde los años 70, con aplicaciones en recuperación de imágenes, inspección industrial, teledetección, y diagnóstico médico asistido por computador. Históricamente, la investigación en texturas se ha dividido en tres grandes eras: **estadística** (años 70-90), **basada en filtros/modelos** (años 80-2000s), y **basada en aprendizaje profundo** (2012-presente).

### 2.1.1. La era estadística: descriptores handcrafted

Los **descriptores handcrafted** dominan la literatura desde los años 70 hasta la aparición de AlexNet (2012). Estos métodos están diseñados por expertos para capturar estadísticas específicas de las texturas.

**LBP (Local Binary Patterns, Ojala et al. 2002):** uno de los descriptores más exitosos. Asigna a cada píxel un código binario basado en comparaciones con sus vecinos, y luego calcula un histograma. Multi-escala: LBP en varias resoluciones captura patrones a diferentes escalas. Variantes: LBP rotation-invariant, LBP uniforme, dynamic texture, LBP completion, CLBP, LTP.

**GLCM (Gray-Level Co-occurrence Matrix, Haralick 1979):** captura estadísticas de segundo orden (correlaciones espaciales entre pares de píxeles a diferentes distancias y orientaciones). Propiedades: contraste, disimilaridad, homogeneidad, energía, correlación, ASM. Variantes: GLCM en color, multi-escala, 3D-GLCM.

**Gabor filters:** banco de filtros pasa-banda inspirados en el cortex visual. Cada filtro responde a una frecuencia y orientación particular. Variantes: Gabor multi-escala, multi-orientación, log-Gabor.

**HOG (Histogram of Oriented Gradients, Dalal & Triggs 2005):** originalmente para detección de personas, también útil para texturas. Histograma de gradientes en celdas locales, normalizado en bloques.

**LBP variants for rotation:** el DRLBP (Dominant Rotated LBP, Mehta & Egiazarian 2011) extrae los patrones dominantes a través de rotaciones para mayor robustez. LBP-TOP (Three Orthogonal Planes) extiende LBP a texturas dinámicas (video).

**Limitaciones de los descriptores handcrafted:** requieren diseño manual, no aprenden de datos, su poder representacional es limitado por la imaginación del diseñador.

### 2.1.2. La era del deep learning: CNNs

**AlexNet (Krizhevsky et al. 2012)** ganó ImageNet 2012 con un margen enorme, inaugurando la era del deep learning. Desde entonces, las CNNs han dominado la clasificación de texturas:

- **VGG (Simonyan & Zisserman 2014):** arquitectura profunda y uniforme, popular como feature extractor.
- **ResNet (He et al. 2016):** conexiones residuales, permitió redes de 50-152+ capas. ResNet-50 sigue siendo popular como baseline.
- **EfficientNet (Tan & Le 2019):** scaling compuesto (depth + width + resolution). EfficientNet-B0 es el más pequeño de la familia.
- **ConvNeXt (Liu et al. 2022):** "ConvNet for the 2020s", moderniza ResNet con designs de Transformers. ConvNeXt V2 (Woo et al. 2023) añade self-supervisión con FCMAE.

**Pre-entrenamiento en ImageNet** es el estándar: los features extraídos de CNNs preentrenadas son sorprendentemente transferibles a texturas, incluso sin fine-tuning.

### 2.1.3. La era de los Transformers y self-supervised

**ViT (Vision Transformer, Dosovitskiy et al. 2021):** aplicó la arquitectura Transformer a imágenes mediante patches. ViT-B/16 es la versión base.

**Swin Transformer (Liu et al. 2021):** jerarquía de ventanas con shifted windows, combina eficiencia local con capacidad global.

**DeiT (Touvron et al. 2021):** ViT entrenado de manera data-efficient con destilación. Más pequeño y rápido que ViT.

**DINOv2 (Oquab et al. 2024):** ViT preentrenado con self-supervisión sobre 142M de imágenes no etiquetadas. Los features resultantes son de propósito general según los autores y han mostrado buen desempeño en múltiples tareas de transferencia. En esta tesis constituye una de las familias modernas incluidas para estudiar su complementariedad con descriptores clásicos, CNN y otros Transformers.

**MAE (Masked Autoencoders, He et al. 2022):** alternativa de self-supervisión con masked reconstruction. Los features MAE son competitivos con DINOv2 en muchas tareas downstream, aunque con diferentes biases. No se incluye en esta tesis pero sería una extensión natural.

**EVA / EVA-02 (Fang et al. 2023):** familia de ViT pre-entrenados con masked image modeling a escala (300M imágenes). EVA-02 ha mostrado SOTA en múltiples benchmarks de visión. No se incluye en esta tesis.

**SigLIP (Zhai et al. 2023):** variante de CLIP con sigmoid loss, más eficiente para entrenamiento a gran escala. Compite con DINOv2 en tareas de clasificación zero-shot.

**InternImage / InternVL (Wang et al. 2023):** modelos de gran escala con mechanisms de attention alternativa. SOTA en varios benchmarks multimodales.

**BEiT-3 (Wang et al. 2023):** generalización de BEiT a multimodal. SOTA en image classification entre modelos open-source.

**Resumen del estado del arte en visión 2024-2026:** la familia de modelos DINOv2, EVA-02, BEiT-3, SigLIP dominan los benchmarks. En esta tesis se eligió **DINOv2** por: (a) excelente rendimiento en texturas reportado por Oquab et al. 2024, (b) disponibilidad de 3 variantes (small/base/large) que permiten estudiar el efecto del scaling, (c) pre-entrenamiento pure-visual (sin multimodal) que evita confounders de lenguaje. Una limitación es que **no se comparan directamente con EVA-02, MAE, SigLIP o BEiT-3** — esto queda como trabajo futuro (Cap. 6.6).

## 2.2. Fusión de features: el estado del arte

La intuición detrás de la **fusión de features** (feature fusion) es que diferentes extractores capturan diferentes aspectos de la información visual. La **concatenación** es la estrategia dominante.

### 2.2.1. Trabajos seminales en texturas

**Cimpoi et al. (2014, 2016):** mostraron que la concatenación de descriptores Fisher Vector (FV) extraídos de CNNs con descriptores handcrafted (SIFT, LBP) mejora la clasificación de texturas en DTD, FMD, y KTH-TIPS2. Su pipeline FV-CNN logró F1 significativamente superior al mejor individual.

**Sánchez et al. (2013):** introdujeron el Fisher Vector como codificación mejor que el BoW (Bag of Words) estándar, sentando las bases para la era moderna de feature fusion en texturas.

**Zhang et al. (2017, Deep-TEN):** CNN entrenada desde cero específicamente para texturas, alternativa a usar features preentrenados.

### 2.2.2. Estrategias de fusión

**Concatenación simple:** la estrategia más común. Veces los embeddings se concatenan y se entrena un clasificador (típicamente SVM lineal). Ventaja: simple. Desventaja: alta dimensionalidad, posible redundancia entre features.

**Weighted concatenation:** cada feature tiene un peso (fijo o aprendido). Reduce el impacto de features ruidosas.

**Sum/Mean fusion:** todos los features se proyectan a la misma dimensión y se suman. Reduce dimensionalidad pero pierde información específica.

**Bilinear pooling:** outer product de dos features, captura interacciones pairwise. Dimensionalidad cuadrática.

**Cross-attention fusion:** los features se atienden entre sí (Transformer-style). Más expresivo pero costoso.

**Tensor fusion:** generalización del bilinear, combina N features con productos externos.

### 2.2.3. Selección de features

Cuando se tienen muchos extractores, surge la pregunta: **¿cuáles son los más útiles?** Tres familias de métodos:

**Filter methods:** score por feature individual (Fisher, mutual information, chi-cuadrado) y selección top-k. Rápido pero ignora interacciones.

**Wrapper methods:** evaluación de subsets específicos por su performance. Más costoso pero captura interacciones. **Greedy Forward Selection (GFS)** es el wrapper más simple.

**Embedded methods:** la selección es parte del entrenamiento (Lasso con L1, attention-based). Más eficiente pero menos modular.

**Sequential Floating Forward Selection (SFFS):** variante de GFS que permite **eliminar** features agregados previamente, corrigiendo errores tempranos.

**Recursive Feature Elimination (RFE):** train, eliminar el feature menos importante, repetir. Más costoso.

### 2.2.4. El estado del arte en feature fusion (2020-2026)

La literatura reciente (2020-2026) sobre feature fusion se ha centrado en:

- **Vision Transformers como feature extractors:** ViT, Swin, BeiT han reemplazado a CNNs en muchas tareas.
- **Self-supervised learning:** DINOv2, MAE, CLIP han mostrado que los features pre-entrenados sin supervisión son sorprendentemente buenos.
- **Multimodal fusion:** combinación de texto + imagen (CLIP), audio + video, etc. Aunque no es directamente texturas, las técnicas se transladan.

**Lacuna identificada:** la mayoría de los estudios se limitan a 2-3 extractores, un solo dataset, o un protocolo fijo. Falta un estudio **sistemático** que evalúe muchos extractores heterogéneos (clásicos + CNN + ViT + SSL) en un marco experimental controlado.

## 2.3. Trabajos relacionados en clasificación de texturas

Varios trabajos recientes han explorado la clasificación de texturas con modelos modernos. **Deep-TEN** (Zhang et al. 2017) fue uno de los primeros en entrenar CNNs end-to-end específicamente para texturas. **TextureNet** (Andrearczyk et al. 2019) exploró redes basadas en la convolución de V1. **Trabelsi et al. 2022** estudió concatenación de features de redes pre-entrenadas con **Deep Multiset CCA**, una técnica relacionada pero más sofisticada que la concatenación simple. **Bellavia et al. 2022** publicó un benchmark de texturas con análisis de texturas handcrafted vs CNN.

**Lacuna identificada:** la mayoría de los estudios se limitan a 2-3 extractores, un solo dataset, o un protocolo fijo. Falta un estudio **sistemático** que evalúe muchos extractores heterogéneos (clásicos + CNN + ViT + SSL) en un marco experimental controlado.

**Por qué no se incluyen datasets médicos:** la clasificación de texturas en imágenes médicas (dermatología, oftalmología, histopathología) comparte desafíos metodológicos con nuestro trabajo (datos escasos, transferibilidad limitada, necesidad de fine-tuning). Sin embargo, en la versión V1 del manuscrito se incluyeron HVD_glaucoma y ocular_toxoplasmosis, y se removieron en V2 por decisión del tutor para mantener el scope en **texturas naturales y controladas** puras, no en imágenes médicas (que típicamente requieren consideraciones éticas y de privacidad adicionales). El trabajo futuro puede extender la metodología a texturas médicas (Cap. 6.6).

## 2.4. ¿Por qué linear probing?

**Linear probing** (Radford et al. 2021, CLIP) es el estándar para evaluar embeddings pre-entrenados: entrenar solo una capa lineal (o SVM) encima de features fijos, sin fine-tuning. Tres razones:

1. **Eficiencia computacional:** no requiere backpropagation a través del modelo grande.
2. **Aislamiento de la calidad del feature:** si el feature es bueno, linear probing lo demuestra.
3. **Comparabilidad:** permite comparar extractores sin la variabilidad introducida por el fine-tuning.

**Limitaciones:**
- En datasets grandes, fine-tuning puede superar a linear probing.
- En datasets pequeños (<1000), linear probing suele ser **mejor o equivalente** a fine-tuning (lo confirmamos en nuestros experimentos, Sección 5.11.2).

## 2.5. Selección de extractores para esta tesis

Dada la proliferación de extractores de características disponibles en 2024-2026, la selección de los 17 modelos evaluados en esta tesis siguió tres criterios:

1. **Cobertura de familias:** 5 clásicos + 6 CNN + 3 ViT + 3 DINOv2 = 4 familias representativas. Esto permite analizar la contribución marginal de cada familia (Cap. 5.3).

2. **Disponibilidad de pre-entrenamiento:** todos los modelos profundos vienen con pesos pre-entrenados en ImageNet (o LVD-142M para DINOv2), facilitando la reproducibilidad.

3. **Variedad de escalas:** DINOv2-small (22M), DINOv2-base (86M), DINOv2-large (304M) permiten estudiar el efecto del scaling.

**Extractores NO incluidos** (y por qué):
- **CLIP, SigLIP:** pre-entrenamiento multimodal añade complejidad (lenguaje). Esta tesis se enfoca en visión pura.
- **EVA-02, MAE, BEiT-3:** SOTA recientes en visión general. Quedan como trabajo futuro (Cap. 6.6).
- **Modelos específicos de texturas** (Deep-TEN, TextureNet, etc.): pre-entrenados desde cero en texturas, no transferibles a otros dominios.

**Decisión sobre los 6 datasets:** los 6 datasets públicos de texturas (DTD, FMD, Outex13, CUReT, Soil, VisTex) cubren 4 tipos de texturas (naturales Web, materiales, controladas laboratorio, pequeñas) y son estándar en la literatura. En la versión V1 del manuscrito se incluyeron también GTOS-Mobile (outdoor scenes) y KTH-TIPS2-b (texturas controladas), pero se removieron en V2 por decisión del tutor para mantener el scope en texturas puras (Cap. 5.5). **Una limitación reconocida** es que no se incluyen texturas industriales, médicas, o satelitales — la generalización a esos dominios queda abierta (Cap. 6.6).

## 2.6. Resumen: gaps que esta tesis llena

Basado en la revisión, identificamos 5 brechas:

1. **No existe un estudio sistemático** de ≥10 extractores heterogéneos (clásicos + CNN + ViT + SSL) en texturas.
2. **No se ha evaluado GFS** como alternativa al prefix concat en este dominio.
3. **Falta cuantificación del balance costo-beneficio** de multi-extractor vs single.
4. **Falta análisis de transferibilidad** texturas→médicos.
5. **No se reportan resultados negativos** (qué NO funciona) con suficiente detalle.

La presente tesis aborda cada uno de estos gaps con experimentos controlados sobre 6 datasets y 17 extractores.
