# FAQ Defensa — Decisiones Metodológicas

**Propósito:** Anticipar y responder preguntas críticas del tutor/tribunal sobre decisiones metodológicas del manuscrito.
**Manuscrito:** *Concatenación sistemática de descriptores visuales clásicos y modernos para clasificación de texturas*
**Autor:** Carlos Ayala & Joaquín Delgado · Tutor: José Vázquez · UNA-FP

---

## P1. ¿Por qué 17 extractores y no más, no menos?

**Pregunta esperada:** "¿Por qué 17 extractores? ¿No son muy pocos? ¿Por qué no incluyeron CLIP o MAE?"

**Respuesta estructurada:**

1. **Cobertura de familias:** 17 extractores cubren las 4 familias principales:
   - 5 clásicos (LBP, GLCM, Gabor, HOG, DRLBP)
   - 6 CNN (VGG16, ResNet-50/101, DenseNet-121, EfficientNet-B0, ConvNeXt V2-T)
   - 3 ViT (ViT-B/16, Swin-T, DeiT-S)
   - 3 DINOv2 (small, base, large)

2. **Diversidad > cantidad (evidencia experimental):** El "primer deep causa el mayor salto" (+0.48-0.51 F1) demuestra que agregar más modelos de la misma familia tiene retorno decreciente (Cap. 5 §5.4).

3. **CLIP/MAE excluidos por restricción de tiempo:** mencionados en Cap. 6 §6.6.1 como trabajo futuro:
   - "CLIP como baseline SSL adicional (no fue probado en esta tesis)"
   - MAE mencionado en Cap. 2 §2.1.3 como alternativa SSL, pero DINOv2 es el SOTA actual

4. **Decisión informada por literatura:** Cimpoi 2014, Sánchez 2013 usaron 2-3 extractores; nuestro benchmark es 5× más comprehensivo.

**Anclaje en manuscrito:**
- Cap. 1 §1.3 (gap en literatura: 10+ extractores)
- Cap. 3 §3.3 (lista de 17 extractores)
- Cap. 5 §5.4 (curva de saturación)
- Cap. 6 §6.6.1 (trabajo futuro CLIP/MAE)

---

## P2. ¿Por qué 6 datasets y no más?

**Pregunta esperada:** "¿Por qué solo 6 datasets? ¿Y Flickr Material original, ALOT, Brodatz?"

**Respuesta estructurada:**

1. **Cobertura de tipos:** Los 6 datasets cubren 4 tipos de texturas:
   - **Naturales** (DTD, VisTex)
   - **Materiales** (FMD)
   - **Controladas** (Outex13, KTH-TIPS2-b)
   - **Outdoor scenes** (GTOS-Mobile) — test de domain shift

2. **Cada dataset tiene un rol específico:**
   - **DTD** = discriminante (47 clases, F1 máximo ≈ 0.87)
   - **FMD** = mejor resultado (F1=0.973 GFS)
   - **Outex13** = muchas clases (68), bajo imgs/clase
   - **KTH-TIPS2-b** = saturado (control positivo)
   - **GTOS-Mobile** = domain shift (outdoor scenes)
   - **VisTex** = data-scarce (167 imgs, 19 clases)

3. **Integración con v3 (benchmark independiente):** 8 datasets totales si se considera la integración en `STEP1_COMBINED_MAX.csv` (incluye CUReT, Soil).

4. **Limitación reconocida en Cap. 6.5:** "Datasets limitados a texturas públicas — sin validación en texturas industriales, médicas, o naturales no-Web."

**Anclaje en manuscrito:**
- Cap. 1 §1.4 (H1, H2, H3 con cada dataset)
- Cap. 3 §3.2 (descripción de los 6 datasets)
- Cap. 4 §4.2 (resultados por dataset)
- Cap. 6 §6.5 (limitación reconocida)

---

## P3. ¿Por qué sin nested cross-validation? (pregunta más esperada)

**Pregunta esperada:** "¿Por qué no usaste nested CV? El GFS puede estar sobre-ajustado."

**Respuesta estructurada:**

1. **Limitación reconocida honestamente:**
   - **Cap. 5.8 (Limitación #1):** "Sin nested CV para GFS: el GFS actual usa el mismo split de 5-fold para seleccionar y evaluar. Esto introduce un sesgo optimista pequeño. Un nested CV (outer para evaluar, inner para GFS) sería más estricto pero ~5× más costoso. Esperaríamos un drop de ~1-2% F1 con nested CV."
   - **Cap. 6.5 (Limitación #1):** Mismo mensaje replicado.

2. **Trade-off documentado:**
   - **Pro:** nested CV sería 5× más costoso (computacional y temporalmente)
   - **Contra:** sin nested CV, hay optimism bias de ~1-2% F1
   - **Decisión:** priorizamos cobertura (17 extractores × 6 datasets × 5 estrategias) sobre rigor estadístico

3. **Mitigación parcial:** usamos paired t-test sobre los 5 folds (Cap. 4 §4.6ter y Cap. 5 §5.12) que muestra que las mejoras son estadísticamente significativas con effect sizes muy grandes (Cohen's d 1.7-6.5).

4. **Trabajo futuro en Cap. 6 §6.6.1:** "Nested CV para GFS (outer 5-fold para evaluar, inner 5-fold para buscar) — resolver el optimism bias"

**Anclaje en manuscrito:**
- Cap. 5 §5.8 (limitación #1)
- Cap. 6 §6.5 (limitación #1)
- Cap. 4 §4.6ter (stat tests como mitigación)
- Cap. 6 §6.6.1 (trabajo futuro)

**Respuesta de cierre sugerida:** "Reconocemos la limitación honestamente. Si el revisor la marca como Major, podemos correr nested CV en el siguiente round (~20 horas de cómputo)."

---

## P4. ¿Por qué removieron los datasets médicos?

**Pregunta esperada:** "¿Por qué removieron HVD_glaucoma y ocular_toxoplasmosis? ¿No pierden generalización clínica?"

**Respuesta estructurada:**

1. **Decisión del tutor** (directriz explícita): los datasets médicos fueron removidos por directriz del tutor en la versión V2.

2. **Reemplazo natural: GTOS-Mobile.** Este dataset es el sustituto natural para evaluar transferibilidad:
   - Linear probing da F1=0.03 (random) → demuestra el límite del transfer out-of-distribution
   - LoRA fine-tuning FIX el problema (F1=0.98) → demuestra que la transferibilidad se puede recuperar con adaptación

3. **Hallazgo más contraintuitivo:** El LoRA FIX de GTOS-Mobile es un resultado valioso, posiblemente más publicable que los datasets médicos (que eran locales y no comparables con SOTA).

4. **Limitación reconocida en Cap. 6.5:** "Datasets limitados a texturas públicas — sin validación en texturas industriales, médicas, o naturales no-Web."

5. **Trabajo futuro en Cap. 6 §6.6.2:** "Validación en texturas médicas (histopatología, radiómica)"

**Anclaje en manuscrito:**
- Cap. 1 §1.3 (gap de transferibilidad)
- Cap. 4 §4.2 obs 4 (GTOS-Mobile outlier)
- Cap. 5 §5.6 (caracterización de domain shift)
- Cap. 5.11.3 (LoRA en data-scarce = negativo)
- Cap. 6 §6.5 (limitación), §6.6.2 (trabajo futuro)

---

## P5. ¿Por qué SVM lineal y no una red neuronal?

**Pregunta esperada:** "¿Por qué SVM lineal y no MLP, Random Forest, o RBF?"

**Respuesta estructurada:**

1. **SVM lineal gana o empata en 5/5 datasets** con GFS subset (Cap. 5.11.6).

2. **Comparación experimental en Cap. 5.11.4:**
   - **Single extractor (1024 dim):** MLP-256 GANA (+0.08 a +0.11 F1)
   - **Multi-extractor concat (1500-10000 dim):** SVM GANA (-0.005 a -0.030 vs MLP)
   - **Interpretación:** con features pre-entrenados ya separables, MLP introduce overfitting en alta dim

3. **Ventajas del SVM lineal:**
   - 1 solo hiperparámetro (C=1.0) vs grid search de MLP
   - ~10× más rápido que MLP en alta dim
   - Estándar en feature fusion (Cimpoi 2014, Sánchez 2013)

4. **Robustez a sobreajuste:** con datos escasos (VisTex=167, GTOS-Mobile subsample=5K) y alta dim, SVM lineal regulariza naturalmente, mientras que MLP y RBF SVM tienden a sobreajustar (Cap. 5.11.6).

5. **Decisión deliberada:** "**SVM lineal se elige como el clasificador de la tesis**" (Cap. 5.11.6).

**Anclaje en manuscrito:**
- Cap. 3 §3.4 (clasificadores: SVM lineal principal + KNN secundario)
- Cap. 4 §4.7 (influencia del clasificador)
- Cap. 5 §5.11 (experimentos exploratorios con MLP)
- Cap. 5 §5.11.6 (decisión final)

---

## P6. ¿Por qué L2-normalización? ¿Qué pasa si no la aplicas?

**Pregunta esperada:** "¿Es necesaria la L2-normalización? ¿Qué pasa si no la aplicas?"

**Respuesta estructurada:**

1. **Esencial por escalas heterogéneas** (Cap. 3 §3.5.1):
   - LBP ≈ 0.7
   - GLCM ≈ 715
   - DINOv2 ≈ sqrt(768) = 27.7 (en L2)
   - Sin normalización, los embeddings de alta magnitud dominan la función de decisión del SVM

2. **Aplicada per-imagen antes de clasificar** (no en la extracción):
   - En cada fold, separadamente para train y test
   - Dentro del bucle de cross-validation
   - Esto evita data leakage (Cap. 3 §3.5.1)

3. **Fórmula:** $x_i^{norm} = \frac{x_i}{\|x_i\|_2}$

4. **Cuándo se aplica:** en cada fold, **separadamente** para train y test, **dentro** del bucle de cross-validation. Esto evita data leakage.

5. **Validación experimental:** sin L2-norm, el SVM lineal con features sin normalizar da F1 mucho más bajo (los embeddings GLCM/LBP dominan).

**Anclaje en manuscrito:**
- Cap. 3 §3.5.1 (L2-normalización)
- Cap. 4 §4.1 (protocolo, normalización aplicada)
- Cap. 4 §4.7 (influencia del clasificador)

---

## P7. ¿Por qué Greedy Forward Selection y no una estrategia más sofisticada?

**Pregunta esperada:** "¿Por qué GFS (greedy) y no beam search o simulated annealing?"

**Respuesta estructurada:**

1. **GFS es la contribución metodológica central** de la tesis (Cap. 6 §6.2 #2):
   - "GFS como estrategia sistemática que encuentra subconjuntos óptimos (2-6 extractores) que superan consistentemente al prefix concat con orden canónico."

2. **Comparación experimental en Cap. 4 §4.4.2:**
   - **FMD:** GFS 0.973 (2 ext) vs Prefix 0.962 (17 ext) → GFS gana con menos dims
   - **DTD:** GFS 0.868 (4 ext) vs Prefix 0.862 (17 ext) → GFS gana con menos dims
   - **VisTex:** GFS 0.923 (5 ext) — pico de +19.3% sobre linear probing

3. **Limitación reconocida (Cap. 5.8):** "GFS puede atascarse en mínimos locales. Es un algoritmo greedy, no óptimo global."

4. **Trabajo futuro (Cap. 5.8):** "Beam search o simulated annealing podrían explorar mejor el espacio de subsets."

5. **Por qué greedy es suficiente empíricamente:** En este problema específico, el espacio de subsets (2^17 = 131,072) es lo suficientemente pequeño para que GFS capture la mayoría del beneficio. La saturación ocurre alrededor de k=6-8 extractores.

**Anclaje en manuscrito:**
- Cap. 4 §4.4.2 (GFS tabla 4.3)
- Cap. 5 §5.2 (GFS > prefix concat)
- Cap. 5 §5.8 (limitación de GFS)
- Cap. 6 §6.2 (contribución central)
- Cap. 6 §6.6.1 (trabajo futuro: beam search, simulated annealing)

---

## P8. ¿Por qué linear probing y no fine-tuning?

**Pregunta esperada:** "¿Por qué linear probing y no fine-tuning? ¿No es el fine-tuning el estándar?"

**Respuesta estructurada:**

1. **Comparación experimental en Cap. 4 §4.3:**
   - **DTD, FMD, KTH-TIPS2-b:** Linear vs LoRA vs Last — diferencias <1% F1
   - **GTOS-Mobile:** Linear 0.031 (random) vs LoRA 0.980 (FIX) — domain shift
   - **VisTex:** Linear 0.730 vs LoRA 0.619 (peor) vs Last 0.811 (mejor)

2. **Validación con literatura SSL (Kumar et al. 2022):**
   - "Fine-Tuning can Distort Pretrained Features and Underperform Out-of-Distribution"
   - En datos suficientes (≥1K imgs/clase), linear probing es competitivo o superior

3. **Decisión informada:** Linear probing es el primer experimento (Cap. 1) y luego fine-tuning es el segundo (Cap. 4). El manuscrito cubre AMBAS estrategias, no solo linear.

4. **Limitación de LoRA en data-scarce:** VisTex con LoRA (F1=0.619) es peor que linear (F1=0.730) y Last (F1=0.811). En data-scarce, fine-tuning distorsiona features.

**Anclaje en manuscrito:**
- Cap. 4 §4.3 (comparación Linear vs LoRA vs Last)
- Cap. 5 §5.5 (linear probing competitivo con fine-tuning)
- Cap. 5 §5.6 (GTOS-Mobile requiere LoRA)
- Cap. 5 §5.11.3 (fine-tuning en data-scarce falla)

---

## P9. ¿Qué papel cumple DINOv2 si la contribución central es la concatenación?

**Pregunta esperada:** "Si DINOv2 obtiene buenos resultados, ¿por qué no usarlo solo?"

**Respuesta estructurada:**

1. **Evidencia experimental en Cap. 4 §4.2:**
   - DINOv2-B gana en 4/6 datasets (DTD=0.842, FMD=0.957, KTH-TIPS2-b=0.999, VisTex=0.734)
   - En promedio la familia DINOv2 supera a CNN/ViT supervisados en +0.05 a +0.10 F1

2. **Validación externa (Oquab et al. 2024):**
   - Paper original: "produce all-purpose features"
   - "supera a CLIP y OpenCLIP en tareas de visión downstream"
   - Confirmado empíricamente en texturas

3. **Confirmación cruzada en Cap. 4 §4.4.2:**
   - DINOv2-B + DINOv2-L es subset GFS óptimo en 2/5 datasets
   - **Hallazgo contraintuitivo:** los dos son complementarios, no redundantes

4. **Matización importante (Cap. 5 §5.6):**
   - GTOS-Mobile (outdoor scenes) requiere LoRA fine-tuning
   - DINOv2 NO es universalmente suficiente — depende del dominio

5. **Implicación práctica:** DINOv2 es una referencia individual fuerte, pero no reemplaza el análisis de concatenación. La evidencia principal muestra que la selección de representaciones complementarias mejora el balance entre F1, dimensionalidad y costo.

**Anclaje en manuscrito:**
- Cap. 4 §4.2 (observación 1: DINOv2 family domina)
- Cap. 4 §4.4.2 (DINOv2-B + DINOv2-L en GFS)
- Cap. 5 §5.1 (desempeño de descriptores individuales dentro del marco de combinación)
- Cap. 5 §5.2 (DINOv2-B + DINOv2-L complementarios)
- Cap. 5 §5.6 (GTOS-Mobile matiza el claim)

---

## Resumen: Preguntas × Anclajes

| # | Pregunta | Cap. principal | Veredicto de defensa |
|---|---|---|---|
| P1 | 17 extractores | Cap. 3 §3.3, Cap. 5 §5.4 | Cubierto por literatura y evidencia experimental |
| P2 | 6 datasets | Cap. 3 §3.2, Cap. 6 §6.5 | Cubierto, limitación reconocida |
| P3 | Sin nested CV | Cap. 5 §5.8, Cap. 6 §6.5 | Honestidad como fortaleza; mitigación con stat tests |
| P4 | Sin datasets médicos | Cap. 4 §4.2 obs 4, Cap. 5 §5.6 | Decisión del tutor; GTOS-Mobile como reemplazo |
| P5 | SVM lineal | Cap. 5 §5.11.4-§5.11.6 | Gana experimentalmente, decisión deliberada |
| P6 | L2-normalización | Cap. 3 §3.5.1 | Necesaria por escalas heterogéneas |
| P7 | GFS vs sofisticado | Cap. 4 §4.4.2, Cap. 5 §5.8 | Contribución central; limitación reconocida |
| P8 | Linear probing | Cap. 4 §4.3, Cap. 5 §5.5 | Cobertura completa (linear + fine-tune) |
| P9 | DINOv2 baseline | Cap. 5 §5.1, §5.2, §5.6 | Evidencia experimental + matización |

---

*Generado por: academic-research-skills:ars-plan (Chapter 4 del CHAPTER_PLAN_PRE_SUBMISSION.md)*
*9 preguntas × anclajes en manuscrito. Listo para defensa oral.*
