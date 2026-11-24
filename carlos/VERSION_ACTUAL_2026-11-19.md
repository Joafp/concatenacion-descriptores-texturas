# Versión actual del paper: 19 de noviembre de 2026

El usuario entregó [main_actual_2026-11-19.tex](main_actual_2026-11-19.tex) como la versión actual del paper. Es una copia exacta del archivo recibido; SHA-256 `5de5c8d9879abbc270b0d2e38ef1236f066acde4670b70304a4ee67989a20d7e`. No se ha modificado su contenido ni sustituido `main.tex`, que se preserva como versión anterior de referencia.

El archivo declara plantilla Elsevier CAS Single Column, `references.bib` y gráficos bajo `figures/`. Se preparó una [copia compilada para revisión](../results/analysis/paper_actual_20261119_v1/main.pdf), sin modificar el TEX recibido. Las ocho imágenes KTH no estaban en las rutas declaradas: se reconstruyeron en la copia a partir de las predicciones archivadas y del manifiesto de imágenes, respetando la selección descrita en la leyenda y verificando los hashes. La [procedencia por imagen](../results/analysis/paper_actual_20261119_v1/provenance.json) registra IDs y archivos fuente. La clase y el gráfico de concatenación se copiaron de `paper/articulo/borrador_profesor/` y la bibliografía de `carlos/references.bib`.

El PDF contiene 28 páginas; se revisaron todas en una hoja de contacto y se inspeccionaron a mayor tamaño las páginas de los ejemplos KTH y la tabla de comparación. La compilación no reportó referencias indefinidas ni overfull, pero Babel avisó que los patrones de división de palabras para español no estaban precargados; es una versión para revisión, no un artefacto editorial final. En particular, **el texto recibido aún refleja los resultados previos de DeepLumina** y no incluye las nuevas mediciones B del 19-11. La designación de versión actual es la indicada por el usuario, no una validación científica de todas sus afirmaciones.

## Actualización: DeepLumina B

La versión para revisión [main_actual_2026-11-19_deeplumina_v2.tex](main_actual_2026-11-19_deeplumina_v2.tex) incorpora por separado la variante B escalada y conserva A y sus reservas. El original entregado permanece intacto. La tabla se generó a partir de la [auditoría](../results/analysis/deeplumina_carlos_online_audit_20261119_v1/datasets.csv). PDF de revisión: [main.pdf](../results/analysis/paper_actual_deeplumina_20261119_v2/main.pdf).

**Importante:** al actualizar `main` se recibió un [manuscrito de Carlos](main.tex) con cambios adicionales sobre E4, E5 y ablaciones (commit `cc8e2e4`). Esa versión y la v2 de DeepLumina parten de textos diferentes; todavía hay que integrar y revisar ambos conjuntos de cambios para obtener un único paper actualizado. No presentar esta v2 como si ya incluyera los cambios nuevos de Carlos.

## Actualización 23-11 (Carlos): versión única

Los cambios de DeepLumina B de `main_actual_2026-11-19_deeplumina_v2.tex` se integraron en [main.tex](main.tex), que ya tenía E4, E5 y la ablación (`cc8e2e4`). Desde esta fecha **`main.tex` es otra vez la versión única del paper**. Los dos `main_actual_*.tex` se conservan sin cambios como referencia. La versión del 19-11 era idéntica a `main.tex` antes de E4 y E5, así que la integración no perdió cambios. Detalle en [PENDIENTES_JOAQUIN.md](PENDIENTES_JOAQUIN.md).
