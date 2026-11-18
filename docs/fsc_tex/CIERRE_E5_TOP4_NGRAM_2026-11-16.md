# Cierre E5: Top-4 más N-gramas — 16 de noviembre de 2026

La comparación específica quedó completa y auditada: **47/47 condiciones SVM**, seis datasets, las mismas particiones y los mismos cuatro bloques en cada par. Se comparó Top-4 con Top-4 más `rgb_ngram_svd`; la SVD aleatorizada se ajustó solo con entrenamiento. Se congelaron las versiones, parámetros, presupuesto y 109 huellas antes de ejecutar; se guardaron predicciones por fila, resultados, modelos SVM y SVD con hashes. Los binarios de modelos permanecen locales por las reglas del repositorio.

| Dataset | Condiciones | Accuracy Top-4 | Accuracy Top-4 + Ng | Diferencia (pp) |
|---|---:|---:|---:|---:|
| DTD | 10 | 87,0266 % | 86,3564 % | −0,6702 |
| FMD | 15 | 98,2333 % | 98,0667 % | −0,1667 |
| CUReT | 2 | 99,8574 % | 99,8753 % | +0,0178 |
| Outex | 1 | 92,9412 % | 96,1765 % | +3,2353 |
| Soil | 15 | 92,7206 % | 92,5740 % | −0,1466 |
| KTH-TIPS2b | 4 | 95,7492 % | 96,2753 % | +0,5261 |

La diferencia equiponderada entre datasets es **+0,466 puntos porcentuales**. No implica una ganancia uniforme: tres datasets aumentaron y tres disminuyeron. No se presenta una prueba de significancia ni intervalos. Las particiones comparten imágenes y Outex tiene una sola condición con reserva de procedencia.

Los 27 casos que coinciden con E1 reprodujeron exactamente las 31.984 predicciones directas y sus índices. Para las 20 condiciones restantes solo se cotejó la accuracy con la fila Top-4 archivada: no hay referencia E1 por predicción. Esas 20 particiones FMD/Soil se reconstruyeron con el separador actual; se cotejaron las 10 reconstrucciones de referencia de semilla 42 contra E1. Los tests ya se habían observado, por lo que este es un análisis exploratorio.

Se reutilizaron embeddings y conteos cacheados; los hashes congelados comprueban inmutabilidad, no que cada conteo corresponda correctamente a cada imagen. No se realizó extracción desde RGB ni se midió latencia online. Las reservas KTH/DTD y Outex siguen vigentes. Precisión macro, recall macro y macro-F1 están en la [tabla de métricas](../../results/analysis/e5_secondary_complete_20261116_v1/summary.json).

Evidencia: [protocolo congelado](../../results/analysis/e5_execution_frozen_20261116_v1/manifest.json), [estado de la corrida](../../results/analysis/e5_top4_plus_ngram_20261116_v1/status.json), [auditoría completa](../../results/analysis/e5_top4_plus_ngram_audit_20261116_v1/summary.json), [comparación con E1](../../results/analysis/e5_direct_e1_audit_20261116_v1/summary.json) y [particiones candidatas](../../results/analysis/e5_candidate_partitions_20261116_v1/partitions.json).
