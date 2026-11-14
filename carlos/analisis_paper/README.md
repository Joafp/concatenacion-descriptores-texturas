# Cálculos propios del paper Top-k directo vs activación por margen

Fecha: 2026-11-14. Son tres cálculos hechos sobre resultados que ya estaban en el repo. No hay ajustes de modelos, extracciones ni mediciones nuevas.

| Archivo | Qué contiene | Fuente |
|---|---|---|
| `estadistica_3_metodos.txt` | Friedman, Iman–Davenport, post hoc con Holm y Wilcoxon exacto para Individual, Completa-22 y Top-4, con cada clasificador | `results/analysis/selection_stats/{svm,resmlp}_metodos.csv` |
| `stats3.awk` | Script del cálculo anterior: `awk -F, -v M="Individual,Completa-22,Top-4" -f stats3.awk <csv>` | — |
| `etapa_barata_oof.csv` | Macro-F1 OOF del entrenamiento de la etapa barata elegida sola, de la cascada, de Top-k directo y de ResNet-50, en las 27 condiciones | `results/exploratory/topk_cascade/cheap_stage_selected_primary22/*_selection_pretest.json` |
| `latencia_p95_reunida.csv` | Media, mediana y percentil 95 de la latencia por dataset, clasificador y política, calculados sobre todas las llamadas | Las 94 trazas de `results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv` |

## Detalles de cálculo

- **Friedman con seis datasets:** el valor *p* asintótico es grueso. Además del asintótico, se informa el exacto, obtenido enumerando las 46.656 asignaciones de rangos (6 datasets, 3 métodos).
- **Percentil 95:** interpolación lineal, igual que `numpy.percentile` por defecto. Se calcula sobre las llamadas reunidas de cada grupo, sin promediar percentiles por condición. Las medias y medianas reproducen exactamente las de la tabla del panel del paper.
- **Etapa barata en test:** su macro-F1 en test no está guardado para la cascada con base elegida. Los archivos de predicciones solo registran la cascada, la cascada con ResNet-50 y Top-k directo. Calcularlo requeriría volver a ajustar clasificadores, así que se informa el macro-F1 OOF del entrenamiento.
