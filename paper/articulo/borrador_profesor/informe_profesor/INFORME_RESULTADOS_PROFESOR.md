# Informe de resultados y pruebas estadísticas

**Estado:** resumen preliminar para revisión del profesor  
**Fecha:** 2026-08-28  
**Alcance:** resultados CPU canónicos auditados; la replicación completa con
SVM-GPU/cuML está en ejecución.

## 1. Qué se comparó

Se compararon cinco estrategias: **Individual**, **Homogénea**, **GFS**
(greedy forward search), **Completa** (concatenación de todos los bloques) y
**Top-k** (control basado en los descriptores individuales mejor puntuados).

Los bloques principales son DTD, FMD, CUReT y Outex. En el análisis primario
cada dataset cuenta como un bloque; no se trataron los splits del mismo dataset
como problemas independientes.

### Cobertura de datasets

| Uso | Datasets | Unidad del análisis |
|---|---|---|
| Primario confirmatorio | DTD, FMD, CUReT, Outex | 4 bloques por dataset |
| Sensibilidad | DTD, FMD, CUReT, Outex | 8 bloques dataset-clasificador (SVM y ResMLP) |
| Extensión suplementaria | SoilOriginal, VisTexReference12 | resultados descriptivos; fuera de la inferencia principal |

SoilOriginal y VisTexReference12 no se incluyeron en las pruebas estadísticas
primarias existentes. Incorporarlos exigiría reconstruir la matriz completa,
justificar su comparabilidad y volver a aplicar las correcciones por
comparaciones múltiples.

## 2. Métricas

El archivo de métricas extendidas conserva:

- accuracy;
- balanced accuracy;
- precision macro;
- recall macro;
- macro-F1;
- AUC ROC one-vs-rest macro;
- tiempo de ajuste/predicción;
- dimensionalidad y descriptores seleccionados.

Las pruebas no paramétricas consolidadas se ejecutaron formalmente sobre
**macro-F1** y **accuracy**. Balanced accuracy, precision, recall y AUC están
disponibles como resultados descriptivos, pero todavía no debemos afirmar
significación estadística para ellas sin ejecutar sus matrices equivalentes.

### Extensión ejecutada con SCI2S

Como preparación para ampliar la inferencia, se ejecutaron `ControlTest` y
`MultipleTest` de SCI2S para las seis métricas disponibles: accuracy,
balanced accuracy, precision macro, recall macro, macro-F1 y AUC ROC
one-vs-rest macro. Las matrices y salidas LaTeX están organizadas en
`results/confirmatory/nonparametric/metrics_cpu/<métrica>/`, con archivos
separados para `primary` y `sensitivity`. Estas salidas deben revisarse en
conjunto con la discrepancia entre procedimientos y las correcciones por
comparaciones múltiples; no se resumirán como una única afirmación de
significación por métrica.

### Resumen provisional de `MultipleTest`

Se extrajeron las cuatro comparaciones contra Individual de cada salida. En el
análisis primario de cuatro datasets, **ninguna de las seis métricas** mostró
una comparación significativa después de Holm o Bergmann--Hommel. En la
sensibilidad de ocho bloques dataset-clasificador, GFS y Top-k frente a
Individual aparecen significativos con Holm para las seis métricas; este patrón
se mantiene como evidencia secundaria por la dependencia entre bloques.

La tabla completa, con p sin ajustar, Holm y Bergmann--Hommel, está en
`results/confirmatory/nonparametric/metrics_cpu/multipletest_summary_vs_individual.csv`.

## 3. Pruebas utilizadas

Se aplicaron Friedman, Iman-Davenport, Friedman aligned ranks y Quade, junto
con comparaciones post-hoc/control y correcciones por comparaciones múltiples
(incluyendo Holm). El nivel nominal fue `alpha = 0,05`.

## 4. Resultado primario auditado: macro-F1

| Prueba | Estadístico | p | ¿Significativo? |
|---|---:|---:|---|
| Friedman | χ²(4) = 6,600 | 0,1586 | No |
| Iman-Davenport | F(4,12) = 2,106 | 0,1429 | No |
| Friedman aligned ranks | χ²(4) = 3,237 | 0,5190 | No |
| Quade | F(4,12) = 2,233 | 0,1264 | No |

Los menores p sin ajustar en las comparaciones post-hoc fueron Top-k vs.
Individual (`p = 0,02535`) y GFS vs. Individual (`p = 0,04417`). En el
contraste específico de **Friedman Aligned Ranks** contra el control de mejor
ranking, la comparación mejor selección vs. Individual aparece con `p ajustado
= 0,02864`. Este resultado debe describirse como una señal dependiente del
procedimiento, no como una conclusión global, porque ninguno de los cuatro
contrastes omnibus primarios fue significativo.

Accuracy también está incluida en el CSV estadístico consolidado. Su lectura
debe seguir el mismo principio: las conclusiones post-hoc se basan en los p
ajustados, no en los p sin ajustar.

## 5. Sensibilidad dataset-clasificador

La sensibilidad usa ocho bloques dataset-clasificador. Tiene menor autoridad
confirmatoria porque las dos observaciones de cada dataset comparten datos.

Para macro-F1 se obtuvieron:

| Prueba | p | Lectura |
|---|---:|---|
| Friedman | 0,02148 | significativo nominalmente |
| Iman-Davenport | 0,01183 | significativo nominalmente |
| Friedman aligned ranks | 0,16393 | no significativo |
| Quade | 0,006535 | significativo nominalmente |

Estas señales se presentan como sensibilidad/descripción, no como evidencia
confirmatoria principal. La dependencia entre bloques impide tratarlas como
una replicación independiente de cuatro datasets adicionales.

## 6. Análisis focalizado contra Individual (CPU)

Para responder directamente a la pregunta “¿las estrategias combinadas
mejoran al mejor descriptor individual?”, se extrajeron las cuatro
comparaciones contra Individual y se recalculó Holm sobre ese conjunto de cuatro
hipótesis. El resultado está en
`results/confirmatory/nonparametric/focused_vs_individual_cpu.csv`.

En el análisis primario de cuatro datasets, ninguna de las cuatro comparaciones
fue significativa tras esta corrección focalizada:

| Métrica | Comparación con menor p ajustado | p Holm (4 hipótesis) | Lectura |
|---|---|---:|---|
| macro-F1 | Top-k vs. Individual | 0,1014 | no significativa |
| accuracy | Top-k vs. Individual | 0,1014 | no significativa |

En la sensibilidad dataset-clasificador, las cuatro comparaciones resultan
significativas con Holm focalizado, pero esa evidencia se mantiene como
exploratoria por la dependencia entre bloques. No se utilizará para reemplazar
la conclusión primaria.

## 7. Conclusiones defendibles

1. Las estrategias combinadas suelen superar descriptivamente al mejor
   descriptor individual en varios datasets.
2. En los cuatro datasets independientes no se detectó una diferencia global
   estadísticamente significativa entre las cinco estrategias.
3. No hay base para afirmar que GFS sea establemente superior a Top-k,
   concatenación completa o selección homogénea.
4. Las señales de la sensibilidad no sustituyen la evidencia primaria.
5. Precision, recall, balanced accuracy y AUC deben presentarse por ahora como
   resultados descriptivos, no como diferencias significativas.
6. Las conclusiones inferenciales actuales se limitan a DTD, FMD, CUReT y
   Outex. SoilOriginal y VisTexReference12 solo aportan evidencia suplementaria
   descriptiva en esta etapa.

## 8. Trabajo pendiente

- finalizar todos los splits SVM-GPU/cuML;
- reconstruir las tablas primarias con ese backend;
- ejecutar las pruebas no paramétricas para las métricas adicionales que se
  quieran inferir;
- aplicar las correcciones por comparaciones múltiples;
- actualizar el borrador solo con los resultados finales y su trazabilidad.

## 9. Fuentes

- `results/confirmatory/extended_metrics/nested_fold_metrics.csv`
- `results/confirmatory/nonparametric/all_sci2s_tests.csv`
- `results/confirmatory/nonparametric/COMPARACION_REPORTE_PREVIO.md`
- `paper/articulo/REPORTE_TESTS_NO_PARAMETRICOS.md` (histórico)
