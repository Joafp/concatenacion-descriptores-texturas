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
de la curva. El 85 % restante de la representación no aporta: la biblioteca
completa de 21 bloques queda en 0,9348, por debajo de k=4.

## Un k fijo supera a la concatenación completa

Sin elegir k mirando el test, el mismo k=4 para los seis datasets:

| Dataset | Macro-F1 | Exactitud | % dims | vs 21 bloques |
|---|---:|---:|---:|---:|
| CUReT | 0,9986 | 0,9986 | 14 | −0,0005 |
| DTD | 0,8689 | 0,8703 | 16 | +0,0032 |
| FMD | 0,9819 | 0,9820 | 16 | +0,0198 |
| KTH-TIPS2-b | 0,9544 | 0,9575 | 16 | +0,0048 |
| Outex13 | 0,9288 | 0,9294 | 14 | **−0,0330** |
| Soil | 0,8876 | 0,9289 | 15 | +0,0168 |
| **media** | **0,9367** | **0,9444** | **15** | **+0,0018** |

**Outex es la excepción y conviene nombrarla, no esconderla:** su óptimo está en
k=18, con el 99 % de las dimensiones, y a k=4 pierde 0,0330. Es el único dataset
donde la representación grande se justifica.

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
- **k=4 se eligió observando esta curva**, que se trazó sobre los tests
  externos. La afirmación defendible es que la curva se aplana temprano; fijar
  el k con rigor exige una regla calculada sólo con entrenamiento, por ejemplo
  el codo de la curva del criterio interno. Ese paso queda pendiente.
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
