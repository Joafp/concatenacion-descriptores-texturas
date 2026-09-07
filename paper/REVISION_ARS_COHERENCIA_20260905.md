# Revisión ARS de coherencia entre método, resultados y conclusiones

Fecha: 5 de septiembre de 2026. Alcance: artículo `articulo/borrador_profesor/main.tex`, tesis y tablas compartidas. Evaluación metodológica local guiada por ARS, seguida de la revisión autorizada por el usuario; no es un panel independiente ni una certificación editorial. Calibration Status: `NOT_CALIBRATED`.

## Dictamen

Revisión menor del relato de la biblioteca de referencia. Sus cifras y su conclusión de no rechazo con cuatro datasets son coherentes. La evaluación conjunta de 21 descriptores no está terminada: no corresponde presentarla como resultado definitivo ni usar sus ejecuciones parciales para sustituir los contrastes de referencia.

## Criterios y evidencia

| Criterio | Juicio | Evidencia y alcance |
|---|---|---|
| Correspondencia entre pregunta y diseño | MEETS | Método y cinco comparadores; se estudian políticas de selección, no mecanismos causales de complementariedad. |
| Unidad de análisis y multiplicidad | MEETS | `generated/holm_primary.tex` y sección Análisis estadístico: cuatro datasets, diez pares, Holm; sensibilidad dependiente separada. |
| Concordancia numérica | MEETS | 280 filas de referencia, 140 de extensión ResMLP; agregación contrastada con `primary_by_dataset.csv` y salidas Java. |
| Reproducibilidad del método | PARTLY_MEETS antes de corregir | Faltaban parámetros de N-gramas, criterio de parada de la red y denominación precisa de LBP. Correcciones W1–W3. |
| Interpretación de efecto e incertidumbre | PARTLY_MEETS | Medias y SD descriptivas; no hay intervalos de generalización a nuevos datasets ni cálculo de tamaño muestral a priori. Se explicitan alcance y diferencias absolutas sin fabricar intervalos usando folds dependientes. |
| Entrega pública | PARTLY_MEETS | Disponibilidad de datos y código: faltan URL/versionado públicos y confirmación de las declaraciones de autoría, ética, financiación y uso de IA por los autores. No impide preparar el borrador para el tutor. |

Fuente de criterios: protocolo metodológico y estándares de reporte estadístico de ARS, aplicados según el diseño de benchmarks; no se impone formato APA a la plantilla CAS ni se exige normalidad para Friedman/Quade. No se calcula potencia retrospectiva a partir del p observado.

## Fortalezas verificadas

- S1. Separación de matrices experimentales. Evidence Anchor: table: `generated/ngram_resmlp.tex` frente a `generated/holm_primary.tex`. La primera es la extensión ResMLP; la segunda procede exclusivamente de la biblioteca de 20.
- S2. Integridad de las tablas. Evidence Anchor: dataset: `generated/baseline_source_rows.csv`. Se comprueban unicidad de condición/método, finitud, cinco métodos por condición y correspondencia con las entradas Java.
- S3. Selección sin consultar la prueba externa en el flujo inspeccionado. Evidence Anchor: text: Método, "exclusivamente dentro de la validación interna". `inner_score`, `greedy` y `RGBNgramSVDBlock.transform` ajustan selección y SVD sobre entrenamiento; esto no certifica ausencia de solapamiento de los corpus de preentrenamiento.

## Hallazgos y correcciones autorizadas

### W1. Denominación y parada de ResMLP

Severity: Minor. Evidence Anchor: text: Clasificadores, "parada temprana con paciencia 10". Confidence: 5, lectura de `ResMLPClassifier.fit` y `make_model`.

El monitor es la pérdida de entrenamiento, no una validación independiente. Además, se usa una MLP residual propia sobre vectores, no una reproducción exacta del modelo de imágenes citado. Explicitarlo, junto con el umbral de mejora 1e-4 y restauración del mejor estado, permite reproducir el entrenamiento sin atribuciones ambiguas.

### W2. Parámetros de N-gramas incompletos

Severity: Minor. Evidence Anchor: text: RGB Pixel N-grams como descriptor multibase, "ventanas deslizantes". Confidence: 5, `encoded_ngrams`, `build_count_cache` y `RGBNgramSVDBlock.transform`.

Añadir ventana vertical 2×1, paso 1, cuantización entera por 12, alfabeto de 22 valores, combinación de canales y uso del tamaño de imagen original; precisar SVD aleatorizado con cinco iteraciones. Mantener el nombre de adaptación comprimida y la advertencia sobre colisiones. No cambiar el extractor mientras corre la cola.

### W3. Nombre del mapeo LBP

Severity: Minor. Evidence Anchor: table: tabla de descriptores clásicos, fila LBP, "mapeo uniforme u2". Confidence: 5, `01_extract_features.py`, llamada `method="uniform"` y P+2 bins.

Sustituir u2 por mapeo uniforme invariante a rotación (riu2), consistente con 10+18+26=54 dimensiones. No alterar las características ni los resultados.

### W4. Dimensionalidad y complementariedad

Severity: Minor. Evidence Anchor: text: Trabajos relacionados, "cuantificando cuándo la complementariedad justifica el aumento de dimensionalidad". Confidence: 5, los comparadores igualan bloques, no coordenadas ni información.

Reducir esa afirmación a comparación de desempeño y dimensión. El diseño no aísla causalmente complementariedad de dimensionalidad. Precisar que el rango de reducción 69,8–85,2% se calcula sobre dimensiones medias por configuración, no sobre todos los folds individuales.

### W5. Trazabilidad del resumen estadístico

Severity: Minor. Evidence Anchor: table: `generated/global_primary.tex`. Confidence: 5, inspección del generador y recálculo de colas superiores.

Las cifras eran correctas, pero estaban escritas como constantes en el generador. Derivarlas de la salida Java y añadir grados de libertad: chi-cuadrado(4) y F(4,12). Identificar explícitamente los p de Holm como comparaciones basadas en rangos de Friedman, no como p post hoc de Quade. Las diferencias absolutas de macro-F1 complementan la lectura de p sin inferir equivalencia.

### W6. Incertidumbre y terminación de la extensión

Severity: Minor para el borrador delimitado. Evidence Anchor: text: Limitaciones, "su extensión conjunta con SVM aún no está cerrada". Confidence: 5, CSV y procesos inspeccionados.

Mantener la condición de borrador y no inferir que una ganancia de un único split de Outex se replica universalmente. Declarar que la SD entre particiones no es un intervalo de confianza multibase. En la tabla de extensión, explicitar que son medias, los n por dataset y la dispersión de las diferencias pareadas cuando n>1. La futura conclusión conjunta requiere completar SVM y Top-k y regenerar matrices y pruebas; no puede resolverse mediante redacción.

## Comprobaciones aritméticas

1. Procedimiento `p_from_test_statistic`; evidencia: tabla global/Friedman y Java original. Entrada: chi-cuadrado 6,6000, gl=4; cola superior. `scipy.stats.chi2.sf(6.6,4)=0.15859761982533205`; Java 0.15859761983510745. Diferencia <1e-10, ambos redondean a 0,1586. Estado: consistent.
2. Procedimiento `p_from_test_statistic`; evidencia: tabla global/Quade y Java original. Entrada completa: F=2.2325581395348837, gl=(4,12); cola superior. `scipy.stats.f.sf(...)=0.1264425224326286`; Java 0.12644252243262852. Ambos redondean a 0,1264. Estado: consistent. La tabla muestra el estadístico redondeado a 2,2326.
3. Agregación de CSV: primero media de condiciones por dataset/clasificador/método, luego media de ambos clasificadores. Se compara con Java con tolerancia absoluta 5e-12 y relativa cero. No se usan p sin ajustar en lugar de Holm.
4. Dimensión GFS media: mínimo 2909,3333 y máximo 5936 frente a 19628; reducción 85,1776% y 69,7575%. La frase requiere especificar que el rango es entre medias de configuraciones.
5. Diferencias GFS–Individual por dataset, promediando clasificadores: CUReT 0,002405; DTD 0,028177; FMD 0,006603; Outex 0,030273. Magnitud descriptiva, no prueba de superioridad general.

GRIM/GRIMMER no se aplican a medias de macro-F1 compuestas. No se infiere N a partir de gl de chi-cuadrado. Las otras familias Java conservadas como auxiliares no se presentan como nuevas pruebas ejecutadas en esta revisión.

## Aplicación y límites

Las correcciones se aplican a artículo, tesis y generador compartido. Copia previa: `revision_20260905_ars_antes/`. No se modifican CSV experimentales, pesos, checkpoints ni ejecuciones. Se prepara una carpeta Overleaf autocontenida con fuentes, figuras, tablas, procedencia y salidas Java originales; la versión anterior se conserva aparte. El cierre editorial y experimental pendiente queda declarado, no encubierto por un dictamen favorable.
