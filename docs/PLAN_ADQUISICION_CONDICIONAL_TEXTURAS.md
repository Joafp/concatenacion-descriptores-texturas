# Plan exploratorio: adquisición condicional de descriptores de textura

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-10-01
- Verification Status: EXPLORATORY (filtro interno y primer piloto externo; no confirmatorio)
- Version Label: conditional_acquisition_plan_v3

## Pregunta y alcance

¿Puede una política entrenada exclusivamente dentro de cada partición de entrenamiento decidir qué bloque de descriptores calcular a continuación, o cuándo detenerse, para mejorar el compromiso entre macro-F1 externo y latencia real respecto de Top-k, GFS y una cascada por margen?

Este plan no sustituye los resultados confirmatorios de concatenación de 22 bloques. La adquisición activa y la selección de descriptor por imagen ya tienen antecedentes; la posible contribución debe residir en la estimación de complementariedad **condicional** entre descriptores heterogéneos de textura, su costo físico y una evaluación externa fuerte. No se reclama novedad absoluta ni mejora antes de probarlas.

## Hallazgo de factibilidad previo (solo diagnóstico)

Los archivos por imagen de `results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison/` permiten calcular un oráculo *no desplegable*: conociendo la etiqueta verdadera, elige la predicción correcta cuando la haya entre ResNet-50 solo y ResNet-50+BEiTv2-final. Su exactitud es un techo para cualquier enrutador que se limite a **elegir entre esas dos predicciones ya entrenadas**; no es un techo para otros modelos, bloques o formas de fusión. Se usaron una sola vez las filas de `budget=0.25`, ya que los presupuestos repiten las mismas imágenes y las mismas dos predicciones.

| Dataset y partición | Aciertos máximos de las dos rutas | Exactitud del oráculo | Exactitud Top-k22 | Exactitud GFS |
| --- | ---: | ---: | ---: | ---: |
| Outex13, oficial 1 | 635/680 | 0,9338 | 0,9441 | 0,9603 |
| DTD, oficial 1 | 1594/1880 | 0,8479 | 0,8734 | 0,8819 |
| CUReT, mitad a→b | 2785/2806 | 0,9925 | 0,9982 | 0,9982 |

Las predicciones provienen de `Outex_rerun_v2/Outex13Official1360_official1_budgets_per_sample.csv`, `DTD_official1_budgets_per_sample.csv` y `CUReT_a_to_b_budgets_per_sample.csv`. Top-k proviene de los JSON `topk_individual_control` del mismo dataset, clasificador SVM, semilla 42 y fold 0; GFS, de los CSV `nested_fold_results.csv` correspondientes. Esta comparación es de **exactitud**, no de macro-F1 ni de latencia. Usar etiquetas de test para construir el oráculo lo convierte únicamente en un límite retrospectivo, jamás en una política válida.

**Decisión de diseño:** mejorar la compuerta de margen de la misma pareja no puede cerrar por sí sola la brecha con Top-k/GFS en estas particiones. El siguiente piloto necesita rutas candidatas adicionales y debe seleccionarlas sin mirar etiquetas externas.

El Top-k22 SVM de estas particiones comparte DINOv2-small, DINOv2-base y DINOv2-large; Outex añade, entre otros, BEiTv2-final. En el diagnóstico de 50 imágenes de Outex, la extracción aislada de DINOv2-large tuvo una media de 177,3 ms, frente a 24,6 ms de DINOv2-small y 12,2 ms de BEiTv2-final (`primary22_e2e/Outex_official1_primary22_online_components.json`). Son costos de componentes con modelos cargados, no latencias finales ni una comparación entre hardware. Sugieren que **evitar DINOv2-large cuando su aporte condicional es bajo** merece examinarse, sin fijarlo todavía como regla.

## Experimento propuesto

1. **Auditar rutas candidatas antes de aprender la política.** Formar una pequeña biblioteca de rutas crecientes (por ejemplo, una base económica y 2–3 ampliaciones) elegidas por desempeño y costo estimados solo dentro del entrenamiento externo. No usar un catálogo de todos los subconjuntos, que haría inestable y caro el aprendizaje. Conservar exactamente el procesamiento por fold de RGB N-grams+SVD.
2. **Medir factibilidad dentro del entrenamiento.** Obtener predicciones fuera de muestra para cada ruta mediante validación interna agrupada. Calcular cuánto corrige o perjudica cada ampliación frente a la ruta actual, y estimar el costo incremental medido de extracción. Si ninguna ruta ofrece suficiente corrección a costo razonable, detener esta línea antes de entrenar otra compuerta.
3. **Entrenar una política pequeña.** Entradas disponibles en el instante de decisión: rasgos de la ruta ya calculada, incertidumbre calibrada y estadísticas visuales baratas. Salidas: detenerse o adquirir una de las ampliaciones. Objetivo de entrenamiento: reducir una pérdida predictiva apropiada (por ejemplo, log-loss calibrada) por costo incremental; macro-F1 permanece como métrica externa principal y no se optimiza falsamente como una pérdida aditiva por imagen.
4. **Evaluar sin filtración.** Congelar rutas, umbrales e hiperparámetros dentro de cada entrenamiento externo. Comparar en las mismas filas de test con Completa-22, Top-k22, GFS, base sola, cascada por margen y control aleatorio del mismo número de adquisiciones. Informar macro-F1, exactitud, fracción de solicitudes, latencia imagen→predicción (mediana y p95), memoria y variación por partición. Separar simulación con embeddings cacheados de medición real en imágenes fuente.

## Salvaguardas y límites

- KTH-TIPS2-b requiere agrupación por muestra física; no mezclar la dirección oficial con la adaptación tres-muestras-para-entrenar sin identificarla. DTD requiere la purga auditada de duplicados. CUReT tiene dos mitades dependientes y Outex un único split; ninguno genera réplicas independientes por sí solo.
- El costo de un subconjunto no se deduce de sus dimensiones. Medir con las implementaciones que reproducen los embeddings archivados, modelos residentes y hardware especificado; contabilizar preprocesamiento compartido sin duplicarlo.
- La reconstrucción online de los 22 bloques todavía no está auditada para todos los extractores. No afirmar una curva de Pareto contra Completa-22 hasta resolver esa equivalencia.
- Como ya se inspeccionaron algunos resultados externos, esta etapa es **exploratoria**. Una afirmación confirmatoria posterior necesita método congelado y datos externos no utilizados para diseñarlo.
- Un margen de no inferioridad y un objetivo de ahorro se fijarán antes de la evaluación final, con justificación práctica; no se elegirán después de ver el test.

## Primer filtro ejecutado: complementariedad dentro del entrenamiento

El programa `scripts/run_conditional_route_feasibility.py` excluye por completo el test externo y genera predicciones *out-of-fold* de cuatro folds agrupados dentro del entrenamiento oficial. Usó SVM lineal con los mismos parámetros base del pipeline confirmatorio. Las cinco rutas se fijaron antes de ver sus predicciones internas: DINOv2-small solo, o seguido de BEiTv2-final, DINOv2-base, DINOv2-large, o DINOv2-base+large. Son rutas exploratorias con cuatro descriptores estáticos; **no** equivalen a la biblioteca confirmatoria de 22 descriptores ni contienen RGB N-grams+SVD. El oráculo retrospectivo usa la etiqueta real solo para medir el margen posible entre estas predicciones, nunca para entrenar una compuerta.

| Dataset, entrenamiento oficial 1 | Mejor ruta fija por exactitud OOF | Exactitud fija | Exactitud oráculo retrospectivo | Diferencia | Macro-F1 de la mejor ruta fija |
| --- | --- | ---: | ---: | ---: | ---: |
| Outex13, 680 imágenes | small+base+large | 610/680 = 0,8971 | 639/680 = 0,9397 | +0,0426 | 0,8915 |
| DTD, 3753 imágenes tras purga | small+large | 3160/3753 = 0,8420 | 3337/3753 = 0,8892 | +0,0472 | 0,8400 |

La diferencia muestra complementariedad predictiva en estas particiones internas, pero está inflada por conocer la etiqueta y **no prueba** que una política aprendida pueda obtenerla. Tampoco autoriza comparar estas cifras de entrenamiento con Top-k/GFS en el test externo. Los detalles de folds, manifiestos y hashes de embeddings están en `results/exploratory/conditional_acquisition/feasibility/`, junto a las predicciones por imagen. No se midió latencia en esta etapa. Las dos pruebas unitarias de cobertura OOF, exclusión del test y cálculo del oráculo pasan.

## Segundo filtro ejecutado: compuerta aprendida y costo de componentes

`scripts/run_conditional_route_gate.py` aprendió, para cada ampliación, la corrección/pérdida de acierto frente a DINOv2-small mediante regresión Ridge con características disponibles después de calcular el bloque base: puntuaciones OOF del SVM, su incertidumbre y 16 componentes principales de su embedding, ajustadas solo con el entrenamiento externo. Seleccionó la ampliación de mayor ganancia prevista por milisegundo incremental. Los umbrales de adquisición del 25 %, 50 % y 75 %, así como la ruta de una cascada por margen competidora, se fijaron con entrenamiento; las métricas se calcularon después en el test oficial 1. Esto es una simulación de decisión con embeddings archivados, no ejecución selectiva online. Se guardaron las decisiones y predicciones por imagen.

| Dataset, test oficial 1 | Base sola | Compuerta 25 % | Cascada por margen 25 % | Mejor ruta fija de estas cinco | Top-k22 / GFS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Outex13, macro-F1 | 0,9062 | 0,9173 | 0,9202 | 0,9313 | 0,9426 / 0,9589 |
| DTD, macro-F1 | 0,8141 | 0,8431 | 0,8411 | 0,8557 | 0,8720 / 0,8807 |

Top-k22/GFS se leyeron de `results/extensions/outex13_official1360/ngram22_beitv2/` y `results/confirmatory/ngram22_beitv2/`, clasificador SVM, semilla 42, fold oficial 0. La compuerta, sus rutas fijas y la cascada están en `results/exploratory/conditional_acquisition/gate/`. Son las mismas filas externas, pero Top-k/GFS usan una biblioteca más amplia y no se debe interpretar esta tabla como una comparación aislada del algoritmo de enrutamiento.

El benchmark online disponible de Outex midió los cuatro componentes usados por el piloto en 50 imágenes, con concordancia de extractor frente al caché. `scripts/benchmark_conditional_route_blocks.py` hizo la misma medición en 50 imágenes de DTD; los cosenos mínimos respecto de los embeddings archivados superaron 0,999. Los costos siguientes **suman tiempos de extracción de componentes medidos**, no incluyen carga de modelos ni son la latencia completa de un sistema enrutado:

| Dataset | Base | Compuerta 25 % | Cascada 25 % | Ruta fija small+BEiT | Ruta fija small+base+large |
| --- | ---: | ---: | ---: | ---: | ---: |
| Outex13, ms/imagen estimados | 24,60 | 27,49 | 27,11 | 36,82 | 259,55 |
| DTD, ms/imagen estimados | 206,54 | 229,65 | 228,76 | 299,38 | 2039,25 |

En las mismas 50 imágenes temporizadas de DTD, al sumar el tiempo medido de los componentes efectivamente elegidos para cada imagen, la compuerta 25 % tuvo media 221,60 ms, mediana 208,33 ms y p95 297,25 ms; la cascada tuvo media 215,60 ms. La diferencia entre este subconjunto y la estimación global muestra por qué no debe presentarse la suma de promedios como latencia end-to-end. Los archivos JSON incluyen el origen y hash del benchmark, los conteos de rutas y los presupuestos 50 % y 75 %; las cinco pruebas unitarias pasan.

**Lectura del resultado:** la primera compuerta reduce mucho el costo estimado frente a rutas que calculan DINOv2-large en todas las imágenes, pero no alcanza su macro-F1 ni los resultados Top-k22/GFS. En Outex pierde ante la cascada simple al 25 %; en DTD la supera solo por 0,0020 de macro-F1 con un costo de componentes ligeramente mayor. Un split por dataset y una biblioteca exploratoria diseñada tras observar resultados previos no justifican significancia, superioridad general ni introducir la compuerta como nueva contribución principal del paper. La ventaja frente a calcular siempre small+BEiT es de costo con macro-F1 prácticamente igual, no una mejora robusta de calidad.

## Siguiente decisión

Antes de ampliar los experimentos, revisar por qué la función ganancia/costo elige casi siempre BEiTv2 y si una política que modele *complementariedad condicional* puede aprovechar rutas de alta calidad sin agotar el presupuesto. Esa nueva política deberá compararse con la cascada simple en múltiples particiones y medir latencia enrutada imagen→predicción, incluida la decisión. Si no demuestra una mejora reproducible de la frontera calidad–costo, conservar este piloto como resultado negativo y buscar otra contribución. El paper actual no se modificó con este experimento exploratorio.

Investigación, planificación e implementación asistidas por IA; conservar la procedencia de todos los números al publicarlos.
