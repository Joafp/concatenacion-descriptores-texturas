# Revisión editorial para revista

**Candidato de referencia:** Pattern Recognition. El alcance editorial admite contribuciones originales de metodología y aplicación con respaldo en la literatura de reconocimiento de patrones. La contribución defendible aquí es la evaluación pareada de cuándo adquirir bloques adicionales para clasificar texturas. El ranking individual, las cascadas y el uso del margen tienen antecedentes. La sección de trabajos relacionados coteja el costo por modelo de IDK y la compuerta aprendida de Nan y Saligrama con la adquisición de bloques reutilizables y el control pareado de este estudio. [Wang et al.](https://arxiv.org/pdf/1706.00885) · [Nan y Saligrama](https://papers.nips.cc/paper_files/paper/2017/file/d9ff90f4000eacd3a6c9cb27f78994cf-Paper.pdf) [Alcance editorial](https://shop.elsevier.com/journals/pattern-recognition/0031-3203)

## Afirmaciones centrales y evidencia

| Afirmación | Evidencia rastreable | Alcance |
|---|---|---|
| Cuatro bloques son un punto de operación compacto | [Curvas por dataset](../../results/analysis/thesis_accuracy_primary_20261115_v3/per_dataset_curves.csv), [SVM](../../results/analysis/thesis_accuracy_primary_20261115_v3/static_accuracy_svm.csv), [ResMLP](../../results/analysis/thesis_accuracy_primary_20261115_v3/static_accuracy_resmlp.csv) | Elección exploratoria. El mejor tamaño depende de la cabeza y del dataset. |
| El margen ordena imágenes cuyo rescate puede compensar el costo | [Medias E1](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e1_complete_dataset_means.csv), [conteos pareados](../analisis_paper/e1_mcnemar_compuerta.csv), [control por condición](../analisis_paper/e1_condiciones.csv) | La comparación con el sorteo usa igual número de activaciones. El contraste contra Top-4 directo debe incluir su intervalo y la reserva sobre la elección retrospectiva. |
| La adquisición de bloques se abarata en E1 | [Auditoría de E1](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/README.md), [implementación de la proyección](../../scripts/run_top4_fixed_e1_e2.py) | Proyección de extracción. El ahorro físico de la cascada exacta sigue sin verificarse. |
| Otra política por margen reduce la latencia media medida en las doce combinaciones | [Panel online](../../results/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json), [medias por política](../../results/analysis/thesis_accuracy_primary_20261115_v3/online_means.csv), [percentiles](../analisis_paper/latencia_p95_reunida.csv) | Rescate por ensamble. La latencia de cola en Soil y la caída de accuracy en KTH-TIPS2-b delimitan la utilidad. |

La tabla de trabajos publicados tiene un [cotejo fila por fila con los PDF primarios](../../docs/fsc_tex/METRICAS_PUBLICADAS_Y_COMPARABILIDAD_2026-11-23.md#cotejo-de-las-11-filas-que-entran-al-manuscrito), con localizadores de cifras y protocolos.

La [versión en español](../main_topk_margen.pdf) conserva el formato de revisión de tesis e incluye las mismas figuras, tablas y referencias que la versión en inglés.

## Archivos editoriales para revisión

- [Highlights](Highlights.txt). Cuatro puntos editables de hasta 85 caracteres, conforme a la guía general de Elsevier. La guía de Pattern Recognition los requiere. [Instrucciones generales sobre highlights](https://www.elsevier.support/publishing/answer/how-do-i-include-highlights-with-my-manuscript)
- [Borrador de carta editorial](COVER_LETTER_DRAFT.md). Para revisión y firma de los autores antes de remitirla. Las confirmaciones sobre autoría, exclusividad, conflictos y financiamiento corresponden a los autores.
- El [manuscrito](../main_en.tex) documenta la ventana cronometrada de la evaluación online, los calentamientos, las llamadas del panel primario y la agregación. Se verificó contra el [ejecutor](../../scripts/benchmark_local_single_image.py) y la [auditoría de cobertura](../../results/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json).

## Pendientes de envío

1. La guía específica se consultó el 26 de noviembre de 2026. El PDF en inglés tiene 32 páginas y 38 referencias; usa una columna, Times New Roman y doble espacio. Se ajustaron los márgenes, los tamaños tipográficos, la numeración de anexos y la carta. La guía contiene dos formulaciones sobre el conteo de anexos. El manuscrito entra en el rango de 20 a 35 páginas contando el PDF completo y también sin las páginas que contienen únicamente anexos. [Guía para autores](https://www.sciencedirect.com/journal/pattern-recognition/publish/guide-for-authors)
2. Se confirmó ausencia de financiamiento y de conflictos de intereses. Quedan la aprobación del texto final, la revisión de contribuciones y exclusividad, y el archivo Word de la declaración de intereses que la guía pide generar con la herramienta de Elsevier. A pedido de Joaquín, el PDF de revisión omite el texto de asistencia de IA. La declaración para la versión de envío y los créditos de las figuras requieren revisión de los autores. [Política de IA de Elsevier](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)
3. La verificación de resultados archivados pasó en una exportación independiente de Git. Volver a entrenar o medir requiere los datasets y reconstruir los pesos, cabezas y embeddings en el entorno experimental. [Verificación reproducible](#verificar-la-evidencia-del-paper)
4. Para una cifra de ahorro físico de la cascada exacta queda pendiente su medición pareada. El manuscrito atribuye el ahorro del 75 % al modelo de extracción. [Alcance de las trazas disponibles](#alcance-de-las-trazas-disponibles)


## Empaquetar la versión para revisión

Desde la raíz del repositorio, con Python 3:

~~~bash
python3 scripts/package_topk_journal.py /tmp/topk_manuscrito_revista.zip
~~~

El ZIP lleva el PDF en inglés, su fuente, las referencias, los recursos necesarios para compilar, los highlights y el borrador de carta. Incluye hashes de los archivos. Para importarlo en Overleaf, el documento principal es **main_en.tex**. En una carpeta extraída, la compilación en inglés utiliza XeLaTeX y BibTeX. Con Times New Roman instalado, reproduce la tipografía de la revista. Verificamos los archivos del manifiesto y compilamos desde una extracción temporal. El texto del manuscrito coincide con el PDF suministrado.

## Compilar el borrador en inglés

Desde la raíz del repositorio, las figuras de resultados se pueden regenerar con Python y Matplotlib a partir del barrido interno de SVM y los CSV archivados. El diagrama vectorial se compila por separado desde su fuente TikZ. El ejemplo de textura se dibuja con rectángulos inclinados en TikZ. La imagen de DTD usada antes queda en el archivo histórico. La página de distribución describe DTD como un conjunto de imágenes de Google y Flickr para investigación. [Descripción de DTD](https://www.robots.ox.ac.uk/~vgg/data/dtd/)

~~~bash
python3 scripts/plot_paper_figures_20261123.py /tmp/tesis_figuras_en --language en --by-dataset
(cd carlos/figures/english && pdflatex -halt-on-error descriptor_pipeline.tex)
(cd carlos && xelatex -halt-on-error main_en.tex &&
 bibtex main_en && xelatex -halt-on-error main_en.tex &&
 xelatex -halt-on-error main_en.tex)
~~~

El primer comando escribe los gráficos recalculados en un directorio temporal. Los PDF versionados de los gráficos ya están en la ruta que lee el manuscrito. El PDF en inglés se compiló con Times New Roman. El código fuente recurre a TeX Gyre Termes cuando la fuente requerida no está disponible; en ese caso conviene usar el PDF verificado para la revisión de formato.

## Verificar la evidencia del paper

La [guía de disponibilidad](DATA_AVAILABILITY.md) identifica los seis manifiestos congelados, sus fuentes, sus hashes y el commit de los archivos de verificación.

Con Python 3.10 o posterior, desde la raíz del repositorio:

~~~bash
python3 scripts/verify_topk_paper_evidence.py
~~~

El comando usa la biblioteca estándar y deja el repositorio intacto. Recalcula las métricas por condición y el promedio por dataset de E1 con 31.984 predicciones. Comprueba los índices de test del protocolo congelado, la aplicación de la ruta guardada y los costos proyectados a partir de las constantes de extracción. Para el panel online verifica los SHA-256 de las 94 trazas, que las cinco políticas recibieron las mismas imágenes por condición y que cada imagen se midió una vez por política. Recalcula 470 filas de métricas por condición y política, 60 medias por dataset, cabeza y política, y las medianas y percentiles 95 de las 36 filas de latencia publicadas en el análisis del paper.

La comprobación pasó sobre una exportación con los 104 archivos de entrada versionados. Una edición deliberada en una copia de una traza produjo el error de hash esperado. El comando verifica agregados de predicciones y tiempos archivados. La verificación de cifras bibliográficas, la recuperación de todos los artefactos de entrenamiento y el cronometraje físico de la cascada Top-4 siguen sus propias fuentes y protocolos.


## Alcance de las trazas disponibles

| Evidencia | Cobertura y receta | Afirmación que respalda |
|---|---|---|
| [E1, auditoría](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/README.md) | 27 condiciones SVM. Top-4 fijo, 31.984 predicciones pareadas desde caché y perfiles por componente. | Calidad de E1 y costo de extracción proyectado. |
| [Piloto físico anterior de KTH](../../results/exploratory/topk_cascade/kth_tips2b/online_fair_topk/) | Cuatro particiones invertidas, 30 imágenes por condición, ResNet-50 inicial y uno o dos bloques de rescate según partición. Cuantil 0,50. | Latencia física de la receta histórica. La cascada supera en tiempo al uso directo en dos condiciones y pierde en dos. |
| [Panel online](../../results/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json) | 94 condiciones, seis datasets y dos cabezas. La política por margen rescata con un ensamble. | Latencia medida de esa política y sus controles. |
| [Preparación física de E1](../../results/analysis/top4_online_case_input_audit_20261116_v1/summary.json) | 24 casos con vinculación de entradas verificada. CUReT SVM s42 f0 y Soil SVM s42 f1 y f4 requieren revisión de fidelidad de ViT-B/16. | La vinculación de entradas es una comprobación previa. La medición pareada de las rutas de E1 sigue pendiente. |

La [inspección de procedencia de ViT](../../results/analysis/vit_provenance_20261116_v1/summary.json) mantiene abierta la identidad del productor histórico de los vectores. La [inspección del checkpoint local](../../results/analysis/vit_local_checkpoint_inspection_20261116_v1/summary.json) verifica sus archivos y configuración. El cotejo documental preserva los tres estados de revisión y las trazas de las corridas previas.


## Registro editorial de asistencia

OpenAI Codex (GPT-6) asistió en la reorganización y revisión de la prosa, la versión en inglés, la preparación en LaTeX y la comprobación de conteos contra archivos existentes. En las Figuras 1 y 2 asistió con el código TikZ y los rótulos. En las figuras de resultados asistió con el código y el rotulado de Matplotlib; los valores provienen de los CSV versionados. Los autores deben revisar el alcance completo antes del envío y confirmar si hubo herramientas adicionales.
