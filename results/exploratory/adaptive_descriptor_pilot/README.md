# Piloto exploratorio: adquisición adaptativa de dos bloques

Este análisis **no** pertenece a los resultados confirmatorios de la tesis.
La evaluación de macro-F1 simula adquisición condicional usando embeddings
ya precalculados. Un ensayo separado mide latencia real de extracción para
50 imágenes de FMD, pero no mide energía, memoria total ni rendimiento de
producción.

## Protocolo de la evaluación de macro-F1

- FMD y SoilOriginal por separado, SVM lineal, semilla 42, particiones
  externas 0--4 del protocolo `StratifiedGroupKFold` existente. La réplica
  Soil conservó la misma regla, bloques y presupuestos del piloto FMD.
- Bloque inicial: `resnet50` (2048 dimensiones). Bloque adicional:
  `beitv2_base_final` (768 dimensiones).
- Se ajusta un clasificador con el bloque inicial y otro con ambos bloques.
- La regla adaptativa solicita el bloque adicional para imágenes con menor
  margen entre las dos clases superiores del clasificador inicial.
- Los umbrales de margen se fijan con predicciones out-of-fold **solo del
  entrenamiento externo**, en los cuantiles 25%, 50% y 75%. Ni las etiquetas
  ni las predicciones de prueba se usan para elegir el umbral.
- Control: 200 asignaciones aleatorias por fold, cada una con exactamente el
  mismo número de solicitudes adicionales que realizó la regla adaptativa.
- Métrica primaria descriptiva: macro-F1 externo. Los cinco folds comparten
  datos de entrenamiento, así que no se tratan como réplicas independientes
  para un contraste inferencial.

## FMD: resultado descriptivo (media de cinco folds)

| Política | Macro-F1 | Fracción que solicita BEiTv2 |
|---|---:|---:|
| Solo ResNet-50 | 0,8517 | 0% |
| Adaptativa, presupuesto objetivo 25% | 0,9179 | 22,7% |
| Aleatoria, mismo conteo que la anterior | 0,8720 | 22,7% |
| Adaptativa, presupuesto objetivo 50% | 0,9378 | 46,2% |
| Aleatoria, mismo conteo que la anterior | 0,8930 | 46,2% |
| Adaptativa, presupuesto objetivo 75% | 0,9399 | 70,3% |
| Aleatoria, mismo conteo que la anterior | 0,9139 | 70,3% |
| ResNet-50 + BEiTv2 para todas | 0,9399 | 100% |

En el presupuesto objetivo del 50%, la regla igualó a la fusión de dos
bloques en tres folds y quedó ligeramente por debajo en dos. No se debe
interpretar como equivalencia estadística ni compararla directamente con
la concatenación completa de 22 descriptores.

## SoilOriginal: réplica descriptiva (media de cinco folds)

| Política | Macro-F1 | Fracción que solicita BEiTv2 |
|---|---:|---:|
| Solo ResNet-50 | 0,8070 | 0% |
| Adaptativa, presupuesto objetivo 25% | 0,8491 | 23,4% |
| Aleatoria, mismo conteo que la anterior | 0,8189 | 23,4% |
| Adaptativa, presupuesto objetivo 50% | 0,8558 | 45,4% |
| Aleatoria, mismo conteo que la anterior | 0,8322 | 45,4% |
| Adaptativa, presupuesto objetivo 75% | 0,8580 | 70,4% |
| Aleatoria, mismo conteo que la anterior | 0,8430 | 70,4% |
| ResNet-50 + BEiTv2 para todas | 0,8580 | 100% |

Estas medias son descriptivas: no justifican una prueba inferencial sobre
cinco folds solapados ni sustituyen los resultados principales de 22
descriptores. El desempeño tampoco mejora en todos los folds y presupuestos.

## Comprobación de costo real en FMD y SoilOriginal

Con la política de presupuesto objetivo 50% del fold externo 0 se procesaron
50 imágenes de prueba de cada dataset por la ruta adaptativa y por la ruta completa. Ambos
extractores estaban cargados en GPU; cada medición incluyó lectura de imagen,
preprocesamiento, inferencia de batch 1, transferencia al CPU y clasificación,
pero excluyó la carga de modelos y el ajuste de SVM. Se alternó el orden de
las políticas y se hicieron cinco calentamientos por política.

| Dataset y ruta | BEiTv2 solicitado | Latencia media | Mediana | p95 |
|---|---:|---:|---:|---:|
| FMD, adaptativa | 42% | 58,3 ms | 55,2 ms | 92,8 ms |
| FMD, completa de dos bloques | 100% | 86,7 ms | 85,2 ms | 125,6 ms |
| SoilOriginal, adaptativa | 46% | 76,0 ms | 72,3 ms | 141,1 ms |
| SoilOriginal, completa de dos bloques | 100% | 104,4 ms | 95,7 ms | 153,1 ms |

La reducción media observada fue 32,8% en FMD y 27,2% en SoilOriginal. Las
decisiones de solicitud y las predicciones coincidieron 50/50, en ambos
datasets, con la simulación basada en embeddings precalculados. El macro-F1
del subconjunto temporizado (0,9117 en FMD y 0,7719 en SoilOriginal para
ambas rutas) **no** constituye una nueva estimación de precisión externa:
los subconjuntos son pequeños y fueron escogidos solo para medir tiempo. La
medición es de un dispositivo y un fold por dataset, con modelos residentes,
y no estima consumo de energía ni ahorro de memoria total. El microbenchmark
separado de cada extractor en FMD está en `latency_FMD_s42_f0_n50.json`.

## Reproducción y límites

```bash
for fold in 0 1 2 3 4; do
  .venv-confirmatory/bin/python scripts/run_adaptive_descriptor_pilot.py \
    --dataset FMD --seed 42 --outer-fold "$fold" \
    --base resnet50 --extra beitv2_base_final
done

for fold in 0 1 2 3 4; do
  .venv-confirmatory/bin/python scripts/run_adaptive_descriptor_pilot.py \
    --dataset SoilOriginal --seed 42 --outer-fold "$fold" \
    --embedding-root embeddings_extensions \
    --manifest-root results/extensions/soil_original \
    --base resnet50 --extra beitv2_base_final
done

HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python \
  scripts/run_online_adaptive_validation.py \
  --dataset FMD --seed 42 --outer-fold 0 --n 50 --budget 0.5

HF_HUB_OFFLINE=1 .venv-confirmatory/bin/python \
  scripts/run_online_adaptive_validation.py \
  --dataset SoilOriginal --embedding-root embeddings_extensions \
  --manifest-root results/extensions/soil_original \
  --seed 42 --outer-fold 0 --n 50 --budget 0.5
```

Cada fold produce un JSON y un CSV por imagen en este directorio. Ejecutado
contra el commit base `1374107` más el nuevo script exploratorio. El estudio
no optimiza una política de 22 bloques ni compara con todos los baselines
principales al mismo costo real. La elección
de BEiTv2, evaluado antes en el proyecto, y cualquier extensión de este
piloto deben reportarse como exploratorias hasta una evaluación prospectiva
con protocolo y presupuestos congelados.

Como comprobación de reproducibilidad, se repitió el fold 0 con los mismos
argumentos: el SHA-256 del JSON fue idéntico antes y después
(`DF207AD9EE4C5D5A5D9B146DCDCE1706747C0CF1872D26D60D7688B9FC3C25FC`).
