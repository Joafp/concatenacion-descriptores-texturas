# Métricas compartidas para el paper

Corte local preparado el 18-11-2026 después de incorporar `origin/main` a `a95307c`. No se ejecutaron experimentos nuevos ni se modificaron las fuentes originales. Los archivos incluyen **más que accuracy**: precisión y recall macro, macro-F1, balanced accuracy y AUC cuando estaban disponibles; tiempos y percentiles cuando fueron medidos, matrices de confusión, datos por clase, cobertura y resúmenes. No todas las métricas existen para cada método/dataset.

## Tablas principales

- [Métricas del panel propio y HyTex ajustada](../analysis/hytex_paper_metrics_20261116_v3/dataset_metrics.csv): accuracy, precisión, recall y F1 macro, media/mediana/p95 de latencia y cobertura. Las [matrices y métricas por clase de HyTex](../analysis/hytex_paper_metrics_20261116_v3/) son acumuladas por llamadas, no imágenes físicas independientes.
- [Comparadores externos](../analysis/external_paper_metrics_20261116_v2/external_dataset_metrics.csv): mismas familias de métricas para 23 combinaciones completas. [Cobertura](../analysis/external_paper_metrics_20261116_v2/coverage.json). DeepLumina conserva avisos de convergencia en varios datasets y DTD 9/10; no se genera media completa con ese faltante.
- [Métricas confirmatorias históricas por fold](../confirmatory/extended_metrics/nested_fold_metrics.csv): incluye balanced accuracy y AUC macro OvR cuando se pudo calcular; interpretar según su propio protocolo, no como si fuera el panel online posterior.
- [E1 y E2](../analysis/top4_fixed_kth_completion_audit_20261115_v1/README.md): tablas y controles por condición. El ahorro de E1 es proyectado por componentes, no latencia física end-to-end.
- [E4 ResMLP, auditoría 27/27](../analysis/e4_resmlp_complete_audit_20261116_v1/summary.json): bloques seleccionados para SVM y evaluados con ResMLP; sin latencia física.
- [E5 Top-4 + N-gramas, auditoría 47/47](../analysis/e5_top4_plus_ngram_audit_20261116_v1/summary.json) y [resumen secundario](../analysis/e5_secondary_complete_20261116_v1/summary.json): resultados exploratorios sin latencia online.
- [HyTex FMD robustez](../analysis/hytex_fmd_robustness_20261116_audit_v1/summary.json): perturbaciones locales, no una comparación emparejada con Top-4.
- [Neshov FMD 10×10](../analysis/neshov_paperlike_fmd_10x10_consolidated_20261103_v1/INFORME.md): aproximación, no reproducción exacta del paper.
- [Tabla descriptiva de accuracy](../analysis/sota_reporte_20261117_v1/tabla_accuracy.md): para localizar la comparación anterior; no reemplaza las tablas multimétrica anteriores.

## Inventario y límites

[inventario.json](inventario.json) registra ruta de origen, ruta disponible en Git, SHA-256, tamaño y situación de cada archivo incluido en el barrido. Los archivos ya versionados mantienen su ubicación; los nuevos no ignorados se comparten en sus rutas originales. Los archivos de métricas de directorios ignorados se copiaron sin cambiar bytes a `archivos_ignorados/` con nombre SHA-256, y el inventario identifica su fuente; pueden ser parciales o intermedios y **no deben sumarse como corridas independientes**.

La selección automática busca nombres de métricas, resúmenes, cobertura, confusión y latencia en texto bajo `results`, más los directorios canónicos arriba. Excluye logs, checkpoints, staging, cachés y smoke: no garantiza capturar toda tabla con otro nombre. El paquete incluye archivos históricos y parciales además de los auditados; usar siempre sus estados y protocolos. No incluye datasets, embeddings ni pesos excluidos de Git. No inferir igualdad de preprocesamiento ni comparar tiempos de sesiones distintas como medición emparejada.
