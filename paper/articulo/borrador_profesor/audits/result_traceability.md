# Trazabilidad de resultados del manuscrito

Fecha de verificación: 2026-08-11

## Cobertura

| Bloque | Condiciones | Evaluaciones | Controles | Fuente |
|---|---:|---:|---:|---|
| DTD | 20 | 80 | 2.000 aleatorios + 20 top-k | `results/confirmatory/nested_fold_results.csv` |
| FMD | 30 | 120 | 3.000 aleatorios + 30 top-k | `results/confirmatory/nested_fold_results.csv` |
| CUReT | 4 | 16 | 400 aleatorios + 4 top-k | `results/confirmatory/nested_fold_results.csv` |
| Outex oficial | 2 | 8 | 200 aleatorios + 2 top-k | `results/extensions/outex13_official1360/` |
| **Total** | **56** | **224** | **5.600 aleatorios + 56 top-k** | unión por clave externa |

## Afirmaciones centrales

| Afirmación | Evidencia | Estado |
|---|---|---|
| GFS supera en media al individual seleccionado en las seis configuraciones DTD/FMD/CUReT | `results/confirmatory/paired_comparisons.csv` | alineada |
| GFS y top-k no muestran ventaja agregada en el bloque principal (25/25/4) | `results/topk_individual_control/paired_gfs_vs_topk.csv` | alineada |
| Outex oficial contiene 1.360 imágenes, 68 clases y split 680/680 | manifiesto y auditoría en `results/extensions/outex13_official1360/` | alineada |
| La reproducción de los dos n-gramas alcanza 0,963235 y 0,952941 | `results/extensions/rgb_pixel_ngrams_outex13_official/results.csv` | alineada |
| N-grama + 20 bloques alcanza 0,969118 de exactitud | mismo directorio, predicciones y `validation.json` | alineada |
| La diferencia de cuatro aciertos no demuestra superioridad | bootstrap pareado y McNemar exacto en el mismo directorio | alineada |
| En Outex, completa supera a GFS con SVM y ResMLP | `nested_fold_results.csv` oficial; deltas 0,014629 y 0,011833 | alineada |
| GFS y top-k terminan 26/26/4 sobre 56 condiciones | `results/topk_individual_control/paired_gfs_vs_topk.csv` | alineada |

## Límites de interpretación

- Macro-F1 es primario en el protocolo general; exactitud es primaria en la
  reproducción del antecedente de RGB Pixel N-grams.
- Los intervalos entre particiones repetidas son descriptivos.
- Para Outex oficial, n=1: se reporta el efecto observado y se omite inferencia
  split-level.
- Los controles aleatorios usan el test y se interpretan como calibración
  descriptiva posterior, no como contraste confirmatorio global.
