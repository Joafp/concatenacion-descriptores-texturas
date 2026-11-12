# Búsqueda local de las cifras del cuadro de defensa

## Resultado

La procedencia de las cifras discordantes del cuadro
`external_sota_full_panel_summary_20261104_v1/summary.json` **sigue sin estar
establecida**. El cuadro no contiene rutas o hashes de las predicciones que
respalden cada celda. Se conservó su archivo y se contrastó con las llamadas
y recibos de los paneles ya auditados; las comparaciones verificadas están en
`comparison_by_dataset.csv` y las diferencias en `board_reconciliation.csv`.

Como búsqueda adicional se inspeccionaron **1.111 archivos** de texto de hasta
5 MB en `scripts/`, `src/`, `results/analysis/` y
`results/exploratory/reference_papers/`, excluyendo los subdirectorios
`jobs/` y `tasks/`, el cuadro bajo revisión y los informes de conciliación que
lo citan. Se buscaron las cadenas decimales exactas `0.4329`, `0.6363`,
`0.8282` y `0.8397`:

- `0.4329` y `0.6363`: no se encontraron en esa búsqueda acotada.
- `0.8282`: apareció en una vista de predicciones de `integration_v9`, ajena a
  la agregación auditada de CellNN en Outex; una coincidencia de cadena no
  acredita que sea la fuente del cuadro.
- `0.8397`: apareció en resultados de otras condiciones/datasets, sin
  identificar la celda Neshov/DTD con cabeza LogReg.

Una búsqueda de `LogisticRegression` en los archivos Python de primer nivel de
`src/` y `scripts/` encontró un uso en
`scripts/run_fsc_tex_phase1_feasibility.py`, pero no una implementación Neshov
LogReg en ese alcance. Esto **no demuestra que no exista** código o evidencia
en otra carpeta, en archivos excluidos, con otra representación decimal o
fuera del workspace. Tampoco determina por sí solo el origen de la diferencia.

## Cómo cerrar la trazabilidad

Para considerar una celda alternativa, recuperar la receta de esa variante,
manifiesto y hashes, identificadores de dataset/seed/fold, predicciones,
etiquetas y tiempos de las mismas llamadas; comparar IDs y SHA-256 de imagen
con el panel local. Una cabeza LogReg se informa separadamente de la MLP ya
auditada. Si no se encuentra esa cadena, conservar la celda como **no
verificada** y usar el tablero reconstruido de llamadas completas, con las
reservas científicas de DeepLumina y las reservas de tiempo KTH/DTD.
