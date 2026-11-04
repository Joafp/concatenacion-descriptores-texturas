# Extensión HyTexNet ADAPTADO a SoilOriginal

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: ejecución técnica de extensión autorizada, sin ajuste por test.
- Origin Date: 2026-11-02.
- Verification Status: fijado antes de extracción/fit/predicciones Soil.
- Version Label: hytex_soil_adaptation_v1.

Hereda íntegro PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md: RGB128,
descriptor514+DenseNet121GAP1024 congelado offlineFP32, cabeza256/ReLU/dropout0.5,
Adam0.001/wd0.0001/betas0.9/0.999,100épocas/batch32/semilla entrenamiento42,
última época. No ajuste por resultados ya observados de otros datasets.

SoilOriginal:1140filas,7clases,semillas42/123/2026 y5folds archivados cada una.
Las15 condiciones usan los índices exactos del panel local, concordantes entre
SVM/ResMLP. Los cinco tests de cada semilla cubren cada fila una vez. Total3420
llamadas, folds de228 salvo seed123/fold1=229 yfold3=227. Conservar grupos y
conteos, no regenerar particiones ni omitir filas para igualar tamaños.

Normalización de esquema en CSV nuevo: source_path→path,source_sha256→sha256,
label textual→índice por primera aparición, manteniendo etiqueta original,
orden,row_id,grupos y bytes. Verificar el array de etiquetas canónico completo
y su hash contra30estados locales, cada bloque policy de verdad archivada,
hashes de1140imágenes y manifiesto. No usar predicciones como etiquetas ni
embeddings históricos como features HyTex. La corrección DeiT de nuestros
comparadores Soil se mantiene declarada, sin pretensión de representación común.

Fuentes/pesos/particiones/paquetes congelados antes de despacho. Cuatro etapas
del runner sellado: extract batch1,gate first/lastfit batch1→batch1≤1e-4 con
evidencia,train,online,audit. Primera auditoría habilita14restantes. Cinco
warmupsfit excluidos, una llamada archivo-a-clase por imagen externa, sin
cachéfeatures online. F1 y tiempos de mismas llamadas. GlobalGPUlock,CPU2hilos,
sin fits/extracciones concurrentes. Timeouts7200/1800/14400/300s,ventana12h.
Fallo científico requiere revisión sin retry, relajar tolerancias ni método.

Consolidar únicamente15/15 y3420llamadas: F1 medio de condiciones, tiempos
ponderados por llamadas reales. Comparar ambos heads×cinco métodos, conservar
pérdidas y ganancias. Hardwarecompartido/fechas distintas, no comparación
temporal aislada ni inferenciaestadística. Es adaptación local completa, no
reproducción de porcentajes publicados. No repetir panelpropio,FMD,CUReT,DTD,
Outex requires_review ni Neshov fallido; no cambios al manuscrito/commits/push.
