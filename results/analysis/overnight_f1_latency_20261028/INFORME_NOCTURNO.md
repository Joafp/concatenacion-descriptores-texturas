# Informe nocturno: corte inicial 28-10-2026

## Material Passport

Registro operativo inicial, ARS inline. No es un cierre del benchmark ni de la
tesis. Actualizar mediante el seguimiento con estados y fuentes verificadas.

## Programación confirmada

- Seguimiento activo del mismo chat cada 15 minutos:
  `tesis-continuar-corridas-f1-y-latencia`.
- Manifiesto: 94 condiciones, cinco métodos por condición, cuatro etapas
  (calidad, replay, ejecución individual, auditoría de llamadas).
- 76 condiciones nuevas de calidad con archivos requeridos localizados.
- Diez condiciones FMD/42 ya terminadas o gestionadas por colas existentes;
  se reservan para evitar duplicación, no se cuentan todas como completas.
- Ocho condiciones KTH retenidas hasta reconciliar su protocolo.
- 28 condiciones físicas FMD elegibles después de heads y replay; las dos
  primeras ya están gestionadas por la secuencia física existente.
- La medición de otros datasets conserva la puerta de adaptación/vínculo de
  extractor. No figura como lista solo por existir en el manifiesto.

## Workers lanzados

`worker_quality.json` y `worker_online.json` contienen los PID y estados.
Ambos esperan las dependencias existentes antes de despachar corridas nuevas;
es una espera prevista, no un bloqueo por sí sola. Ventana inicial: diez horas
de despacho. Una condición activa conserva su límite individual, sin matarla
porque se agotó la ventana de despacho. No hay reintentos automáticos.

## Primer resultado físico disponible para auditoría

FMD/42/0 SVM completó las 1.000 llamadas desde imágenes (200 por método), con
F1 y tiempos de esas mismas llamadas. Cifras del CSV crudo final:

| Método | F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,939764 | 1845,889634 |
| Diversidad | 0,954599 | 398,065143 |
| Tómbola | 0,954599 | 377,378928 |
| Top-4 | 0,959648 | 277,692812 |
| Adaptativo | 0,964815 | 60,577735 |

Fuente: `results/exploratory/local_batch1_20261028/FMD_s42_f0_svm/online_summary.csv`.
Antes de promover la tabla, comprobar el resultado del auditor en
`results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/svm_audit/`.
La secuencia ya programada audita SVM y después mide/audita ResMLP sin solapar
ambos benchmarks GPU. No presentar este corte inicial como una media de FMD,
de tres semillas o de los seis datasets.

Contexto: GPU compartida y trabajo CPU concurrente ya identificado; una
observación por imagen. Son mediciones exploratorias del entorno observado,
no pruebas de hardware aislado. El acuerdo de clases con el archivo fue 100%
en esta partición; eso no demuestra paridad de todos los vectores.

## Qué sigue

Actualización del mismo corte: la auditoría de las 1.000 llamadas SVM pasó
(`ONLINE_CALL_RECORDS_REAGGREGATED`) y la secuencia avanzó a medir ResMLP.
La cola de calidad ResMLP/42 también cerró sus cuatro pliegues restantes con
replay; su agregación separada terminó: adaptativo 0,972955, Completa 0,962027,
diversidad 0,978971, tómbola 0,978035 y Top-4 0,978017 (medias por pliegue,
sin tiempos, una semilla). Fuente: `results/analysis/local_fmd_seed42_summary_20261028/resmlp/`.
Los workers nocturnos siguen esperando
el fin de la secuencia física antes de agregar carga nueva.

Auditar/terminar la secuencia física inicial, cerrar ResMLP/42 y su agregación,
continuar condiciones elegibles del manifiesto y resolver puertas de los otros
datasets sin modificar el método. Consolidar la tabla completa solo al cerrar
la cobertura prevista. Papers después del panel local.

No hubo commits, push, cambios al manuscrito ni promesa de terminar toda la
matriz esta noche. Equipo y entorno local deben permanecer disponibles.

## Actualización del primer seguimiento nocturno (28-10-2026 UTC)

Este apartado reemplaza los estados operativos iniciales anteriores, que se
conservan como historial. La secuencia física inicial terminó con estado
`both_pilots_and_call_audits_complete` a las 23:48:53 UTC.

### Pilotos físicos completos: FMD, semilla 42, pliegue 0

Ambos clasificadores tienen 200 imágenes externas y cinco métodos: 1.000
llamadas por clasificador. Las dos auditorías terminaron como
`ONLINE_CALL_RECORDS_REAGGREGATED`, con F1 y tiempos de las mismas llamadas.

| Método | SVM F1 online | SVM media ms/imagen | ResMLP F1 online | ResMLP media ms/imagen |
| --- | ---: | ---: | ---: | ---: |
| Completa-22 | 0,939764 | 1845,889634 | 0,944786 | 1782,194512 |
| Diversidad | 0,954599 | 398,065143 | 0,954674 | 405,803180 |
| Tómbola | 0,954599 | 377,378928 | 0,964815 | 377,484539 |
| Top-4 | 0,959648 | 277,692812 | 0,959756 | 272,147641 |
| Adaptativo | 0,964815 | 60,577735 | 0,954674 | 55,925806 |

Fuentes adicionales a la tabla SVM anterior:
`results/exploratory/local_batch1_followup_20261028/FMD_s42_f0/resmlp_online/online_summary.csv`,
`svm_audit/audit.json` y `resmlp_audit/audit.json` bajo esa secuencia.
Estos auditores verifican registros y aritmética, no constituyen una segunda
medición independiente de hardware. GPU compartida, una repetición por imagen:
no interpretar estas latencias como benchmark aislado ni media completa de FMD.

Lectura acotada: el adaptativo es más rápido en ambos pilotos. En SVM obtiene
el mayor F1 de esta partición. En ResMLP empata numéricamente con diversidad,
supera a Completa y pierde frente a Top-4 y tómbola. No hay una victoria
uniforme de calidad ni una conclusión de significancia estadística.

### Cobertura y colas observadas

- Matriz prevista: 94 condiciones y 470 filas condición–método.
- Calidad archivada más replay: diez condiciones FMD/42 cerradas previamente
  (cinco pliegues por clasificador), y seis condiciones nuevas completadas por
  el worker: SVM/123/pliegues 0–4 y SVM/2026/pliegue 0. Corte: 16 condiciones
  de calidad; esto NO son 16 condiciones con latencia online.
- Online completo y auditado: dos condiciones (los pilotos anteriores),
  diez filas condición–método, 2.000 llamadas temporizadas en total.
- Worker CPU PID 6307 activo, procesando FMD/SVM/2026/pliegue 1 en el corte.
- Worker online PID 6315 y único benchmark GPU PID 6592 activos sobre
  FMD/SVM/42/pliegue 1; checkpoint de 550 llamadas. No es una condición
  completa y no se incorpora a las medias anteriores.
- Ningún `requires_review` en ambos workers al consultar sus estados.
- Continúan pendientes las ocho condiciones KTH retenidas y las puertas de
  adaptación/vínculo de extractor para la ejecución física de otros datasets.

No se lanzó ningún benchmark duplicado ni se cambiaron fuentes congeladas,
tolerancias, métodos, protocolos, manuscrito o repositorio remoto.

## Seguimiento 29-10-2026, 00:06 UTC

La calidad en caché y el replay de FMD/SVM completaron sus quince condiciones
(tres semillas por cinco pliegues). Esto cierra esa etapa, NO sus tiempos
físicos. El worker de calidad completó once condiciones nuevas en total y
avanzó a FMD/ResMLP/123/pliegue 1. Con las diez condiciones previas, el corte
registra 21 condiciones de calidad con replay: quince SVM y seis ResMLP.

La ejecución física FMD/SVM/42/pliegue 1 terminó y pasó la auditoría de sus
1.000 llamadas. El panel físico tiene ahora tres condiciones completas y
auditadas (3.000 llamadas, quince filas condición–método), no una media
completa de dataset. Resultados de esta nueva condición únicamente:

| Método | F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,984994 | 1703,105770 |
| Diversidad | 0,989997 | 367,419577 |
| Tómbola | 0,989997 | 348,271360 |
| Top-4 | 0,994997 | 269,065729 |
| Adaptativo | 0,989997 | 33,999973 |

Fuente: `jobs/FMD_svm_s42_f1/online/online_summary.csv`; auditoría
`jobs/FMD_svm_s42_f1/online_audit/audit.json`, estado
`ONLINE_CALL_RECORDS_REAGGREGATED`. La cascada reduce el tiempo observado,
pero en este pliegue pierde aproximadamente 0,0050 de F1 frente a Top-4.
Se mantienen las reservas de entorno compartido y una repetición por imagen.

Ambos workers siguen vivos (PID 6307 y 6315), sin condiciones marcadas como
`requires_review`. Hay un único benchmark GPU activo (PID 7125), ahora en
FMD/SVM/42/pliegue 2. No se duplicaron corridas ni se repitieron fallos.
Las puertas de otros datasets y KTH permanecen vigentes.

## Seguimiento 29-10-2026, 00:21 UTC

Avance operativo sin cierre adicional de una semilla completa: 23 condiciones
de calidad con replay (las diez previas y trece del worker), y cinco
condiciones físicas completas y auditadas (5.000 llamadas, 25 filas
condición–método). Las nuevas auditorías online de FMD/SVM/42/pliegues 2 y 3
registran `ONLINE_CALL_RECORDS_REAGGREGATED`, 1.000 llamadas cada una y F1/ms
de las mismas llamadas. Se revisaron los logs de ejecución y auditoría del
pliegue 3, sin errores registrados. No se publican medias de la semilla:
falta cerrar el pliegue 4.

Workers CPU/GPU vivos (6307/6315), sin `requires_review`. Calidad activa:
FMD/ResMLP/123/pliegue 3. Único benchmark GPU activo: PID 7609,
FMD/SVM/42/pliegue 4. El resto conserva dependencias y reservas anteriores;
no se relanzaron procesos ni se alteraron experimentos.

## Seguimiento 29-10-2026, 00:36 UTC: primer cierre físico de cinco pliegues

FMD/SVM/semilla 42 completó sus cinco pliegues físicos y auditorías. Se
consolidaron 5.000 llamadas de 1.000 imágenes únicas, cinco métodos, con
comprobación de hashes, referencias a heads congelados, cobertura disjunta y
recomputación de F1/latencias desde las llamadas registradas. Sin nueva
inferencia ni repetición de experimentos.

| Método | F1 online medio por pliegue | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,965099 | 1768,199628 |
| Diversidad | 0,978911 | 378,222587 |
| Tómbola | 0,978912 | 355,060368 |
| Top-4 | 0,981922 | 270,131909 |
| Adaptativo | 0,977976 | 41,350536 |

La cascada pierde 0,003946 de F1 medio por pliegue frente a Top-4 (0,395
puntos porcentuales), con menor tiempo medio observado. Es un compromiso
calidad–latencia, no superioridad uniforme. La media de latencia combina las
llamadas de esta semilla; no es una medición de hardware aislado. No se han
completado aún las tres semillas de FMD con tiempos, ni el panel de datasets.

Fuente: `summary_FMD_svm_s42_online_v1/seed_summary.csv` y `summary.json`.
Se conserva por separado el F1 agrupado de las 1.000 predicciones: adaptativo
0,977997 frente a Top-4 0,981983. No se confunde con la media de cinco F1.
El consolidado documenta hashes de entrada, salidas y script.

Infraestructura añadida: `scripts/summarize_fmd_online_seed.py` y tres pruebas
unitarias. Verificación focalizada con las cinco pruebas del auditor de
llamadas: ocho pruebas aprobadas. No se modificó ninguna fuente activa del
benchmark ni se ejecutaron modelos GPU adicionales.

En el corte inicial de este seguimiento: 26 condiciones de calidad con replay
(diez previas y dieciséis nuevas), seis condiciones físicas auditadas contando
el piloto ResMLP (6.000 llamadas, treinta filas condición–método). Workers
6307/6315 activos: calidad FMD/ResMLP/2026/pliegue 1 y online
FMD/SVM/123/pliegue 0, un solo benchmark GPU (7901). Sin `requires_review`.

## Seguimiento 29-10-2026, 00:51 UTC

Cobertura observada: 28 condiciones de calidad con replay (diez previas y
dieciocho del worker), ocho físicas completas y auditadas (8.000 llamadas,
cuarenta filas condición–método). Los nuevos pliegues físicos son
FMD/SVM/123/0 y /1; la auditoría del pliegue 1 registra 1.000 llamadas desde
200 imágenes y F1/ms de las mismas llamadas. Sus logs de ejecución terminaron
sin error registrado. No hay un nuevo cierre de las tres semillas físicas.

Workers 6307/6315 vivos, sin `requires_review`: calidad en
FMD/ResMLP/2026/pliegue 3 y único benchmark GPU 8473 en
FMD/SVM/123/pliegue 2. No se relanzaron trabajos ni se cambiaron fuentes.

Preparación independiente, solo lectura, de las puertas de otros datasets:
`embeddings_confirmatory/CUReT/deit_s_metadata.json` declara semilla 42,
5.612 filas y SHA-256 de embedding
`5d6dd6274c7dad3e711177eac20ff2f0a7386dc670db286943c9a62773529380`.
Outex tiene metadatos de construcción canónica de 1.360 imágenes y 68 clases,
pero ese archivo no declara semilla: no autoriza asumir la inicialización del
pooler. DTD usa el directorio `embeddings`, no `embeddings_confirmatory`; no
se localizó `deit_s_metadata.json` allí en el inventario consultado. Estas
observaciones NO validan paridad ni habilitan nuevos benchmarks. Se mantiene
`dataset_adapter_binding_review`; cualquier diagnóstico GPU tendrá que
respetar la exclusión del benchmark activo. KTH conserva además la puerta de
reconciliación de protocolo. No se descargaron modelos ni se modificaron datos.

## Seguimiento 29-10-2026, 01:06 UTC: calidad FMD completa

Se cerraron las treinta condiciones FMD de calidad en caché y replay: tres
semillas, cinco pliegues y dos clasificadores. Se comprobaron para las treinta
fuentes los estados completos, los hashes de predicciones/métricas y la
vinculación hash del auditor al estado. Cada CSV tiene cinco métodos y 200
imágenes externas por método. Sin nueva inferencia, ajuste o reintento.

### F1 medio en caché: quince condiciones por clasificador, SIN latencia

| Método | SVM | ResMLP |
| --- | ---: | ---: |
| Completa-22 | 0,964746 | 0,957395 |
| Diversidad | 0,978259 | 0,977268 |
| Tómbola | 0,979242 | 0,976976 |
| Top-4 | 0,982302 | 0,979999 |
| Adaptativo | 0,977600 | 0,975970 |

Esta tabla es únicamente la etapa de calidad sobre embeddings archivados.
NO se une con latencias nuevas para representar F1 online. La cascada supera
a Completa en FMD, pero queda por debajo de Top-4 y de ambos ensambles en
los dos clasificadores. No se deduce significancia ni no inferioridad.
Fuentes: las treinta rutas `quality_run` y `quality_audit` del manifiesto;
FMD/42 conserva sus diez rutas previas, no duplicadas por la cola nocturna.

También cerró Outex13Official1360/SVM: 680 imágenes externas y 3.400
predicciones reproducidas por el auditor. F1 en caché: Completa 0,965551;
diversidad 0,945802; tómbola 0,939870; Top-4 0,928779; adaptativo 0,927581.
La pérdida frente a Completa es 0,037970 (3,797 puntos porcentuales), y frente
a Top-4 es 0,001197. Se conserva íntegro el resultado desfavorable; no se
cambia la selección, el margen ni el presupuesto. Fuente:
`jobs/Outex13Official1360_svm_s42_f0/quality/metrics.csv`, replay validado en
`quality_audit/audit.json`. No hay aún latencia publicada para esta condición.

Cobertura del corte: 31 condiciones de calidad con replay y nueve físicas
completas y auditadas (9.000 llamadas, 45 filas condición–método). Workers
6307/6315 vivos, sin `requires_review`; calidad en Outex/ResMLP y único
benchmark GPU 9932 en FMD/SVM/123/pliegue 3. Se comprobaron logs y auditoría
del nuevo pliegue físico 2. Persisten las puertas físicas de otros datasets.

## Seguimiento 29-10-2026, 01:21 UTC

Segundo cierre físico de cinco pliegues: FMD/SVM/123, consolidado en
`summary_FMD_svm_s123_online_v1/`. La consolidación volvió a comprobar hashes,
auditorías, cobertura disjunta de 1.000 imágenes y 5.000 llamadas. F1 y tiempos
provienen de las mismas llamadas, sin inferencia nueva.

| Método | F1 online medio por pliegue | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,963131 | 1752,338445 |
| Diversidad | 0,976939 | 351,346343 |
| Tómbola | 0,976911 | 358,958137 |
| Top-4 | 0,981000 | 268,388246 |
| Adaptativo | 0,972849 | 36,282589 |

La cascada pierde aproximadamente 0,008151 de F1 medio frente a Top-4
(0,815 puntos porcentuales); mantiene un tiempo observado menor. Este corte
es una semilla, no la media física final de las tres semillas de FMD.

Outex/ResMLP también completó calidad y replay de 3.400 predicciones sobre
680 imágenes. F1 en caché: adaptativo 0,960869; Completa 0,951996;
diversidad 0,952206; tómbola 0,957757; Top-4 0,927490. Aquí el adaptativo
supera numéricamente los cuatro controles, a diferencia de Outex/SVM. Fuente:
`jobs/Outex13Official1360_resmlp_s42_f0/quality/metrics.csv`, con auditoría
`CACHED_HEAD_PREDICTIONS_REPLAYED`. Se revisó el final del log, sin error.
Esto no prueba significancia ni incorpora aún latencia de Outex.

Cobertura del corte: cuarenta condiciones de calidad con replay (diez previas
y treinta nuevas), once físicas auditadas (11.000 llamadas, 55 filas
condición–método). Workers 6307/6315 activos, sin `requires_review`:
calidad en SoilOriginal/SVM/123/pliegue 3 y único benchmark GPU 10577 en
FMD/SVM/2026/pliegue 0. No se repitieron fallos, no se cambiaron tolerancias
y siguen vigentes las puertas de adaptación por dataset y de protocolo KTH.

## Seguimiento 29-10-2026, 01:36 UTC: Soil/SVM calidad completa

Las quince condiciones SoilOriginal/SVM cerraron calidad y replay. Auditoría
adicional de hashes, filas de predicciones y reconstrucción determinista de
los índices originales: todas coinciden exactamente con entrenamiento/test
persistidos. F1 medio de las quince condiciones en caché, SIN tiempos:

| Método | F1 medio |
| --- | ---: |
| Completa-22 | 0,881609 |
| Diversidad | 0,879225 |
| Tómbola | 0,877233 |
| Top-4 | 0,886389 |
| Adaptativo | 0,882957 |

La cascada supera numéricamente a Completa y los ensambles, pero pierde
0,003432 frente a Top-4. No se atribuye significancia ni se combina con
latencias de FMD.

### Incidencia del control de cobertura, resuelta sin repetir experimentos

Una comprobación ad hoc inicial falló porque asumía 228 imágenes por pliegue
en todas las semillas. El registro de la consulta fue `AssertionError`; no
fue un fallo del experimento ni del replay. Se conservan estos hechos aquí.
La inspección encontró que la partición original `StratifiedGroupKFold` tiene
tamaños [228,229,228,227,228] para semilla 123, sumando 1.140 imágenes; las
semillas 42 y 2026 tienen [228,228,228,228,228]. Se verificaron los quince
índices externos e internos contra `outer_indices` del programa original y
las filas de predicciones, sin ejecutar modelos, modificar particiones,
relajar tolerancias ni repetir condiciones. La discrepancia era la suposición
del control, no una cobertura incompleta de Soil. No se promueve el chequeo
fallido a prueba aprobada; lo sustituye esta comparación exacta con la fuente.
Fuente de particiones: `src/run_topk_individual_control.py:outer_indices` y
`results/extensions/soil_original/sample_manifests/SoilOriginal.csv`.

Cobertura inicial del corte: 48 condiciones de calidad/replay y doce físicas
auditadas (12.000 llamadas, sesenta filas condición–método). Se revisó la
auditoría del nuevo FMD/SVM/2026/0 y el log final Soil/SVM/2026/4. Workers
6307/6315 vivos, sin `requires_review`: calidad Soil/ResMLP/42/1 y único
benchmark GPU 11004 en FMD/SVM/2026/1. Sin cambios a fuentes activas,
protocolo, datos, manuscrito o repositorio remoto.

## Seguimiento 29-10-2026, 01:51 UTC

Avance sin nuevo cierre completo de dataset/clasificador: 49 condiciones de
calidad/replay y catorce físicas auditadas (14.000 llamadas, setenta filas
condición–método). Se consultaron la auditoría del nuevo FMD/SVM/2026/2 y
el replay/log final de Soil/ResMLP/42/1: completos, sin error registrado.
Workers 6307/6315 vivos, sin `requires_review`; calidad activa en
Soil/ResMLP/42/2 y único benchmark GPU 12604 en FMD/SVM/2026/3. Aún no se
consolida la semilla 2026 física: falta completar sus cinco pliegues.

Revisión de infraestructura, solo lectura: el ejecutor físico ya acepta un
dataset genérico, pero exige un diagnóstico DeiT cuyo hash de embedding
coincida con ese dataset. `verified_state_path` exige dos comprobaciones
finitas de igual forma aprobadas a 1e-4 y el hash del pooler recuperado. Esta
puerta se conserva; los metadatos o el éxito de FMD no la sustituyen. No se
ejecutaron diagnósticos GPU mientras el benchmark estaba activo ni se
modificó el ejecutor congelado. La cola original mantiene las retenciones
explícitas de otros datasets, por lo que no deben contarse como ya medidos.

## Seguimiento 29-10-2026, 02:06 UTC

Workers 6307/6315 activos y sin `requires_review`. Calidad: 52 condiciones
con replay (diez previas más 42 nuevas); online: quince auditadas (15.000
llamadas, 75 filas condición–método). El único benchmark GPU 12896 procesa
FMD/SVM/2026/pliegue 4; la semilla aún no se declaró cerrada en este corte.
Calidad activa: Soil/ResMLP/123/pliegue 0.

Trabajo independiente completado sin GPU: preparación de los vínculos DeiT
para CUReT [0,5611], Outex [0,1359], Soil [0,1139] y DTD [0,5639], fijados
por primera/última fila completa, sin mirar aciertos. Se verificaron formas,
finitud de los embeddings, etiquetas/manifiesto y hashes de las dos imágenes,
config, embedding, código y estado histórico recuperado. Evidencias nuevas:
`binding_preparation_v1/<dataset>/diagnostic.json`.

Estas cuatro preparaciones son `binding_inputs_prepared`, NO diagnósticos
aprobados ni paridad general. El script nuevo
`scripts/diagnose_deit_dataset_binding.py` requiere `--execute` para tocar la
GPU y conserva el umbral 1e-4. Rechaza benchmarks activos, KTH y nuevos
intentos de FMD. Ocho pruebas focalizadas aprobadas (tres nuevas y cinco del
adaptador recuperado). No se ejecutaron modelos, descargaron pesos o
modificaron scripts congelados. El plan operativo documenta que todavía no
hay cola automática de estos diagnósticos; deben despacharse con exclusión
GPU y resultados nuevos antes de preparar la cola física suplementaria.

ARS se aplicó inline para preservar evidencia/preparación separada de una
validación aprobada y no convertir la inicialización recuperada del pooler en
pesos preentrenados. No hubo cambios al manuscrito, commits o push.

## Seguimiento 29-10-2026, 02:21 UTC: FMD/SVM físico completo

Se completaron y auditaron las quince condiciones físicas FMD/SVM: tres
semillas por cinco pliegues. El consolidado verifica nuevamente hashes de
todos los archivos de evidencia y resume 15.000 llamadas (3.000 por método),
con 1.000 imágenes únicas que se repiten entre semillas. No son quince
datasets independientes. Tabla completa para este dataset/clasificador:

| Método | F1 online medio por pliegue | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,965072 | 1759,500817 |
| Diversidad | 0,978259 | 364,539990 |
| Tómbola | 0,979242 | 356,758867 |
| Top-4 | 0,982302 | 268,959611 |
| Adaptativo | 0,977600 | 38,629834 |

Fuente: `summary_FMD_svm_all_seeds_online_v1/dataset_summary.csv` y
`summary.json`; los CSV combinados preservan semilla, pliegue y cada llamada.
Media/mediana/p95 se calculan sobre las llamadas combinadas, no promediando
percentiles de los pliegues. F1 es la media de los quince F1 externos, no el
F1 agrupado de predicciones repetidas.

Frente a Top-4, el adaptativo pierde 0,004702 de F1 (0,470 puntos porcentuales)
y reduce aproximadamente 85,6% la latencia media observada. Frente a Completa
mejora el F1 medio en 0,012528. El entorno sigue siendo compartido, una
repetición por imagen; no se declara hardware aislado ni significancia.
La cifra online de Completa (0,965072) difiere de su calidad en caché
(0,964746): no se reemplazó por la histórica para ocultar esa diferencia.

Infraestructura de consolidación añadida:
`scripts/summarize_fmd_online_all_seeds.py`, sin nuevas inferencias. Tres
pruebas nuevas más tres del resumen de semilla: seis aprobadas. Conserva
hashes y rechaza semillas incompletas, duplicados y deriva de evidencias.

Cobertura inicial del corte: 54 condiciones de calidad/replay y diecisiete
físicas completas (17.000 llamadas, 85 filas condición–método). Workers
6307/6315 vivos, sin `requires_review`: calidad Soil/ResMLP/123/2 y único
benchmark GPU 13391 en FMD/ResMLP/42/2. El panel físico de ResMLP y de los
otros datasets aún no está completo; las preparaciones DeiT no lo habilitan.

## Seguimiento 29-10-2026, 02:36 UTC

Avance operativo sin un nuevo cierre completo: 56 condiciones de calidad con
replay y dieciocho físicas auditadas (18.000 llamadas, noventa filas
condición–método). Se consultaron auditoría y logs finales de
FMD/ResMLP/42/pliegue 2 y Soil/ResMLP/123/pliegue 3: etapas completas y sin
error registrado. No se publica una media física parcial de ResMLP como
resultado final de FMD.

Workers 6307/6315 vivos, sin `requires_review`: calidad activa en
Soil/ResMLP/123/pliegue 4, único benchmark GPU 13694 en
FMD/ResMLP/42/pliegue 3. Las comprobaciones DeiT preparadas siguen sin
ejecución GPU, respetando exclusión y dependencias. No hubo reintentos,
cambios metodológicos, modificaciones a fuentes activas, manuscrito o remoto.

## Seguimiento 29-10-2026, 02:51 UTC: FMD/ResMLP/42 físico completo

La primera semilla física de ResMLP cerró cinco pliegues y auditorías.
Consolidación nueva en `summary_FMD_resmlp_s42_online_v1/`: cobertura disjunta
de 1.000 imágenes, 5.000 llamadas, hashes de entradas/salidas comprobados y
F1/tiempos de las mismas llamadas. Sin ajuste o inferencia adicional.

| Método | F1 online medio por pliegue | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,963027 | 1771,110582 |
| Diversidad | 0,978971 | 382,088544 |
| Tómbola | 0,978035 | 365,907430 |
| Top-4 | 0,978017 | 268,746969 |
| Adaptativo | 0,972955 | 37,024610 |

La cascada pierde 0,005062 de F1 medio frente a Top-4, y también queda por
debajo de diversidad y tómbola; supera a Completa con tiempo observado menor.
No se presenta como resultado final de ResMLP/FMD: faltan dos semillas físicas.
La calidad online de Completa difiere de su versión en caché; ambas quedan
separadas, sin sustituir F1 para que coincida con el histórico.

Cobertura inicial del corte: 58 condiciones de calidad/replay y veinte
físicas auditadas (20.000 llamadas, cien filas condición–método). Se revisaron
logs de auditoría del último pliegue físico y replay de Soil/ResMLP/2026/0.
Workers 6307/6315 vivos, sin `requires_review`: calidad
Soil/ResMLP/2026/1 y único benchmark GPU 14184 en FMD/ResMLP/123/0. Se
mantienen las retenciones físicas de otros datasets y de protocolo KTH.

## Seguimiento 29-10-2026, 03:06 UTC

Avance sin nuevo cierre completo: sesenta condiciones de calidad/replay y
veintiuna físicas auditadas (21.000 llamadas, 105 filas condición–método).
Se consultaron auditorías y finales de log de FMD/ResMLP/123/pliegue 0 y
Soil/ResMLP/2026/pliegue 2: completos, sin error registrado. No se agregan
medias incompletas de ResMLP/FMD ni se mezclan tiempos con F1 en caché.

Workers 6307/6315 vivos, sin `requires_review`: calidad activa en
Soil/ResMLP/2026/3 y único benchmark GPU 14437 en FMD/ResMLP/123/1.
Se respetan las puertas de otros datasets y no se inicia ningún diagnóstico
GPU concurrente. Sin reintentos ni cambios a fuentes, método o manuscrito.

## Seguimiento 29-10-2026, 03:21 UTC: Soil calidad completa

Se cerraron las treinta condiciones SoilOriginal de calidad/replay, quince
por clasificador. Se volvieron a verificar hashes de estados, configuraciones,
métricas y predicciones; las treinta particiones coinciden exactamente con
`outer_indices`, y las predicciones cubren todas sus filas externas sin
repeticiones dentro de método/condición. Se respetan los tamaños variables
227–229 de la semilla 123; no se alteraron particiones.

### F1 medio en caché, quince condiciones por clasificador; SIN tiempos

| Método | SVM | ResMLP |
| --- | ---: | ---: |
| Completa-22 | 0,881609 | 0,862098 |
| Diversidad | 0,879225 | 0,874029 |
| Tómbola | 0,877233 | 0,874781 |
| Top-4 | 0,886389 | 0,866179 |
| Adaptativo | 0,882957 | 0,870302 |

En ResMLP, el adaptativo supera numéricamente a Completa y Top-4, pero pierde
frente a ambos ensambles. En SVM pierde frente a Top-4. No hay un ganador
uniforme de calidad. Son resultados del panel nuevo de heads congelados
entrenados en CPU, no una sustitución silenciosa de las cifras históricas.
Fuentes: `quality/metrics.csv`, `quality/status.json` y `quality_audit/audit.json`
de las treinta condiciones Soil del manifiesto. No se añadieron latencias de
otro dataset ni se declara significancia estadística.

Cobertura inicial del corte: 62 condiciones de calidad/replay y veintitrés
físicas auditadas (23.000 llamadas, 115 filas condición–método). Workers
6307/6315 vivos, sin `requires_review`; CPU pasó a CUReT/SVM/42/pliegue 0 y
único benchmark GPU 14914 en FMD/ResMLP/123/pliegue 3. Se inspeccionó el
final del log Soil/ResMLP/2026/4 y la auditoría del nuevo pliegue físico 2.
Persisten las puertas físicas de otros datasets y la reconciliación KTH.

## Seguimiento 29-10-2026, 03:36 UTC: CUReT/SVM calidad completa

Las dos direcciones canónicas de CUReT/SVM cerraron calidad y replay, con
2.806 imágenes de entrenamiento y 2.806 externas en cada dirección. Se
verificaron estados, hashes de métricas/predicciones y vínculo del auditor
al estado. F1 medio en caché, SIN latencias:

| Método | F1 medio |
| --- | ---: |
| Completa-22 | 0,998931 |
| Diversidad | 0,998752 |
| Tómbola | 0,998931 |
| Top-4 | 0,998574 |
| Adaptativo | 0,998396 |

La cascada queda por debajo de los cuatro controles en este promedio, con
una diferencia pequeña en una tarea cercana a saturación. No se interpreta
esa diferencia como equivalencia, significancia o mejora. Fuentes:
`jobs/CUReT_svm_s42_f{0,1}/quality/metrics.csv` y sus auditorías. Se revisó
el log final de la dirección 1, sin error registrado. CUReT/ResMLP y las
latencias de CUReT siguen pendientes.

Cobertura inicial del corte: 64 condiciones de calidad/replay y veinticuatro
físicas auditadas (24.000 llamadas, 120 filas condición–método). Workers
6307/6315 vivos, sin `requires_review`: calidad en CUReT/ResMLP/42/0 y
único benchmark GPU 15176 en FMD/ResMLP/123/4. Se comprobó la auditoría del
nuevo pliegue físico 3. Sin cambios científicos ni reintentos automáticos.

## Seguimiento 29-10-2026, 03:51 UTC: FMD/ResMLP/123 físico completo

Segunda semilla física de ResMLP cerrada y consolidada, cinco pliegues,
1.000 imágenes únicas y 5.000 llamadas. Evidencia nueva:
`summary_FMD_resmlp_s123_online_v1/`, con hashes y verificación de cobertura,
auditorías, F1 y latencias derivados de las mismas llamadas. Resultados de
esta semilla únicamente:

| Método | F1 online medio por pliegue | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,954085 | 1743,837270 |
| Diversidad | 0,975911 | 366,495582 |
| Tómbola | 0,972909 | 372,670571 |
| Top-4 | 0,978974 | 268,644099 |
| Adaptativo | 0,974927 | 34,168552 |

El adaptativo pierde 0,004047 de F1 medio frente a Top-4 y 0,000984 frente
a diversidad; supera a tómbola y Completa. No se declara un ganador global,
significancia ni equivalencia. Falta la semilla 2026 para cerrar FMD/ResMLP.

Cobertura del corte: 64 condiciones de calidad/replay y veintiséis físicas
auditadas (26.000 llamadas, 130 filas condición–método). Workers 6307/6315
vivos, sin `requires_review`. CUReT/ResMLP/42/0 sigue trabajando: log OOF
33/36, proceso 15295 con actividad CPU aproximadamente de dos hilos y 16
minutos transcurridos, no una corrida estancada. Único benchmark GPU 15598
en FMD/ResMLP/2026/1. Los diagnósticos preparados esperan exclusión GPU;
no se añadieron cargas ni se cambiaron protocolos o tolerancias.

## Seguimiento 29-10-2026, 04:06 UTC; programación adicional 04:09 UTC

Corte inicial: 65 condiciones de calidad/replay y veintisiete físicas
auditadas (27.000 llamadas, 135 filas condición–método). Workers originales
6307/6315 activos, sin `requires_review`; calidad CUReT/ResMLP/42/1 y online
FMD/ResMLP/2026/2. Se revisaron las auditorías del primer CUReT/ResMLP
(14.030 predicciones reproducidas) y nuevo pliegue físico FMD/2026/1.
Durante la preparación siguiente la GPU avanzó al pliegue 3 (PID 16028).

### Continuación suplementaria automática, todavía sin mediciones nuevas

Se preparó y lanzó en espera `scripts/overnight_multidataset_online.py`:
PID 16153, sesión de ejecución 3060, estado `waiting_for_fmd_or_gpu` a las
04:09 UTC. Registro nuevo:
`results/analysis/overnight_multidataset_online_20261029_v1/`.
56 condiciones físicas pendientes de Outex/Soil/CUReT/DTD; no incluye FMD ni
KTH y no duplica calidad. No se modificaron workers ni manifiesto originales.

La puerta comprueba las treinta condiciones FMD completas y sus auditorías
ligadas por hash, además de ausencia de benchmark GPU. Después ejecuta una
sola vez el diagnóstico de vínculo DeiT por dataset, preservando 1e-4; solo
un resultado aprobado permite medir. No se cambian heads, particiones,
presupuesto, selección, semilla o biblioteca. Fallos quedan requiere revisión,
sin reintentos; las otras condiciones independientes continúan. GPU siempre
secuencial, pesos offline y dos hilos CPU. El nuevo worker tiene lock propio,
hashes de manifiestos, protocolo, código/config y respeta la misma fecha
límite de despacho, 09:42:43 UTC.

Pruebas de infraestructura: catorce aprobadas (seis nuevas de puertas/colas,
tres del detector y cinco de evidencia del pooler). Esto prueba controles
locales, no aprueba los diagnósticos científicos pendientes. El seguimiento
debe consultar también el nuevo `worker.json`, `bindings/` y `jobs/`.
Ninguna condición de esta cola se cuenta todavía como medida ni se añade a
medias completas. Sin descargas, cambios al manuscrito, commits o push.

## Seguimiento 29-10-2026, 04:21 UTC

Cobertura del corte: 65 condiciones de calidad/replay y veintinueve físicas
auditadas (29.000 llamadas, 145 filas condición–método). Se revisaron la
auditoría y el final de log de FMD/ResMLP/2026/3: completos, sin error.
La última condición física FMD/ResMLP/2026/4 todavía está activa; no se
declaran completas sus treinta condiciones ni se consolida ResMLP/FMD antes
de su auditoría final.

Workers originales 6307/6315 vivos, sin `requires_review`. CUReT/ResMLP/42/1
sigue activo con dos hilos CPU y ajuste de cabezas externas 11/29. Único benchmark GPU 16564,
el último FMD. Worker suplementario 16153 vivo en `waiting_for_fmd_or_gpu`,
sin diagnósticos ni mediciones despachados. La exclusión y la puerta de cierre
FMD operan como se esperaba; no se duplica carga para acelerar el seguimiento.

## Seguimiento 29-10-2026, 04:36 UTC: FMD físico cerrado y dos vínculos fallidos

### FMD: treinta condiciones físicas completas, cinco métodos

ResMLP terminó su tercera semilla. Consolidación nueva y comprobada en
`summary_FMD_resmlp_s2026_online_v1/` y
`summary_FMD_resmlp_all_seeds_online_v1/`. F1 y tiempos de las mismas llamadas,
sin ajustes o inferencia adicional. Resumen completo de FMD/ResMLP:

| Método | F1 online medio por pliegue (15 condiciones) | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,957728 | 1759,695352 |
| Diversidad | 0,977268 | 373,453197 |
| Tómbola | 0,976976 | 367,836104 |
| Top-4 | 0,979999 | 258,562295 |
| Adaptativo | 0,975970 | 36,354072 |

Se preserva la diferencia con la calidad en caché de Completa (0,957395).
El adaptativo pierde 0,004029 de F1 frente a Top-4, con menor tiempo medio
observado. No se declara equivalencia ni hardware aislado. FMD completo:
treinta condiciones, 30.000 llamadas, 150 filas condición–método. Las mismas
1.000 imágenes reaparecen entre semillas, no son 30.000 imágenes únicas.

### Fallos relevantes: Outex y Soil retenidos, sin medición o reintento

Después del cierre auditado de FMD se ejecutaron secuencialmente los vínculos
DeiT fijados previamente. Evidencias íntegras en la cola suplementaria:

| Dataset | Filas comprobadas | Error absoluto máximo por fila | Resultado a 1e-4 |
| --- | --- | --- | --- |
| Outex13Official1360 | 0, 1359 | 0,213217; 0,200802 | No pasa |
| SoilOriginal | 0, 1139 | 0,189241; 0,185920 | No pasa |
| CUReT | 0, 5611 | 1,043e-7; 1,737e-7 | Pasa |

Son diferencias de representación sustanciales para Outex/Soil, no una
justificación para relajar tolerancia. Son compatibles con un estado histórico
de pooler diferente, pero la causa exacta aún no está demostrada. Los dos
diagnósticos constan como `diagnostic_complete`, `all_rows_pass=false`,
`requires_review=true`, con vectores, hashes y logs preservados. Se marcaron
32 condiciones físicas dependientes (dos Outex, treinta Soil) requiere
revisión sin ejecutar sus benchmarks. No se omitió DeiT, cambió semilla,
reextrajo entrenamiento ni inició una búsqueda/repetición automática.
Resolver estos vínculos requiere revisar la representación original y una
decisión explícita antes de nuevas pruebas numéricas o cambios científicos.

CUReT sí pasó las dos filas a tolerancia original y comenzó su primer
benchmark físico SVM (PID 16899), único proceso GPU. Esto valida el vínculo
acotado, no paridad universal de todos los extractores. DTD aún espera su
diagnóstico; KTH mantiene su reserva de protocolo.

### Estado operativo

Calidad/replay: 66 condiciones completas (FMD 30, Outex 2, Soil 30, CUReT 4);
CPU 6307 activo en DTD/SVM/42/0. Online original 6315 terminó sus 28 nuevas
condiciones, más dos pilotos gestionados antes, y espera sin trabajo GPU.
Suplementaria 16153 activa, cero condiciones físicas completas y 32 retenidas
por los dos diagnósticos; no son 32 ejecuciones GPU fallidas. Restan cuatro
condiciones físicas CUReT, veinte DTD y ocho KTH, además de resolver las 32
retenidas. Ningún parcial de CUReT se cuenta como media completa.

## Seguimiento 29-10-2026, 04:51 UTC

Sin un nuevo cierre físico o fallo: treinta condiciones online completas
(FMD) y 67 condiciones de calidad/replay. DTD/SVM/42/pliegue 0 terminó
calidad y replay de 9.400 predicciones; se revisaron su auditoría y final del
log. CPU 6307 trabaja ahora en DTD/SVM/42/pliegue 1.

La suplementaria 16153 sigue midiendo CUReT/SVM/42/0, único benchmark GPU
16899, con checkpoint de 2.450 llamadas sobre 14.030 previstas. Es progreso,
no cobertura completa ni una tabla de F1/latencia publicable todavía. La cola
online original 6315 espera sin despachar GPU. Las 32 condiciones dependientes
de Outex/Soil siguen requiere revisión por los dos diagnósticos ya informados;
no hay reintentos. DTD espera diagnóstico y KTH reconciliación. Se mantienen
los resultados FMD completos separados de esos pendientes.

## Seguimiento 29-10-2026, 05:06 UTC

Sin nuevo cierre físico ni fallo: 68 condiciones de calidad/replay, treinta
físicas completas (FMD) y 32 retenidas por los vínculos DeiT ya informados.
DTD/SVM/42/1 completó replay de 9.400 predicciones; auditoría y log final
consultados. CPU 6307 avanza en DTD/SVM/42/2, sin `requires_review` nuevo.

La suplementaria 16153 continúa en CUReT/SVM/42/0, único benchmark GPU 16899,
con 4.050/14.030 llamadas registradas. Se revisó el log y el incremento de
checkpoint; sigue activo y no se contabiliza como condición completa. La
cola online original espera sin competir por GPU. No se repitieron los
diagnósticos fallidos ni se publicaron medias parciales como completas.

Inspección causal solo lectura: el script heredado
`scripts/extract_curet_soil.sh` invoca extracciones por descriptor, pero no
demuestra por sí solo la procedencia del archivo actual SoilOriginal ni el
estado exacto del pooler. La búsqueda de la etiqueta de construcción Outex
en scripts/src no localizó un generador. No se convirtió esta ausencia en
diagnóstico causal ni se ejecutaron nuevas pruebas numéricas sobre los casos
fallidos. Se mantienen las evidencias y la revisión pendiente.

## Seguimiento 29-10-2026, 05:21 UTC

Sin nuevo cierre físico ni fallo: 69 condiciones de calidad/replay y treinta
físicas completas (FMD), además de las 32 retenidas ya informadas. La nueva
condición DTD/SVM/42/2 terminó calidad y replay de 9.400 predicciones, con
marcador `complete`; auditoría y final del log consultados. CPU 6307 activo
en DTD/SVM/42/3, sin fallos nuevos.

CUReT/SVM/42/0 sigue en medición física, único benchmark GPU 16899:
5.700/14.030 llamadas en checkpoint, frente a 4.050 en el corte anterior.
Worker suplementario 16153 activo, cero condiciones físicas terminadas aún,
32 requiere revisión sin reintento. El online original continúa esperando.
No se derivaron resultados finales de ese checkpoint ni se modificaron
recetas, fuentes activas, tolerancias, particiones o manuscrito.

## Seguimiento 29-10-2026, 05:36 UTC

Sin cierre físico o fallo adicional: setenta condiciones de calidad/replay,
treinta físicas completas y 32 retenidas por los dos vínculos conocidos.
DTD/SVM/42/3 cerró calidad y auditoría de 9.400 predicciones; se consultaron
el auditor y el final del log. CPU 6307 sigue en DTD/SVM/42/4, sin fallos
nuevos. La suplementaria 16153 continúa CUReT/SVM/42/0: checkpoint
7.300/14.030 llamadas, frente a 5.700 en el corte previo, único benchmark
GPU 16899. No es aún una condición completa ni una nueva media publicable.

Revisión independiente solo lectura de la reserva KTH: el plan de cierre
vigente exige reconciliar muestras físicas, entrenamiento, selección interna,
transformaciones y cache N-grams a nivel de filas. La existencia de cuatro
claves/splits o la sensibilidad estadística ya calculada no cumplen esa
puerta. Se conservan las ocho condiciones KTH retenidas, sin activar nuevas
corridas ni sustituir medias para forzar concordancia. No hubo cambios a
fuentes, método, tolerancia, datos, manuscrito o remoto.

## Seguimiento 29-10-2026, 05:51 UTC

Sin nuevo cierre físico ni fallo: 71 condiciones de calidad/replay, treinta
físicas completas (FMD) y 32 retenidas conocidas. DTD/SVM/42/4 terminó su
calidad y replay de 9.400 predicciones; marcador completo, auditoría y log
final consultados. CPU 6307 avanza al split oficial 6 (índice 5); DTD tiene
diez splits previstos, no cinco, por lo que todavía no se agrega como cerrado.

CUReT/SVM/42/0 continúa con 8.950/14.030 llamadas registradas, frente a
7.300 previamente. Worker suplementario 16153 y único benchmark GPU 16899
siguen vivos, sin casos nuevos requiere revisión. Las retenciones Outex/Soil
siguen vigentes, sin reintentos ni cambios de representación. KTH retenido y
DTD físico pendiente de diagnóstico. Sin publicación de F1/tiempo parcial.

## Seguimiento 29-10-2026, 06:06 UTC

Sin nuevo cierre físico o fallo: 72 condiciones de calidad/replay, treinta
físicas completas y 32 retenidas ya documentadas. DTD/SVM/42/5 terminó
calidad y replay de 9.400 predicciones; marcador completo, auditoría y log
final consultados. CPU 6307 activo en DTD/SVM/42/6, sin `requires_review`.

CUReT/SVM/42/0 alcanza 10.550/14.030 llamadas registradas, frente a 8.950
en el corte previo. Único benchmark GPU 16899 y suplementaria 16153 vivos,
sin nuevas retenciones. No se publica todavía F1/latencia de esa condición ni
se reinician Outex/Soil. DTD conserva sus diez splits y KTH su puerta de
reconciliación. Sin cambios de fuentes, método, tolerancia o manuscrito.

## Seguimiento 29-10-2026, 06:21 UTC

Sin nuevo cierre físico ni fallo: 73 condiciones de calidad/replay y treinta
físicas completas; persisten las 32 retenciones conocidas. DTD/SVM/42/6
terminó con replay de 9.400 predicciones, marcador completo, auditoría y log
final consultados. CPU 6307 continúa en DTD/SVM/42/7, sin fallos nuevos.

La suplementaria 16153 sigue en CUReT/SVM/42/0, único benchmark GPU 16899:
12.200/14.030 llamadas registradas frente a 10.550 previamente. Todavía
no se incorpora esa condición a la cobertura física completa ni se publica
una media de CUReT. No se reintentaron diagnósticos o benchmarks retenidos,
no se duplicó carga GPU ni se alteraron recetas o límites.

## Seguimiento 29-10-2026, 06:36 UTC

Sin nuevo cierre físico o fallo: 74 condiciones de calidad/replay y treinta
físicas completas, con las 32 retenciones conocidas. DTD/SVM/42/7 cerró
calidad y replay de 9.400 predicciones, marcador completo, auditoría y log
final consultados. CPU 6307 trabaja en DTD/SVM/42/8, sin fallos nuevos.

CUReT/SVM/42/0 alcanza 13.800/14.030 llamadas en checkpoint, todavía en
`timing_online`; no se promueve a condición completa antes del estado final
y su auditoría. Suplementaria 16153 y único benchmark GPU 16899 vivos. No se
repitieron diagnósticos fallidos, se solaparon benchmarks o cambiaron fuentes.

## Seguimiento 29-10-2026, 06:51 UTC: primera dirección física CUReT completa

CUReT/SVM/42/dirección 0 completó 2.806 imágenes externas por método,
14.030 llamadas en total. Auditoría `ONLINE_CALL_RECORDS_REAGGREGATED`, F1
y tiempos desde las mismas llamadas, sin pretender paridad universal de
vectores ni medición independiente de hardware. Resultado SOLO de esta
dirección, no media final CUReT:

| Método | F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,997862 | 1696,588824 |
| Diversidad | 0,997861 | 412,546214 |
| Tómbola | 0,998218 | 346,201262 |
| Top-4 | 0,998218 | 270,124075 |
| Adaptativo | 0,997505 | 33,571299 |

El adaptativo pierde aproximadamente 0,000713 de F1 frente a Top-4
(0,071 puntos porcentuales), con menor latencia media observada. No se
declara equivalencia ni significancia. Fuentes de la cola suplementaria:
`jobs/CUReT_svm_s42_f0/online/online_summary.csv` y
`jobs/CUReT_svm_s42_f0/online_audit/audit.json`. Se inspeccionó el log final
del auditor. La segunda dirección sigue pendiente de cierre y auditoría.

Cobertura inicial del corte: 75 condiciones de calidad/replay, 31 físicas
completas y auditadas (44.030 llamadas, 155 filas condición–método), 32
retenidas por los vínculos fallidos. DTD/SVM/42/8 cerró calidad/replay de
9.400 predicciones, auditoría y log consultados; CPU 6307 en DTD/SVM/42/9.
Suplementaria 16153 viva, un caso completado, sin nuevas retenciones; único
benchmark GPU 21248 ejecuta CUReT/SVM/42/1. El online original espera y no
compite. Sin reintentos, cambios científicos, manuscrito, commits o push.

## Seguimiento 29-10-2026, 07:06 UTC: DTD/SVM calidad completa

Los diez splits oficiales DTD/SVM cerraron calidad y replay, 1.880 imágenes
externas por split y cinco métodos. Se comprobaron los diez hashes de config,
estados, métricas/predicciones y vínculos del auditor. No se presume que los
splits oficiales constituyan datasets independientes o imágenes disjuntas.
F1 medio en caché, SIN latencias:

| Método | F1 medio (10 splits) |
| --- | ---: |
| Completa-22 | 0,863854 |
| Diversidad | 0,873424 |
| Tómbola | 0,872351 |
| Top-4 | 0,868890 |
| Adaptativo | 0,866806 |

La cascada supera numéricamente a Completa, pero pierde frente a ambos
ensambles y Top-4. No se optimiza la regla usando estos resultados ni se
adjuntan tiempos de FMD. Fuente: las diez rutas DTD/SVM `quality_run` y
`quality_audit` del manifiesto. Se inspeccionó el auditor del último split.

Cobertura inicial del corte: 76 condiciones de calidad/replay, 31 físicas
completas (44.030 llamadas) y 32 retenidas por los vínculos conocidos. CPU
6307 pasó a DTD/ResMLP/42/0. Suplementaria 16153 mide la segunda dirección
CUReT/SVM, único benchmark GPU 21248, con 2.900/14.030 llamadas registradas.
Sin nuevos fallos ni retenciones; no se publica media física de CUReT hasta
cerrar y auditar esa dirección. KTH permanece retenido y DTD espera vínculo.

## Seguimiento 29-10-2026, 07:21 UTC

Sin cierre físico ni fallo nuevo: 77 condiciones de calidad/replay y 31
físicas completas (44.030 llamadas), más las 32 retenciones conocidas.
DTD/ResMLP/42/0 cerró calidad y replay de 9.400 predicciones, marcador
completo, auditoría y log final consultados. CPU 6307 continúa con el segundo
split DTD/ResMLP (índice 1), sin `requires_review` nuevo.

Suplementaria 16153 y único benchmark GPU 21248 siguen en la segunda
dirección CUReT/SVM: 4.500/14.030 llamadas en checkpoint frente a 2.900
previamente. No se incorpora a medias completas todavía ni se toman medidas
para sortear los diagnósticos fallidos de Outex/Soil. Se mantiene KTH
retenido, DTD físico pendiente y la misma ventana/recetas de ejecución.

## Seguimiento 29-10-2026, 07:36 UTC

Cobertura completa sin cambios: 77 condiciones de calidad/replay, 31 físicas
auditadas y las 32 retenciones conocidas. Ambos trabajos activos avanzan:
DTD/ResMLP/42/1 en OOF 32/35 (CPU 21992), segunda dirección CUReT/SVM en
6.150/14.030 llamadas (único benchmark GPU 21248), frente a 4.500 previamente.
Workers 6307/16153 vivos; logs consultados, sin fallos nuevos. No se relanzó
ningún proceso ni se convirtieron esos checkpoints en resultados completos.

## Seguimiento 29-10-2026, 07:52 UTC

Sin nuevo cierre físico ni fallo: 78 condiciones de calidad/replay, 31
físicas auditadas (44.030 llamadas) y 32 retenidas conocidas. El segundo
split DTD/ResMLP terminó calidad y replay de 9.400 predicciones; se revisaron
auditoría, marcador completo y log final. CPU 6307 pasó a DTD/ResMLP/42/2.

Segunda dirección CUReT/SVM aún activa: 7.750/14.030 llamadas en checkpoint,
frente a 6.150 previamente. Suplementaria 16153 y único benchmark GPU 21248
vivos, sin retenciones nuevas. Se mantienen recetas, tolerancias y ventana;
no se repiten fallos, se suman resultados incompletos o se modifica manuscrito.

## Seguimiento 29-10-2026, 08:07 UTC

Cobertura completa sin cambios: 78 condiciones de calidad/replay, 31 físicas
auditadas y 32 retenidas. Los logs muestran avance, no estancamiento:
DTD/ResMLP/42/2 ajusta cabezas externas 10/21 (CPU 22596), y segunda dirección
CUReT/SVM alcanza 9.350/14.030 llamadas frente a 7.750 previamente (único
benchmark GPU 21248). Workers 6307/16153 vivos, sin fallos nuevos. No se
despacharon trabajos duplicados ni se promovieron parciales a resultados finales.

## Seguimiento 29-10-2026, 08:22 UTC

Sin nuevo cierre físico o fallo: 79 condiciones de calidad/replay, 31 físicas
completas y 32 retenidas. DTD/ResMLP/42/2 cerró calidad y replay de 9.400
predicciones, marcador completo, auditoría y log final consultados. CPU 6307
continúa en DTD/ResMLP/42/3, sin `requires_review` nuevo.

La segunda dirección CUReT/SVM registra 10.950/14.030 llamadas, frente a
9.350 previamente. Suplementaria 16153 y único benchmark GPU 21248 vivos.
No se publica una media final hasta la auditoría de ambas direcciones; los
vínculos fallidos, KTH y DTD físico mantienen sus puertas, sin reintentos.

## Seguimiento 29-10-2026, 08:37 UTC

Sin nuevo cierre físico ni fallo: ochenta condiciones de calidad/replay,
31 físicas completas y 32 retenidas. DTD/ResMLP/42/3 cerró calidad y replay
de 9.400 predicciones; marcador completo, auditoría y log final consultados.
CPU 6307 pasó al split índice 4; no se presenta ResMLP/DTD como completo
con cuatro de sus diez splits terminados.

Segunda dirección CUReT/SVM registra 12.550/14.030 llamadas frente a
10.950 previamente. Suplementaria 16153 y único benchmark GPU 21248 vivos,
sin casos nuevos requiere revisión. Se preserva el final pendiente y su
auditoría antes de consolidar CUReT; no se modificaron métodos o tolerancias.

## Seguimiento 29-10-2026, 08:52 UTC: CUReT/SVM físico completo

Ambas direcciones canónicas terminaron y pasaron sus auditorías de llamadas.
Consolidación nueva en la suplementaria:
`summary_CUReT_svm_online_v1/`, con comprobación de hashes, referencias a
heads, cobertura disjunta de 5.612 imágenes, 28.060 llamadas y recomputación
de F1/tiempos desde las mismas llamadas. Resultados completos CUReT/SVM:

| Método | F1 online medio por dirección (2 condiciones) | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,998931 | 1712,570869 |
| Diversidad | 0,998752 | 404,018992 |
| Tómbola | 0,998931 | 348,359768 |
| Top-4 | 0,998574 | 270,692594 |
| Adaptativo | 0,998396 | 36,830131 |

La cascada pierde aproximadamente 0,000178 de F1 medio frente a Top-4
(0,018 puntos porcentuales) y reduce alrededor de 86,4% la latencia media
observada. Frente a Completa la pérdida es aproximadamente 0,000535.
No se declara equivalencia o significancia. El consolidado también conserva
por separado el F1 agrupado; p95/mediana se calculan sobre llamadas, no como
promedios de percentiles. Entorno compartido y una repetición por imagen.

Infraestructura de consolidación nueva: `scripts/summarize_curet_online.py`,
sin inferencia o nuevos ajustes. Tres pruebas nuevas más cinco del auditor:
ocho aprobadas. Se rechazan direcciones faltantes, imágenes solapadas, deriva
de evidencia y discrepancias aritméticas. Los hashes de entrada/salida quedan
en `summary.json`; se preservan los CSV de cada llamada y dirección.

Cobertura inicial: ochenta condiciones de calidad/replay, 32 físicas completas
y auditadas (58.060 llamadas, 160 filas condición–método) y 32 retenidas.
CPU 6307 sigue DTD/ResMLP/42/4. La suplementaria 16153 pasó a CUReT/ResMLP/42/0,
único benchmark GPU 24013, tras cerrar el SVM; se consultaron auditoría y
marcador completos de la segunda dirección SVM. No hay fallos nuevos ni
reintentos de Outex/Soil. DTD físico y KTH conservan sus puertas.

## Seguimiento 29-10-2026, 09:07 UTC

Sin nuevo cierre físico ni fallo: 81 condiciones de calidad/replay, 32
físicas auditadas (58.060 llamadas) y 32 retenidas conocidas. DTD/ResMLP/42/4
cerró calidad y replay de 9.400 predicciones, marcador completo, auditoría y
log final consultados. CPU 6307 pasó al split índice 5: faltan aún cinco
splits para completar DTD/ResMLP, incluido el activo.

Suplementaria 16153 mide CUReT/ResMLP/42/0, único benchmark GPU 24013,
con 1.650/14.030 llamadas registradas. No hay retenciones nuevas ni reintentos.
Sigue vigente el cierre de despacho 09:42:43 UTC: una condición ya activa
conserva su timeout propio; la llegada de esa hora no debe matar una corrida
sana ni interpretarse como panel terminado. Los casos nunca despachados
deben permanecer explícitamente pendientes, no figurar como fallos científicos.

## Seguimiento 29-10-2026, 09:22 UTC

Cobertura completa sin cambios: 81 condiciones de calidad/replay, 32 físicas
auditadas y 32 retenidas. Hay avance comprobado en logs: DTD/ResMLP/42/5
en ajuste externo 5/21 (CPU 24420), y CUReT/ResMLP/42/0 en 3.250/14.030
llamadas frente a 1.650 previamente (único benchmark GPU 24013). Workers
6307/16153 vivos, sin fallos o retenciones nuevos. No se reinician procesos,
amplían timeouts de casos fallidos ni se presentan estos parciales como cierre.

## Seguimiento 29-10-2026, 09:37 UTC: continuación de pendientes no iniciados

Corte inicial: 82 condiciones de calidad/replay, 32 físicas auditadas y
32 retenidas conocidas. DTD/ResMLP/42/5 cerró calidad/replay de 9.400
predicciones, auditoría y final del log consultados. CPU original 6307
trabaja en DTD/ResMLP/42/6; único benchmark GPU 24013 en CUReT/ResMLP/42/0,
con 4.850/14.030 llamadas. Suplementaria 16153 viva, sin retenciones nuevas.

Se preparó, probó y lanzó `scripts/resume_overnight_quality.py`, en espera de
que el worker de calidad original cierre normalmente su ventana y termine
la condición activa. Registro nuevo:
`results/analysis/overnight_quality_resume_20261029_v1/continuation.json`.
Estado observado `waiting_for_original_quality_worker`, sin nuevos jobs
despachados. El filtro admite solo condiciones nunca iniciadas: excluye
marcadores de intento, cualquier resultado parcial, fallos, completos,
managed y retenciones KTH. No repite ningún experimento fallido.

La continuación tendrá tres horas de despacho desde el traspaso, mismos
timeouts y dos hilos CPU; usa nuevos directorios, configs científicas
originales y un manifiesto con hashes del original, fuentes y protocolo.
Nueve pruebas focalizadas aprobadas (cinco nuevas y cuatro del worker).
No modifica ni interrumpe los workers activos. Las rutas tardías de calidad
deben leerse de su manifiesto antes de preparar una futura ejecución física;
no se reemplazan rutas del manifiesto anterior ni se cuentan como completas.

## Seguimiento 29-10-2026, 09:52 UTC: traspaso de calidad sin duplicados

La ventana original de calidad terminó normalmente después de cerrar
DTD/ResMLP/42/6 y su replay de 9.400 predicciones. Se consultó el auditor.
Workers originales 6307/6315 ya salieron con `dispatch_window_ended`, sin
fallos de calidad; sus condiciones completas no se repiten. Cobertura de
calidad/replay: 83 condiciones. Físicas completas: 32 (58.060 llamadas),
con 32 retenidas por los dos vínculos fallidos ya informados.

La continuación 25570 realizó el traspaso a las 09:48:16 UTC y registra SOLO
tres condiciones nunca iniciadas: DTD/ResMLP/42/7, /8 y /9. Está ejecutando
la primera en una ruta nueva, con ventana de tres horas y dos hilos CPU;
cero condiciones completadas o fallidas en esa cola al corte. Su manifiesto
es la fuente de las nuevas rutas, no el manifiesto original. Se verificó el
estado y ausencia del worker CPU anterior antes de contar el traspaso.

La suplementaria 16153 sigue en CUReT/ResMLP/42/0, único benchmark GPU 24013:
6.450/14.030 llamadas frente a 4.850 previamente. La ventana de despacho
suplementaria ya venció, pero deja terminar esa condición sana bajo su
timeout original. No se le contabiliza como completa todavía ni se amplía
el límite de un experimento fallido. Sin reintentos ni nuevos fallos.

## Seguimiento 29-10-2026, 10:07 UTC: siguiente tramo físico en espera

Cobertura completa sin cambios: 83 condiciones de calidad/replay, 32 físicas
auditadas y 32 retenidas. CPU de continuación 25570 trabaja DTD/ResMLP/42/7,
log OOF 32/34. Único benchmark GPU 24013 avanza CUReT/ResMLP/42/0:
8.050/14.030 llamadas, frente a 6.450 previamente. Ambos workers vivos,
sin fallos nuevos, y las ventanas anteriores no interrumpen esas condiciones.

Se preparó, probó y lanzó en espera `scripts/resume_multidataset_online.py`.
Registro `results/analysis/overnight_online_resume_20261029_v2/continuation.json`:
espera que la suplementaria termine normalmente y quede libre la GPU. Solo
admitirá condiciones nunca intentadas, sin marcador ni salida parcial;
excluye las 32 retenidas y los completos. No repite Outex/Soil ni KTH.

Reutilizará por copia hash-verificada únicamente el vínculo CUReT ya
aprobado. Antes de otro benchmark largo podrá ejecutar una sola vez el
vínculo DTD pendiente, a tolerancia original, conservando fallos sin retry.
La calidad tardía se enlaza desde su manifiesto nuevo solo para la misma
config científica/hash. Salidas nuevas, fuentes/protocolo/hash custodiados,
tres horas de despacho desde el traspaso y timeouts propios sin ampliaciones.
Catorce pruebas focalizadas aprobadas (cinco nuevas, seis de la cola y tres
del detector). Ninguna medición nueva se atribuye a este wrapper en espera.

## Seguimiento 29-10-2026, 10:22 UTC

Sin nuevo cierre físico o fallo: 84 condiciones de calidad/replay (83 del
registro inicial y una de la continuación), 32 físicas completas y 32
retenidas. DTD/ResMLP/42/7 cerró calidad y replay de 9.400 predicciones en
la ruta nueva; auditoría, marcador completo y log final consultados. CPU
25570 avanzó al split índice 8; queda además el 9 para cerrar DTD/ResMLP.

CUReT/ResMLP/42/0 sigue con 9.600/14.030 llamadas frente a 8.050 previamente,
único benchmark GPU 24013, suplementaria 16153 viva y sin fallos nuevos.
Continuación física 26367 permanece esperando su salida, sin modelos o
diagnósticos despachados ni competencia GPU. No se contabilizan esos
pendientes como medidos ni se reintentan las retenciones Outex/Soil/KTH.

## Seguimiento 29-10-2026, 10:37 UTC

Cobertura completa sin cambios: 84 condiciones de calidad/replay, 32 físicas
auditadas y 32 retenidas. Avance en logs: DTD/ResMLP/42/8 ajusta cabezas
externas 10/20 (CPU 26455); CUReT/ResMLP/42/0 registra 11.200/14.030 llamadas
frente a 9.600 previamente (único benchmark GPU 24013). Workers 25570/16153
vivos, sin fallos nuevos; continuación física 26367 sigue esperando sin
despachos. No se duplica trabajo ni se promueven checkpoints a resultados.

## Seguimiento 29-10-2026, 10:52 UTC

Sin cierre físico o fallo nuevo: 85 condiciones de calidad/replay (83 del
registro inicial y dos de la continuación), 32 físicas auditadas y 32
retenidas. DTD/ResMLP/42/8 cerró calidad y replay de 9.400 predicciones en
su ruta nueva; auditoría, marcador completo y log final consultados. CPU
25570 avanza al último split, índice 9. No se agrega DTD/ResMLP como cerrado
antes de terminar ese split y su auditoría.

CUReT/ResMLP/42/0 sigue en 12.800/14.030 llamadas frente a 11.200 previamente,
único benchmark GPU 24013 y suplementaria 16153 vivos. La continuación
física 26367 espera sin ejecutar modelos ni repetir diagnósticos. No se
añaden estos checkpoints a la cobertura física completa ni a medias finales.

## Seguimiento 29-10-2026, 11:07 UTC: calidad no-KTH cerrada y vínculo DTD aprobado

### Calidad: 86 condiciones completas, no confundir con tiempos físicos

La continuación de calidad cerró sus tres splits nunca iniciados. DTD/ResMLP
tiene sus diez splits oficiales completos, con hashes de config, estados,
métricas/predicciones y vínculos del auditor comprobados; 1.880 imágenes
externas por split, cinco métodos. F1 medio en caché, SIN tiempos:

| Método | F1 medio DTD/ResMLP (10 splits) |
| --- | ---: |
| Completa-22 | 0,861270 |
| Diversidad | 0,877080 |
| Tómbola | 0,874513 |
| Top-4 | 0,861311 |
| Adaptativo | 0,866087 |

La cascada supera numéricamente a Completa y Top-4, pero pierde frente a
los ensambles. Fuentes: siete rutas DTD/ResMLP del manifiesto inicial y tres
rutas nuevas /7–9 del manifiesto de continuación. No se usan las rutas
antiguas inexistentes para esos últimos splits. Se verificó el replay final
de 9.400 predicciones. Calidad/replay de cinco datasets sin KTH: 86/86
condiciones cerradas; las ocho KTH siguen retenidas, no fallidas.

### Primera dirección física CUReT/ResMLP cerrada y auditada

2.806 imágenes externas y 14.030 llamadas. Resultados SOLO de esta dirección:

| Método | F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,998218 | 1730,345622 |
| Diversidad | 0,997861 | 412,045667 |
| Tómbola | 0,998218 | 373,055234 |
| Top-4 | 0,997149 | 270,773708 |
| Adaptativo | 0,997861 | 31,010355 |

La cascada supera numéricamente a Top-4 en esta dirección y es más rápida;
no se extrapola a la segunda dirección ni a la media final. Fuente:
suplementaria v1 `jobs/CUReT_resmlp_s42_f0/online/online_summary.csv` y su
auditor `ONLINE_CALL_RECORDS_REAGGREGATED`.

### Traspaso físico y diagnóstico DTD, sin reintentos

La suplementaria v1 terminó normalmente su ventana al completar esa dirección.
La continuación 26367 preparó 21 condiciones nunca iniciadas: última dirección
CUReT/ResMLP y veinte DTD. Reutilizó por copia hash-verificada el vínculo
CUReT aprobado, sin repetir su diagnóstico. DTD se diagnosticó UNA vez en
filas fijas 0 y 5639: errores máximos 5,124e-5 y 2,065e-5, ambos menores a
1e-4; estado `diagnostic_complete`, `all_rows_pass=true`. Evidencia:
v2 `bindings/DTD/diagnostic.json`, vectores y hashes preservados. Es un vínculo
acotado, no paridad de todos los extractores ni latencia publicada de DTD.

Worker v2 arrancó a las 11:04 UTC, único benchmark GPU 27537 midiendo la
segunda dirección CUReT/ResMLP. Está preparado para medir DTD después bajo
las recetas congeladas y con F1 de las mismas llamadas online. Ningún
Outex/Soil retenido entró en la continuación. Cobertura física cerrada:
33 condiciones, 72.090 llamadas y 165 filas condición–método. Persisten las
32 retenciones de vínculos y ocho KTH. No hay fallos nuevos ni medias finales
de CUReT/ResMLP o DTD físico antes de cerrar su cobertura.

## Seguimiento 29-10-2026, 11:22 UTC

Cobertura completa sin cambios: 86 condiciones de calidad/replay no-KTH,
33 físicas auditadas (72.090 llamadas), 32 retenidas de Outex/Soil y ocho
KTH retenidas por protocolo. La calidad de continuación tiene sus tres jobs
completos y espera sin entrenamiento activo; no se duplican ni reinician.

La continuación física 26367 sigue con la segunda dirección CUReT/ResMLP,
único benchmark GPU 27537: checkpoint 2.050/14.030 llamadas, con log en
avance y sin errores o retenciones nuevos. No se cuenta como completa ni se
consolida aún CUReT/ResMLP. DTD permanece habilitado para las veinte
condiciones físicas pendientes después, no contado como ya medido.

## Seguimiento 29-10-2026, 11:37 UTC

Cobertura completa sin cambios: 86 condiciones de calidad/replay no-KTH,
33 físicas auditadas y las retenciones conocidas (32 Outex/Soil, ocho KTH).
La segunda dirección CUReT/ResMLP sigue activa y avanza de 2.050 a
3.800/14.030 llamadas en checkpoint. Worker 26367 y único benchmark GPU
27537 vivos, logs consultados, sin errores o retenciones nuevos. No se
despachan duplicados, repiten fallos o incorporan parciales a medias finales.

## Seguimiento 29-10-2026, 11:52 UTC

Sin nuevo cierre físico o fallo. Cobertura cerrada: 86 condiciones de
calidad/replay no-KTH, 33 físicas auditadas; retenciones sin cambios.
CUReT/ResMLP segunda dirección avanza de 3.800 a 5.550/14.030 llamadas.
Worker 26367 y único benchmark GPU 27537 vivos, log consultado y sin
retenciones nuevas. DTD sigue pendiente de medición física, no se presenta
como medido por haber aprobado su diagnóstico. No se relanzó ningún caso.

## Seguimiento 29-10-2026, 12:07 UTC

Sin cierre físico ni fallo nuevo: 86 condiciones de calidad/replay no-KTH,
33 físicas auditadas y las retenciones conocidas. La segunda dirección
CUReT/ResMLP avanza de 5.550 a 7.350/14.030 llamadas. Worker 26367 y único
benchmark GPU 27537 vivos, log consultado, sin casos nuevos requiere revisión.
No se inicia otro benchmark ni se cuentan esos checkpoints como completos.

## Seguimiento 29-10-2026, 12:22 UTC

Cobertura cerrada sin cambios: 86 condiciones de calidad/replay no-KTH,
33 físicas auditadas y las retenciones conocidas. CUReT/ResMLP segunda
dirección avanza de 7.350 a 9.100/14.030 llamadas. Worker 26367 y único
benchmark GPU 27537 vivos, log consultado, sin fallos nuevos. No se reinician
casos ni se transforma ese progreso en una media completa de CUReT/ResMLP.

## Seguimiento 29-10-2026, 12:37 UTC

Sin nuevo cierre físico o fallo. Cobertura cerrada sin cambios: 86 condiciones
de calidad/replay no-KTH y 33 físicas auditadas; retenciones conocidas vigentes.
La segunda dirección CUReT/ResMLP registra 10.850/14.030 llamadas frente a
9.100 previamente. Worker 26367 y único benchmark GPU 27537 vivos, log en
avance y sin errores nuevos. No se publican medias finales o se reintentan
los casos retenidos para acelerar el cierre.

## Seguimiento 29-10-2026, 12:52 UTC

Cobertura cerrada sin cambios: 86 condiciones de calidad/replay no-KTH,
33 físicas auditadas y retenciones conocidas. CUReT/ResMLP segunda dirección
avanza de 10.850 a 12.650/14.030 llamadas. Worker 26367 y único benchmark
GPU 27537 vivos, logs consultados, sin fallos nuevos. Se espera el cierre y
auditoría antes de consolidar; no se duplica carga o reintenta ningún caso.

## Seguimiento 29-10-2026, 13:07 UTC: CUReT físico completo, ambos clasificadores

La última dirección CUReT/ResMLP cerró sus 14.030 llamadas y pasó la auditoría
`ONLINE_CALL_RECORDS_REAGGREGATED`. Se consolidaron ambas direcciones,
verificando hashes y condición científica idéntica entre los registros v1/v2,
sin repetir inferencias. Nuevo consolidado:
v2 `summary_CUReT_resmlp_online_v1/`, 5.612 imágenes, 28.060 llamadas.

| Método | F1 online medio por dirección (2 condiciones) | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,999109 | 1618,512434 |
| Diversidad | 0,998931 | 395,115313 |
| Tómbola | 0,999109 | 365,792121 |
| Top-4 | 0,998396 | 268,424242 |
| Adaptativo | 0,998931 | 30,472172 |

Aquí el adaptativo supera numéricamente a Top-4 en aproximadamente 0,000535
de F1 (0,054 puntos porcentuales), con menor tiempo observado; empata
numéricamente con diversidad y queda por debajo de Completa/tómbola.
No se declara significancia, equivalencia o victoria global. El entorno sigue
siendo compartido y se conserva una repetición por imagen. Fuente:
`dataset_summary.csv` y `summary.json` del consolidado, con hashes y CSV de
llamadas/direcciones. No se promedian percentiles ni se confunde F1 agrupado
con media por dirección.

Se extendió únicamente el consolidador de CUReT para aceptar un manifiesto
de continuación con rutas nuevas; exige idénticos config/hash, dataset,
clasificador, semilla y dirección. Cuatro pruebas del consolidador y cinco
del auditor: nueve aprobadas. Ningún script congelado de experimento cambió.

Cobertura física completa: 34 condiciones (FMD 30, CUReT 4), 86.120 llamadas
y 170 filas condición–método. Calidad/replay no-KTH: 86 condiciones completas.
Siguen 32 condiciones Outex/Soil retenidas y ocho KTH por reconciliación.
Worker v2 26367 pasó a DTD/SVM/42/0, único benchmark GPU 30161; las veinte
condiciones DTD siguen pendientes de cierre físico, incluida la activa.
No hay fallos nuevos ni reintentos de casos retenidos.

## Seguimiento 29-10-2026, 13:22 UTC

Cobertura completa sin cambios: 86 condiciones de calidad/replay no-KTH,
34 físicas auditadas (86.120 llamadas) y las retenciones conocidas. Primer
split físico DTD/SVM sigue activo: 2.050/9.400 llamadas en checkpoint. Worker
26367 y único benchmark GPU 30161 vivos, log en avance y sin errores o
retenciones nuevos. No se contabiliza DTD como completo ni se reintenta
Outex/Soil/KTH; se mantienen parámetros y salidas científicas congeladas.

## Seguimiento 29-10-2026, 13:37 UTC

Sin cierre físico ni fallo nuevo: cobertura completa y retenciones sin
cambios. DTD/SVM primer split avanza de 2.050 a 3.800/9.400 llamadas.
Worker 26367 y único benchmark GPU 30161 vivos, log consultado y sin
errores nuevos. No se reinician procesos ni se publica un F1/tiempo parcial
como resultado de sus diez splits o del dataset completo.

## Seguimiento 29-10-2026, 13:52 UTC

Sin cierre físico ni fallo nuevo. Cobertura cerrada: 86 condiciones de
calidad/replay no-KTH y 34 físicas auditadas, retenciones conocidas vigentes.
Primer split DTD/SVM avanza de 3.800 a 5.600/9.400 llamadas. Worker 26367 y
único benchmark GPU 30161 vivos, log consultado, sin errores nuevos. La
ventana de despacho v2 está próxima a vencer; no debe cortar este split
sano ni convertir los otros diecinueve DTD nunca iniciados en fallos.

## Seguimiento 29-10-2026, 14:07 UTC

Sin cierre físico ni fallo nuevo: cobertura completa y retenciones sin
cambios. Primer split DTD/SVM avanza de 5.600 a 7.350/9.400 llamadas.
Worker 26367 y único benchmark GPU 30161 vivos, log consultado, sin errores
nuevos. La ventana de despacho v2 venció, pero el split ya iniciado sigue
bajo su timeout original; no se interrumpe ni se publica como completo.

## Seguimiento 29-10-2026, 14:22 UTC

Sin cierre físico ni fallo nuevo. DTD/SVM primer split alcanza 9.150/9.400
llamadas frente a 7.350 previamente. Worker 26367 y único benchmark GPU
30161 vivos, log consultado y sin errores nuevos. Se espera su final y
auditoría antes de contarlo: siguen 34 condiciones físicas completas y 86
de calidad/replay no-KTH. No se reinicia ningún caso ni se modifica el método.

## Seguimiento 29-10-2026, 14:37 UTC: primer split DTD físico auditado

DTD/SVM/42/split oficial 1 (índice 0) terminó 1.880 imágenes por método,
9.400 llamadas totales, y pasó `ONLINE_CALL_RECORDS_REAGGREGATED`. F1 y
tiempos de las mismas llamadas, resultado SOLO de este split:

| Método | F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,865697 | 1530,190526 |
| Diversidad | 0,875672 | 344,203054 |
| Tómbola | 0,875781 | 346,621993 |
| Top-4 | 0,874652 | 264,250352 |
| Adaptativo | 0,867427 | 39,272614 |

La cascada pierde aproximadamente 0,007225 de F1 frente a Top-4 (0,723
puntos porcentuales), con menor tiempo observado. Supera numéricamente a
Completa pero pierde ante ambos ensambles. No se extrapola al promedio de
los diez splits. Completa tiene acuerdo de clases 99,9468% con caché,
mientras los otros métodos tienen 100%; se conserva el F1 online sin
sustituirlo por el histórico. Fuentes v2:
`jobs/DTD_svm_s42_f0/online/online_summary.csv` y su auditor. Log de auditoría
consultado, sin error. GPU compartida, una repetición por imagen.

La v2 cerró normalmente a las 14:24 UTC, sin fallos nuevos. Se verificó su
salida y ausencia de benchmark antes de lanzar continuación v3, reutilizando
el ejecutor ya probado: `results/analysis/overnight_online_resume_20261029_v3/`.
Solo diecinueve condiciones DTD nunca iniciadas, outputs nuevos, mismas
recetas/configs y tolerancias, tres horas de despacho, timeouts originales.
Reutiliza por copia hash-verificada el vínculo DTD aprobado, sin otro
diagnóstico ni reintentos. Las 32 retenciones Outex/Soil no forman parte de
esa cola; KTH sigue retenido. Sesión 93002, worker 31857, primer job DTD/SVM/42/1,
único benchmark GPU 31860. No hubo commits, push o cambios al manuscrito.

Cobertura física cerrada: 35 condiciones, 95.520 llamadas y 175 filas
condición–método. Calidad/replay no-KTH: 86 condiciones completas. Restan
diecinueve DTD físicos, más resolver las 32 retenciones y ocho KTH; no se
anuncia panel completo ni medias físicas completas de DTD.

## Seguimiento 29-10-2026, 14:52 UTC

Sin nuevo cierre físico o fallo: 86 condiciones de calidad/replay no-KTH,
35 físicas auditadas y retenciones conocidas. V3 mide el segundo split
DTD/SVM (índice 1): checkpoint 1.500/9.400 llamadas. Worker 31857 y único
benchmark GPU 31860 vivos, log consultado y sin casos nuevos requiere
revisión. No se duplica trabajo o contabiliza el split activo como terminado.

## Seguimiento 29-10-2026, 15:07 UTC

Sin cierre físico ni fallo nuevo: cobertura y retenciones sin cambios.
Segundo split DTD/SVM avanza de 1.500 a 3.250/9.400 llamadas. Worker v3
31857 y único benchmark GPU 31860 vivos, log consultado, sin errores nuevos.
No se reinician procesos ni se promueven esos checkpoints a resultados finales.

## Seguimiento 29-10-2026, 15:22 UTC

Cobertura completa sin cambios: 86 condiciones de calidad/replay no-KTH,
35 físicas auditadas y retenciones conocidas. Segundo split DTD/SVM avanza
de 3.250 a 5.000/9.400 llamadas. Worker 31857 y único benchmark GPU 31860
vivos, log consultado y sin errores o retenciones nuevos. No se duplica carga
ni se presentan parciales como medias completas del dataset.

## Seguimiento 29-10-2026, 15:37 UTC

Sin cierre físico ni fallo nuevo: cobertura y retenciones sin cambios.
Segundo split DTD/SVM avanza de 5.000 a 6.700/9.400 llamadas. Worker v3
31857 y único benchmark GPU 31860 vivos, log consultado y sin errores nuevos.
No se reinician procesos ni se incorporan estos checkpoints a medias finales.

## Seguimiento 29-10-2026, 15:52 UTC

Cobertura cerrada y retenciones sin cambios. Segundo split DTD/SVM avanza
de 6.700 a 8.450/9.400 llamadas. Worker 31857 y único benchmark GPU 31860
vivos, log consultado y sin errores nuevos. Todavía no se contabiliza ese
split como completo: se espera su cierre y auditoría, sin duplicar trabajos.

## Seguimiento 29-10-2026, 16:07 UTC: segundo split DTD físico auditado

DTD/SVM/42/split oficial 2 (índice 1) completó 1.880 imágenes por método,
9.400 llamadas y auditoría `ONLINE_CALL_RECORDS_REAGGREGATED`. F1 y tiempo
de las mismas llamadas. Resultado únicamente de este split:

| Método | F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,870642 | 1563,688623 |
| Diversidad | 0,869066 | 346,330393 |
| Tómbola | 0,867852 | 346,435725 |
| Top-4 | 0,863321 | 264,496078 |
| Adaptativo | 0,867081 | 43,844512 |

Aquí el adaptativo supera numéricamente a Top-4, pero pierde ante Completa
y los ensambles. No se generaliza al conjunto DTD: solo dos de diez splits
SVM están medidos, y ninguno ResMLP. Completa conserva una diferencia de
clase frente a caché (acuerdo 99,9468%); el resto tiene acuerdo 100%. No se
sustituye F1 online por histórico ni se afirma paridad de vectores.
Fuentes v3: `jobs/DTD_svm_s42_f1/online/online_summary.csv` y su auditor;
log final de auditoría consultado, sin error registrado.

Cobertura cerrada: 36 condiciones físicas, 104.920 llamadas y 180 filas
condición–método; calidad/replay no-KTH sigue en 86. Worker v3 31857 pasó al
tercer split DTD/SVM (índice 2), único benchmark GPU 33313. Restan dieciocho
DTD físicos incluidos los activos, además de las retenciones Outex/Soil/KTH.
No hay fallos nuevos, reintentos o cambios metodológicos.

## Seguimiento 29-10-2026, 16:22 UTC

Sin cierre físico ni fallo nuevo. Tercer split DTD/SVM (índice 2) avanza
a 2.400/9.400 llamadas; worker v3 31857 y único benchmark GPU 33313 vivos,
con log consultado. Se mantienen 36 condiciones físicas auditadas,
104.920 llamadas completas y 86 condiciones de calidad/replay no-KTH.
Retenciones Outex/Soil/KTH sin cambios; no se duplican trabajos ni se
incorporan checkpoints a resultados finales.

## Seguimiento 29-10-2026, 16:37 UTC

Tercer split DTD/SVM (índice 2) en ejecución: 4.150/9.400 llamadas al
consultar el estado. Worker v3 y benchmark GPU vivos; sin cierre nuevo ni
error nuevo registrado. Cobertura completa y retenciones sin cambios:
36 condiciones físicas auditadas, 104.920 llamadas completas y 86 de
calidad/replay no-KTH. No se inician trabajos duplicados ni reintentos.

## Seguimiento 29-10-2026, 16:52 UTC

Sin cierre ni fallo nuevo. Tercer split DTD/SVM (índice 2) alcanza
5.900/9.400 llamadas; worker 31857 y único benchmark GPU 33313 vivos,
con log y estado consultados. Cobertura auditada sin cambios: 36 condiciones
físicas y 104.920 llamadas completas; 86 condiciones de calidad/replay
no-KTH. Se conservan las retenciones y no se duplican trabajos.

## Seguimiento 29-10-2026, 17:07 UTC

Tercer split DTD/SVM (índice 2) continúa, con 7.600/9.400 llamadas al
consultar el checkpoint. Worker 31857 y único benchmark GPU 33313 vivos;
log sin fallo nuevo. No hay nueva condición cerrada: se conservan las
36 condiciones físicas auditadas y 104.920 llamadas completas. Retenciones
y decisiones científicas sin cambios; no se ejecutan trabajos duplicados.

## Seguimiento 29-10-2026, 17:22 UTC

Tercer split DTD/SVM (índice 2) alcanza 9.300/9.400 llamadas en el log.
Worker 31857 y único benchmark GPU 33313 continúan vivos, sin fallo nuevo.
Todavía no hay cierre ni auditoría final de esta condición: cobertura
completa permanece en 36 condiciones físicas y 104.920 llamadas. No se
modifican protocolo, orden de cola, retenciones o métodos.

## Seguimiento 29-10-2026, 17:37 UTC: tercer split DTD/SVM cerrado

Split oficial 3 (índice 2): 1.880 imágenes por método, 9.400 llamadas,
auditoría `ONLINE_CALL_RECORDS_REAGGREGATED`, sin fallo registrado. F1 y
latencias provienen de las mismas llamadas online:

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,862677 | 1559,363209 |
| Diversidad | 0,877583 | 381,050203 |
| Tómbola | 0,878829 | 355,096015 |
| Top-4 | 0,875556 | 265,025533 |
| Adaptativo | 0,872388 | 47,922388 |

El adaptativo pierde 0,003168 de F1 frente a Top-4 en este split y reduce
su tiempo medio aproximadamente 81,9%. No es una media de DTD. Acuerdo
de predicción frente a caché: Completa 99,7872%; adaptativo y tómbola
99,9468%; diversidad y Top-4 100%. Se conserva el F1 online observado,
sin afirmar identidad con los embeddings históricos.

Cobertura completa: 37 condiciones físicas auditadas, 114.320 llamadas y
185 filas condición–método. DTD/SVM: tres de diez splits; DTD/ResMLP aún
pendiente. Fuente: v3/jobs/DTD_svm_s42_f2/online y online_audit.
Worker 31857 ejecuta el cuarto split (índice 3), único benchmark GPU 35993;
no se interrumpe al vencer la ventana de despacho. Retenciones sin cambios.

## Seguimiento 29-10-2026, 17:52 UTC

Cuarto split DTD/SVM (índice 3) avanza a 3.200/9.400 llamadas. Worker 31857
y único benchmark GPU 35993 vivos, log consultado y sin fallo nuevo. La
ventana de despacho venció, pero se permite terminar la condición activa.
Cobertura completa permanece en 37 condiciones físicas, 114.320 llamadas;
no se agregan parciales, se duplican trabajos ni se reintentan retenciones.

## Seguimiento 29-10-2026, 18:07 UTC

Cuarto split DTD/SVM (índice 3) alcanza 4.950/9.400 llamadas. Worker 31857
y único benchmark GPU 35993 siguen vivos, con log consultado y sin fallo
nuevo. Se deja finalizar la condición activa tras el cierre de despacho;
no se inicia otra cola en paralelo. Cobertura auditada sin cambios:
37 condiciones físicas, 114.320 llamadas completas; retenciones preservadas.

## Seguimiento 29-10-2026, 18:22 UTC

Cuarto split DTD/SVM (índice 3): 6.750/9.400 llamadas, worker 31857 y único
benchmark GPU 35993 vivos. Estado y log revisados, sin cierre ni fallo nuevo.
Cobertura auditada permanece en 37 condiciones físicas y 114.320 llamadas
completas. No se modifican recetas ni se reinician trabajos; Outex/Soil/KTH
siguen retenidos y no se contabilizan como resultados físicos completos.

## Seguimiento 29-10-2026, 18:37 UTC

Cuarto split DTD/SVM (índice 3) avanza a 8.500/9.400 llamadas. Worker 31857
y único benchmark GPU 35993 vivos, sin error nuevo en estado/log. Se espera
su cierre y auditoría antes de contabilizarlo; permanecen 37 condiciones
físicas auditadas y 114.320 llamadas completas. Retenciones sin cambios,
sin reintentos ni trabajos duplicados.

## Seguimiento 29-10-2026, 18:52 UTC: cuarto split cerrado y continuación v4

DTD/SVM split oficial 4 (índice 3): auditoría
`ONLINE_CALL_RECORDS_REAGGREGATED`, 9.400 llamadas sobre 1.880 imágenes por
método, F1 y tiempos de las mismas llamadas. Acuerdo de clases frente a
caché 100% en los cinco métodos; no implica paridad universal de vectores.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,874361 | 1543,883016 |
| Diversidad | 0,876952 | 363,458611 |
| Tómbola | 0,875724 | 356,302795 |
| Top-4 | 0,869603 | 267,360235 |
| Adaptativo | 0,872230 | 43,844355 |

En este split el adaptativo supera numéricamente a Top-4 en 0,002627 F1
y reduce su tiempo medio 83,6%; queda por debajo de los otros tres métodos.
No se generaliza como media completa DTD. Cobertura: 38 condiciones físicas
auditadas, 123.720 llamadas completas y 190 filas condición–método.

V3 cerró normalmente a 18:44:49 UTC sin requiere revisión. Se comprobó
ausencia de workers/benchmarks activos antes de iniciar la continuación
`results/analysis/overnight_online_resume_20261029_v4/`, con el mismo script
sin modificar, ventana de despacho de tres horas y 16 condiciones DTD
nunca iniciadas (seis SVM, diez ResMLP). Worker 37719, sesión 1161; empieza
DTD_svm_s42_f4. Manifiesto nuevo SHA256
3998379ca82d722826174ed917032dfb39c3db78f49a991e17bf060a1361881a.
Diagnóstico DTD aprobado copiado con verificación de hashes; sin nueva
prueba numérica ni reintentos científicos. Retenciones Outex/Soil/KTH
preservadas, sin commits, push o cambios al manuscrito.

## Seguimiento 29-10-2026, 19:07 UTC

Quinto split DTD/SVM (índice 4), primera condición v4, avanza a
1.700/9.400 llamadas. Worker 37719 y único benchmark GPU 37722 vivos;
estado y log sin fallo nuevo. Cobertura auditada permanece en 38 condiciones
físicas y 123.720 llamadas completas. No hay nueva condición cerrada ni
cambios de protocolo, retenciones o trabajos duplicados.

## Seguimiento 29-10-2026, 19:22 UTC

Quinto split DTD/SVM (índice 4) avanza a 3.500/9.400 llamadas. Worker v4
37719 y único benchmark GPU 37722 vivos, sin error nuevo en estado/log.
No hay nuevo cierre: se mantienen 38 condiciones físicas auditadas y
123.720 llamadas completas. Se preservan protocolo y retenciones, sin
reintentos ni ejecución duplicada.

## Seguimiento 29-10-2026, 19:37 UTC

Quinto split DTD/SVM (índice 4): 5.300/9.400 llamadas. Worker 37719 y único
benchmark GPU 37722 vivos; estado y log revisados, sin cierre ni fallo nuevo.
Cobertura permanece en 38 condiciones físicas auditadas y 123.720 llamadas
completas. No se modifica el protocolo ni se repiten trabajos o diagnósticos.

## Seguimiento 29-10-2026, 19:52 UTC

Quinto split DTD/SVM (índice 4) alcanza 7.050/9.400 llamadas. Worker 37719
y único benchmark GPU 37722 vivos, estado/log sin fallo nuevo. Ninguna
condición adicional cerrada: cobertura auditada 38 condiciones físicas y
123.720 llamadas completas. Retenciones y protocolo se mantienen intactos;
sin duplicaciones o reintentos.

## Seguimiento 29-10-2026, 20:07 UTC

Quinto split DTD/SVM (índice 4): 8.800/9.400 llamadas. Worker 37719 y único
benchmark GPU 37722 vivos; estado/log revisados, sin fallo nuevo. Aún no
se contabiliza esta condición: 38 condiciones físicas auditadas y 123.720
llamadas completas. Continúan las retenciones conocidas sin reintentos,
cambios metodológicos ni trabajos duplicados.

## Seguimiento 29-10-2026, 20:22 UTC: quinto split DTD/SVM auditado

DTD/SVM split oficial 5 (índice 4) cerró con auditoría
`ONLINE_CALL_RECORDS_REAGGREGATED`: 9.400 llamadas, 1.880 imágenes por método,
F1 y tiempo de las mismas llamadas. Acuerdo de clases frente a caché 100%
para los cinco métodos, sin afirmar paridad de todos los vectores.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,869644 | 1540,279774 |
| Diversidad | 0,879405 | 351,474518 |
| Tómbola | 0,877917 | 313,290780 |
| Top-4 | 0,878192 | 262,580056 |
| Adaptativo | 0,880554 | 43,847122 |

El adaptativo tiene el mayor F1 observado entre los cinco en este split;
frente a Top-4 gana 0,002361 F1 y reduce su tiempo medio 83,3%. No constituye
una media completa DTD ni una conclusión inferencial. Fuente:
v4/jobs/DTD_svm_s42_f4/online y online_audit.

Cobertura auditada: 39 condiciones físicas, 133.120 llamadas completas,
195 filas condición–método. DTD/SVM cinco de diez splits; ResMLP pendiente.
Worker 37719 continúa el sexto split (índice 5), único benchmark GPU 38727,
1.050/9.400 llamadas al consultar. Sin fallos nuevos o cambios de receta;
retenciones Outex/Soil/KTH preservadas.

## Seguimiento 29-10-2026, 20:37 UTC

Sexto split DTD/SVM (índice 5): 2.800/9.400 llamadas. Worker 37719 y único
benchmark GPU 38727 vivos, log y estado consultados sin fallo nuevo.
Cobertura auditada sin cambios: 39 condiciones físicas y 133.120 llamadas
completas. No se cuentan checkpoints como resultados finales ni se inician
trabajos duplicados; protocolo y retenciones preservados.

## Seguimiento 29-10-2026, 20:52 UTC

Sexto split DTD/SVM (índice 5) alcanza 4.500/9.400 llamadas. Worker 37719
y único benchmark GPU 38727 vivos, estado/log sin fallo nuevo. Sin nuevo
cierre: 39 condiciones físicas auditadas, 133.120 llamadas completas.
No se altera protocolo, se duplican trabajos ni se reintentan retenciones.

## Seguimiento 29-10-2026, 21:07 UTC

Sexto split DTD/SVM (índice 5): 6.250/9.400 llamadas. Worker 37719 y único
benchmark GPU 38727 vivos; log y estado consultados sin fallo nuevo.
No hay nuevo cierre, por lo que siguen 39 condiciones físicas auditadas y
133.120 llamadas completas. Sin duplicaciones, cambios o reintentos.

## Seguimiento 29-10-2026, 21:22 UTC

Sexto split DTD/SVM (índice 5) alcanza 7.950/9.400 llamadas. Worker 37719
y único benchmark GPU 38727 vivos, estado/log sin error nuevo. No hay
nueva condición auditada: 39 condiciones físicas y 133.120 llamadas
completas. Se preservan protocolo, retenciones y ejecución secuencial.

## Seguimiento 29-10-2026, 21:37 UTC: sexto split DTD/SVM auditado

DTD/SVM split oficial 6 (índice 5) completó 9.400 llamadas (1.880 imágenes
por método), auditoría `ONLINE_CALL_RECORDS_REAGGREGATED`. Se conservan F1
y latencias de las mismas llamadas, sin reutilizar el F1 histórico.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,863749 | 1568,980520 |
| Diversidad | 0,874223 | 353,515183 |
| Tómbola | 0,870461 | 339,564617 |
| Top-4 | 0,865008 | 264,938968 |
| Adaptativo | 0,860754 | 58,757891 |

En este split el adaptativo reduce el tiempo medio 77,8% frente a Top-4,
pero pierde 0,004254 F1; no supera en calidad a los otros cuatro métodos.
Escala al rescate en 48,94% de imágenes. Acuerdo de clases frente a caché:
tómbola 99,9468%; demás 100%. No se afirma paridad universal de vectores ni
se presenta este split como una media completa de DTD.

Cobertura: 40 condiciones físicas auditadas, 142.520 llamadas completas y
200 filas condición–método. DTD/SVM seis de diez; DTD/ResMLP pendiente.
Fuente v4/jobs/DTD_svm_s42_f5/online y online_audit. Worker 37719 pasó al
séptimo split (índice 6), único benchmark GPU 39701. Sin fallo nuevo,
reintento o modificación de recetas; retenciones conocidas preservadas.

## Seguimiento 29-10-2026, 21:52 UTC

Séptimo split DTD/SVM (índice 6): 1.950/9.400 llamadas. Worker 37719 y único
benchmark GPU 39701 vivos, estado/log sin fallo nuevo. La ventana de
despacho v4 está por terminar; se deja completar el trabajo activo antes
de otra continuación. Cobertura sin cambios: 40 condiciones físicas
auditadas y 142.520 llamadas completas, sin duplicaciones o reintentos.

## Seguimiento 29-10-2026, 22:07 UTC

Séptimo split DTD/SVM (índice 6) avanza a 3.700/9.400 llamadas. Worker
37719 y único benchmark GPU 39701 vivos; estado y log sin fallo nuevo.
Se deja terminar la condición activa tras vencer la ventana de despacho.
Cobertura completa permanece en 40 condiciones físicas auditadas y
142.520 llamadas. Retenciones intactas, sin duplicaciones ni reintentos.

## Pausa al finalizar la condición activa, solicitada por el usuario

Se deja terminar DTD_svm_s42_f6 y su auditoría. La ventana v4 ya venció
(21:52:12 UTC), de modo que el worker saldrá después, sin nuevo despacho.
La automatización fue actualizada mediante la herramienta del producto y
confirmó estado PAUSED. No se creará v5 ni se iniciarán otras condiciones
hasta una solicitud explícita de reanudación. No se interrumpió el benchmark
ni se modificaron archivos científicos. El cierre del split activo aún
debe verificarse al retomar; cobertura confirmada por ahora: 40 condiciones
físicas auditadas y 142.520 llamadas completas.

## Reanudación 30-10-2026, 02:49 UTC (29-10, 23:49 Asunción)

El usuario pidió continuar, revocando la pausa. V4 terminó normalmente a
00:25:06 UTC con el séptimo split DTD/SVM (índice 6) completo y auditoría
ONLINE_CALL_RECORDS_REAGGREGATED: 9.400 llamadas, 1.880 imágenes por método,
F1 y tiempo de las mismas llamadas. No hay fallo de ejecución registrado.

| Método | Macro-F1 online | Media ms | Mediana ms |
| --- | ---: | ---: | ---: |
| Completa-22 | 0,867002 | 2272,342133 | 1610,724540 |
| Diversidad | 0,885871 | 906,261126 | 337,880554 |
| Tómbola | 0,883413 | 1137,026264 | 369,531278 |
| Top-4 | 0,880462 | 960,945250 | 268,928569 |
| Adaptativo | 0,882362 | 130,239665 | 15,495988 |

REQUIERE REVISIÓN de aptitud física: medias muy superiores a medianas y
ralentización observada durante la ejecución. Causa no establecida; el
auditor verifica registros y aritmética, no aislamiento del hardware.
Se preservan los datos sin filtrar valores extremos, repetir la condición,
reemplazar medias por medianas o presentar ahorros robustos de este split.
Cobertura de registros auditados: 41 condiciones, 151.920 llamadas y 205
filas condición–método; una condición con reserva explícita de latencia.

Comprobada ausencia de workers/benchmarks activos antes del lanzamiento,
se reutilizó el script de continuación sin cambios en carpeta v5 nueva:
trece condiciones DTD nunca iniciadas (SVM índices 7–9 y ResMLP 0–9).
Worker 41544, sesión 26914, benchmark 41547, primer job DTD_svm_s42_f7.
Manifiesto SHA256 5cff856fa4c85bf63d78332d1f155df5b0ea393e4fdeab6e548f0648f4fcbcaf.
La automatización confirmó ACTIVE; no se repiten diagnósticos ni fallos.
Retenciones Outex/Soil/KTH intactas; sin cambios al manuscrito, commits o push.

## Seguimiento 30-10-2026, 03:04 UTC

Octavo split DTD/SVM (índice 7): 1.550/9.400 llamadas. Worker v5 41544 y
único benchmark GPU 41547 vivos, log y estado sin fallo nuevo. No hay nuevo
cierre: 41 condiciones con registros auditados y 151.920 llamadas completas,
manteniendo la reserva de aptitud física del séptimo split. Sin duplicaciones,
reintentos, filtrado de valores extremos o cambios metodológicos.

## Seguimiento 30-10-2026, 03:19 UTC

Octavo split DTD/SVM (índice 7) avanza a 3.300/9.400 llamadas. Worker v5
41544 y único benchmark GPU 41547 vivos, estado/log sin fallo nuevo. No
hay nuevo cierre: 41 condiciones con registros auditados y 151.920 llamadas
completas, con la reserva de latencia del séptimo split preservada. Sin
trabajos duplicados ni reintentos; recetas y retenciones intactas.

## Seguimiento 30-10-2026, 03:34 UTC

Octavo split DTD/SVM (índice 7): 5.050/9.400 llamadas. Worker 41544 y único
benchmark GPU 41547 vivos; estado y log revisados, sin fallo ni cierre nuevo.
Cobertura sin cambios: 41 condiciones con registros auditados y 151.920
llamadas completas, conservando la reserva física del séptimo split. No se
duplican trabajos, reintentan fallos o cambian métodos/tolerancias.

## Seguimiento 30-10-2026, 03:49 UTC

Octavo split DTD/SVM (índice 7) avanza a 6.850/9.400 llamadas. Worker v5
41544 y único benchmark GPU 41547 vivos, estado/log sin fallo nuevo.
No hay cierre adicional: 41 condiciones con registros auditados, 151.920
llamadas completas y reserva física del séptimo split preservada. Sin
duplicaciones, reintentos o cambios de protocolo.

## Seguimiento 30-10-2026, 04:04 UTC

Octavo split DTD/SVM (índice 7): 8.600/9.400 llamadas. Worker 41544 y único
benchmark GPU 41547 vivos, estado/log revisados sin error nuevo. No hay
nuevo cierre: 41 condiciones con registros auditados y 151.920 llamadas
completas; reserva física del séptimo split intacta. Sin duplicaciones,
reintentos ni cambios científicos.

## Seguimiento 30-10-2026, 04:19 UTC: octavo split DTD/SVM auditado

DTD/SVM split oficial 8 (índice 7) cerró con 9.400 llamadas, 1.880 imágenes
por método y auditoría ONLINE_CALL_RECORDS_REAGGREGATED. Calidad y tiempo
de las mismas llamadas; acuerdo de clases frente a caché 100% para todos,
sin afirmar paridad universal de vectores.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,844263 | 1524,973755 |
| Diversidad | 0,851531 | 366,847414 |
| Tómbola | 0,852877 | 336,180566 |
| Top-4 | 0,854571 | 263,727275 |
| Adaptativo | 0,845017 | 44,376948 |

Frente a Top-4, adaptativo pierde 0,009554 F1 (0,9554 puntos porcentuales)
y reduce el tiempo medio 83,2% en este split. No se presenta como promedio
DTD ni equivalencia. Fuente v5/jobs/DTD_svm_s42_f7/online y online_audit.

Cobertura: 42 condiciones con registros auditados, 161.320 llamadas
completas y 210 filas condición–método; permanece la reserva de aptitud
física del séptimo split. DTD/SVM ocho de diez, ResMLP aún pendiente.
Worker 41544 pasó al noveno split (índice 8), único benchmark GPU 42666,
850/9.400 llamadas al consultar. Sin nuevos fallos, reintentos o cambios.

## Seguimiento 30-10-2026, 04:34 UTC

Noveno split DTD/SVM (índice 8): 2.650/9.400 llamadas. Worker 41544 y único
benchmark GPU 42666 vivos, estado/log revisados sin fallo nuevo. Cobertura
sin nuevo cierre: 42 condiciones con registros auditados y 161.320 llamadas
completas; reserva de aptitud física del séptimo split preservada. No se
duplican trabajos, reintentan fallos ni alteran recetas.

## Seguimiento 30-10-2026, 04:49 UTC

Noveno split DTD/SVM (índice 8) avanza a 4.400/9.400 llamadas. Worker
41544 y único benchmark GPU 42666 vivos, estado/log sin fallo nuevo. Sin
nuevo cierre: 42 condiciones con registros auditados y 161.320 llamadas
completas, con la reserva física del séptimo split intacta. Sin reintentos,
duplicaciones o cambios metodológicos.

## Seguimiento 30-10-2026, 05:04 UTC

Noveno split DTD/SVM (índice 8): 6.200/9.400 llamadas. Worker 41544 y único
benchmark GPU 42666 vivos, estado/log revisados sin cierre ni fallo nuevo.
Cobertura permanece en 42 condiciones con registros auditados y 161.320
llamadas completas, conservando la reserva física del séptimo split.
No se duplican trabajos, reintentan fallos ni modifican recetas.

## Seguimiento 30-10-2026, 05:19 UTC

Noveno split DTD/SVM (índice 8) avanza a 7.950/9.400 llamadas. Worker
41544 y único benchmark GPU 42666 vivos, estado/log sin error nuevo.
No hay cierre adicional: 42 condiciones con registros auditados y 161.320
llamadas completas; reserva física del séptimo split intacta. Sin
duplicaciones, reintentos ni cambios metodológicos.

## Seguimiento 30-10-2026, 05:34 UTC: noveno split DTD/SVM auditado

Split oficial 9 (índice 8): ONLINE_CALL_RECORDS_REAGGREGATED, 9.400 llamadas,
1.880 imágenes por método. F1 y tiempo de las mismas llamadas online.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,864320 | 1510,519940 |
| Diversidad | 0,876294 | 337,873230 |
| Tómbola | 0,876845 | 368,172296 |
| Top-4 | 0,867093 | 263,957608 |
| Adaptativo | 0,867210 | 46,854230 |

Adaptativo supera numéricamente Top-4 en 0,000116 F1 y reduce tiempo medio
82,2% en este split; pierde frente a ambos ensambles. No es equivalencia
formal ni resultado agregado DTD. Acuerdo frente a caché: Completa 99,8404%,
diversidad 99,9468%, demás 100%; se preserva F1 online, no se afirma paridad
universal de vectores. Fuente v5/jobs/DTD_svm_s42_f8/online y online_audit.

Cobertura: 43 condiciones con registros auditados, 170.720 llamadas completas,
215 filas condición–método. Se conserva la reserva de latencia del séptimo
split. DTD/SVM nueve de diez; ResMLP físico pendiente. Worker 41544 inició
el décimo split (índice 9), único benchmark GPU 43605. Sin fallos nuevos,
reintentos, cambios de recetas o duplicaciones.

## Seguimiento 30-10-2026, 05:49 UTC

Décimo split DTD/SVM (índice 9): 2.000/9.400 llamadas. Worker 41544 y único
benchmark GPU 43605 vivos, estado/log sin error nuevo. La ventana de
despacho v5 venció; se deja terminar y auditar la condición activa antes
de continuar los ResMLP nunca iniciados en otra carpeta. Cobertura sin
cambios: 43 condiciones con registros auditados, 170.720 llamadas completas,
reserva física del séptimo split preservada. Sin reintentos o duplicaciones.

## Seguimiento 30-10-2026, 06:04 UTC

Décimo split DTD/SVM (índice 9) avanza a 3.800/9.400 llamadas. Worker
41544 y único benchmark GPU 43605 vivos, estado/log sin fallo nuevo.
Se deja finalizar la condición activa tras vencer la ventana de despacho.
Cobertura sin nuevo cierre: 43 condiciones con registros auditados y
170.720 llamadas completas; reserva física del séptimo split intacta.
Sin duplicaciones, reintentos o cambios científicos.

## Seguimiento 30-10-2026, 06:19 UTC

Décimo split DTD/SVM (índice 9): 5.550/9.400 llamadas. Worker 41544 y único
benchmark GPU 43605 vivos; estado/log sin cierre ni error nuevo. Cobertura
permanece en 43 condiciones con registros auditados y 170.720 llamadas
completas, manteniendo la reserva física del séptimo split. Se deja cerrar
la condición activa sin duplicaciones, reintentos o cambios de protocolo.

## Seguimiento 30-10-2026, 06:34 UTC

Décimo split DTD/SVM (índice 9) avanza a 7.350/9.400 llamadas. Worker
41544 y único benchmark GPU 43605 vivos, estado/log sin error nuevo. No
hay cierre adicional: 43 condiciones con registros auditados y 170.720
llamadas completas, con reserva física del séptimo split preservada.
Sin duplicaciones, reintentos ni cambios metodológicos.

## Seguimiento 30-10-2026, 06:49 UTC

Décimo split DTD/SVM (índice 9): 9.150/9.400 llamadas. Worker 41544 y único
benchmark GPU 43605 vivos, estado/log sin fallo nuevo. Todavía no hay
cierre/auditoría final: se mantienen 43 condiciones con registros auditados
y 170.720 llamadas completas, incluida la reserva física del séptimo split.
Sin trabajos duplicados, reintentos ni cambios científicos.

## Seguimiento 30-10-2026, 07:04 UTC: diez splits DTD/SVM cerrados

Décimo split (índice 9) completó 9.400 llamadas y auditoría
ONLINE_CALL_RECORDS_REAGGREGATED. V5 cerró normalmente a 06:51:43 UTC,
sin requiere revisión del worker. La reserva externa de aptitud de latencia
del séptimo split permanece: no equivale a un fallo del auditor aritmético.

Consolidación de los diez splits SVM: se verificaron estados completos,
hash de status enlazado por cada auditor, 9.400 filas y unicidad
política/repetición/imagen por split. Total 94.000 llamadas; F1 es media
de macro-F1 por split, no F1 de imágenes únicas ni diez datasets independientes.
Tiempos calculados sobre las llamadas, sin excluir el séptimo split o outliers:

| Método | Media Macro-F1 online | Media ms | Mediana ms |
| --- | ---: | ---: | ---: |
| Completa-22 | 0,863544 | 1611,567793 | 1538,413997 |
| Diversidad | 0,873371 | 411,434197 | 350,325776 |
| Tómbola | 0,872353 | 424,629680 | 343,088853 |
| Top-4 | 0,868890 | 333,976675 | 262,385446 |
| Adaptativo | 0,866857 | 54,353746 | 14,097969 |

El adaptativo pierde 0,002033 F1 frente a Top-4 y 0,006514 frente a
diversidad, y supera a Completa en 0,003312. No se interpreta el cociente
de medias de tiempo como ahorro robusto porque incluye la condición física
marcada para revisión. No se cambia la métrica por mediana para ocultarlo.
Resumen con hashes fuente: v5/summary_DTD_svm_online_v1/summary.json.

Cobertura global de registros: 44 condiciones, 180.120 llamadas completas,
220 filas condición–método; una condición física con reserva de latencia.
Tras comprobar ausencia de benchmarks/workers activos se lanzó v6 nueva,
solo diez ResMLP DTD nunca iniciados. Worker 45000, sesión 96929, primer job
DTD_resmlp_s42_f0, mismas recetas y tres horas de despacho. Manifiesto SHA256
f31f049f5c8ac87f074cb955fdff6bdeb0398680dd312b924d806345972137bf.
Sin reintentos, diagnósticos repetidos, cambios al manuscrito, commits o push.
Outex/Soil/KTH continúan retenidos.

## Seguimiento 30-10-2026, 07:19 UTC

Primer split DTD/ResMLP (índice 0): 1.450/9.400 llamadas. Worker v6 45000
y único benchmark GPU 45003 vivos, estado/log sin fallo nuevo. No hay
nuevo cierre: 44 condiciones con registros auditados y 180.120 llamadas
completas; reserva física del séptimo split SVM intacta. Sin duplicaciones,
reintentos ni cambios metodológicos.

## Seguimiento 30-10-2026, 07:34 UTC

Primer split DTD/ResMLP (índice 0) avanza a 3.250/9.400 llamadas. Worker
45000 y único benchmark GPU 45003 vivos, estado/log sin cierre ni error
nuevo. Se mantienen 44 condiciones con registros auditados y 180.120
llamadas completas, con reserva física del séptimo split SVM preservada.
Sin duplicaciones, reintentos o cambios científicos.

## Seguimiento 30-10-2026, 07:49 UTC

Primer split DTD/ResMLP (índice 0): 5.050/9.400 llamadas. Worker 45000 y
único benchmark GPU 45003 vivos, estado/log revisados sin error nuevo.
No hay cierre adicional: 44 condiciones con registros auditados, 180.120
llamadas completas; reserva física del séptimo split SVM preservada. Sin
duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 30-10-2026, 08:04 UTC

Primer split DTD/ResMLP (índice 0) alcanza 6.750/9.400 llamadas. Worker
45000 y único benchmark GPU 45003 vivos, estado/log sin fallo nuevo. No
hay nuevo cierre: 44 condiciones con registros auditados y 180.120 llamadas
completas; reserva física del séptimo split SVM intacta. Sin duplicaciones,
reintentos ni cambios de protocolo.

## Seguimiento 30-10-2026, 08:19 UTC

Primer split DTD/ResMLP (índice 0): 8.500/9.400 llamadas. Worker 45000 y
único benchmark GPU 45003 vivos; estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 44 condiciones con registros auditados, 180.120
llamadas completas y reserva física del séptimo split SVM preservada.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 30-10-2026, 08:34 UTC: primer DTD/ResMLP auditado

DTD/ResMLP split oficial 1 (índice 0): 9.400 llamadas, 1.880 imágenes por
método, auditoría ONLINE_CALL_RECORDS_REAGGREGATED. F1 y latencias de las
mismas llamadas online, sin paridad universal de vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,866493 | 1501,987142 |
| Diversidad | 0,880691 | 365,760036 |
| Tómbola | 0,878676 | 362,560705 |
| Top-4 | 0,865159 | 269,541986 |
| Adaptativo | 0,868831 | 44,131796 |

Adaptativo supera numéricamente Top-4 en 0,003672 F1 y reduce tiempo medio
83,6% en este split; queda por debajo de ambos ensambles. No es una media
DTD/ResMLP completa ni evidencia de equivalencia o superioridad general.
Acuerdo de clases frente a caché: Completa 99,7872%, demás 100%; se mantiene
el F1 online. Fuente v6/jobs/DTD_resmlp_s42_f0/online y online_audit.

Cobertura: 45 condiciones con registros auditados y 189.520 llamadas
completas, 225 filas condición–método; reserva física del séptimo split SVM
preservada. DTD/ResMLP uno de diez. Worker 45000 pasó al segundo split
(índice 1), único benchmark GPU 46046, 750/9.400 llamadas al consultar.
Sin fallos nuevos, reintentos, duplicaciones o cambios metodológicos.

## Seguimiento 30-10-2026, 08:49 UTC

Segundo split DTD/ResMLP (índice 1): 2.500/9.400 llamadas. Worker 45000 y
único benchmark GPU 46046 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 45 condiciones con registros auditados y 189.520
llamadas completas; reserva física del séptimo split SVM preservada.
Sin duplicaciones, reintentos ni cambios metodológicos.

## Seguimiento 30-10-2026, 09:04 UTC

Segundo split DTD/ResMLP (índice 1) avanza a 4.250/9.400 llamadas. Worker
45000 y único benchmark GPU 46046 vivos, estado/log sin error nuevo. No
hay cierre adicional: 45 condiciones con registros auditados y 189.520
llamadas completas; reserva física del séptimo split SVM intacta. Sin
duplicaciones, reintentos o cambios científicos.

## Seguimiento 30-10-2026, 09:19 UTC

Segundo split DTD/ResMLP (índice 1): 6.000/9.400 llamadas. Worker 45000 y
único benchmark GPU 46046 vivos, estado/log sin cierre ni error nuevo.
Cobertura sin cambios: 45 condiciones con registros auditados y 189.520
llamadas completas; reserva física del séptimo split SVM preservada.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 30-10-2026, 09:34 UTC

Segundo split DTD/ResMLP (índice 1) avanza a 7.750/9.400 llamadas. Worker
45000 y único benchmark GPU 46046 vivos, estado/log sin fallo nuevo.
No hay cierre adicional: 45 condiciones con registros auditados y 189.520
llamadas completas; reserva física del séptimo split SVM intacta. Sin
duplicaciones, reintentos ni cambios científicos.

## Seguimiento 30-10-2026, 09:49 UTC: segundo DTD/ResMLP auditado

Split oficial 2 (índice 1): 9.400 llamadas, 1.880 imágenes por método,
auditoría ONLINE_CALL_RECORDS_REAGGREGATED. F1 y tiempos de las mismas
llamadas online; no se afirma paridad universal con vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,864110 | 1502,690723 |
| Diversidad | 0,877855 | 385,401470 |
| Tómbola | 0,878052 | 352,611922 |
| Top-4 | 0,863858 | 263,901365 |
| Adaptativo | 0,867618 | 49,009877 |

Adaptativo supera numéricamente Top-4 en 0,003760 F1 y reduce tiempo medio
81,4% en este split; pierde frente a ambos ensambles. No es media completa
DTD/ResMLP ni evidencia inferencial de equivalencia/superioridad general.
Acuerdo de clases frente a caché: Completa 99,8404%, adaptativo 99,9468%,
demás 100%. Fuente v6/jobs/DTD_resmlp_s42_f1/online y online_audit.

Cobertura: 46 condiciones con registros auditados, 198.920 llamadas completas,
230 filas condición–método; reserva física del séptimo split SVM intacta.
DTD/ResMLP dos de diez. Worker 45000 inició el tercero (índice 2), único
benchmark GPU 47128. Sin fallos nuevos, reintentos, duplicaciones o cambios.

## Seguimiento 30-10-2026, 10:04 UTC

Tercer split DTD/ResMLP (índice 2): 1.750/9.400 llamadas. Worker 45000 y
único benchmark GPU 47128 vivos, estado/log sin cierre ni fallo nuevo.
La ventana de despacho v6 está por terminar; se deja completar la condición
activa antes de una continuación. Cobertura sin cambios: 46 condiciones
con registros auditados y 198.920 llamadas completas; reserva física del
séptimo split SVM preservada. Sin duplicaciones, reintentos o cambios.

## Seguimiento 30-10-2026, 10:19 UTC

Tercer split DTD/ResMLP (índice 2) avanza a 3.550/9.400 llamadas. Worker
45000 y único benchmark GPU 47128 vivos, estado/log sin fallo nuevo. La
ventana de despacho v6 venció; se deja terminar y auditar el trabajo activo.
Cobertura sin nuevo cierre: 46 condiciones con registros auditados, 198.920
llamadas completas y reserva física del séptimo split SVM preservada.
Sin duplicaciones, reintentos o cambios científicos.

## Seguimiento 30-10-2026, 10:34 UTC

Tercer split DTD/ResMLP (índice 2): 5.300/9.400 llamadas. Worker 45000 y
único benchmark GPU 47128 vivos, estado/log sin cierre ni error nuevo.
Se deja completar la condición activa; cobertura permanece en 46 condiciones
con registros auditados y 198.920 llamadas completas. Reserva física del
séptimo split SVM intacta; sin duplicaciones, reintentos o cambios.

## Seguimiento 30-10-2026, 10:49 UTC

Tercer split DTD/ResMLP (índice 2) avanza a 7.050/9.400 llamadas. Worker
45000 y único benchmark GPU 47128 vivos, estado/log sin error nuevo. No
hay cierre adicional: 46 condiciones con registros auditados y 198.920
llamadas completas; reserva física del séptimo split SVM preservada.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 30-10-2026, 11:04 UTC

Tercer split DTD/ResMLP (índice 2): 8.800/9.400 llamadas. Worker 45000 y
único benchmark GPU 47128 vivos, estado/log sin fallo nuevo. Todavía no
se contabiliza como cierre: 46 condiciones con registros auditados y
198.920 llamadas completas, con reserva física del séptimo split SVM
preservada. Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 30-10-2026, 11:20 UTC: tercer DTD/ResMLP auditado y v7

Split oficial 3 (índice 2): 9.400 llamadas, 1.880 imágenes por método,
auditoría ONLINE_CALL_RECORDS_REAGGREGATED. F1 y latencias de las mismas
llamadas online; sin afirmación de paridad universal de vectores.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,862362 | 1506,826724 |
| Diversidad | 0,877538 | 368,183455 |
| Tómbola | 0,875572 | 358,695765 |
| Top-4 | 0,862218 | 264,372675 |
| Adaptativo | 0,872924 | 55,776780 |

Adaptativo supera numéricamente Top-4 en 0,010706 F1 y reduce tiempo medio
78,9% en este split; pierde frente a ambos ensambles. No es media completa
DTD/ResMLP ni superioridad general. Acuerdo de clases frente a caché:
Completa 99,7340%, Top-4 99,9468%, demás 100%. Fuente:
v6/jobs/DTD_resmlp_s42_f2/online y online_audit.

Cobertura: 47 condiciones con registros auditados, 208.320 llamadas y
235 filas condición–método; reserva física del séptimo split SVM preservada.
V6 terminó normalmente a 11:09:44 UTC, sin fallos nuevos. Comprobada ausencia
de workers/benchmarks activos, se lanzó v7 en carpeta nueva con siete
ResMLP DTD nunca iniciados, índices 3–9, mismas recetas, hashes y tres horas
de despacho. Worker 48261, sesión 84016, primer job DTD_resmlp_s42_f3.
Manifiesto SHA256 d9196110ee8bf8e3b3971adf828e6579724d2c822c399d5dbe48e400d2956e46.
No se repiten diagnósticos o condiciones; retenciones Outex/Soil/KTH intactas.

## Seguimiento 30-10-2026, 11:35 UTC

Cuarto split DTD/ResMLP (índice 3): 1.400/9.400 llamadas. Worker v7 48261
y único benchmark GPU 48264 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 47 condiciones con registros auditados y 208.320
llamadas completas; reserva física del séptimo split SVM preservada.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 30-10-2026, 11:50 UTC

Cuarto split DTD/ResMLP (índice 3) avanza a 2.950/9.400 llamadas. Worker
48261 y único benchmark GPU 48264 vivos, estado/log sin error nuevo.
No hay cierre adicional: 47 condiciones con registros auditados y 208.320
llamadas completas; reserva física del séptimo split SVM intacta. Sin
duplicaciones, reintentos o cambios científicos.

## Pausa inmediata por solicitud del usuario, 30-10-2026

Automatización PAUSED confirmada. Benchmark v7 48264 y worker 48261
detenidos voluntariamente por SIGTERM, después de verificar comandos y
detener primero el despacho. Consulta posterior de procesos sin workers
o benchmarks activos. No se borraron ni sobrescribieron resultados.
Cuarto DTD/ResMLP queda parcial (último checkpoint observado 3.100/9.400),
fuera del recuento completo y sin etiqueta de fallo científico. Estados JSON
running pueden quedar obsoletos por la terminación por señal; este registro
documenta la interrupción humana. No tiene reanudación exacta garantizada;
una repetición requerirá decisión explícita y directorio nuevo. No iniciar
otra cola hasta solicitud de reanudación. Cobertura completa sin cambios:
47 condiciones auditadas, 208.320 llamadas; reserva física SVM preservada.

## Reanudación 31-10-2026, 21:56 Asunción (01-11, 00:56 UTC)

Solicitud explícita de continuar y programar revoca pausa. Verificados
ausencia de workers/benchmarks y GPU disponible. La transición desde v7
interrumpida se documenta con recibo user_pause_resume_receipt.json ligado
a hashes de worker y manifiesto, sin reescribirlos como completos.
Adaptador nuevo resume_user_paused_online.py mantiene source/config guards,
rechaza recibos alterados o autorización de reintento y excluye parciales.
9 pruebas enfocadas aprobadas (adaptador nuevo + tests de continuación previa).
No cambios de método, selección, modelos, semillas, particiones o tolerancias.

Outputs nuevos: results/analysis/overnight_online_resume_20261031_v8/,
seis condiciones DTD/ResMLP nunca iniciadas, índices 4–9. Primer job índice 4;
worker 817, sesión 72844, manifiesto SHA256
70ecb78aede6b5d71d7580b4b1a66ff7fcf034961fb109a4ac52d11a5977ea95.
Reutiliza diagnóstico DTD aprobado verificado, sin repetirlo. Ventana de
despacho tres horas, timeouts anteriores. Automatización existente confirmó
ACTIVE, intervalo 15 minutos, sin duplicarla. Receta original conservada.

Índice 3 parcial no se repite: se solicitó decisión del usuario en paralelo.
Continúan reservas Outex/Soil/KTH y latencia SVM. Cobertura completa sin
cambios: 47 condiciones y 208.320 llamadas. Sin manuscrito, commits o push.

## Seguimiento 01-11-2026, 01:12 UTC

Quinto split DTD/ResMLP (índice 4): 1.550/9.400 llamadas. Worker v8 817 y
único benchmark GPU 820 vivos, estado/log sin cierre ni error nuevo.
Cobertura sin cambios: 47 condiciones con registros auditados y 208.320
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 01:27 UTC

Quinto split DTD/ResMLP (índice 4) avanza a 3.300/9.400 llamadas. Worker
817 y único benchmark GPU 820 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 47 condiciones con registros auditados y 208.320
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 01:42 UTC

Quinto split DTD/ResMLP (índice 4): 5.050/9.400 llamadas. Worker 817 y único
benchmark GPU 820 vivos, estado/log sin cierre ni error nuevo. Cobertura
permanece en 47 condiciones con registros auditados y 208.320 llamadas
completas; parcial índice 3 excluido y reserva física SVM preservada. Sin
duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 01:57 UTC

Quinto split DTD/ResMLP (índice 4) avanza a 6.800/9.400 llamadas. Worker
817 y único benchmark GPU 820 vivos, estado/log sin cierre ni error nuevo.
Cobertura sin cambios: 47 condiciones con registros auditados y 208.320
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 02:12 UTC

Quinto split DTD/ResMLP (índice 4): 8.500/9.400 llamadas. Worker 817 y único
benchmark GPU 820 vivos, estado/log sin cierre ni fallo nuevo. Cobertura
permanece en 47 condiciones con registros auditados y 208.320 llamadas
completas; parcial índice 3 excluido y reserva física SVM preservada. Sin
duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 02:27 UTC: quinto split DTD/ResMLP auditado

Split oficial 5 (índice 4): 9.400 llamadas, 1.880 imágenes por método,
auditoría ONLINE_CALL_RECORDS_REAGGREGATED. F1 y latencias de las mismas
llamadas online, sin afirmar paridad universal de vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,868941 | 1579,787060 |
| Diversidad | 0,879831 | 364,634004 |
| Tómbola | 0,877973 | 322,931445 |
| Top-4 | 0,866233 | 266,195885 |
| Adaptativo | 0,871380 | 47,293735 |

Adaptativo supera numéricamente Top-4 en 0,005147 F1 y reduce tiempo medio
82,2% en este split; pierde frente a ambos ensambles. No es promedio completo
DTD/ResMLP ni evidencia inferencial de superioridad general. Acuerdo de
clases frente a caché: Completa 99,9468%, demás 100%. Fuente:
v8/jobs/DTD_resmlp_s42_f4/online y online_audit.

Cobertura: 48 condiciones con registros auditados, 217.720 llamadas completas,
240 filas condición–método. DTD/ResMLP tiene cuatro splits completos
(índices 0,1,2,4), no cinco: el índice 3 sigue parcial sin autorización de
repetición recibida. Worker 817 inició split oficial 6 (índice 5), único
benchmark GPU 2058, 700/9.400 llamadas al consultar. Reserva física SVM
preservada, sin fallos nuevos, reintentos, duplicaciones o cambios científicos.

## Seguimiento 01-11-2026, 02:42 UTC

Sexto split DTD/ResMLP (índice 5): 2.450/9.400 llamadas. Worker 817 y único
benchmark GPU 2058 vivos, estado/log sin cierre ni error nuevo. Cobertura
sin cambios: 48 condiciones con registros auditados y 217.720 llamadas
completas; parcial índice 3 excluido y reserva física SVM preservada.
Sin duplicaciones, reintentos ni cambios metodológicos.

## Seguimiento 01-11-2026, 02:57 UTC

Sexto split DTD/ResMLP (índice 5) avanza a 4.150/9.400 llamadas. Worker
817 y único benchmark GPU 2058 vivos, estado/log sin fallo nuevo. No hay
cierre adicional: 48 condiciones con registros auditados y 217.720 llamadas
completas; parcial índice 3 excluido y reserva física SVM intacta. Sin
duplicaciones, reintentos o cambios científicos.

## Seguimiento 01-11-2026, 03:12 UTC

Sexto split DTD/ResMLP (índice 5): 5.850/9.400 llamadas. Worker 817 y único
benchmark GPU 2058 vivos, estado/log sin cierre ni error nuevo. Cobertura
sin cambios: 48 condiciones con registros auditados y 217.720 llamadas
completas; parcial índice 3 excluido y reserva física SVM preservada.
Sin duplicaciones, reintentos ni cambios metodológicos.

## Seguimiento 01-11-2026, 03:27 UTC

Sexto split DTD/ResMLP (índice 5) avanza a 7.550/9.400 llamadas. Worker
817 y único benchmark GPU 2058 vivos, estado/log sin fallo nuevo. No hay
cierre adicional: 48 condiciones con registros auditados y 217.720 llamadas
completas; parcial índice 3 excluido y reserva física SVM intacta. Sin
duplicaciones, reintentos o cambios científicos.

## Seguimiento 01-11-2026, 03:42 UTC

Sexto split DTD/ResMLP (índice 5): 9.300/9.400 llamadas. Worker 817 y único
benchmark GPU 2058 vivos, estado/log sin fallo nuevo. Aún no se contabiliza
como cierre: 48 condiciones con registros auditados y 217.720 llamadas
completas; parcial índice 3 excluido y reserva física SVM preservada.
Sin duplicaciones, reintentos ni cambios metodológicos.

## Seguimiento 01-11-2026, 03:57 UTC: sexto split DTD/ResMLP auditado

Split oficial 6 (índice 5): 9.400 llamadas, 1.880 imágenes por método,
auditoría ONLINE_CALL_RECORDS_REAGGREGATED. F1 y tiempos de las mismas
llamadas online; sin afirmación de paridad universal de vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,856046 | 1582,924457 |
| Diversidad | 0,875037 | 371,634772 |
| Tómbola | 0,877541 | 346,140012 |
| Top-4 | 0,869500 | 270,171609 |
| Adaptativo | 0,853610 | 38,474077 |

Adaptativo pierde 0,015891 F1 (1,5891 puntos porcentuales) frente a Top-4
y reduce tiempo medio 85,8% en este split. Tiene menor F1 que los otros
cuatro métodos. No es promedio completo DTD/ResMLP ni equivalencia formal.
Acuerdo de clases frente a caché: Completa y adaptativo 99,9468%, demás
100%; se mantiene F1 online. Fuente v8/jobs/DTD_resmlp_s42_f5/online y auditoría.

Cobertura: 49 condiciones con registros auditados, 227.120 llamadas completas,
245 filas condición–método. DTD/ResMLP cinco completos (índices 0,1,2,4,5),
índice 3 parcial sin autorización de repetición recibida. Worker 817 ejecuta
split oficial 7 (índice 6), único benchmark GPU 3194, 1.550/9.400 llamadas.
Ventana de despacho v8 vencida; dejar terminar y auditar activo antes de
continuar índices 7–9 en carpeta nueva. Reserva física SVM intacta, sin
fallos nuevos, reintentos, duplicaciones o cambios científicos.

## Seguimiento 01-11-2026, 04:12 UTC

Séptimo split DTD/ResMLP (índice 6): 3.250/9.400 llamadas. Worker 817 y
único benchmark GPU 3194 vivos, estado/log sin cierre ni error nuevo.
Se deja finalizar y auditar el activo tras vencer la ventana v8. Cobertura
sin cambios: 49 condiciones con registros auditados y 227.120 llamadas
completas; parcial índice 3 excluido y reserva física SVM preservada.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 04:27 UTC

Séptimo split DTD/ResMLP (índice 6) avanza a 5.000/9.400 llamadas. Worker
817 y único benchmark GPU 3194 vivos, estado/log sin fallo nuevo. No hay
cierre adicional: 49 condiciones con registros auditados y 227.120 llamadas
completas; parcial índice 3 excluido y reserva física SVM intacta. Sin
duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 04:42 UTC

Séptimo split DTD/ResMLP (índice 6): 6.700/9.400 llamadas. Worker 817 y
único benchmark GPU 3194 vivos, estado/log sin cierre ni error nuevo.
Cobertura sin cambios: 49 condiciones con registros auditados y 227.120
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 04:57 UTC

Séptimo split DTD/ResMLP (índice 6) avanza a 8.400/9.400 llamadas. Worker
817 y único benchmark GPU 3194 vivos, estado/log sin fallo nuevo. Aún no
hay cierre adicional: 49 condiciones con registros auditados y 227.120
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 05:12 UTC: séptimo oficial auditado y v9

DTD/ResMLP split oficial 7 (índice 6): 9.400 llamadas, 1.880 imágenes por
método, auditoría ONLINE_CALL_RECORDS_REAGGREGATED. Calidad y tiempos de las
mismas llamadas online; no se afirma paridad universal de vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,867450 | 1577,045221 |
| Diversidad | 0,886002 | 338,127540 |
| Tómbola | 0,884637 | 370,391024 |
| Top-4 | 0,860901 | 270,539062 |
| Adaptativo | 0,882455 | 52,289816 |

Adaptativo supera numéricamente Top-4 en 0,021554 F1 y reduce tiempo medio
80,7% en este split; pierde frente a ambos ensambles. No es promedio completo
DTD/ResMLP ni evidencia inferencial de superioridad general. Acuerdo de
clases frente a caché: adaptativo y Top-4 99,8936%, demás 100%. Fuente:
v8/jobs/DTD_resmlp_s42_f6/online y online_audit.

Cobertura: 50 condiciones con registros auditados, 236.520 llamadas completas,
250 filas condición–método. DTD/ResMLP seis completos (índices 0,1,2,4,5,6),
no siete: índice 3 parcial, sin autorización recibida para repetir. Reserva
física SVM intacta. V8 cerró normalmente a 05:05:44 UTC, sin fallos nuevos.
Comprobada ausencia de workers/benchmarks activos, se lanzó v9 nueva con
tres condiciones DTD/ResMLP nunca iniciadas (índices 7–9), mismo script
probado y ventana de tres horas. Worker 4321, sesión 74244, primer job
DTD_resmlp_s42_f7. Manifiesto SHA256
787efac6f3355fb32caf8e64eed8da10e717f1aabfc37a0b35e367382d1e0204.
Sin reintentos, diagnósticos repetidos, cambios científicos, commits o push.

## Seguimiento 01-11-2026, 05:27 UTC

Octavo split DTD/ResMLP (índice 7): 1.600/9.400 llamadas. Worker v9 4321
y único benchmark GPU 4324 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 50 condiciones con registros auditados y 236.520
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 05:42 UTC

Octavo split DTD/ResMLP (índice 7) avanza a 3.300/9.400 llamadas. Worker
4321 y único benchmark GPU 4324 vivos, estado/log sin cierre ni error nuevo.
Cobertura sin cambios: 50 condiciones con registros auditados y 236.520
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 05:57 UTC

Octavo split DTD/ResMLP (índice 7): 5.050/9.400 llamadas. Worker 4321 y
único benchmark GPU 4324 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura permanece en 50 condiciones con registros auditados y 236.520
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 06:12 UTC

Octavo split DTD/ResMLP (índice 7) avanza a 6.800/9.400 llamadas. Worker
4321 y único benchmark GPU 4324 vivos, estado/log sin cierre ni error nuevo.
Cobertura sin cambios: 50 condiciones con registros auditados y 236.520
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 06:27 UTC

Octavo split DTD/ResMLP (índice 7): 8.550/9.400 llamadas. Worker 4321 y
único benchmark GPU 4324 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura permanece en 50 condiciones con registros auditados y 236.520
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 06:42 UTC: octavo oficial DTD/ResMLP auditado

Split oficial 8 (índice 7): 9.400 llamadas, 1.880 imágenes por método,
auditoría ONLINE_CALL_RECORDS_REAGGREGATED. Calidad y tiempo de las mismas
llamadas online; no se afirma paridad universal de vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,842701 | 1568,152198 |
| Diversidad | 0,863479 | 372,564911 |
| Tómbola | 0,857619 | 340,384230 |
| Top-4 | 0,850453 | 264,599883 |
| Adaptativo | 0,858241 | 44,105604 |

Adaptativo supera numéricamente Top-4 en 0,007788 F1 y reduce tiempo medio
83,3% en este split. También supera numéricamente tómbola y Completa, pero
pierde frente a diversidad. No es promedio completo DTD/ResMLP ni conclusión
inferencial de superioridad general. Acuerdo frente a caché: Completa
99,7872%, demás 100%. Fuente v9/jobs/DTD_resmlp_s42_f7/online y online_audit.

Cobertura: 51 condiciones con registros auditados, 245.920 llamadas completas,
255 filas condición–método. DTD/ResMLP siete completos (índices 0,1,2,4,5,6,7);
índice 3 sigue parcial sin permiso recibido para repetir. Worker 4321 ejecuta
noveno oficial (índice 8), único benchmark GPU 5385, 750/9.400 llamadas.
Reserva física SVM preservada; sin fallos nuevos, reintentos o cambios.

## Seguimiento 01-11-2026, 06:57 UTC

Noveno split DTD/ResMLP (índice 8): 2.450/9.400 llamadas. Worker 4321 y
único benchmark GPU 5385 vivos, estado/log sin cierre ni error nuevo.
Cobertura sin cambios: 51 condiciones con registros auditados y 245.920
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 07:12 UTC

Noveno split DTD/ResMLP (índice 8) avanza a 4.150/9.400 llamadas. Worker
4321 y único benchmark GPU 5385 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 51 condiciones con registros auditados y 245.920
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 07:27 UTC

Noveno split DTD/ResMLP (índice 8): 5.850/9.400 llamadas. Worker 4321 y
único benchmark GPU 5385 vivos, estado/log sin cierre ni error nuevo.
Cobertura permanece en 51 condiciones con registros auditados y 245.920
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 07:42 UTC

Noveno split DTD/ResMLP (índice 8) avanza a 7.550/9.400 llamadas. Worker
4321 y único benchmark GPU 5385 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 51 condiciones con registros auditados y 245.920
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 07:57 UTC

Noveno split DTD/ResMLP (índice 8): 9.250/9.400 llamadas. Worker 4321 y
único benchmark GPU 5385 vivos, estado/log sin fallo nuevo. Todavía no
se contabiliza como cierre: 51 condiciones con registros auditados y 245.920
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 08:12 UTC: noveno oficial DTD/ResMLP auditado

Split oficial 9 (índice 8): 9.400 llamadas, 1.880 imágenes por método,
auditoría ONLINE_CALL_RECORDS_REAGGREGATED. F1 y latencias de las mismas
llamadas online; sin afirmar paridad universal con vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,861447 | 1573,943606 |
| Diversidad | 0,880759 | 367,833493 |
| Tómbola | 0,877369 | 381,633193 |
| Top-4 | 0,854398 | 270,663594 |
| Adaptativo | 0,861613 | 36,884558 |

Adaptativo supera numéricamente Top-4 en 0,007215 F1 y reduce tiempo medio
86,4% en este split; pierde frente a ambos ensambles. No es promedio completo
DTD/ResMLP ni evidencia inferencial de superioridad general. Acuerdo de
clases frente a caché: Completa 99,9468%, demás 100%. Fuente:
v9/jobs/DTD_resmlp_s42_f8/online y online_audit.

Cobertura: 52 condiciones con registros auditados, 255.320 llamadas completas,
260 filas condición–método. DTD/ResMLP ocho completos, índice 3 parcial
excluido sin permiso recibido para repetir. Worker 4321 ejecuta décimo
oficial (índice 9), único benchmark GPU 6759, 1.450/9.400 llamadas al consultar.
Ventana v9 próxima a vencer: dejar terminar y auditar activo. No crear otra
cola vacía al cerrar; quedará pendiente el parcial y las reservas conocidas.
Reserva física SVM intacta; sin fallos nuevos, reintentos o cambios.

## Seguimiento 01-11-2026, 08:27 UTC

Décimo split DTD/ResMLP (índice 9): 3.200/9.400 llamadas. Worker 4321 y
único benchmark GPU 6759 vivos, estado/log sin cierre ni error nuevo.
Ventana v9 vencida; se deja terminar y auditar el activo. Cobertura sin
cambios: 52 condiciones con registros auditados y 255.320 llamadas completas;
parcial índice 3 excluido y reserva física SVM intacta. Sin duplicaciones,
reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 08:42 UTC

Décimo split DTD/ResMLP (índice 9) avanza a 4.950/9.400 llamadas. Worker
4321 y único benchmark GPU 6759 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 52 condiciones con registros auditados y 255.320
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 08:57 UTC

Décimo split DTD/ResMLP (índice 9): 6.650/9.400 llamadas. Worker 4321 y
único benchmark GPU 6759 vivos, estado/log sin cierre ni error nuevo.
Cobertura permanece en 52 condiciones con registros auditados y 255.320
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos o cambios metodológicos.

## Seguimiento 01-11-2026, 09:12 UTC

Décimo split DTD/ResMLP (índice 9) avanza a 8.350/9.400 llamadas. Worker
4321 y único benchmark GPU 6759 vivos, estado/log sin cierre ni fallo nuevo.
Cobertura sin cambios: 52 condiciones con registros auditados y 255.320
llamadas completas; parcial índice 3 excluido y reserva física SVM intacta.
Sin duplicaciones, reintentos ni cambios científicos.

## Seguimiento 01-11-2026, 09:27 UTC: cola v9 cerrada, no panel completo

Décimo oficial DTD/ResMLP (índice 9): 9.400 llamadas, 1.880 imágenes por
método, auditoría ONLINE_CALL_RECORDS_REAGGREGATED. F1 y tiempos de las
mismas llamadas online; sin afirmar paridad universal de vectores archivados.

| Método | Macro-F1 online | Media ms/imagen |
| --- | ---: | ---: |
| Completa-22 | 0,855978 | 1550,235183 |
| Diversidad | 0,868970 | 364,209747 |
| Tómbola | 0,862573 | 367,152447 |
| Top-4 | 0,849946 | 268,223937 |
| Adaptativo | 0,849671 | 57,528598 |

Adaptativo pierde 0,000274 F1 frente a Top-4 y reduce tiempo medio 78,6%
en este split; tiene menor F1 que los otros cuatro métodos. No es una
conclusión inferencial ni media DTD/ResMLP completa. Acuerdo frente a caché:
Completa 99,8936%, demás 100%. Fuente v9/jobs/DTD_resmlp_s42_f9/online y auditoría.

V9 terminó normalmente a 09:21:11 UTC; comprobación posterior sin procesos
de benchmark/continuación activos. No se inicia cola vacía. Cobertura de
registros auditados: 53 condiciones, 264.720 llamadas, 265 filas condición–método.
DTD/SVM diez de diez; DTD/ResMLP nueve de diez: índices 0,1,2,4,5,6,7,8,9.
No se publica media de diez ni se completa con F1 histórico el índice 3.

Intervenciones pendientes: autorizar una medición nueva del índice 3
interrumpido por petición humana; resolver procedencia DeiT en Outex/Soil
sin relajar tolerancias ni repetir diagnósticos; reconciliar KTH; revisar
aptitud física del séptimo split SVM con tiempos extremos. Datos y reservas
preservados. No avanzar a réplicas de papers como si el panel local estuviera
cerrado. Sin reintentos, cambios al manuscrito, commits o push.

## Repetición única autorizada: 01-11-2026, 12:14 UTC (09:14 Asunción)

El usuario autorizó expresamente repetir solo DTD_resmlp_s42_f3 en carpeta
nueva conservando el parcial. No es reintento automático ni permiso para
fallos científicos de otros datasets. Sin procesos de benchmark/continuación
activos al iniciar. Manifiesto de una condición, copiada de v7 con config y
hashes originales sin cambios; únicamente outputs nuevos y plazo operativo.

Carpeta: results/analysis/overnight_online_retry_20261101_DTD_resmlp_f3/.
Worker original probado overnight_multidataset_online.py, PID 9095,
sesión 40526, primer y único job DTD_resmlp_s42_f3. Manifiesto SHA256
9a71f1b5ad7ff0cac4a75275a12ff1d7ab4a442941ec10aa2691e2f7b32dddbe.
Inicio 12:14:58 UTC. Misma medición batch1 y F1 de las mismas llamadas,
repeat=1, dos hilos CPU, modelos offline, selección OOF y head congelados;
timeout de ejecución 14.400 s y auditoría posterior. Reutiliza por copia
diagnóstico DTD previamente aprobado. No se sobrescribe parcial v7.

Cobertura completa sigue 53 condiciones/264.720 llamadas hasta el cierre
y auditoría de esta repetición. Reservas físicas DTD/SVM, DeiT Outex/Soil y
KTH intactas. Sin cambios al manuscrito, commits o push. Automatización
existente continúa y debe seguir ahora esta carpeta. Si falla, no repetir.

## Seguimiento 01-11-2026, 12:27 UTC

Repetición única autorizada DTD/ResMLP índice 3: 1.200/9.400 llamadas.
Worker 9095 y único benchmark GPU 9097 vivos, estado/log sin cierre ni
fallo nuevo. Parcial original conservado; no se cuenta la nueva condición
hasta cerrar y auditar. Cobertura sin cambios: 53 condiciones con registros
auditados y 264.720 llamadas completas; reservas conocidas intactas.
Sin duplicaciones, reintentos adicionales o cambios metodológicos.

## Seguimiento 01-11-2026, 12:42 UTC

Repetición única autorizada DTD/ResMLP índice 3: 2.900/9.400 llamadas.
Worker 9095 y único benchmark GPU 9097 vivos, estado/log sin cierre ni
error nuevo. Cobertura sin cambios: 53 condiciones con registros auditados
y 264.720 llamadas completas; parcial original y reservas preservados.
Sin duplicaciones, reintentos adicionales ni cambios científicos.

## Seguimiento 01-11-2026, 12:57 UTC

Repetición única autorizada DTD/ResMLP índice 3: 4.600/9.400 llamadas.
Worker 9095 y único benchmark GPU 9097 vivos, estado/log sin cierre ni
fallo nuevo. Cobertura sin cambios: 53 condiciones con registros auditados
y 264.720 llamadas completas; parcial original y reservas preservados.
Sin duplicaciones, reintentos adicionales o cambios metodológicos.

## Seguimiento 01-11-2026, 13:12 UTC

Repetición única autorizada DTD/ResMLP índice 3: 6.300/9.400 llamadas.
Worker 9095 y único benchmark GPU 9097 vivos, estado/log sin cierre ni
error nuevo. Cobertura sin cambios: 53 condiciones con registros auditados
y 264.720 llamadas completas; parcial original y reservas preservados.
Sin duplicaciones, reintentos adicionales ni cambios científicos.

## Seguimiento 01-11-2026, 13:27 UTC

Repetición única autorizada DTD/ResMLP índice 3: 8.050/9.400 llamadas.
Worker 9095 y único benchmark GPU 9097 vivos, estado/log sin cierre ni
fallo nuevo. Cobertura sin cambios: 53 condiciones con registros auditados
y 264.720 llamadas completas; parcial original y reservas preservados.
Sin duplicaciones, reintentos adicionales o cambios metodológicos.

## Cierre DTD/ResMLP, 01-11-2026, 13:45 UTC

Repetición única autorizada índice 3 terminada y auditada: 9.400 llamadas,
1.880 imágenes y cinco métodos. Worker all_jobs_terminal, requires_review
vacío; no workers/benchmarks activos. Auditoría ONLINE_CALL_RECORDS_REAGGREGATED:
F1 y tiempos de las mismas llamadas. No certifica aislamiento del hardware.
Parcial v7 preservado y excluido, sin reemplazar ni omitir registros.

Consolidación completa de diez splits ResMLP: 94.000 llamadas, 18.800 por
método. Se comprobaron hashes de estados auditados, estados completos,
cobertura y unicidad de llamadas. Resumen nuevo con hashes de llamadas,
auditorías y resúmenes fuente:
results/analysis/overnight_online_retry_20261101_DTD_resmlp_f3/summary_DTD_resmlp_online_v1/summary.json.

Método | F1 macro medio de diez splits | Media ms de todas las llamadas
--- | ---: | ---:
Adaptive-selection-margin | 0.866019864 | 47.612719
Completa-22 | 0.861613633 | 1551.337844
Ens-diversidad | 0.877080173 | 366.447978
Ens-tombola | 0.874512525 | 356.182873
Top-4 | 0.861266856 | 267.504118

Sin afirmación de superioridad estadística; splits repetidos no constituyen
datasets independientes. Cobertura global 54 condiciones con registros
auditados, 274.120 llamadas completas y 270 filas condición×método.
FMD, CUReT y DTD tienen registros completos de ambos clasificadores.
Persiste reserva de comparabilidad física DTD/SVM índice 6; auditoría
aritmética no la resuelve. Outex/Soil continúan sujetos a fallos científicos
de binding DeiT y KTH a reconciliación metodológica. Las otras 40 condiciones
del panel de 94 no están completadas online. No estimar su cierre como mera
espera de GPU ni iniciar papers como si los seis datasets estuvieran cerrados.
Sin cambios de método, tolerancias, manuscrito, commits ni push.

## Desbloqueo autorizado y relanzamiento versionado, 01-11, 13:58 UTC

Usuario: «bueno resolve todo para continuar». Se pidieron decisiones concretas
y autorizó ambas: enmienda de representación DeiT Outex/Soil y observación
adicional completa DTD/SVM official7. Protocolo nuevo y acotado en
docs/fsc_tex/ENMIENDA_DESBLOQUEO_PANEL_2026-11-01.md; original sin editar.

DeiT: las dos salidas online ya guardadas no coinciden tampoco con ninguna
fila del archivo completo de Outex/Soil a1e-4 (mínimos errores máximos entre
0,167 y0,171). No se ejecutó otra prueba GPU para ese análisis ni se buscó
semilla. No resuelve causa/estado histórico. Se autoriza regenerar solo bloque
deit_s, preservar otros bloques byteidénticos referenciados por hash y ajustar
OOF adaptativo/heads en train antes del test, conservando controles archivados.

KTH: informe nuevo results/analysis/blocker_resolution_20261101/kth_reconciliation.json,
SHA256 feb328f31c176cd062c331ab9d50f024a2235b78189ea05b31bdb9a878ce0c9a.
4752imágenes rehasheadas,0divergencias, cuatro splits invertidos alineados
fila por fila, innerSGKF3 sample sin fuga,21bloques finitos alineados, loader
Ngrams raíz compatible. Habilita solo nuevo panel de calidad, no equivalencia
histórica de cascada ni online sin binding. Diagnóstico KTH nuevo probado.

DTD/SVM:80llamadas consecutivas contienen todas62>10s y25>60s; consumen5087,510s,
50,05% del tiempo registrado, en0,85% de llamadas. Sin timestamps por llamada
ni eventos históricos suficientes para atribuir causa. Original no eliminado
ni corregido. Repetición completa autorizada será evidencia adicional, no
selección de mejor latencia. Observador externo sin GPU polling, overhead
declarado, conserva UTC/monotónico/boottime/PID+startticks/CPU/RSS cada30s.

Infraestructura nueva probada:39tests focalizados de preparación/cola/observador/
bindingKTH pasaron. No es auditoría independiente ni prueba de calidad científica.
Manifiesto queue_v1 SHA256 ab504ed069cb827f76891c15e0959439e20e4da7be992fb62c3c06f4017bd7a4,
40condiciones únicas+1observación adicionalDTD,86tareas. Worker GPU14246,
CPU14242, inicio13:58:33UTC; extracción Outex PID14259 y calidadKTH/ResMLP/f0
PID14258 iniciadas sin trabajos anteriores activos. Sesiones72022/51653.
Paquetes/fuentes/configs/datos guardados por hash y versiones; CPU2hilos,
una tareaGPU, offline, locks y plazos por tarea, sin fallback/retry automático.
Originales y parciales intactos; sin manuscrito/commits/push.

Cobertura todavía54condiciones/274120llamadas completas auditadas. Esta
preparación/ejecución iniciada no agrega condiciones terminadas. Consultar
cpu.json/gpu.json y tasks/<id>/state.json de queue_v1. Continuar solo tareas
nunca despachadas después de ventana10h si no hay worker vivo; conservar
requires_review/blocked hasta nueva decisión. Papers aún diferidos.

### Binding aprobado y corrección de esquema Soil, 01-11

Outex: nueva extracción DeiT1360filas completada, hash embedding
534a96abd1ff9512b243e9df0c345ed771c0b10318d98c055b25bc2b2cbc226f;
binding nuevo aprobado en ambas filas a tolerancia original. KTH: primera y
última fila0/4751 aprobadas, errores máximos1,7136e-7 y1,2200e-7. No es
certificación completa de igualdad de biblioteca ni medición online terminada.

Soil se detuvo en validación del esquema CSV antes de construir el extractor:
source_path/labels texto no compatibles con path/label numérico/class_name del
loader existente. Se preservó requires_review; ninguna extracción Soil nueva
ni condición de calidad/online se completó por ese intento.
Adaptador prepare_soil_extraction_manifest.py probado:4tests; loader original
aceptó1140filas/7clases, imágenes rehasheadas, orden/grupos/labels equivalentes.
Recibo soil_schema_adapter_v1/receipt.json; CSV adaptado SHA256
6e3fbf6100548ee3f381abd008a3d6e1bbd563e4a4ceaf6f6cd560f007e711c1.
No se ejecutó GPU al validar el adaptador.

Usuario autorizó expresamente «Sí, despachar Soil con el formato corregido».
Cola nueva soil_format_resume_v1, SHA256 de manifiesto
5342efbbffea30d35e9f32050a2c6081bfdedb484fdd6de74e7c1e45b76a0fd2;
solo extracción+binding nuevos, no retry del estado anterior. Worker15566,
sesión90290, inicio14:05:59UTC, espera lock GPU compartido mientras DTD/SVM
adicional sigue activo. Si pasa, preparar las30condiciones Soil pendientes
con nueva raíz y rutas, sin duplicar CPU vigente. Fallo nuevo→revisión.
Cobertura completa sigue54/274120; calidad KTH y adicionalDTD son parciales.

## Primer cierre de calidad KTH/ResMLP, 01-11, 14:31 UTC

Official1/índice0 calidad y replay completos a14:17:09UTC, nueva cola queue_v1.
Auditoría CACHED_HEAD_PREDICTIONS_REPLAYED:5940filas,1188imágenes×5métodos,
sin nuevos fits en replay. Hash source_status verificado contra estado actual:
c2beeae2963b3e32deefc3c9a4389cd01e01d7bb2f1b83869cb0690a1d602c0a.
F1 macro en caché: Completa22 .985638817; Top4 .985649299; diversidad .989041999;
tómbola .989885327; adaptativa .979711177. Son valores de UNA condición y
representación caché, no media KTH ni F1/ms online. La adaptativa en esta
condición queda por debajo de los cuatro controles; conservar sin ajuste por test.

Official2 KTH/ResMLP en calidad, PID16273; un único benchmarkGPU DTD/SVM
adicional PID14363,3100/9400llamadas, con observador; Soil15566 esperando lock.
Sin errores científicos nuevos ni reintentos. Cobertura física sin cambios:
54condiciones únicas y274120llamadas completas auditadas. AdicionalDTD parcial
no aumenta cobertura, y KTH online no se cuenta hasta cerrar y auditar.

## Seguimiento 01-11, 14:46 UTC

KTH/ResMLP official2/índice1 calidad y replay completos,5940predicciones,
auditoría CACHED_HEAD_PREDICTIONS_REPLAYED y hash del estado verificado.
Dos de cuatro condiciones ResMLP con calidad/replay; no media completa ni
latencia física KTH. Official3/índice2 activo PID16602. DTD/SVM adicional
4650/9400llamadas PID14363, único benchmark GPU; observador vigente. Soil15566
espera lock, sin repetir el fallo previo. No fallos nuevos, cambios científicos
ni duplicaciones. Cobertura online auditada sigue54condiciones/274120llamadas.

## Seguimiento 01-11, 15:01 UTC

KTH/ResMLP official3/índice2 calidad y replay completos:5940predicciones,
CACHED_HEAD_PREDICTIONS_REPLAYED, hash de estado coincidente. Tres de cuatro
condiciones de calidad ResMLP, no media completa ni evaluación física KTH.
Official4/índice3 activo PID16869. DTD/SVM adicional6200/9400llamadas PID14363,
único benchmark GPU; Soil15566 sigue esperando lock. No nuevos fallos/retries,
configuraciones intactas. Cobertura física completa sigue54/274120; parciales
y repetición adicional no aumentan condiciones únicas.

## Cierre de calidad KTH/ResMLP, 01-11, 15:16 UTC

Cuatro de cuatro condiciones de calidad y replay cerradas y verificadas contra
hashes de sus estados:23760predicciones,1188imágenes×5métodos por condición.
Resumen nuevo con fuentes: queue_v1/summary_KTH_resmlp_cached_quality_v1/summary.json.
F1 macro medio de cuatro splits EN CACHÉ: Completa22 .945652786; Top4 .952320017;
diversidad .955620731; tómbola .954288686; adaptativa .939089669.
La adaptativa queda por debajo de todos los controles en esta calidad media;
no ajustar procedimiento mirando test ni presentar como F1 online. No medición
de latencia KTH completa todavía, ni prueba de equivalencia histórica.

KTH/SVM official1 también calidad/replay auditados5940filas y hash coincidente;
official2 activo PID17230. DTD/SVM adicional7750/9400llamadas, único benchmark,
PID14363; Soil15566 espera lock. Sin nuevos fallos ni duplicaciones. Cobertura
física completa sigue54condiciones/274120llamadas; repetición adicional no suma
condición única. No hay media online KTH hasta sus cuatro condiciones por head.

## Cierre de calidad KTH de ambos clasificadores, 01-11, 15:31 UTC

Ocho condiciones (cuatro SVM/cuatro ResMLP),47520predicciones replayadas.
Verificados hashes source_status,5940filas por condición y1188por método.
Resumen SVM nuevo: queue_v1/summary_KTH_svm_cached_quality_v1/summary.json.
Media F1 macro en caché SVM: Completa22 .960130906, Top4 .954391233,
diversidad .954307344, tómbola .954006273, adaptativa .938996502.
La adaptativa también queda debajo de todos los controles con SVM. No
optimizar por test ni mezclar estas medias con los tiempos físicos pendientes.
Reservas históricas KTH intactas; no inferencia estadística de superioridad.

CPU ahora Outex/ResMLP PID17608. DTD/SVM adicional9350/9400llamadas PID14363,
todavía running sin auditoría final; Soil15566 espera lock. Sin nuevos fallos,
duplicaciones ni cambios al manuscrito. Cobertura física única54/274120,
sin contar calidad en caché ni adicionalDTD parcial como nuevos completados.

## Cierre adicional DTD y fallo de ruta KTH, 01-11, 15:46 UTC

DTD/SVM official7 adicional terminó y pasó ONLINE_CALL_RECORDS_REAGGREGATED
a15:31:49UTC,9400llamadas. Hash de estado87a1c5f0ba773d2538f88e9220ac89a0cad6f0851999d53ecc842e43f81ee4d6
verificado por auditoría. Observador cerró target_exited, sin señales al target.
Comparación íntegra y hashes nuevos: queue_v1/DTD_additional_comparison_v1.json.
F1 online idéntico por método entre ambas versiones. En adicional no hay
llamadas>60s (máximo global2281,489ms), frente25en original. Medias adicionales
ms: adaptativa48,998; Completa1820,934; diversidad344,550; tómbola379,293;
Top4271,590. No elimina reserva física del original, prueba causa ni certifica
aislamiento. Se mantienen ambas versiones y sus extremos sin sustitución.
54condiciones únicas/274120llamadas primarias auditadas más9400adicionales;
total283520observaciones completas auditadas, sin aumentar cobertura única.

Outex nueva representación cerró calidad/replay de ambos heads; CPUall_tasks_terminal.
GPU pasó a onlineOutex/ResMLP PID18024. Soil15566 espera lock compartido.

Incidente nuevo:8condiciones KTH online requieren revisión por FileNotFoundError
en benchmark_local_single_image.py:111: ruta embeddings_extensions/KTHTIPS2b
en lugar de KTH-TIPS2-b. Todas fallaron antes de construir extractores/medir
llamadas; calidad y binding aprobados siguen válidos. Preservar los8estados,
logs y outputs parciales. El worker no reintentó ninguna de esas condiciones.
Se creó benchmark_local_single_image_alias_v1.py con única corrección de ruta.
3tests aprobados, incluida equivalencia AST del programa salvo helper/expresión
de ruta. Original y fuentes activas intactos. Se solicitó autorización para
despachar8mediciones nuevas con mismos heads/selección, sin relajar tolerancias;
pendiente respuesta. No contar KTH online como completado ni rellenar con caché.

## Cierre físico Outex/ResMLP, 01-11, 16:16 UTC

Nueva versión DeiT: único split oficial completo,680imágenes,3400llamadas,
ONLINE_CALL_RECORDS_REAGGREGATED y hash source_status coincidente. Fuente:
queue_v1/jobs/Outex13Official1360_resmlp_s42_f0/online{,_audit}.
F1/ms media de las mismas llamadas: adaptativa .960868749/21,648947;
Completa22 .947678728/1563,182395; diversidad .952206267/349,427860;
tómbola .957757026/337,531757; Top4 .927490407/263,768511.
No F1 histórico combinado con tiempos nuevos; ni afirmación de superioridad
estadística o independencia del test ya observado. Archivo anterior preservado.
Observador cerró target_exited, sin señales ni certificación de aislamiento.

Cobertura física única55de94condiciones,277520llamadas primarias completas
auditadas; más9400adicionalesDTD=286920observaciones auditadas en total.
Outex/SVM activoPID18720, único benchmark. Soil15566 espera lock compartido.
KTH online requiere decisión de redespacho por alias; calidad íntegra conservada,
sin reintentos automáticos. CPU original terminó normalmente y no está activo.

## Cierre Outex completo y lanzamiento Soil, 01-11, 16:46 UTC

Outex/SVM online/auditoría terminó16:37:16UTC,680imágenes×5métodos=3400llamadas,
hash estado2aa36025efd5f3d3f6121c71487e6777e4c16f5e6c1f4064ffa672a8dd9d74fa
verificado. F1/ms media online: adaptativa .927581357/40,327673;
Completa22 .955222001/1574,192011; diversidad .944197491/358,167907;
tómbola .939870333/362,654890; Top4 .928778548/265,377279.
Adaptativa SVM inferior en F1 a los cuatro controles; no selección post-test.
Outex ambos clasificadores y cinco métodos completo,6800llamadas. Resumen y
hashes:queue_v1/summary_Outex_both_online_v1/summary.json. Representación nueva
explícitamente enmendada, histórico preservado, sin certificación de aislamiento.

Cobertura única56/94condiciones,280920llamadas primarias auditadas más9400de
observación adicionalDTD=290320totales auditadas. Falta onlineSoil30 y KTH8.

Soil nuevo: extracción completa y binding aprobado,2checks a1e-4, errores
máximos1,9744e-7 y1,5646e-7. Embedding71165181b79c1ecba54703392076421011fd4278ff8c3c84181c5b71459bc9fd.
Se comprobó que las30condiciones enmendadas previas jamás iniciaron calidad/
online (blocked por dependencia); no son reintentos de experimentos fallidos.
Preparador nuevo y cola probados con14tests focalizados aprobados.
Nueva soil_pending_v1, SHA manifiesto3fab9e1b648be1d7b60b660ae5798c12f56346b4442de7ed02ee9aee2e0b1829,
60tareas de30condiciones, mismas semillas/particiones/controles/presupuesto/
selecciónOOFtrain-only. Guarda nuevos heads, predicciones, tiempos y auditorías.
WorkersCPU19573sesión81741/GPU19563sesión32808; CPU PID19574 primera calidad
ResMLP/42/f0, GPU espera dependencia. Confirmada ausencia de workers/modelos
previos activos antes de despachar. KTH8online pendiente autorización de ruta;
no se reintenta. No manuscrito/commits/push ni papers adelantados.

## Seguimiento Soil, 01-11, 17:01 UTC

Primera condición Soil/ResMLP/42/f0 cerró calidad/replay:1140predicciones,
CACHED_HEAD_PREDICTIONS_REPLAYED y hash de estado coincidente. Medición online
de esa condición activa PID19692; calidad del siguiente fold PID19687. Un único
benchmark GPU y un ajuste CPU2hilos, sin fallos nuevos ni cambios de receta.
Cobertura física completa todavía56/94,280920llamadas primarias más9400DTD
adicionales; no se cuenta Soil hasta cerrar y auditar llamadas. KTH online
mantiene retención y solicitud explícita de autorización sin respuesta recibida.

## Primeros cierres físicos Soil, 01-11, 17:16 UTC

Soil/ResMLP/42/folds0y1 cerraron online y auditoría,1140llamadas/228imágenes
por condición, cinco métodos. Ambos ONLINE_CALL_RECORDS_REAGGREGATED y hashes
de estados actuales coincidentes; no mezcla con F1 anterior. Nueva representación
enmendada, originales intactos. Dos de15ResMLP y cero de15SVM; no media completa.
Cobertura única58/94,283200llamadas primarias auditadas más9400adicionalDTD,
total292600observaciones auditadas. Mediciónfold2 PID20219, calidadfold3 PID20160,
unGPU y CPU2hilos; no errores nuevos ni repeticiones. KTH online retenido.

## Seguimiento Soil, 01-11, 17:31 UTC

Soil/ResMLP/42/fold2 online y auditoría completos1140llamadas/228imágenes;
ONLINE_CALL_RECORDS_REAGGREGATED y hash del estado verificado. Tres de15
ResMLP completos, sin media Soil completa. Cobertura única59/94,284340llamadas
primarias más9400adicionalDTD=293740observaciones completas auditadas.
Onlinefold3 PID20622; calidadResMLP/123/f0 PID20634; workers19563/19573 vivos,
unbenchmarkGPU, sin nuevos fallos/retries. KTH online sin autorización nueva.

## Seguimiento Soil, 01-11, 17:46 UTC

Soil/ResMLP/42/folds3y4 online y auditoría completos,1140llamadas/228imágenes
cada uno; hash de estado y ONLINE_CALL_RECORDS_REAGGREGATED verificados.
Cinco de15ResMLP completos (seed42 cerrada), no media completa de tres semillas.
Cobertura única61/94,286620llamadas primarias más9400adicionalDTD=296020
observaciones auditadas. GPUResMLP/123/f0 PID21163, CPUcalidad123/f3 PID21260;
workers vivos, unbenchmarkGPU y CPU2hilos. Sin nuevos errores/retries ni permiso
recibido para redespacho KTH. No se modifica manuscrito ni protocolos activos.

## Seguimiento Soil, 01-11, 18:01 UTC

Soil/ResMLP/123/fold0 online y auditoría completos,1140llamadas. Revalidadas
todas las auditorías online Soil cerradas contra hashes de sus estados:6de30
condiciones Soil,6840llamadas. Cobertura única62/94,287760llamadas primarias
más9400adicionalDTD=297160observaciones auditadas. No media Soil completa.
GPU123/f1 PID21559 y CPUcalidad2026/f0 PID21680; unbenchmarkGPU, CPU2hilos,
workers vivos, sin nuevos fallos/reintentos. KTH online mantiene retención.

## Seguimiento Soil, 01-11, 18:16 UTC

Soil/ResMLP/123/folds1y2 cerrados online/auditoría; revalidadas todas las8
auditorías Soil y hashes de estado:9125llamadas. Fold123/f1 tiene229imágenes
(1145llamadas) según partición fijada; no forzar228ni omitir filas. Cobertura
única64/94,290045llamadas primarias más9400DTDadicional=299445observaciones
auditadas. No media completa:8de15ResMLP,0de15SVM. Online123/f3 PID22244 y
calidad2026/f2 PID22276, unGPU y CPU2hilos; sin nuevos errores/retries.
KTH online sigue retenido por permiso de redespacho pendiente.

## Seguimiento Soil, 01-11, 18:31 UTC

Soil/ResMLP/123/fold3 cerró online/auditoría:1135llamadas/227imágenes según
partición fijada. Verificados hashes de todas las9auditorías Soil,10260llamadas.
Cobertura única65/94,291180llamadas primarias más9400adicionalDTD=300580
observaciones completas auditadas. Nueve de15ResMLP, cero de15SVM: sin media
Soil completa. Online123/f4 PID22828, calidad2026/f4 PID22937, workersvivos,
unbenchmarkGPU y CPU2hilos, sin nuevos fallos ni reintentos. KTH retenido.

## Seguimiento Soil, 01-11, 18:46 UTC

Soil/ResMLP/123/fold4 y2026/fold0 cerrados online/auditoría; todas11auditorías
Soil revalidadas y hashes de estados coincidentes,12540llamadas. Cobertura
única67/94,293460llamadas primarias más9400adicionalDTD=302860observaciones
completas auditadas. Once de15ResMLP y0de15SVM, sin media completa Soil.
GPU2026/f1 PID23763, CPU ya calidadSVM/123/f1 PID23739; workers19563/19573
vivos, unbenchmarkGPU y CPU2hilos, sin nuevos errores/retries. KTH retenido.

## Cierre calidad Soil y seguimiento online, 01-11, 19:01 UTC

Las30condiciones Soil (15SVM/15ResMLP) completaron calidad y replay:34200
predicciones, todas CACHED_HEAD_PREDICTIONS_REPLAYED y hashes source_status
coincidentes. WorkerCPU19573 terminó normalmente; sin fits activos. No se
convierten cifras de caché en F1 online ni se adjuntan tiempos de otra ejecución.

OnlineResMLP/2026/f1 terminó auditado; todas12auditorías Soil verificadas,
13680llamadas. Cobertura única68/94,294600llamadas primarias más9400DTD
adicional=304000observaciones auditadas. GPU19563 mide2026/f2 PID24541,
un solo benchmark; faltan3ResMLP y15SVM online. Sin nuevos fallos/retries;
KTH8online siguen retenidas hasta autorización pendiente. Sin manuscrito/papers.

## Seguimiento Soil, 01-11, 19:16 UTC

OnlineResMLP/2026/folds2y3 cerrados auditados; revalidadas14auditorías Soil,
15960llamadas y hashes de estado coincidentes. Cobertura única70/94,
296880primarias+9400adicionalDTD=306280observaciones auditadas. ResMLP14/15,
SVM0/15, no media completa todavía. GPU19563 mide2026/f4 PID26023, único
benchmark; CPU terminado. Sin estados nuevos requires_review/retries en esta
cola. KTH8online siguen pendientes de autorización; no se despachan por heartbeat.

## Cierre Soil/ResMLP online completo, 01-11, 19:31 UTC

Quince de quince condiciones auditadas,17100llamadas,3420por método; verificados
estados finales, hashes source_status/calls/summary y cobertura por condición.
Resumen nuevo con15fuentes:soil_pending_v1/summary_Soil_resmlp_online_v1/summary.json.
F1 macro medio de15splits y ms media de todas las llamadas de cada método:
adaptativa .866818251/48,326247; Completa22 .867274981/1823,245423;
diversidad .875789935/208,142231; tómbola .874182280/183,521899;
Top4 .863293313/78,208257. Medianas/p95 también guardados desde llamadas crudas.
Adaptativa tiene mayor F1 queTop4, pero menor queCompleta/diversidad/tómbola.
No inferir significación ni equivalencia: seeds/folds no son datasets
independientes, hardware compartido, representación DeiT enmendada explícita.
F1 y tiempos provienen de las mismas llamadas; no histórico mezclado.

Cobertura única71/94,298020llamadas primarias más9400DTDadicional=307420
observaciones auditadas. Soil/SVM primera condición42/f0 activaPID27145,
único benchmarkGPU, worker19563; CPU terminó. SVM0/15cerradas, no media completa
de ambos heads. KTH8online siguen retenidas hasta autorización, sin retries.

## Redespacho KTH explícitamente autorizado, 01-11, 19:36 UTC

Respuesta recibida: «Sí, despachar las ocho mediciones con la ruta corregida».
Registro AUTORIZACION_REDESPACHO_KTH_2026-11-01.md. Preparador nuevo y tests:
17passed (alias/calculocronómetroAST, conservación de inputs y guardas de cola).
Inicialmente falló un índice incorrecto en el propio test; corregido el test
y pasada suite antes de preparar/lanzar. Ningún experimento fue reintentado
por ese test ni cambió la receta científica.

Cola kth_alias_redispatch_v1, manifiesto SHA256
01fb79fc89bf1b15dc87fd70b76a9b9312d1cf44ae6341659cb4dae2d4b508d5.
Ocho condiciones online con mismos heads, decisiones congeladas, particiones,
normalización/semillas/repeat1. Nuevas rutas de salida y único cambio del ejecutor:
alias del archivo DeiT; benchmark original y8fallos previos intactos. Guardados
hashes de calidad completa, configs, fuente nueva/original, paquetes y binding.
Worker28523, sesión5188, inició19:36:35UTC y espera lockGPU de Soil; no inicia
segundo benchmark. Sin fits nuevos ni selección por test. Nuevos fallos se
retienen sin retry automático; ventana10h no interrumpe tarea iniciada.

Revalidadas16auditorías Soil:18240llamadas (15ResMLP y primeraSVM42/f0).
Cobertura única72/94,299160primarias+9400DTDadicional=308560observaciones
auditadas. Soil/SVM42/f1 sigue activo; KTH en espera no suma cobertura. Medias
KTH al cerrar4porhead; reservas históricas/físicas preservadas, sin papers
adelantados ni modificaciones de manuscrito/commits/push.

## Seguimiento y autonomía rutinaria, 01-11, 19:46 UTC

El usuario pidió decidir autónomamente opciones rutinarias; se conserva esa
preferencia sin ampliar permisos científicos ni reintentos ante fallos nuevos.
Soil/SVM42/f1 online/auditoría completo. Revalidadas17auditorías Soil,19380
llamadas, hashes source_status coincidentes. Cobertura única73/94,300300
llamadas primarias+9400DTDadicional=309700observaciones auditadas. ResMLP15/15,
SVM2/15: no media completa de SVM. Soil/SVM42/f2 PID29046 activo, único
benchmarkGPU; workerKTH28523 espera lock compartido. Sin nuevos fallos ni retry.

## Seguimiento Soil, 01-11, 20:01 UTC

Soil/SVM42/folds2y3 cerraron online/auditoría. Revalidadas19auditorías Soil,
21660llamadas y hashes coincidentes. Cobertura única75/94,302580llamadas
primarias+9400DTDadicional=311980observaciones completas auditadas. SVM4/15,
ResMLP15/15, sin media completa de SVM. OnlineSVM42/f4 PID30340, worker19563;
KTH28523 espera lock global, sin otro benchmark ni estados nuevos de fallo.
No reintentos, cambios científicos, manuscrito ni papers adelantados.

## Seguimiento Soil, 01-11, 20:16 UTC

Soil/SVM42/fold4 cerró online/auditoría; todas20auditorías Soil revalidadas,
22800llamadas, hashes de estados coincidentes. Cobertura única76/94,303720
llamadas primarias+9400DTDadicional=313120observaciones auditadas. SVM5/15,
solo semilla42 completa, no media completa de15condiciones. ResMLP15/15.
OnlineSVM123/f0 PID31572, worker19563; KTH28523 espera mismo lock global.
UnbenchmarkGPU, sin nuevos fallos/retries ni alteraciones metodológicas.

## Seguimiento Soil, 01-11, 20:31 UTC

Soil/SVM123/folds0y1 cerrados online/auditoría; todas22auditorías Soil y hashes
de estados coincidentes,25085llamadas (fold1con229imágenes, sin omitir filas).
Cobertura única78/94,306005llamadas primarias+9400DTDadicional=315405
observaciones completas auditadas. SVM7/15, ResMLP15/15, sin media completa
de SVM. OnlineSVM123/f2 PID32957, worker19563; KTH28523 espera lock global.
Un solo benchmark, sin nuevos errores, repeticiones ni cambios al protocolo.

## Seguimiento Soil, 01-11, 20:46 UTC

Soil/SVM123/folds2y3 online/auditoría completos; revalidadas24auditorías Soil,
27360llamadas y hashes de estados coincidentes. Fold3con227imágenes conserva
partición fijada. Cobertura única80/94,308280primarias+9400DTDadicional=317680
observaciones completas auditadas. SVM9/15, ResMLP15/15; todavía sin media
SVM completa. OnlineSVM123/f4 PID34432, worker19563; KTH28523 espera lock.
UnbenchmarkGPU, sin nuevos fallos/retries; manuscrito y protocolos intactos.

## Seguimiento Soil, 01-11, 21:01 UTC

Soil/SVM123/fold4 online/auditoría completo; todas25auditorías Soil verificadas,
28500llamadas y hashes de estado coincidentes. Cobertura única81/94,309420
llamadas primarias+9400DTDadicional=318820observaciones auditadas. SVM10/15,
ResMLP15/15; no media SVM completa. GPU mideSVM2026/f0 PID35830, worker19563;
KTH28523 espera lock compartido. Sin nuevos errores ni repeticiones automáticas.

## Seguimiento Soil, 01-11, 21:16 UTC

Soil/SVM2026/folds0y1 cerrados online/auditoría; revalidadas27auditorías Soil,
30780llamadas, hashes de estado coincidentes. Cobertura única83/94,311700
primarias+9400DTDadicional=321100observaciones completas auditadas. SVM12/15,
ResMLP15/15: faltan3SVM, sin media completa aún. OnlineSVM2026/f2 PID37412,
worker19563; KTH28523 espera lockGPU. Unbenchmark, sin nuevos fallos/retries.

## Seguimiento Soil, 01-11, 21:31 UTC

Soil/SVM2026/folds2y3 cerrados online/auditoría;29auditorías Soil y hashes de
estado revalidados,33060llamadas. Cobertura única85/94,313980primarias+
9400DTDadicional=323380observaciones completas auditadas. SVM14/15, última
condición2026/f4 PID39053 activa, sin media SVM completa todavía. KTH28523
espera lock global; un solo benchmark, sin nuevos errores ni repeticiones.

## Cierre Soil completo y comienzo KTH, 01-11, 21:46 UTC

Soil/SVM15/15cerradas,17100llamadas; junto aResMLP15/15, Soil30/30y34200
llamadas online auditadas. Verificados todos los hashes de estados/auditorías,
cobertura por condición, calls y summaries. SVMconsolidado nuevo con15fuentes:
soil_pending_v1/summary_Soil_svm_online_v1/summary.json; ResMLP ya consolidado.

SVM media F1 macro de15splits / ms media de todas las llamadas por método:
adaptativa .872540331/38,482833; Completa22 .879187619/1651,187988;
diversidad .876987107/204,911164; tómbola .866406809/200,331897;
Top4 .859404021/70,984756.3420llamadas por método, mediana/p95 guardados.
Adaptativa mayor F1 queTop4/tómbola, menor queCompleta/diversidad; no prueba
de superioridad estadística. No mezclar histórico, ni tratar folds/seeds como
datasets independientes. CPU terminó, sin nuevos fits ni cambios por test.

Cobertura física única86/94,315120llamadas primarias más9400DTDadicional=
324520observaciones auditadas. FMD,CUReT,DTD,Outex,Soil tienen cobertura de
ambos heads/cinco métodos; persiste reserva física de originalDTD/SVMofficial7.

WorkerSoil19563 all_tasks_terminal y sin proceso. KTHworker28523 tomó lock,
primera ResMLPofficial1 PID40652 ejecutando550/5940llamadas; la corrección de
alias superó preflight y entró a medición. Único benchmarkGPU, no nuevos fallos,
sin contar parcialKTH como terminado. Faltan8condiciones online KTH, mantener
reserva de comparación histórica; papers/manuscrito aún fuera de esta etapa.

## Primera condición física KTH auditada, 01-11, 22:46 UTC

KTH/ResMLPofficial1 cerró5940llamadas/1188imágenes/cinco métodos, auditoría
ONLINE_CALL_RECORDS_REAGGREGATED y hash de estado actual coincidente. Nueva
cola kth_alias_redispatch_v1; misma calidad congelada, alias corregido, F1/ms
de las mismas llamadas, fallos anteriores intactos. No media completa KTH.
Cobertura única87/94,321060llamadas primarias+9400DTDadicional=330460
observaciones completas auditadas. Falta3ResMLP y4SVM online. Official2activo
PID42729, worker28523, único benchmarkGPU. Sin nuevos fallos/retries, reservas
históricas/físicas intactas y papers/manuscrito fuera de esta etapa.

## Seguimiento KTH, 01-11, 23:31 UTC

KTH/ResMLPofficial2 online y auditoría completos5940llamadas. Revalidadas
dos auditorías KTH y hashes de estados:11880llamadas. Cobertura única88/94,
327000primarias+9400DTDadicional=336400observaciones auditadas. KTHResMLP2/4,
SVM0/4: no media completa KTH. Official3 PID43468 activo, worker28523;
único benchmarkGPU, sin nuevos fallos ni reintentos. Mantener reservas previas.

## Cierre KTH/ResMLP online completo, 02-11, 01:16 UTC

Cuatro de cuatro condiciones online auditadas,23760llamadas,4752por método;
verificados estados, hashes source_status/calls/summary y5940llamadas por split.
Resumen nuevo:kth_alias_redispatch_v1/summary_KTH_resmlp_online_v1/summary.json.
Media F1 macro de cuatro splits / ms media de todas las llamadas por método:
adaptativa .939089669/32,162136; Completa22 .946102030/1626,698818;
diversidad .955620731/366,384001; tómbola .954288686/354,334936;
Top4 .952320017/260,112276. Medianas/p95 guardados desde llamadas crudas.
Adaptativa inferior en F1 a todos los controles con ResMLP; no ajustar por
test ni ocultar esa pérdida. Diferencias descriptivas, no prueba estadística
de equivalencia/superioridad, ni equivalencia de cascada histórica/aislamiento.

Cobertura única90/94,338880llamadas primarias+9400DTDadicional=348280
observaciones auditadas. Faltan cuatroKTH/SVM; official1 PID45443 activo,
worker28523 y único benchmarkGPU. Sin nuevos fallos/retries ni cambios de
receta. Guardar reservas físicas/históricas; no declarar panel94cerrado aún.

## Seguimiento KTH, 02-11, 02:16 UTC

KTH/SVMofficial1 online y auditoría cerrados5940llamadas; revalidadas cinco
auditorías KTH y hashes source_status,29700llamadas. Cobertura única91/94,
344820primarias+9400DTDadicional=354220observaciones completas auditadas.
KTHSVM1/4, ResMLP4/4; sin media completa SVM. Official2 PID46585 activo,
worker28523, único benchmarkGPU; sin nuevos fallos/retries ni cambios científicos.

## Seguimiento KTH, 02-11, 03:01 UTC

KTH/SVMofficial2 online/auditoría cerrados5940llamadas; revalidadas seis
auditorías KTH y hashes source_status,35640llamadas. Cobertura única92/94,
350760primarias+9400DTDadicional=360160observaciones completas auditadas.
KTHSVM2/4, ResMLP4/4, sin media SVM completa. Official3 PID47678 activo,
worker28523, único benchmarkGPU. Sin nuevos fallos/retries ni alteraciones.

## Seguimiento KTH y preparación de cierre consolidado, 02-11, 04:01 UTC

KTH/SVMofficial3 online/auditoría cerrados5940llamadas; sieteKTHauditadas,
41580llamadas, hashes source_status coincidentes. Cobertura única93/94,
356700primarias+9400DTDadicional=366100observaciones completas auditadas.
Última SVMofficial4 PID49003 activa, worker28523 y único benchmarkGPU.
No media completa de SVM ni panel94cerrado mientras esté activa.

Consolidador nuevo scripts/consolidate_overnight_online_panel.py probado con
5tests. Reagregación explícita de las93condiciones ya cerradas:0errores al
verificar linaje por manifiestos, identidades, cobertura, hashes de estados/
auditorías/configs/calidad/heads/decisiones y cálculo deF1/medias desde llamadas.
Registro nuevo consolidation_preflight_93_v1.json: full_panel_complete=false,
falta KTHTIPS2b_svm_s42_f3. No modelos ni fits ejecutados. Tests validan rechazo
de faltantes, duplicados, conteos incorrectos y VisTex, yF1 independiente.
La preparación no publica medias completas ni certifica hardware/precedencia
histórica. AdicionalDTD permanecerá separado del94primario; todas las reservas
seguirán en coverage.json al cierre. Papers diferidos, manuscrito intacto.

## Cierre consolidado definitivo de cobertura, 02-11, 04:46 UTC

Última KTH/SVMofficial4 completó benchmark y auditoría a las04:44:12.874UTC.
Worker28523 finalizado normalmente; sin benchmarks activos al cierre.
Estado online SHA256:fcd796676d87c8a039836f82fcf350ae08f5e8e8f9ae47d4669088ae2693d6e6.
Auditoría SHA256:194d7cdafcf0c9d80ef1375233ed3bf850142a111e49d32f0ca3e8d93f995021.

Consolidador scripts/consolidate_overnight_online_panel.py:5tests pasan y
ejecución final exit0. Artefacto nuevo completo:
results/analysis/blocker_resolution_20261101/full_panel_online_v1/.
Estado ALL_94_ONLINE_CONDITIONS_REAGGREGATED_WITH_RESERVES:94/94condiciones
únicas,47por head; seis datasets×dos clasificadores×cinco métodos=60resúmenes.
470filas condición-método,362640llamadas primarias. AdicionalDTD9400llamadas
en CSV separado, no95.ªcondición ni sustituto de la medición original.
Total372040llamadas auditadas, excluidos intentos fallidos y parciales.

Reagregación desde llamadas crudas verifica identidad, cobertura de imágenes,
repetición1, predicciones, F1macro, tiempos finitos positivos, hashes de estados,
auditorías, calidad, configs, heads y decisiones congeladas. No mezcla de F1
histórico y tiempos nuevos. Archivos condition_summary.csv,dataset_summary.csv,
additional_DTD_observation.csv,coverage.json y provenance.json conservan linaje.
SHA256 coverage.json:2789666cea7bbce1cd893f24eb0886fd1bd45f0041ab5aa14b198e4753b4e365.
SHA256 dataset_summary.csv:d60b15b1046cfb82b052d1b370900c07d2ddac3d69537c0557fd5e6ae4968846.
SHA256 provenance.json:51fdacdcdf3b7cf5b50f35b6c36e656d98989b5d1fcd165075031cf617fd95f8.

KTH/SVM4/4completo,23760llamadas: F1medio/msmedios por método:
Adaptive .938996502/30.953840; Completa22 .959928044/1579.083710;
Diversidad .954307344/367.460638; Tómbola .954006273/345.556581;
Top4 .954391233/260.379058. Resultados descriptivos de llamadas online;
no convertir F1cache previo en sustituto de este F1.

Reservas explícitas vigentes: DTD/SVMofficial7 original con episodio físico
extremo permanece primario; observación adicional separada. Outex/Soil tienen
representación nueva autorizada. KTH nuevo reconciliado no demuestra equivalencia
con cascada histórica. Hardware compartido, una repetición por imagen y
folds/semillas no son datasets independientes. Sin inferencia global ni afirmación
de superioridad universal. Cobertura cerrada no equivale a reservas resueltas.

Próximo alcance: preparación de comparadores externos, sin nuevas corridas hasta
receta ejecutable aprobada. El plan27-10 es preparación; piloto Neshov28-10 ya
realizado solo cubre desarrollo FMD, no expansión ni latencia online. No repetir
piloto ni inventar presupuesto/protocolo. No cambios al manuscrito, commits,
push, manifiesto original ni protocolo congelado. Monitoreo silencioso si no
hay cambio accionable; este cierre sustituye los cortes parciales anteriores.

## Continuación técnica post-panel, 02-11

Plan vigente adicional: docs/fsc_tex/PLAN_CONTINUACION_POST_PANEL_2026-11-02.md.
Preparado adaptador Neshov archivo-a-clase en src/neshov_online_adapter.py,
separado de benchmarks y protocolos congelados.19tests pasan:7casos sintéticos
del adaptador y12existentes. Sin entrenamiento, extracción de imágenes reales,
benchmarkGPU ni evaluación externa en esta etapa. Carga offline estricta y hashes
exigidos, FP32, backbone en dispositivo declarado y MLP en CPU, sin caché/retries.
El tiempo y predicción se obtienen en una misma llamada, no se mezcla F1piloto
con tiempos nuevos. Falta validar fidelidad real bajo protocolo externo fijado;
tests no equivalen a reproducción del paper ni a nueva cobertura experimental.
Panel94 y sus reservas permanecen intactos. No manuscrito/commits/push.

## Preflight externo Neshov/FMD, 02-11

scripts/prepare_neshov_fmd_external.py completó exit0 sin cargar modelos.
15condiciones únicas congeladas en
results/analysis/neshov_fmd_external_preflight_20261102_v1/manifest.json:
concordancia entre índices de SVM/ResMLP de30fuentes,800fit/200test,
sin fuga de grupos,10clases y cobertura de1000filas test por cada semilla.
Hashes de1000imágenes y checkpoint offline verificados.3000llamadas previstas,
0nuevas predicciones/latencias.14tests de preparación/adaptador pasan.
No entrenamientos ni mediciones despachados; runner externo aún pendiente.
Priorizar papers de concatenación/fusión aportados por el autor; conservar
etiquetas de adaptación y antecedentes de otras tareas. Panel94 intacto.

## Despacho Neshov/FMD externo autorizado, 02-11, 10:43 UTC

Tras pedido de autonomía durante ausencia aproximada12h, runner externo y
preparador de cola pasan32tests con infraestructura existente. Fuentes/paquetes
sellados y verificados. Cola nueva Neshov: ruta exacta
results/analysis/neshov_fmd_external_queue_20261102_v1/manifest.json,
SHA2564f43c3ba8b812987d52dad2d25b7d25f7a8d7e283200e77bf5932fba402a2a36.
WorkerGPU54789, sesión48201; primer proceso extracción54797 activo al corte.
15condiciones, cada una extracción→fit100épocas→online→auditoría; ventana12h.
Primer cierre auditado desbloquea otras14.0condiciones externas completas al
inicio: no anunciar nuevoF1 ni latencia por iniciar un proceso. Toda etapa bajo
lockglobalGPU, CPU2hilos, offline, sin retries ni cambios al panel94.
Heartbeat15min actualizado para continuar réplicas de papers y revisar cola.
No promesa de terminar todo en12h; sin manuscrito/commits/push.

### Fallo científico de control Neshov, 10:43:59UTC

Extracción800fit finalizó, pero control batch1/batch8 no pasó: errores absolutos
.003938198089599609 y .005510807037353516, umbral.0001 en filasfit0/999.
Evidencia parity.json/status.json y stage_0.log del primer job preservada.
Primero requires_review,14dependientes blocked, worker all_tasks_terminal.
0heads entrenadas,0llamadas externas,0F1/latencia nuevos. No se relaja umbral,
repite automáticamente ni se omiten casos. No es timeout ni error de preparación.

Continúa trabajo independiente autorizado de otros papers mediante heartbeat.
Inventario nuevo reference_paper_inventory_20261102_v1:11PDFlocales con hashes,
sin descargas/uploads ni afirmación de lectura/replicación.3PDFnofiguraban en
README y quedan identificados para fichas completas. Panel94 y manuscrito intactos.

## Auditoría de recetas y componentes independientes, 02-11

Sin relanzarNeshov: lectura de métodos Compactcolor–texture yAsTexNet, evidencias
en paper_recipe_audit_20261102_v1/RECIPE_READINESS.md, textos derivados y sidecars
PDF. PreflightestructuralPASS7/30páginas usando runtime documental empaquetado;
no se alteró entorno experimental ni PDFs. Identificados componentes y parámetros
necesarios para réplica, no se asumieron equivalencias con bloques locales.
Operadores aisladosAsTexNet implementados en astexnet_formula_components.py,
13tests pasan. No CNN/MLP completo ni entrenamiento/medición nuevos. Estado
full_recipe_pending, no contar como paper replicado. Continuar otras fichas y
verificación de implementaciones oficiales sin descargas grandes/contactos.

## HyTexNet y DeepLumina: avance independiente, 02-11

PDFs19/16páginas pasan comprobaciónestructural; leídos pasajes de método,
protocolo y tablas, con render visual deHyTexNetecuaciones1–6. Detalles en
paper_recipe_audit_20261102_v1/RECIPE_READINESS.md. DescriptorHyTex514 y cabeza
de fusión implementados,9tests nuevos/22conAsTexNet pasan; no pesos entrenados
ni métricas nuevas. Se fijó protocoloHyTexADAPTADO, con defaults locales explícitos
y checkpointoffline hashverificado, para poder comparar sistema completo sin
afirmar réplica exacta no sustentada. Runner/adaptador completo es siguientepaso.
DeepLumina requierefc1000yECOCMATLAB, no sustituir por ResNetGAP/SVC local.
Neshovrequires_review sinretry;0benchmarks activos, panel94 intacto.

## HyTexNet adaptado: ejecución nueva iniciada, 02-11, 11:21UTC

35tests pertinentes pasan de representación/adaptadoroffline/head/runner/auditoría/
dispatcher. Cola nueva hytex_fmd_external_queue_20261102_v1,15condicionesFMD,
manifiestoSHA25694f40dc297e3516abad630a7ad7c1c24622d7cf005dee0305d842b748f18aa75.
Fuentes y paquetes revalidados antes de despacho;1000imágenes y mismos índices.
Worker56637, sesión18682, inicio11:21:27UTC, procesoextract56645 en primera
FMD42/f0,451/800fit al corte. Único lockglobalGPU,2hilosCPU, offline.0auditorías
externas completas al iniciar: ningúnF1/ms anunciado todavía. Todos los resultados
deben rotularseHyTexNetadaptado, no reproducción exacta. Primera auditoría habilita
14restantes. Neshovfallido y panel94 preservados, no manuscrito/commits/push.

Primer cierreHyTexFMD42/f0 auditado200llamadas,fit100épocas, consistencia de
vectores1538 error0/0en las2filas fijadas. F1macro.6786837642161999 ymedia
28.220804215ms de las mismas llamadas;accuracy.68,mediana22.5302675ms,
p9559.6321425ms. No mediaFMD ni réplica de porcentajes delpaper. Fuente
hytex_fmd_external_queue_20261102_v1/jobs/HyTex_FMD_s42_f0/audit/summary.json,
onlineestadoSHA256ef155e7f303ecce59c8320e5b39deb42dd239814bec91f89ff5e776a12efdb4a.
Cobertura1/15,200/3000llamadas; siguienteFMD42/f1extractPID56714, worker56637.

## Cierre completo HyTexNetADAPTADO/FMD, 02-11

15condiciones terminadas y auditadas,3000llamadas, worker56637all_tasks_terminal.
Consolidador nuevo7tests pasan, revalida60recibos y rawcalls/cadena de fuentes.
Artefacto results/analysis/hytex_fmd_external_summary_20261102_v1/ con15métricas,
150comparaciones por condición y10resúmenes contra ambosheads×cincométodos.
F1macro medio.7414168220822994,media31.180759932ms, calidad/tiempo mismasllamadas.
SummarySHA25643ca6a521b0a03cb0c701d6a587398f5e4d8cac13d78d881b926991184aa9dc8.
Nuestro adaptativoSVM.977600499/38.629833773ms yResMLP.975969620/36.354072400ms:
mayorF1pero mayortiempo queestaadaptación; no dominancia calidad-latencia.
Comparación descriptiva con momentos/hardwarecompartido, no inferencia global
ni reproducción de cifraspublicadas. UNdatasetexterno, no seisdatasets.
SeguirCUReT primero conpreflight/protocolo deextensión y mismo método, sin
repetirFMD niNeshov fallido, sin editar fuentes históricas/manuscrito/commits/push.

## Extensión HyTexNetADAPTADO/CUReT iniciada, 02-11, 11:51UTC

Protocolo nuevo PROTOCOLO_HYTEX_EXTENSION_CURET_2026-11-02.md y preparador con
11tests pasan junto a contratos de runner.2direcciones complementarias,
61clases,5612imágenes/labels/particiones verificadas contra4fuenteslocales,
sin cambio de parámetros ni selección porFMD. Cola nueva
hytex_curet_external_queue_20261102_v1, manifiestoSHA256
99dc75626ffd268e4a0c5b60df60133b971a974e0a16afbbde3e591d943bfbd5.
Worker57833/sesión37797, primerextract57835,2601/2806fit al corte,0auditorías
CUReT completas.5612llamadas externas planificadas, no se presentan como medidas.
FMD15cerrado yNeshovfallido preservados. Sin otrobenchmark/fit competidor.
Consolidador multidataset y tests nuevos preparados; validar y ejecutar solo
cuando cola esté terminal y no haya benchmark. No conteosFMDhardcodeados enCUReT.

Erratum de planificación: total47condiciones porUNsistema externo=36264llamadas,
no72528 (esa cifra duplicaba nuestros2heads). No cambia ningúncaso/imagen;
conteos ejecutadosFMD3000 yplanCUReT5612 sin cambios. No nuevas medias globales.

## Cierre CUReT adaptado y despacho DTD — 2026-11-02, 12:12 UTC

CUReT: 2/2 condiciones HyTexNet adaptado completas, 5.612 llamadas auditadas,
F1 macro medio 0,9830668097498063, media 32,41285442818959 ms de las mismas
llamadas. Ocho tests del consolidador y reagregación exit 0; resumen en
results/analysis/hytex_curet_external_summary_20261102_v1, SHA256 de summary.json
6f6716fed152aefcccb00978abe16de1f55bd970986e52ea0e71867ccf2bf571.
Comparaciones guardan ambos heads y cinco métodos, incluidas pérdidas.
No es reproducción de cifras del paper ni comparación aislada contemporánea.

DTD: cola de diez splits oficiales preparada con protocolo fijo; 18.800 llamadas
planificadas, ninguna condición completa al despacho. Verificadas fuentes,
paquetes y ausencia de otro worker. Manifest SHA256
cac2fd912d968efe40c2021718be55f9582f3c0249859002d270f6f8af940fac;
worker 58627 / sesión 92162, inicio 12:12:06 UTC, extract PID 58635.
Lock global GPU, CPU dos hilos, primera auditoría condiciona nueve splits.

Preparación inicial detenida antes de modelos por guard incorrecto de unión
de tests: oficiales cubren 5.546/5.640 filas; 94 nunca son test. Corregido
contra unión oficial, añadiendo control independiente del array completo de
etiquetas y hashes; diez tests pasan. Exclusiones históricas por grupos y
1.880 tests/split intactos. No retry de un experimento científico ni ajuste
de tolerancia/método. FMD y CUReT cerrados; Neshov sigue requiere revisión.

### DTD: gate inicial superado, 12:16 UTC

Primera condición HyTex_DTD_s42_f0 completa y auditada: 1.880 llamadas,
F1 0,6278908265695777, media 33,35765404893617 ms. Summary SHA256
77b69cbab8b2190c41782a451d4b644c5c34a9926c5df96e990e878e4c0c535d.
Cobertura 1/10, no agregado completo DTD. Segundo split extrayendo PID 58727
bajo mismo worker 58627; sin otro benchmark/fit. No cambiar fuentes selladas.

### DTD: 5/10 auditados — 12:31 UTC

Cinco condiciones completas (índices 0–4), 9.400 llamadas auditadas, sin
media completa DTD. Worker 58627 vivo; índice 5 extrayendo, PID 59046.
Se conservan fuentes, parámetros, particiones y cronómetro. No otro trabajo
de cálculo despachado; consolidación pospuesta hasta cobertura 10/10.

### DTD: 9/10 condiciones completas — 12:46 UTC

16.920 llamadas auditadas de índices 0–8; último split extrayendo, PID 59263,
worker 58627 vivo. No fallos observados ni otra cola despachada. Aún no hay
media DTD completa; esperar último online/audit antes de reagregar.

## DTD completo y fallo de contrato Outex — 13:04 UTC

DTD10/10,18.800 llamadas auditadas y reagregadas: F1 medio0,624152670943813,
media33,51206467335106ms. Resumen hytex_dtd_external_summary_20261102_v1,
SHA25682710cc3de9959567c124c03b6b8438bba1308b4fe51f16a47d189fe57553c57.
Nuestros adaptativos tienen mayorF1 pero mayorlatencia media; reserva DTD/SVM
conservada. Tres datasets HyTex adaptado completos, no réplica de cifraspaper.

Outex cola nueva685427d07448bd817194be484ff2f9276add2f848a3a4467997e87e71f902ae4,
worker59624 a13:04:06–08 UTC: requires_review por KeyError checkpoint_sha256
omitido en preflight, antes de cargar modelo/extracción/fit. Cero llamadas.
Doce tests de preparación/runner habían pasado pero no cubrían ese contrato.
Evidencias intactas en hytex_outex_external_queue_20261102_v1/tasks/
HyTex_Outex13Official1360_s42_f0/stage_0.log ystate.json. No retry automático
ni modificación de fuentes selladas. Continuar ramas Soil/KTH independientes.

## SoilOriginal en ejecución — 13:18 UTC

Preparación independiente, once tests pasan; contrato incluye checkpointSHA.
Verificadas30fuentes de ambos heads,1140imágenes/etiquetas canónicas,15splits
exactos y grupos. Tamaños externos228 salvo229/227 en dosfolds seed123,
3420llamadas planificadas, cero medias completas nuevas. Nueva cola
hytex_soil_external_queue_20261102_v1, manifestSHA256
3f86f18577d61c60fbfffe427c84bc86fae08e45bea7512bf062b12e37bd566e;
worker59897/sesión28801, inicio13:18:38 UTC,extract59899 con101/912fit al corte.
Único workerGPU,CPU2hilos; gate inicial habilitará14restantes. No retryOutex
niNeshov, no cambios de método/tolerancia/particiones por resultados anteriores.

## Soil completo — 13:34 UTC

15/15 a13:32:10 UTC,3420llamadas verificadas y reagregadas,exit0. F1 macro
medio0,787961802069162, media ponderada33,11436526491228ms. SummarySHA256
0cdb9d1881e5afa77f953d0865ea175120ce074b27e3f8cda27b20c6a08bcf17,
hytex_soil_external_summary_20261102_v1. Comparaciones completas sin omitir
pérdidas: adaptativoslocales mayorF1 pero mayortiempo. Hardwarecompartido,
fechas distintas y representaciónDeiT declarados. Cuatrodatasets cerrados,
no resultados completos de seis ni cifraspaperreproducidas.
KTHpreparador/protocolo independientes con12tests pasan; preflight hash de
4752imágenes en curso, sin llamadas KTH ni workers benchmark activos.

KTH preflight finalizó:4752imágenes verificadas y8fuentes concordantes. Cola
hytex_kth_external_queue_20261102_v1, SHA256
9fbd93da564f1da51c958f7a20a88afb3e6f4ca0163dd3b4e236b7c209995e17.
Despacho13:34:18 UTC,worker60664/sesión41162,extract60666 con251/3564fit al
corte. Cero condiciones completas,4752llamadas planificadas en4particiones.
Único workerGPU/CPU2hilos, sin cambios de método ni reserva históricaKTH.

## KTH completo — 13:46 UTC

4/4 a13:46:14 UTC,4752llamadas reagregadas exit0: F1medio0,8258556692598311,
media30,977041996843436ms. SummarySHA256
b988d2c5fc1768e4998c7bbba99ddbee9ac0573ca126987f28ca3d7446536edd.
Comparadores completos deambosheads×cincométodos, reservaKTHhistórica intacta.
HyTexadaptado tiene cinco datasets cerrados,46condiciones/35584llamadas;
Outexrequires_review0/1, faltan680, sin media global ni panel completo.
Estado y próximos pasos en paper_recipe_audit_20261102_v1/PANEL_STATUS_1346.md.
No workers propios activos al cierre. Continúa auditoría deotros papers,
sin reintentar fallos, descargas ni modificaciones almanuscrito.

## Auditoría de viabilidad TiO2023 — 14:07 UTC

Etapa documental terminada: método/Algoritmo1,páginas6/7 visualizadas,
preflightPASS17páginas yrepositorio delpaper verificado. Árbol API
a1749b45e8ef07bda8056453f0ca8e0ebfcc3cbb, códigoBiT/licencias inspeccionados
sin ejecución ni instalación. Solo componenteBiT verificado, no sistemaTiO;
ambigüedadesdimensionales/descriptores/clasificadores impiden despacho fiel.
Evidencia en MULTISCALE2023_READINESS.md. Cero nuevas llamadas/benchmarks,
HyTexcinco datasets cerrados intactos. Próxima auditoría CellNN2024.

## Fuente y checkpoint LBP+dCellNN auditados — 14:22 UTC

Auditoría documental yestática completada, CELLNN2024_READINESS.md. Repo
primario contienecheckpoint10.311bytes. Versiónactual89fc3d6 incompatible;
versiónautor299502cbb2243ecb78018110236871f261aa92b2 seleccionadacandidata,
20clavesmcellnn coinciden conpesosFP32finitos,cargasoloweights_onlyCPU.
SHA256checkpointaf56a7e939c93e4ec7b0e2c8af348bff756ac25267af4ca45b52005552fba65f.
Sin códigodelautor ejecutado,datosDRIVE descargados ni llamadas nuevas.
Próxima etapa:protocolo adaptado ytests/paridad sintética antes deentrenar.
HyTexcinco datasets cerrados yrequires_reviewOutex/Neshov permanecenintactos.

## Gate sintético LBP+dCellNN superado — 14:36 UTC

Protocolo adaptado previo a datosreales,bundleautor43.281bytesverificado,
port20pesosstrict y8tests pasan. Gate contra versiónautor299502c en gradiente,
checkerboard yrandom: errorfloat0,binarios/hist768 exactos ypreprocesoidéntico.
Evidencias cellnn_synthetic_parity_20261102_v1,statusSHA256
623308ebbda02ff562dd428e01e3dc91f5ba0be5a0d686de80c2d232b2cbe92e.
No datosreales extraídos,ningúnfit,nuevaspredicciones externas niF1 declarado.
Adapter/cronómetro/runnerpreflight siguen pendientes antes deldespachoFMD.

## LBP+dCellNN FMD despachado — 14:51 UTC

29tests pasan, incluida cadena4etapassintética,probabilidades/cronómetro y
preflight15splits. Rutacompleta archivo→contornos+6LBP768→MLP400→clase,
sinF1histórico. Protocolo,pesos,paquetes,headparams yparticionescongelados.
Cola cellnn_fmd_external_queue_20261102_v1,manifestSHA256
ac7453232802240c0ad0786e9474bfacee56117ac438eba1e570035357b50965.
Worker61901/sesión78440,inicio14:51:14 UTC,primerextract61909,101/800fit al
corte.0condicionescompletas,3000llamadasplanificadas. ÚnicoGPUworker,CPU2hilos,
primeraauditoría habilita14restantes. No editarfuentes ni repetirOutex/Neshov.
No mediasnuevas hasta cobertura15/15; adaptation,papercifras no reproducidas.

## LBP+dCellNN: falloJSON preservado y14nunca iniciados — 15:04 UTC

Primer42/f0requires_review:800features yparidadexacta completos,headguardado,
falloTypeErrornp.float32 alguardarhistorial,0llamadasonline. No repetir,
reanudar nireutilizarparcial. Corrección serializacióngeneralv2 probada:
36tests pasan,float32exacto,NaN/inf siguenrechazados, método sin cambios.
Solo14condiciones originalesblocked sin ningúnindiciodeejecución elegibles.

Colanueva cellnn_fmd_never_started_queue_20261102_v2,manifestSHA256
0b6baafdcc3c28dfa7cdeb00d799468173243f52ea71eccb42cd8dcaabba2046.
Worker62133/sesión58443 a15:04:51 UTC,extract62141,101/800fit,42/f1primero.
ÚnicoGPUworker/CPU2hilos;2800llamadas planificadas,cero completas aldespacho.
Máximo14/15FMD, no agregado completo. Fuente/intento42/f0 yOutex/Neshovintactos.

## CellNN14condicionesFMD auditadas yCUReTenmarcha — 15:20 UTC

14/14nuevas terminaron15:15:39;2800llamadas rawreverificadas conrecibos/hash.
FMDsigue14/15; solo14métricasindividuales y140comparaciones, sinmediadataset.
SummarySHA25628509cffa320bf36954e682789c6187b09580ea4e48c691bc2e144d9a90c7401,
cellnn_fmd_individual_audits_20261102_v1.42/f0parcialnoseusó nirepitió.
Once tests preparadorCUReT/antiagregadoparcial pasan. Protocoloextensiónnuevo.

CUReTCellNNpreflight completo5612imágenes/61clases,dosdireccionesexactas.
Colacellnn_curet_external_queue_20261102_v1,SHA256
535b8d7284320d97323715813d4cb23c8d8c14811ac628c5a11df8b01d7fd981.
Worker62902/sesión56267,15:20:34 UTC,extract62910,201/2806fit,ceroauditorías
CUReTnuevas aún. Mismo método/CPU2hilos/lockGPUglobal, sinotrobenchmark.

## CellNN CUReT cerrado;DTDactivo — 15:32 UTC

CUReT2/2 a15:27:02,5612llamadasauditadas/reagregadasexit0:F1medio
0,6933675335753301,media31,0245325753742ms. SummarySHA256
7990d0529d7dc3f69020de0776c9ffec9e1dad1bb5ac918a275aed103e64002f,
cellnn_curet_external_summary_20261102_v1. Comparacionescompletas de10pares,
fechasdistintas/hardwarecompartido;no cifraspaperreproducidas. FMD14/15sinmedia.
17tests preparación/auditorpasan,exclusionesDTDprobadas sinmodificarsellados.

ColanuevaCellNNDTD10particiones,5640imágeneshashverificadas,18800llamadas
planificadas. ManifestSHA256ba7d8171362bc546f23db04696c482619cc49684ff5ee5104fcc44ca12f87640.
Worker63192/sesión93243,inicio15:32:48 UTC,extract63200,201/3753fit,ceroaudits
completos. ÚnicoGPUworker/CPU2hilos,sincompetidores. ReservasDTD/KTHintactas.

### CellNN DTD4/10 — 15:46 UTC

7520llamadasauditadas deíndices0–3;índice4enextracciónPID63455,worker63192
vivo. Sinfallosnuevos/otrobenchmark. No mediaglobalDTD ni consolidaciónparcial.

### CellNN DTD8/10 — 16:01 UTC

15040llamadasauditadas deíndices0–7;índice8extractPID63673,2501/3751fit,
worker63192 vivo. Sin nuevosfallos niotrop rocesodecálculodespachado.
Continúa lamismacola, sin mediaDTDcompleta nicambios asellados.

## CellNN DTD cerrado yOutexactivo — 16:17 UTC

DTD10/10,18800llamadasreagregadasexit0:F1medio0,21618426956606546,
media31,519920409574468ms. SummarySHA256
51688085e4f884b421ef44b31d6a464dcb9a99b8cf6e2d650b177428c3158ac9.
F1bajo no disparaajustes;comparacionescompletas yreservaDTD/SVM preservadas.
24tests preparación/auditpasan;OutexCellNNnuevoverificó1360imágenes/68clases,
680train/680test. Noesreintento delmétodoHyTexfallido.
Colacellnn_outex_external_queue_20261102_v1,manifestSHA256
36087051177e2828e2c543ecacbd9da68aa230caca6c8d7a1b454e0f577a7a31,
worker63979/sesión69347,16:17:37 UTC,extract63987.680llamadasplanificadas,
ceroauditscompletos aldespacho,únicoGPUworker/CPU2hilos. FMD14/15sinmedia.

## CellNN Outex cerrado;Soilactivo — 16:32 UTC

Outex1/1,680llamadasrawreagregadasexit0:F1macro0,6355652763549626,
media29,910913772058827ms. SummarySHA256
fc051d62dcdf7b9967aa7b95d7e734a039b197b29f7b99ee3169d75af5c87497.
Diezcomparadorescompletos,sinconfundirconHyTexOutexrequires_review ni
reproducirporcentajespublicados. Reservas/fechashardwaredeclarados.
30testspreparación/auditpasan;Soilverificó1140imágenes/7clases/15particiones,
incluidos227/229tests,3420llamadasplanificadas.
Colacellnn_soil_external_queue_20261102_v1,manifestSHA256
f5ab7717bd58f6b4114db404935272b9482b989c4dece647c6be32e5c8965c14.
Worker64205/sesión58028,16:32:38 UTC,extract64213,1/912fit,ceroauditscompletos.
ÚnicoGPUworker/CPU2hilos;recetasinajustes. FMD14/15parcial,noretry42/f0.

## CellNN Soil cerrado;KTHactivo — 16:47 UTC

Soil15/15,3420llamadasrawreagregadasexit0:F1medio0,35496685877029893,
mediaponderada32,98486323157895ms. SummarySHA256
55e3c517f58651710b7a768dbf2b677cc6709bcc6ba1a526e840f5d94abcbee1.
Comparacionescompletas incluyenpérdidas;sinajustesmétodo.Hardware/fechasreservados.
37tests preparación/auditpasan;KTHpreflight4752imágenes,11clases,4folds,
3564train/1188test, separaciónmuestrasfísicas,reservahistóricaconservada.
Colacellnn_kth_external_queue_20261102_v1,manifestSHA256
de416b777cb38d3cd1d2d0c089bf304e3e32a329bc6045aedfc39a812775b970.
Worker64938/sesión49285,16:47:39 UTC,extract64941,201/3564fit,ceroauditsKTH
completos,únicoGPUworker/CPU2hilos. FMDCellNN14/15sinmedia;sinreintentos.

## Seguimiento KTH, corte de consulta de estado posterior

KTH/ResMLPofficial3 cerró online/auditoría5940llamadas. Revalidadas tres
auditorías KTH y hashes actuales,17820llamadas. Cobertura única89/94,
332940primarias+9400DTDadicional=342340observaciones completas auditadas.
Official4/índice3 activo PID44348,50/5940llamadas, worker28523, único benchmark.
Faltan1ResMLP y4SVM KTH online; no media ResMLP completa aún. Sin nuevos
fallos/retries, reservas físicas/históricas intactas. Cinco datasets completos;
no declarar cerrado panel de seis ni adelantar papers/manuscrito.

## Corte actual consolidado — reunión semanal 2026-11-02

El párrafo de seguimiento anterior es histórico; no describe el estado actual.
El panel propio está cerrado **94/94** en
`results/analysis/blocker_resolution_20261101/full_panel_online_v1`:
362640 llamadas primarias y 9400 observaciones DTD adicionales separadas.
No se repitió el panel ni se modificó el manuscrito.

LBP+dCellNN/KTH cerró 4/4 condiciones, 4752 llamadas auditadas; F1 medio
0.5750307215685133 y media 31.93726876094276 ms. Summary SHA256:
`5fd8fd876f7b696cfd099d6f5b06b9fd52eace5b38f05d2cc725e141959aec7c`.
Cobertura externa consolidada por dataset, no por panel completo, en
`results/analysis/external_adaptation_coverage_20261102_v1`:
HyTexNet adaptado y LBP+dCellNN adaptado tienen 46/47 condiciones y cinco
datasets completos cada uno. Faltan HyTexNet/Outex y CellNN/FMD 42/f0; Neshov
sigue en revisión por paridad científica. No se reintentaron estos casos.

En el chequeo de procesos de esta preparación no había workers experimentales
activos. Se preparó material de reunión en
`results/analysis/weekly_presentation_20261102_v1/deliverables`: PowerPoint de
nueve diapositivas, tablas editables y guion de 10 minutos. Paquete, geometría,
fuentes y reimportación pasan; nueve diapositivas inspeccionadas visualmente.
Conclusión descriptiva: el adaptativo reduce tiempo medio frente a Completa-22
en los doce pares dataset×cabeza, pero tiene pérdidas de F1 en varios casos.
Las adaptaciones externas no reproducen fielmente porcentajes publicados.
Sin afirmación de superioridad estadística, garantía de 60 ms ni media de
datasets incompletos. Próximas corridas conservan los bloqueos y reglas vigentes.

## Recuperaciones y seguimiento posterior

Ambas recuperaciones autorizadas terminaron y sus llamadas se auditaron. Los
dos sistemas ADAPTADOS tienen 47/47 condiciones y seis datasets completos cada
uno en `results/analysis/external_adaptation_coverage_20261102_v2`. HyTexNet
Outex: F1 0.8927455542401957, 29.04045229852941 ms, 680 llamadas. CellNN FMD:
F1 medio 0.2476506444806386, 29.655137729333337 ms, 3000 llamadas. No son las
cifras originales de los papers. Las fuentes y evidencias previas se conservan.

El diagnóstico Neshov reprodujo el fallo previo entre lotes y mostró repetición
exacta dentro de cada tamaño. Primer intento diagnóstico detenido antes de cargar
modelo por ruta de preflight; corrección de resolución y hash probada. Variante
prospectiva de extracción individual en
`results/analysis/neshov_fmd_batch1_queue_20261102_v1`, con fallo anterior
conservado, 24 pruebas y protocolo
`docs/fsc_tex/PROTOCOLO_NESHOV_BATCH1_CORREGIDO_2026-11-02.md`. Worker 5289,
primera condición FMD completada, cola restante en curso al corte. No presentar
medias completas hasta 15/15 ni confundir adaptación con protocolo original.

## Neshov FMD cerrado y 10 × 10 aproximado iniciado

Neshov batch1 adaptado: 15/15 condiciones, 3000 llamadas auditadas; macro-F1
0.94213042191491, media 16.890381723666664 ms. Resultados en
`results/analysis/neshov_fmd_batch1_external_summary_20261102_v1`.
No corresponde atribuirlos al protocolo 10×10 del artículo.

Preparada y despachada la aproximación 10×10 de FMD, worker 7356 y manifiesto
`results/analysis/neshov_paperlike_fmd_10x10_queue_20261102_v1/manifest.json`
SHA256 `8d9259af0faaf5691124247ac731020f910e73dfe78088bf74aed600e28f371f`.
Son 100 condiciones, 10000 llamadas planificadas, sin promedio parcial. Paper:
96.7 % accuracy; particiones, estado RNG y versiones exactas no verificados.
Extensión a cinco datasets preparada en
`results/analysis/neshov_batch1_extension_queue_20261102_v1` para despachar
después, sin concurrencia GPU. Protocolo y evidencias en el plan principal.
