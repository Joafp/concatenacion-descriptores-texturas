# Las dos ideas de muestreo con cuatro bloques

Estado: **exploratorio y descriptivo**. No modifica resultados confirmatorios ni
tablas del manuscrito.

La tómbola por ranking y el muestreo que penaliza la redundancia se evaluaron
primero con el tamaño de subconjunto que cada condición hereda del GFS. El
barrido de k mostró después que un k fijo en 4 es la elección simple más sólida
(`../k_sweep/README.md`), así que ambas ideas se repiten aquí con k=4, en las
mismas 27 condiciones externas, frente al Top-4 determinista y a la Completa de
22 bloques del manuscrito.

SVM lineal, semilla 42, 15 sorteos por celda. KTH-TIPS2-b con protocolo RADAM,
agrupamiento interno por muestra física y sin `beitv2_base_multilayer`. Las
medias se calculan primero por dataset, para que las diez particiones de DTD no
pesen más que la única de Outex; los recuentos de victorias son por condición.

## Resultado

| Método | Macro-F1 | vs Top-4 | vs Completa-22 | Gana a Top-4 | Gana a Completa-22 |
|---|---:|---:|---:|---:|---:|
| **Completa-22** | **0,9409** | +0,0042 | — | 9/27 | — |
| Diversidad λ=0,25, β=8, ensamble | 0,9393 | +0,0026 | −0,0017 | 16/27 | 17/27 |
| Tómbola β=8, ensamble suave | 0,9390 | +0,0023 | −0,0020 | 15/27 | 21/27 |
| Diversidad λ=1, β=8, ensamble | 0,9389 | +0,0022 | −0,0020 | 15/27 | 18/27 |
| Tómbola β=2, ensamble suave | 0,9381 | +0,0014 | −0,0028 | 17/27 | 17/27 |
| **Top-4 determinista** | **0,9367** | — | −0,0042 | — | 18/27 |
| Diversidad λ=0,25, determinista | 0,9348 | −0,0019 | −0,0062 | 3/27 | 15/27 |
| Diversidad λ=1, determinista | 0,9340 | −0,0027 | −0,0069 | 10/27 | 15/27 |
| Tómbola β=8, sorteo único | 0,9349 | −0,0018 | −0,0060 | 6/27 | 17/27 |

Comprobación: la diversidad con λ=0 en su versión determinista reproduce
exactamente el Top-4 (0,9367), como debe.

**Lectura.**

- **Como ensamble, las dos ideas mejoran a Top-4 y son lo más cercano a la
  concatenación completa** que se probó en este repositorio: quedan a 0,002 de
  la Completa-22 y le ganan en 17 a 21 de las 27 condiciones, sobre todo por DTD
  y FMD. En promedio por dataset la Completa-22 sigue arriba.
- **Como regla determinista, ninguna mejora a Top-4.** Elegir un único
  subconjunto de 4 por diversidad, o un único sorteo, rinde por debajo.
- Las mejores configuraciones de ensamble están empatadas entre sí (0,9389 a
  0,9393). La tabla resume 24 configuraciones y la primera fila se eligió tras
  ver los resultados, así que su ventaja sobre las siguientes no es
  interpretable; lo que sí es estable es que los ensambles de β alto quedan
  todos entre +0,0015 y +0,0026 sobre Top-4.

Por dataset, la mejor configuración de cada familia:

| Dataset | Completa-22 | Top-4 | Tómbola β=8 ens. | Diversidad λ=0,25 β=8 ens. |
|---|---:|---:|---:|---:|
| CUReT | 0,9989 | 0,9986 | 0,9989 | 0,9988 |
| DTD | 0,8639 | 0,8689 | 0,8723 | **0,8734** |
| FMD | 0,9651 | **0,9819** | 0,9789 | 0,9789 |
| KTH-TIPS2-b | **0,9601** | 0,9544 | 0,9540 | 0,9541 |
| Outex13 | **0,9656** | 0,9288 | 0,9399 | 0,9458 |
| Soil | **0,8919** | 0,8876 | 0,8897 | 0,8846 |

## Outex13: la diversidad rompe el trío de DINOv2

Outex13 es el dataset donde k=4 más pierde contra la Completa-22, y su Top-4
contiene tres variantes de DINOv2. La diversidad las reemplaza a medida que
crece λ:

| λ | Subconjunto de 4 | CKA medio | Macro-F1 |
|---|---|---:|---:|
| 0 (= Top-4) | beitv2_base_final, dinov2, dinov2_large, dinov2_small | 0,922 | 0,9288 |
| 0,25 | beitv2_base_final, convnext_v2_t, dinov2_large, dinov2_small | 0,901 | 0,9295 |
| 1,0 | beitv2_base_final, dinov2_large, resnet50, vit_b16 | 0,818 | 0,9366 |

Con λ=1 el subconjunto es mucho menos redundante y sube +0,0078, y el ensamble
con diversidad llega a 0,9458 (+0,0170 sobre Top-4). El diagnóstico se confirma
donde más importaba, pero la distancia a la Completa-22 (0,9656) sigue siendo
grande, y la misma λ=1 determinista empeora el promedio de los seis datasets.

## Costo

Los ensambles entrenan 15 clasificadores de 4 bloques cada uno. Lo que fija el
costo de extracción es la unión de bloques que tocan:

| Método | Bloques distintos usados (de 21) |
|---|---:|
| Tómbola β=8 | 8,8 (42 %) |
| Diversidad λ=0,25, β=8 | 10,1 (48 %) |
| Diversidad λ=1, β=8 | 12,0 (57 %) |
| Tómbola β=2 | 14,7 (70 %) |

Las configuraciones de β=8 usan menos de la mitad de la biblioteca. No se midió
latencia; la reducción de bloques no implica una reducción proporcional del
tiempo de extremo a extremo.

## Limitaciones

- Un clasificador, una semilla, 27 condiciones dependientes entre sí; sin
  contraste inferencial.
- La Completa-22 incluye `rgb_ngram_svd`, que ninguno de estos métodos puede
  elegir porque no está en el paquete de embeddings. La prueba que falta es
  justamente darles acceso a ese bloque de color, que es el más distinto del
  resto y el que separa a la Completa-22 de los 21 bloques.
- La configuración destacada en la tabla se eligió entre 24 tras observar el
  test.

## Comandos

```bash
python src/run_weighted_lottery_selection.py --dataset DTD --official-split 1 \
  --classifier svm --seed 42 --k 4 --draws 15 --betas 0 2 8 --skip-draw-inner \
  --audit-root results/confirmatory --manifest-root results/confirmatory \
  --output results/exploratory/k4/lottery/dtd

python src/run_diversity_lottery.py --dataset DTD --official-split 1 \
  --classifier svm --seed 42 --k 4 --draws 15 --lambdas 0 0.25 0.5 1.0 --betas 2 8 \
  --audit-root results/confirmatory --manifest-root results/confirmatory \
  --output results/exploratory/k4/diversity/dtd

python src/analyze_k4_professor.py
```
