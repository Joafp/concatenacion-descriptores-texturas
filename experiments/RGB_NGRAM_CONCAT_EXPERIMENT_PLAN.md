# Protocolo congelado v2: RGB Pixel N-grams y concatenación heterogénea

Fecha de congelamiento inicial: 2026-08-11  
Versión 2, congelada antes de evaluar cualquier concatenación sobre el test oficial: 2026-08-11

## Motivo de la versión 2

Después del primer protocolo se recibió el archivo
`Outex_TC_00013-20260120T014101Z-3-001.zip`. La auditoría confirmó que contiene
las 1.360 imágenes RGB de Outex_TC_00013, las 68 clases y la partición oficial
de 680 imágenes de entrenamiento y 680 de prueba.

Este hallazgo permite sustituir la comparación histórica indirecta por una
reproducción controlada. No se observó el resultado de ninguna concatenación
sobre el test oficial antes de congelar esta versión.

## Pregunta primaria

¿La concatenación seleccionada de RGB Pixel N-grams con descriptores visuales
heterogéneos supera la exactitud de RGB Pixel N-grams bajo la misma partición
oficial y el mismo clasificador lineal?

La hipótesis primaria es direccional: `rgb_ngram_gfs` obtiene mayor exactitud
que `rgb_ngram_selected_l2`. Macro-F1 es una métrica secundaria y se informa
para mantener continuidad con el estudio principal. Superar numéricamente el
0,963 publicado será descrito como una mejora del valor puntual; una afirmación
de mejora con incertidumbre exigirá además que el intervalo bootstrap pareado
no incluya cero.

## Reproducción del artículo base

Se implementan las dos variantes con los parámetros publicados:

- `rgb_ngram_impl1`: $W_{R\Vert G\Vert B}$, rango `r=12`, ventana vertical
  `2x1`.
- `rgb_ngram_impl2`: $W_R \cup W_G \cup W_B$, rango `r=11`, ventana vertical
  `4x1` y etiqueta de canal.

El vocabulario se construye solo con las 680 imágenes oficiales de
entrenamiento. La clasificación de referencia utiliza histogramas de frecuencia
sin normalización y `SVC(C=1, kernel="linear")`. Esta configuración reproduce
exactamente, antes del estudio de fusión, los valores redondeados de la Tabla 4
de Paiva Pavón et al.: 0,963 y 0,953. El texto del artículo menciona
`OneVsRestClassifier` en la subsección de ajuste; esa variante reproduce en
cambio los valores 0,954 y 0,941 de dicha subsección. Por ello la reproducción
de la tabla final se fija como comparador principal.

## Métodos comparados

- `published_reproduction_impl1_raw` y `published_reproduction_impl2_raw`:
  controles de reproducción con histogramas crudos.
- `rgb_ngram_selected_l2`: variante de n-gramas elegida por exactitud interna,
  normalizada por fila para concatenación por bloques.
- `best_direct_descriptor`: mejor descriptor no concatenado entre los veinte
  bloques, seleccionado exclusivamente dentro del entrenamiento.
- `rgb_ngram_gfs`: parte del n-grama anterior y añade mediante GFS como máximo
  tres bloques. Se detiene tras dos pasos consecutivos con mejora menor que
  0,001 y conserva el mejor subconjunto histórico.
- `rgb_ngram_full_concat`: n-grama seleccionado unido a los veinte bloques.

La selección usa cuatro folds internos estratificados, semilla 42 y exactitud.
Todos los métodos finales se ajustan con `SVC(C=1, kernel="linear")` sobre las
680 imágenes de entrenamiento y se evalúan una sola vez sobre las 680 de test.

## Prevención de fuga

- El vocabulario de n-gramas se construye solo con el entrenamiento oficial.
- Las variantes y los bloques se seleccionan solo en validación interna.
- Cada bloque se normaliza por muestra con norma L2 antes de concatenar.
- El test oficial no interviene en vocabulario, selección, parada ni ajuste.
- El mejor descriptor directo se incluye para separar el efecto de la
  concatenación del efecto de un único extractor fuerte.

## Análisis

Se reportan exactitud, macro-F1, número y nombres de bloques, dimensionalidad
implícita por vocabulario y tiempo de ajuste. La diferencia primaria se calcula
de manera pareada sobre las mismas 680 predicciones. Se obtiene un intervalo
bootstrap percentil estratificado por clase con 20.000 remuestreos y semilla 42.

Como análisis secundario posterior se conservarán particiones repetidas para
estudiar robustez, pero no reemplazarán la comparación principal sobre el
protocolo oficial.

## Criterios de integridad

- 1.360 BMP RGB legibles de 128x128, sin duplicados y con hashes registrados.
- 68 clases, 20 imágenes por clase y partición oficial 10/10 sin solapamiento.
- 20 matrices de descriptores con 1.360 filas y etiquetas idénticas al
  manifiesto.
- Métricas finitas en `[0,1]` y predicciones persistidas para auditoría.
- Reproducción previa de 0,963235 y 0,952941 para las dos variantes publicadas.
- El manuscrito se actualizará solo después de validar resultados y procedencia.
