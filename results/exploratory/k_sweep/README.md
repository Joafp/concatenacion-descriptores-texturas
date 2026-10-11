# Cuánto de la biblioteca hace falta: barrido completo de k

Estado: **exploratorio y descriptivo**. No se modificó ningún resultado
confirmatorio ni ninguna tabla del manuscrito.

El control Top-k hereda su tamaño del GFS de la misma condición, de modo que
cada dataset aporta un único punto al plano acierto–tamaño. Acá se recorre k
desde un bloque hasta la biblioteca entera, con el mismo ranking que usa Top-k
—calculado en los pliegues internos del entrenamiento externo— y evaluando cada
prefijo una sola vez en el test.

27 condiciones externas: Outex 1, CUReT 2, KTH-TIPS2-b 4, Soil 5, FMD 5, DTD 10.
SVM lineal, semilla 42. KTH usa protocolo RADAM, agrupamiento interno por
muestra física y excluye `beitv2_base_multilayer`.

## La curva se aplana en k=4

Media sobre los seis datasets, cada uno pesando igual:

| k | Macro-F1 | % dimensiones | % del máximo |
|---:|---:|---:|---:|
| 1 | 0,9176 | 4 | 97,9 |
| 2 | 0,9301 | 8 | 99,2 |
| 3 | 0,9330 | 12 | 99,5 |
| **4** | **0,9367** | **15** | **99,9** |
| 6 | 0,9364 | 24 | 99,9 |
| 10 | 0,9375 | 46 | 100,0 |
| 15 | 0,9356 | 84 | 99,8 |
| 21 | 0,9348 | 100 | 99,7 |

Con cuatro bloques y el 15 % de las dimensiones se alcanza el 99,9 % del máximo
de esta curva, y la biblioteca de 21 bloques queda en 0,9348, por debajo de
k=4. Esa biblioteca **no** es la Completa del manuscrito: le falta
`rgb_ngram_svd` (ver la sección siguiente).

## k=4 frente a la concatenación completa: depende de cuál

Sin elegir k mirando el test, el mismo k=4 para los seis datasets, en macro-F1,
contra los 21 bloques del barrido y contra la Completa de 22 bloques del
manuscrito en las mismas particiones (semilla 42):

| Dataset | k=4 | 21 bloques | Completa-22 | k=4 − 21 | k=4 − Completa-22 |
|---|---:|---:|---:|---:|---:|
| CUReT | 0,9986 | 0,9991 | 0,9989 | −0,0005 | −0,0004 |
| DTD | 0,8689 | 0,8657 | 0,8639 | +0,0032 | **+0,0050** |
| FMD | 0,9819 | 0,9622 | 0,9651 | +0,0198 | **+0,0168** |
| KTH-TIPS2-b | 0,9544 | 0,9496 | 0,9601 | +0,0048 | −0,0057 |
| Outex13 | 0,9288 | 0,9618 | 0,9656 | −0,0330 | −0,0368 |
| Soil | 0,8876 | 0,8708 | 0,8919 | +0,0168 | −0,0043 |
| **media** | **0,9367** | **0,9348** | **0,9409** | **+0,0018** | **−0,0042** |

En exactitud el patrón es el mismo: k=4 0,9444, 21 bloques 0,9439, Completa-22
0,9483.

**k=4 supera a los 21 bloques, pero no a la Completa-22 del manuscrito**, que gana
en cuatro de seis datasets y en el promedio por 0,0042. La afirmación correcta es
que cuatro bloques quedan a 0,004 de la concatenación completa con un quinto de
su tamaño, no que la superen.

La diferencia entre 21 y 22 bloques es un solo descriptor, `rgb_ngram_svd`, de
color. Pesa: agregarlo a la concatenación completa sube +0,0211 en Soil, +0,0105
en KTH-TIPS2-b y +0,0038 en Outex13. Nunca entra individualmente en el top 4 de
ningún dataset y, sin embargo, aporta información que los otros 21 no tienen.
La prueba pendiente es **top 4 + `rgb_ngram_svd`**, cinco bloques, para ver si
alcanza a la Completa-22 con un cuarto del tamaño.

**Outex13 es la excepción:** su óptimo en el barrido está en k=18, con el 99 % de
las dimensiones, y a k=4 pierde 0,0368 contra la Completa-22. Es el dataset
donde la representación grande más se justifica.

## Contra la literatura

Exactitud a k=4 frente a los valores publicados que ya compara el manuscrito:

| Dataset | k=4 | Neshov et al. | Scabini et al. | Supera a |
|---|---:|---:|---:|---|
| DTD | 0,8703 | 0,8200 | 0,7910 | ambos |
| FMD | 0,9820 | 0,9670 | 0,9090 | ambos |
| KTH-TIPS2-b | 0,9575 | 0,9680 | 0,9370 | Scabini |
| Outex13 | 0,9294 | — | 0,9160 | Scabini |

Cuatro bloques superan a Scabini et al. en los cuatro datasets comparables y a
Neshov et al. en dos de tres, con el 15 % de la representación completa. Los
protocolos, clasificadores y agregaciones difieren entre trabajos, de modo que
la comparación es descriptiva, como ya advierte el manuscrito.

## Limitaciones

- El k=21 del barrido son los 21 bloques almacenados y **no** incluye
  `rgb_ngram_svd`, que se reconstruye por fold desde las imágenes fuente. No es
  idéntico al «Completa» de 22 bloques del manuscrito y no debe presentarse como
  tal.
- Un solo clasificador (SVM) y una sola semilla. Las particiones de CUReT son
  complementarias y dependientes, Outex tiene un único split y las de DTD y FMD
  reutilizan imágenes: no se aplica ningún contraste inferencial.
- k=4 se leyó de esta curva, trazada sobre los tests externos. La sección
  siguiente comprueba si una regla calculada sólo con entrenamiento llega al
  mismo lugar: no llega, y la constante resulta mejor que toda regla probada.
- El ranking proviene del criterio interno, cuyo poder predictivo sobre el test
  externo este repositorio ya documentó como limitado
  (`results/exploratory/SELECCION_BUSQUEDA_README.md`).

## Comandos

```bash
python src/run_k_sweep.py --dataset DTD --classifier svm --seed 42 \
  --official-split 1 \
  --audit-root results/confirmatory --manifest-root results/confirmatory \
  --output results/exploratory/k_sweep/dtd

python src/run_k_sweep.py --dataset KTHTIPS2b --classifier svm --seed 42 \
  --official-split 1 --invert-official-split --inner-group-column sample \
  --exclude-extractors beitv2_base_multilayer \
  --audit-root results/extensions/kth_tips2b \
  --manifest-root results/extensions/kth_tips2b \
  --embedding-root embeddings_extensions \
  --output results/exploratory/k_sweep/kth_tips2b
```

El barrido evalúa los prefijos de forma secuencial a propósito: el prefijo con k
alto es la biblioteca entera, y hacerlo en paralelo mantiene varias
concatenaciones completas en memoria a la vez, lo que agota los 10 GB de WSL en
DTD y KTH.

## ¿Se puede elegir k sin mirar el test? No, y no hace falta

`src/run_k_sweep_inner.py` puntúa los mismos prefijos en los pliegues internos
del entrenamiento, de modo que una regla aplicada a esa curva elige k sin
consultar el test. `src/analyze_k_selection_rules.py` compara las reglas.

**Las dos curvas apenas se parecen.** Spearman entre el criterio interno y el
macro-F1 externo, por dataset:

| Dataset | ρ | n |
|---|---:|---:|
| FMD | +0,727 | 5 |
| DTD | +0,371 | 10 |
| CUReT | +0,204 | 2 |
| KTH-TIPS2-b | +0,076 | 4 |
| Soil | −0,172 | 5 |
| Outex13 | −0,336 | 1 |
| **media** | **+0,254** | 27 |

Positiva en 20 de 27 condiciones, pero débil, y **negativa en dos datasets**.

**Toda regla derivada de la curva interna pierde contra una constante.** Media
sobre las 27 condiciones:

| Regla | k medio | Macro-F1 | % dims | vs 21 bloques | vs oráculo |
|---|---:|---:|---:|---:|---:|
| argmax del criterio interno | 6,6 | 0,9130 | 29 | +0,0026 | −0,0117 |
| codo τ=0,001 | 2,6 | 0,9115 | 11 | +0,0011 | −0,0132 |
| codo τ=0,005 | 1,9 | 0,9085 | 8 | −0,0018 | −0,0161 |
| codo τ=0,01 | 1,6 | 0,9053 | 7 | −0,0051 | −0,0194 |
| **fijo k=4** | 4,0 | **0,9178** | 16 | **+0,0074** | **−0,0069** |
| fijo k=6 | 6,0 | 0,9168 | 23 | +0,0065 | −0,0078 |
| fijo k=3 | 3,0 | 0,9121 | 12 | +0,0018 | −0,0125 |

Referencias: oráculo externo 0,9246 y biblioteca completa 0,9104. El oráculo se
lee del test y es una cota superior, nunca una selección alcanzable.

Las reglas del codo eligen k entre 1 y 3, demasiado pronto. El argmax interno
elige 6,6 en promedio y queda por debajo de la constante. **El k fijo en 4 supera
a todas y es el más cercano al oráculo.**

La lectura es que k no puede elegirse por condición con este criterio, y que no
conviene intentarlo: una constante justificada por la forma de la curva en seis
datasets es más simple y rinde mejor. Es la cuarta vez que este repositorio
mide que el criterio interno predice mal el desempeño externo, junto con SFFS,
la selección del mejor sorteo por criterio interno y la regla de saturación
(`results/exploratory/SELECCION_BUSQUEDA_README.md`,
`results/analysis/policy_under_fix/`).

Los promedios de esta sección son **por condición**, de modo que DTD pesa diez
veces y Soil y FMD cinco; por eso sus niveles absolutos son menores que los de
las secciones anteriores, que promedian **por dataset**. La comparación relativa
entre reglas no depende de esa elección.
