# Cascada adaptativa con Top-k como etapa de escalado

Estado: **exploratorio y descriptivo**. No se modificó ningún resultado
confirmatorio ni ninguna tabla del manuscrito.

## Qué cambia respecto del piloto anterior

`results/exploratory/adaptive_descriptor_pilot/` escala de `resnet50` a una ruta
fija de dos bloques (`resnet50 + beitv2_base_final`). El techo de acierto de esa
cascada es esa ruta, que queda por debajo de los métodos del manuscrito: en
Outex official1, 0,9101 contra 0,9656 de Completa-22. Por eso no se puede
afirmar ahorro de costo a acierto equivalente.

Acá la etapa cara es el subconjunto `topk_individual` **archivado para la misma
condición**, de modo que el techo pasa a ser el resultado Top-k ya publicado y
la pregunta se vuelve: cuánto del costo de la ruta Top-k se puede evitar sin
perder acierto.

## Protocolo

- KTH-TIPS2-b, SVM lineal, semilla 42, particiones oficiales 1-4 con
  `--invert-official-split` (protocolo RADAM: entrena con tres muestras físicas
  y evalúa sobre una), igual que los runs archivados de
  `scripts/run_primary22_beitv2.sh`.
- Etapa barata: `resnet50` (2048 dimensiones).
- Etapa cara: el subconjunto Top-k de la condición.
- El umbral de escalado es un cuantil de los márgenes out-of-fold calculados
  **solo sobre las filas de entrenamiento externo**. Ni las etiquetas ni las
  predicciones de prueba intervienen en elegirlo.
- Control: 100 asignaciones aleatorias por partición, cada una escalando
  exactamente el mismo número de imágenes que la regla de margen.
- Se verifica ausencia de intersección de grupos entre entrenamiento y prueba, y
  cada JSON registra el protocolo, la columna de agrupamiento interno, los
  bloques usados y los SHA-256 de auditoría, manifiesto, embeddings y runner.

Dos variantes que difieren **solo** en el agrupamiento de los folds internos que
derivan el umbral:

- `group_image/` — columna `group` del manifiesto (SHA-256 por imagen).
- `group_sample/` — `--inner-group-column sample` (muestra física).

## Resultado 1: el agrupamiento interno controla el presupuesto

El umbral es un cuantil de márgenes de entrenamiento, así que los folds internos
tienen que plantear la misma tarea que el test externo. Partir imágenes al azar
dentro del entrenamiento hace la tarea interna más fácil, infla los márgenes y
deja el umbral demasiado permisivo.

| Objetivo | Pedido (imagen) | Pedido (muestra) | Error imagen | Error muestra |
|---|---:|---:|---:|---:|
| 25% | 56,1% | 21,4% | 31,1 pts | 3,6 pts |
| 50% | 72,4% | 43,8% | 22,4 pts | 6,2 pts |
| 75% | 84,6% | 67,3% | 9,6 pts | 7,7 pts |

Error absoluto medio: **21,0% con agrupamiento por imagen, 5,8% por muestra.**

Es el mismo defecto ya documentado para el criterio de selección
(`results/analysis/inner_grouping/`), actuando sobre un mecanismo distinto: la
calibración de un umbral, no la elección de un subconjunto.

## Resultado 2: acierto frente a costo

Agrupamiento por muestra, media de las cuatro particiones:

| Objetivo | Pedido | Adaptativa | Top-k siempre | Aleatoria | vs Top-k | vs aleatoria |
|---|---:|---:|---:|---:|---:|---:|
| 25% | 21,4% | 0,9179 | 0,9364 | 0,8763 | −0,0185 | +0,0416 |
| 50% | 43,8% | 0,9342 | 0,9364 | 0,8930 | −0,0021 | +0,0413 |
| 75% | 67,3% | 0,9364 | 0,9364 | 0,9111 | +0,0000 | +0,0253 |

Solo la etapa barata: 0,8580.

Escalando el 43,8% de las imágenes la regla recupera el 97% de la ganancia
disponible entre la etapa barata y Top-k, a 0,0021 de pagar Top-k siempre, y
supera en 0,0413 al control aleatorio con el mismo número de escalaciones.

## Verificación de la etapa cara

| Partición | Bloques | Top-k archivado | Reproducido | Delta | Derivado |
|---|---|---:|---:|---:|---|
| official1_inverted | swinv2_base+dinov2_large | 0,9941 | 0,9857 | −0,0084 | sí |
| official2_inverted | beitv2_base | 0,9040 | 0,9040 | +0,0000 | sí |
| official3_inverted | beitv2_base+dinov2_large | 0,9884 | 0,9884 | +0,0000 | sí |
| official4_inverted | vit_b16 | 0,8736 | 0,8674 | −0,0062 | no |

Delta absoluto medio 0,0037.

## Limitaciones

- Cuatro particiones de un solo dataset. Las particiones comparten datos de
  entrenamiento, así que **no** se aplica ningún contraste inferencial y las
  comparaciones son descriptivas.
- En tres de las cuatro particiones el subconjunto Top-k se **re-derivó** con la
  biblioteca disponible localmente, porque `beitv2_base_final` no está en este
  equipo. La composición difiere de la del manuscrito; está marcado como
  `expensive_subset_derived_locally` en cada JSON.
- La partición 4 usó el subconjunto archivado (`vit_b16`) y deja un residuo de
  −0,0062 sin explicación confirmada, compatible con diferencias de convergencia
  de `LinearSVC` entre entornos.
- **No se reporta costo en milisegundos.** Los 345,59 ms medidos para la ruta
  Top-k corresponden al subconjunto de ocho bloques de Outex y no transfieren a
  estos subconjuntos de uno y dos bloques. La fracción pedida es el único proxy
  de costo aquí; una afirmación en milisegundos requiere cronometrar la ruta de
  KTH-TIPS2-b.
- La etapa barata es únicamente `resnet50`; no se exploraron alternativas.

## Comandos

```bash
for SP in 1 2 3 4; do
  python scripts/run_adaptive_topk_cascade.py \
    --dataset KTHTIPS2b --classifier svm --seed 42 \
    --official-split $SP --invert-official-split \
    --inner-group-column sample \
    --cheap-blocks resnet50 \
    --audit-root results/extensions/kth_tips2b \
    --manifest-root results/extensions/kth_tips2b \
    --topk-control results/extensions/kth_tips2b/ngram22_beitv2/topk_individual_control \
    --embedding-root embeddings_extensions \
    --output results/exploratory/topk_cascade/kth_tips2b/group_sample
done

python scripts/report_topk_cascade.py
```

`--derive-topk` solo es necesario cuando la biblioteca local no contiene algún
bloque del subconjunto archivado; sin esa bandera el runner falla con el nombre
del bloque ausente en lugar de sustituirlo en silencio.
