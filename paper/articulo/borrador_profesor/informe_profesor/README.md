# Informe de resultados para revisión del profesor

Este directorio reúne un resumen legible de los experimentos y pruebas
estadísticas realizados hasta el momento.

## Archivo principal

- [`INFORME_RESULTADOS_PROFESOR.md`](INFORME_RESULTADOS_PROFESOR.md): resumen de
  métricas, diseño estadístico, resultados significativos y conclusiones.

## Fuentes reproducibles

- `results/confirmatory/extended_metrics/nested_fold_metrics.csv`: métricas
  extendidas por condición.
- `results/confirmatory/nonparametric/all_sci2s_tests.csv`: salida consolidada
  de las pruebas no paramétricas y sus ajustes por comparaciones múltiples.
- `results/confirmatory/nonparametric/focused_vs_individual_cpu.csv`: análisis
  focalizado de las cuatro estrategias frente a Individual, con Holm aplicado
  sobre esas cuatro hipótesis.
- `results/confirmatory/nonparametric/COMPARACION_REPORTE_PREVIO.md`: auditoría
  y comparación con el reporte histórico.

El lote SVM-GPU sigue ejecutándose. El resumen estadístico corresponde al
conjunto CPU canónico previamente auditado hasta que finalice la replicación.

La inferencia principal cubre DTD, FMD, CUReT y Outex. SoilOriginal y
VisTexReference12 quedan identificados como extensiones suplementarias
descriptivas hasta que se reconstruya una matriz estadística específica.

Las salidas LaTeX para todas las métricas están en
`results/confirmatory/nonparametric/metrics_cpu/`, separadas por métrica y
alcance (`primary` o `sensitivity`).

El resumen de las comparaciones contra Individual está en
`results/confirmatory/nonparametric/metrics_cpu/multipletest_summary_vs_individual.csv`.
