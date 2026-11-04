# Plan nocturno: comparación de F1 y latencia individual

## Estado y autoridad

Solicitud del usuario: dejar programadas todas las tareas/corridas pendientes.
Seguimiento del mismo chat cada quince minutos:
`tesis-continuar-corridas-f1-y-latencia`, activo.
La programación no implica que cada dependencia esté resuelta ni que todo
terminará esta noche. Protocolo: `PROTOCOLO_COLA_NOCTURNA_2026-10-28.md`.

## Registro único

Manifiesto: `results/analysis/overnight_f1_latency_20261028/manifest.json`.
Contiene 94 condiciones (47 por clasificador), cinco métodos por condición,
las configuraciones, dependencias y salidas. Las 60 celdas agregadas de la tabla
final representan seis datasets × dos clasificadores × cinco métodos.

Hay cuatro etapas por condición: calidad en caché, replay de heads, medición
batch1 desde imágenes y auditoría de llamadas. Solo las dos últimas producen
F1/ms de la tabla física nueva. Las etapas no listas están registradas, no
contadas como corridas completadas.

## Orden operativo

1. Cerrar/auditar el piloto físico FMD/42/0 SVM ya activo.
2. Ejecutar su piloto equivalente ResMLP, ya en la secuencia dependiente.
3. Cerrar la cola externa ResMLP/42 de cinco pliegues y agregarla sin mezclar
   con los resultados físicos. SVM/42 ya está agregado.
4. Worker CPU: completar FMD/123 y FMD/2026 de ambos clasificadores; después
   Outex, Soil, CUReT y DTD, según disponibilidad y sin duplicar fuentes.
5. Worker GPU: condiciones FMD cuyos heads/replay estén listos. Un solo
   benchmark GPU. No interferir con la secuencia inicial ni compartir features.
6. Resolver adaptación/vínculos de extracción por dataset antes de habilitar
   la medición de los otros cinco. Auditar KTH antes de activar sus condiciones.
7. Consolidar tablas por condición y dataset con cobertura completa, F1 online,
   media/mediana/p95 de ms y diferencias descriptivas. No llenar faltantes con
   costos analíticos ni datos históricos de otro backend.
8. Solo después del panel local: retomar las réplicas de papers compatibles,
   con protocolo y condiciones equivalentes. Conservar el piloto Neshov previo
   como adaptación de desarrollo, no como prueba externa/latencia publicada.

## Qué debe hacer el seguimiento

Al corte de lanzamiento: el piloto físico SVM finalizó y su auditoría de
1.000 llamadas pasó. La secuencia está midiendo ResMLP. Calidad FMD/42 está
completa y agregada para ambos clasificadores; no repetir esas diez condiciones.
El informe nocturno inicial contiene valores y fuentes; no extrapolar el
piloto físico de un pliegue a la media de cinco pliegues en caché.

Leer antes de actuar este plan, manifiesto, estados de workers, estados por job
y logs. Confirmar procesos vivos; no reiniciar un job solo por no ver salida.
Las colas activas están en `results/exploratory/local_external_followup_20261028/`
y `results/exploratory/local_batch1_followup_20261028/`.

Workers nuevos: `worker_quality.json`, `worker_online.json`; estados de cada
condición en `jobs/<id>/{quality,online}_state.json`. Un marcador requiere revisión
no autoriza reintentar. Si el worker murió, conservar el estado y diagnosticar.
Una ventana de despacho agotada no significa panel terminado; reanudar solo
tareas nunca ejecutadas, en condiciones verificadas, sin reiniciar fallos.

Preparar un `INFORME_NOCTURNO.md` en la carpeta del manifiesto con lo terminado,
lo activo, los fallos, los pendientes y los resultados con fuentes. Permanecer
en silencio si no hay cambio significativo. Avisar por cierres importantes,
errores relevantes o decisiones que requieran al usuario. Al cerrar todas las
tareas, informar cobertura real y proponer detener el seguimiento; no archivar
el chat automáticamente.

## Límites de autonomía

Sin cambios de biblioteca, presupuesto, criterios, particiones, tolerancias o
umbral basados en test. Sin descargas masivas, nuevos entrenamientos fundacionales,
subidas externas, commits/push ni edición del manuscrito. No borrar archivos.
Sí a implementar comprobaciones/adaptadores fieles y orquestación dentro de
los protocolos autorizados, con tests y trazabilidad. Si hace falta un cambio
científico o autoridad nueva, registrar el bloqueo y consultar cuando el usuario
esté disponible, continuando tareas independientes seguras.

## Preparación del vínculo de DeiT (seguimiento 29-10, 02:06 UTC)

Se añadió `scripts/diagnose_deit_dataset_binding.py`, sin modificar el
benchmark activo ni el adaptador histórico. Sin `--execute`, verifica hashes,
forma del archivo y dos imágenes fijadas antes de ejecutar modelos: primera y
última fila del manifiesto completo. La preparación de CUReT, Outex, Soil y
DTD está en `binding_preparation_v1/` bajo la carpeta nocturna. Estado
`binding_inputs_prepared`: NO es paridad aprobada ni una medición física.

Próxima dependencia: cuando no haya benchmark GPU activo, ejecutar una sola
vez el diagnóstico de cada dataset, en otra carpeta nueva, usando su config,
el pooler recuperado de FMD y la tolerancia original 1e-4. El script rechaza
ejecutarse si detecta un benchmark activo y no admite KTH ni una repetición
de FMD. No lanzar diagnósticos en paralelo. Revisar procesos inmediatamente
antes de despachar; el detector no sustituye una orquestación exclusiva.
La continuación automática se incorporó en la cola suplementaria descrita abajo.

Solo `diagnostic_complete` con dos checks aprobados, hash del embedding local
y hash del pooler permite evaluar el vínculo. Un fallo se conserva como
requiere revisión, sin nuevo intento, cambio de semilla, tolerancia o vector.
Aunque pase, revisar el resto de la receta/manifest y preparar una cola
suplementaria versionada; no editar el manifiesto que consumen los workers
activos ni levantar su puerta a ciegas. Las ocho condiciones KTH continúan
retenidas por reconciliación de protocolo.

## Cola suplementaria programada (29-10, 04:09 UTC)

Registro independiente: `results/analysis/overnight_multidataset_online_20261029_v1/manifest.json`.
Worker: `scripts/overnight_multidataset_online.py`, PID inicial 16153;
estado: `worker.json` en esa carpeta. No editar sus fuentes mientras está vivo.
Registrar también esta cola en los seguimientos, sin sumarla a condiciones
completas hasta que sus auditorías terminen.

Contiene las 56 condiciones online de Outex, Soil, CUReT y DTD, con cinco
métodos por condición, reutilizando heads y replay del manifiesto original.
KTH no se habilita y ninguna receta científica cambia. Las rutas físicas y
diagnósticos serán nuevas, sin sobrescribir las reservadas por la cola original.

Espera las treinta condiciones físicas FMD completas y auditadas, y ausencia
de benchmark GPU. La cola original conserva su manifiesto y sus puertas, por
lo que no puede despachar estas condiciones. La suplementaria usa lock propio
y comprueba procesos antes del diagnóstico y antes del benchmark. Solo tras
un diagnóstico DeiT aprobado para el dataset despacha su ejecución física y
auditoría. Un fallo se conserva y bloquea las condiciones de ese dataset,
sin reintento ni búsqueda de semilla/tolerancia alternativa; avanza con las
independientes que pasen. Todavía ninguna de estas 56 se cuenta como medida.

Ventana de despacho hasta 29-10 09:42:43 UTC, alineada con la cola original.
Una condición ya activa conserva su límite de cuatro horas. No se garantiza
completar todas antes de esa hora. Red offline para pesos, dos hilos CPU,
sin descargas grandes. Comprobar `requires_review`, logs, hashes y cobertura.

## Corte de ejecución 29-10, 04:36 UTC

FMD físico completo: treinta condiciones auditadas, ambos clasificadores y
los cinco métodos; consolidados por clasificador y tres semillas disponibles
en `summary_FMD_{svm,resmlp}_all_seeds_online_v1/` dentro del registro original.
No repetir ninguna condición FMD.

Los primeros diagnósticos suplementarios ya se ejecutaron UNA vez. Outex y
Soil no pasan el vínculo DeiT (errores ~0,19–0,21 frente a 1e-4): los dos
datasets y sus 32 condiciones físicas dependientes requieren revisión.
NO reintentar diagnósticos ni benchmarks, cambiar semilla, quitar DeiT o
relajar tolerancia. Conservar hashes/vectores/logs. La investigación causal
puede continuar en lectura; nuevas pruebas o cambios requieren dirección
explícita. Sus resultados de calidad en caché siguen siendo válidos dentro
de ese alcance, no son F1 online para acompañar tiempos de otro contexto.

CUReT pasó sus dos filas acotadas y la suplementaria está midiendo su primera
condición SVM. DTD espera su diagnóstico en el orden de la cola. KTH sigue
retenido. Consultar ambos registros; no informar panel completo porque cerró
FMD. El informe nocturno contiene resultados, cobertura y las incidencias.

Actualización 08:52 UTC: CUReT/SVM también cerró ambas direcciones físicas,
con auditorías y consolidado `summary_CUReT_svm_online_v1/` en la carpeta
suplementaria. No repetirlas. La GPU sigue con CUReT/ResMLP, todavía incompleto.

## Continuación de calidad nunca iniciada (29-10, 09:37 UTC)

Registro: `results/analysis/overnight_quality_resume_20261029_v1/continuation.json`.
Script `scripts/resume_overnight_quality.py`, preparado/probado y lanzado en
espera de que el worker CPU original termine normalmente su ventana y salga.
No mata la condición activa y no añade un segundo trabajo de calidad mientras
el worker original vive. Después admite únicamente jobs sin marcador de
intento y sin ninguna carpeta de resultado/auditoría previa; excluye fallos,
parciales, completos, managed y KTH retenido. Nuevos directorios y manifiesto,
misma configuración científica, hashes y dos hilos CPU. Ventana nueva de
tres horas de despacho después del traspaso, con timeouts originales.

Antes de usar resultados tardíos en una cola física futura, consultar este
manifiesto de continuación: las nuevas rutas de calidad no sustituyen ni
modifican el manifiesto que ya consumen los workers anteriores. No contar
los jobs registrados como ejecutados hasta que cierren calidad y replay.

## Continuación física nunca iniciada (29-10, 10:07 UTC)

Registro nuevo: `results/analysis/overnight_online_resume_20261029_v2/continuation.json`.
Script `scripts/resume_multidataset_online.py`, lanzado en espera del cierre
normal de la suplementaria y ausencia de benchmark GPU. No prolonga ni
interrumpe la condición CUReT/ResMLP activa. Después filtra exclusivamente
jobs sin marcador de intento y sin resultado parcial: no copia fallos o
completos. Las 32 condiciones Outex/Soil quedan excluidas por sus marcadores,
y KTH nunca formó parte de esa cola.

Reutiliza por copia hash-verificada solo el diagnóstico CUReT aprobado,
sin repetirlo. Diagnostica las dependencias aún nunca probadas (DTD) antes
de otro benchmark largo, a la misma tolerancia; un fallo queda requiere
revisión y no se reintenta. Vincula las rutas tardías de calidad desde el
manifiesto de continuación solo si config y hash científico son idénticos.
Outputs/manifiesto nuevos, recetas y timeouts iguales, GPU secuencial, dos
hilos CPU, pesos offline y ventana de tres horas desde el traspaso.

Actualización 11:07 UTC: calidad/replay no-KTH cerrada (86 condiciones), usando
las tres rutas nuevas DTD/ResMLP de la continuación. Físico: FMD completo,
CUReT/SVM completo y primera dirección CUReT/ResMLP auditada. La v1 terminó
su ventana y la v2 ejecuta la última dirección CUReT/ResMLP. Vínculo DeiT DTD
pasó sus dos filas a 1e-4; la v2 conserva veinte condiciones DTD nunca
iniciadas para medir después, con heads congelados y rutas de calidad
reconciliadas. Outex/Soil no se reintentan; KTH continúa retenido.

Actualización 13:07 UTC: CUReT físico completo en ambos clasificadores,
consolidado ResMLP en v2 `summary_CUReT_resmlp_online_v1/`. Para reconstruirlo
se usa el manifiesto v1 y `--override-manifest` v2, exigiendo condición/hash
idénticos; no repetir mediciones. FMD y CUReT suman 34 condiciones físicas
auditadas. La cola v2 ya mide el primer split DTD/SVM; no anunciar todavía
medias físicas de DTD o un panel completo de seis datasets.

Actualización 14:37 UTC: primer split DTD/SVM auditado (v2), todavía no una
media completa del dataset. V2 salió normalmente; continuación v3 en
`results/analysis/overnight_online_resume_20261029_v3/`, diecinueve condiciones
DTD nunca iniciadas, tres horas de despacho y mismos límites científicos.
Worker 31857, GPU secuencial. Consulta ahora también su `worker.json` y sus
rutas nuevas; no repetir el primer split ni el diagnóstico DTD aprobado.

Actualización 17:37 UTC: tres splits DTD/SVM físicos auditados (primero en
v2; segundo y tercero en v3), cuarto en ejecución. Cobertura total física:
37 condiciones, 114.320 llamadas completas. No consolidar aún DTD como
dataset completo ni mezclar sus F1 de caché con tiempos online. Al cerrar
normalmente la ventana v3, continuar solo condiciones nunca iniciadas en
una carpeta nueva, usando el mismo script probado y sin repetir diagnósticos
aprobados o fallidos. No interrumpir la condición activa por fin de ventana.

Actualización 18:52 UTC: cuarto split DTD/SVM físico auditado; cobertura
total 38 condiciones y 123.720 llamadas completas. V3 terminó normalmente
a 18:44:49 UTC. Continuación v4 en
`results/analysis/overnight_online_resume_20261029_v4/`: 16 condiciones DTD
nunca iniciadas, worker 37719 (sesión 1161), mismo script/protocolo y tres
horas de despacho. Empieza quinto split SVM; los diez ResMLP siguen en cola.
Usar ahora también manifiesto/worker/rutas v4; no repetir los cuatro splits
cerrados ni diagnósticos DeiT. Outex/Soil y KTH continúan retenidos.

Actualización 20:22 UTC: quinto split DTD/SVM auditado en v4, sexto activo.
Cobertura física total 39 condiciones y 133.120 llamadas completas. DTD/SVM
cinco de diez; DTD/ResMLP sigue pendiente. No consolidar medias DTD parciales
ni promover el mejor resultado de un split a superioridad general.

Actualización 21:37 UTC: sexto split DTD/SVM físico auditado en v4, séptimo
activo (GPU 39701, worker 37719). Total 40 condiciones físicas auditadas y
142.520 llamadas completas; DTD/SVM seis de diez, ResMLP aún pendiente.
Mantener las diferencias de calidad observadas, incluidos los splits donde
el adaptativo pierde; no resumirlos como mejora universal.

## Pausa solicitada por el usuario, 29-10-2026

El usuario pidió dejar finalizar únicamente el split activo DTD_svm_s42_f6
y después pausar hasta nueva solicitud explícita. La ventana v4 venció a
21:52:12 UTC: el worker 37719 terminará la medición y auditoría actuales y
saldrá, sin despachar otro split. La automatización
`tesis-continuar-corridas-f1-y-latencia` se puso en PAUSED para impedir que
se cree una continuación v5. No reanudar ni iniciar nuevas condiciones sin
pedido explícito del usuario. Conservar todos los resultados y consultar
worker.json, online/status.json y online_audit/audit.json al retomar; no
asumir que el split activo cerró correctamente solo porque se pidió pausa.

## Reanudación explícita del usuario: 30-10-2026, 02:49 UTC

La nueva solicitud de continuar revoca la pausa anterior. V4 cerró
normalmente a 00:25:06 UTC, con DTD_svm_s42_f6 medido y auditado. Sus
registros aritméticos pasan, pero las latencias contienen valores extremos:
Top-4 media 960,945 ms frente a mediana 268,929 ms. Marcar la aptitud de esa
medición física como REQUIERE REVISIÓN; preservar todos los valores, sin
recortar outliers, repetir la condición ni declarar causalidad no verificada.
No interpretar el auditor aritmético como certificación del entorno físico.

Tras comprobar que no había workers/benchmarks activos, continuación v5 en
`results/analysis/overnight_online_resume_20261029_v5/`: trece condiciones DTD
nunca iniciadas, tres SVM y diez ResMLP; worker 41544, sesión 26914, primer
job DTD_svm_s42_f7, único benchmark GPU 41547. Mismo script/protocolo,
diagnóstico DTD aprobado copiado y verificado, ventana de despacho tres
horas. Automatización reactivada mediante herramienta del producto (ACTIVE).
Cobertura de registros auditados: 41 condiciones y 151.920 llamadas;
de ellas una condición física con reserva explícita de latencia. Las
retenciones Outex/Soil/KTH siguen sin autorización de reintento o cambio.

Actualización 30-10, 04:19 UTC: octavo split DTD/SVM auditado en v5,
noveno activo (GPU 42666, worker 41544). Cobertura 42 condiciones con
registros auditados y 161.320 llamadas; una condición física sigue marcada
para revisión por latencias extremas. No eliminar esa reserva al consolidar
DTD ni repetirla automáticamente. DTD/ResMLP permanece pendiente.

Actualización 30-10, 05:34 UTC: noveno split DTD/SVM auditado en v5, décimo
activo (GPU 43605, worker 41544). Cobertura 43 condiciones con registros
auditados y 170.720 llamadas; reserva física del séptimo split preservada.
Tras cerrar el décimo, consolidar los diez sin ocultar la anomalía física,
y continuar DTD/ResMLP en nueva carpeta cuando v5 termine normalmente.

Actualización 30-10, 07:04 UTC: diez splits DTD/SVM medidos y auditados.
Consolidado con hashes en v5/summary_DTD_svm_online_v1/summary.json; incluye
sin filtrar el séptimo split con reserva explícita de latencia. No publicar
ahorro robusto basado en medias contaminadas por valores extremos ni ocultar
la anomalía cambiando a medianas. F1 medio: adaptativo 0,866857, Top-4
0,868890, diversidad 0,873371, tómbola 0,872353, Completa 0,863544.
V5 terminó normalmente; continuación v6 nueva a 07:05 UTC con diez DTD
ResMLP nunca iniciados, worker 45000, sesión 96929. Consultar ahora
results/analysis/overnight_online_resume_20261029_v6/worker.json y sus rutas.
Cobertura: 44 condiciones con registros auditados, 180.120 llamadas; una
condición con reserva de latencia. Sin reintentos o cambios científicos.

Actualización 30-10, 08:34 UTC: primer DTD/ResMLP físico auditado en v6,
segundo activo (GPU 46046, worker 45000). Cobertura 45 condiciones con
registros auditados y 189.520 llamadas completas; reserva del séptimo split
SVM preservada. No consolidar DTD/ResMLP antes de sus diez condiciones.

Actualización 30-10, 09:49 UTC: segundo DTD/ResMLP auditado en v6, tercero
activo (GPU 47128, worker 45000). Total 46 condiciones con registros
auditados, 198.920 llamadas completas; reserva física del séptimo split
SVM preservada. Esperar cierre normal v6 antes de otra continuación en
directorio nuevo y nunca repetir condiciones ya intentadas.

Actualización 30-10, 11:20 UTC: tercer DTD/ResMLP auditado en v6; v6 terminó
normalmente a 11:09:44 UTC. Continuación v7 nueva en
results/analysis/overnight_online_resume_20261029_v7/ con siete condiciones
DTD/ResMLP nunca iniciadas (índices 3–9), worker 48261, sesión 84016,
misma receta y ventana de tres horas. Cuarto split ResMLP en ejecución.
Cobertura 47 condiciones con registros auditados y 208.320 llamadas; reserva
física del séptimo split SVM preservada. Sin reintentos o cambios científicos.

## Pausa inmediata solicitada por el usuario, 30-10-2026

La instrucción vigente es «pausa de momento». Automatización confirmada
PAUSED. Se detuvieron por SIGTERM el benchmark v7 48264 y worker 48261,
tras verificar sus argumentos y congelar primero el despacho del worker.
Comprobación posterior: ningún proceso de benchmark/continuación activo.
DTD_resmlp_s42_f3 queda interrumpido voluntariamente, con último checkpoint
observado 3.100/9.400 llamadas, no completo ni fallo científico. Los archivos
se conservan íntegros; worker.json/status.json pueden decir running porque
no se reescribieron evidencias experimentales al terminar por señal.
No retomar este parcial como si hubiera checkpoint de ejecución ni repetirlo
automáticamente. Al reanudar, requerirá decisión explícita para una nueva
medición en directorio nuevo. Restantes condiciones nunca iniciadas pueden
continuarse solo tras pedido de reanudación. Cobertura completa: 47 condiciones
con registros auditados y 208.320 llamadas; reserva de latencia SVM intacta.

## Reanudación explícita y programación, 31-10-2026, 21:56 Asunción

El usuario pidió continuar y dejar programado, revocando la pausa. Se
verificó ausencia de benchmarks/workers y GPU disponible. Worker v7 JSON
running es evidencia obsoleta por SIGTERM humano, no finalización normal.
Se mantiene inalterado y se añadió user_pause_resume_receipt.json ligado
por hashes a worker/manifiesto, excluyendo DTD_resmlp_s42_f3 interrumpido.

Nuevo adaptador scripts/resume_user_paused_online.py permite esa transición
solo con recibo explícito válido y únicamente condiciones nunca iniciadas;
conserva guards de fuentes/config, exclusión de parciales y recetas originales.
Pruebas enfocadas nuevas + originales: 9 aprobadas. Script original no cambiado.

Cola activa: results/analysis/overnight_online_resume_20261031_v8/,
seis DTD/ResMLP índices 4–9, worker 817, sesión 72844, inicio 01-11
00:56:24 UTC; primer job DTD_resmlp_s42_f4. Tres horas de despacho y límites
previos sin cambios. Automatización existente confirmada ACTIVE cada 15 min.
Consultar worker/manifiesto v8 y continuar desde esa cola al cerrar normalmente;
no lanzar de nuevo v7. No repetir el parcial índice 3 sin decisión explícita
del usuario (pregunta enviada), ni fallos Outex/Soil o reserva física SVM.
KTH sigue retenido. Cobertura completa 47 condiciones y 208.320 llamadas.

Actualización 01-11, 02:27 UTC: split oficial 5 DTD/ResMLP auditado en v8;
cuatro splits completos en total (índices 0,1,2,4), índice 3 parcial aún
excluido y sin autorización recibida para repetir. Sexto split oficial
activo (índice 5, GPU 2058, worker 817). Cobertura 48 condiciones con
registros auditados y 217.720 llamadas; reserva física SVM preservada.
No presentar cobertura parcial como media completa ni reintentar el parcial.

Actualización 01-11, 03:57 UTC: split oficial 6 DTD/ResMLP auditado en v8;
cinco completos (índices 0,1,2,4,5), no seis; índice 3 sigue parcial excluido.
Séptimo oficial activo (índice 6, GPU 3194, worker 817). Cobertura 49
condiciones con registros auditados y 227.120 llamadas. Ventana v8 vencida;
al cerrar normalmente continuar solo índices 7–9 nunca iniciados en nueva
carpeta usando script probado. No reintentar índice 3 sin decisión explícita,
ni ocultar reserva de latencia SVM. Sin cambios científicos.

Actualización 01-11, 05:12 UTC: split oficial 7 DTD/ResMLP auditado; seis
completos (índices 0,1,2,4,5,6), índice 3 sigue parcial sin permiso de repetir.
V8 terminó normalmente a 05:05:44 UTC; v9 nueva en
results/analysis/overnight_online_resume_20261101_v9/ ejecuta índices 7–9
nunca iniciados, worker 4321, sesión 74244, tres horas de despacho. Primer
job DTD_resmlp_s42_f7. Cobertura 50 condiciones con registros auditados y
236.520 llamadas; reserva física SVM preservada. No consolidar como diez
splits completos cuando v9 cierre: seguirá faltando el índice 3 interrumpido.

Actualización 01-11, 06:42 UTC: octavo oficial DTD/ResMLP auditado en v9;
siete completos (índices 0,1,2,4,5,6,7). Noveno oficial activo (índice 8,
GPU 5385, worker 4321). Cobertura 51 condiciones con registros auditados y
245.920 llamadas. Parcial índice 3 excluido, reserva física SVM preservada;
no informar medias de diez condiciones ni reintentar sin decisión explícita.

Actualización 01-11, 08:12 UTC: noveno oficial DTD/ResMLP auditado en v9;
ocho completos, índice 3 parcial excluido sin autorización de repetición.
Décimo oficial activo (índice 9, GPU 6759, worker 4321). Cobertura 52
condiciones con registros auditados y 255.320 llamadas. Al cerrar v9 no
crear una continuación vacía: documentar nueve de diez ResMLP completos,
sin presentar media como panel completo; parcial y reservas requieren decisión.
No pasar a réplicas de papers como si el panel local estuviera cerrado.

Actualización 01-11, 09:27 UTC: décimo oficial DTD/ResMLP auditado, v9
terminó normalmente a 09:21:11 UTC; sin workers/benchmarks activos. Total
53 condiciones con registros auditados y 264.720 llamadas. DTD/ResMLP
nueve de diez completos, índice 3 interrumpido aún excluido sin permiso
recibido para repetir. No lanzar v10 vacía ni reintentar el parcial por
heartbeat. Mantener reservas DeiT Outex/Soil, protocolo KTH y latencia SVM.
No publicar media completa de diez splits ni saltar a papers. Continuar
solo trabajo independiente seguro; permanecer en silencio si no hay nueva
decisión o cambio accionable. Automatización no significa autorización de
repetir condiciones fallidas/interrumpidas ni alterar recetas congeladas.

## Autorización explícita recibida y repetición única, 01-11, 12:14 UTC

El usuario respondió «Sí, repetir ese split en una carpeta nueva» a la
pregunta del cuarto DTD/ResMLP interrumpido. Esta decisión autoriza solo
DTD_resmlp_s42_f3 desde cero con receta idéntica y parcial v7 conservado.
Comprobada ausencia de benchmarks/workers activos, se preparó manifiesto
de una condición en results/analysis/overnight_online_retry_20261101_DTD_resmlp_f3/,
copiando la condición original y cambiando únicamente rutas de salida,
plazo operativo y constancia de autorización. Fuentes, config, selección,
pesos, semillas, particiones, tolerancias, tiempo por imagen y repeat=1
sin cambios. Diagnóstico DTD aprobado reutilizado, sin nueva prueba.

Worker probado overnight_multidataset_online.py en modo worker; PID 9095,
sesión 40526, inicio 12:14:58 UTC; timeout de medición 14.400 s más auditoría.
La automatización existente deberá consultar esta carpeta activa, no lanzar
v10 ni reintentos adicionales. Ante fallo preservar y pedir revisión.
Tras auditoría exitosa, consolidar diez DTD/ResMLP usando v6 índices 0–2,
esta carpeta índice 3, v8 índices 4–6 y v9 índices 7–9. No incluir parcial
v7 ni F1 histórico para rellenar. Mantener reserva de latencia DTD/SVM,
DeiT Outex/Soil y KTH. Cobertura completa sigue 53/264.720 hasta auditar.

Actualización 01-11, 13:45 UTC: repetición autorizada índice 3 completada
y auditada (9.400 llamadas); worker all_jobs_terminal, sin benchmarks activos.
DTD/ResMLP consolidado en diez splits, 94.000 llamadas, con hashes por
fuente en overnight_online_retry_20261101_DTD_resmlp_f3/summary_DTD_resmlp_online_v1/summary.json.
DTD/SVM también tiene diez splits; permanece su reserva física de latencia.
Cobertura global: 54 condiciones con registros auditados, 274.120 llamadas.
FMD, CUReT y DTD tienen cobertura completa de registros para ambos
clasificadores/cinco métodos. No equivale a cerrar el panel de seis datasets:
Outex/Soil requieren revisión del binding DeiT; KTH, reconciliación de protocolo.
No lanzar nuevas repeticiones ni papers por este cierre parcial del panel.

## Enmienda explícita y nueva cola, 01-11, 13:58 UTC

El usuario pidió resolver los bloqueos y aprobó expresamente regenerar solo
DeiT en Outex/Soil, recalcular OOF/heads train-only y medir sus32condiciones,
y repetir completo DTD/SVM official7 con observabilidad y originales intactos.
Autoridad y alcance exacto: ENMIENDA_DESBLOQUEO_PANEL_2026-11-01.md.
No extender esta autorización a regenerar KTH ni repetir fallos nuevos.

La reconciliación KTH comprobó imágenes/filas, particiones, selección interna
por muestra y cache configurado. Habilitada nueva calidad8condiciones, con
reserva histórica intacta. Online depende de un diagnóstico KTH nuevo probado,
alias KTH-TIPS2-b, filas0/4751, tolerancia original. Fallo→revisión, no retry.

Cola activa: results/analysis/blocker_resolution_20261101/queue_v1/manifest.json.
SHA256 ab504ed069cb827f76891c15e0959439e20e4da7be992fb62c3c06f4017bd7a4.
Contiene40condiciones únicas pendientes y una observación adicional DTD que
no aumenta cobertura. 86tareas con dependencias, hashes de fuentes/configs/
datos/paquetes; originales no modificados. Nuevo ejecutor probado:
scripts/run_authorized_remediation_queue.py. Worker GPU14246 (sesión72022),
CPU14242 (sesión51653), inicio13:58:33UTC. Un solo proceso GPU y CPU2hilos;
CPU CUDA oculto. Estados gpu.json/cpu.json; tareas tasks/<id>/state.json y logs.

Orden GPU: extraer nuevos DeiT Outex/Soil, verificar vínculos de los tres
datasets, medición adicional DTD/SVM, online de40condiciones según calidad.
CPU: calidad/replay KTH; luego Outex/Soil con representación nueva verificada.
Las recetas archivadas de controles no cambian; la selección adaptativa OOF
se vuelve a congelar antes del test. No mezclar calidad anterior con ms nuevos.

Seguimiento: inspeccionar ESTA cola además de los cierres anteriores. No
duplicar workers. Ventana10h por lane, sin cortar tarea activa al expirar.
Si un worker termina normalmente por ventana y no hay proceso vivo, se puede
reanudar el mismo manifiesto/lane para tareas nunca despachadas; el ejecutor
omite terminales y NO repite estados parciales/fallidos. No editar scripts ni
manifiesto activos. requires_review/blocked no son permisos de repetición.
Auditar outputs, actualizar cobertura e informe antes de contar completados.
Observador externo cada30s no certifica aislamiento ni elimina reserva original.

### Soil: corrección de esquema aprobada, 01-11, 14:06 UTC

La extracción Soil se detuvo en read_manifest antes de construir el modelo:
el CSV usa source_path/etiquetas texto en lugar de path/label numérico/class_name.
Fallo y outputs originales intactos. No fue una prueba científica de DeiT.
Adaptador nuevo prepare_soil_extraction_manifest.py:4tests aprobados; comprobadas
1140imágenes, siete clases, orden/grupos/hashes/etiquetas canónicas intactos,
y loader de extracción real acepta el CSV adaptado. Recibo sin GPU en
results/analysis/blocker_resolution_20261101/soil_schema_adapter_v1/receipt.json.

El usuario autorizó «Sí, despachar Soil con el formato corregido». Nueva cola
results/analysis/blocker_resolution_20261101/soil_format_resume_v1/manifest.json,
solo extracción+binding Soil, nuevas salidas. Sesión90290, lane GPU, lock GPU
compartido: espera la medición DTD activa, no la duplica ni interfiere.
No editar queue_v1 activa ni sus estados blocked/requires_review.
Tras pasar extracción/binding: preparar cola nueva de calidad/replay/online
de las30condiciones Soil nunca iniciadas sobre esta nueva raíz de embeddings,
con mismos configs científicos, sin duplicar worker CPU vigente. La autorización
de enmienda original sigue vigente para esos30jobs; la autorización adicional
no permite otro retry si falla de nuevo. Outex/KTH binding pasaron en queue_v1;
CPU calidad KTH y benchmark adicional DTD continúan. Cobertura54/274120 intacta.

Seguimiento01-11,14:31UTC: primera condición KTH/ResMLP official1 cerró calidad
y replay el14:17:09UTC:5940predicciones (1188imágenes×5métodos), hash de estado
c2beeae2963b3e32deefc3c9a4389cd01e01d7bb2f1b83869cb0690a1d602c0a
coincide con auditoría. No hay medición online KTH completada ni media completa.
Official2/calidad activo PID16273; DTD adicional3100/9400llamadas PID14363;
Soil corrección espera lock GPU. No duplicar ni cambiar colas activas.

Seguimiento01-11,15:16UTC: cuatro condiciones KTH/ResMLP calidad+replay
completas,23760predicciones, hashes auditados. Resumen explícitamente en caché:
queue_v1/summary_KTH_resmlp_cached_quality_v1/summary.json. No F1/ms online.
KTH/SVM official1 también calidad auditada; official2 activo PID17230.
DTD adicional7750/9400llamadas, Soil sigue esperando lock. Sin nuevo fallo.
Cobertura física única54/274120 intacta; no extrapolar caché a resultados online.

Seguimiento01-11,15:31UTC: KTH completó calidad/replay de ocho condiciones
(cuatro SVM y cuatro ResMLP), hashes y cobertura auditados. Ambos resúmenes
en queue_v1/summary_KTH_{svm,resmlp}_cached_quality_v1/summary.json; son caché,
sin ms online. CPU pasó a Outex/ResMLP PID17608. DTD adicional9350/9400,
no contado completo aún; Soil esperando lock. No nuevos fallos ni cambios.

Seguimiento01-11,15:46UTC: adicionalDTD/SVM completó9400llamadas y auditoría
a15:31:49UTC, observador cerró sin señalizar target. Original intacto; comparación
versionada en queue_v1/DTD_additional_comparison_v1.json. F1 por método idéntico
al original;0llamadas>60s en adicional frente25original. No sustituir ni elegir
versión por menor latencia, no afirmar aislamiento/causa probada. Cobertura
única54/274120 más9400llamadas adicionales auditadas (283520totales distintas
observaciones, no nuevas condiciones). Outex calidad/replay ambos heads cerrados.

Las8mediciones KTH fallaron antes de modelos/extracción/cronómetro: benchmark
original línea111 construye ruta KTHTIPS2b/deit_s.npy sin resolver alias
KTH-TIPS2-b, aunque loader y diagnóstico lo manejan. Son8condiciones distintas,
no reintentos; cada fallo requiere revisión y se conserva. No medidas KTH
completadas. Adaptador NUEVO benchmark_local_single_image_alias_v1.py corrige
únicamente esa ruta. Tres tests pasan, incluyendo igualdad AST de todo el
programa salvo helper/expresión de ruta; fuente original no editada.
Se pidió autorización explícita para volver a despachar las8condiciones en
directorios nuevos con los mismos heads/selección; no lanzar hasta recibirla.
Outex/ResMLP online activo PID18024; Soil15566 sigue esperando lock. CPU14242
terminó normalmente todas sus tareas elegibles, sin fits activos. No tocar
colas/scripts guardados mientras workerGPU14246 sigue activo.

Seguimiento01-11,16:16UTC: Outex/ResMLP nueva representación completó online
y auditoría3400llamadas/680imágenes/cinco métodos, hash de estado verificado.
Primera condición física Outex cerrada; su único split oficial es toda la
cobertura prevista de este head, no extrapolar a SVM aún activo PID18720.
Cobertura única55/94,277520llamadas primarias auditadas más9400adicionalDTD
(286920observaciones totales auditadas). Soil15566 espera lock; KTH online
sigue requiere revisión por ruta, no se reintenta sin autorización pendiente.

## Cierre Outex y cola Soil habilitada, 01-11, 16:46 UTC

Outex/SVM cerró online/auditoría3400llamadas, hash de estado coincidente.
Outex ambos heads completo en su único split oficial, resumen nuevo
queue_v1/summary_Outex_both_online_v1/summary.json. Cobertura física única56/94,
280920llamadas primarias completas más9400adicionalDTD=290320observaciones
auditadas. No extrapolar Outex a otros datasets ni sustituir archivos históricos.

Soil corrigió esquema, extrajo DeiT y aprobó binding primera/última fila a
tolerancia1e-4, errores máximos1,9744e-7/1,5646e-7. Nuevo embedding SHA256
71165181b79c1ecba54703392076421011fd4278ff8c3c84181c5b71459bc9fd.
soil_format_resume_v1 terminó ambas tareas sin error; no se reintenta nada.

Preparador nuevo prepare_soil_pending_queue.py y tests focalizados14passed.
Cola soil_pending_v1/manifest.json SHA256
3fab9e1b648be1d7b60b660ae5798c12f56346b4442de7ed02ee9aee2e0b1829,
30condiciones Soil de enmienda nunca iniciadas,60tareas calidad/replay+online/
auditoría, configs científicos intactos salvo raíz nueva de embeddings y salidas.
Dependencia binding aprobado guardada por hash; control de paquetes/fuentes,
CPU2hilos, unGPU, repeat1, sin retries. WorkerCPU19573(sesión81741), GPU19563
(sesión32808). CPU calidadResMLP/s42/f0 PID19574, GPU espera esa calidad.
Workers anteriores terminales y sin procesos al despachar. Consultar ahora
soil_pending_v1/{cpu,gpu}.json y tasks/<id>/state.json, no reactivar queue_v1
para Soilblocked. KTH online sigue detenido hasta aprobación explícita pendiente.

Seguimiento01-11,17:16UTC: Soil/ResMLP/42/folds0y1 online completos y auditados,
1140llamadas/228imágenes cada uno, hashes source_status coincidentes. Cobertura
única58/94,283200llamadas primarias más9400adicionalDTD=292600observaciones
auditadas. No media Soil completa: faltan13condiciones ResMLP y15SVM.
GPU fold2 PID20219 y CPUcalidadfold3 PID20160, workers19563/19573 vigentes;
no duplicar, no nuevos fallos/retries. KTH autorización aún pendiente.

Seguimiento01-11,19:01UTC: Soil cerró calidad/replay de30condiciones
(15SVM+15ResMLP),34200predicciones; hashes auditados, workerCPU19573terminal
y sin fits activos. GPU19563 continúa onlineResMLP/2026/f2 PID24541.
Doce condiciones Soil online auditadas,13680llamadas; cobertura global68/94,
294600primarias+9400adicionalDTD=304000observaciones auditadas. No media Soil
online completa hasta15condiciones por head. Sin nuevos fallos; KTH retenido.

Seguimiento01-11,19:31UTC: Soil/ResMLP online15/15 completo y auditado,
17100llamadas,3420por método, tres semillas×cincofolds. Consolidado con hashes
en soil_pending_v1/summary_Soil_resmlp_online_v1/summary.json. Es media completa
de ese head, no de SVM ni de ambos. GPU19563 pasó a SVM/42/f0 PID27145.
Cobertura única71/94,298020llamadas primarias+9400adicionalDTD=307420auditadas.
SVM0/15online y KTH8retenidas; no adelantar papers ni relajar reservas.

## Autorización KTH recibida y cola nueva, 01-11, 19:36 UTC

El usuario respondió «Sí, despachar las ocho mediciones con la ruta corregida».
Autoridad exacta: AUTORIZACION_REDESPACHO_KTH_2026-11-01.md. Los8fallos previos
y sus salidas se conservan. No hubo llamadas medidas en esos intentos.
Nueva cola kth_alias_redispatch_v1/manifest.json SHA256
01fb79fc89bf1b15dc87fd70b76a9b9312d1cf44ae6341659cb4dae2d4b508d5,
ocho tareas benchmark+auditoría. Usa benchmark_local_single_image_alias_v1.py,
sin nuevos fits/OOF: fitted_heads/frozen_decisions/calidad originales guardados
por hash, fuentes/configs/paquetes/binding aprobados, mismos splits/repeat1.
17tests focalizados preparador/alias/cola aprobados. Original no modificado.

WorkerGPU28523, sesión5188, inicio19:36:35UTC, espera mismo lockGPU global de
soil_pending_v1. No hay segundo benchmark ni modificación de Soil activo.
Ventana10h de despacho; después reanudar solo tareas nunca ejecutadas si no
hay worker vivo, sin repetir requires_review. Nuevo fallo→revisión, no retry.
Seguir ambos manifiestos/estados. Media KTH solo tras4splits por head y auditoría.
Reservas de cascada histórica y hardware compartido intactas, papers diferidos.

En este corte Soil16online auditadas (15ResMLP+1SVM),18240llamadas, cobertura
única72/94,299160primarias+9400adicionalDTD=308560observaciones auditadas.
No contar KTH en cola como terminado. Preservar manuscrito y archivos previos.

Preferencia operativa posterior del usuario: elegir autónomamente las mejores
opciones técnicas y no consultar decisiones rutinarias. No amplía límites
científicos ni autoriza retries automáticos ante nuevos fallos científicos,
alterar métodos/tolerancias o editar manuscrito. Continuar alternativas seguras.

Seguimiento01-11,19:46UTC: Soil17online auditadas (15ResMLP+2SVM),19380llamadas;
cobertura global73/94,300300primarias+9400adicionalDTD=309700observaciones
auditadas. GPU Soil/SVM42/f2 PID29046, worker19563; KTH28523 espera lock global,
sin segundo benchmark ni nuevos fallos. No medias completas SVM todavía.

## Cierre Soil y comienzo KTH online, 01-11, 21:46 UTC

Soil30/30condiciones online completas y auditadas,34200llamadas. SVM15/15
consolidado con15fuentes/hashes en soil_pending_v1/summary_Soil_svm_online_v1/
summary.json; ResMLP15/15 en summary_Soil_resmlp_online_v1/summary.json.
F1 y tiempos de las mismas llamadas; archivos históricos intactos. Cobertura
única86/94,315120primarias+9400adicionalDTD=324520observaciones auditadas.

WorkerSoil19563 terminó normalmente y salió. KTHworker28523 tomó lockGPU y
está midiendo ResMLPofficial1 PID40652,550/5940llamadas al corte. Corrección
de alias ya superó preflight; no alterar receta ni repetir si falla. Único
benchmark activo. Faltan8KTHonline; no media completa hasta4porhead. Mantener
reservas históricas KTH y físicas DTD, papers diferidos, sin tocar manuscrito.

Seguimiento01-11,22:46UTC: primera KTH/ResMLPofficial1 online cerrada y auditada,
5940llamadas/1188imágenes/cinco métodos, hash de estado coincidente. Cobertura
única87/94,321060primarias+9400DTDadicional=330460observaciones auditadas.
No media KTH completa:1/4ResMLP y0/4SVM. Official2 activo PID42729, worker28523,
único benchmarkGPU; sin nuevos fallos ni reintentos. Reservas previas intactas.

Seguimiento02-11,01:16UTC: KTH/ResMLP4/4online completo y auditado,23760
llamadas,4752por método. Resumen y hashes en kth_alias_redispatch_v1/
summary_KTH_resmlp_online_v1/summary.json. No comparar calidad en caché con
ms nuevos: este resumen usa F1 de las mismas llamadas. GPU28523 pasó a
KTH/SVMofficial1 PID45443, único benchmark; faltan4SVM. Cobertura única90/94,
338880primarias+9400DTDadicional=348280observaciones auditadas. Reservas
históricas/físicas intactas, sin medias SVM parciales como completas ni papers.

Seguimiento02-11,04:01UTC: KTH/SVMofficial3 cerrado y auditado; sieteKTHonline,
41580llamadas. Cobertura única93/94,356700primarias+9400DTDadicional=366100
observaciones auditadas. Última KTH/SVMofficial4 PID49003, worker28523, único
benchmarkGPU. No nuevos fallos/retries; no media SVM completa todavía.

Consolidador nuevo scripts/consolidate_overnight_online_panel.py,5tests pasan.
Rutas explícitas por manifiesto para las94condiciones; separa adicionalDTD y
rechaza medias completas con faltantes. Reagregadas y verificadas las93ya
cerradas desde llamadas crudas y hashes de calidad/configs/heads/decisiones:
0errores, falta solo KTHTIPS2b_svm_s42_f3. Registro consolidation_preflight_93_v1.json.
No modelos ejecutados ni nuevos fits. Cuando última auditoría cierre, ejecutar
con --output results/analysis/blocker_resolution_20261101/full_panel_online_v1
(directorio NUEVO), sin --check-ready: debe producir94/470/60y362640llamadas
primarias más9400adicionales=372040. Si falla conservar evidencias y revisar,
no corregir promedios con caché/históricos ni ocultar reservas. No papers antes
de cerrar ese artefacto y el informe nocturno. Manuscrito/commits/push intactos.

## Cierre consolidado del panel local, 02-11, 04:46 UTC

Última KTH/SVMofficial4 terminó online y auditoría a las04:44:12UTC. Worker28523
terminó normalmente; no quedan benchmarks activos. Consolidador ejecutado con
éxito tras5tests: full_panel_online_v1/coverage.json declara
ALL_94_ONLINE_CONDITIONS_REAGGREGATED_WITH_RESERVES. Directorio completo:
results/analysis/blocker_resolution_20261101/full_panel_online_v1/.

Cobertura94/94condiciones únicas,47por clasificador; seis datasets, SVM/ResMLP,
cinco métodos.470filas condición-método y60filas dataset-clasificador-método.
362640llamadas primarias;9400adicionales DTD separadas,372040auditadas en total.
F1 y latencia reagregados desde las mismas llamadas online; fuentes, configs,
heads y decisiones verificadas mediante hashes. No resultados parciales como
medias completas. No nuevos entrenamientos ni repeticiones en la consolidación.

SHA256 coverage.json:2789666cea7bbce1cd893f24eb0886fd1bd45f0041ab5aa14b198e4753b4e365.
SHA256 dataset_summary.csv:d60b15b1046cfb82b052d1b370900c07d2ddac3d69537c0557fd5e6ae4968846.
SHA256 provenance.json:51fdacdcdf3b7cf5b50f35b6c36e656d98989b5d1fcd165075031cf617fd95f8.

Reservas conservadas: tiempos originales extremos DTD/SVMofficial7 siguen en
panel primario, observación adicional no los reemplaza; representación DeiT
nueva autorizada Outex/Soil; protocolo KTH nuevo reconciliado sin equivalencia
con cascada histórica; hardware compartido y una repetición por imagen.
No inferencia estadística global ni superioridad universal declarada.

Siguiente etapa: revisar preparación de comparadores externos y protocolos ya
aprobados. PLAN_MEDICION_COMPARADORES_Y_PAPERS_2026-10-27.md es preparación,
no receta ejecutable completa. PROTOCOLO_PILOTO_NESHOV_FMD_2026-10-28.md cubre
solo piloto de desarrollo ya realizado, no ampliación de datasets/semillas,
replicación100fold ni latencia online. No repetirlo ni lanzar nuevas corridas
improvisadas. Monitoreo posterior: permanecer en silencio ante estado sin cambio;
el panel local está cerrado en cobertura, no la tesis ni la reproducción de papers.
Manifiesto original, protocolo congelado, evidencias y manuscrito preservados.

## Continuación solicitada por el autor, 02-11

Siguiente plan operativo: PLAN_CONTINUACION_POST_PANEL_2026-11-02.md.
No quedan condiciones locales por despachar. Se pasa a preparación técnica
de comparadores, comenzando Neshov por disponibilidad de implementación.
Reauditoría nueva results/analysis/neshov_fmd_readiness_20261102_v1/:800
predicciones/logits de3heads reproducidos exactamente, exit0;12tests pasan.
No nuevos fits, extracción ni tiempos. Adaptador online y especificación externa
son siguientes entregables; no confundir piloto de desarrollo con panel externo.
El monitoreo continúa ese plan sin relanzar las94condiciones cerradas.
