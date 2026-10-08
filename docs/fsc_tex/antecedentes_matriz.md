# Matriz de Antecedentes y Frontera Científica (FSC-Tex)

**Fecha:** 8 de octubre de 2026  
**Documento de referencia:** `docs/PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md`  
**Objetivo:** Mapear con precisión la literatura existente en *Active Feature Acquisition* (AFA) y clasificación de texturas para delimitar qué ha sido resuelto y cuál es el aporte específico defendible de esta tesis.

---

## 1. Literatura de Adquisición Activa de Características (AFA)

| Trabajo / Fuente | Enfoque Principal | Aporte Teórico Relevante | Limitación Declarada en el Artículo Original | Consecuencia y Posicionamiento para FSC-Tex |
| :--- | :--- | :--- | :--- | :--- |
| **EDDI** (Ma et al., *ICML 2019*) | Adquisición basada en información mutua con VAE (*Partial VAE*). | Selecciona la siguiente característica que maximiza la reducción de entropía condicional. | Asume costos homogéneos, características tabulares/escalares y no evalúa extractores de visión pesados. | La selección adaptativa no es nueva; FSC-Tex opera sobre **bloques extractores completos**, no variables aisladas. |
| **AFA Survey** (Erickson et al., *arXiv 2026*) | Taxonomía comprensiva de AFA (modelos generativos, RL, regresión). | Formaliza el problema como un MDP (*Markov Decision Process*) con costos de adquisición. | La gran mayoría de los trabajos evalúa datasets médicos/tabulares con costos teóricos o unitarios. | Posiciona a FSC-Tex dentro de la categoría de AFA basada en valor/riesgo, no como una invención aislada. |
| **Explainability-driven Ranking** (Güney et al., *ICML 2025*) | Políticas secuenciales a partir de ordenamientos locales guiados por explicabilidad. | Demuestra que el orden de adquisición debe depender de la muestra individual. | No incorpora paradas tempranas con latencia real de hardware ni extractores heterogéneos. | Refuerza la hipótesis H4 (dependencia de la imagen), pero FSC-Tex modela utilidad predictiva y costo físico. |
| **BRiG-AFA** (Preprint, agosto 2026) | Regresión supervisada de riesgo futuro mediante recurrencia de Bellman. | Aprende el valor futuro $Q(s, a)$ sin requerir aprendizaje por refuerzo libre de modelo inestable. | **Limitación explícita (Secciones 3 y 7):** Asume horizonte fijo y **costos unitarios/idénticos**; deja costos reales y parada para trabajo futuro. | **Antecedente algorítmico más directo:** FSC-Tex extiende la recurrencia de Bellman a **bloques heterogéneos con costos medidos en GPU y parada explícita (`STOP`)**. |
| **SynAFA** (Preprint, septiembre 2026) | Adquisición dependiente del estado considerando sinergias de pares. | Formula la ganancia conjunta para capturar complementariedad entre atributos. | Desconexión documentada entre criterios de teoría de la información y la utilidad predictiva del clasificador downstream. | FSC-Tex mide directamente la **utilidad predictiva downstream** ($L_S - L_{S \cup a}$) en lugar de sustitutos puramente informacionales. |
| **Learning-to-Measure** (Kobayashi et al., *ICML 2026*) | Adquisición guiada por reducción de incertidumbre con observaciones parciales. | Usa cotas de incertidumbre para decidir si realizar una medición adicional. | Asume mediciones de sensores con costo constante y linealidad en la observación. | La incertidumbre es un componente del estado, no el aporte exclusivo de FSC-Tex. |
| **Gated Multimodal Units** (Arevalo et al., *2017*) | Compuertas dinámicas para ponderar modalidades o representaciones. | Modulación dependiente de la muestra mediante compuertas continuas. | Requiere que todas las modalidades estén precalculadas antes de evaluar la compuerta. | La ponderación dinámica (tipo DynaTex) es un antecedente de fusión; no ahorra latencia de extracción. |

---

## 2. Literatura Específica en Clasificación de Texturas

| Trabajo / Publicación | Paradigma de Fusión | Descriptores Evaluados | Limitación Explícita / Brecha Abierta | Posicionamiento de FSC-Tex |
| :--- | :--- | :--- | :--- | :--- |
| **AsTexNet** (Gupta et al., *Applied Sciences*, junio 2026) | Concatenación ponderada fuera de línea de CNNs + Clásicos. | DWT, GLCM, LBP combinados con ResNet/EfficientNet. | Señala textualmente que la combinación estática con pesos fijos $(\alpha, \beta)$ es subóptima al no adaptarse a la muestra. | FSC-Tex resuelve la limitación adaptando no solo los pesos sino la **adquisición física de los bloques por imagen**. |
| **HyTexNet** (Gupta et al., *KBS*, 2026) | Fusión híbrida multimodelo profunda. | Modelos convolucionales y de atención preentrenados. | Partición aleatoria en KTH-TIPS2-b (fuga entre muestras físicas) y extracción obligatoria de todos los modelos. | FSC-Tex mantiene partición estricta sin fuga (LOPO físico) y permite omisión real de modelos pesados. |
| **Neshov et al.** (*Electronics*, 2025) | Concatenación estática de CNNs + ViTs para clasificación de suelos. | ResNet, ViT y extractores supervisados. | Extrae siempre la totalidad de los modelos; alta latencia en inferencia para muestras triviales. | Demuestra la fuerza de las combinaciones profundas pero evidencia la necesidad de un mecanismo de parada temprana. |
| **Scabini et al.** (*Pattern Recognition / JImaging*, 2024) | Redes complejas y grafos de atributos de textura. | Medidas topológicas y descriptores estadísticos. | Alto costo de cálculo en descriptores de grafos complejos sin filtrado condicional. | Justifica la inclusión de descriptores clásicos y estructurales dentro del registro de 22 bloques. |
| **RGB Pixel N-grams** (2023) | Estadísticas de co-ocurrencia de color y textura de bajo nivel. | N-gramas espaciales sobre píxeles RGB con proyección SVD. | Requiere ajuste de proyección SVD que debe confinarse al conjunto de entrenamiento para evitar fuga. | Se incluye como el bloque 22 (`rgb_ngram_svd`), ajustado estrictamente en los folds de entrenamiento. |

---

## 3. Delimitación Precisa del Aporte de FSC-Tex

Para preservar la integridad científica y evitar falacias ARS, FSC-Tex **NO** afirma:
* Haber inventado la adquisición activa de características (AFA existe formalmente desde hace décadas).
* Haber inventado los objetivos de Bellman para reducción de riesgo (provienen de la literatura de MDP y BRiG-AFA).
* Haber inventado la noción de complementariedad o de compuertas (Arevalo et al., 2017).

**Lo que FSC-Tex SÍ investiga y propone defender:**
1. **Formulación sobre bloques completos heterogéneos:** Las acciones de adquisición no son escalares abstractos, sino invocaciones a extractores pesados de visión (desde LBP de 54 dims hasta VGG16 de 4.096 dims o ViT-B).
2. **Costos incrementales físicamente medidos en GPU ($\Delta t$):** Modela y mide el tiempo real considerando operaciones compartidas (ej. conversión a escala de grises para clásicos, normalización común) en lugar de asumir costos unitarios o abstractos.
3. **Decisión de parada (`STOP`) y utilidad bidireccional:** El objetivo de optimización castiga activamente el perjuicio de clasificación ($L_S < L_{S \cup a}$) y balancea explícitamente el costo de computación frente al riesgo de error.
4. **Regla de ruta directa previa al test:** Detecta antes de inferencia si la cascada compensará su sobrecosto fijo frente a una ruta estática de costo comparable, evitando penalizaciones de latencia en dominios donde el subconjunto base ya es óptimo.
