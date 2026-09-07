# Registro de revisión del manuscrito

## Protocolo confirmatorio principal

- Se congeló la pregunta de investigación alrededor de la selección y
  concatenación de bloques de descriptores heterogéneos.
- Se separó la selección interna de la evaluación externa y se fijaron los
  comparadores: descriptor individual, concatenación completa, GFS, mejor
  familia homogénea, top-k y subconjuntos aleatorios de igual cardinalidad.
- DTD, FMD y CUReT completaron 54 condiciones externas, 216 evaluaciones
  principales, 54 controles top-k y 5.400 subconjuntos aleatorios.
- Se incorporaron controles de procedencia, manifiestos canónicos, grupos de
  dependencia, hashes y reejecuciones deterministas.

## Revisión académica y de integridad

- Se reescribieron resumen, introducción, estado del arte, métodos, resultados,
  discusión y conclusión para centrar la contribución en la concatenación y la
  selección de bloques, no en una arquitectura particular.
- Se corrigieron referencias bibliográficas y se vinculó cada afirmación
  cuantitativa central con un artefacto experimental.
- Se explicitó que los folds repetidos no son réplicas científicas
  independientes, que el margen de 0,01 es descriptivo y que el costo medido
  corresponde al ajuste sobre embeddings precalculados.
- El control top-k mostró que la fortaleza individual de los bloques explica
  parte de la ganancia; por ello, el manuscrito no atribuye toda mejora a la
  búsqueda secuencial de complementariedad.

## Reestructuración solicitada por el tutor (2026-08-15)

- La Sección 3 se mantuvo exclusivamente como descripción del método de
  concatenación y selección; datasets, clasificadores, métricas y protocolo
  quedaron en ``Resultados experimentales''.
- Se conservaron una figura del pipeline completo y una segunda figura del
  protocolo anidado; esta última fue regenerada para mejorar su legibilidad.
- Se concentraron el diseño del análisis estadístico y sus resultados de
  contraste en las subsecciones ``Análisis estadístico'' y ``Resultados del
  análisis estadístico'', sin separar la interpretación inmediata de las
  tablas principales.
- Se redujo ``Trabajos relacionados'' para justificar exclusivamente la
  complementariedad, la concatenación y la selección de bloques; se mantuvo
  RGB Pixel N-grams como antecedente directo.
- Las contribuciones de la introducción se consolidaron en tres puntos
  verificables y la conclusión conserva la secuencia propuesta, evaluación,
  resultados principales y trabajo futuro.
- Se fijó la posición de las tablas principales de resultados antes de su
  interpretación inmediata mediante barreras de flotantes; así el lector ve
  cada resultado antes de su lectura analítica.

## Rediseño visual a partir del antecedente RGB Pixel N-grams (2026-08-15)

- Se reemplazó el pipeline genérico por una figura que hace visibles las
  familias de bloques, su normalización y la concatenación antes de clasificar.
- Se añadió una figura de GFS paso a paso con la trayectoria realmente medida
  en el experimento de continuidad de Outex: n-grama, DINOv2-Large, VGG16 y
  DINOv2-Base. Los valores mostrados son exactitudes internas; el macro-F1 se
  reserva para la evaluación externa posterior.
- Se rediseñó el protocolo anidado como particiones y folds explícitos, y se
  actualizó la figura desempeño--dimensionalidad con barras de dispersión y
  etiquetas no redundantes por dataset.

## Revisión de primera lectura y segunda iteración visual (2026-08-15)

- La Figura 1 se simplificó a cinco etapas legibles; los checkpoints concretos
  permanecen en la tabla de extractores, no dentro del diagrama.
- La Figura 2 dejó de mostrar una trayectoria particular de Outex y ahora
  explica GFS como algoritmo general con macro-F1 interno, regla de parada y
  test reservado. La excepción de exactitud para reproducir RGB Pixel N-grams
  se declara explícitamente en el texto.
- Se agregó una tabla de configuración de GFS, siguiendo la separación entre
  selección de parámetros y resultados principales del antecedente.
- La comparación de estrategias y su tabla de macro-F1 se trasladaron para
  aparecer inmediatamente después de la configuración experimental; las
  comparaciones con trabajos publicados y el análisis estadístico quedan
  después como evidencia complementaria.
- La leyenda de la tabla principal ahora define el significado de la negrita.

## Contextualización frente a métodos publicados (2026-08-15)

- Se añadió una tabla de exactitud para DTD, FMD, CUReT y Outex con una
  referencia publicada por dataset y la mejor configuración correspondiente
  del estudio.
- Cada fila declara su grado de comparabilidad. Sólo Outex comparte imágenes,
  partición y clasificador con el antecedente RGB Pixel N-grams; la mejora de
  cuatro aciertos se mantiene como puntual porque McNemar no fue significativo.
- DTD, FMD y CUReT se presentan como referencias de contexto, no como récords
  de estado del arte, debido a diferencias de pipeline o de partición externa.

## Outex_TC_00013 oficial (2026-08-11)

- Se auditó la colección completa: 1.360 imágenes BMP RGB, 68 clases
  balanceadas, IDs continuos, ausencia de archivos corruptos o duplicados y
  partición oficial de 680 imágenes de entrenamiento y 680 de prueba.
- Se alinearon y validaron los 20 bloques de descriptores contra el manifiesto
  oficial. Todo análisis de Outex usa exclusivamente esta colección y esta
  partición.
- Se reprodujeron exactamente las exactitudes publicadas de RGB Pixel N-grams:
  0,963235 y 0,952941 con SVM lineal.
- La concatenación del mejor n-grama con los 20 bloques obtuvo 0,969118 de
  exactitud y 0,968649 de macro-F1. La mejora fue de cuatro aciertos; el IC95 %
  bootstrap pareado incluyó cero y McNemar exacto produjo p=0,584665. El texto
  informa una mejora puntual, no superioridad estadística.
- Outex se integró al mismo flujo de selección de bloques con una condición
  oficial por clasificador. La validación interna utiliza solo el entrenamiento
  oficial y el análisis omite deliberadamente Wilcoxon e intervalos entre
  splits cuando n=1.

## Estado de entrega

- El manuscrito se compila con el formato LaTeX del artículo y conserva tablas,
  figuras y referencias dentro de sus márgenes.
- Antes de una entrega pública resta reemplazar el marcador de URL por una
  versión archivada del código y de los artefactos reproducibles.

## Control editorial de figuras (2026-08-15)

- Se redibujaron las Figuras 1--3 a un ancho editorial de 6,9 pulgadas, con
  tipografía mínima legible, paleta apta para daltonismo y una función visual
  inequívoca para cada figura: pipeline, búsqueda GFS y protocolo anidado.
- Se añadió una validación geométrica que detiene la generación si un rótulo
  sale del lienzo o del bloque al que pertenece. Después se inspeccionaron las
  figuras aisladas y nuevamente dentro de las páginas compiladas.
- La antigua gráfica de dispersión desempeño--dimensionalidad se reemplazó por
  una comparación directa y pareada entre GFS y concatenación completa. La
  nueva Figura 4 muestra simultáneamente reducción dimensional, diferencia de
  macro-F1, margen práctico y variabilidad entre particiones.
- Se corrigió el texto de resultados y la leyenda de la Figura 4 para evitar
  que el gráfico sugiera dominancia universal: FMD favorece GFS, Outex favorece
  la concatenación completa y seis de ocho configuraciones quedan dentro del
  margen práctico o lo rozan.

## Reconstrucción vectorial con TikZ y QA renderizado (2026-08-15)

- Se instaló y aplicó la skill `tikz-diagrams`, junto con XeLaTeX y Poppler.
  El control inicial rechazó tres de las cuatro figuras Matplotlib por
  solapamientos, proximidad a bordes y ocupación inadecuada del área editorial.
- Las cuatro figuras se reconstruyeron como fuentes TikZ independientes en
  modo `research`. Cada fuente pasó el control estático, compiló con XeLaTeX,
  se rasterizó y obtuvo `PASS` en el control visual automático.
- La Figura 4 se rediseñó como dos paneles alineados por condición: reducción
  dimensional a la izquierda y diferencia pareada de macro-F1 a la derecha.
  Esto elimina etiquetas flotantes y permite comparar costo y desempeño sobre
  las mismas ocho filas.
- Se inspeccionaron además las páginas 5, 7, 10 y 15 del manuscrito compilado.
  La Figura 1 requirió una simplificación adicional del encabezado para evitar
  una colisión que sólo resultaba visible a escala de página.
- Los PDF integrados se generan en versión 1.5, compatible con el template del
  artículo. Las figuras Matplotlib anteriores se conservaron en
  `figures/legacy_matplotlib/` únicamente como respaldo.

## Pipeline detallado con imagen y vectores (2026-08-15)

- La Figura 1 compacta se sustituyó por un flujo detallado que utiliza una
  imagen real de la colección Outex validada.
- El diagrama muestra explícitamente la ejecución paralela de las cuatro
  familias de extractores congelados, sus bloques vectoriales, la
  normalización $L_2$ independiente, la selección de $S$, la concatenación, el
  clasificador final y la clase predicha.
- Se distinguió la salida por muestra ($\hat y_i$) de la evaluación agregada:
  macro-F1 se calcula únicamente sobre el test externo y no se presenta como
  una salida directa del clasificador.
- La versión final pasó el control estático, la compilación XeLaTeX, el QA
  visual en modo `research` y una inspección adicional dentro de la página 5
  del manuscrito.

## Análisis SCI2S de métricas múltiples y comparación contra Individual (2026-08-28)

- Se ejecutaron las implementaciones Java originales de `ControlTest` y
  `MultipleTest` usando los resultados CPU canónicos.
- Se conservaron las salidas LaTeX en
  `paper/articulo/borrador_profesor/informe_profesor/latex_sci2s/`.
- Se repitió el análisis para accuracy, balanced accuracy, precision macro,
  recall macro, macro-F1 y AUC ROC macro.
- En el análisis primario de cuatro datasets (DTD, FMD, CUReT y Outex), ninguna
  métrica mostró una comparación contra Individual significativa después de
  Holm o Bergmann--Hommel.
- En la sensibilidad de ocho bloques dataset--clasificador, GFS y Top-k frente
  a Individual resultaron significativos con Holm para las seis métricas. Esta
  sensibilidad se conserva como evidencia secundaria porque reutiliza los
  mismos datasets por clasificador.
- El resumen reproducible de las comparaciones está en
  `results/confirmatory/nonparametric/metrics_cpu/multipletest_summary_vs_individual.csv`.
- El informe para el profesor se actualizó en
  `paper/articulo/borrador_profesor/informe_profesor/INFORME_RESULTADOS_PROFESOR.md`.
