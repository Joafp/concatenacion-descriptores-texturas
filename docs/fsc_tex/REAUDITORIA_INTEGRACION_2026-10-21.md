# Reauditoría de los pilotos de integración y del plan

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: validate, revisión local de código y recálculo desde predicciones.
- Origin Date: 2026-10-21.
- Verification Status: ANALYZED. Se reprodujeron métricas y cálculos de costos desde artefactos; no se reentrenaron modelos ni se verificó una ejecución independiente de entrenamiento.
- Version Label: reauditoria_integracion_v3.
- Alcance: siete condiciones de desarrollo, seis datasets, SVM y biblioteca común de 21 bloques. VisTex excluido.

## Dictamen

Las cifras predictivas guardadas son aritméticamente consistentes. Hay evidencia útil para desarrollar una adquisición condicional, pero el componente central propuesto —selección de la base y de los rescates usando costo marginal de unión— todavía no está implementado. El ejecutor actual selecciona por ranking de calidad, sortea subconjuntos según ese ranking y calcula el costo después. Construir su frontera de Pareto es un análisis de candidatos, no una demostración del optimizador propuesto.

El plan debe priorizar comparabilidad de protocolos, integración del N-gram existente, contabilidad por imagen y selección que realmente use costos. El siguiente paso no es repetir masivamente la implementación actual ni trasladar estas métricas al manuscrito.

## Comprobaciones ejecutadas

Comando: `.venv-confirmatory/bin/python src/reaudit_integration_v2.py`.

Se leyeron los CSV de predicciones y métricas, los logs de folds, los manifiestos y los caches de embeddings. Se reconstruyeron las particiones con el código vigente y se calcularon otra vez macro-F1, exactitud, cobertura de filas, clases presentes, solapamiento de grupos y costos. Los resultados de esta auditoría se escriben en `results/analysis/integration_v2/reaudit_20261021/`; los resultados históricos permanecen conservados.

| Comprobación | Resultado | Alcance |
|---|---|---|
| Macro-F1 desde las predicciones | 147/147 coinciden; error máximo 1,11×10⁻¹⁶ | Verifica la aritmética de métricas |
| Exactitud desde las predicciones | Coincide dentro de precisión numérica | Verifica la aritmética de métricas |
| Orden, etiquetas y unicidad de filas OOF | Correctos en 7/7 condiciones | Cobertura del outer-train reconstruido |
| Grupos entre fit/validación interna | Cero intersecciones | Para el agrupamiento declarado en cada condición |
| Clases ausentes en fit interno | Cero | El mapeo global de scores no falla en estas condiciones |
| Grupos entre outer-train y su test | Cero intersecciones | No certifica independencia de otras variables de origen |
| Tamaños de folds registrados/reconstruidos | Coinciden | KTH tiene 3 folds; las demás condiciones, 4 |
| Resumen consolidado de métricas | Coincide con las predicciones | El consolidador anterior solo copiaba métricas |
| Entrenamiento reproducido desde cero | No ejecutado | Modelos y procedencia completa de su ejecución no certificados |

## Hallazgos que cambian el plan

### 1. DTD no coincide con el protocolo oficial del benchmark principal

La condición nueva de DTD usó SGKF seed 42/fold 0: 4.512 imágenes de entrenamiento y 1.128 de test. El benchmark principal archivado usa diez particiones oficiales. En el outer-train de la nueva condición hay **1.501 imágenes del test oficial 1**. Eso no es fuga entre los lados del SGKF reconstruido: demuestra que son protocolos diferentes.

Consecuencia: conservar DTD-SGKF como desarrollo histórico. Antes de comparar con Complete-22, GFS, Carlos o artículos, ejecutar la regla y sus controles sobre las mismas particiones oficiales, representaciones y clasificadores. Tampoco puede describirse ahora el test oficial 1 como material nunca observado por el desarrollo.

Evidencia: `src/run_topk_individual_control.py`, función `outer_indices`; `src/register_nested_frontiers.py`, entrada `CONDITIONS['DTD']`; `condition_checks.csv` de esta reauditoría.

### 2. N-grams existe; la integración nueva está incompleta

`src/rgb_ngram_descriptor.py` implementa conteos por imagen sin etiquetas, hashing fijo y un `RGBNgramSVDBlock.transform(train, evaluation)` que ajusta SVD con entrenamiento. `run_confirmatory_nested.py` y `run_topk_individual_control.py` ya lo usan mediante `--include-rgb-ngram`.

Se localizaron **102 caches de conteos** de los seis datasets: todos tienen los tres archivos de conteos y formas/índices compatibles; **101 coinciden con el digest del manifiesto vigente**. Un cache de KTH no coincide y debe excluirse hasta reconciliar su origen. Hay al menos un cache con digest coincidente por dataset. Esta comprobación no rehasha las imágenes fuente ni certifica el contenido de cada conteo.

La ausencia de `rgb_ngram_svd.npy` en el directorio de embeddings estáticos no significa que el descriptor falte en el proyecto. Una única SVD global sería inadecuada para este protocolo. El trabajo pendiente es reutilizar el bloque existente dentro del ranking, la calibración y cada fold productor del evaluador nuevo, verificando sus entradas. Hashing es fijo; la transformación aprendida que debe reajustarse es SVD.

### 3. El costo calculado no participa todavía en la elección de bloques

En `src/run_rescue_nested_selection.py`, la base es `ranked[0]`, Top-k toma los primeros bloques y los ensambles se sortean con pesos de ranking. Las latencias se consultan después de producir predicciones. No hay selección de candidatos bajo presupuesto ni penalización por costo marginal durante la construcción de la unión. Tampoco hay todavía ablación de selección por relevancia frente a selección por costo, ni diversidad nueva, Complete-22 o GFS en esas 21 políticas.

La base más precisa puede ser costosa: en CUReT/Outex/KTH aparecen promedios de extracción de base entre 122 y 177 ms. Deben evaluarse bases en la frontera individual de calidad/costo dentro del entrenamiento, en lugar de presuponer que la mejor individual es una etapa económica.

### 4. Media por fold y media por imagen son estimandos distintos

El ejecutor usa `np.mean(per_fold_costs)`. CUReT tiene folds de validación de 732, 732, 671 y 671 imágenes; Soil tiene 228, 229, 228 y 227. Para reportar costo medio por imagen corresponde `sum(n_j × C_j) / sum(n_j)`.

La reponderación cambia **56/147 costos** en más de 10⁻⁸ ms. Cambio absoluto máximo: **1,300543 ms** en CUReT a→b; **0,415317 ms** en CUReT b→a; **0,029441 ms** en Soil. Ninguna etiqueta de Pareto cambia en este conjunto de resultados. Macro-F1 ya se calculaba agrupando predicciones OOF y no necesita este ajuste.

| Punto mostrado previamente | Costo archivado | Media corregida por imagen |
|---|---:|---:|
| CUReT a→b, Top-5 adaptativo q=0,10 | 161,633733 ms | 162,795624 ms |
| CUReT b→a, ensamble-3 q=0,10 | 188,289364 ms | 188,458646 ms |
| Soil, Top-4 adaptativo q=0,25 | 27,851068 ms | 27,846974 ms |

El recálculo usa el perfil de latencias vigente y está en `policy_recalculation.csv`; sin un snapshot al lanzamiento no certifica el perfil histórico exacto. El ejecutor fue actualizado en el seguimiento P0 descrito al final para ponderar tamaños y guardar el perfil de las corridas futuras. Las proyecciones omiten clasificación de rescates, carga/residencia y ejecución física. El overhead 0,45 ms se toma como constante; no sustituye un benchmark de cada ruta.

### 5. Procedencia parcial y significado de “test reservado”

El registro reconstruye correctamente los lados de las siete condiciones y vincula archivos actuales por hashes. Sin embargo, no guardó el código exacto al lanzamiento, cada índice productor, los subconjuntos completos sorteados, los márgenes OOF de calibración ni checkpoints de clasificación. `external_test_used=False` es una afirmación del ejecutor, no una prueba independiente de toda la historia experimental.

La revisión del código es consistente con que esta ejecución calcula métricas solo sobre outer-train. Los tests de estos datasets ya se observaron en trabajos previos del proyecto, incluidos los cuatro pilotos de integración. La evaluación posterior debe describirse como exploratoria con protocolo congelado prospectivamente; congelar ahora no la convierte en confirmatoria ciega.

### 6. La búsqueda interna y la frontera requieren una regla de evaluación

Los resultados son de siete condiciones de desarrollo, no siete datasets independientes ni 27 resultados canónicos de la propuesta nueva. Elegir el máximo OOF entre 21 candidatos y publicar ese mismo valor como desempeño final añade sesgo de selección. Las métricas OOF sirven para seleccionar; la regla elegida debe evaluarse en su nivel externo con todos los pasos anidados.

La alternativa operativa propuesta es definir una curva por presupuesto: para cada presupuesto fijado antes de consultar test, seleccionar dentro de entrenamiento la política de mayor macro-F1 que lo cumpla. Eso permite comparar optimizadores y controles a presupuesto común sin inventar una tolerancia universal de pérdida. Los presupuestos y el tratamiento de casos inviables siguen siendo decisiones de diseño por fijar, y las primeras curvas serán de costo proyectado.

## Escaneo ARS de falacias: 11/11 revisadas

| Patrón | Evaluación en esta revisión |
|---|---|
| Simpson | Se conserva el desglose por condición; no se infiere un ganador de una media mezclada |
| Falacia ecológica | Los folds, imágenes y direcciones no se tratan como datasets independientes |
| Berkson/selección de muestra | Una condición de desarrollo por dataset limita la generalización; no se demuestra este mecanismo específico |
| Sesgo de colisionador | No se identificó un ajuste causal de ese tipo; el escalado es una selección de ruta, no un estimando causal |
| Negligencia de tasa base | Macro-F1 y exactitud se distinguen; especialmente relevante con clases desbalanceadas de Soil |
| Regresión a la media | Elegir variantes por máximos internos puede producir optimismo; no hay inferencia de intervención longitudinal |
| Supervivencia | Hay archivos completos para las siete condiciones auditadas; esto no prueba cobertura de todas las corridas históricas |
| Búsqueda múltiple | Se conservan 21 políticas por condición; no se aplican contrastes inferenciales a sus máximos |
| Caminos analíticos múltiples | El cambio de bibliotecas, base y splits impide llamar confirmatorios a los pilotos |
| Correlación/causalidad | El costo proyectado no acredita ahorro físico ni mecanismo causal |
| Causalidad inversa | No aplica una conclusión causal entre variables observacionales; las rutas describen un algoritmo |

No se calcularon p-valores nuevos ni intervalos de equivalencia. Los checks de métricas no prueban originalidad, ausencia universal de fuga ni calidad editorial de la tesis.

## Prioridad registrada en la reauditoría inicial

1. Corregir contabilidad por imagen y persistencia de la próxima ejecución, con comprobaciones sintéticas de costo, agrupamiento y clases.
2. Definir un registro canónico: DTD 10 oficiales, FMD 5 seed 42, CUReT 2 direcciones, Outex 1, Soil 5 seed 42 y KTH 4 oficiales invertidos = 27 condiciones. La elegibilidad inferencial de KTH sigue sujeta a reconciliación.
3. Reutilizar caches N-gram coincidentes e integrar SVD por fold; recuperar el panel real de 22/20.652 dimensiones. Mantener 21 como ablación.
4. Implementar selección que use presupuesto y costo marginal de unión para base, rescates y compuerta, con controles de relevancia y ensambles de Carlos.
5. Completar curvas internas y pruebas de protocolo; congelar la regla y ejecutar comparaciones externas emparejadas, manteniendo su carácter exploratorio.
6. Medir imagen RGB→predicción con extracción condicional y clasificadores, resolver fidelidad físico/cache y después actualizar estadística y manuscrito.

## Seguimiento P0 implementado — 21 de octubre de 2026

Esta actualización documenta cambios al ejecutor y al registro; no modifica el resultado de la reauditoría aritmética ni vuelve a entrenar las corridas anteriores.

### P0-A: contabilidad y trazabilidad de futuras corridas

`src/run_rescue_nested_selection.py` ahora agrega los costos mediante `sum(n_validation × cost_fold) / sum(n_validation)`. La proyección de cascada calcula el costo por fold con su fracción de escalado observada en las filas OOF de ese fold y luego pondera por el número de imágenes de validación. El perfil sigue excluyendo la latencia del clasificador, residencia/carga de modelos y medición física; por tanto, el campo continúa describiendo costo proyectado de extractores más compuerta.

La ejecución nueva registra hora UTC, comando y argumentos, versión de Python y paquetes, estado/hash del checkout, hashes de los módulos que intervienen, manifiesto, etiquetas, cada matriz de embeddings y perfil de costo. Los artefactos guardan índices e identificadores hash de folds productores, conteos de clases y grupos, ranking completo, descriptor base, miembros y uniones, modelos de subconjunto únicos, márgenes, umbrales, decisiones de escalado y predicciones por muestra. El ejecutor rechaza rutas que ya contengan los archivos de salida previstos; el ranking usa una caché versionada separada en `results/exploratory/integration_v3/ranking_cache/`.

Un smoke técnico final en FMD (seed 42, fold externo 0, dos folds productores y dos de calibración) terminó con 21 políticas, 800 predicciones OOF sin valores faltantes, trazas de margen y seis columnas de umbral/compuerta. Los dos folds quedaron persistidos con miembros sorteados y conteos de modelos únicos. Sus archivos están en `results/exploratory/integration_v3/smoke_fmd_20261021_final/`. El costo de este smoke es proyectado; sus particiones reducidas no se comparan con resultados canónicos ni se incluyen en la tesis.

### P0-B: registro canónico

`src/build_canonical_condition_registry.py` generó `results/analysis/integration_v3/canonical_registry_20261021/` con **27 condiciones**: DTD (10 splits oficiales), FMD (5 folds seed 42), CUReT (2 direcciones), Outex (split oficial 1), SoilOriginal (5 folds seed 42) y KTH-TIPS-2b (4 splits oficiales invertidos). Vincula **216 filas** de primary22: SVM y ResMLP, cada uno con Individual, Completa, GFS y mejor homogéneo. Verifica cobertura de métodos/logs, etiqueta de biblioteca con N-gram, ausencia de solapamiento de grupos y guarda hashes de manifiestos e índices train/test. El builder no ajusta modelos.

Límite histórico: los logs archivados guardan comando, split solicitado y hash del script, pero las ejecuciones originales no persistieron los índices por fila. Por ello, los hashes del registro representan una reconstrucción con el manifiesto y el código de partición actualmente disponibles; el registro **no certifica identidad retrospectiva de cada fila** de aquellas predicciones. Para una comparación emparejada plenamente verificable, los nuevos controles deberán emitirse desde el mismo protocolo y guardar los índices junto a predicciones.

### Estado tras P0

- Implementación de contabilidad/procedencia: completada para corridas futuras y comprobada por smoke técnico; los resultados anteriores conservan su estimador y no se sobrescribieron.
- Panel canónico: definido y registrado; la procedencia histórica por ejemplo queda parcialmente reconstruida.
- N-gram en el evaluador nuevo: P1-A completado posteriormente, con SVD reajustada por fit, tres corridas técnicas FMD y control de 21. Ver [reporte P1-A](INTEGRACION_NGRAM_RESCATE_2026-10-21.md).
- El smoke P0 mantiene selección por ranking. P1-B fue implementado posteriormente como greedy bajo presupuesto; su evidencia se documenta en el [reporte de pilotos](PILOTOS_SELECTOR_PRESUPUESTO_2026-10-21.md).
- No se ejecutó la batería completa, no se recalcularon p-valores y no se midió latencia física.

**Actualización posterior a P2:** además de los pilotos P1-B, hay controles directos de Carlos en FMD/Outex, reselección Outex-21 y ablación de color con ruta fija. La comparación auditada conserva 55 filas y 16 pruebas pertinentes aprobadas. El siguiente paso vigente es emparejar el pool con/sin N-grams, según integración v7 y el [reporte P2](P2_CARLOS_Y_ABLACION_COLOR_2026-10-21.md). Los scripts de recálculo se ejecutan en esta misma conversación y no establecen independencia humana/de modelo ni reproducción independiente del entrenamiento. Las proyecciones de costo no garantizan cumplimiento fuera de muestra ni acreditan latencia física.
