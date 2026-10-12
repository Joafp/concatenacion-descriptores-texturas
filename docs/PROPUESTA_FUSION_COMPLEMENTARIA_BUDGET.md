# Piloto de fusión complementaria con presupuesto de dimensiones

## Estado

Implementación exploratoria, todavía no propuesta confirmatoria ni afirmación
de novedad. Los artefactos se guardan bajo
`results/exploratory/complementary_budget/`; no se mezclan con las tablas del
artículo.

## Pregunta

¿Puede una representación supervisada y de bajo rango conservar la información
complementaria de los 22 descriptores con muchas menos dimensiones que la
concatenación original?

La evaluación aprende una proyección PCA seguida por LDA regularizado dentro de
cada partición de entrenamiento. Una búsqueda codiciosa sobre validación
cruzada agrupada añade bloques y aumenta sus rangos mientras la macro-F1 media
interna mejore, respetando un máximo global de dimensiones. Se evalúa la
representación final con el mismo SVM lineal usado en la referencia. El test
externo solo se usa después de fijar selección y proyecciones.

## Pilotos exploratorios

Todos los pilotos descritos abajo son exploratorios, de una condición externa
cada uno, con semilla 42, tres folds agrupados internos, presupuesto máximo de
128 dimensiones, rangos candidatos 8/16/32 y ganancia interna mínima cero. El
umbral cero se fijó después de observar el primer piloto DTD; por tanto, estos
resultados no son confirmatorios y no deben usarse para sostener una conclusión
estadística.

Comando reproducible para DTD, partición oficial 1, semilla 42, tres folds
internos agrupados, máximo de 128 dimensiones y mejora interna mínima de 0,001:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  .venv-confirmatory/bin/python scripts/run_complementary_budget_pilot.py \
  --dataset DTD --official-split 1 --dimension-budget 128 \
  --rank-choices 8 16 32 --inner-folds 3
```

La ejecución seleccionó 104 dimensiones: SigLIP-B (32), DINOv2-L (32),
EVA-02 base (32) y BEiTv2-B final (8). El macro-F1 externo fue **0,8395**.
Al bajar el umbral interno de mejora a cero, el mismo split seleccionó 128
dimensiones y obtuvo macro-F1 **0,8438**. Esta sensibilidad es post hoc.

| Método | Macro-F1 externo | Dimensiones |
|---|---:|---:|
| Individual, referencia archivada | 0,8402 | 768 |
| Concatenación completa | 0,8663 | 20 652 |
| Top-k | 0,8720 | 3 712 |
| GFS | 0,8807 | 4 352 |
| Propuesta, umbral interno 0,001 | 0,8395 | 104 |
| Propuesta, umbral interno 0 | 0,8438 | 128 |

Las filas de referencia pertenecen al mismo DTD split oficial 1 y provienen
del protocolo de 22 descriptores. Es una sola condición exploratoria: la
propuesta no debe reemplazar GFS, Top-k ni la concatenación completa en la
tesis. Con el umbral cero, supera al mejor descriptor individual por 0,0036
macro-F1 usando 128 dimensiones, pero queda 0,0225 por debajo de la
concatenación completa y 0,0369 por debajo de GFS. Es una posible relación
compacta entre rendimiento y tamaño, aún no una mejora general. El umbral cero
se probó después de observar la primera ejecución; por eso ambas filas son
exploratorias y los valores externos no son confirmatorios.

La misma configuración con umbral cero se ejecutó en los cinco folds de
SoilOriginal, semilla 42. La media y desviación estándar son descriptivas; las
cinco condiciones no justifican una prueba confirmatoria.

| Método | Macro-F1 media ± DE | Folds ganados por la propuesta | Dimensiones de la propuesta |
|---|---:|---:|---:|
| Propuesta | 0,8742 ± 0,0418 | — | 12–42; media 28,8 |
| Completa | 0,8919 ± 0,0387 | 2/5 | 20 652 |
| GFS | 0,8681 ± 0,0254 | 2/5 | variable |
| Top-k | 0,8701 ± 0,0283 | 2/5 | variable |
| Individual | 0,8615 ± 0,0415 | 3/5 | 768 |
| LDA uniforme, 22 bloques | 0,8429 ± 0,0395 | 3/5 | 110 |
| Mejor bloque LDA seleccionado por CV interna | 0,8377 ± 0,0447 | 4/5 | 6 |

En Soil, dos folds muestran mejoras claras respecto de Completa, GFS y Top-k;
en los otros tres el resultado varía y en dos cae por debajo de Completa. La
media de la propuesta queda 0,0178 por debajo de Completa y apenas 0,0041 por
encima de Top-k. El control LDA uniforme obtiene 0,8429: la selección conjunta
es prometedora, pero aún falta establecer que su ventaja sea estable.

### Transferencia inicial a otros datasets

Se corrió una condición externa fija por dataset para comprobar transferencia,
sin recalibrar hiperparámetros. Las referencias se extrajeron de las mismas
filas experimentales de 22 descriptores (mismo split, seed y clasificador).

| Dataset / condición | Propuesta (dim.) | Completa | GFS | Top-k | Individual | LDA uniforme 22 bloques | Mejor bloque LDA |
|---|---:|---:|---:|---:|---:|---:|---:|
| FMD, fold 0 | 0,9399 (60) | 0,9398 | 0,9599 | 0,9647 | 0,9449 | 0,9241 (110) | 0,9252 (9) |
| CUReT, A→B | 0,9968 (128) | 0,9979 | 0,9982 | 0,9982 | 0,9929 | 0,9940 (110) | 0,9889 (32) |
| Outex, oficial 1 | 0,9481 (76) | 0,9656 | 0,9589 | 0,9426 | 0,9066 | 0,9398 (110) | 0,8713 (32) |
| KTH-TIPS2b, oficial 1 invertido | 0,9822 (46) | 0,9729 | 0,9633 | 0,9941 | 0,9941 | 0,7913 (110) | 0,9632 (10) |

El resultado es mixto y no respalda una mejora general: FMD queda casi igual
a Completa (diferencia +0,0001) pero pierde ante GFS y Top-k; CUReT A→B queda
por debajo de Completa/GFS/Top-k, aunque supera al mejor descriptor individual;
Outex supera a GFS y al control Top-k de esta condición, pero no a Completa;
KTH supera a Completa y GFS, pero queda por debajo de Top-k e Individual. La
propuesta usa entre 46 y 128 dimensiones, frente a 20 652 en Completa; eso
reduce la dimensión de la representación final, no el costo de extraer los 22
encoders.

Estas cuatro comparaciones son puntos de exploración, no pruebas pareadas ni
evidencia de significancia. CUReT requiere evaluar también B→A; FMD necesita
los cinco folds y las demás conclusiones deben cubrir todos los folds/splits
predefinidos. La selección interna casi saturó macro-F1 en CUReT, otro motivo
para auditar estabilidad y posibles efectos del tamaño de muestra antes de
escalar el estudio.

### Auditoría de robustez en curso

Se congeló una tanda adicional de 24 condiciones: 10 splits oficiales DTD,
5 folds FMD, las dos direcciones de CUReT, el split oficial disponible de
Outex13, 5 folds SoilOriginal y el split oficial disponible de KTH-TIPS2b.
Parámetros fijos: seed 42, SVM lineal balanceado, tres folds internos
agrupados, presupuesto 128, rangos 8/16/32 y ganancia interna mínima cero.
Cada condición se compara con las filas existentes de Individual, Completa,
GFS y Top-k bajo el mismo split.

La tanda se interpreta como auditoría exploratoria, no confirmatoria: el
umbral cero se eligió después de observar resultados externos de desarrollo.
Además, solo Outex y KTH tienen un split externo en este plan, por lo que no
permiten inferencia estadística entre particiones. La repetición corregida de
DTD split 1 reprodujo exactamente el piloto (macro-F1 0,843822; misma
asignación), tras detectar y corregir una implementación previa que limitaba
globalmente todos los rangos por el descriptor con menos dimensiones. El
resultado incompleto de aquella ejecución se conserva, marcado como inválido,
en `results/exploratory/complementary_budget_frozen_v1/`. La suite corregida
usa `results/exploratory/complementary_budget_frozen_v2/`.

## Alcance y controles pendientes

- El máximo de dimensiones no mide el costo de extracción de los encoders. Se
  siguen calculando los 22 embeddings; el ahorro observado aquí se limita a
  representación, almacenamiento y clasificador posterior.
- PCA/LDA, N-gramas y asignación de rangos se ajustan solo en entrenamiento;
  las particiones internas y externas respetan los grupos del manifiesto.
- El procedimiento es codicioso, utiliza coordenadas LDA ordenadas y puede
  ser sensible a la partición interna. El criterio de decorrelación de clase
  de LDA tiene antecedentes; la asignación de rangos por ganancia conjunta no
  demuestra por sí sola novedad bibliográfica.
- Antes de una afirmación de rendimiento se requiere una comparación anidada
  en los seis datasets y controles de dimensión igualada: PCA no supervisado,
  proyección supervisada sin selección conjunta, y GFS/Top-k. Deben informarse
  macro-F1, dimensiones, tiempo de ajuste y variabilidad entre condiciones.
- Una evaluación formal de costo total requiere medir cada encoder y demostrar
  que los extractores no seleccionados se pueden omitir en inferencia.

## Artefactos

- Ejecutor: `scripts/run_complementary_budget_pilot.py`.
- Suite congelada y reanudable: `scripts/run_complementary_budget_frozen_suite.py`.
- Proyecciones y asignación: `src/complementary_budget_fusion.py`.
- Resultados DTD split 1: `results/exploratory/complementary_budget/` y `results/exploratory/complementary_budget_min_gain0/`.
- Resultados SoilOriginal, cinco folds: `results/exploratory/complementary_budget_soil/`.
- Transferencia inicial FMD, CUReT A→B, Outex y KTH-TIPS2b: `results/exploratory/complementary_budget_transfer/`.
- Auditoría de robustez corregida: `results/exploratory/complementary_budget_frozen_v2/`.
