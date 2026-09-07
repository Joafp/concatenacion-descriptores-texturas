# Protocolo congelado: RGB Pixel N-grams como candidato multibase

Fecha de congelamiento: 2026-09-04

## Alcance

Este experimento añade un bloque derivado de RGB Pixel N-grams a la biblioteca
de 20 descriptores en DTD, FMD, CUReT y Outex. No sustituye la reproducción
oficial con histogramas crudos de Outex. La variante multibase se denomina
`rgb_ngram_svd` y es una representación comprimida diseñada para que el bloque
pueda entrar en el mismo protocolo anidado que los demás candidatos.

## Transformación congelada

1. Se extraen los conteos de la implementación 1 de Paiva et al. por imagen.
   Esta operación no usa etiquetas y puede almacenarse en caché.
2. Los códigos se proyectan determinísticamente a 8.192 bins mediante
   `codigo mod 8192` y se suman las colisiones.
3. Dentro de cada partición, `TruncatedSVD` se ajusta exclusivamente con las
   filas de entrenamiento y transforma entrenamiento y evaluación.
4. Se conservan 256 componentes, o el máximo permitido por el tamaño del
   entrenamiento cuando sea menor. Cada vector resultante se normaliza con L2.

El hashing es fijo y no consulta etiquetas ni filas de evaluación. SVD sí
aprende una proyección y por ello se vuelve a ajustar en cada fold interno y en
el ajuste externo final. La variante no debe denominarse reproducción exacta
del histograma original; esa reproducción permanece separada en Outex.

## Comparaciones

Se repite la biblioteca con 21 candidatos para:

- mejor descriptor individual;
- concatenación completa;
- GFS, con máximo de ocho bloques y la regla de parada vigente;
- mejor selección homogénea, incorporando N-gramas como familia propia;
- top-k con el mismo presupuesto que GFS;
- subconjuntos aleatorios de igual tamaño.

Las particiones, clasificadores, semillas y controles de fuga son los mismos del
protocolo principal. No se reutilizan resultados de selección obtenidos con la
biblioteca de 20 bloques porque añadir un candidato cambia el espacio de
búsqueda.

## Resultados y decisión de incorporación

Macro-F1 sigue siendo la métrica principal. Se conservan además exactitud,
dimensionalidad, tamaño del subconjunto y tiempo de ajuste del clasificador.
El descriptor se incorporará a las tablas del manuscrito solamente cuando:

- estén completas las 56 condiciones externas de los dos clasificadores;
- no existan filas duplicadas, faltantes o no finitas;
- las transformaciones registren que SVD se ajustó sólo con entrenamiento;
- se regenere el control top-k y el análisis no paramétrico con la biblioteca
  de 21 candidatos;
- las conclusiones distingan claramente la variante comprimida multibase de la
  reproducción cruda oficial de Outex.

