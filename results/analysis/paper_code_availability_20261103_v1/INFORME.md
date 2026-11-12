# Auditoría de disponibilidad de código de papers de textura

**Fecha de búsqueda:** 2026-11-03. **Alcance:** los 11 PDFs indexados en `docs/referencias/README.md`; comprobación de declaraciones de código/datos en los artículos y búsqueda dirigida por título en páginas editoriales y GitHub. Se consultaron los artículos o páginas editoriales primarias y los repositorios enlazados por ellas cuando estaban disponibles. Búsquedas negativas significan «no localizado en este alcance», no prueba de inexistencia.

## Resultado ejecutivo

Hay dos repositorios públicos vinculados directamente por los artículos a métodos del conjunto de referencias: `LBP_Contour` y `BioInspiredFDesc`. El primero ofrece código de la fusión LBP+dCellNN y un punto de entrada explícito para OTC12, aunque la inspección web superficial no acredita un entorno reproducible para todos los datasets/splits ni una licencia explícita en la raíz. El segundo es el repositorio enlazado por el artículo de análisis multiescala y tiene licencia MIT; su README se identifica principalmente con BiT v0.1.5 y anuncia carpetas/código de publicaciones relacionadas, así que falta validar que reproduzca el pipeline completo y sus tablas del artículo de 2023.

Neshov sí enlaza el repositorio `Phantom-fs/Agro-Companion-Modules`, pero el artículo lo cita para código de partición y aumento de entrenamiento y el propio README atribuye ese proyecto a otro artículo de clasificación de suelos (Sheth et al.). No es el código completo de BEiTv2 + agregación multicapa + MLP de Neshov. Para los otros ocho registros no localicé una publicación directa de código del método en esta búsqueda. Esto no equivale a probar que no exista un repositorio privado/no indexado.

**Conclusión sobre “mismos números”:** hallar el código es una oportunidad para una réplica verificable, no evidencia de que ya reprodujimos los valores del paper. Ningún repositorio se clonó ni ejecutó durante esta auditoría; no se descargaron pesos/datasets. Los resultados locales ya existentes son comparaciones adaptadas o aproximadas, no resultados producidos por esos repositorios. En consecuencia, hoy no podemos afirmar que tenemos los mismos números publicados.

## Inventario de los 11 artículos

| Paper local | Código localizado / calidad de evidencia | Estado para conseguir números comparables |
|---|---|---|
| García & Puig (2007), integración supervisada por píxel | No localicé código oficial por DOI/título. Es clasificación por píxel y ventanas, distinta de la tarea actual de clasificación por imagen; no conviene tratarlo como la misma receta sin redefinir evaluación. | No replicable aún con evidencia localizada; primero habría que fijar una tarea equivalente. |
| Puig et al. (2010), selección de características independiente de aplicación | No localicé repositorio oficial. El artículo describe selección/integración de métodos y experimentos de clasificación de textura. | La implementación local de selección anidada por dataset no es este procedimiento global. Aún no hay base para decir paridad. |
| Khan et al. (2015), descriptor compacto color-textura | No localicé repositorio oficial. La receta del paper incluye cinco descriptores, DITC supervisado y fusión tardía con color discriminativo; sustituir DITC por PCA/SVD o usar otro descriptor no sería el método. | Dependencias de la receta siguen pendientes. KTH-TIPS-2b y FMD tienen protocolos distintos de los usados localmente; no comparar directamente el número publicado. |
| Simon & Uma (2022), DeepLumina | No localicé código enlazado por la página editorial ni por la búsqueda dirigida. El artículo describe extracción ResNet101 y luminancia YIQ, con clasificación SVM. | Los bloques ResNet/SVM locales no bastan para llamar al sistema DeepLumina; hacen falta la receta completa, split y preprocesamiento. |
| Ataky et al. (2023), análisis multiescala | **Sí:** el artículo enlaza [BioInspiredFDesc](https://github.com/stevetmat/BioInspiredFDesc); el repo es público y lista licencia MIT. El README identifica BiT v0.1.5 y menciona carpetas de trabajos relacionados, pero su inspección offline encontró que CMIG/EBiT aún contienen avisos, no el código de esas publicaciones. | No se acreditó código/receta para regenerar las tablas del pipeline multiescala de 2023. Además, el artículo usa KTH-TIPS original y Outex TC00011-r, no las variantes locales KTH-TIPS2b/Outex TC00013. |
| Chang et al. (2024), LBP multiescala + contornos dCellNN | **Sí, evidencia directa fuerte:** el artículo declara abiertos los códigos y enlaza [UESTC-nnLab/LBP_Contour](https://github.com/UESTC-nnLab/LBP_Contour). Repo público con `cellnn.py`, `train.py`, `tools.py`, `main_otc12.py` y `cellnn_model.ph`; README instruye correr `main_otc12.py` para OTC12. | Es el candidato prioritario para revisión de código completo. Aún no se ejecutó; README pequeño y sin licencia evidente en el listado raíz. El protocolo local KTH comparte imágenes físicas entre fit/test y el paper usa OTC12, mientras que el dataset local es Outex TC0013: hay que mantener estas diferencias explícitas. |
| Gupta et al. (2026), HyTexNet | No localicé repositorio del artículo enlazado por la página editorial ni búsqueda GitHub por título. La fuente local describe DenseNet-121 + codificación local por percentil y fusión. | La adaptación HyTexNet local ya medida no es código de autores; las métricas paperlike KTH son 0.93908 accuracy y 0.93944 macro-F1 frente a 0.9979 accuracy reportada, bajo split aproximado con 44 muestras físicas compartidas. No reproducido. |
| Paiva Pavón et al. (2023), RGB Pixel N-grams | No localicé repositorio oficial por título/DOI/GitHub. | El bloque local basado en SVD no equivale a secuencias RGB n-gram. No afirmar reproducción. |
| Gupta et al. (2026), AsTexNet | No localicé repo del método en la página/paper y búsqueda dirigida. El paper especifica MobileNetV2, descriptores locales multiescala, ponderación y embedding compacto. | En local sólo están probados operadores aislados; el documento de readiness marca dependencias del sistema completo pendientes. No es método completo ni reproduce números. |
| Neshov et al. (2025), agregación multicapa preentrenada | El artículo señala que el código para dividir datos y hacer aumento de entrenamiento está en la referencia [46]. Esa referencia lleva a [Agro-Companion-Modules](https://github.com/Phantom-fs/Agro-Companion-Modules), repo público sobre clasificación de suelos, cuyo README atribuye el código a **Sheth et al.**, no al método de agregación BEiTv2 de Neshov. La página del paper describe BEiTv2 y otros backbones, GAP, concatenación de capas y MLP; el repo enlazado no constituye ese sistema completo. | Neshov paperlike FMD 10×10 ya cerrado localmente: accuracy 0.94220, macro-F1 0.94192, 16.767 ms; paper 0.967 accuracy. La corrida es aproximada y versiones/protocolo difieren. La extensión batch-1 es adaptación del sistema Neshov, tampoco reproducción del porcentaje. No repetir esas corridas. |
| Scabini et al. (2024), survey comparativo de ViTs | No corresponde a un método único nuevo que se replique; no localicé código propio del survey. El repositorio VORTEX, cuando aparece en la literatura vecina, es otro método/paper y no debe adjudicarse al survey. | Comparar los métodos que el survey cita requeriría escoger uno por separado y auditar su protocolo/código. |

## Qué se verificó sobre los dos repositorios más directos

- **LBP_Contour:** el artículo del editor dice explícitamente que el código fuente está abierto en el enlace GitHub. El listado y lectura de `main_otc12.py` confirman extracción/fusión multiescala, `cellnn_model.ph`, split OTC12 codificado y MLP; no se halló `requirements.txt` ni licencia en la raíz visible. Es el candidato de réplica de mayor fidelidad si se fija el entorno y se valida el protocolo del paper. No fue ejecutado ni se verificó el hash del checkpoint. [Artículo](https://www.sciencedirect.com/science/article/pii/S0957417423026027) · [Repositorio](https://github.com/UESTC-nnLab/LBP_Contour).
- **BioInspiredFDesc:** el artículo de MDPI enlaza la fuente GitHub y el repo enumera licencia MIT y BiT v0.1.5. La lectura de `main.py` solo acredita extracción de un ejemplo; los README de CMIG/EBiT son avisos de código futuro, no scripts de evaluación. No hay evidencia suficiente para regenerar las tablas del paper multiescala. [Artículo](https://www.mdpi.com/2076-3417/13/3/1291) · [Repositorio](https://github.com/stevetmat/BioInspiredFDesc).
- **Neshov:** la inspección del PDF local confirma que el artículo refiere el código de splitting/augmentation a la cita [46]. La bibliografía de ese mismo PDF identifica [46] como Sheth et al., `Agro-Companion-Modules`; su README declara el propósito de clasificación de suelo, describe notebooks de splitting/preprocesamiento, fine-tuning y ensembles, y atribuye el proyecto a aquel artículo. No hay base para atribuirle el algoritmo BEiTv2+GAP-concat+MLP de Neshov. [Artículo Neshov](https://www.mdpi.com/2079-9292/14/23/4779) · [Repo citado por Neshov](https://github.com/Phantom-fs/Agro-Companion-Modules).

## Por qué un repo no garantiza “el mismo número”

Para atribuir el porcentaje impreso hace falta confirmar la versión/commit de código y checkpoints, variante exacta del dataset, índices de train/test y grupos físicos, preprocesamiento, hiperparámetros/selección, semilla y métrica/agregación. Además, un tiempo de inferencia debe medirse en el mismo protocolo y junto con las predicciones de las que se calcula F1; no emparejar F1 histórico con tiempos nuevos. Es particularmente importante para KTH/DTD, donde una partición por imágenes puede filtrar ejemplares/materiales entre train y test. Neshov reporta accuracy publicada, no macro-F1, por lo que esos valores tampoco son intercambiables.

Los resultados locales ya auditados ilustran la diferencia: HyTexNet paperlike-KTH (0.93908 acc; paper 0.9979), LBP+dCellNN paperlike-KTH (0.66004; paper 0.9129) y Neshov paperlike-FMD (0.94220; paper 0.967). Los primeros dos emplean la selección KTH aproximada con 44 muestras físicas compartidas y versiones/supuestos locales; el tercero adapta 10×10 a la receta descrita, sin índices/autores confirmados. Son resultados transparentes con diferencias; no deben retocarse para acercarlos al artículo.

## Inspección técnica offline de los dos repositorios (2026-11-03)

Se revisaron desde las páginas públicas los README y archivos de entrada relevantes, sin clonar ni ejecutar código.

| Repositorio | Evidencia concreta del flujo | Dependencias/assets/licencia | Juicio de reproducibilidad |
|---|---|---|---|
| `UESTC-nnLab/LBP_Contour` | `main_otc12.py` carga `cellnn_model.ph`, calcula LBP fusionado con mapas de contorno CellNN a varias escalas, usa `Outex_TC_00012` y un `MLPClassifier(hidden_layer_sizes=400, max_iter=10000)`. Mide extracción y clasificación por separado. | Checkpoint en raíz; sin `requirements.txt` ni licencia visible; rama `main` fijada en commit `89fc3d6097ab13f800c8d2828f4d6ed2225f3eb1`. Versiones/hash del checkpoint no verificados. | El flujo existe, pero su split 4560/4560 contradice el del paper (480/8640); no es candidato para reproducir fielmente la cifra publicada sin resolver la discrepancia. Resultados locales previos son Outex TC0013/KTH aproximado, no OTC12. Código: [entrada OTC12](https://github.com/UESTC-nnLab/LBP_Contour/blob/main/main_otc12.py), [entrenamiento CellNN](https://github.com/UESTC-nnLab/LBP_Contour/blob/main/train.py). |
| `stevetmat/BioInspiredFDesc` | El `main.py` público solo toma `resources/test.png`, instancia `ClassBit.BiT(...)` y extrae/visualiza un vector. El README identifica el repositorio como BiT v0.1.5, no un runner de las tablas del artículo de 2023. El README dentro de `CMIG` es un aviso de que se agregarían códigos del artículo de análisis multiescala en histopatología; el README de `EBiT` es otro aviso de código futuro. | La raíz indica licencia MIT. En las carpetas CMIG/EBiT, los READMEs consultados son avisos, no recetas. No apareció `requirements.txt` en la ruta consultada; no se verificaron submódulos/dependencias o assets. | Corrijo la lectura inicial: aunque el artículo enlaza este repositorio, la evidencia vista **no demuestra que esté disponible la implementación completa de ese artículo**. Hay código del descriptor BiT base, pero no un pipeline que replique las tablas de 2023. No es actualmente candidato para recuperar “los mismos números” de ese artículo solo a partir de esta raíz. [árbol y README](https://github.com/stevetmat/BioInspiredFDesc), [main.py](https://github.com/stevetmat/BioInspiredFDesc/blob/main/main.py), [aviso CMIG](https://raw.githubusercontent.com/stevetmat/BioInspiredFDesc/main/CMIG/README.md). |

### Qué significa para la continuación

1. **Candidato bloqueado: LBP_Contour en OTC12.** Antes de medir hay que obtener OTC12 por vía autorizada y resolver split/semilla/licencia. El script actual no sigue el split del paper. Una versión con 480/8640 y wrapper de cronometraje sería una reimplementación adaptada, en una cola nueva con predicciones y latencias de las mismas llamadas; no ejecutarla como si fuera el script original.
2. **No promover BioInspiredFDesc a reproducción completa** sin localizar una versión con los archivos del artículo multiescala, receta de datos y scripts de evaluación. El enlace editorial al repositorio por sí solo no resuelve esa carencia.
3. No reutilizar los resultados locales KTH/TC0013 de LBP como si fueran OTC12; tampoco volver a correr los paneles ya cerrados. Una ejecución del repositorio LBP sería un experimento aparte, no una corrección retroactiva de los resultados de adaptación.

**Estado:** revisión técnica offline completada; no se lanzó benchmark. Resultado: un repo es candidato para una réplica por dataset (LBP_Contour/OTC12) con requisitos pendientes; el otro solo permite reproducir el extractor BiT del ejemplo, no se acreditó el método completo del paper enlazado.

## Preflight OTC12 y discrepancia paper/código — 2026-11-03

La comparación del código con el PDF local de Chang et al. encontró un conflicto de protocolo que impide llamar a una corrida del repositorio “reproducción fiel”:

- El paper especifica 9.120 imágenes OTC12: las 480 imágenes `inca`, ángulo 0°, para entrenamiento; las otras 8.640 para prueba (razón 1:18). La tabla reporta 99,18% para `6LBP+dCellNNs`.
- En `main_otc12.py` de la rama `main` fijada a `89fc3d6097ab13f800c8d2828f4d6ed2225f3eb1`, `OutexDataLoad` asigna 4.560 filas a train y 4.560 a test. En cada clase mueve a entrenamiento los primeros 85 ejemplos de **cada una** de dos secuencias no-Inca (IDs `480 + ...` y `4800 + ...`) y deja los 95 restantes de cada secuencia en test. Sumado a los 480 Inca, el resultado es 4.560/4.560. Así parte de las iluminaciones que el paper reserva para test participa en el ajuste del MLP.
- El workspace solo contiene Outex TC0013: `data/Outex` está vacío. No es posible correr OTC12 sin incorporar el dataset.

Fuentes: [PDF local del paper](../../../docs/referencias/1-s2.0-S0957417423026027-main.pdf), [script OTC12](https://github.com/UESTC-nnLab/LBP_Contour/blob/main/main_otc12.py), [commit fijado](https://github.com/UESTC-nnLab/LBP_Contour/commit/89fc3d6097ab13f800c8d2828f4d6ed2225f3eb1), [página editorial que enlaza el repo](https://www.sciencedirect.com/science/article/abs/pii/S0957417423026027), [descripción Outex TC12](https://color.univ-lille.fr/datasets/extended-outex).

**Decisión:** no ejecutar el script tal cual y atribuir su resultado al split del paper; tampoco corregir la partición a escondidas. El MLP no fija `random_state`; el repo no muestra licencia ni `requirements.txt` en la raíz; el script separa cronómetro de extracción y de `score`, mientras la comparación común exige predicciones y latencia por la misma llamada online. Antes de una medición hacen falta OTC12 autorizado, reconciliación explícita de split, entorno y licencia. Una posible ejecución con 480/8.640, semilla fijada y temporización online sería una **reimplementación adaptada del método bajo el protocolo del paper**, no ejecución exacta del script público. Se requiere manifiesto y directorio nuevos; no cambiar resultados anteriores.

El checkpoint público `cellnn_model.ph` es pequeño (10,1 KB). Commit de la rama principal consultado por `git ls-remote`: `89fc3d6097ab13f800c8d2828f4d6ed2225f3eb1`. No se clonó ni ejecutó código ni se descargó el checkpoint o el dataset. Estado: **preflight completado, medición no iniciada**; no se adquirió lock GPU. La GPU estaba libre en la inspección.

## Siguiente paso recomendado

Preparar, antes de cualquier corrida, un manifiesto nuevo para una eventual réplica LBP_Contour/OTC12 que pinne commit/checkpoint y describa entorno, dataset, split, semillas, salida de predicciones y cronometraje online. No descargar recursos grandes hasta inventariar necesidad/tamaño; no correr todavía si falta permiso de licencia o split/asset reproducible. Para BioInspiredFDesc, continuar solo una búsqueda focalizada de un release/código suplementario del paper de 2023, sin dar por suficiente el repositorio base. Neshov, KTH y extensiones ya cerradas no se repiten.

**Límites de esta auditoría:** búsquedas de código a fecha indicada y en fuentes públicas localizadas; no incluye repos privados, comunicaciones a autores ni revisión/ejecución de todo el código de terceros. No se clonó repositorio ni se descargó un peso. Los PDFs locales no se enviaron a servicios externos. Investigación asistida por IA; las afirmaciones de disponibilidad se apoyan en los artículos/repos enlazados arriba.

## Segunda pasada: disclosures de disponibilidad y búsquedas exactas en GitHub

La segunda pasada confirma que AsTexNet declara que los datos procesados y los
detalles de implementación se entregan por solicitud razonable, y HyTexNet
declara código/datos por la misma vía. Las búsquedas exactas de repositorios
GitHub para HyTexNet, AsTexNet, DeepLumina, RGB Pixel N-grams y Compact
color-texture no arrojaron repositorios coincidentes. Esto solo significa
“no localizado en esta búsqueda”; no descarta repositorios con otro nombre,
privados o materiales no indexados.

DeepLumina describe su pipeline RGB + luminancia YIQ, ResNet101 y SVM, pero la
sección de disponibilidad del artículo inspeccionado enlaza los datasets y no
un repo de código. RGB Pixel N-grams describe dos variantes, pero tampoco se
localizó una URL de implementación en su registro editorial. Son métodos que
podrían reimplementarse desde las recetas, no fuente original ejecutable para
recuperar sin ambigüedad el porcentaje publicado. La ficha extensa, búsquedas,
límites y decisión están en
[`ANEXO_BUSQUEDA_CODIGO_20261103.md`](ANEXO_BUSQUEDA_CODIGO_20261103.md).
