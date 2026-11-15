# Accuracy como métrica principal de la tesis

Fecha: 15 de noviembre de 2026, America/Asuncion.

## Decisión de los autores

Joaquín pidió añadir accuracy y precisión a los reportes y después indicó
expresamente que toda la tesis use **accuracy (exactitud) como métrica
principal**, con macro-F1 como complemento. Se incluyen también precisión
macro y recall macro cuando las predicciones permiten reconstruirlas.

Accuracy es la proporción de imágenes correctamente clasificadas. Precisión
macro promedia, entre clases, la proporción de predicciones positivas que
fueron correctas. Son magnitudes distintas. En datasets desbalanceados se
conservan las métricas macro para visibilizar pérdidas por clase.

## Alcance y cronología

- Se reconstruyen tablas, gráficos y contrastes principales sobre accuracy;
  no se renombran cifras F1 como si fueran exactitud.
- Los resultados históricos ya se habían observado al decidir este cambio.
  La decisión se declara posterior a esa observación y no como preregistro.
- Se conservan el ranking interno y las reglas de selección realmente
  ejecutadas: macro-F1, grilla q={0,25;0,50;0,75} y tolerancia 0,005.
  El cambio de reporte no altera el método ni sus fuentes originales.
- E1/E2 conserva ese método para hacer comparable la nueva evaluación y
  reporta accuracy primero. Una variante que seleccione bloques y rutas por
  accuracy sería otro experimento.
- Las métricas online se reconstruyen de las mismas predicciones asociadas
  a sus tiempos. Las métricas estáticas, los costos proyectados y las
  latencias físicas permanecen separados.
- Las pruebas principales de accuracy usan medias por dataset y familias
  de comparación explícitas. No se reutilizan valores p calculados con F1.

## Entrega documental

La tesis principal es `paper/tesis.tex` y su PDF `paper/tesis.pdf`. Se actualizan
resúmenes, objetivo, diseño, resultados, gráficos, discusión y conclusiones.
Los análisis originales basados en macro-F1 se conservan identificados como
secundarios o históricos en anexos. Los otros borradores de artículos y
presentaciones archivados no se convierten silenciosamente en una edición
nueva de la tesis.

La reconstrucción canónica de esta revisión está en
`results/analysis/thesis_accuracy_primary_20261115_v3/`, con 144 fuentes
identificadas mediante SHA-256, cero ajustes y cero predicciones nuevas.
Las carpetas v1/v2 conservan las salidas de preparación editorial previas;
v3 incorpora la tabla completa de comparadores y el escape LaTeX de etiquetas.

El respaldo de la tesis anterior está en
`archive/local/tesis_before_accuracy_primary_20261115.tar.gz`, SHA-256
`1ae2e1dfbe83ba97b397c4bd8501ccb42c61fcf83abd22c89398e2f57cc57194`.

## Ampliación experimental separada

E1/E2 se registra en
`results/exploratory/topk_cascade/top4_fixed_primary22_20261115_v1/`.
Su perfil KTH nuevo conserva fallos científicos de fidelidad de EVA-02
(coseno mínimo 0,931978) y SigLIP (0,981889), frente al mínimo congelado
0,999. Ninguno se repitió. Las condiciones que dependen de esos costos
quedan en revisión; no se sustituyen con otro perfil ni se ocultan para
producir una media completa de KTH.
