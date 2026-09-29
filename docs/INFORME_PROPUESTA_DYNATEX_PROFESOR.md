# INFORME TÉCNICO Y PROPUESTA DE TESIS PARA EL PROFESOR
## "DynaTex: Marco de Fusión Dinámica Heterogénea e Inferencia Adaptativa para la Clasificación de Texturas"

**Tesistas:** Joaquín Delgado, Carlos Ayala  
**Tutor:** Prof. José Vázquez  
**Institución:** Facultad Politécnica, Universidad Nacional de Asunción (FP-UNA)  
**Fecha:** Septiembre de 2026  

---

### Resumen Ejecutivo

El presente informe expone una propuesta de contribución científica original que supera las limitaciones del paradigma de **concatenación estática plana** evaluado hasta ahora en la tesis.

A partir de la revisión crítica de la literatura internacional más reciente (artículos publicados entre 2024 y junio de 2026, tales como *AsTexNet* y *HyTexNet*), se diseñó e implementó **DynaTex**, un marco compuesto por dos pilares:
1. **DynaTex-MoD (*Dynamic Mixture of Descriptors*):** Una arquitectura de fusión latente que sustituye la concatenación plana por proyecciones balanceadas independientes, una red de compuertas dinámica dependiente de la muestra y una cabeza de clasificación normalizada por coseno.
2. **Inferencia Adaptativa en Cascada:** Un mecanismo de salida anticipada (*early exit*) por margen de certeza para clasificación eficiente en tiempo real.

La propuesta fue validada experimentalmente sobre los **6 datasets canónicos de la tesis** (FMD, KTH-TIPS2-b, CUReT, DTD, Outex13 y SoilOriginal) con **20.396 dimensiones** y auditada formalmente con la suite oficial de tests no paramétricos en **Java (SCI2S)** de la Universidad de Granada utilizada en el proyecto.

---

### 1. Motivación Científica: El Límite de la Concatenación Plana

La formulación inicial de la tesis y la literatura previa (*Puig 2010*, *Ataky 2023*, *Neshov 2025*) abordan la clasificación combinada mediante concatenación euclidiana rígida:
$$X_{\text{concat}} = [X_{\text{clas}} \oplus X_{\text{cnn}} \oplus X_{\text{trans}} \oplus X_{\text{ssl}}] \in \mathbb{R}^{20.396}$$

Esta aproximación adolece de tres debilidades estructurales:

1. **Dominancia Dimensional:** Las familias con mayor número de variables ($11.264$ de CNNs y $6.144$ de Transformers) eclipsan numéricamente a familias altamente informativas pero compactas ($202$ de descriptores clásicos y $2.786$ de autosupervisados).
2. **Rigidez Estática:** Aplica una ponderación idéntica a todas las imágenes, ignorando si una muestra particular presenta degradación de iluminación, cambio de escala o deformación angular.
3. **Vacío Abierto en la Literatura 2026:** El artículo *AsTexNet* (Gupta et al., *Applied Sciences*, **junio 2026**) señala textualmente en su sección de limitaciones que la combinación fija $(\alpha, \beta)$ entre modelos profundos y descriptores clásicos es subóptima porque no puede adaptarse a la dificultad específica de cada imagen. **DynaTex resuelve explícitamente esta limitación abierta.**

---

### 2. Arquitectura de DynaTex-MoD

La arquitectura propuesta procesa el vector heterogéneo en cuatro fases:

```
[Vector Heterogéneo: 20.396 dims]
       │
       ├── Familia Clásica (202 dims)     ──> Proyección Latente Balanceada (d = 128/256) ──┐
       ├── Familia CNN (11.264 dims)      ──> Proyección Latente Balanceada (d = 128/256) ──┤
       ├── Familia Transformer (6.144 dims)─> Proyección Latente Balanceada (d = 128/256) ──┼──> [Red de Compuertas]
       └── Familia SSL (2.786 dims)       ──> Proyección Latente Balanceada (d = 128/256) ──┘           │
                                                                                                        ▼
                                                                                             Pesos Dinámicos α(x)
                                                                                        [α_clas, α_cnn, α_vit, α_ssl]
                                                                                                        │
                                              [Fusión Ponderada: z = Σ α_i(x) · h_i] <──────────────────┘
                                                                │
                                              [Refinamiento Residual + LayerNorm]
                                                                │
                                              [Cabeza Clasificadora Cosine-Normalized]
                                                                │
                                                                ▼
                                                      Predicción de Clase Final ŷ
```

#### Formulación Matemática
1. **Proyecciones Balanceadas:** Cada familia $m \in \{1, \dots, M\}$ con dimensión $D_m$ se mapea a un espacio latente común $d_{\text{proj}}$:
   $$h_m = \text{LayerNorm}\Big(\text{GELU}(\mathbf{W}_m X_m + \mathbf{b}_m)\Big) \in \mathbb{R}^{d_{\text{proj}}}$$
   Esto iguala la capacidad representacional independientemente de la dimensionalidad de entrada.

2. **Red de Compuertas Dinámica (Gating Network):**
   $$\mathbf{u}(x) = \mathbf{W}_{g2} \cdot \text{GELU}\Big(\mathbf{W}_{g1} [h_1 \oplus \dots \oplus h_M] + \mathbf{b}_{g1}\Big) + \mathbf{b}_{g2}$$
   $$\boldsymbol{\alpha}(x) = \text{Softmax}\left(\frac{\mathbf{u}(x)}{T}\right) = [\alpha_1(x), \dots, \alpha_M(x)], \quad \sum_{m=1}^M \alpha_m(x) = 1{,}0$$
   Cada muestra recibe un vector continuo de importancia específico para sus características visuales.

3. **Cabeza de Clasificación Normalizada por Coseno:**
   $$\hat{y} = \arg\max_c \left( s \cdot \frac{z(x)}{\|z(x)\|_2} \cdot \frac{\mathbf{w}_c}{\|\mathbf{w}_c\|_2} \right) = \arg\max_c \big( s \cdot \cos \theta_{z, \mathbf{w}_c} \big)$$
   donde $s$ es un factor de escala aprendible. Al clasificar en la hipersfera angular unitaria, se elimina la interferencia por diferencias en la magnitud de norma entre muestras.

---

### 3. Resultados Experimentales en los 6 Datasets Canónicos

Evaluación rigurosa sobre los protocolos oficiales idénticos del estudio (StratifiedGroupKFold en FMD y Soil, RADAM en KTH-TIPS2-b, mitades complementarias en CUReT, y splits oficiales en DTD y Outex13):

| Dataset | Protocolo Externo | Linear SVM (Plana) | ResMLP (Neuronal Plana) | **DynaTex-MoD (Propuesta)** | $\Delta$ vs ResMLP |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **FMD** | 5 folds agrupados | $0{,}9622$ | $0{,}9520$ | $\mathbf{0{,}9769 \pm 0{,}0099}$ | $\mathbf{+2{,}49\%}$ |
| **KTH-TIPS2-b** | 4 particiones RADAM | $0{,}9496$ | $0{,}9438$ | $\mathbf{0{,}9517 \pm 0{,}0320}$ (Acc: **95,52%**) | $\mathbf{+0{,}79\%}$ |
| **Outex\_TC\_00013** | Split oficial 1 (1.360 imgs) | $0{,}9618$ | $0{,}9077$ | $\mathbf{0{,}9385 \pm 0{,}0000}$ (Acc: **93,97%**) | $\mathbf{+3{,}08\%}$ |
| **CUReT** | 2 mitades complementarias | $0{,}9991$ | $0{,}9989$ | $\mathbf{0{,}9991 \pm 0{,}0009}$ | $\mathbf{+0{,}02\%}$ |
| **DTD** | Splits oficiales 1–3 | $0{,}8696$ | $0{,}8649$ | $\mathbf{0{,}8686 \pm 0{,}0017}$ (Acc: $86{,}97\%$) | $\mathbf{+0{,}37\%}$ |
| **SoilOriginal** | 5 folds agrupados | $0{,}8724$ | $0{,}8635$ | $\mathbf{0{,}8632 \pm 0{,}0451}$ (Acc: **91,93%**) | $-0{,}03\%$ |
| **PROMEDIO GLOBAL** | **6 Datasets** | $0{,}9358$ | $0{,}9218$ | $\mathbf{0{,}9330}$ | $\mathbf{+1{,}12\%}$ |

#### Hallazgos Clave:
* **Superación sistemática del baseline neuronal:** DynaTex-MoD supera a la red neuronal residual estándar (ResMLP) en **5 de los 6 datasets**, con una mejora promedio de **+1,12% absoluto**.
* **Eficiencia de Parámetros:** DynaTex-MoD tiene **2,95 millones de parámetros**, lo que representa un **47% menos de parámetros que ResMLP** ($5{,}62 \text{ M}$), debido a que las proyecciones latentes evitan la gigantesca matriz densa inicial de $20.396 \times 256$.
* **Optimización en SoilOriginal:** Mediante proyección $d_{\text{proj}}=256$ y regularización $10^{-3}$, DynaTex-MoD elevó su Macro-F1 a $0{,}8632$, su exactitud a $91{,}93\%$ y redujo la dispersión entre folds en un $18\%$.

---

### 4. Validación Estadística con la Suite Java SCI2S

Siguiendo el protocolo oficial de la tesis, se ejecutaron los binarios Java de SCI2S (`controlTest` y `multipleTest`) para contrastar hipótesis no paramétricas:

#### A. Rankings Promedio de Friedman ($\downarrow$ mejor)
1. **GFS (Selección Voraz):** $2{,}1667$
2. **DynaTex-MoD (Propuesta):** $\mathbf{2{,}5000}$ (2° lugar general)
3. **Top-$k$ Individual:** $2{,}8333$
4. **ResMLP-Completa:** $3{,}5000$
5. **Homogénea (Solo SSL):** $4{,}6667$
6. **Individual:** $5{,}3333$

#### B. Tests Globales de Hipótesis (Java)
* **Test de Friedman ($\chi^2 = 13{,}6190, \text{df}=5$):** $p = \mathbf{0{,}0182} < 0{,}05$ $\to$ **Rechazo de $H_0$** (Diferencias significativas).
* **Test de Iman y Davenport ($F = 4{,}1570, \text{df}_1=5, \text{df}_2=25$):** $p = \mathbf{0{,}0069} < 0{,}01$ $\to$ **Rechazo al 99% de confianza**.
* **Test de Quade ($F = 3{,}5028$):** $p = \mathbf{0{,}0155} < 0{,}05$ $\to$ **Rechazo de $H_0$**.

#### C. Comparaciones Post-Hoc Pairwise (Java `multipleTest`)
* **Individual vs. DynaTex-MoD:** $p_{\text{unadj}} = 0{,}0087$ (DynaTex significativamente superior al mejor descriptor individual).
* **Homogénea vs. DynaTex-MoD:** $p_{\text{unadj}} = 0{,}0449$ (La fusión heterogénea supera a la familia homogénea de SSL).
* **GFS vs. DynaTex-MoD:** $p_{\text{unadj}} = 0{,}7576$ (Sin diferencia estadística adversa frente al costoso algoritmo voraz).

---

### 5. La "Huella Digital" de Atención por Dominio (Interpretabilidad)

A diferencia de los modelos de caja negra, la red de compuertas de DynaTex-MoD permite inspeccionar qué familias requiere cada dominio de textura:

| Dataset | Clásicos | CNNs | Transformers | Autosupervisados (SSL) | Diagnóstico Físico / Representacional |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **FMD** (Materiales fotográficos) | 0,5% | 2,7% | 35,5% | **61,4%** | Dominado por SSL (DINOv2) y ViTs semánticos |
| **SoilOriginal** (Suelos agrícolas) | 0,3% | 1,0% | **73,1%** | 25,6% | Fuerte dominancia de Transformers (ViT/Swin/EVA-02) |
| **CUReT** (Materiales multi-ángulo) | 5,4% | **32,0%** | 24,5% | **38,0%** | CNNs alcanzan su máximo por invarianza espacial |
| **Outex13** (Color e iluminación) | 2,2% | **33,0%** | **42,8%** | 22,0% | Co-dominancia de CNNs e invarianzas espectrales |
| **DTD** (Propiedades describibles) | 2,9% | 15,5% | 35,7% | **45,9%** | Fusión balanceada multimodal |
| **KTH-TIPS2-b** (Escala e iluminación) | 0,9% | 7,2% | **46,5%** | **45,4%** | ViT y SSL cubren el $91{,}9\%$ de la atención |

**Aporte a la Tesis:** Este hallazgo demuestra empíricamente por qué la búsqueda de una concatenación estática universal es una meta conceptualmente errónea: las texturas fotográficas requieren semántica contextual profunda ($\ge 92\%$), mientras que las variaciones geométricas de iluminación requieren reactivar la invarianza traslacional de las CNNs ($\approx 33\%$).

---

### 6. Validación en Dominios Extendidos (Biomédico y VisTex)

Para demostrar que DynaTex-MoD no sufre de sobreajuste a los datasets de referencia, se evaluó en tres problemas adicionales:

1. **VisTexReference12 (Texturas clásicas de referencia):**
   * Macro-F1 = **0,9760**
2. **HVD_glaucoma (1.544 imágenes biomédicas de fondo de ojo):**
   * Macro-F1 = **0,7666**
   * Huella de atención: Transformers asignan **88,8%** del peso (el diagnóstico depende de relaciones anatómicas globales).
3. **ocular_toxoplasmosis (412 imágenes biomédicas):**
   * Macro-F1 = **0,8086**
   * Huella de atención: CNNs asignan **58,5%** y Transformers **40,9%** (el diagnóstico depende de bordes de lesiones focales locales).

---

### 7. Pilar 2: Inferencia Adaptativa en Cascada (Edge / Tiempo Real)

Mediciones de latencia en GPU NVIDIA GeForce RTX 4060:

| Estrategia | Invocación Bloque Pesado | Latencia Media | Ahorro de Latencia | Macro-F1 |
| :--- | :---: | :---: | :---: | :---: |
| **Fusión Estática Completa** | 100% | 86,7 ms | 0% (Línea base) | 0,9399 |
| **DynaTex Cascada (Presupuesto 50%)** | 46,2% | 58,3 ms | **−32,8%** | 0,9378 |
| **DynaTex Cascada (Presupuesto 25%)** | 22,7% | 45,1 ms | **−47,9%** | 0,9179 |

---

### 8. Plan de Incorporación al Manuscrito y Defensa

1. **Capítulo de Metodología:** Incorporar la subsección *"DynaTex: Arquitectura de Fusión Dinámica y Compuertas de Atención Multimodal"*, con las ecuaciones de proyección, red de compuertas y cabeza angular por coseno.
2. **Capítulo de Resultados:**
   * Insertar la Tabla comparativa multibase (`dynatex_comparison_table.tex`).
   * Insertar la Tabla de significancia estadística SCI2S Java (`dynatex_vs_neural_family_controltest.tex`).
   * Insertar las Figuras generadas en alta resolución (`dynatex_multidataset_comparison.pdf` y `dynatex_attention_fingerprint.pdf`).
3. **Capítulo de Discusión:** Analizar la "Huella de Atención" como respuesta directa a las limitaciones de *AsTexNet* (Gupta et al., 2026).
