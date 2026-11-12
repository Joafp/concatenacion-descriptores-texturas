# Conciliación de sota-timing con el panel auditado — 8 de noviembre de 2026

Alcance: revisión documental y del código incorporado en `main` por el PR 6,
commit `f6de27f`, frente a las auditorías locales del 04-11. No se ejecutaron
modelos, se modificaron resultados sellados ni se verificaron de nuevo las
predicciones de Carlos. Sus cifras son las que declaran sus archivos; esta
conciliación no es una auditoría independiente de sus corridas.

Fuentes: [informe de Carlos](../../results/exploratory/sota_timing/README.md),
[tabla por método](../../results/exploratory/sota_timing/timing_all.csv),
[panel auditado](../../results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md),
[Neshov FMD 10×10](../../results/analysis/neshov_paperlike_fmd_10x10_consolidated_20261103_v1/INFORME.md).

## Comparabilidad

| Aspecto | Carlos | Panel local auditado | Decisión |
|---|---|---|---|
| Latencia | RTX 5060 Ti, extracción en lotes de 32 y componentes temporizados por separado; estimación por imagen, con o sin lectura | RTX 4060 Laptop, llamadas online de una imagen; F1 y tiempos de las mismas llamadas | No combinar como latencia individual homogénea. Los tiempos batch amortizados no prueban latencia batch=1. |
| Métricas | La tabla incluye accuracy y macro-F1; el informe destaca accuracy | macro-F1 por condición y accuracy reconstruidos de predicciones | Comparar únicamente la misma métrica y conservar unidad de agregación y cobertura. |
| FMD | Comparadores en 100 folds de 10×10; métodos propios en 5 folds | Panel común FMD con 15 condiciones; existe por separado Neshov paper-like 100/100 | No presentar los 5 folds y los 100 como comparación emparejada. Las dos 10×10 requieren verificar coincidencia exacta de IDs, semillas y receta. |
| KTH | RADAM separado por muestra física; además una aproximación al protocolo del paper HyTex | Panel por muestra física; otro experimento aproximado comparte 44 muestras físicas | No mezclar protocolos; la aproximación con muestras compartidas no mide generalización a muestra física nueva. |
| DTD | Diez particiones; train+validación en algunas variantes, imágenes test duplicadas retiradas | Diez condiciones HyTex y Neshov auditadas; reserva de duplicados | Verificar IDs y roles exactos antes de llamar a los resultados emparejados. |
| Outex13 | Partición oficial 680/680; hallazgo sobre cinco filas de dos embeddings | Comparaciones locales reconstruidas para 680 llamadas y hashes de imagen | La integridad de las imágenes y de las llamadas no verifica por sí sola la correspondencia imagen–embedding histórico. |

## Neshov: diferencias de implementación y números

El informe de Carlos atribuye a su versión la concatenación de las capas 2, 5,
8 y 11 y a la adaptación local 12 capas. El código de extracción de Carlos
documenta esas cuatro capas (`src/time_extraction.py`, 159–160), y su evaluador
carga `beitv2_base_multilayer` (`src/benchmark_sota_methods.py`). La descripción
del extractor aclara que la copia multicapa estaba guardada solo en KTH y que
en otros datasets se comprueba la salida final; esto no demuestra que se hayan
guardado los vectores exactos usados en todas las corridas publicadas. Debe
verificarse su procedencia y hash antes de afirmar identidad de entradas.

| Dataset | Macro-F1 Carlos | Macro-F1 panel/auditoría local | Interpretación |
|---|---:|---:|---|
| DTD | 0,79851 | 0,80203 | Diferencia −0,00352; variantes distintas, sin pareo comprobado. |
| KTH | 0,92847 | 0,92448 | Diferencia +0,00399; verificar IDs y muestras físicas. |
| FMD 10×10 | 0,94230 | 0,94192 | Diferencia +0,00038; cercanía descriptiva, no prueba de identidad de folds ni de método. |

Para FMD Carlos informa accuracy 0,9426 y la auditoría local 0,9422; el paper
publica 0,967. Son aproximaciones, no reproducción fiel confirmada. No se
comparan sus desviaciones como si usaran la misma unidad de agregación.

## HyTexNet: diferencias de entrenamiento y partición

Carlos ajusta `denseblock4` y `norm5` de DenseNet-121 y congela el resto
(`src/replicate_hytexnet.py`, 107–126); su informe indica que la adaptación local
utiliza DenseNet congelado. También documenta decisiones no especificadas del
paper, entre ellas tasa de aprendizaje y parada temprana. No se ha demostrado
una implementación idéntica a la original.

| Dataset/protocolo | Carlos | Auditoría local | Reserva |
|---|---:|---:|---|
| DTD, macro-F1 | 0,61138 | 0,62415 | Diferencia −0,01277; adaptación y entrenamiento diferentes. |
| KTH, muestra física separada, macro-F1 | 0,83996 | 0,82586 | Diferencia +0,01410; no atribuir la causa exclusivamente al ajuste del bloque. |
| KTH aproximado al paper, accuracy | 0,987 declarada | F1 0,93944 | Son métricas diferentes y selecciones aproximadas; no restarlas ni concluir identidad de receta. |

La cifra 0,987 de Carlos no demuestra por sí sola que la transcripción sea
correcta ni que las selecciones de poses, escalas y semillas sean las del autor.

## Outex13: estado de la alerta

Carlos informa que los índices 991, 1034, 1137, 1302 y 1329 de los embeddings
ViT-B/16 y DeiT-S no encajan en el ajuste afín entre CLS y el `pooler_output`
guardado. `src/check_outex_pooler.py` calcula dicho ajuste y vuelve a extraer
CLS en GPU. En los artefactos examinados no se localizó una salida persistida
con los cinco diagnósticos individuales, por lo que se conserva como **alerta
de Carlos pendiente de verificación independiente**, no como origen demostrado
ni como impacto cuantificado en F1. Los índices son posiciones cero-basadas
del array según el código. El cruce de solo lectura con el manifiesto ordenado
por `row_id` da:

| Fila/ID | Clase | Rol oficial | SHA-256 de la imagen |
|---:|---|---|---|
| 991 | sandpaper004 | test | `92074574874cd8aea048aefe233a0144d740edeed105f4c3d7e98a25e8a3f39d` |
| 1034 | sandpaper006 | train | `badd035895c84a9b5ff7455d13bc79c9ab4d7bfbffc39b245755fd93afba0322` |
| 1137 | wood001 | test | `c41b0dd44c06f169b654123b1eb52e077b3595dcabcc071cf343a6b5c85ecb04` |
| 1302 | barleyrice009 | train | `4bf2f2e9a093023e973010c480b8e5ac75961d4192e8f1a07d93ff71883d8c3c` |
| 1329 | barleyrice010 | test | `a803808aa922bd90d850d19c28afec447bb8c851559f5f7f252e92ceef3ad4ac` |

Son tres filas de test y dos de train bajo el reparto indicado en el manifiesto;
queda por establecer qué métodos usaron esos bloques y cómo llegaron a sus
predicciones. El chequeo de hashes de
imagen de la auditoría previa no resuelve por sí mismo esa correspondencia.

No volver a extraer ni modificar embeddings por esta alerta. Siguiente análisis
de solo lectura: localizar registros del diagnóstico y filas usadas
por cada método; documentar dependencias y definir una prueba
independiente congelada antes de cualquier extracción o reevaluación. No
asegurar que cinco filas alteran la exactitud ni que el problema afecta todas
las estrategias sin ese cruce.

## Siguientes pasos

1. Localizar recibos, predicciones, hashes y configuraciones de las corridas de
   Carlos; auditar cobertura y correspondencia de IDs antes de incorporar sus
   cifras al tablero. Si no existen, etiquetar como reporte exploratorio.
2. Trazar los bloques seleccionados por cada estrategia Outex y conservar la
   evidencia de las cinco filas del manifiesto, sin modificar datos observados.
3. Comparar código y versiones de pesos para Neshov e HyTex contra las fuentes
   primarias, separando supuestos de decisiones confirmadas.
4. Diseñar, solo si procede, mediciones nuevas batch=1 con la misma llamada
   para F1 y tiempo, CPU de dos hilos y lock GPU; no sustituir ni repetir
   automáticamente resultados cerrados ni estados `requires_review`.
5. Mantener DeepLumina bajo revisión por no convergencia y DTD 9/10; no
   cambiar manuscrito ni presentación como parte de esta conciliación.

## Huellas de las fuentes revisadas

- README Carlos: `0cbff2e00a184565c2f4fcca5b7b6ad18621c08350b257edbb89d17d667048e7`.
- `timing_all.csv`: `bb67d0a65b07d34d9d016669c8e86a47c335ba3e9bd9b7c318d0161e4f1cf970`.
- `check_outex_pooler.py`: `53bd46dc5ae2c36cdebc2c8631fc7f7b0c6aa2dc5ad59ff087206e1081ad0cc6`.
- `replicate_hytexnet.py`: `5b5f1bed5fc301b9532b6a53d566386acc457b3a888754f2a0a24d607440d28a`.
- `benchmark_sota_methods.py`: `954ee028dffbb419fc01d691f93cc1d558f5d36f3ec6db48f82d3993e9c55ebc`.
