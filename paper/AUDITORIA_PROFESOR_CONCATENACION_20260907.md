# Lectura final como profesor: coherencia, escritura y evidencia

Fecha: 7 de septiembre de 2026. Manuscrito: `articulo/borrador_profesor/main.tex`, tablas generadas y PDF; tesis sincronizada. Revisión local guiada por ARS, sin panel independiente. Estado de calibración: NOT_CALIBRATED.

## Lectura del trabajo

El estudio tiene una pregunta coherente: cómo cambian el desempeño y la dimensión al concatenar descriptores frente a seleccionar uno individual. Su contribución es la comparación de políticas de representación bajo particiones comunes. GFS y Top-k son mecanismos para seleccionar los bloques que se concatenan; el artículo no introduce un nuevo algoritmo ni demuestra que la complementariedad sea la causa de cada ganancia.

La secuencia final es: problema de representación, antecedentes, definición de concatenación, cinco estrategias, biblioteca de 21 descriptores, detalles de selección, protocolo, desempeño y dimensión, inferencia, discusión y conclusión. Las estrategias se presentan antes del detalle de GFS para que el método responda a la pregunta central del trabajo. N-gramas está integrado en la biblioteca y no aparece como ampliación separada. El nombre utilizado en el texto es Outex.

## Hallazgos y cambios aplicados

| Hallazgo | Evidencia | Cambio y resultado |
|---|---|---|
| La contribución podía confundirse con proponer GFS | text: Introducción y Método, "GFS se utiliza como un método" | Se explicita que GFS y Top-k eligen qué concatenar; se reordena la presentación de los cinco comparadores. |
| El costo dimensional se prometía para toda la comparación, pero se resumía solo para GFS | table: tablas principales y texto posterior | Se añade `dimensions_primary.tex` para las cinco estrategias y ocho configuraciones; dimensión no se interpreta como latencia o memoria medida. |
| La ventaja de concatenar podía parecer uniforme | dataset: medias de `ngram21_source_rows.csv` | Se explica el contraejemplo de FMD para Completa: mejora en tres datasets y pierde en uno al promediar clasificadores. La mejor estrategia de Outex depende del clasificador. |
| DRLBP no identificaba fielmente la implementación | text: `src/01_extract_features.py`, `_drlbp`, `method="ror"`, `bins=P+2`, `range=(0,P+2)` | El artículo la denomina LBP-rot y documenta su correspondencia con la clave interna `drlbp`. Explica que descarta códigos fuera de [0,10] y no reproduce el DRLBP publicado. |
| Se afirmaban declaraciones personales y revisión final sin evidencia aportada en la sesión | text: declaraciones finales, "Los autores dirigieron el proceso, revisaron el contenido" | Se precisa el uso real de IA y la responsabilidad de revisión final. Conflictos, financiación y declaración ética quedan pendientes de confirmación de los autores. |
| El texto podía confundir mejora descriptiva con significancia | table: `vs_individual_primary.tex` y `holm_primary.tex` | Se muestran diferencias y p ajustados, manteniendo la familia de diez pares. La sensibilidad dependiente no sustituye el análisis de cuatro datasets. |

Los primeros tres hallazgos son correcciones de claridad y alineación. La identificación de LBP-rot afecta la interpretación del descriptor y queda como limitación sustantiva: documentar su comportamiento hace fiel el reporte, pero no corrige la pérdida de códigos de la implementación. Cambiar el histograma y sustituir sus resultados exigiría reextraer y reevaluar las estrategias. Esta revisión no presenta esa reevaluación como realizada.

## Evidencia comprobada

- 56 condiciones completas de 21 descriptores, 28 por clasificador; cinco estrategias por condición y 280 filas. Fuentes separadas para DTD/FMD/CUReT y Outex, siempre con `/ngram21/` para la biblioteca actual.
- Unicidad de filas, finitud de métricas, número de bloques seleccionados y suma de dimensiones. Completa contiene 21 bloques y 19.884 coordenadas. Los nombres internos se conservan en los CSV para mantener trazabilidad.
- Medias y SD generadas desde las filas originales. GFS supera descriptivamente a Individual en las ocho medias dataset–clasificador. La tabla frente a Individual promedia primero por clasificador y luego por dataset.
- Matriz Java principal idéntica a la agregación de las tablas, con tolerancia absoluta 5e-12. Friedman: p=0,10737970491308535; Quade: p=0,07052048669968665. Colas superiores contrastadas mediante SciPy. Los diez p de Holm se extraen de la salida original y se acotan a 1 para presentar.
- Las 32 claves citadas del artículo tienen una entrada bibliográfica. La ausencia de claves faltantes no equivale a verificar exhaustivamente cada dato bibliográfico o cada afirmación de los artículos citados.

## Fuentes académicas contrastadas en esta lectura

Se verificaron las afirmaciones centrales sobre codificación, selección y estadística usando fuentes primarias: [Deep Filter Banks, manuscrito de los autores](https://arxiv.org/abs/1507.02620), [Deep TEN, CVF](https://openaccess.thecvf.com/content_cvpr_2017/html/Zhang_Deep_TEN_Texture_CVPR_2017_paper.html), [selección de características, JMLR](https://www.jmlr.org/papers/v3/guyon03a.html), [Derrac y colaboradores, tutorial original](https://sci2s.ugr.es/sites/default/files/files/TematicWebSites/sicidm/2011-Derrac-SWEVO.pdf) y [descriptor RGB, página del editor](https://www.sciencedirect.com/science/article/abs/pii/S0923596523001108). Sus resultados publicados no se presentan como resultados del estudio propio. La ficha de Deep TEN en CVF utiliza una paginación distinta de la entrada IEEE conservada; no se modificó el DOI basándose solo en esa diferencia.

## Dictamen para el borrador del tutor

La pregunta, el diseño y las conclusiones están alineados con un estudio comparativo de concatenación. El trabajo tiene resultados descriptivos positivos, límites claros y una comparación estadística que no confirma superioridad general. Eso permite discutir cuándo y con qué dimensión funcionan las combinaciones evaluadas, pero no afirmar que concatenar siempre mejora ni que GFS sea superior a Top-k.

La revisión no detectó discrepancias entre las cifras principales y las fuentes comprobadas. No constituye garantía de ausencia absoluta de errores: no se reprodujo desde cero la extracción de todas las imágenes, no se auditó el solapamiento de los corpus de preentrenamiento y no se verificaron exhaustivamente las 32 publicaciones. El hallazgo de LBP-rot queda explícito y debe considerarse antes de una entrega definitiva. Las declaraciones personales y los metadatos editoriales requieren confirmación de los autores.
