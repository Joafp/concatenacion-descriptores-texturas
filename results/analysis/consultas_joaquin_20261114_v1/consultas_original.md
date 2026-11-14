# Consultas de Carlos para Joaquín — paper Top-k directo vs activación por margen

Fecha: 2026-11-14

Joaco, estoy escribiendo el paper «Concatenación Top-k de descriptores para
clasificar texturas: comparación del uso directo y la activación por margen».
La decisión del equipo es no correr experimentos nuevos y escribir solo con lo
que ya está en el repo. Para eso me faltan explicaciones o datos que solo vos
tenés (sección A). La sección B lista experimentos que pidió la revisión
simulada; quedan fuera de esa decisión salvo que el equipo los acuerde.

## Archivos de referencia

| Qué | Ruta |
|---|---|
| Borrador del paper (LaTeX, formato Elsevier CAS) | `carlos/main.tex` |
| PDF compilado del borrador | `carlos/main_topk_margen.pdf` |
| Revisión por pares simulada (decisión: revisión mayor) | `carlos/REVISION_PARES_TOPK_v1.md` |
| Bibliografía corregida | `carlos/references.bib` |

Las referencias a líneas de `carlos/main.tex` corresponden a la versión del
2026-11-14.

## Cómo responder

- Escribí la respuesta debajo de cada **Respuesta:** en este mismo archivo y
  hacé commit. Si algo ya está documentado, alcanza con la ruta y la línea.
- Si respondés con un número, indicá el archivo de donde sale y cómo se calcula.
- No edites `carlos/main.tex`; yo incorporo las respuestas.
- No corras nada de la sección B sin acordarlo antes con el equipo.

---

## A. Dudas que no requieren correr nada

### A1. Soil: Top-4 con SVM da distinto en el panel y en la evaluación estática

- **Evidencia:**
  - Panel: `results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv`, fila `SoilOriginal,svm,Top-4`, `local_mean_split_f1 = 0.8594`.
  - Estática: `results/exploratory/k_sweep/soil_original/k_sweep.csv`, `classifier=svm`, `k=4`, media de 3 semillas × 5 folds = 0.8864.
  - En el paper: `carlos/main.tex:605`.
- **Pregunta:** ¿de dónde sale la diferencia de 0,027? En concreto:
  - ¿El panel usa, por fold, las mismas listas de 4 bloques que la columna `selected` de `k_sweep.csv`?
  - ¿Coinciden la normalización y el escalado? El panel usa estadísticas congeladas del entrenamiento.
  - ¿Coinciden las semillas?
- **Necesito:** la causa en 1–3 líneas y cuál de los dos valores corresponde informar como Top-4 en Soil.

**Respuesta:**

### A2. Piloto físico: cosenos bajos aunque coinciden las predicciones

- **Evidencia:** `results/exploratory/fsc_tex/cascade_physical_paired_benchmark.json`. El coseno mínimo entre los embeddings extraídos en el piloto y los almacenados es −0,0707 en CUReT y 0,0085 en Soil, pero las rutas y predicciones coinciden con el caché. En el paper: `carlos/main.tex:541`.
- **Pregunta:**
  - ¿Por qué ocurre? ¿Son pocas imágenes, o hay una diferencia de preprocesamiento (resize, crop, color)?
  - ¿Puedo informar el piloto de los seis datasets, o hay que excluir CUReT y Soil?
- **Necesito:** la explicación y, si existe, cuántas imágenes por dataset tienen coseno < 0,99.

**Respuesta:**

### A3. KTH-TIPS2-b en la cascada

- **Evidencia:**
  - `results/exploratory/topk_cascade/kth_tips2b/` y `results/exploratory/topk_cascade/README.md`, que describe el experimento original y los controles online corregidos.
  - `docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md:79-94`.
  - En el paper (`carlos/main.tex:380`) excluí KTH de las pruebas por ser «una variante archivada no reconciliada con el control Top-k corregido», así que N=5.
- **Pregunta:**
  - ¿Qué difiere exactamente entre la variante archivada de KTH y el control Top-k corregido?
  - ¿Las filas KTH de `results/exploratory/topk_cascade/cheap_stage_selected_primary22/rows.csv` pueden considerarse reconciliadas?
  - Si no, ¿está bien informar KTH solo descriptivamente y usar N=5 en las pruebas?
- **Por qué importa:** con KTH, la cascada queda arriba de Top-k (0,9345 frente a 0,9341). Sin KTH queda apenas abajo (0,9325 frente a 0,9329). El resumen del paper depende de esto.

**Respuesta:**

### A4. ¿Cuáles son las 94 corridas canónicas del panel?

- **Evidencia:** hay 126 `frozen_decisions.json` repartidos en:
  - `results/analysis/overnight_f1_latency_20261028/jobs/`
  - `results/analysis/overnight_quality_resume_20261029_v1/jobs/`
  - `results/analysis/blocker_resolution_20261101/` (`queue_v1`, `soil_pending_v1`)
  - `results/exploratory/local_external_followup_20261028/`
  - `results/exploratory/local_external_panel_20261028/`

  `reconciliation_full_panel_20261104_v1` resume 94.
- **Pregunta:** ¿cuáles son las 94 carpetas que entran en la reconciliación?
- **Necesito:** la ruta del manifiesto o la lista de carpetas de trabajo. Con eso calculo el percentil 95 de latencia desde los `online/online_calls.csv` (columna `ms`).

**Respuesta:**

### A5. Perfil de costos de la cascada

- **Evidencia:** `docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md:62-68`. DTD, FMD, CUReT y Soil usan tiempos medidos en Outex como proxy; KTH tiene tiempos propios. En el paper: `carlos/main.tex:370`.
- **Pregunta:** ¿existe un perfil de latencias propio para cada dataset, o lo dejo declarado como proxy?
- **Necesito:** la ruta, o «no hay».

**Respuesta:**

### A6. Memoria de GPU

- **Pregunta:** ¿se registró la memoria de GPU máxima con los modelos cargados para Top-4, `Adaptive-selection-margin` y Completa-22 en el panel?
- **Necesito:** la ruta, o «no registrado».

**Respuesta:**

### A7. Matriz principal y GFS: ¿qué se puede citar?

- **Evidencia:**
  - `carlos/main.tex:368`: Individual y Completa-22 salen de la «matriz principal del proyecto».
  - El k de la cascada se hereda de GFS (k entre 1 y 8, mediana 5; solo 5 de 27 condiciones tienen k=4).
- **Pregunta:** ¿hay un documento citable para la matriz principal y para el procedimiento GFS, como un capítulo de la tesis o un preprint? Si no lo hay, ¿cuál es el archivo de resultados fuente de Individual y Completa-22?
- **Necesito:** las rutas del capítulo o documento y del CSV fuente.

**Respuesta:**

### A8. ¿Cómo se eligieron las candidatas de la cascada?

- **Evidencia:** `carlos/main.tex:283`. Las etapas baratas candidatas son ResNet-50, SigLIP-B, BEiTv2-B y ConvNeXt V2-T (en KTH solo ResNet-50 y BEiTv2-B), y la grilla es q ∈ {0,25; 0,50; 0,75}. Ya está documentado que la tolerancia de 0,005 se fijó después de ver resultados exploratorios (`docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md:125`).
- **Pregunta:** ¿la lista de cuatro etapas baratas y la grilla de q se fijaron antes de mirar resultados externos, o también después?
- **Necesito:** «antes» o «después», con la fuente si la hay.

**Respuesta:**

### A9. Top-4 con ResMLP corrido en otro equipo

- **Evidencia:** `carlos/main.tex:368` dice que Top-4 se corrió en otro equipo y que con ResMLP eso introduce variación propia del dispositivo.
- **Pregunta:** ¿en qué equipo (GPU o CPU, versión de torch)? ¿Hay alguna estimación de esa variación, por ejemplo una condición corrida en ambos equipos?
- **Necesito:** hardware, versiones y la diferencia medida, o «no medida».

**Respuesta:**

### A10. DeepLumina

- **Evidencia:** en `comparison_by_dataset.csv`, DeepLumina figura con `scientific_status_reference = requires_review_solver_nonconvergence`.
- **Pregunta:** ¿sigue pendiente la revisión por no convergencia? ¿Lo incluyo en la tabla de estado del arte con una nota, o lo saco?

**Respuesta:**

### A11. Verificar cálculos que hice yo desde los JSON archivados

Estos números no estaban en ningún resumen del repo; los calculé yo y están en el paper:

- **Control aleatorio de la cascada:**
  - Fuente: `results/exploratory/topk_cascade/*/exact_archive/`.
  - Resultado: el margen supera al escalamiento aleatorio con igual cantidad de imágenes en 27/27 condiciones, en cada q.
  - Wilcoxon exacto bilateral sobre las 6 medias por dataset: p = 0,0312; con Holm, 0,0938.
- **Cascada sin KTH:** 0,9325 frente a 0,9329 de Top-k directo, y Friedman p = 0,4518 (ver A3).

**Pregunta:** ¿te dan lo mismo?

**Respuesta:**

---

## B. Experimentos que pidió la revisión (no correr sin acuerdo del equipo)

Están en orden de importancia. **B1 es el único que cambia lo que el paper
puede afirmar.** Hoy ninguna tabla compara Top-4 directo con Top-4 activado
por margen: la cascada reutiliza la Top-k archivada con k interno, y la política
del panel rescata con subconjuntos de cuatro bloques del ensamble de diversidad,
no con Top-4. La revisión lo marca como el problema más grave.

### B1. Cascada con Top-4 fijo

- **Entrada:** las 27 condiciones con SVM y semilla 42 de la cascada actual. Etapa cara: Top-4 por fold, tomado de `results/exploratory/k_sweep/<dataset>/k_sweep.csv`, columna `selected` con `classifier=svm`, `seed=42` y `k=4`.
- **Protocolo:** el mismo de `scripts/run_cheap_stage_selected_cascade.py` (las mismas etapas baratas, la misma grilla de q, los márgenes OOF agrupados en el entrenamiento externo y la misma regla de ruta), cambiando solo la etapa cara a Top-4. Incluye el control aleatorio con la misma cantidad de imágenes y 100 repeticiones, como en KTH.
- **Salida sugerida:** `results/exploratory/topk_cascade/top4_fixed_primary22/rows.csv`, con las columnas de `cheap_stage_selected_primary22/rows.csv` y además la macro-F1 media del control aleatorio.
- **Costo:** con embeddings en caché debería ser barato.

### B2. Compuerta con otra medida de confianza

- Con las mismas predicciones guardadas, comparar el margen s(1) − s(2) con el puntaje máximo s(1) y con la entropía del softmax de los puntajes. Los umbrales se fijan por cuantil, para comparar con la misma fracción escalada.
- **Por qué:** el único control actual es el aleatorio, y cualquier medida de confianza le gana.

### B3. Cascada con ResMLP

- Mismo protocolo, con el margen tomado de los logits de ResMLP. Hoy la comparación central es solo con SVM.

### B4. Opcional: Top-4 más `rgb_ngram_svd` (5 bloques)

- Está pendiente en `results/exploratory/k_sweep/README.md:64`. El ranking del barrido usó 21 bloques, así que Top-4 nunca pudo elegir el bloque de color.

---

## C. Lo que calculo yo (no hace falta que lo hagas)

- Friedman y Holm con solo los tres métodos del paper (Individual, Completa-22 y Top-4), desde `results/analysis/selection_stats/`. La familia actual incluye 8 métodos que el paper no muestra.
- Macro-F1 de la etapa barata sola por dataset, desde los `*_predictions.json` de `cheap_stage_selected_primary22/`.
- Percentil 95 de latencia del panel, cuando respondas A4.

---

## D. Errores que encontré en archivos tuyos

### D1. `paper/chapters/05_resultados.tex:220`: factor de aceleración

El texto dice que `Adaptive-selection-margin` reduce el tiempo «entre 5,6× y
12,2× frente a Top-4/Ens-diversidad». En Soil no se cumple. Valores calculados
desde `results/analysis/reconciliation_full_panel_20261104_v1/comparison_by_dataset.csv`:

| Dataset | Clasificador | Margen (ms) | Top-4 (ms) | × vs Top-4 | Ens-diversidad (ms) | × vs Ens |
|---|---|---:|---:|---:|---:|---:|
| CUReT | ResMLP | 30,5 | 268,4 | 8,8 | 395,1 | 13,0 |
| CUReT | SVM | 36,8 | 270,7 | 7,3 | 404,0 | 11,0 |
| DTD | ResMLP | 47,6 | 267,5 | 5,6 | 366,4 | 7,7 |
| DTD | SVM | 54,4 | 334,0 | 6,1 | 411,4 | 7,6 |
| FMD | ResMLP | 36,4 | 258,6 | 7,1 | 373,5 | 10,3 |
| FMD | SVM | 38,6 | 269,0 | 7,0 | 364,5 | 9,4 |
| KTH-TIPS2-b | ResMLP | 32,2 | 260,1 | 8,1 | 366,4 | 11,4 |
| KTH-TIPS2-b | SVM | 31,0 | 260,4 | 8,4 | 367,5 | 11,9 |
| Outex13 | ResMLP | 21,6 | 263,8 | 12,2 | 349,4 | 16,1 |
| Outex13 | SVM | 40,3 | 265,4 | 6,6 | 358,2 | 8,9 |
| **Soil** | ResMLP | 48,3 | 78,2 | **1,6** | 208,1 | 4,3 |
| **Soil** | SVM | 38,5 | 71,0 | **1,8** | 204,9 | 5,3 |

Corrección propuesta: «entre 1,6× y 12,2× frente a Top-4 (entre 5,6× y 12,2×
sin Soil, cuya Top-4 ya es liviana) y entre 4,3× y 16,1× frente a
Ens-diversidad». No verifiqué la cifra de 30× a 72× frente a Completa-22.

### D2. `paper/articulo/borrador_profesor/references.bib`: dos entradas con autores y títulos incorrectos

Están corregidas en `carlos/references.bib`:

- `gupta2026hytexnet`: Gupta, Vandana; Mishra, Ashish; Shrivastava, Nishant. «HyTexNet: Percentile-guided local encoding and deep feature fusion for enhanced texture classification». *Knowledge-Based Systems* 338, 115482 (2026).
- `chang2024cellnn`: Chang, Mingzhe; Ji, Luping; Zhu, Jiewen. «Multi-scale LBP fusion with the contours from deep CellNNs for texture classification».

Si la tesis usa ese mismo `.bib`, conviene corregirlo también.
