# Cálculos propios del paper Top-k directo vs activación por margen

Actualizado: 2026-11-15. Estos cálculos se hicieron sobre resultados que ya estaban en el repo. No hay ajustes de modelos, extracciones ni mediciones nuevas.

Desde el 15-11 el paper usa **accuracy** como métrica principal, igual que la tesis, y macro-F1 como complemento. Los archivos del 14-11 en macro-F1 se conservan como antecedente.

## Vigentes (accuracy, 2026-11-15)

| Archivo | Qué contiene | Fuente |
|---|---|---|
| `reglas_k.txt` / `reglas_k.awk` | Tabla de reglas para elegir k. El k sale de la curva interna de macro-F1 (la métrica del ranking) y se informa la accuracy externa resultante. También incluye la versión en macro-F1, que reproduce la tabla anterior | `results/exploratory/k_sweep/` y `results/exploratory/resmlp/k_sweep/` (`k_sweep_inner.csv`, `k_sweep.csv`) |
| `estadistica_3_metodos_accuracy.txt` / `no_inferioridad.awk` | Friedman, Iman–Davenport, post hoc con Holm y Wilcoxon exacto para Individual, Completa-22 y Top-4, más la no inferioridad de Top-4 frente a Completa-22 (δ = 0,01) | `results/analysis/thesis_accuracy_primary_20261115_v3/static_accuracy_{svm,resmlp}.csv` |
| `e1_condiciones.csv` / `e1_extraer.ps1` | Una fila por cada una de las 27 condiciones de E1: ruta elegida, ruta con ResNet-50, Top-4 directo, control aleatorio y etapa barata sola en test | `result.json` de cada condición, listados en `results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e1_conditions.csv` |
| `e1_medias_por_dataset.csv` / `e1_contrastes.txt` | Medias por dataset de la cascada, la ruta con ResNet-50, Top-4 directo y Completa-22 (semilla 42), con los Wilcoxon exactos, Holm y el control aleatorio | `e1_condiciones.csv` y la matriz principal (`nested_fold_results.csv`, método `full_concat`) |
| `e1_no_inferioridad.txt` / `e1_ni_entrada.csv` | No inferioridad de la cascada frente a Top-4 directo (δ = 0,01 y 0,005) e IC 95 % de la diferencia media. Se definió después de observar E1 y reutiliza el margen de la evaluación estática | `e1_medias_por_dataset.csv` |
| `latencia_p95_reunida.csv` | Media, mediana y percentil 95 de la latencia por dataset, clasificador y política, sobre todas las llamadas (no depende de la métrica) | Las 94 trazas de `results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv` |
| `e1_por_imagen.csv` / `e1_por_imagen.sh` | Una fila por imagen de test en las 27 condiciones de E1 (31.984): clase real y predicciones de la etapa barata, de Top-4 directo y de la cascada, y si la imagen se escaló. Verificado: la cascada cumple la regla en todas las filas y las accuracies coinciden exactamente con las almacenadas (agregado 18-11) | `scores_predictions.json.gz` de cada condición |
| `e1_analisis_por_imagen.awk` → `e1_mcnemar_compuerta.csv`, `e1_resumen_por_dataset.csv`, `e1_confusion.csv`, `e1_por_clase.csv` | McNemar exacto por condición con Holm, kappa de Cohen, media y DE entre condiciones, calidad de la compuerta (acierto de la base en no escaladas, errores de la base escalados, corregidos y perdidos al escalar), matrices de confusión sumadas y métricas por clase. Alimentan la Tabla 10 y la Figura 4 del paper | `e1_por_imagen.csv` |
| `stats3.awk` | Script de Friedman/Wilcoxon: `awk -F, -v M="Individual,Completa-22,Top-4" -f stats3.awk <csv>` | — |

Las sensibilidades del 16-11 no se recalcularon acá; se toman de `results/analysis/ars_revision_existing_analyses_20261115_v1/`. Son la evaluación estática sin KTH o sin Outex, y las diferencias de E1 por condición y dejando un dataset fuera. Joaquín las calcula en puntos porcentuales y el paper las informa en fracción.

Las medias de E2 (compuertas) se toman directamente de `results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e2_complete_dataset_means.csv` y `e2_statistics.csv`. Las del panel online y de los métodos externos en accuracy, de `results/analysis/thesis_accuracy_primary_20261115_v3/online_means.csv` y `paper/generated_accuracy_primary_20261115_v3/externos_accuracy.tex`.

## Antecedente (macro-F1, 2026-11-14)

| Archivo | Qué contiene |
|---|---|
| `estadistica_3_metodos.txt` | La misma estadística de tres métodos en macro-F1 |
| `etapa_barata_oof.csv` | Macro-F1 OOF de la etapa barata de la cascada anterior (Top-k archivada). Ya no se usa en el paper: E1 guarda la etapa barata sola en test |

## Detalles de cálculo

- **Friedman con seis datasets:** el valor *p* asintótico es grueso. Además del asintótico se informa el exacto, de 46.656 asignaciones de rangos (6 datasets, 3 métodos).
- **No inferioridad:** cota inferior unilateral al 95 % con t de Student (5 grados de libertad) y Wilcoxon exacto unilateral sobre d + δ. El margen δ = 0,01 se fijó para macro-F1; aplicarlo a accuracy es posterior al cambio de métrica.
- **Wilcoxon de E1:** sobre las seis medias por dataset. La familia de Holm es cascada frente a Top-4 directo, frente a la ruta con ResNet-50 y frente a Completa-22.
- **Percentil 95:** interpolación lineal, igual que `numpy.percentile` por defecto, sobre las llamadas reunidas de cada grupo.
