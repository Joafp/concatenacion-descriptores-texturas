# Material Passport: cascada adaptativa hacia Top-k

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

La ruta completa imagen→predicción se ejecutó también para la partición oficial
1 invertida, presupuesto nominal 50%, con 30 imágenes, cinco calentamientos y
modelos residentes, en tres rondas independientes. Se alternaron por imagen la
cascada y la ruta Top-k siempre. Antes de aceptar cada ronda, el ejecutor exigió
concordancia exacta con el artefacto en caché: decisiones de escalamiento,
predicciones adaptativas y predicciones Top-k coincidieron en el 100% de las
imágenes; la similitud coseno mínima fuente→embedding fue 0.999994.

| Métrica entre rondas | Cascada adaptativa | Top-k siempre |
|---|---:|---:|
| Mediana de las medias | 201.59 ms | 535.95 ms |
| Rango de las medias | 197.07–231.81 ms | 520.81–549.77 ms |

En esta muestra, la reducción media emparejada osciló entre 57.8% y 62.4%
(mediana: 62.2%) y la fracción observada de escalamiento fue 33.3%. Las trazas
por ronda están en `kth_tips2b/online/`, `kth_tips2b/online_round2/` y
`kth_tips2b/online_round3/`.

Se efectuó además una ronda de 30 imágenes en cada una de las otras tres
particiones, con el mismo control de concordancia exacta. No se promedian las
cuatro filas porque sus rutas Top-k tienen distinto costo intrínseco.

| Partición | Etapa Top-k | Escalamiento observado | Cascada media | Top-k siempre media | Reducción media |
|---|---|---:|---:|---:|---:|
| 1 (mediana de 3 rondas) | DINOv2-Large + BEiT | 33.3% | 201.59 ms | 535.95 ms | 62.2% |
| 2 | BEiT | 36.7% | 49.81 ms | 73.62 ms | 32.3% |
| 3 | BEiT + DINOv2-Large | 46.7% | 312.58 ms | 566.37 ms | 44.8% |
| 4 | ViT-B/16 | 70.0% | 70.98 ms | 81.22 ms | 12.6% |

Todas las filas tuvieron 100% de concordancia en decisión, predicción adaptativa
y predicción Top-k. Las trazas están en `kth_tips2b/online_official2/`,
`online_official3/` y `online_official4/`.

## Limitaciones y siguiente validación

Los resultados de clasificación son una simulación de predicciones con
embeddings en caché. La validación online cubre extracción, decisión y
clasificación, pero excluye carga de modelos y ajuste del clasificador; además,
abarca una partición y una muestra determinista. No debe transformarse todavía
en una afirmación general de latencia de punta a punta. Falta repetirla en las
otras particiones y con un muestreo mayor.

Los JSON por partición en `kth_tips2b/exact_archive/` contienen huellas SHA-256
de manifiestos, auditoría, control Top-k, ejecutor y embeddings usados.

## Regeneración

Ejecutar las cuatro órdenes `scripts/run_adaptive_topk_cascade.py` con
`--official-split 1..4 --invert-official-split --inner-group-column sample`,
sin `--derive-topk`, y luego:

```bash
.venv-confirmatory/bin/python scripts/report_topk_cascade.py
```
