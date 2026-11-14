# Consultas de Carlos para Joaquín — paper Top-k directo vs activación por margen

Fecha: 2026-11-14

Joaco, estoy escribiendo el paper «Concatenación Top-k de descriptores para
clasificar texturas: comparación del uso directo y la activación por margen».
La decisión del equipo es no correr experimentos nuevos y escribir solo con lo
que ya está en el repo. Para eso me faltan explicaciones o datos que solo vos
tenés (sección A). La sección B lista experimentos que pidió la revisión
simulada; quedan fuera de esa decisión salvo que el equipo los acuerde.


## Respuestas y material actualizado — 14-11-2026

Se respondieron **A1–A11**, se anotó el estado de **B1–B4** y se verificaron
**D1–D2**. Esta entrega audita registros existentes: **cero experimentos nuevos**.
La revisión de texto del 13-11 aplicó ocho cambios ARS y pasó 26 pruebas de
software; esas pruebas no son nuevas corridas científicas.

- [Tesis actualizada: 82 páginas](../paper/tesis.pdf) y [fuente](../paper/tesis.tex).
- [Informe de revisión aplicada](../docs/fsc_tex/REVISION_ARS_TOPK_MARGEN_2026-11-13.md).
- [Auditoría de estas respuestas](../results/analysis/consultas_joaquin_20261114_v1/summary.json): 295 fuentes con hashes, sin fits ni nuevas mediciones.
- [Lista exacta de 94 trazas canónicas](../results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv).

El borrador `carlos/main.tex`, su PDF y su bibliografía se conservan tal como
se recibieron de `fbfe2b5`; estas respuestas son para incorporarlas después.
Las tareas de C siguen asignadas a Carlos. En B, el panel completo de Top-4
por margen y los otros controles específicos siguen pendientes; las cinco
coincidencias archivadas de cuatro bloques se identifican como evidencia parcial.

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

**Coinciden las listas y las semillas en las 15 condiciones.** Con los embeddings guardados, `quality/metrics.csv` del panel reproduce exactamente los 15 F1 del barrido: media **0,8863893405**. La media **0,8594040214** aparece al extraer nuevamente características online con las mismas cabezas congeladas: diferencia −0,0269853191. La discrepancia queda localizada en la representación online; su causa primaria todavía no está diagnosticada.

Ambas rutas usan L2 por bloque (`src/run_confirmatory_nested.py:61–64,90`; `scripts/benchmark_local_single_image.py:162`). El escalado del único miembro Top-4 divide sus scores por un escalar positivo y conserva `argmax` (`src/local_external_panel.py:26–27`, `src/ensemble_scoring.py:22–33`); no explica esta diferencia. Las semillas de partición/cabeza son 42/123/2026. La extracción online además usa raíz 20261028 y una semilla por imagen/bloque; no consta identidad con la semilla original de extracción histórica.

Las ocho condiciones cuyo F1 cambia contienen `vit_b16`; las siete sin ese bloque conservan F1. Los diagnósticos guardados muestran diferencias de ViT de aproximadamente 0,133–0,150, sin aislar pooler, preprocesamiento o versión como causa. **Informar 0,8864 en la tabla estática y 0,8594 cuando se empareje calidad con latencia online**, con etiquetas explícitas; no intercambiar las cifras.

Evidencia por semilla/pliegue, listas y F1: [soil_top4_alignment_15.csv](../results/analysis/consultas_joaquin_20261114_v1/soil_top4_alignment_15.csv). Fuentes: `results/exploratory/k_sweep/soil_original/k_sweep.csv`, filtros `classifier=svm,k=4`, y `results/analysis/blocker_resolution_20261101/soil_pending_v1/jobs/SoilOriginal_svm_s{seed}_f{fold}/quality/{frozen_decisions.json,metrics.csv}`; online en `full_panel_online_v1/condition_summary.csv`.

### A2. Piloto físico: cosenos bajos aunque coinciden las predicciones

- **Evidencia:** `results/exploratory/fsc_tex/cascade_physical_paired_benchmark.json`. El coseno mínimo entre los embeddings extraídos en el piloto y los almacenados es −0,0707 en CUReT y 0,0085 en Soil, pero las rutas y predicciones coinciden con el caché. En el paper: `carlos/main.tex:541`.
- **Pregunta:**
  - ¿Por qué ocurre? ¿Son pocas imágenes, o hay una diferencia de preprocesamiento (resize, crop, color)?
  - ¿Puedo informar el piloto de los seis datasets, o hay que excluir CUReT y Soil?
- **Necesito:** la explicación y, si existe, cuántas imágenes por dataset tienen coseno < 0,99.

**Respuesta:**

La discrepancia está concentrada en **ViT-B/16**, no diagnosticada causalmente como resize, crop, color o pooler. Pocas imágenes limitan el alcance del piloto, pero no explican por sí solas que el vector de una misma imagen cambie. La nota inicial sobre pooler quedó como hipótesis histórica; `docs/fsc_tex/AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md:61,74–75` conserva el diagnóstico pendiente.

La fuente de los cosenos es `results/exploratory/fsc_tex/physical_six_20261012/<dataset>/parity.json`, no `cascade_physical_paired_benchmark.json`: este último contiene solo DTD y no registra cosenos.

| Dataset | Imágenes únicas | Algún bloque con coseno <0,99 | Pares temporales |
|---|---:|---:|---:|
| DTD | 47 | 0 | 141 |
| FMD | 10 | 0 | 30 |
| CUReT | 61 | **61** | 183 |
| Outex13 | 68 | 0 | 204 |
| Soil | 7 | **7** | 21 |
| KTH-TIPS2-b | 11 | 0 | 33 |

Cálculo: por cada objeto de `parity.json`, contar `any(c < 0.99 for c in row["cosine"].values())`, comprobando índices únicos. En CUReT y Soil solo falla `vit_b16`; mínimos −0,0707095712 y 0,0084876344. Sus `status.json` dicen `measured_with_fidelity_discrepancies`, aunque las concordancias de rutas y predicciones sean 1.

Se pueden presentar **los seis como piloto histórico descriptivo**, identificando estas reservas; CUReT/Soil no respaldan una afirmación de fidelidad completa respecto al caché ni de seis datasets físicamente validados. Son 204 imágenes, con tres repeticiones y 612 pares, no 612 imágenes independientes. KTH además conserva su reserva de procedencia. [Conteos auditados](../results/analysis/consultas_joaquin_20261114_v1/physical_parity_by_dataset.csv).

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

Hay dos correcciones distintas. La corrección temporal omite ResNet-50 en la ruta Top-k directo (`results/exploratory/topk_cascade/README.md:72–95`, trazas `kth_tips2b/online_fair_topk/`). La corrección de selección rehace el control Top-k con agrupación interna por muestra física, `ngram22_beitv2_innergrp_sample_v1`; no cambia automáticamente el subconjunto heredado por la cascada antigua.

**Las cuatro filas de `cheap_stage_selected_primary22` siguen sin reconciliarse con ese control corregido.** Los `_result.json` apuntan por `source_archive` y SHA al `exact_archive` antiguo. `topk_repro_delta=0` reproduce ese origen, no el control nuevo.

| Partición | k antiguo | F1 antiguo | k corregido | F1 corregido |
|---|---:|---:|---:|---:|
| 1 | 2 | 0,9941021143 | 8 | 0,9813869925 |
| 2 | 1 | 0,9039989016 | 5 | 0,9044029160 |
| 3 | 2 | 0,9884259255 | 8 | 0,9725562081 |
| 4 | 1 | 0,8736003166 | 1 | 0,9194970486 |
| Media | | 0,9400318145 | | 0,9444607913 |

Fuentes: `results/extensions/kth_tips2b/{ngram22_beitv2,ngram22_beitv2_innergrp_sample_v1}/topk_individual_control/nested_fold_results.csv`, filtros SVM/42, ordenados por `outer_fold`. Cambian las cuatro listas; en la cuarta se sustituye ViT por BEiTv2. [Comparación exacta](../results/analysis/consultas_joaquin_20261114_v1/kth_old_vs_corrected.csv).

Hoy **sí existen las cuatro filas corregidas**; las notas antiguas y vacíos KTH del ledger quedaron desactualizados. Eso no modifica la procedencia de la cascada. La media 0,9445000370 de la cascada seleccionada y 0,9444607913 del control nuevo son próximas numéricamente, sin demostrar identidad. Mantener KTH descriptivo y **N=5 datasets / 23 condiciones** para esos contrastes es coherente con la auditoría, declarando la exclusión posterior motivada por procedencia.

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

La fuente canónica es `results/analysis/blocker_resolution_20261101/full_panel_online_v1/provenance.json`. Guardé la lista exacta de **94 carpetas/CSV**, sus identificadores, SHA-256 y conteos en [canonical_panel_calls_94.csv](../results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv).

Selección reproducible: tomar las keys terminadas en `/online_calls.csv` y excluir **únicamente** `results/analysis/blocker_resolution_20261101/queue_v1/jobs/DTD_svm_s42_f6_additional/online/online_calls.csv`. Hay 95 keys antes de excluir esa observación adicional. No exigir `/online/online_calls.csv`, porque dos fuentes FMD canónicas están en `local_batch1_20261028/...` y `local_batch1_followup_20261028/.../resmlp_online/`.

Verifiqué 94 IDs únicos, cinco métodos por condición y **362.640 llamadas primarias**; las 9.400 adicionales permanecen aparte. Identidad: `status.json` hermano del CSV, campos `dataset,classifier,seed,outer_fold`. La reserva DTD/SVM original se conserva. El consolidador es `scripts/consolidate_overnight_online_panel.py:29–82,192–211`.

`full_panel_online_v1/condition_summary.csv` ya contiene `p95_ms` por condición/método. Para un p95 reunido por dataset/política usar las llamadas canónicas que correspondan; **promediar percentiles no produce el percentil reunido**. No recalculé tu tarea de C.

### A5. Perfil de costos de la cascada

- **Evidencia:** `docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md:62-68`. DTD, FMD, CUReT y Soil usan tiempos medidos en Outex como proxy; KTH tiene tiempos propios. En el paper: `carlos/main.tex:370`.
- **Pregunta:** ¿existe un perfil de latencias propio para cada dataset, o lo dejo declarado como proxy?
- **Necesito:** la ruta, o «no hay».

**Respuesta:**

**Dejar declarado el proxy en esta cascada.** Los 27 `_result.json` de `cheap_stage_selected_primary22` registran 23 usos del perfil `results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison/primary22_e2e/Outex_official1_primary22_online_train_components.json` y cuatro del perfil `results/exploratory/topk_cascade/kth_tips2b/timing/latency_KTHTIPS2b_s42_official1_n30.json`. En el perfil proxy, ViT puede tomar el costo KTH cuando no supera el criterio de fidelidad Outex.

Fuentes de implementación: `scripts/report_cost_aware_topk.py:21–25,40–60,118–121` y `scripts/run_cheap_stage_selected_cascade.py:140–156,214–220`. Los conteos de `cost_profile` quedaron en [summary.json](../results/analysis/consultas_joaquin_20261114_v1/summary.json).

Existen mediciones propias **parciales** DTD/FMD (`adaptive_descriptor_pilot/official_protocol_50pct/latency_DTD_s42_official1_n50.json` y `adaptive_descriptor_pilot/latency_FMD_s42_f0_n50.json`, solo ResNet/BEiTv2), otra suite DTD y el piloto de rutas en seis datasets. No constituyen seis perfiles completos y homogéneos de 22 bloques ni fueron los perfiles utilizados por este consolidado. No sustituir retrospectivamente los costos de la evaluación histórica.

### A6. Memoria de GPU

- **Pregunta:** ¿se registró la memoria de GPU máxima con los modelos cargados para Top-4, `Adaptive-selection-margin` y Completa-22 en el panel?
- **Necesito:** la ruta, o «no registrado».

**Respuesta:**

**Pico de memoria por política: no registrado.** Hay snapshots globales de `nvidia-smi` con la unión de extractores de las cinco políticas residente; no son máximos ni medidas separadas para Top-4, Adaptive y Completa-22.

Fuente: `scripts/benchmark_local_single_image.py:56–58,90–91,115–143,184,201,223`. Ejemplo: `results/analysis/blocker_resolution_20261101/soil_pending_v1/jobs/SoilOriginal_svm_s42_f1/online/status.json`, campos `gpu_after_loading` y `gpu_after` (6.884 MiB), con GPU compartida. No utilizar esos snapshots como memoria máxima atribuible a cada política.

### A7. Matriz principal y GFS: ¿qué se puede citar?

- **Evidencia:**
  - `carlos/main.tex:368`: Individual y Completa-22 salen de la «matriz principal del proyecto».
  - El k de la cascada se hereda de GFS (k entre 1 y 8, mediana 5; solo 5 de 27 condiciones tienen k=4).
- **Pregunta:** ¿hay un documento citable para la matriz principal y para el procedimiento GFS, como un capítulo de la tesis o un preprint? Si no lo hay, ¿cuál es el archivo de resultados fuente de Individual y Completa-22?
- **Necesito:** las rutas del capítulo o documento y del CSV fuente.

**Respuesta:**

Hay un **borrador de tesis verificable del proyecto**, no un preprint/DOI que deba inventarse: [PDF vigente](../paper/tesis.pdf), `paper/chapters/03_metodologia.tex` (ranking y control Top-k), `paper/chapters/05_resultados.tex:5–13` (matriz estática). La explicación más explícita de GFS está en `paper/articulo/borrador_profesor/main.tex:241–249` y `src/run_confirmatory_nested.py:262`: máximo ocho bloques, parada tras dos mejoras consecutivas <0,001 y devolución del mejor paso histórico. Puede citarse el repositorio y su commit como material del proyecto, sin presentarlo como artículo revisado.

CSV originales, enumerados en `scripts/build_primary22_beitv2_paper.py:23–28`:

```text
results/confirmatory/ngram22_beitv2/nested_fold_results.csv
results/extensions/outex13_official1360/ngram22_beitv2/nested_fold_results.csv
results/extensions/soil_original/ngram22_beitv2/nested_fold_results.csv
results/extensions/kth_tips2b/ngram22_beitv2/nested_fold_results.csv
```

Filtrar `method=best_individual`, `full_concat` o `gfs` y emparejar `dataset,classifier,seed,outer_fold`; métrica `macro_f1`. Completa-22 tiene 22 bloques y 20.652 dimensiones nominales. Esta matriz tiene 47 condiciones por clasificador; el ledger de la cascada tiene 27 SVM/42 y otra variante KTH de referencia. No intercambiar ambos paneles.

### A8. ¿Cómo se eligieron las candidatas de la cascada?

- **Evidencia:** `carlos/main.tex:283`. Las etapas baratas candidatas son ResNet-50, SigLIP-B, BEiTv2-B y ConvNeXt V2-T (en KTH solo ResNet-50 y BEiTv2-B), y la grilla es q ∈ {0,25; 0,50; 0,75}. Ya está documentado que la tolerancia de 0,005 se fijó después de ver resultados exploratorios (`docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md:125`).
- **Pregunta:** ¿la lista de cuatro etapas baratas y la grilla de q se fijaron antes de mirar resultados externos, o también después?
- **Necesito:** «antes» o «después», con la fuente si la hay.

**Respuesta:**

**Antes de evaluar externamente esta variante con base seleccionada; después de haber observado benchmarks en pilotos anteriores.** El commit `a8de0dd` (10-10-2026, 17:24:49 −03) incorporó el protocolo/código con las cuatro bases y q={0,25;0,50;0,75}; `cfb7605` (18:01:21 −03) incorporó sus resultados. `scripts/run_cheap_stage_selected_cascade.py:4–16` declara esa congelación para esta variante.

`docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md:54–57,121–127` y `docs/fsc_tex/REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md:9` documentan exposición previa y decisiones exploratorias, incluido destacar q=0,75 post hoc en el piloto anterior. La secuencia registrada no demuestra preregistro ni test virgen, ni que las cuatro identidades se escogieran independientemente de todo el desarrollo previo. Conviene mantener la etiqueta exploratoria.

### A9. Top-4 con ResMLP corrido en otro equipo

- **Evidencia:** `carlos/main.tex:368` dice que Top-4 se corrió en otro equipo y que con ResMLP eso introduce variación propia del dispositivo.
- **Pregunta:** ¿en qué equipo (GPU o CPU, versión de torch)? ¿Hay alguna estimación de esa variación, por ejemplo una condición corrida en ambos equipos?
- **Necesito:** hardware, versiones y la diferencia medida, o «no medida».

**Respuesta:**

El mensaje histórico del commit **`0a165894ec4134ad0a0603922eb19265a7a9daa7`**, que incorporó `results/exploratory/resmlp/k_sweep/` el 18-10-2026, registra **GPU para DTD, KTH-TIPS2-b, CUReT y Outex; CPU para Soil y FMD**.

No encontré modelo específico de GPU/CPU ni versión histórica de torch vinculados a esos CSV. Tampoco una comparación controlada del mismo entrenamiento en ambos equipos: **variación entre equipos no medida**. Los datos de RTX 4060/torch de pilotos posteriores no identifican el equipo del barrido. Puede declararse la heterogeneidad de ejecución como límite, sin cuantificar o atribuir causalmente una diferencia al dispositivo.

### A10. DeepLumina

- **Evidencia:** en `comparison_by_dataset.csv`, DeepLumina figura con `scientific_status_reference = requires_review_solver_nonconvergence`.
- **Pregunta:** ¿sigue pendiente la revisión por no convergencia? ¿Lo incluyo en la tabla de estado del arte con una nota, o lo saco?

**Respuesta:**

**Sigue pendiente la revisión científica.** La auditoría registra 46/47 condiciones terminadas, avisos de no convergencia en las 46, y 1.653/2.441 clasificadores binarios en 10.000 iteraciones. DTD sigue 9/10, sin media completa.

Fuentes: `results/analysis/deeplumina_convergence_review_20261104_v1/summary.json`, `deeplumina_stationarity_review_20261104_v1/INFORME.md:37` y `reconciliation_full_panel_20261104_v1/summary.json:6`. Puede conservarse como **adaptación local descriptiva sujeta a revisión**, con nota explícita y DTD incompleto. No presentarla como réplica validada ni emplear esas diferencias como prueba definitiva de superioridad sobre el paper. No ejecuté reintentos ni cambié tolerancias.

### A11. Verificar cálculos que hice yo desde los JSON archivados

Estos números no estaban en ningún resumen del repo; los calculé yo y están en el paper:

- **Control aleatorio de la cascada:**
  - Fuente: `results/exploratory/topk_cascade/*/exact_archive/`.
  - Resultado: el margen supera al escalamiento aleatorio con igual cantidad de imágenes en 27/27 condiciones, en cada q.
  - Wilcoxon exacto bilateral sobre las 6 medias por dataset: p = 0,0312; con Holm, 0,0938.
- **Cascada sin KTH:** 0,9325 frente a 0,9329 de Top-k directo, y Friedman p = 0,4518 (ver A3).

**Pregunta:** ¿te dan lo mismo?

**Respuesta:**

**Sí, coinciden, separando dos archivos experimentales.** Recalculé desde los registros guardados, sin volver a ejecutar modelos. Primero media por condición dentro de cada dataset y luego media equiponderada entre datasets.

| q | Margen > media aleatoria | Media margen (6 datasets) | Media aleatoria | W | p exacto bilateral | Holm, familia de 3 q |
|---:|---:|---:|---:|---:|---:|---:|
| 0,25 | 27/27 | 0,911170087 | 0,867445201 | 0 | 0,03125 | 0,09375 |
| 0,50 | 27/27 | 0,929972422 | 0,887685987 | 0 | 0,03125 | 0,09375 |
| 0,75 | 27/27 | 0,933827568 | 0,907726844 | 0 | 0,03125 | 0,09375 |

Esto corresponde al **piloto original con ResNet-50 fijo**: `*/exact_archive/*_topk_cascade.json`, claves `budgets[].target_budget`, `adaptive.macro_f1`, `random_same_count_mean_macro_f1` y `random_repeats=100`. «27/27» significa superar la media de las cien repeticiones, no necesariamente cada repetición. No trasladar esos controles a la variante que elige la base.

Para **`cheap_stage_selected_primary22`**, las medias de cinco datasets sin KTH son **0,9325057587** (seleccionada) y **0,9329024087** (directo); diferencia −0,0003966499. Con seis, descriptivamente: 0,9345048051 y 0,9340906430. Para los **cuatro métodos** seleccionada/ResNet/directo/Completa-22 y las cinco medias emparejadas: Friedman χ²=2,6326530612, **p=0,4517937790**. Completa sale del ledger `results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv`, columna `full_22_macro_f1`; no traté sus vacíos KTH como una media completa.

[Recálculo y estimando](../results/analysis/consultas_joaquin_20261114_v1/a11_statistics.json), [81 filas originales por condición y q](../results/analysis/consultas_joaquin_20261114_v1/random_control_original_81.csv) y [cinco medias por método](../results/analysis/consultas_joaquin_20261114_v1/selected_cascade_five_dataset_means.csv). El no rechazo con N=5 no acredita equivalencia ni no inferioridad; las 27 condiciones no son 27 dominios independientes.

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

**Estado auditado (14-11-2026): pendiente como panel nuevo completo.** No existe una ejecución completa equivalente de las 27 condiciones con Top-4 fijado de antemano y sus cien controles aleatorios. Sí se identificaron **cinco condiciones** cuyo rescate archivado tiene cuatro bloques y coincide con el Top-4 del barrido (DTD 8/10, FMD folds 2/3 y CUReT A→B). Sus predicciones directas/condicionales están comparadas en [top4_margin_subset.json](../results/analysis/topk_margin_rewrite_20261113_v1/top4_margin_subset.json) y en la tesis. Es evidencia parcial por identidad de bloques, no identidad de todos los ajustes ni cumplimiento íntegro de B1. No lancé corridas nuevas.

### B2. Compuerta con otra medida de confianza

- Con las mismas predicciones guardadas, comparar el margen s(1) − s(2) con el puntaje máximo s(1) y con la entropía del softmax de los puntajes. Los umbrales se fijan por cuantil, para comparar con la misma fracción escalada.
- **Por qué:** el único control actual es el aleatorio, y cualquier medida de confianza le gana.

**Estado auditado (14-11-2026): no localizado como panel pareado y auditado de las tres compuertas bajo ese protocolo.** El control aleatorio existente de A11 pertenece al piloto ResNet-50. No demuestra que margen supere a puntuación máxima o entropía. No ejecuté B2 ni asumí disponibles todas las puntuaciones OOF necesarias para calibrarlo.

### B3. Cascada con ResMLP

- Mismo protocolo, con el margen tomado de los logits de ResMLP. Hoy la comparación central es solo con SVM.

**Estado auditado (14-11-2026): pendiente para la misma comparación de cascada archivada.** Las 27 condiciones del contraste central son SVM. El panel online sí tiene políticas con ResMLP, pero `Adaptive-selection-margin` rescata con miembros del ensamble y no acredita esta misma cascada Top-k con margen de logits. No ejecuté B3.

### B4. Opcional: Top-4 más `rgb_ngram_svd` (5 bloques)

- Está pendiente en `results/exploratory/k_sweep/README.md:64`. El ranking del barrido usó 21 bloques, así que Top-4 nunca pudo elegir el bloque de color.

**Estado auditado (14-11-2026): pendiente como control Top-4 fijo + N-gramas.** Existen ablaciones de biblioteca con/sin N-gramas y reselecciones GFS/Top-k, que son otros experimentos. No las conté como concatenar los cuatro bloques fijados más `rgb_ngram_svd`, ni ejecuté B4.

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

**Respuesta (14-11-2026):** verificado. Desde `comparison_by_dataset.csv`, deduplicando `(dataset,classifier,local_method)` porque se repite por referencia, calculé `ms_comparador / ms_Adaptive`. Rangos: **Top-4 1,6183–12,1839×** (sin Soil 5,6183–12,1839×), **Ens-diversidad 4,3070–16,1406×** y **Completa-22 29,6496–72,2059×**. Tu corrección a un decimal es correcta; 30–72× frente a Completa-22 es un redondeo a enteros. [Razones por dataset/clasificador](../results/analysis/consultas_joaquin_20261114_v1/timing_ratios.csv). La tesis reescrita conserva separadas la cascada Top-k y la política de ensamble; esta frase del corte anterior ya no se usa como resultado del Top-k por margen.

### D2. `paper/articulo/borrador_profesor/references.bib`: dos entradas con autores y títulos incorrectos

Están corregidas en `carlos/references.bib`:

- `gupta2026hytexnet`: Gupta, Vandana; Mishra, Ashish; Shrivastava, Nishant. «HyTexNet: Percentile-guided local encoding and deep feature fusion for enhanced texture classification». *Knowledge-Based Systems* 338, 115482 (2026).
- `chang2024cellnn`: Chang, Mingzhe; Ji, Luping; Zhu, Jiewen. «Multi-scale LBP fusion with the contours from deep CellNNs for texture classification».

Si la tesis usa ese mismo `.bib`, conviene corregirlo también.

**Respuesta (14-11-2026):** ambas entradas ya están corregidas en la bibliografía activa de la tesis que subo: `paper/articulo/borrador_profesor/references.bib`, claves `gupta2026hytexnet` y `chang2024cellnn`. Los metadatos contrastados por DOI quedaron en `results/analysis/topk_margin_rewrite_20261113_v1/reference_metadata.json`. `carlos/references.bib` se conserva sin modificaciones.
