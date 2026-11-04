# Controles concatenados completos y piloto de fidelidad física

## Material Passport

- Origin Skill: ARS experiment-agent, ejecución y validación locales guiadas.
- Origin Mode: run / validate.
- Origin Date: 2026-10-26.
- Verification Status: ANALYZED para controles archivados; medición física aún no validada.
- Version Label: matched_panel_complete_physical_parity_pilot_v1.

## Recuperación de Outex completada

Las semillas 42, 123 y 2026 terminaron el reintento autorizado con código 0, en aproximadamente 56,2, 37,3 y 63,0 minutos por condición. `results/analysis/matched_concat_outex_retry_20261026/audit/summary.json` registra 3/3 auditadas. El auditor reprodujo noventa decisiones adicionales, costos, selección, predicciones, grupos y exclusión del test externo. Las tres condiciones FMD anteriores siguen auditadas y no se repitieron: seis condiciones de controles concatenados completas en total.

Los tres timeouts originales siguen intactos. La recuperación usa salidas nuevas y no transforma retrospectivamente un fallo original en éxito. El límite de 120 minutos no cambió el método.

## Informe conjunto y cobertura

`scripts/report_matched_concat_panel.py` liga los controles FMD originales y Outex recuperados con las cinco condiciones nuevas del híbrido ya auditadas. Comprueba hashes y correspondencia de particiones. Guarda `results/analysis/matched_concat_panel_20261026`:

- 220 filas de políticas/condiciones y 88 medias de política/dataset.
- Comparación conjunta: FMD semillas 42/123/2026 y Outex semillas 123/2026.
- Outex/42 conserva sus diez controles concatenados en un archivo separado; su híbrido pertenece al piloto histórico y no se incorpora silenciosamente a las medias nuevas.
- Cuatro medias de prefijos presupuestados Outex carecen de cobertura factible completa. Se conservan explícitamente sin F1 ni costo agregado; no se promedian solo las semillas que pudieron ejecutarlos.

La cobertura de seis controles completos no equivale a seis datasets ni a seis dominios independientes. No se usan los tests externos. Las medias de macro-F1 parten de predicciones productoras reunidas por condición, no del promedio de F1 de los pliegues.

## Resultado nuevo Outex

Dos semillas nuevas, costos de adquisición proyectados:

| Método | Macro-F1 medio | Adquisición proyectada, ms |
| --- | ---: | ---: |
| GFS libre | 0,908080 | 274,047 |
| Top-k con tamaño GFS | 0,897153 | 318,805 |
| GFS bajo B60 | 0,878574 | 55,426 |
| Ensamble estático B60 | 0,889152 | 49,047 |
| Cascada del pool anterior, relevancia/B60 | 0,911895 | 42,845 |
| Híbrido de Carlos, relevancia/B60 | 0,905991 | 40,750 |

El híbrido tiene mayor F1 y menor adquisición media que Top-k en estas condiciones. Frente a GFS libre, pierde F1 y reduce adquisición proyectada. La cascada del pool anterior sigue teniendo mayor F1 con un costo algo mayor. No hay un ganador universal y no se transfiere significancia del benchmark histórico.

## Medición física: implementación y puerta de fidelidad

Se añadieron `src/frozen_ensemble_route.py` y `scripts/benchmark_frozen_ensemble_routes.py`, sin modificar fuentes científicas congeladas. El evaluador comparte bloques entre miembros de una misma política, mantiene multiplicidades de voto, conserva N-grams al final de la concatenación histórica y no adquiere rescate si el margen es igual al umbral. Tres pruebas sintéticas cubren esas propiedades. Dos pruebas adicionales del informe conjunto impiden promediar solo semillas factibles y verifican la unidad dataset. Las cinco pruebas focalizadas pasaron.

El [protocolo físico](PROTOCOLO_FISICO_ENSAMBLES_2026-10-26.md) fija FMD/42 y Outex/123, primer pliegue, seis filas deterministas y tres repeticiones, sin selección por F1. Ante la ocupación GPU ajena (aproximadamente 6,5 de 8 GB), el piloto inicial es CPU y offline. No se interrumpe actividad ajena ni se presentan tiempos CPU como GPU.

**FMD/42 se detuvo por fidelidad numérica antes de cronometrar:** los modelos reajustados reprodujeron clases y compuertas archivadas sobre características guardadas; BEiT-v2, ConvNeXt-v2, DINOv2-base y DINOv2-large pasaron los controles iniciales. DINOv2-small en la fila 193 registró un error absoluto máximo de 0,00018891, superior a la tolerancia predefinida de 0,0001. Se conserva `physical_timing_validated=false`. No se relaja la tolerancia, no se afirma que ese error cambie necesariamente la clase y no se publica un ahorro físico a partir de ese intento. La causa concreta (precisión/dispositivo, versión o reconstrucción) todavía debe diagnosticarse.

**Outex/123 también se detuvo antes de cronometrar**, como segunda condición previamente fijada, no como sustitución escogida por un fallo de FMD. DINOv2-small en la fila 266 registró un error máximo de 0,00010315 frente al umbral 0,0001. Su estado se conserva en `results/exploratory/integration_v14/physical_routes_20261026/Outex_s123/status.json`, con `physical_timing_validated=false`. Los dos intentos completaron el recálculo de clases y compuertas en caché sobre las seis filas fijadas, pero no todas las verificaciones de características online. No hay latencias válidas que incorporar ni se relanza automáticamente una condición fallida.

La suite completa posterior obtuvo **114 pruebas aprobadas en 52,89 s**. Es una comprobación de software, no una validación de ahorro físico ni de superioridad científica.

**Diagnóstico GPU posterior autorizado:** DINOv2-small pasó las cuatro comparaciones fijadas de FMD/Outex con tolerancia 0,0001 intacta, incluido el par de filas que falló en CPU. Error máximo GPU observado: 0,000000488013. El [resultado específico](RESULTADO_DIAGNOSTICO_PARIDAD_GPU_2026-10-26.md) conserva filas, hashes y límites, separado del protocolo congelado. Esto resuelve esa comprobación parcial del extractor en GPU, no valida la ruta completa ni publica tiempos físicos. Las corridas de calidad no se repitieron y los fallos CPU no se reescribieron.

## Interpretación guiada por ARS: 11/11 controles

| Riesgo | Límite aplicado |
| --- | --- |
| Agregación / Simpson | Medias separadas por dataset y conservación de pérdidas por semilla |
| Falacia ecológica | Semillas y pliegues no se contabilizan como datasets independientes |
| Selección / Berkson | Se identifica el panel de desarrollo y el piloto histórico separado |
| Colisionador | No se atribuye un efecto causal por filtrar por costo o activación |
| Tasas base | Macro-F1 conserva el universo de clases y cobertura de cada condición |
| Regresión a la media | No se usa una comparación pre/post ni se eligen semillas por valores extremos |
| Supervivencia | Timeouts originales e inviabilidades permanecen visibles; sin medias de cobertura parcial |
| Búsqueda múltiple | Se conservan reglas y B15/B30/B60/B120, sin un nuevo p-valor confirmatorio |
| Caminos analíticos | Exposición previa a benchmarks y carácter exploratorio explícitos |
| Asociación / causalidad | Diferencias de política no se presentan como efecto causal poblacional ni ahorro físico |
| Causalidad inversa | No se infiere temporalidad a partir de asociaciones observacionales |

## Decisión para continuar

Los controles emparejados están atendidos. La elección final de método sigue abierta: el híbrido no domina a todos los rivales y el pool anterior conserva ventajas. El siguiente paso es resolver la fidelidad de extracción y ejecutar un benchmark físico pareado fiel, con disponibilidad de recursos documentada. Solo entonces corresponde elegir alternativas para ampliar a otros dominios. No se inicia un barrido nuevo de seis datasets para favorecer una variante aún no seleccionada.

La presentación para diez minutos incorpora Outex auditado y conserva la validación física como pendiente. El PDF de tesis no se modificó en este corte. Este reporte no certifica novedad, equivalencia estadística ni cierre institucional.
