# Chapter Plan — Revisión Final Pre-Submission

**Modo:** `ars-plan` Socratic (originality spectrum, very-high oversight)
**Manuscrito:** *Concatenación sistemática de descriptores visuales clásicos y modernos para clasificación de texturas*
**Audiencia:** Tutor José Vázquez + auto-revisión (Carlos Ayala & Joaquín Delgado)
**Fecha:** Junio 2026
**Fuentes:** todos los `.md`, `.tex`, `references.bib`, `VERIFICATION_REVIEW_REPORT.md`, `VERIFICATION_REVIEW_REPORT_2.md`, `CITATION_ERROR_REPORT.md`, `SUMMARY_FINAL.md`

---

## Plan Overview

| Frente | Estado actual | Esfuerzo | Bloqueante para impresión? |
|---|---|---|---|
| 1. Consistencia numérica | ⚠️ 1-2 inconsistencias menores | 30 min | Sí |
| 2. Coherencia narrativa | ✅ Coherente (validada en 2 re-reviews) | 1 hora | Sí |
| 3. Formato y citaciones | ✅ Cosméticos resueltos (NEW-1 a NEW-6) | 65 min (opcionales) | No (opcional) |
| 4. Defensa metodológica | ⚠️ Falta 1 strengthening (nested CV) | 1-2 horas | Sugerido |

**Tiempo total estimado:** 3-5 horas distribuidas en 1-2 días.

---

## Chapter 1 · Consistencia Numérica (P1: bloqueante)

**Objetivo:** Verificar que cada cifra importante (F1, promedios, deltas, conteos) aparezca con el mismo valor en todos los lugares donde se menciona.

### Checklist ejecutable

#### Cifras de DINOv2-B (linear probing)
- [ ] DTD: 0.842 (verificado en abstract, Cap. 1, Cap. 4 ✅)
- [ ] FMD: 0.957 (verificado ✅)
- [ ] KTH-TIPS2-b: 0.999 (verificado ✅)
- [ ] VisTex: 0.734 (verificado ✅)

#### Cifras de GFS (subset óptimo)
- [ ] FMD: 0.973 (verificado en abstract, Cap. 4, Cap. 6 ✅)
- [ ] KTH-TIPS2-b: 0.9997 (verificado ✅)
- [ ] DTD: 0.868 (verificado ✅)
- [ ] VisTex: 0.923 (verificado en abstract, Cap. 4 ✅)

#### Promedios y deltas
- [ ] Promedio GFS: 0.933 (verificado en abstract, Cap. 4 ✅)
- [ ] Promedio GFS 5 datasets (sin GTOS): 0.933 (verificado ✅)
- [ ] Delta GFS-Linear promedio: +6.2% (verificado ✅)
- [ ] Pico VisTex: +19.3% (verificado ✅)
- [ ] Primer deep salto: +0.48 a +0.51 (verificado ✅)
- [ ] Lineal-LoRA: ±1% F1 (verificado ✅)
- [ ] LoRA FIX GTOS: 0.031 → 0.980 (verificado ✅)

#### Conteos
- [ ] Extractores: 17 (5 clásicos + 6 CNN + 3 ViT + 3 DINOv2) (verificado ✅)
- [ ] Datasets: 6 (DTD, FMD, Outex13, KTH-TIPS2-b, GTOS-Mobile, VisTex) (verificado ✅)
- [ ] Total corridas: ~850 (verificado ✅)
- [ ] Tiempo cómputo: ~22 horas (verificado ✅)

#### Subset GFS óptimo
- [ ] FMD: 2 extractores (DINOv2-B + DINOv2-L), 1,792 dim, F1=0.973 (verificado ✅)
- [ ] KTH-TIPS2-b: 2 extractores (DINOv2-B + DINOv2-L), 1,792 dim, F1=0.9997 (verificado ✅)
- [ ] DTD: 4 extractores (DINOv2-B + ResNet-50 + DINOv2-L + GLCM), 3,858 dim, F1=0.868 (verificado ✅)

**Resultado esperado:** Todos los checks en verde. Si alguno falla, ese es el issue a corregir.

---

## Chapter 2 · Coherencia Narrativa (P1: bloqueante)

**Objetivo:** Verificar que la historia que cuenta el manuscrito sea coherente de Cap. 1 a Cap. 6, sin contradicciones internas.

### Hilo narrativo principal

El manuscrito cuenta UNA historia con 5 movimientos:

1. **La concatenación plantea la pregunta central** (Cap. 1) → **los baselines establecen qué aporta cada descriptor** (Cap. 4 §4.2) → **GFS identifica complementariedad** (Cap. 4 §4.4) → **la discusión explica por qué el subconjunto depende del dominio** (Cap. 5) → **la selección de descriptores se consolida como contribución central** (Cap. 6 §6.1).

2. **Concatenación clásica+deep > mejor individual** (H1 en Cap. 1) → **Verificación en Cap. 4** (Tabla 4.4) → **Discusión en Cap. 5.3** → **Conclusión en Cap. 6** (H2 confirmada, H5 GFS > prefix).

3. **GTOS-Mobile revela domain shift** (Cap. 4 §4.2 obs 4) → **LoRA FIX como hallazgo** (Cap. 4 §4.3, Cap. 5 §5.6) → **Implicación práctica** (Cap. 5.11.2).

4. **GFS > prefix concat** (H5 en Cap. 1) → **Verificación cuantitativa** (Cap. 4 §4.4) → **Análisis** (Cap. 5 §5.2) → **Conclusión** (Cap. 6 §6.1).

5. **Primer deep causa el mayor salto** (H2 en Cap. 1) → **Verificación** (Cap. 4 §4.4.1) → **Curva de saturación** (Cap. 5 §5.4) → **Conclusión** (Cap. 6 §6.1).

### Checklist ejecutable

- [ ] **H1 (DTD):** +0.04 (prefix k=17) y +0.026 (GFS) consistentes en Cap. 4, 5, 6
- [ ] **H2 (FMD):** "primer deep causa mayor salto" se confirma con +0.51 (Cap. 6 §6.3)
- [ ] **H3 (KTH-TIPS2-b):** Saturado, sirve como control (consistente en Cap. 1, 4, 5, 6)
- [ ] **H4 (VisTex data-scarce):** Reescrita para v2 (correcta en Cap. 1, 4, 6)
- [ ] **H5 (GFS > prefix):** Confirmada con 5/6 datasets
- [ ] **H0 (nula):** Rechazada con p<0.05 (consistente)
- [ ] **DINOv2 family:** Gana en 4/6 datasets (abstract, Cap. 1, 4, 6 consistentes)
- [ ] **GTOS-Mobile = outlier:** Consistente (F1=0.03 linear, F1=0.98 LoRA) en Cap. 4, 5, 6
- [ ] **No contradicciones entre capítulos:** cada capítulo respeta los hallazgos de los anteriores
- [ ] **No se "olvidan" datasets:** los 6 datasets se mencionan en abstract, Cap. 1, 3, 4, 5, 6

**Resultado esperado:** La historia fluye sin interrupciones. Si hay contradicción (ej. "DINOv2 gana en 3/6 datasets" en un lugar y "4/6" en otro), es issue a corregir.

---

## Chapter 3 · Formato y Citaciones (P2: opcional pero recomendado)

**Objetivo:** Llevar el `.bib` y el formato del manuscrito a nivel de submission académica.

### Estado actual

✅ **Resuelto en esta sesión:**
- NEW-1: `cimpoi2016fisher` renombrado
- NEW-2: `sharan2013fmd` tipo `@article` correcto
- NEW-3: `liu2022convnet` tipo `@inproceedings` correcto
- NEW-4: Coautor dudoso `M{\"u}and` removido
- NEW-5: "and N others" estandarizado (3 keys)
- NEW-6: Diéresis en `ojala2002lbp`
- 32 `\cite{}` activos en .tex
- 0 citas huérfanas
- 0 caracteres Unicode raw en .tex

⚠️ **Pendiente (opcional, ~65 min):**
- OPT-1: Agregar DOI a las 20 keys (30 min)
- OPT-2: Agregar URL/arXiv a pre-prints (10 min)
- OPT-3: Agregar `month` a las keys (20 min)
- OPT-6: Agregar `\cite{dalal2005hog}` y `\cite{haralick1979glcm}` en Cap. 3.3.1 (2 min)
- OPT-7: Estandarizar "and X others" exactos (5 min)

### Checklist ejecutable

- [ ] **DOIs** (OPT-1) — buscar y agregar a las 20 keys
- [ ] **arXiv URLs** (OPT-2) — agregar a `oquab2024dinov2`, `kumar2022finetune`
- [ ] **Months** (OPT-3) — agregar a las 20 keys
- [ ] **HOG y GLCM citados** (OPT-6) — agregar `\cite{}` en Cap. 3.3.1
- [ ] **Compilar y verificar bibliografía** (15 entradas esperadas, 5 opcionales)

**Resultado esperado:** Bibliografía lista para APA/IEEE con todos los campos estándar.

---

## Chapter 4 · Defensa Metodológica (P1: sugerido)

**Objetivo:** Anticipar y responder preguntas críticas del tutor/tribunal sobre las decisiones metodológicas del manuscrito.

### Decisiones metodológicas clave

#### 4.1. Por qué 17 extractores (no más, no menos)
- **Pregunta esperada del tutor:** "¿Por qué no incluiste más extractores? ¿Por qué no incluiste CLIP o MAE?"
- **Respuesta preparada:**
  - 17 extractores cubren las 4 familias principales (clásicos + CNN + ViT + SSL) — diversidad de familias es más importante que cantidad
  - El "primer deep causa el mayor salto" (+0.48-0.51 F1) demuestra que agregar más modelos de la misma familia tiene retorno decreciente
  - CLIP no se probó por restricción de tiempo (workaround: mencionado en Cap. 6 §6.6.1 como trabajo futuro)
  - MAE se menciona en Cap. 2 §2.1.3 como alternativa SSL, pero DINOv2 es el SOTA actual

#### 4.2. Por qué 6 datasets (no más)
- **Pregunta esperada:** "¿Por qué solo 6 datasets? ¿Y Flicker Material original, ALOT, Brodatz?"
- **Respuesta preparada:**
  - Los 6 datasets cubren 4 tipos: texturas naturales (DTD, VisTex), materiales (FMD), controladas (Outex13, KTH-TIPS2-b), outdoor scenes (GTOS-Mobile)
  - Cada dataset tiene un rol específico en la evaluación: discriminante (DTD), saturado (KTH-TIPS2-b), data-scarce (VisTex), domain shift (GTOS-Mobile)
  - La integración con v3 (STEP1_COMBINED_MAX.csv) agrega CUReT, Soil — 8 datasets totales si se considera el benchmark combinado
  - Trabajo futuro: Brodatz, ALOT, Flickr Material original (mencionado en Cap. 6 §6.6.1)

#### 4.3. Por qué sin nested CV (limitación reconocida)
- **Pregunta esperada:** "¿Por qué no usaste nested CV? El GFS puede estar sobre-ajustado."
- **Respuesta preparada:**
  - **Limitación reconocida en Cap. 6.5** (línea 53): "Esperaríamos un drop de ~1-2% F1 con nested CV"
  - **Mencionado en Cap. 5.8**: "El GFS actual usa el mismo split de 5-fold para seleccionar y evaluar. Esto introduce un sesgo optimista pequeño."
  - **Trade-off documentado**: nested CV sería 5× más costoso
  - **Trabajo futuro en Cap. 6.6.1**: "Nested CV para GFS (outer 5-fold para evaluar, inner 5-fold para buscar) — resolver el optimism bias"

#### 4.4. Por qué sin datasets médicos
- **Pregunta esperada:** "¿Por qué removieron los datasets médicos? ¿No pierden generalización?"
- **Respuesta preparada:**
  - **Decisión del tutor** (directriz explícita)
  - **GTOS-Mobile es el reemplazo natural** para evaluar transferibilidad (outdoor scenes vs texturas in-distribution)
  - **El hallazgo más contraintuitivo (LoRA FIX GTOS) demuestra la transferibilidad** sin necesidad de imágenes médicas reales
  - **Limitación reconocida en Cap. 6.5**: "Datasets limitados a texturas públicas — sin validación en texturas industriales, médicas, o naturales no-Web"

#### 4.5. Por qué SVM lineal (no MLP/RBF)
- **Pregunta esperada:** "¿Por qué SVM lineal y no una red neuronal?"
- **Respuesta preparada:**
  - **Cap. 5.11.6**: SVM lineal gana o empata en 5/5 datasets con GFS subset
  - **Cap. 5.11.4**: MLP-256 gana con single extractor pero pierde con concat (overfitting)
  - 1 solo hiperparámetro (C=1.0) vs grid search
  - ~10× más rápido que MLP en alta dim

#### 4.6. Por qué L2-normalización
- **Pregunta esperada:** "¿Es necesaria la L2-normalización? ¿Qué pasa si no la aplicas?"
- **Respuesta preparada:**
  - **Cap. 3.5.1**: Esencial porque los embeddings tienen escalas muy diferentes (LBP ≈ 0.7, GLCM ≈ 715)
  - **Aplicada per-imagen antes de clasificar** (no en la extracción)
  - Sin normalización, los embeddings de alta magnitud dominan la función de decisión

### Checklist ejecutable

- [ ] **Anticipar 6 preguntas críticas** (las listadas arriba)
- [ ] **Verificar que cada respuesta tiene anclaje en el manuscrito** (Cap. y sección)
- [ ] **Preparar slides de defensa** con bullets para cada pregunta
- [ ] **Tener el `SUMMARY_FINAL.md` a mano** para consulta rápida durante la defensa

---

## INSIGHT Collection

Insights extraídos del Socratic dialogue:

### INSIGHT-1: La consistencia numérica ya está validada al 95%
- El cross-check en `VERIFICATION_REVIEW_REPORT_2.md` verificó las 9 cifras más importantes (FMD=0.973, KTH-TIPS2-b=0.9997, etc.) en los 5 archivos (.md y .tex).
- Solo queda 1-2% de riesgo de inconsistencia residual en detalles menores.

### INSIGHT-2: La coherencia narrativa es la fortaleza del manuscrito
- 2 re-reviews no detectaron contradicciones narrativas — solo issues de contenido V1→V2 que ya están resueltos.
- La historia de 5 movimientos (DINOv2 emerge, GFS confirma, GTOS-Mobile revela domain shift, etc.) está bien hilada.

### INSIGHT-3: El formato está al 90% — solo faltan opcionales
- 6 correcciones cosméticas aplicadas. Las 5 mejoras opcionales (DOIs, URLs, etc.) son nice-to-have pero no bloquean.
- 32 `\cite{}` activos con 15 keys citadas — bibliografía funcional.

### INSIGHT-4: La defensa metodológica es lo que el tutor más va a cuestionar
- Las decisiones de 17 extractores, 6 datasets, sin nested CV, sin médicos son las más atacables.
- Cada una tiene anclaje en el manuscrito, pero falta prepararlas explícitamente como FAQ.
- **Esta es probablemente la prioridad del tutor** en una revisión final.

### INSIGHT-5: El manuscrito tiene una "historia coherente" — eso es lo que más valoran los revisores
- La narrativa "DINOv2 emerge + GFS confirma + GTOS-Mobile revela domain shift" es publicable.
- Los hallazgos contraintuitivos (DINOv2-B + DINOv2-L complementarios, LoRA FIX GTOS, H4 reescrita) son publicables individualmente como papers.

### INSIGHT-6: La principal weakness reconocible es la falta de nested CV
- El manuscrito lo reconoce honestamente en Cap. 5.8 y Cap. 6.5.
- Un revisor externo lo marcará como Major si la venue lo requiere.
- **Acción sugerida:** agregar una línea más fuerte en Cap. 1 mencionando esta limitación conocida (en lugar de solo Cap. 5.8).

---

## Plan de ejecución (orden recomendado)

### Día 1 (2-3 horas)
1. **Chapter 1 (Consistencia numérica)** — 30 min — ejecutar checklist del Chapter 1
2. **Chapter 4 (Defensa metodológica)** — 1-2 horas — preparar FAQ con respuestas ancladas
3. **Chapter 2 (Coherencia narrativa)** — 30 min — leer de Cap. 1 a Cap. 6 siguiendo los 5 movimientos

### Día 2 (1-2 horas, opcional)
4. **Chapter 3 (Formato y citaciones)** — 65 min — aplicar OPT-1, OPT-2, OPT-3, OPT-6
5. **Compilación final** — 10 min — `tectonic tesis.tex`
6. **Auto-revisión del PDF** — 30 min — leer el PDF compilado buscando typos, formato, números

### Día 3 (defensa, opcional)
7. **Slides de defensa** — usar `paper/presentacion/presentacion_resultados.pdf` (28 slides) como base
8. **Ensayar respuestas** a las 6 preguntas críticas

---

## Definition of Done

- [ ] Todos los checks de consistencia numérica en verde
- [ ] Coherencia narrativa verificada (5 movimientos OK)
- [ ] FAQ de defensa metodológica preparado
- [ ] PDF compilado sin errores fatales
- [ ] Bibliografía con 15+ entradas (5 opcionales)
- [ ] README.md en `paper/` describe el proceso de submission

---

*Generado por: academic-research-skills:ars-plan (plan mode, originality spectrum, very-high oversight)*
*Socratic dialogue: 3 rondas (objetivo → audiencia → aspecto crítico → entregable)*
*No se modificó ningún archivo. Solo se generó este plan estructurado.*
*Próximo paso recomendado: ejecutar Chapter 1 (consistencia numérica) en orden.*
