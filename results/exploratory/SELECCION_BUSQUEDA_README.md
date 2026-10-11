# Cuatro búsquedas alternativas de subconjuntos de descriptores

Estado: **exploratorio y descriptivo**. No se modificó ningún resultado
confirmatorio ni ninguna tabla del manuscrito.

Todo lo que sigue comparte el protocolo confirmatorio: el mismo criterio interno
(macro-F1 sobre cuatro pliegues `StratifiedGroupKFold` del entrenamiento
externo), los mismos clasificadores, el test externo tocado una sola vez, y en
KTH-TIPS2-b el agrupamiento interno por muestra física
(`--inner-group-column sample`) y la exclusión de `beitv2_base_multilayer`.
Solo cambia **cómo se busca el subconjunto**.

La pregunta común: si GFS deja rendimiento sobre la mesa —la enumeración
exhaustiva de KTH mide una brecha de oráculo de $+0{,}0362$—, ¿lo recupera una
búsqueda mejor?

## 1. SFFS: búsqueda con paso de retroceso

`src/run_sffs_selection.py`. Selección secuencial flotante hacia adelante
(Pudil, Novovičová y Kittler, 1994, *Pattern Recognition Letters* 15(11),
1119–1125): tras cada inclusión intenta quitar el bloque menos significativo,
siempre que el subconjunto resultante supere al mejor conocido de ese tamaño.
Responde al *nesting effect*, que es la limitación que GFS tiene por diseño.

KTH-TIPS2-b, SVM, cuatro particiones, protocolo RADAM:

| Partición | GFS interno | SFFS interno | GFS externo | SFFS externo |
|---|---:|---:|---:|---:|
| 0 | 0,9425 | **0,9446** | **0,9839** | 0,9822 |
| 1 | 0,9325 | **0,9328** | **0,9050** | 0,9025 |
| 2 | 0,9537 | **0,9560** | **0,9616** | 0,9523 |
| 3 | 0,9415 | 0,9415 | 0,9195 | 0,9195 |
| media | 0,9425 | **0,9437** | 0,9425 | 0,9391 |

El mecanismo de flotación operó: 4 exclusiones en dos particiones, de modo que
la búsqueda deshizo elecciones y no degeneró en GFS. **SFFS gana por el criterio
interno en 3 de 4 particiones y pierde en el test externo en 4 de 4.**

Optimizar mejor el criterio empeora el resultado. Eso descarta el nesting como
causa del bajo desempeño de GFS aquí y localiza el problema en el criterio: el
macro-F1 sobre pliegues internos no predice el desempeño externo en este
dataset. Es la firma del sobreajuste al criterio de selección.

## 2. La regla de saturación bajo la corrección de agrupamiento

`src/check_policy_under_fix.py`. La regla adaptativa de
`results/analysis/selection_saturation/` usa el *headroom* del criterio interno
—$1 - \text{inner\_f1}$ del mejor bloque individual— y recurre a la
concatenación completa cuando ese margen cae por debajo de $\tau$. KTH es la
única partición donde la regla dispara en la validación *leave-one-dataset-out*.

Pero la corrección del agrupamiento interno existe justamente para que el
criterio deje de saturar allí, de modo que mueve la entrada de la propia regla:

| | Headroom medio | Satura | La regla logra | Siempre GFS | Siempre Completa |
|---|---:|---:|---:|---:|---:|
| Sin corrección (SVM) | 0,0002 | 4/4 | **0,9473** | 0,9213 | 0,9473 |
| Con corrección (SVM) | 0,0728 | 0/4 | 0,9425 | 0,9425 | **0,9473** |

Con la corrección la regla **deja de dispararse** y se vuelve idéntica a
«siempre GFS», por debajo de «siempre Completa». La saturación no era la causa
de que la selección fallara: era una señal que apuntaba en la dirección correcta
por correlación. Al corregir el defecto la señal desaparece y la respuesta
correcta sigue siendo la misma.

Ambas corridas usan la biblioteca disponible localmente, no la del manuscrito;
la comparación describe el comportamiento de la regla, no reproduce valores
publicados.

## 3. Tómbola ponderada por ranking

`src/run_weighted_lottery_selection.py`. Top-k concatena los $k$ mejores de
forma determinista y el control aleatorio archivado sortea $k$ bloques con
probabilidad uniforme. Ambos son extremos de una familia: al bloque de rango $r$
se le da peso $(n - r + 1)^{\beta}$ y se muestrea sin reemplazo. $\beta = 0$ es
el control uniforme; $\beta \to \infty$ es Top-k.

Doce condiciones (Outex 1, CUReT 2, KTH 4, Soil 5), SVM, 15 sorteos por celda.
Diferencia contra el Top-k de la misma condición:

| $\beta$ | Sorteo único | Mejor por criterio interno | Ensamble suave | Ensamble por voto |
|---|---:|---:|---:|---:|
| 0 | −0,0416 (1/12) | −0,0074 (3/12) | −0,0037 (5/12) | −0,0048 (5/12) |
| 1 | −0,0187 (2/12) | +0,0001 (3/12) | +0,0037 (5/12) | +0,0045 (6/12) |
| 2 | −0,0095 (4/12) | −0,0012 (4/12) | **+0,0080 (8/12)** | +0,0062 (8/12) |
| 4 | −0,0037 (5/12) | −0,0003 (4/12) | +0,0069 (7/12) | +0,0055 (6/12) |
| 8 | −0,0005 (6/12) | +0,0020 (4/12) | +0,0066 (7/12) | **+0,0065 (8/12)** |

Un sorteo aislado pierde contra Top-k con todo $\beta$, y el déficit se cierra
monótonamente a medida que $\beta$ crece, como corresponde si $\beta \to \infty$
converge a Top-k. Lo que gana es el **ensamble**: un clasificador por sorteo con
las predicciones combinadas, que aprovecha errores decorrelacionados en lugar de
buscar más fuerte (Ho, 1998, *Random Subspace Method*, IEEE TPAMI 20(8),
832–844). Seleccionar el mejor sorteo por el criterio interno no aporta, lo que
concuerda con el resultado de SFFS.

## 4. Redundancia entre bloques y muestreo por diversidad

`src/analyze_block_redundancy.py` mide CKA lineal (Kornblith et al., 2019) entre
bloques sobre las filas de entrenamiento.

**Diagnóstico.** Top-k elige bloques mucho más parecidos entre sí que el azar:

| | CKA medio dentro del Top-k | CKA medio de subconjuntos al azar |
|---|---:|---:|
| Outex, $k=8$ | **0,890** | 0,638 |
| KTH, $k=2$ | **0,901** | 0,617 |

En Outex los tres pares más redundantes de toda la biblioteca están dentro del
Top-k: `dinov2`~`dinov2_large` 0,959, `dinov2`~`dinov2_small` 0,941 y
`dinov2_large`~`dinov2_small` 0,931. Tres variantes del mismo modelo ocupan tres
de los ocho lugares.

**Corrección propuesta.** `src/run_diversity_lottery.py` descuenta la relevancia
por el parecido con lo ya elegido, $u_i = r_i - \lambda \cdot \overline{\text{CKA}}(i, \text{elegidos})$,
recalculado en cada paso, en el espíritu de mRMR (Peng, Long y Ding, 2005, IEEE
TPAMI 27(8), 1226–1238). $\lambda = 0$ reproduce la tómbola anterior y, con
$\beta \to \infty$, Top-k exactamente —verificado: el determinista con
$\lambda = 0$ da el valor de Top-k en todas las condiciones.

Doce condiciones, diferencia contra Top-k:

| $\lambda$ | Determinista | Ensamble suave ($\beta = 2$) |
|---|---:|---:|
| 0,00 | +0,0000 (0/12) | **+0,0087 (8/12)** |
| 0,25 | +0,0016 (2/12) | +0,0056 (7/12) |
| 0,50 | +0,0017 (5/12) | +0,0028 (6/12) |
| 0,75 | +0,0014 (3/12) | +0,0043 (7/12) |
| 1,00 | −0,0020 (3/12) | +0,0064 (7/12) |

**El diagnóstico es correcto y la corrección no funciona.** Como método
determinista la ganancia es +0,0017 acertando en 5 de 12, indistinguible del
ruido. Dentro del ensamble, la diversidad explícita lo **empeora**: $\lambda = 0$
rinde mejor que cualquier $\lambda > 0$. Una explicación compatible es que el
ensamble ya obtiene su diversidad **entre** miembros, porque cada sorteo produce
un subconjunto distinto; forzarla **dentro** de cada miembro no agrega variedad
al conjunto y sí le resta relevancia a cada uno.

## Resumen

| Método | Macro-F1 medio | vs Completa |
|---|---:|---:|
| Completa | **0,9541** | — |
| Ensamble de tómbola | 0,9489 | −0,0052 |
| Diversidad determinista | 0,9445 | −0,0096 |
| Top-k | 0,9379 | −0,0162 |
| GFS | 0,9327 | −0,0214 |

Las dos filas intermedias toman el mejor parámetro **por dataset**, protocolo
optimista que se reporta sólo como cota. Con un parámetro fijo las ganancias
sobre Top-k son +0,0087 (ensamble, $\beta = 2$) y +0,0017 (diversidad,
$\lambda = 0{,}5$).

Ninguna de las cuatro búsquedas supera a la concatenación completa en ninguno de
los cuatro datasets, ni en macro-F1 ni en exactitud. La ordenación entre métodos
de selección sí es consistente y las dos propuestas nuevas mejoran a GFS y a
Top-k.

## Limitaciones

- Cuatro datasets y doce condiciones externas, con un solo clasificador (SVM) y
  una sola semilla. Las particiones de CUReT son complementarias y dependientes,
  Outex tiene un único split: no se aplica ningún contraste inferencial y las
  comparaciones son descriptivas.
- Los experimentos de SFFS y de la regla de saturación usan la biblioteca de
  bloques disponible localmente al momento de correrlos, que no es la del
  manuscrito; describen comportamiento, no reproducen valores publicados.
- `rgb_ngram_svd` no participa en ninguna de estas búsquedas: se reconstruye por
  fold desde las imágenes fuente y no está en el paquete de embeddings.
- Los ensambles entrenan 15 clasificadores por celda. No se midió su costo de
  extracción ni de inferencia, y en los $\beta$ de mejor desempeño la unión de
  bloques cubre casi toda la biblioteca, de modo que no se afirma ahorro alguno.
- Las familias se evaluaron después de haber observado resultados externos
  previos de este repositorio, así que esta etapa es exploratoria; una
  afirmación confirmatoria requeriría método congelado y datos no usados para
  diseñarlo.

## Comandos

```bash
# 1. SFFS
python src/run_sffs_selection.py --dataset KTHTIPS2b --classifier svm --seed 42 \
  --official-split 1 --invert-official-split --inner-group-column sample \
  --max-k 8 --n-jobs 10 \
  --audit-root results/extensions/kth_tips2b \
  --manifest-root results/extensions/kth_tips2b \
  --embedding-root embeddings_extensions \
  --output results/extensions/kth_tips2b/sffs_inner_group_sample

# 2. La regla de saturación bajo la corrección
python src/check_policy_under_fix.py

# 3. Tómbola por ranking
python src/run_weighted_lottery_selection.py --dataset Outex13Official1360 \
  --classifier svm --seed 42 --official-split 1 --draws 15 --betas 0 1 2 4 8 \
  --audit-root results/extensions/outex13_official1360 \
  --manifest-root results/extensions/outex13_official1360 \
  --results-root results/extensions/outex13_official1360 \
  --embedding-root embeddings_extensions \
  --output results/exploratory/lottery/outex13

# 4. Redundancia y muestreo por diversidad
python src/analyze_block_redundancy.py --dataset Outex13Official1360 \
  --official-split 1 \
  --audit-root results/extensions/outex13_official1360 \
  --manifest-root results/extensions/outex13_official1360 \
  --results-root results/extensions/outex13_official1360 \
  --embedding-root embeddings_extensions

python src/run_diversity_lottery.py --dataset Outex13Official1360 \
  --classifier svm --seed 42 --official-split 1 --draws 15 \
  --lambdas 0 0.25 0.5 0.75 1.0 --betas 2 8 \
  --audit-root results/extensions/outex13_official1360 \
  --manifest-root results/extensions/outex13_official1360 \
  --results-root results/extensions/outex13_official1360 \
  --embedding-root embeddings_extensions \
  --output results/exploratory/diversity/outex13
```
