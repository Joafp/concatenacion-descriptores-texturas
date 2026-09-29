## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run + reproducibility audit
- Origin Date: 2026-09-26
- Verification Status: ANALYZED (Outex/DTD official splits; CUReT condition halves; adapted KTH LOPO; online timing completed)
- Version Label: adaptive_sample_generalization_v2

# Evaluación adaptativa de bloques en splits oficiales y protocolos por muestra

## Protocolo congelado

Se mantuvo ResNet-50 primero, BEiTv2-final como bloque adicional, SVM lineal,
semilla 42, mediana de márgenes OOF calculados solo dentro del entrenamiento
externo y presupuesto objetivo de 50%. Se usaron cuatro folds internos
agrupados en Outex, DTD y CUReT; en KTH, por la adaptación leave-one-sample-out,
se usaron tres folds internos agrupados por `label::sample`. El control
aleatorio solicita exactamente el mismo número de bloques extra que la regla
adaptativa, con 200 asignaciones por split. Todas las métricas externas son
descriptivas.

La ruta respetó el split oficial de Outex13, los diez splits oficiales de DTD
y los dos sentidos `curet_half_indices` de CUReT. KTH usa una adaptación
explícita de los cuatro splits por muestra: invierte los roles de train/test
del protocolo oficial para entrenar con tres muestras físicas y reservar una.
No se presenta como réplica de la dirección Caputo ni como baseline
directamente comparable.

## Outex13Official1360: resultado offline

El manifiesto y la auditoría oficial PASS identifican 1.360 imágenes, 68
clases, 680 imágenes de entrenamiento y 680 de prueba, sin grupos compartidos
entre esos lados. Los embeddings contienen 2.048 dimensiones para ResNet-50 y
768 para BEiTv2-final. El umbral OOF fue 0,808129; la ruta solicitó BEiTv2 en
299/680 imágenes (43,97%).

| Ruta | Macro-F1 | Accuracy | Fracción con BEiTv2 |
|---|---:|---:|---:|
| Solo ResNet-50 | 0,8809 | 0,8853 | 0% |
| Adaptativa, objetivo 50% | 0,9101 | 0,9132 | 43,97% |
| Aleatoria, mismo conteo (media; SD) | 0,8945; 0,0048 | 0,8981 | 43,97% |
| ResNet-50 + BEiTv2 siempre | 0,9101 | 0,9132 | 100% |

La igualdad de macro-F1 entre adaptativa y dos bloques siempre depende de este
split: las 69 predicciones distintas entre los clasificadores base y completo
están dentro del conjunto solicitado por la regla. No es garantía para otros
datasets o particiones.

## DTD: diez splits oficiales

Los diez splits tuvieron 47 clases y 1.880 muestras de test cada uno; el lado
de entrenamiento tuvo entre 3.749 y 3.757 muestras. La auditoría oficial
`PASS_OFFICIAL_SPLITS_PURGED_DUPLICATES` elimina del entrenamiento copias SHA
que cruzan roles. En todos los outer splits se verificó intersección de grupos
cero; cada uno de los cuatro folds OOF internos conservó las 47 clases. El
presupuesto objetivo fue 50%, con fracción observada de solicitud entre 45,74%
y 48,88%.

| Ruta | Macro-F1 medio (10 splits) | Rango | BEiTv2 solicitado medio |
|---|---:|---:|---:|
| Solo ResNet-50 | 0,7303 | 0,7114–0,7447 | 0% |
| Adaptativa, objetivo 50% | 0,8115 | 0,7931–0,8174 | 47,16% |
| Aleatoria, mismo conteo (media por split) | 0,7703 | 0,7525–0,7796 | 47,16% |
| ResNet-50 + BEiTv2 siempre | 0,8151 | 0,7960–0,8223 | 100% |

La ruta adaptativa quedó por debajo de los dos bloques siempre en cada uno de
los diez splits. Las particiones oficiales se solapan; estas medias y rangos
son descriptivos y no se usaron como diez réplicas independientes para una
prueba inferencial.

## CUReT: mitades agrupadas por condición

Se evaluaron ambos sentidos de `curet_half_indices`: `a_to_b` (46 grupos
condición para train, 46 para test) y `b_to_a`. Son mitades alternadas
deterministas del subset auditado Oxford de 5.612 imágenes/61 clases; no se
afirma que reconstruyan la asignación histórica no publicada. En ambos
sentidos no hubo intersección de grupos, los cuatro folds OOF internos
conservaron las 61 clases y se verificaron SHA-256 de las 5.612 fuentes.

| Sentido | Ruta | Macro-F1 | Accuracy | Solicitud BEiTv2 |
|---|---|---:|---:|---:|
| a_to_b | Solo ResNet-50 | 0,9572 | 0,9572 | 0% |
| a_to_b | Adaptativa | 0,9915 | 0,9914 | 45,87% |
| a_to_b | Aleatoria, mismo conteo (media; SD) | 0,9730; 0,0018 | 0,9730 | 45,87% |
| a_to_b | Dos bloques siempre | 0,9915 | 0,9914 | 100% |
| b_to_a | Solo ResNet-50 | 0,9678 | 0,9679 | 0% |
| b_to_a | Adaptativa | 0,9961 | 0,9961 | 41,02% |
| b_to_a | Aleatoria, mismo conteo (media; SD) | 0,9795; 0,0017 | 0,9795 | 41,02% |
| b_to_a | Dos bloques siempre | 0,9961 | 0,9961 | 100% |

La igualdad adaptativa/full en ambos sentidos es propia de estas predicciones:
en estos tests las diferencias entre base y full quedaron cubiertas por las
solicitudes. La fracción es una decisión por umbral, no una cuota; los dos
sentidos tampoco se tratan como réplicas independientes.

## KTH-TIPS2-b: LOPO adaptado, 3 muestras train / 1 held-out

El protocolo fuente Caputo entrena con una muestra física y prueba en las
otras tres. Aquí, conforme al alcance autorizado, cada columna oficial
`split_1..4` se invirtió para reservar su muestra de train como held-out y
entrenar con las otras tres. Es por tanto un leave-one-physical-sample-out
adaptado, no el protocolo Caputo ni una comparación directa con sus baselines.
Se usó OOF interno de tres folds agrupados por `label::sample`; cada fold
interno conservó las 11 clases. Cada split tuvo 3.564 filas train candidatas y
1.188 held-out; la purga posterior a la inversión quitó cero filas en los
cuatro casos. Se verificó cero intersección SHA de imágenes y cero intersección
de muestra física entre train/test, así como SHA de las 4.752 fuentes por
split. Los grupos son 33 `label::sample` para train y 11 para test.

| Ruta | Macro-F1 medio (4 splits) | Rango | BEiTv2 solicitado medio |
|---|---:|---:|---:|
| Solo ResNet-50 | 0,8577 | 0,8280–0,8876 | 0% |
| Adaptativa | 0,9399 | 0,9053–0,9758 | 44,55% |
| Aleatoria, mismo conteo (media por split) | 0,8986 | 0,8715–0,9258 | 44,55% |
| ResNet-50 + BEiTv2 siempre | 0,9424 | 0,9053–0,9833 | 100% |

La ruta adaptativa fue igual o inferior a dos bloques siempre en los cuatro
splits (empate en split 2). El objetivo 50% no es un presupuesto exacto:
debido al umbral congelado, la solicitud por split varió de 35,02% a 59,85%
(split 4). Las particiones comparten muestras de entrenamiento; no se hizo
inferencia estadística ni comparación con resultados del protocolo Caputo.

## Comparación descriptiva con métodos principales

Los resultados de referencia pertenecen al mismo split oficial Outex13, SVM,
semilla 42 y métrica macro-F1; por tanto la comparación de puntuación es
descriptivamente equiparable. La adaptativa de dos bloques obtuvo 0,9101 frente
a 0,9426 para Top-k individual, 0,9589 para GFS y 0,9656 para la concatenación
de 22 descriptores. No se afirma superioridad en precisión ni una frontera
precisión-costo: las latencias de Top-k, GFS y 22 descriptores no se midieron
con la misma ruta en este ensayo. La regla adaptativa queda por debajo de los
tres baselines en macro-F1 en este test.

En DTD, las diez particiones oficiales también coinciden con las filas seed
42/SVM de los baselines principales (split oficial 1–10 mapeado a fold 0–9).
La adaptativa obtuvo macro-F1 medio 0,8115, frente a 0,8700 para Top-k22,
0,8703 para GFS y 0,8639 para full22. La adaptación queda por debajo de esos
baselines y de la fusión fija de dos bloques en esta evaluación descriptiva.
No se comparan costos de inferencia: la latencia equivalente de Top-k22, GFS y
full22 no fue medida.

Fuentes de esos baselines: Top-k está en
`results/extensions/outex13_official1360/ngram22_beitv2/topk_individual_control/nested_fold_results.csv`
(SHA-256 `fa89a052d31931ebf2030c2fdaa52d4acb0b16dfb35a8d3a4633901aefcc3918`),
y GFS/full concat en
`results/extensions/outex13_official1360/ngram22_beitv2/nested_fold_results.csv`
(SHA-256 `73114486931e506a343ee520199f4358bf16bafd72c49531b09a4e95fc4eb545`).
La fila Top-k registra SVM, seed 42, fold 0, k=8, macro-F1 0,9425744 y
accuracy 0,9441176. El launcher
`scripts/run_primary22_beitv2.sh` invoca tanto el runner principal como
`run_topk_individual_control.py` con los mismos argumentos oficiales; el log
`results/extensions/outex13_official1360/ngram22_beitv2/logs/Outex13Official1360__svm__42__official1__full.json`
confirma `official_split=1`, `fold=0`, semilla 42, biblioteca
`ngram22_beitv2` y embedding root `embeddings_extensions`. El código Top-k
obtiene sus particiones mediante `official_split_indices` y selecciona sobre el
entrenamiento. No se usó el Top-k 0,9503 del directorio histórico distinto
`results/extensions/outex13_official1360/topk_individual_control/`. Estos
baselines no son medidas de latencia ni evaluaciones de la misma política de
extracción.

Para CUReT, los baselines SVM/seed42 usan los mismos dos sentidos
`curet_half_indices`, el mismo subset/auditoría y macro-F1, por lo que la
comparación emparejada por sentido es descriptiva y protocolariamente
equiparable. `a_to_b`: adaptativa 0,9915; Top-k22 0,9982, GFS 0,9982 y full22
0,9979. `b_to_a`: adaptativa 0,9961; Top-k22 0,9996, GFS 0,9993 y full22
1,0000. La adaptativa quedó por debajo de los tres baselines en ambos
sentidos; no se midieron costos con una misma ruta.

Fuentes CUReT: `results/confirmatory/ngram22_beitv2_parts/CUReT_svm_a_to_b/nested_fold_results.csv`
(SHA-256 `068e233c442eab28c04787bd685494e5d3253a09fed6d6471a4549d6aa1e1dfb`)
y su `topk_individual_control/nested_fold_results.csv` (SHA-256
`66e3f61c67e23b09fe94d3699a6517b5258ea3b62036cc17b027b50486631f40`), más
los artefactos correspondientes de `CUReT_svm_b_to_a` (SHA-256
`d5d554714234b68f94c2845a91bf42a14014eb849ca54c48cb74950ae32a3920` y
`5764ec9bf97a0d6d1844faf2a30a4a0b7f55e227a31fbfc200a4918591796e83`). Los
folds corresponden a `a_to_b`→0 y `b_to_a`→1. Top-k tiene k=4/5
respectivamente. Estos valores no comparan tiempos ni dominancia de costo.

KTH no se compara con los resultados main: estos siguen la dirección Caputo
(una muestra train/tres test), opuesta a este LOPO adaptado.

Para DTD, las filas principales provienen de
`results/confirmatory/ngram22_beitv2/nested_fold_results.csv` (SHA-256
`473dd378038fdecc6f98faf5e06a7d3039f56a9a56d69b13ed048f385e4408a8`) y
Top-k de `results/confirmatory/ngram22_beitv2/topk_individual_control/nested_fold_results.csv`
(SHA-256 `9d5188758cadc882aa02495cc135f124dee2f29a67d5000d95d82be6882dfc6a`).
Ambos contienen diez filas por método, dataset DTD, SVM y seed 42; el runner
principal usa `--official-split 1..10` y Top-k recibe los mismos argumentos de
split y el mismo GFS archivado para elegir k.

## Latencia e identidad de los embeddings

En GPU NVIDIA RTX 4060, con PyTorch 2.12.1+cu126 y timm 1.0.28, se midieron
50 imágenes del test oficial, batch 1 y cinco calentamientos. La carga del
modelo quedó excluida. Cada medición individual incluye lectura/decodificación,
preprocesamiento, inferencia sincronizada y transferencia al CPU.

| Extractor | Media | Mediana | p95 | Coseno mínimo vs embedding | Coseno mediano |
|---|---:|---:|---:|---:|---:|
| ResNet-50 | 28,40 ms | 25,72 ms | 41,56 ms | 0,999957 | 0,999995 |
| BEiTv2-final | 31,37 ms | 28,94 ms | 44,17 ms | 0,999931 | 0,999999 |

Los cosenos verifican que los extractores timm usados para el microbenchmark
reproducen los embeddings almacenados con alta concordancia. Esto mide cada
bloque por separado, no el tiempo completo de la política adaptativa.

Se repitió el microbenchmark para 50 imágenes del test oficial DTD split 1;
los 1.880 source paths de ese test pasaron el preflight de existencia.

| Dataset / extractor | Media | Mediana | p95 | Coseno mínimo | Coseno mediano |
|---|---:|---:|---:|---:|---:|
| DTD ResNet-50 | 38,90 ms | 39,51 ms | 50,10 ms | 0,999993 | 0,999999 |
| DTD BEiTv2-final | 38,11 ms | 37,70 ms | 47,59 ms | 0,999988 | 1,000000 |

Se midió también la ruta completa imagen-a-predicción para 50 imágenes de test
en Outex oficial y DTD split 1. Ambos extractores quedaron residentes en la
misma RTX 4060; se alternó el orden de políticas, se usaron cinco calentamientos,
batch 1 y se excluyeron carga de modelos y ajuste del SVM.

| Dataset, ruta | Solicitud BEiTv2 en la muestra | Media | Mediana | p95 | Reducción de media vs full |
|---|---:|---:|---:|---:|---:|
| Outex, adaptativa | 46% | 25,40 ms | 24,20 ms | 47,83 ms | 24,47% |
| Outex, dos bloques siempre | 100% | 33,63 ms | 30,79 ms | 50,50 ms | — |
| DTD split 1, adaptativa | 42% | 46,13 ms | 38,72 ms | 73,21 ms | 27,30% |
| DTD split 1, dos bloques siempre | 100% | 63,46 ms | 62,97 ms | 72,51 ms | — |

Las solicitudes y predicciones online coincidieron al 100% con la simulación
precalculada en ambos subconjuntos Outex/DTD y también en los subconjuntos
CUReT/KTH siguientes. Las latencias son medidas de una GPU, batch 1 y
subconjuntos usados solo para timing; no convierten sus métricas de
clasificación en estimaciones externas. Se omiten las métricas de clasificación
de todos los subsets de 50 imágenes. Las latencias online y las medias del
microbenchmark por extractor no tienen por qué sumarse: cambian orden, caché,
decodificación, decisión de ruta y clasificación.

Se midió además la ruta completa imagen-a-predicción para 50 filas con los
modelos residentes en RTX 4060, PyTorch 2.12.1+cu126 y timm 1.0.28, batch 1 y
cinco calentamientos. Cada imagen de timing pasó verificación SHA-256; la carga
de los modelos y el ajuste de SVM quedaron excluidos.

| Dataset / protocolo y ruta | Solicitud BEiTv2 en la muestra | Media | Mediana | p95 | Reducción media vs full |
|---|---:|---:|---:|---:|---:|
| CUReT a_to_b, adaptativa | 44% | 74,39 ms | 71,38 ms | 146,96 ms | 32,24% |
| CUReT a_to_b, dos bloques siempre | 100% | 109,79 ms | 94,37 ms | 218,26 ms | — |
| KTH LOPO adaptado split 1, adaptativa | 32% | 105,58 ms | 86,42 ms | 198,29 ms | 28,42% |
| KTH LOPO adaptado split 1, dos bloques siempre | 100% | 147,50 ms | 136,12 ms | 263,04 ms | — |

En ambos subsets de 50 imágenes, predicción adaptativa, predicción full y
decisión de solicitud tuvieron acuerdo 100% con la simulación. La concordancia
coseno entre extracción online desde fuente y embedding guardado fue:

| Dataset | ResNet-50 min / mediana | BEiTv2-final min / mediana |
|---|---:|---:|
| CUReT a_to_b | 0,999972 / 0,999998 | 0,999975 / 0,9999999 |
| KTH LOPO adaptado split 1 | 0,999980 / 0,999998 | 0,9999996 / 1,000000 |

## Ejecuciones y estado

Completada, simulación externa basada en embeddings y 200 controles aleatorios:

```bash
.venv-confirmatory/bin/python scripts/run_adaptive_official_protocol.py \
  --dataset Outex13Official1360 --split-number 1 --seed 42 \
  --audit-root results/extensions/outex13_official1360 \
  --manifest-root results/extensions/outex13_official1360 \
  --embedding-root embeddings_extensions \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct
```

Completada, identidad y latencia individual de extractores:

```bash
HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python scripts/benchmark_adaptive_blocks.py \
  --dataset Outex13Official1360 --embedding-root embeddings_extensions \
  --manifest-root results/extensions/outex13_official1360 --seed 42 \
  --official-split 1 --n 50 --warmup 5 \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct

HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python scripts/benchmark_adaptive_blocks.py \
  --dataset DTD --embedding-root embeddings \
  --manifest-root results/confirmatory --seed 42 \
  --official-split 1 --n 50 --warmup 5 \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct
```

CUReT: ResNet-50 references copied into an isolated extension, then the
BEiTv2-final block was re-extracted from the audited images (all 5.612 source
hashes matched the manifest). The extracted block matched the pre-existing
BEiT cache on 100 evenly spaced rows with minimum cosine 0,99999988, median
1,000000 and maximum absolute difference 0.

```bash
mkdir -p embeddings_extensions/adaptive_descriptor_pilot/CUReT
cp embeddings_confirmatory/CUReT/resnet50.npy \
  embeddings_confirmatory/CUReT/resnet50_labels.npy \
  embeddings_confirmatory/CUReT/resnet50_classes.json \
  embeddings_extensions/adaptive_descriptor_pilot/CUReT/
HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python src/extract_beitv2_extension.py \
  --dataset CUReT --embedding-root embeddings_extensions/adaptive_descriptor_pilot \
  --data-root data/confirmatory_sources/CUReT/curetgrey_extracted/curetgrey \
  --reference-extractor resnet50 --batch-size 16 --num-workers 2 --final-only

.venv-confirmatory/bin/python scripts/run_adaptive_sample_generalization.py \
  --dataset CUReT --curet-direction a_to_b --seed 42 \
  --audit-root results/confirmatory --manifest-root results/confirmatory \
  --embedding-root embeddings_extensions/adaptive_descriptor_pilot \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct \
  --random-repeats 200

.venv-confirmatory/bin/python scripts/run_adaptive_sample_generalization.py \
  --dataset CUReT --curet-direction b_to_a --seed 42 \
  --audit-root results/confirmatory --manifest-root results/confirmatory \
  --embedding-root embeddings_extensions/adaptive_descriptor_pilot \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct \
  --random-repeats 200
```

Completadas las mediciones online, con validación de hash de inputs y audit gate:

```bash
HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python scripts/run_online_adaptive_validation.py \
  --dataset Outex13Official1360 --embedding-root embeddings_extensions \
  --manifest-root results/extensions/outex13_official1360 --seed 42 \
  --official-split 1 --n 50 --warmup 5 --budget 0.5 \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct

HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python scripts/run_online_adaptive_validation.py \
  --dataset DTD --embedding-root embeddings --manifest-root results/confirmatory \
  --seed 42 --official-split 1 --n 50 --warmup 5 --budget 0.5 \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct
```

Mediciones online CUReT/KTH y LOPO KTH splits 1–4. Las corridas KTH se
ejecutaron individualmente; el loop siguiente es una receta de reproducción.
KTH invierte cada split manifestado y purga de train cualquier SHA compartido
con el held-out, conservando el test entero.

```bash
HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python scripts/run_adaptive_online_sample_validation.py \
  --dataset CUReT --curet-direction a_to_b --seed 42 \
  --audit-root results/confirmatory --manifest-root results/confirmatory \
  --embedding-root embeddings_extensions/adaptive_descriptor_pilot \
  --prior-json results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct/CUReT_svm_s42_a_to_b_resnet50_then_beitv2_base_final.json \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct \
  --n 50 --warmup 5

for split in {1..4}; do
  .venv-confirmatory/bin/python scripts/run_adaptive_sample_generalization.py \
    --dataset KTHTIPS2b --split-number "$split" --seed 42 \
    --audit-root results/extensions/kth_tips2b \
    --manifest-root results/extensions/kth_tips2b \
    --embedding-root embeddings_extensions \
    --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct/kth_lopo_purged \
    --random-repeats 200
done

HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python scripts/run_adaptive_online_sample_validation.py \
  --dataset KTHTIPS2b --split-number 1 --seed 42 \
  --audit-root results/extensions/kth_tips2b \
  --manifest-root results/extensions/kth_tips2b \
  --embedding-root embeddings_extensions \
  --prior-json results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct/kth_lopo_purged/KTHTIPS2b_svm_s42_LOPO_split1_resnet50_then_beitv2_base_final.json \
  --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct/kth_lopo_purged \
  --n 50 --warmup 5
```

Receta de reproducción para las corridas DTD official1–10 completadas (las
corridas originales se lanzaron por split):

```bash
for split in {1..10}; do
  .venv-confirmatory/bin/python scripts/run_adaptive_official_protocol.py \
    --dataset DTD --split-number "$split" --seed 42 \
    --audit-root results/confirmatory --manifest-root results/confirmatory \
    --embedding-root embeddings \
    --output results/exploratory/adaptive_descriptor_pilot/official_protocol_50pct
done
```

Historial de fallos corregidos: el primer intento DTD official1 no guardó
artefactos por un path relativo en provenance (`ValueError: relative_to`);
una primera medición online Outex encontró el esquema antiguo `budgets`
(`KeyError`). Un preflight `py_compile` también detectó una indentación en el
adaptador online; se corrigió y la compilación final pasó. Tras autorización
explícita del usuario se repitieron los dos experimentos fallidos con lector y
provenance corregidos, y ambos completaron correctamente. No hubo otros fallos
en las corridas autorizadas.

## Validez de artefactos y datasets fuera del alcance

La primera salida KTH split1 en el directorio padre, creada antes de la
auditoría de SHA posterior a invertir roles, se conserva pero es
`INVALID/SUPERSEDED` y no se agrega ni cita. Las únicas métricas KTH válidas son
las salidas de `kth_lopo_purged/`, con purge y verificaciones explícitos.
CUReT y KTH completaron la ruta exploratoria autorizada. FMD y Soil continúan
como desarrollo exploratorio y no se usan para estas comparaciones.

## Artefactos y provenance

- Outex official1: JSON de métricas, CSV por muestra, JSON de microbenchmark y JSON de timing online.
- DTD official1–10: 10 JSON de métricas y 10 CSV por muestra, uno por split; además JSON de microbenchmark y timing online para official1.
- CUReT: dos JSON y dos CSV por muestra (`a_to_b`, `b_to_a`), más timing online a_to_b; BEiTv2-final regenerado en `embeddings_extensions/adaptive_descriptor_pilot/CUReT` sin modificar el almacén confirmatorio.
- KTH LOPO adaptado: cuatro JSON y cuatro CSV válidos en `kth_lopo_purged/`, más timing online para split1. La primera JSON split1 sin auditoría de purge queda retenida solo como inválida/supersedida en el directorio padre.
- `data_audit.csv` SHA-256: `39eece9737486943218039b3a362bb13ffb17457470ff66766146c973cfa41ef`
- Manifiesto SHA-256: `6499321a05630111dda4e3a7421995555553deea4807f23a5b4673a011856447`
- ResNet-50 embeddings SHA-256: `928fea231403ea8b92f998fdd4488c73469f5fa2a503a7b1fe950bd46673ea05`
- BEiTv2-final embeddings SHA-256: `ea2a2f54c676bf521e603fb27131ef143b2c128bd0b94646a9a273409d03f014`
- Ambos archivos de etiquetas tienen SHA-256 idéntico:
  `dd2e0aae92f26e20d79d33abe4ecf65e4046992983f5ded18fef7d7347f396fe`.

CUReT audit y manifest corresponden a 5.612 imágenes, 61 clases y las mitades
deterministas por condición; audit SHA-256
`6feae9c01a93bccea62521a495a6720aa6d0b19b5fb7d90441433402863ea331`, manifest
SHA-256 `42f1af10b02ab55b9ffce3019e318a52b758f6c8ec7d70d4428fa2c397524a34`.
El ResNet-50 aislado (misma matriz auditada) SHA-256
`f41315d0f04063862a583f681ae61ac0b61b5bff0d71a78fbb0f09e8e549b9fd`; el
BEiTv2-final regenerado SHA-256
`ef66989bd4669dd571acf848a4768c6cba950b6df04b20c795cf77745f74a307`; labels
de ambos SHA-256 idéntico `4bbb260035bc1344807e928ae5d4c1d50c36b702e0b00b99938567b19b5aeaaa`.
Metadata del extractor (timm BEiTv2 base patch16, pooling final 768D) SHA-256
`35b6f1eb3d999168cf46c0fba9ea03c7ad4f2c908dc0058094fefdb10dc189b7`.
Cada ejecución comprobó paths y hashes de las 5.612 imágenes, cero faltantes y
cero discrepancias.

SHA-256 de resultados CUReT: JSON a_to_b
`7bebbc063a88d514e650b63a689ac358290f9daa73adb64f5746b81ffa7e4011`, CSV por
muestra `9bd07348509fa5852df838c2ad42c82a2aad25d6bd32f82415f17ad44bb2f7f8`;
JSON b_to_a `3c493e989b41823d84966f38a211189113c31db1232f6b0c85c4d35d9942837f`,
CSV `600c20f6be6701172536bb39958593974e1797f7e4ca579907353eb885a56bf8`.
Timing online CUReT SHA-256 `3daf5729522a9cacfb446e38bd2ba2073595606ac4536cf1b1a7120f4db0a998`.

KTH manifest SHA-256 `df7d23f6681f2d5974d47f33ef5246845f51435d9db539d0522d6de8ab5cb2e7`,
audit SHA-256 `34ec936366f52076e4b48296c01894a64da6dfd7980656648553da3bc03729b0`;
ResNet-50 embeddings SHA-256
`3a0cb05bedecb9cc17db9c82b82c1701f20a3f239bc1beebda4bf508a46caacc`,
BEiTv2-final `47204c3d400fc327ef18adab6b39df1f473f385e948783c6204acf120734203a`,
labels comunes `11d848bcf4a9a1b09f40f32c9ec15364006b0cb71b808b8878058b409358bdc7`.
En cada corrida se verificaron los SHA de las 4.752 imágenes locales; cero
paths faltantes y cero discrepancias.

SHA-256 de JSON LOPO KTH splits 1–4: `54812f7f058ac516ed1175d7aaf28937467667d83369fda271733d1801128e4d`,
`561c0db52b4ac125d0fd3ace026266e8b0d752a4163b5e158808b081e1152808`,
`2c018fa94072892ca471af4be4eba36b3b201364b8fa98e0e0ff34cb250b6465`,
`b584c92db4636cb37a705097032c27a38f19cf446f441c0b035164504300897d`.
Timing online KTH split1 SHA-256
`90785718a8f8fa8d412ce3bb42396a7a02e067e46e4cfba69b7f14736134cc4e`.
La salida split1 previa sin purge se mantiene solo para trazabilidad:
`KTHTIPS2b_svm_s42_LOPO_split1_resnet50_then_beitv2_base_final.json` (SHA-256
`661a7a3dda961fcc5397c99e8655a5e5f9f70fb5edda175041709c3cfd62137b`);
etiquétese `INVALID/SUPERSEDED` y no se mezcle con la salida corregida del
subdirectorio.

CSV por muestra KTH LOPO 1–4 (mismo orden que los JSON): SHA-256
`474afaa881f91ae4909ff23370841eadc3f63b69c7b17f70d22a32554bd41cdf`,
`aa43f786111e87aba6b85b9dfe6730d491c338dbd2cb91d1bed51f2800d9c982`,
`21d495ed4a57235d8fc442a091d3f31d1c74a0e0e421d037082e8b8659316625`,
`c173964eeb94eb2cc92214d0889698f7d04185ea4c9b97d77a22a7ef14b56abf`.
SHA-256 de los runners nuevos: offline
`69e8a2d6a9e7fe087408540a21940cf22ef484d5454e0e93a52162f6b78602ba` y online
`511c919e5cb87ceab6f059fabf3f4186137e1ce95d72363869a91fdfee7984d8`.

Para DTD, cada JSON de split conserva los mismos hashes de auditoría,
manifiesto, embeddings y etiquetas: auditoría
`6feae9c01a93bccea62521a495a6720aa6d0b19b5fb7d90441433402863ea331`,
manifiesto `2cf599cd934d8569ded9e73cd8019bef53627878d98260d7c071921bdd635b3b`,
ResNet-50 `21562f4a42c5893fc29670ffdb2558cc838d17bc93674597ea8bd21d5035f625`,
BEiTv2-final `b1fe068b2a8e3642e71f86650f7bdf39585a538b564e0658d9c3b8d9c383ca49`,
y etiquetas comunes `a54314e1074f10ec8a5750620de42a0046a2c65c1b1337cabbbfb65af27233de`.

SHA-256 de los JSON de resultado DTD, splits 1–10:

- official1: `2f66cce12b039e77fed420e2e4658dd5ef02f5c1d6a318fa648b628f2cd78415`
- official2: `aff234137b29725f314123dcb413d58727987cf41861d38eeb72a17286c69f6f`
- official3: `b2f6734d93cb0c6af392e937a3313ca5f3f227a0f30a69bc9294393f8281544e`
- official4: `f9e3717b824bc9ca604048833321e9475a6d10093d2dec8fab1d7461e69a78e5`
- official5: `ae718558dbed1256253006bd199f0133a8f4ea7f4641e63d1ab62d8e0b7dd2e8`
- official6: `f407ac68e988e4ace64a4c79d9ef211a066df09ab5c7e4c7dbe886e00ab87f17`
- official7: `15296d29dfd8cf8f2456471ee58d323b6a677a5182febeb0596fff37e85d3ada`
- official8: `5cbcb5d4019716629e7557ee2f1bf8345e9b3cf5dc553827afa1714284df8d70`
- official9: `3b6833ebc5b59545c869689eb28f4a738c92d483ac41b02464c8418fb19001ce`
- official10: `89bfdf628ea20ca92fcc26f942ef807dfb431a00a15469f5293933c6d9deb0f7`

SHA-256 de latencia DTD official1: microbenchmark
`68511224d313ea34dbc462a33cbe875b05ef6587f91eab97d61a729f43e883ac`, online
`2d2189a27e7f6e14b899c948bbbdac5dfca0bd3bd1562a134403716528f0923b`.
SHA-256 de timing online Outex:
`8c1095a128197476e57beab46ca4cd87fa451808e4076460c46e8f6f8629f326`.
SHA-256 del microbenchmark Outex:
`6d4f53dbdde4de150d75dabfedd63d8be0468e52165255e4385fc0f9e13d5dba`.
SHA-256 del JSON de métricas adaptativas Outex:
`934f16d1f8f073a24753f3aa7e17588697c74e853e697ea3a84a2d5a981a19c`; su CSV
por muestra:
`14abe4f58e3c25caa00e9035a4f563defac35d002e5da7b4537f808d1e6b8752`.

El JSON conserva los hashes de manifest, auditoría, embeddings y etiquetas.
No se editaron tesis, artículo ni resultados confirmatorios; no se hicieron
commits ni push.
