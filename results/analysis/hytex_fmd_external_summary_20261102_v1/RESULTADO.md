# FMD completo: HyTexNet adaptado y panel local

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: reagregación descriptiva y auditoría, no inferencia estadística.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: ANALYZED desde3000llamadas con recibos completos.
- Version Label: hytex_fmd_external_summary_v1.

15/15condiciones (3semillas×5folds),3000llamadas. No son15datasets ni3000
imágenes distintas:1000imágenes deFMD en tres particiones por semilla. Fuente
de método: HyTexNetADAPTADO, configuración local fijada; no código de autores,
ni reproducción de sus porcentajes/hiperparámetros. Cambios locales explícitos
en PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md, fijados antes de las predicciones.

Reagregación scripts/consolidate_hytex_fmd_external.py:7tests pasan, exit0.
Valida15identidades,60recibos, salidas y hashes, cadenaextract→train→online→audit,
particiones e integridad de predicciones/logits/tiempos, y calculaF1 desde llamadas.
Verifica tabla local congeladaSHA256bd490536bd178fa3f329257d991639c0791865dedca00711bb66ada988fc9838.
150comparaciones por condición,10resúmenes dataset/head/método en CSV;
ninguna condición omitida por desempeño.

| Sistema | Media de F1macro por condición | Media de ms de todas sus llamadas |
| --- | ---: | ---: |
| HyTexNetADAPTADO, cabeza propia | 0.741417 | 31.180760 |
| Nuestro adaptativoSVM | 0.977600 | 38.629834 |
| Nuestro adaptativoResMLP | 0.975970 | 36.354072 |

En esta comparaciónFMD nuestro adaptativo tiene mayorF1medio, pero no menor
latenciamedia: deltaF1+.236184SVM y+.234553ResMLP, latenciasmásaltas. Esto no
demuestra dominancia calidad–latencia ni superioridad sobre el método original.
Todos los otroscontroles permanecen en comparison_dataset.csv, no solo los
puntos favorables. El costo de biblioteca22 no se oculta ni se atribuye al rival.

F1 y latencia de cada sistema corresponden a sus mismas llamadas online. Las
mediciones local y externa ocurrieron en fechas/momentos diferentes y hardware
compartido: no comparación temporal contemporánea aislada. Mismas filas externas,
semillas y pliegues; cabezas diferentes son sistemas completos distintos. No
testeoinferencial, significancia, noinferioridad ni margen de pérdida elegido
después de observar. Semillas/folds no son dominios independientes.

summary.json SHA25643ca6a521b0a03cb0c701d6a587398f5e4d8cac13d78d881b926991184aa9dc8.
provenance.json conserva fuentes/artefactos. Panel externoactualcubreUNdataset,
no los seis. Neshov permanece requiere revisión, sin retries ni sustitución
porHyTex. No cambios a manuscrito ni commits/push.
