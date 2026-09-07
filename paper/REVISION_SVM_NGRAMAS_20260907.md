# Integración completa de SVM y N-gramas — 7 de septiembre de 2026

Esta revisión reemplaza el estado experimental del informe ARS del 5 de septiembre. Se aplicó la revisión de coherencia guiada por ARS al artículo y a la tesis, usando la implementación y los CSV como evidencia. No constituye una revisión externa independiente.

## Datos verificados

Se comprobaron las fuentes de `results/confirmatory/ngram21/` y `results/extensions/outex13_official1360/ngram21/`, incluidos sus subdirectorios `topk_individual_control`. La carpeta Outex sin `/ngram21/` corresponde a la referencia de 20 y no se usó como resultado de 21.

Cada clasificador tiene DTD=10, FMD=15, CUReT=2 y Outex=1 condiciones: 28 por clasificador, 56 en total. Cada condición cuenta con Individual, Completa, GFS, Homogénea y Top-k: 280 filas. Top-k aporta 28 resultados SVM y 28 ResMLP, no 56 de SVM. Se verificaron unicidad, datos finitos y coincidencia de semillas y particiones entre métodos y bibliotecas. Los CSV de las dos bibliotecas permanecen sin editar.

## Cambios en los documentos

- Las tablas principales de macro-F1 y exactitud ahora corresponden a 21 descriptores con ambos clasificadores.
- Conforme a la indicación final del autor, el artículo presenta una única biblioteca de 21 descriptores. N-gramas figura en la tabla de extractores y su parametrización, sin sección separada de ampliación. Las comparaciones históricas 20 frente a 21 se conservan solo como archivos auxiliares.
- Se utiliza únicamente el nombre Outex en el texto del artículo y de la tesis. Las rutas técnicas de procedencia conservan su identificador original.
- Se retiraron las afirmaciones de SVM pendiente y las conclusiones que asignaban a Completa el mejor resultado de Outex con ambos clasificadores.
- Se actualizaron resumen, discusión, conclusión, dimensión, rankings y valores p. Se añadió una tabla explícita de las cuatro estrategias combinadas frente a Individual, manteniendo Holm para los diez pares.
- La tesis comparte las mismas tablas y resultados. La carpeta Overleaf utiliza las nuevas fuentes y los nuevos originales Java; el análisis de 20 queda como referencia histórica.

## Resultados relevantes

Con SVM en Outex, GFS sube de 0,9426 a 0,9610 y Completa de 0,9572 a 0,9674; Top-k baja de 0,9503 a 0,9441. Con ResMLP, GFS sube de 0,9423 a 0,9715. Estas diferencias son descriptivas de la partición evaluada. GFS conserva sus resultados SVM en los otros tres datasets; incorporar N-gramas no garantiza una mejora uniforme.

## Estadística regenerada con Java

Se ejecutaron ControlTest y MultipleTest sobre la nueva matriz primaria de cuatro datasets y la matriz de sensibilidad de ocho filas dataset–clasificador. La media de los clasificadores dentro de cada dataset tiene el mismo peso. Los resultados están en `results/confirmatory/ngram21/nonparametric/`.

| Comparación primaria | p ajustado con Holm, diez pares |
|---|---:|
| Top-k vs. Individual | 0,13906296895346038 |
| GFS vs. Individual | 0,22812586809721433 |
| Completa vs. Individual | 0,5891061609624212 |
| Homogénea vs. Individual | 1,0000 (original sin acotar: 1,2579874641529991) |

Friedman: estadístico 7,6, gl=4, p=0,10737970491308535. Quade: F=2,8631921824104234, gl=(4,12), p=0,07052048669968665. Los valores se contrastan con las colas superiores de SciPy en el generador (tolerancia 1e-9); los originales Java se conservan byte a byte. Ningún par rechaza en el análisis principal a 0,05.

En sensibilidad, GFS y Top-k frente a Individual tienen pHolm=0,01565402258002583. Esas ocho filas comparten datasets y no justifican una afirmación confirmatoria independiente. La conclusión principal sigue siendo que las mejoras descriptivas no establecen superioridad estadística general. No se cambió alfa ni se eligió una corrección según su resultado.

## Reproducibilidad

Generadores: `scripts/build_ngram21_nonparametric.py`, `scripts/build_paper_revision_tables.py` y `scripts/package_overleaf_revision.py`. Los dos primeros validan 56 condiciones completas y la concordancia de las tablas con las matrices Java. El empaquetado compila artículo y tesis y rechaza referencias sin resolver o desbordamientos de cajas. El archivo `VALIDACION_ENTREGA.json` contiene hashes de los archivos entregados. Copia previa de los documentos: `paper/revision_20260907_antes/`.

Los metadatos editoriales y la URL pública del repositorio continúan pendientes de confirmación de los autores; las ejecuciones SVM de esta comparación ya están completas.
