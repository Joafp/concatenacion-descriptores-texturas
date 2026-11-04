# Despacho autónomo autorizado, 02-11

El autor autorizó continuar durante su ausencia aproximada de12h. No promesa
de completar todos los papers. El protocolo científico Neshov previamente sellado
se mantiene byte-idéntico; esta nota operativa no lo sustituye.

Runner scripts/run_neshov_external_condition.py y preparador
scripts/prepare_neshov_fmd_queue.py:32tests pasan de runner/preflight/adaptador/
dispatcher. Primera cola:15condiciones FMD, cuatro etapas por condición con
timeouts7200/1800/14400/300s. Todas en laneGPU del dispatcher existente para
retener lock durante extracción, fitCPU y benchmark, evitando competencia interna.
Condiciones2–15 dependen del cierre auditado deFMD42/f0. Fallo→requires_review
y dependientes bloqueados; no retry automático. Ventana de despacho12h, sin
recortar el timeout de una etapa ya activa por alcanzar el final de ventana.

Cola: results/analysis/neshov_fmd_external_queue_20261102_v1/manifest.json.
SHA256:4f43c3ba8b812987d52dad2d25b7d25f7a8d7e283200e77bf5932fba402a2a36.
Los argv exactos por etapa y hashes de fuentes/pesos/versiones están sellados
antes del primer modelo. No editar fuentes selladas con trabajo activo.

Dispatcher registraPID/startticks/tiempo/estado y logs. Runner registra avance,
timestampUTC por llamada y ambiente; no observador externo ni aislamiento.
CUBLAS_WORKSPACE_CONFIG=:4096:8 antes deCUDA. Auditoría relee llamadas y verifica
orden/cobertura, verdad, logits→clase y ns→ms; recalcula F1/accuracy/latencias.
CPU2hilos, FP32, offline, sin descargas, sin inferencia estadística global.
