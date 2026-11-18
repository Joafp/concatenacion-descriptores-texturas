# Qué reporta HyTexNet (2026) y qué reportamos nosotros

Fecha: 2026-11-18

El revisor pidió tomar como referencia «el paper de 2026». El único de 2026 que
citamos es HyTexNet: Gupta, Mishra y Shrivastava, *Knowledge-Based Systems* 338
(2026) 115482 (`carlos/1-s2.0-S095070512600225X-main.pdf`). DeepLumina es de
2022 y Neshov et al. de diciembre de 2025. Si el revisor se refería a otro,
esta comparación hay que rehacerla.

Leyenda del estado:
- **Ya estaba:** el paper ya lo tenía antes del 18-11.
- **Agregado 18-11:** se calculó a partir de las predicciones guardadas y se
  integró en `carlos/main.tex`.
- **Se puede sin experimentos:** los datos están en el repo o en la máquina,
  pero falta calcularlo.
- **Requiere experimento:** decisión del equipo.

| Qué reporta HyTexNet | Dónde | Equivalente en nuestro paper | Estado |
|---|---|---|---|
| Accuracy frente a muchos métodos | Tablas 1–3 | Tabla de métodos recientes en el panel común (§4.11). Además, los corremos en nuestras mismas particiones, cosa que HyTexNet no hace: copia las cifras publicadas | Ya estaba |
| Accuracy media en DTD sobre 10 particiones | Fig. 9 | DTD con sus 10 particiones oficiales en todas las tablas | Ya estaba |
| Accuracy y macro-F1 | Tabla 6 | Accuracy principal y macro-F1 complementaria en todo el paper | Ya estaba |
| Ablación de componentes y decisiones de diseño | Tabla 6, Fig. 15 | Los resultados ya estaban repartidos en varias tablas. El 18-11 se juntaron en la **Tabla 14** (§4.12), con accuracy, macro-F1 y una lectura por fila, como la Tabla 6 de HyTexNet | Agregado 18-11 |
| Estabilidad: media ± DE de 5 corridas e IC 95 % | Tabla 6, fila 7 | Media ± DE entre particiones y kappa (Tabla 10). Sin IC por dataset: las particiones comparten entrenamiento y CUReT y Outex tienen 2 y 1 condición | Agregado 18-11 |
| Matrices de confusión normalizadas por fila | Figs. 5c–7c | Figura 4: FMD y KTH-TIPS2-b; las de los seis datasets en `e1_confusion.csv` | Agregado 18-11 |
| Ejemplos de confusión entre clases parecidas (lino y algodón en KTH) | Fig. 14 | Encontramos la misma confusión: el 23 % del algodón va a lino (§4.8) | Agregado 18-11 (en texto) |
| Pruebas estadísticas | — | HyTexNet **no informa ninguna**. Nosotros: Friedman, Holm, Wilcoxon exacto, no inferioridad y, desde el 18-11, McNemar exacto por condición | Ya estaba + agregado 18-11 |
| Dimensión y tiempo por imagen de cada descriptor | Tabla 7 | Las tablas de extractores tienen la dimensión; los ms por bloque están en el perfil de latencias, pero no en esas tablas | Se puede sin experimentos |
| Parámetros (M) y GFLOPs | Tablas 4 y 8 | No están. Los parámetros salen de las fichas de los modelos; los GFLOPs requieren un script que no entrena (pedir a Joaquín) | Se puede sin experimentos |
| Ejemplos de imágenes mal clasificadas | Fig. 14 | Figura 5: algodón de la muestra b clasificado como lino, frente a algodón de las muestras a, c y d y lino bien clasificados. El 81 % de esos errores viene de esa muestra | Agregado 18-11 |
| t-SNE de los embeddings | Fig. 11 | Los embeddings están en `embeddings_confirmatory/` (757 MB, fuera de git); hace falta Python, que esta máquina no tiene | Se puede sin experimentos |
| Curvas de entrenamiento y pérdida | Figs. 5–8 | No aplica a SVM sobre redes congeladas, que no entrena por épocas. ResMLP sí; habría que ver si Joaquín guardó sus curvas | Preguntar |
| Mapas de activación de la red | Fig. 12 | No aplica directamente: no modificamos las redes | No se propone |
| Evaluación cruzada entre datasets (KTH → Kylberg) | Tabla 5, Fig. 10 | No está | Requiere experimento |
| Robustez a ruido y brillo | Tabla 6, fila 6 | No está | Requiere experimento |
| CRediT y conflicto de intereses | Declaraciones | Pendientes en nuestro paper | Falta que lo completen los autores |

## Qué se agregó al paper el 18-11

- §4.4 (Análisis estadístico): McNemar exacto por condición, ajustado con Holm,
  y kappa de Cohen.
- §4.8, nueva («Análisis por imagen de la activación por margen»):
  - **Tabla 10:** media ± DE, kappa, discordancias y calidad de la compuerta.
  - **Figura 4:** matrices de confusión de FMD y KTH-TIPS2-b.
- Discusión: dos frases con los números por imagen.
- Apéndice A: fuentes del cálculo.

Resultados principales:
- Las dos políticas difieren en 319 de 31.984 imágenes (1,0 %): Top-4 directo
  acierta solo en 151 y la cascada solo en 168.
- Ninguna condición es significativa con McNemar: el menor *p* es 0,0625 y,
  con Holm, todos valen 1.
- La compuerta escala el 21,8 % de las imágenes, pero ahí reúne el 72,9 % de
  los errores de la etapa barata. En las imágenes que no escala, esa etapa
  acierta el 96,2 %.

El PDF tiene ahora 25 páginas. Todo se calculó con
`carlos/analisis_paper/e1_por_imagen.sh` y `e1_analisis_por_imagen.awk`.

## Siguiente paso sugerido

Si el revisor insiste en seguir el esquema de HyTexNet, lo más barato es
agregar lo que se puede sin experimentos:
1. Una columna de ms por bloque en las tablas de extractores.
2. Parámetros por modelo.
3. Una figura con ejemplos de algodón confundido con lino.

La evaluación cruzada entre datasets y la robustez a ruido serían
experimentos nuevos.
