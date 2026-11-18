# Cierre E4: Top-4 directo y activación por margen con ResMLP

La corrida completó y auditó 27/27 condiciones, con seis datasets. Se mantuvieron
los cuatro descriptores elegidos en E1 y sus mismas particiones; esto permite
examinar el cambio de clasificador, pero no equivale a seleccionar un Top-4
propio de ResMLP. La selección de ruta usa macro-F1 fuera de fold de
entrenamiento; la métrica principal reportada es accuracy. Los datos de prueba
ya habían sido observados, por lo que la evaluación es exploratoria.

| Dataset | Condiciones | Accuracy Top-4 directo | Accuracy ruta seleccionada | Diferencia (pp) |
|---|---:|---:|---:|---:|
| DTD | 10 | 86,638 % | 86,707 % | +0,069 |
| FMD | 5 | 97,300 % | 97,300 % | 0,000 |
| CUReT | 2 | 99,857 % | 99,857 % | 0,000 |
| Outex | 1 | 94,118 % | 93,676 % | −0,441 |
| Soil | 5 | 91,842 % | 91,842 % | 0,000 |
| KTH | 4 | 95,918 % | 96,086 % | +0,168 |

Son medias por condición, no evidencia de equivalencia ni significancia.
Outex tiene una condición y conserva su reserva de procedencia; KTH y DTD
conservan las reservas documentadas. La auditoría verificó hashes, logits,
predicciones, máscaras y métricas, y reconstruyó la selección de entrenamiento.
La extracción de imágenes no se repitió y no se midió latencia física. El
fin de entrenamiento por paciencia o límite de épocas no demuestra convergencia.

Fuentes: `results/analysis/e4_resmlp_fixed_20261116_v1/manifest.json`,
`results/analysis/e4_resmlp_fixed_20261116_v1/status.json` y
`results/analysis/e4_resmlp_complete_audit_20261116_v1/summary.json`.
