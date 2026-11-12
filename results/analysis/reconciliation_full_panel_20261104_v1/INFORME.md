# Conciliación de comparadores del panel común — 04-11-2026

Se reconstruyeron **1.780 comparaciones por condición** y **230 comparaciones
por dataset** desde las llamadas guardadas: 47 condiciones completas de cada
uno de CellNN, HyTex y Neshov, y 37 condiciones completas de DeepLumina en los
cinco datasets que cerraron su cobertura. DeepLumina/DTD se deja fuera del
promedio del dataset porque una condición quedó en `requires_review`.

Para cada comparación se verificaron los IDs, las etiquetas y el SHA-256 de las
imágenes con los registros de los dos clasificadores locales; además, se
verificaron hashes de llamadas, estados y recibos. F1, accuracy y tiempo se
recalcularon a partir de las mismas llamadas. Las 230 filas se contrastaron
con los resúmenes locales independientes; los F1 y tiempos externos coinciden
con los resúmenes auditados previos. No hubo nuevas inferencias ni mediciones.

## Reserva científica de DeepLumina

Las **46/46 condiciones DeepLumina marcadas como completas en ejecución** tienen
al menos una línea `ConvergenceWarning: Liblinear failed to converge` en el log
de entrenamiento. DTD `s42_f3`, además, agotó 3.600 s y quedó en
`requires_review`. Después se inspeccionaron, sin entrenar ni inferir, los 46
modelos guardados y sus hashes: **1.653 de 2.441 clasificadores binarios**
alcanzaron `max_iter=10.000`, al menos uno en cada condición. El conteo de
clasificadores alcanzando el límite coincide con los avisos por condición.
En CUReT fueron 178/178 y en Outex 92/92; en FMD 41/690. DTD `s42_f3` no dejó
un clasificador terminado para inspeccionar. Las predicciones y los tiempos
existen y pueden trazarse, pero las comparaciones con DeepLumina quedan
**sujetas a revisión científica**: el impacto sobre F1 y tiempos no está
cuantificado. No se alteraron estados ni se reintentó ningún caso. Detalle y
hashes en `../deeplumina_niter_review_20261104_v1/` y logs en
`../deeplumina_convergence_review_20261104_v1/`.

Una inspección posterior del gradiente primal sobre los rasgos de entrenamiento
guardados está en `../deeplumina_stationarity_review_20261104_v1/INFORME.md`.
Es un indicador descriptivo, no la prueba dual de parada de Liblinear ni una
medida del cambio en F1; no hubo reentrenamiento ni inferencia sobre test.

## Ejemplo: política adaptativa con SVM

Cada celda es **Δ macro-F1 local − comparador / Δ ms local − comparador**.
Un ΔF1 positivo favorece al método local; un Δms negativo indica menor tiempo
local. Los tiempos son descriptivos: se midieron en fechas distintas y con
hardware compartido. † DeepLumina requiere la revisión anterior.

| Dataset | CellNN | HyTex | Neshov BEiTv2+MLP | DeepLumina † |
|---|---:|---:|---:|---:|
| FMD | +0,72995 / +8,97 | +0,23618 / +7,45 | +0,03547 / +21,74 | +0,12169 / −14,70 |
| CUReT | +0,30503 / +5,81 | +0,01533 / +4,42 | +0,00443 / +22,56 | +0,01033 / −16,17 |
| Outex-13 | +0,29202 / +10,42 | +0,03484 / +11,29 | +0,00828 / +25,72 | +0,02032 / −13,21 |
| SoilOriginal | +0,51757 / +5,50 | +0,08458 / +5,37 | +0,00944 / +19,31 | +0,06753 / −19,32 |
| KTH-TIPS2b | +0,36397 / −0,98 | +0,11314 / −0,02 | +0,01452 / +14,47 | +0,06462 / −20,61 |
| DTD | +0,65067 / +22,83 | +0,24270 / +20,84 | +0,06483 / +37,56 | **sin media: 9/10** |

La tabla completa de las cinco estrategias locales, dos clasificadores y
comparadores disponibles está en `comparison_by_dataset.csv`. De sus 230
filas descriptivas, 229 tienen ΔF1 positivo y una negativo: **Top-4/SVM en
Soil frente a Neshov**, −0,00370 F1 y +51,82 ms. Estas filas no son datasets
independientes ni prueban significación o dominancia universal. Para las
latencias, 214 filas tienen mayor media local y 16 menor; la interpretación
queda limitada por las fechas y el hardware compartido. Las comparaciones
DeepLumina conservan además la reserva de convergencia.

## Diferencias con el cuadro nuevo

`board_reconciliation.csv` contrasta las cifras del cuadro de defensa del
04-11 con lo reconstruido. Por ejemplo, CellNN FMD es **0,24765** en las
llamadas auditadas frente a **0,4329** en ese cuadro; CellNN Outex es
**0,63557** frente a **0,8282**; HyTex DTD está **10/10** con F1 **0,62415**
frente a **9/10 y 0,6363**. La fuente exacta de esas otras cifras no quedó
identificada en este análisis. El cuadro denomina Neshov a una variante
**LogReg**, mientras la corrida reconstruida es **BEiTv2+MLP**; no se deben
considerar el mismo método sin prueba adicional.

Archivos: `comparison_by_dataset.csv` (todas las parejas),
`board_reconciliation.csv` (discrepancias), `reference_results.json`,
`summary.json` y `provenance.json`. Las comparaciones por condición están en
los seis directorios `reconciliation_{fmd,curet,outex,soil,kth,dtd}_calls_20261104_v1`.
No se cambió el manuscrito ni el material preparado por el equipo.
