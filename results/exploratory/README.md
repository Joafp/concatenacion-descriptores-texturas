# Búsquedas alternativas de subconjuntos: qué se probó y qué resultó

Guía de lectura del trabajo exploratorio sobre **cuántos descriptores hacen
falta y cómo elegirlos**. Nada de lo que está acá modifica los resultados
confirmatorios ni las tablas del manuscrito.

Rama: `feat/selection-search-experiments`.

## El resultado

**Cuatro descriptores de veintiuno —el 15 % de las dimensiones— igualan o
superan a la concatenación completa, y superan al estado del arte.**

Exactitud con un k fijo en 4, el mismo para los seis datasets, sin consultar el
test para elegirlo:

| Dataset | k=4 | 21 bloques | Neshov et al. | Scabini et al. | Supera a |
|---|---:|---:|---:|---:|---|
| DTD | 0,8703 | 0,8671 | 0,8200 | 0,7910 | ambos |
| FMD | 0,9820 | 0,9620 | 0,9670 | 0,9090 | ambos |
| KTH-TIPS2-b | 0,9575 | 0,9516 | 0,9680 | 0,9370 | Scabini |
| Outex13 | 0,9294 | 0,9618 | — | 0,9160 | Scabini |
| CUReT | 0,9986 | 0,9991 | — | — | — |
| Soil | 0,9289 | 0,9219 | — | — | — |

Todas las cifras de la tabla son **exactitud**, promediada sobre las particiones
externas de cada dataset.

La curva de acierto contra tamaño se aplana en k=4: con el 15 % de las
dimensiones se alcanza el 99,9 % del máximo, y el 85 % restante no aporta.

**La excepción es Outex13**, que necesita k=18 y a k=4 pierde 0,0330. Es el
único dataset donde la representación grande se justifica, y conviene decirlo.

Detalle completo, curva por k y limitaciones: [`k_sweep/README.md`](k_sweep/README.md).

## Lo que no funcionó, y por qué vale la pena leerlo

Seis métodos se probaron contra la concatenación completa y **ninguno la
superó**. Están documentados con sus números porque juntos sostienen un
diagnóstico, no una lista de fracasos.

| Método | Resultado | Dónde |
|---|---|---|
| Cascada hacia Top-k | −0,0021 del techo escalando el 44 % | [`topk_cascade/README.md`](topk_cascade/README.md) |
| SFFS, búsqueda con retroceso | gana el criterio interno 3/4, pierde el externo 4/4 | [`SELECCION_BUSQUEDA_README.md`](SELECCION_BUSQUEDA_README.md) |
| Regla de saturación | deja de dispararse al corregir el agrupamiento | [`../analysis/policy_under_fix/`](../analysis/policy_under_fix/) |
| Tómbola ponderada por ranking | +0,0087 sobre Top-k en ensamble, −0,0052 vs completa | [`SELECCION_BUSQUEDA_README.md`](SELECCION_BUSQUEDA_README.md) |
| Ponderación por diversidad | +0,0017 en 5/12; empeora el ensamble | [`SELECCION_BUSQUEDA_README.md`](SELECCION_BUSQUEDA_README.md) |
| Elección de k por regla interna | toda regla pierde contra la constante | [`k_sweep/README.md`](k_sweep/README.md) |

**El diagnóstico común:** el criterio interno —macro-F1 sobre pliegues internos—
predice mal el desempeño externo. Cuatro mediciones independientes lo muestran:
SFFS optimiza mejor el criterio y empeora afuera; elegir el mejor sorteo por
criterio interno no aporta; la regla de saturación se cae al corregir su propia
señal; y las curvas interna y externa de k correlacionan apenas +0,254, con
signo negativo en dos datasets.

Por eso buscar mejor no sirve y una constante simple gana: el cuello de botella
no es la búsqueda, es el criterio.

**Hallazgo adicional medido:** Top-k elige bloques redundantes. El CKA medio
dentro del Top-k es 0,890 contra 0,638 de subconjuntos al azar en Outex, con
tres variantes de DINOv2 ocupando tres de ocho lugares
([`../analysis/block_redundancy/`](../analysis/block_redundancy/)). El
diagnóstico es correcto; corregirlo explícitamente no mejora el resultado.

## Cómo reproducir

Cada README termina con los comandos exactos. Todos necesitan los embeddings,
que no están versionados: se extraen con `src/01_extract_features.py` o se piden
al equipo. `rgb_ngram_svd` se reconstruye por fold desde las imágenes fuente y
no participa de estos experimentos, de modo que la «biblioteca completa» de acá
son 21 bloques y **no** es idéntica al Completa de 22 del manuscrito.

Scripts, en `src/`:

| Archivo | Para qué |
|---|---|
| `run_k_sweep.py` | curva externa de acierto contra k |
| `run_k_sweep_inner.py` | la misma curva sobre los pliegues internos |
| `analyze_k_selection_rules.py` | compara reglas de elección de k |
| `run_sffs_selection.py` | selección flotante con retroceso |
| `run_weighted_lottery_selection.py` | muestreo ponderado por ranking |
| `run_diversity_lottery.py` | muestreo que penaliza la redundancia |
| `analyze_block_redundancy.py` | matriz CKA entre bloques |
| `check_policy_under_fix.py` | la regla de saturación antes y después de la corrección |

## Alcance

Seis datasets, 27 condiciones externas, SVM lineal, semilla 42. Las particiones
de CUReT son complementarias y dependientes, Outex tiene un único split, y las
de DTD y FMD reutilizan imágenes: **no se aplica ningún contraste inferencial** y
todas las comparaciones son descriptivas. Las familias se diseñaron después de
observar resultados externos previos del repositorio, así que esta etapa es
exploratoria; una afirmación confirmatoria exigiría método congelado y datos no
usados para diseñarlo. La comparación con la literatura es descriptiva porque
los protocolos, clasificadores y formas de agregación diferen entre trabajos.
