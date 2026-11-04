# Avance: controles GFS y Top-k emparejados

**Corte posterior vigente:** los tres reintentos Outex terminaron y pasaron auditoría. Hay 6/6 condiciones de controles concatenados auditadas, sin repetir FMD. El [registro actualizado](CIERRE_CONTROLES_Y_MEDICION_2026-10-26.md) y `results/analysis/matched_concat_panel_20261026` presentan el informe conjunto. Los estados parciales y timeouts descritos abajo son cortes históricos preservados, no procesos todavía pendientes.

## Material Passport

- Origin Skill: ARS experiment-agent, guía local, no pipeline formal
- Origin Mode: run
- Origin Date: 2026-10-26
- Verification Status: ANALYZED — panel parcial: tres condiciones FMD auditadas, Outex sin resultados finales
- Version Label: matched_concat_fmd_analyzed_outex_authorized_retry_v3

**Estado vigente:** la cola original terminó. FMD/42, FMD/123 y FMD/2026 están completas y auditadas; Outex/42, Outex/123 y Outex/2026 alcanzaron el límite de 1.800 segundos y se terminaron con código −15. El autor autorizó repetir únicamente las tres condiciones Outex con hasta 7.200 segundos cada una. La nueva cola inició Outex/42 y Outex/123, con Outex/2026 en espera al corte; todavía no hay nuevos resultados auditados. Se conserva el método original y no se repite FMD. Detalle: [enmienda operativa](ENMIENDA_REINTENTO_OUTEX_2026-10-26.md).

## Objetivo y decisiones fijadas

Se continúa el [plan de cierre](PLAN_CIERRE_VIGENTE_2026-10-25.md) después de incorporar la réplica al manuscrito. Este avance agrega controles que faltaban; no modifica el híbrido ni reutiliza cifras externas para cubrir una comparación nueva.

El [protocolo](PROTOCOLO_GFS_TOPK_EMPAREJADO_2026-10-26.md) distingue GFS libre, Top-k con k heredado de ese GFS, GFS greedy con restricción de costo y selección de prefijo factible. La última variante no hereda k de GFS y se identifica con otro nombre. Se mantienen explícitas las políticas inviables y los cuatro presupuestos 15/30/60/120, sin saltar extractores caros de un prefijo para producir un ranking distinto.

Son seis condiciones de desarrollo en dos datasets: FMD y Outex con semillas 42/123/2026. Se incluye Outex/42 del piloto para disponer también de los controles emparejados del punto discutido originalmente. Cada condición reutiliza exactamente los índices productores e internos de su referencia, los 22 bloques y el mismo perfil de adquisición. No se evalúan sus tests externos ni se extraen imágenes nuevas.

## Implementación y pruebas

- `src/static_concat_controls.py`: selección independiente de etiquetas o predicciones productoras; GFS conserva máximo ocho bloques, parada de dos mejoras inferiores a 0,001, mejor paso histórico y desempate léxico del antecedente. Las rutas con presupuesto se construyen desde cero, no truncando la ruta libre a posteriori.
- `src/run_matched_concat_controls.py`: reutiliza scores internos compatibles y ajusta concatenaciones faltantes en tres pliegues internos. Guarda las treinta decisiones política/pliegue antes de evaluar ninguna validación productora. Registra cada candidato, transformaciones y cobertura completa/incompleta.
- `scripts/run_matched_concat_queue.py`: cola de dos condiciones simultáneas, dos hilos BLAS por proceso, treinta minutos por condición, logs y PID; sin reintentos automáticos ni sobrescrituras.
- `scripts/audit_matched_concat_controls.py`: auditor incremental preparado para reproducir selección, k heredado, clases predichas, costos, factibilidad, grupos y exclusión del test. Su prueba sintética pasa; **no equivale a haber auditado las corridas científicas aún en ejecución**.

Diez pruebas nuevas pasaron antes de lanzar la cola; la suite completa inicial obtuvo **107 aprobadas en 60,40 s**. Posteriormente se amplió la prueba sintética para ejecutar también el auditor y se corrigió un campo ausente en esa simulación de procedencia (perfil de costos); los diez tests focalizados volvieron a pasar en 11,33 s. Se añadió un caso con todos los prefijos presupuestados inviables, comprobando que no se inventa una métrica ni se omiten bloques caros. Suite completa final: **108 aprobadas en 54,04 s**. La corrección y ampliación afectaron solo al fixture de prueba, no al código ni a la configuración científica congelados.

## Ejecución iniciada

Configuración: `configs/fsc_tex/matched_concat_20261026.json`.

Comando desde la raíz:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONPATH=.:src \
  .venv-confirmatory/bin/python -u scripts/run_matched_concat_queue.py \
  --config configs/fsc_tex/matched_concat_20261026.json --execute
```

Salidas: `results/exploratory/integration_v12/matched_concat_20261026`. El archivo `frozen_protocol.json` guarda antes de ejecutar comandos, configuración, fuentes y hashes de referencias. Cada condición conserva `state.json`, `controls.log` y, al terminar, su carpeta `controls`. El estado en esos archivos puede avanzar después de este corte.

Primeras condiciones activas al corte: FMD/42 y Outex/42. Las demás quedan en cola. Los logs muestran candidatos internos, no resultados finales. La selección puede continuar tras un paso de menor F1 por la regla de parada de GFS, y después devolver el mejor paso; esto no es un fallo ni una selección usando validación productora.

Primer corte del auditor incremental: `PARTIAL`, 0/6 condiciones auditadas, con las dos primeras en ejecución y cuatro en cola. Ese registro documenta ausencia de resultados terminados, no un fallo científico. Los archivos de estado y el resumen del auditor deben consultarse nuevamente al continuar.

## Primer corte histórico: una condición terminada y auditada

FMD/42 completó los ajustes en aproximadamente 520 segundos. El auditor reprodujo sus treinta decisiones de política/pliegue, incluido el k heredado, verificó las 800 predicciones por política y recalculó sus diez resultados. En ese primer corte había **1/6 auditadas**; Outex/42 y FMD/123 estaban en ejecución y las otras tres en cola. El estado vigente y las interrupciones posteriores se identifican por separado arriba y a continuación.

| Control FMD/42 | Macro-F1 productor reunido | Adquisición proyectada ms |
| --- | ---: | ---: |
| GFS libre | 0,974990 | 130,920 |
| Top-k con tamaño GFS | 0,976277 | 208,508 |
| GFS B15 | 0,970082 | 11,680 |
| Prefijo factible B15 | 0,970082 | 11,680 |
| GFS B30 | 0,968824 | 15,939 |
| Prefijo factible B30 | 0,970082 | 11,680 |
| GFS B60 | 0,973793 | 33,834 |
| Prefijo factible B60 | 0,973786 | 24,552 |
| GFS B120 | 0,976271 | 80,817 |
| Prefijo factible B120 | 0,975028 | 43,721 |

En esa misma condición, el híbrido de relevancia/B60 previamente auditado obtiene 0,977506/38,282 ms: mayor F1 que GFS B60, pero mayor adquisición proyectada. El ensamble estático presupuestado anterior obtiene 0,978772/35,078 ms y sigue favorecido frente al híbrido en ambas medidas. No debe omitirse ese rival ni deducirse una ventaja global a partir de esta primera condición. Las otras semillas y Outex siguen pendientes. No se añadieron estos resultados parciales al PDF.

## Corte actualizado: FMD completo y Outex interrumpido

La auditoría incremental ya registra **3/6 condiciones auditadas**, las tres semillas FMD. Se reprodujeron noventa decisiones y treinta resultados del control concatenado. El panel conjunto sigue `PARTIAL`: los controles Outex agotaron el tiempo durante la selección interna del segundo pliegue productor, antes de congelar las decisiones finales y evaluar validación productora. Cada carpeta interrumpida conserva metadatos y log, sin `results.csv` ni predicciones finales. No se rellenan esos datos con cifras parciales ni se interpretan los timeouts como derrotas predictivas.

`scripts/report_matched_concat_fmd.py` une las tres auditorías con las referencias previas del híbrido, comprobando igualdad de hashes de las particiones. Guarda las 132 filas de políticas/condiciones, 44 medias y 42 diferencias emparejadas, además de las tres interrupciones, en `results/analysis/matched_concat_20261026/comparison_fmd`. La comparación nueva cubre **un dataset con tres semillas**, no tres dominios ni toda la réplica del híbrido.

En FMD, relevancia/B60 tiene F1 medio 0,977489 y costo proyectado 35,689 ms; GFS libre, 0,975410/197,414 ms; Top-k con tamaño GFS, 0,975444/210,751 ms. La reducción de adquisición proyectada como razón de costos medios es 81,92 % y 83,07 %, respectivamente. GFS B60 tiene menor F1 y menor costo (0,970436/30,902 ms), por lo que no hay dominancia del híbrido en esa comparación. El contraejemplo FMD/42 frente al ensamble estático presupuestado se conserva. No se calcularon p-valores ni se midió latencia física.

El [resumen para el profesor](RESUMEN_PARA_PROFESOR_2026-10-26.md) separa estos resultados de FMD, la réplica del híbrido y el benchmark histórico. El PDF no se modificó para incorporar un panel GFS/Top-k que sigue incompleto.

El informe FMD tiene una prueba de reconstrucción que comprueba 132 filas, 44 medias, tres timeouts explícitos y el contraejemplo FMD/42, sin ejecutar modelos. Última suite completa: **109 aprobadas en 45,87 s**, anterior a este reintento. La cola original ya no tiene procesos activos. La autorización posterior permitió lanzar una cola nueva limitada a Outex, sin modificar los archivos científicos originales; el ensayo en seco verificó tres trabajos y exclusión de FMD.

### Reintento Outex autorizado e iniciado

Configuración nueva: `configs/fsc_tex/matched_concat_outex_retry_20261026.json`. Salidas: `results/exploratory/integration_v13/matched_concat_outex_retry_20261026`. Se mantienen dos trabajadores, dos hilos y el documento científico original; solo cambian la selección de condiciones, las rutas de salida y el límite temporal. El recibo `results/analysis/matched_concat_outex_retry_20261026/authorization.json` registra la respuesta del autor, los 48 hashes verificados, la comparación de configuraciones y los estados originales. Los PID iniciales son 67574 (Outex/42) y 67575 (Outex/123); son una instantánea, no una garantía de continuidad. Consultar estados y logs para conocer el avance posterior.

La auditoría de la recuperación se guardará en `results/analysis/matched_concat_outex_retry_20261026/audit`, separada del panel original. El comando está en la enmienda. No hay un segundo reintento automático autorizado, ni se consideran los 120 minutos una estimación de duración. Hasta completar y auditar esas condiciones, el panel sigue con tres de seis condiciones científicas auditadas. No se incorporaron cifras nuevas al PDF.

### Comprobaciones de interpretación guiadas por ARS

Cobertura: 11/11 tipos examinados; alcance descriptivo, no certificado de validez.

| Riesgo | Comprobación y límite |
| --- | --- |
| Simpson/agregación | Se contrastaron medias y semillas; el contraejemplo estático FMD/42 se conserva. No se declara una paradoja de Simpson ni dominancia de cada semilla por el promedio |
| Falacia ecológica | La comparación concatenada nueva tiene un dataset y tres semillas, no tres dominios independientes |
| Berkson/selección | FMD se resume por cobertura completa, no por ganar en F1. La selección por disponibilidad limita la extensión de la conclusión |
| Collider | No se ajustó una asociación causal condicionando por costo o por finalización; no se deriva una conclusión causal de ese filtrado |
| Tasas base | Se conserva macro-F1 y el mismo universo de diez clases FMD; no hay PPV/NPV clínicos a interpretar |
| Regresión a la media | No se seleccionaron semillas por valores extremos; no se presenta una serie pre/post como mejora causal |
| Supervivencia | Se declaran los tres timeouts Outex y el panel incompleto; no se computa una media de dos datasets excluyéndolos silenciosamente |
| Búsqueda múltiple | Se conservan las 44 variantes y los cuatro presupuestos; B60 es ilustrativo, sin p-valor confirmatorio nuevo |
| Caminos de análisis | Las decisiones se fijaron antes de ajustar el control, pero los benchmarks y el híbrido eran conocidos; alcance exploratorio |
| Asociación/causalidad | El contraste de scores y rutas no acredita una ventaja causal universal ni ahorro físico medido |
| Causalidad inversa | No se usa un diseño observacional temporal para inferir causalidad; la reproducción de cálculo queda limitada a las rutas fijadas |

## Auditoría y próximo paso

Cuando una condición marque `complete_pending_audit`, ejecutar:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONPATH=.:src \
  .venv-confirmatory/bin/python scripts/audit_matched_concat_controls.py \
  --suite results/exploratory/integration_v12/matched_concat_20261026 \
  --output results/analysis/matched_concat_20261026
```

El auditor conserva las condiciones todavía no terminadas como pendientes; las políticas cuyo prefijo no cumple presupuesto no se rellenan con una puntuación parcial. Cada condición terminada puede contrastarse con sus referencias emparejadas, como FMD/42 arriba; la conclusión del panel requiere completar las seis. Se informarán calidad y costo proyectado, sin escoger una política por el resultado productor ni tratar semillas como datasets independientes.

El PDF permanece en el corte de 67 páginas de la incorporación de la réplica. No se añadieron métricas parciales ni afirmaciones sobre los controles nuevos. La medición física del híbrido, el resto del panel y la entrega pública siguen pendientes.
