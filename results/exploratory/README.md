# Búsquedas alternativas de subconjuntos: qué se probó y qué resultó

Guía de lectura del trabajo exploratorio sobre **cuántos descriptores hacen
falta y cómo elegirlos**. Nada de lo que está acá modifica los resultados
confirmatorios ni las tablas del manuscrito.

Ramas: `feat/selection-search-experiments` (etapa anterior) y
`feat/k4-professor-ideas` (grilla completa).

## Grilla completa: dos clasificadores y pruebas estadísticas

La etapa anterior (más abajo) usó SVM y la semilla 42. Esta repite todo sobre la
grilla del manuscrito: seis datasets y 47 condiciones externas por clasificador
(FMD y Soil con las semillas 42, 123 y 2026), con SVM lineal y ResMLP. Subconjunto
de k=4 bloques; los ensambles combinan 15 sorteos con $\beta=8$ (tómbola) y
$\lambda=0{,}25$, $\beta=8$ (diversidad), configuraciones elegidas con SVM y
aplicadas sin cambios a ResMLP. Macro-F1, media por dataset y luego entre datasets:

| Método | SVM | ResMLP |
|---|---:|---:|
| Completa-22 (manuscrito) | **0,9391** | 0,9288 |
| Ensamble con diversidad | 0,9383 | **0,9394** |
| Ensamble tómbola | 0,9369 | **0,9394** |
| Top-4 | 0,9366 | 0,9331 |
| 21 bloques (sin color) | 0,9356 | 0,9299 |

**Con ResMLP, seleccionar le gana a concatenar todo**; con SVM la Completa-22 sigue
arriba por menos de una milésima frente al ensamble con diversidad.

**Pruebas, con el procedimiento del manuscrito** (SCI2S sobre una media por
dataset, Holm sobre los 28 pares de ocho métodos, Wilcoxon exacto bilateral):

- Friedman, Iman–Davenport y Quade rechazan con ambos clasificadores; Friedman
  alineado no. Tras Holm, solo los dos ensambles superan a Individual con ResMLP;
  ningún par es significativo con SVM.
- Top-4 frente a Completa-22: Wilcoxon $p=1{,}00$ (SVM) y $p=0{,}56$ (ResMLP).
  Los ensambles frente a Completa-22 con ResMLP: $p=0{,}0625$, cinco de seis
  datasets; con seis datasets el mínimo posible es 0,031.
- No inferioridad con margen de 0,01: se demuestra para Top-4 con ResMLP
  ($p=0{,}010$); no con SVM, donde Outex solo permite descartar una pérdida de
  0,018.

**Controles y robustez:**

- *¿Sortear o solo votar?* Quince modelos sobre el mismo Top-4 cambiando la
  semilla dan 0,9366 (SVM, idéntico a Top-4) y 0,9356 (ResMLP); con bagging,
  0,9340 y 0,9327. Con ResMLP, unas tres quintas partes de la mejora del ensamble
  vienen de sortear subconjuntos distintos. No es significativo.
- *Configuración:* con ResMLP las diez configuraciones que usan el ranking
  superan a la Completa-22 (0,936 a 0,939); el sorteo uniforme sin ranking
  ($\beta=0$) queda a la par (0,930).
- *Cantidad de modelos:* con ResMLP la mejora llega con tres a cinco; quince ya
  está en la meseta.
- *ResMLP con 21 bloques:* reducirlos con PCA al tamaño del Top-4 (0,9308) o
  regularizar más (0,9274) no recupera el desempeño del Top-4 (0,9331). No es el
  tamaño de la entrada sino qué bloques entran.
- *Costo:* el ranking interno hace que entrenar Top-4 lleve más tiempo que entrenar
  la concatenación completa (641 s contra 157 s con SVM, seis condiciones). El
  modelo final tiene un sexto de las dimensiones y, con SVM, predice unas siete
  veces más rápido.

Dónde está cada cosa:

| Qué | Resultados | Script |
|---|---|---|
| Curva de k | `k_sweep/`, `resmlp/k_sweep/` | `run_k_sweep.py` |
| Tómbola y diversidad | `k4/`, `resmlp/k4/` | `run_weighted_lottery_selection.py`, `run_diversity_lottery.py` |
| Control de ensambles | `ensemble_control/` | `run_ensemble_control.py` |
| Cantidad de modelos | `ensemble_size/` | `run_ensemble_size.py` |
| ResMLP con 21 bloques | `resmlp_capacity/` | `run_resmlp_capacity.py` |
| Costo | `selection_cost/` | `measure_selection_cost.py` |
| Tablas del reporte | `../analysis/selection_tables/` | `build_selection_tables.py` |
| Pruebas estadísticas | `../analysis/selection_stats/` | `run_selection_stats.py` |

`scripts/run_selection_grid.sh` corre el control, la cantidad de modelos, la
capacidad y el costo sobre las 47 condiciones. `run_selection_stats.py` necesita
Java para SCI2S; con `--tables-only` regenera las tablas LaTeX sin volver a
correr las pruebas. El ranking interno de cada condición se calcula una vez y se
guarda en `ranking_cache/` (`src/singleton_ranking.py`).

`src/resmlp_classifier.py` cambió solo en velocidad: la pérdida de cada época se
acumula en el dispositivo. Pesos y predicciones son idénticos bit a bit en CPU y
GPU.

## Etapa anterior: SVM, semilla 42

**Cuatro descriptores —un quinto del tamaño de la representación completa—
superan al estado del arte y quedan a 0,004 de la concatenación completa.** La
concatenación completa del manuscrito sigue siendo el mejor método en promedio.

Exactitud con un k fijo en 4, el mismo para los seis datasets, sin consultar el
test para elegirlo, frente a la Completa de 22 bloques del manuscrito en las
mismas particiones (semilla 42):

| Dataset | k=4 | Completa-22 | Neshov et al. | Scabini et al. | k=4 supera a |
|---|---:|---:|---:|---:|---|
| DTD | 0,8703 | 0,8654 | 0,8200 | 0,7910 | Completa, Neshov, Scabini |
| FMD | 0,9820 | 0,9650 | 0,9670 | 0,9090 | Completa, Neshov, Scabini |
| KTH-TIPS2-b | 0,9575 | 0,9609 | 0,9680 | 0,9370 | Scabini |
| Outex13 | 0,9294 | 0,9662 | — | 0,9160 | Scabini |
| CUReT | 0,9986 | 0,9989 | — | — | — |
| Soil | 0,9289 | 0,9333 | — | — | — |
| **media** | **0,9444** | **0,9483** | | | |

Todas las cifras son **exactitud**, promediada sobre las particiones externas de
cada dataset. En macro-F1 la diferencia media es la misma en signo: k=4 0,9367
contra Completa-22 0,9409 (−0,0042).

**Lo que se sostiene:** con cuatro bloques se supera a Scabini et al. en los
cuatro datasets comparables y a Neshov et al. en dos de tres, y se gana a la
concatenación completa en DTD y FMD. **Lo que no:** que concatenar menos sea mejor
que concatenar todo. La Completa-22 gana en cuatro de seis datasets y en el
promedio.

**La excepción es Outex13**: necesita k=18 y a k=4 pierde 0,0368 contra la
Completa-22. Es el dataset donde la representación grande más se justifica.

### La diferencia entre 21 y 22 bloques es el color

El barrido de k trabaja con los 21 bloques almacenados; la Completa del
manuscrito agrega `rgb_ngram_svd`, que se reconstruye por fold desde las
imágenes. Ese único bloque explica la distancia: contra los 21 bloques, k=4 sí
queda arriba en promedio (0,9367 contra 0,9348 en macro-F1), pero agregarle el
N-gram a la concatenación completa sube +0,021 en Soil y +0,011 en KTH-TIPS2-b.
El descriptor de color nunca entra individualmente en el top 4 y, sin embargo,
aporta información que los otros 21 no tienen.

La prueba natural pendiente es **top 4 + `rgb_ngram_svd`**: cinco bloques, un
cuarto del tamaño, para ver si alcanza a la Completa-22.

Con 21 bloques la curva de acierto contra tamaño se aplana en k=4: con el 15 % de
las dimensiones se alcanza el 99,9 % del máximo de esa curva.

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

Etapa anterior: seis datasets, 27 condiciones externas, SVM lineal, semilla 42.
La grilla completa de arriba sí aplica las pruebas del manuscrito. Las particiones
de CUReT son complementarias y dependientes, Outex tiene un único split, y las
de DTD y FMD reutilizan imágenes: **no se aplica ningún contraste inferencial** y
todas las comparaciones son descriptivas. Las familias se diseñaron después de
observar resultados externos previos del repositorio, así que esta etapa es
exploratoria; una afirmación confirmatoria exigiría método congelado y datos no
usados para diseñarlo. La comparación con la literatura es descriptiva porque
los protocolos, clasificadores y formas de agregación diferen entre trabajos.
