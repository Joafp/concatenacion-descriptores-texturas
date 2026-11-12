# Cierre Neshov FMD paper-like 10x10

Estado: auditoría completa de 100/100 condiciones y 10.000 llamadas. El worker
estaba terminal y no se repitió ninguna medición. Una invocación inicial del
consolidador con Python del sistema falló antes de escribir por `package
version drift: numpy`; se comprobó la causa y se ejecutó el consolidador una
sola vez con `.venv-confirmatory/bin/python`, que coincide con el entorno
congelado. El incidente fue de entorno de auditoría, no un fallo científico.

Resultados de la misma llamada online que produce cada predicción:

- Accuracy media de 10 repeticiones: **0,94220**; desviación estándar descriptiva **0,00402**.
- Macro-F1 media entre folds: **0,94192**.
- Latencia media individual: **16,767 ms/llamada**.
- El paper reporta accuracy **0,967**: diferencia de **−2,48 puntos porcentuales**.
- No hay macro-F1 ni latencia publicada directamente comparable.

Etiqueta: **aproximación paper-like**, no reproducción fiel ni afirmación de
haber igualado los números del paper. Persisten split/semillas aproximados,
versiones/hardware distintos y el hecho de que las diez repeticiones no son
datasets independientes. No interpretar la SD como intervalo de confianza.

Artefactos auditables: `summary.json`, `fold_metrics.csv`,
`repetition_metrics.csv` y `provenance.json` en este directorio; cola fuente en
`../neshov_paperlike_fmd_10x10_queue_20261102_v1/`.
