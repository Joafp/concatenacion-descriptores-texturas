# Resultado del primer piloto adaptado de Neshov en FMD

## Material Passport

- Origin Skill: ARS experiment-agent, ejecución y auditoría local.
- Origin Mode: run.
- Origin Date: 2026-10-28, America/Asuncion.
- Verification Status: ANALYZED; piloto de desarrollo y replay de cabezas, no reproducción de porcentajes publicados.
- Version Label: neshov_fmd_matched_development_result_v1.

## Qué se completó

La nueva comprobación funcional pasó con el checkpoint del paper disponible en caché. Se mantuvo carga estricta: los doce buffers posicionales regenerados coincidieron exactamente; no se eliminaron pesos aprendidos para evitar un fallo. Se preserva el intento fallido del 27-10.

Después se ejecutó el [protocolo fijado antes de extraer](PROTOCOLO_PILOTO_NESHOV_FMD_2026-10-28.md): BEiTv2 congelado, GAP de las cuatro capas, concatenación de 3.072 valores y MLP de 64 unidades. Se entrenaron tres cabezas nuevas durante 100 épocas fijas, sin seleccionar épocas con validación. Se usaron 800 imágenes de desarrollo FMD/42 en tres pliegues productores; cada imagen recibió una predicción de una cabeza que no se ajustó con ella. Las 200 imágenes externas quedaron excluidas.

La extracción y el ajuste se realizaron en CPU con dos hilos, sin ocupar la GPU compartida ni descargar pesos. El protocolo y sus hashes se conservaron sin modificaciones tras conocer el resultado.

## Calidad observada

- Macro-F1 agrupado de las 800 predicciones: **0,9459926699434446**.
- Exactitud agrupada: **0,94625** (94,625 %).
- Media aritmética de macro-F1 de los tres pliegues: **0,9461472743949386**. No es la misma cantidad que el F1 agrupado.

| Pliegue productor | Fit | Validación | Macro-F1 | Exactitud |
| --- | ---: | ---: | ---: | ---: |
| 0 | 533 | 267 | 0,940049 | 0,940075 |
| 1 | 534 | 266 | 0,950931 | 0,951128 |
| 2 | 533 | 267 | 0,947461 | 0,947566 |

## Comparación emparejada disponible

Todos los valores siguientes se recalcularon desde predicciones sobre **las mismas 800 filas, etiquetas y asignaciones a pliegues de FMD/42**. No son las medias de tres semillas de la comparación anterior ni la tabla de seis datasets proporcionada por el compañero. El MLP de referencia y los SVM son sistemas completos diferentes; este contraste no aísla la contribución del extractor manteniendo idéntico clasificador.

| Método | Clasificador | Macro-F1 agrupado | Exactitud |
| --- | --- | ---: | ---: |
| Neshov BEiTv2 adaptado | MLP (64) | 0,94599 | 0,94625 |
| Individual seleccionado | SVM | 0,97008 | 0,97000 |
| Completa-22 | SVM | 0,96131 | 0,96125 |
| Top-k con tamaño GFS | SVM | 0,97628 | 0,97625 |
| Top-4 | SVM | 0,97878 | 0,97875 |
| GFS | SVM | 0,97499 | 0,97500 |
| Ensamble de diversidad permanente, voto soft | SVM | 0,97878 | 0,97875 |
| Ensamble de diversidad, voto hard | SVM | 0,97752 | 0,97750 |
| Ensamble de tómbola, voto hard | SVM | 0,97751 | 0,97750 |
| Ensamble de tómbola, voto soft | SVM | 0,97752 | 0,97750 |
| Ensamble estático seleccionado | SVM | 0,97877 | 0,97875 |
| Selección y margen, pool previo | SVM | 0,97629 | 0,97625 |
| Selección y margen, pool con diversidad | SVM | 0,97751 | 0,97750 |

En este piloto, la adaptación del paper queda por debajo de los controles mostrados. La variante con margen y pool de diversidad queda, a su vez, ligeramente por debajo del ensamble permanente y Top-4 en esta condición concreta. No se oculta ese resultado por la mejora media observada previamente al agregar tres semillas FMD. No hay superioridad uniforme ni pruebas inferenciales nuevas.

## Auditoría realizada

- La salida final está completa y el proceso terminó correctamente; no se interpreta un timeout como resultado.
- Se verificaron hashes de fuentes, protocolo, manifiesto, particiones, imágenes y artefactos producidos.
- Se recargaron estrictamente las tres cabezas guardadas y se reprodujeron **exactamente sus logits y las 800 clases** a partir de las características guardadas.
- Se recalcularon F1/accuracy y se verificó la correspondencia exacta de filas, pliegues y etiquetas con cada control, cuya predicción archivada también conserva el hash de su auditoría.
- Pasaron **26 pruebas focalizadas** en 4,18 s. No se repitió ni se declara aprobada aquí toda la suite del repositorio.
- No se reextrajeron independientemente las 800 representaciones durante esta auditoría. El replay valida cabezas y métricas desde caché; no constituye paridad contra una salida oficial de los autores.

## Límites y próximos pasos

Esto es una **reimplementación adaptada al benchmark común**. Se conservan las decisiones explícitas de indexación desde 1, exclusión de CLS, interpolación y versiones de software del [registro de implementación](REPRODUCCION_NESHOV_BEITV2_2026-10-27.md). No se reprodujo el protocolo original FMD de 10 repeticiones de 10-fold ni se dispone de salidas oficiales para cotejo; no se afirma que los porcentajes publicados se hayan confirmado o refutado.

Todavía no se midió latencia de inferencia de este sistema ni de todos sus competidores bajo un régimen común. El tiempo de extracción del lote o de entrenamiento no se convierte en latencia por imagen. Quedan pendientes el cronometraje completo pareado, más semillas/datasets y la evaluación comparable de nuestra variante nueva en los seis conjuntos principales. No se reajustan los hiperparámetros de esta adaptación después de observar el F1 para mejorar su posición en la tabla.

No se cambió el manuscrito ni se reemplazaron tablas principales por este resultado exploratorio.

## Artefactos

- Ejecución: `results/exploratory/reference_papers/neshov_fmd_development_20261028/`.
- Auditoría y tabla completa de precisión íntegra: `results/analysis/neshov_fmd_matched_20261028/summary.json` y `matched_quality.csv`.
- Cabezas: `fold0_head.pt`, `fold1_head.pt`, `fold2_head.pt`.
- Características, logits, 800 predicciones, pérdidas de entrenamiento y hashes de imágenes preservados en la salida de ejecución.
- Código: `scripts/run_neshov_fmd_development.py`, `scripts/audit_neshov_fmd_development.py`, `src/neshov_reference_training.py`, `src/matched_reference_quality.py` y el extractor de referencia ya documentado.
