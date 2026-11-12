# Anexo: segunda pasada de disponibilidad de código

Fecha: 2026-11-03 (America/Asuncion). Alcance: continuación de la auditoría
de código de las referencias con concatenación/fusión. Se consultaron fuentes
editoriales/artículos y se hicieron búsquedas dirigidas en GitHub por nombre
de método/título. No se contactó a autores, no se descargó código, datos ni
pesos y no se ejecutaron repositorios.

## Hallazgos verificables

| Método | Declaración/publicación observada | Estado de código público | Implicación |
|---|---|---|---|
| AsTexNet (2026) | El PDF local declara datasets públicos, pero que los datos procesados y detalles de implementación se entregan por solicitud razonable al autor correspondiente. | No apareció un repositorio asociado al paper en la búsqueda exacta de GitHub (`AsTexNet`) ni un enlace GitHub en la declaración del artículo inspeccionada. | Los operadores pueden reconstruirse desde el artículo, pero no se dispone de la implementación del autor; una implementación propia debe rotularse como reimplementación/adaptación, no como ejecución del código original. |
| HyTexNet (2026) | El PDF local declara que datos y código estarán disponibles bajo solicitud razonable. La implementación local medida es `ADAPTADO`, no código del autor. | Sin resultado de repositorio para `HyTexNet` en la búsqueda exacta de GitHub. | Para recuperar la implementación/autenticidad del autor se requiere una vía autorizada de acceso; no inferir que el código no existe. Mantener separadas las tablas locales ya cerradas. |
| DeepLumina (2022) | El artículo describe RGB + luminancia YIQ, ResNet101 y clasificador SVM ECOC sparse-random; especifica 224×224 para ResNet, capa `fc1000`, y una partición aleatoria 80/20. Informa FMD 90.15% ±1.2 y DTD 73.63% ±0.5 en resumen; tablas dan valores puntuales. La sección final enlaza datasets, no código. | Sin repositorio encontrado con la búsqueda exacta `DeepLumina texture classification`; la ficha del artículo consultada tampoco enlaza un repositorio. | Candidato a reimplementación de método, no a reproducción exacta: el PDF no fija los índices/semillas de split 80/20, no se localizó la implementación MATLAB/ECOC, y “batch size 27” aparece en la sección de resultados sin aclarar su rol para el pipeline de extracción+SVM. Con particiones comunes locales, rotular como adaptación. |
| RGB Pixel N-grams (2023) | La fuente editorial describe dos implementaciones de n-grams RGB y experimentos de exactitud con tres clasificadores y cinco bases. No se localizó un enlace de código en la página del artículo consultada. | Sin repositorio encontrado con la búsqueda exacta `RGB pixel n-grams texture`. | El extractor local `rgb_ngram_svd` no equivale por sí solo a ambas variantes del descriptor original ni acredita el sistema completo. Habría que cerrar alfabeto, n, diccionario, variante, clasificadores y protocolo antes de preparar medición. |
| Compact color-texture (2015) | La página editorial confirma fusión de múltiples descriptores, compresión DITC y fusión tardía con nombres de color discriminativos; cuatro datasets, entre ellos FMD y KTH-TIPS-2b. | Sin repositorio encontrado con búsqueda de título/nombre en GitHub; el artículo y el registro público consultados no enlazan código. | No reemplazar DITC por PCA/SVD ni elegir uno de los clasificadores/color descriptors sin fijar la variante. Reimplementación posible solo tras cerrar las decisiones del paper desde la fuente completa. |
| LBP + dCellNN (Chang et al., 2024) | El artículo enlaza explícitamente `UESTC-nnLab/LBP_Contour`; `main_otc12.py` contiene el pipeline OTC12 y el checkpoint `cellnn_model.ph`. | Código público directo, pero el split del script inspeccionado (4560/4560, incluye imágenes de secuencias no-Inca en train) contradice el protocolo escrito del artículo (480 train / 8640 test). No se ejecutó. | Candidato de mayor cercanía a código de autores, pero no atribuir la cifra publicada sin resolver la discrepancia; requiere OTC12 y evaluación nueva. Los resultados locales KTH/Outex13 no son esta réplica. |
| Multiscale Analysis (Ataky et al., 2023) | El artículo enlaza `stevetmat/BioInspiredFDesc`. | Repo público MIT confirmado, pero los ficheros revisados describen BiT base y avisos de futuro código CMIG/EBiT, no un runner comprobado del pipeline/tablas 2023. | El enlace existe; la completitud del método del artículo no está verificada. No ejecutar como si fuera réplica completa. |
| Neshov et al. (2025) | La referencia de código del artículo apunta a material de partición/aumento de Sheth et al. (`Phantom-fs/Agro-Companion-Modules`). | El enlace existe, pero no se acredita como implementación de BEiTv2 + agregación multicapa + MLP de Neshov. | Las corridas FMD paperlike previamente cerradas siguen siendo aproximación, no resultado generado por el código de Neshov. No repetirlas. |

## Búsqueda y límites

Consultas de repositorio por `HyTexNet`, `AsTexNet texture classification`,
`DeepLumina texture classification`, `RGB pixel n-grams` y
`Compact color texture description texture classification` devolvieron cero
repositorios coincidentes en GitHub. También se hicieron búsquedas dirigidas
en web por esos nombres junto a `GitHub`, `code` y `code availability`.
Un cero en estas búsquedas significa solo **no localizado en el alcance y
fecha de la búsqueda**: no descarta repos privados, repos con otro nombre,
material suplementario no indexado o entrega por solicitud.

Fuentes primarias/de repositorio verificadas:

- AsTexNet: https://www.mdpi.com/2076-3417/16/12/5743
- HyTexNet: https://www.sciencedirect.com/science/article/pii/S095070512600225X
- DeepLumina: https://pmc.ncbi.nlm.nih.gov/articles/PMC9023203/
- RGB Pixel N-grams: https://www.sciencedirect.com/science/article/abs/pii/S0923596523001108
- Compact color-texture: https://www.sciencedirect.com/science/article/abs/pii/S0167865514002451
- LBP_Contour: https://github.com/UESTC-nnLab/LBP_Contour
- BioInspiredFDesc: https://github.com/stevetmat/BioInspiredFDesc
- Agro-Companion-Modules: https://github.com/Phantom-fs/Agro-Companion-Modules

## Decisión operativa

No hay un nuevo candidato listo para ejecutar que a la vez permita afirmar
"mismos números que el paper". Los dos pipelines adaptados ya evaluados y
los demás cierres anteriores se conservan intactos. Para avanzar sin
dependencias externas, la próxima tarea técnica de bajo riesgo es cerrar una
ficha de receta/ambigüedades de DeepLumina o RGB Pixel N-grams contra el PDF
completo y diseñar una evaluación etiquetada como adaptación en particiones
comunes; no se inicia una corrida hasta sellar esa ficha, recursos, versiones,
semillas y cronometraje. Para intentar equivalencia de implementación de
AsTexNet/HyTexNet haría falta recibir el paquete por el canal de acceso
permitido; esta auditoría no autoriza contactar autores.
