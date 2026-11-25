# Métricas y cifras de los artículos de referencia

Revisión de las once copias primarias del [catálogo de referencias](../referencias/por_nombre/README.md). Las cifras del manuscrito se toman de las tablas del artículo que describe cada método, con su variante, dataset y agregación originales. El cuadro bibliográfico utiliza accuracy y conserva la desviación estándar publicada cuando acompaña a la cifra seleccionada.

| Artículo | Qué mide y dónde | Correspondencia con nuestro artículo |
|---|---|---|
| [Neshov et al., agregación multicapa](https://doi.org/10.3390/electronics14234779) | Tabla 4: accuracy, con desviación estándar para KTH-TIPS2-b, FMD y DTD en la fila BEiTv2. Incluye parámetros y GMAC del modelo preentrenado. Analiza ejemplos de errores. | Compartimos accuracy. FMD usa 10 repeticiones de 10 folds en su estudio y 3 repeticiones de 5 folds en el barrido propio. Su Soil es aumentado y el nuestro usa imágenes originales deduplicadas. |
| [Gupta et al., HyTexNet](https://doi.org/10.1016/j.knosys.2026.115482) | Tablas 1–4 y sección 4.5: accuracy. También curvas de aprendizaje, matrices de confusión, dimensión, parámetros, GFLOPs, transferencia, robustez y estabilidad. El ensayo de cinco inicializaciones informa 99,14 ± 0,11 % y un IC 95 % de [98,88; 99,41] en la p. 16 del PDF. | Compartimos accuracy y análisis de errores. Las desviaciones estimadas entre particiones propias responden a otra unidad que las cinco inicializaciones. El manuscrito cita 99,79 % de la Tabla 1 para KTH-TIPS2-b, que pertenece a la comparación principal. Su tercio de entrenamiento se selecciona por pose, luz y escala. |
| [Chang et al., 6LBP+dCellNNs](https://doi.org/10.1016/j.eswa.2023.122100) | Tablas 2–4: accuracy de clasificación de texturas. Tabla 5: dimensión y costo de cómputo. Tabla 1: accuracy, AUC-ROC, AUC-PR, sensibilidad y especificidad de contornos en DRIVE. | Compartimos accuracy de clasificación. DRIVE corresponde a otra etapa y otra tarea. El 99,18 % pertenece a Outex TC 00012. Nuestro Outex es TC 00013 y nuestro KTH-TIPS2-b separa muestras físicas completas. |
| [Simon y Uma, DeepLumina](https://doi.org/10.1155/2022/9510987) | Tablas 4 y 5: accuracy por configuración. La fila ResNet101 + SVM con RGB y luminancia informa 73,63 % en DTD y 90,15 % en FMD. También presentan ablaciones de color, curvas y análisis de complejidad. | Compartimos accuracy. El artículo describe un reparto aleatorio 80/20. Las cifras citadas son las de los autores para esa receta. |
| [Paiva et al., RGB Pixel N-grams](https://doi.org/10.1016/j.image.2023.117028) | Tablas 1–5: accuracy y, para la parametrización, tamaño de diccionario. Tablas 6–7: rankings y contrastes Friedman, Quade y post hoc. La Tabla 5 selecciona el mejor resultado por dataset entre KNN, RF y SVM. | Compartimos accuracy. La implementación 1 reporta 96,2 % en CUReT y 96,3 % en Outex13. CUReT en color y con validación cruzada difiere del CUReT gris agrupado que usamos. Outex13 usa el reparto oficial en ambos estudios. Nuestro bloque N-gramas + SVD es una configuración distinta. |
| [Gupta et al., AsTexNet](https://doi.org/10.3390/app16125743) | Tablas 2–4: accuracy y, en Tabla 4, precision, recall y F1. FMD: 78,71 %, 0,787, 0,787 y 0,786. KTH-TIPS2-b: 90,6 %, 0,906, 0,906 y 0,905. También curvas, matrices y análisis de recursos. | Tenemos las cuatro métricas calculadas. La Tabla 4 presenta los valores como agregados y no explicita allí la fórmula de promediado. Se conservan como cifras citadas y se evita asumir identidad con nuestro promedio macro. |
| [Scabini et al., comparación de Vision Transformers](https://doi.org/10.3390/jimaging11090304) | Tablas 2–3: accuracy de extractores congelados con cabezas KNN, LDA y SVM. Tabla 4: throughput de extracción. | Contextualiza los extractores que pueden entrar al ranking. Nuestra latencia del panel incluye la política completa y usa una imagen por llamada. |
| [Khan et al., descripción compacta de color y textura](https://doi.org/10.1016/j.patrec.2014.07.020) | Tablas 1–4: accuracy por representación, incluyendo comparaciones de descriptores individuales, combinaciones y compresión. También contrastan tamaño de representación. | Compartimos accuracy y dimensión. Es un antecedente para discutir costo de representación y complementariedad del color. |
| [Ataky et al., análisis multiescala](https://doi.org/10.3390/app13031291) | Tablas 1–9: accuracy, con desviación estándar cuando la estimación se basa en validación cruzada. | Compartimos accuracy. Sus suites Outex y KTH-TIPS originales difieren de nuestras variantes. |
| [Puig et al., selección independiente de la aplicación](https://doi.org/10.1016/j.patcog.2010.05.005) | Tablas 1–5: rankings y tamaños de subconjuntos de métodos, junto con rendimiento en clasificación y segmentación. | Antecedente para la selección de bloques. La clasificación por píxel tiene otra unidad de observación. |
| [García y Puig, integración de métodos y ventanas](https://doi.org/10.1016/j.imavis.2006.05.023) | Tablas 1–4: tasas de clasificación por píxel para tamaños de ventana y conjuntos de métodos. | Antecedente de integración. Nuestro acierto cuenta imágenes completas. |

La **accuracy por imagen** se mantiene como métrica principal. La **precisión macro**, el **recall macro** y el **macro-F1** están calculados junto con accuracy para las 60 combinaciones completas de dataset, cabeza y política de nuestro panel. Las columnas se pueden consultar en el [consolidado propio](../../results/analysis/thesis_accuracy_primary_20261115_v3/online_means.csv). Precisión mide, por clase, cuántas predicciones de esa clase acertaron. Recall mide cuántos ejemplos reales de la clase se recuperaron. Para cada medida macro se da el mismo peso a todas las clases. Los diagnósticos por clase de E1 están en [las métricas por clase](../../carlos/analisis_paper/e1_por_clase.csv).

La [versión del artículo](../../carlos/main_metricas_publicadas_20261123.tex) usa cifras de los artículos para los métodos externos y conserva el costo y la latencia de los métodos propios en sus experimentos correspondientes. Las cifras publicadas sirven como contexto bibliográfico. La similitud de una métrica o del nombre del dataset permite ubicar los resultados, pero la equivalencia experimental también requiere comprobar datos, splits, receta y forma de agregación.


## Cotejo de las 11 filas que entran al manuscrito

Las páginas son las posiciones físicas del PDF de cada copia primaria. Las cifras se toman de las variantes y tablas indicadas, con sus unidades originales.

| Dataset | Artículo y cifra | Localizador de la cifra | Localizador del protocolo |
|---|---|---|---|
| DTD | Neshov, 82,0 ± 0,9 % | Tabla 4, fila BEiTv2, p. 15 | Sección 3.1, pp. 8–9, diez particiones de DTD |
| DTD | HyTexNet, 73,2 % | Figura 9 y texto de la sección 4.5, pp. 12–13 | Pie de la Figura 9, p. 12, diez repartos aleatorios de entrenamiento, validación y test |
| DTD | DeepLumina, 73,63 % | Tabla 4, fila ResNet101 + SVM, RGB-YIQ, p. 11 | Sección experimental, p. 9, reparto aleatorio 80/20 |
| FMD | Neshov, 96,7 ± 1,9 % | Tabla 4, fila BEiTv2, p. 15 | Sección 3.1, p. 8, 10 repeticiones de validación cruzada de diez folds |
| FMD | DeepLumina, 90,15 % | Tabla 5, fila ResNet101 + SVM, RGB-YIQ, p. 12 | Sección experimental, p. 9, reparto aleatorio 80/20 |
| KTH-TIPS2-b | Neshov, 96,8 ± 2,5 % | Tabla 4, fila BEiTv2, p. 15 | Sección 3.1, p. 8, cuatro particiones fijas |
| KTH-TIPS2-b | HyTexNet, 99,79 % | Tabla 1, p. 7 | Discusión del dataset, p. 7, tercio de entrenamiento por pose, iluminación y escala |
| KTH-TIPS2-b | 6LBP+dCellNNs, 91,29 % | Tabla 4, p. 9 | Descripción experimental, p. 6, tercio por pose, iluminación y escala |
| CUReT en color | Paiva et al., 96,2 % | Tabla 5, fila Imp. 1, p. 9, proporción 0,962 | Sección 4.1, p. 5, validación cruzada de diez folds |
| Outex TC 00013 | Paiva et al., 96,3 % | Tabla 5, fila Imp. 1, p. 9, proporción 0,963 | Sección 4.1, p. 5, partición original |
| Soil aumentado | Neshov, 94,5 % | Tabla 4, fila BEiTv2, p. 15 | Sección 3.1, p. 9, 70/15/15 y aumento del entrenamiento |

Los autores de Chang et al. enlazan el repositorio [LBP_Contour](https://github.com/UESTC-nnLab/LBP_Contour). El README documenta un punto de entrada para Outex TC 00012. El número citado en nuestro cuadro corresponde a KTH-TIPS2-b y nuestro panel de Outex usa TC 00013, por lo que se conserva el localizador del artículo para ese 91,29 %. La existencia de ese código no verifica la reproducción de la fila de KTH.

La Tabla 5 de Paiva et al. selecciona por dataset el mejor resultado entre KNN, RF y SVM. Aunque Outex TC 00013 comparte el reparto oficial, nuestro E5 es una ablación pareada que fija SVM y añade RGB N-gramas + SVD, con la transformación ajustada en entrenamiento.

Las Tablas 4 y 5 de DeepLumina informan los valores puntuales por combinación del extractor y del canal. La comparación posterior del mismo artículo también presenta los valores 73,63 ± 0,5 y 90,15 ± 1,2. El manuscrito cita las tablas de configuración para identificar de manera inequívoca la fila ResNet-101 + SVM con RGB y luminancia YIQ.
