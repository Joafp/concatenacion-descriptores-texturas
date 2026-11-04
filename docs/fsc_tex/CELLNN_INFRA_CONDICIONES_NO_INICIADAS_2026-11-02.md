# CellNN: serialización v2 solo para condiciones nunca iniciadas

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: corrección de infraestructura y continuación independiente autorizada.
- Origin Date: 2026-11-02.
- Verification Status: no autoriza repetir un experimento fallido/parcial.
- Version Label: cellnn_json_scalar_bridge_v2.

Primer CellNN_FMD_s42_f0: extract800completo,gateexacto(error0),train llegó a
guardarhead.joblib/head_params.json pero falló TypeError al serializar un
np.float32 delhistorial. Estado requires_review preservado en colaoriginal,
cero llamadas externas, sinreintento,recuperación dehead ni sustitución demétodo.
No se modifica runner/protocolo/artefactos sellados deese intento.

Corrección en entrypoint nuevo run_cellnn_external_condition_v2.py: convertir
solo escalaresNumPy a escalaresPython mediante .item() antes de JSON. float32
mantiene exactamente suvalor representable; no redondear, filtrar nonfinite,
alterar tensores/array/pesos ni operaciones científicas. JSONallow_nan=False
permanece. Runneroriginal fija entrenamiento/preproceso/cronómetro/auditoría;
elwrapper agrega suSHA a estados para identificar procedencia.

Continuar únicamente14condiciones que están blocked/dependency_requires_review
yNUNCA tuvieron pid,stage,started_utc,success_artifacts ojobdir. Verificar
esa ausencia explícitamente. Nueva cola/directorios/pins, sin reutilizarhead
delintento fallido; la primera nuevaauditoría habilita13restantes. No es
reintento de42/f0 ni cambio de suestado. Mismas particiones,receta,pesos,
MLPparams,presupuesto,semilla,lockGPU yCPU2hilos; protocolo científicoheredado.

Pruebas deben reproducir elTypeErrororiginal conlossnp.float32 ycomprobar
JSONnumérico equivalente, rechazo deNaN/inf yarrays inesperados; no sufice
un mock de loss_curve como floatPython. Elfallo expuso esa limitación detests.

Cobertura máxima deesta cola14/15FMD,2800llamadas. Nunca mediaFMDcompleta,
no sustituir lacondiciónfaltante porotra ni mezclar elheadparcial confitsnuevos.
Si otra condición falla,conservarrequires_review sinretry; continuar solo
ramas independientes autorizadas. Outex yNeshov intactos.
