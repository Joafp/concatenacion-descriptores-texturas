# ARS REV-05/06: variación observada y sensibilidad de resultados guardados

Se conserva el cierre E1 de 27 condiciones y seis datasets y los archivos
estáticos canónicos. Este análisis no ajusta modelos, no extrae características,
no produce predicciones de modelo ni mide tiempos.

## REV-05: diferencias E1

[Cada condición](e1_condition_differences.csv), [rangos/cuantiles por dataset](e1_dataset_observed_ranges.csv)
y [exclusión de un dataset](e1_leave_one_dataset_out.csv).

La diferencia accuracy margen−directo es +0,0132211 puntos porcentuales en
la media equiponderada de seis datasets. Al excluir uno por vez, varía de
−0,0192224 (sin Soil) a +0,0746888 pp (sin Outex). Estas exclusiones cambian
el conjunto objetivo; no reemplazan el resultado de seis datasets ni eligen
un conjunto favorable. Ningún p de esos diagnósticos resulta menor que 0,05.

Los cuantiles usan interpolación lineal de las condiciones observadas y
describen el archivo. Las particiones solapadas no son réplicas independientes;
los rangos no son intervalos de confianza ni límites poblacionales. Outex
tiene una sola condición: sus cinco cuantiles coinciden por construcción y
no estiman variabilidad de particiones o de futuros dominios.

## REV-06: contraste estático de accuracy sin KTH

[Estadísticos completos](static_accuracy_sensitivity.json), [Friedman](static_accuracy_sensitivity_friedman.csv)
y [pares/Holm](static_accuracy_sensitivity_pairs.csv).

Se reutiliza **el mismo helper exacto y la misma familia de tres pares** del
contraste principal Individual/Completa-22/Top-4, separada por SVM y ResMLP.
Las seis medias originales reproducen exactamente sus p de Friedman y de
Wilcoxon/Holm guardados. Después se excluye KTH del archivo estático, sin
sustituirlo por la variante del cierre E1.

Con cinco datasets y 7.776 permutaciones de rangos, Friedman exacto da
0,1242283951 para SVM y 0,5216049383 para ResMLP. Ningún par de accuracy es
significativo tras Holm (mínimos: SVM 0,1875; ResMLP 1). Esto no demuestra
equivalencia. Los candidatos, bibliotecas y medias históricas no se cambian.

Las exclusiones de Outex y de KTH+Outex también están disponibles como
sensibilidad diagnóstica. Su cálculo no demuestra una desalineación de
datos ni autoriza omitir Outex en las tablas canónicas.

## Trazabilidad y reproducción

[Resumen](summary.json) · [Fuentes y salidas con hashes](provenance.json).
Cuatro tablas para el manuscrito están en
`paper/generated_ars_revision_20261115/`; no se modificó ningún capítulo.

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 MPLBACKEND=Agg \
.venv-confirmatory/bin/python scripts/analyze_ars_existing_results_20261115.py \
  --output <directorio-nuevo-de-analisis> --generated <directorio-nuevo-de-tablas>
```

Pasaron cuatro pruebas de estimando equiponderado, cobertura, familias,
valores exactos y conservación de hashes. No se atribuye a estas pruebas una
validación de generalización externa ni de latencia física.
