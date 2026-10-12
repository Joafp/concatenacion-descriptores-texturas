# Material Passport: cascada adaptativa hacia Top-k

La extensión sensible al costo y la evaluación de los seis datasets están
documentadas en `docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md`. Este README conserva
el experimento original de KTH y sus controles online corregidos.

## Propósito y alcance

Experimento exploratorio de adquisición condicional de descriptores en
KTH-TIPS2-b. Cada imagen se clasifica primero con `resnet50`; una regla de
incertidumbre, ajustada solamente sobre el entrenamiento externo, decide si se
calcula la etapa Top-k específica de la partición. El objetivo es evaluar la
relación entre fracción escalada y macro-F1, no declarar una mejora confirmatoria
ni una reducción de latencia.

## Protocolo reproducible

- Dataset y clasificador: KTH-TIPS2-b, SVM, semilla 42.
- Particiones: las cuatro particiones oficiales invertidas, con el protocolo de
  muestra física del experimento principal.
- Etapa barata: `resnet50`.
- Etapa cara: el subconjunto `topk_individual` archivado para la misma
  partición. No se derivó de nuevo ningún subconjunto.
- Regla de escalamiento: cuantiles 0.25, 0.50 y 0.75 de márgenes out-of-fold
  sobre el entrenamiento externo, agrupados por `sample`.
- Control: escalamiento aleatorio con exactamente la misma cantidad de
  imágenes, 100 repeticiones por partición y presupuesto.

La verificación exacta de la etapa cara está en
`kth_tips2b/topk_cascade_rows.csv`: las cuatro diferencias entre el macro-F1
Top-k archivado y el reproducido son menores o iguales a `1e-10` en valor
absoluto.

## Resultados descriptivos

| Fracción objetivo | Fracción solicitada | Cascada | Top-k siempre | Aleatorio igual conteo | Cascada − Top-k | Cascada − aleatorio | Extracción estimada |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 25% | 21.3% | 0.9207 | 0.9400 | 0.8763 | -0.0193 | +0.0444 | 90.7 ms |
| 50% | 43.8% | 0.9384 | 0.9400 | 0.8951 | -0.0016 | +0.0434 | 145.3 ms |
| 75% | 67.3% | 0.9401 | 0.9400 | 0.9134 | +0.0000 | +0.0267 | 208.5 ms |

La media de la etapa barata sola es 0.8577. Las medias cubren cuatro
particiones solapadas y, por tanto, son descriptivas: no se aplicó una prueba
de hipótesis ni deben tratarse como observaciones independientes.

La cascada puede superar a la etapa Top-k siempre porque conserva la predicción
barata cuando no escala; Top-k no es un techo matemático de esa combinación.

## Medición de extracción

Se realizó una medición auxiliar en GPU sobre 30 imágenes de la partición
oficial 1, con cinco calentamientos, tamaño de lote uno y carga de modelos
excluida. Cada vector extraído se contrastó contra el embedding archivado; las
similitudes coseno mínimas fueron superiores a 0.99999 para los cuatro bloques.

| Bloque | Media (ms/imagen) | Mediana (ms/imagen) |
|---|---:|---:|
| `resnet50` | 37.08 | 39.36 |
| `beitv2_base_final` | 33.33 | 32.65 |
| `dinov2_large` | 476.04 | 409.64 |
| `vit_b16` | 60.12 | 42.03 |

El archivo completo es `kth_tips2b/timing/latency_KTHTIPS2b_s42_official1_n30.json`.
Como todas las imágenes pasan primero por la etapa barata, el costo predicho de
una política es `C(resnet50) + fracción_escalada × C(etapa_top-k)`, donde la
etapa Top-k puede contener uno o dos bloques según la partición. Esto ilustra
el valor potencial de evitar DINOv2-Large; no es una medición de latencia de
punta a punta.

## Validación online de la política

La primera versión del ejecutor calculaba `resnet50` incluso en la ruta
"Top-k siempre". Esa comparación no era justa y las reducciones anteriores en
`online/`, `online_round2/`, `online_round3/` y `online_official2..4/`
quedan supersedidas. El ejecutor corregido salta la etapa barata en Top-k
directo. Se repitió una ronda de 30 imágenes por cada partición oficial
invertida, presupuesto nominal 50%, con cinco calentamientos y modelos
residentes. En las cuatro rondas, decisiones y predicciones coincidieron al
100% con el experimento en caché; la similitud coseno mínima superó 0.99998.

| Partición | Top-k | Escalamiento | Cascada media | Top-k directo medio | Ahorro de cascada |
|---|---|---:|---:|---:|---:|
| 1 | DINOv2-Large + BEiT | 33.3% | 196.03 ms | 447.49 ms | 56.2% |
| 2 | BEiT | 36.7% | 49.45 ms | 42.61 ms | -16.0% |
| 3 | BEiT + DINOv2-Large | 46.7% | 238.42 ms | 441.05 ms | 45.9% |
| 4 | ViT-B/16 | 70.0% | 57.17 ms | 40.07 ms | -42.7% |

Las trazas corregidas están en `kth_tips2b/online_fair_topk/`. No se promedian
las cuatro filas porque las rutas Top-k tienen distinto costo intrínseco.
En las particiones 2 y 4, el costo fijo de la etapa barata hace que la cascada
sea más lenta que Top-k directo. La política de costo fijo para `q=0,50`
permite omitirla en ambas antes de ver las etiquetas externas. Esto **no**
garantiza que una política con otro presupuesto sea más rápida: el selector
entrenado eligió `q=0,25` en la partición 4 y su nueva medición online fue
59,61 ms frente a 45,29 ms de Top-k directo. El análisis completo y sus
limitaciones están en `docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md`.

## Limitaciones y siguiente validación

Los resultados de clasificación son una simulación de predicciones con
embeddings en caché. La validación online cubre extracción, decisión y
clasificación en cuatro particiones, pero excluye carga de modelos y ajuste del
clasificador y usa solo 30 imágenes deterministas por partición. No debe
transformarse en una afirmación general de latencia de punta a punta.

Los JSON por partición en `kth_tips2b/exact_archive/` contienen huellas SHA-256
de manifiestos, auditoría, control Top-k, ejecutor y embeddings usados.

## Regeneración

Ejecutar las cuatro órdenes `scripts/run_adaptive_topk_cascade.py` con
`--official-split 1..4 --invert-official-split --inner-group-column sample`,
sin `--derive-topk`, y luego:

```bash
.venv-confirmatory/bin/python scripts/report_topk_cascade.py
```
