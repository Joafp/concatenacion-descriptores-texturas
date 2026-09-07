# Plan confirmatorio para el cierre de la tesis

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: plan
- Origin Date: 2026-07-18
- Verification Status: UNVERIFIED
- Version Label: confirmatory_plan_v1

## Objetivo

Determinar, sin reutilizar los datos de evaluación para seleccionar el
subconjunto, si Greedy Forward Selection (GFS) permite construir
concatenaciones de descriptores compactas que mejoran o mantienen el macro-F1
del mejor descriptor individual y de la concatenación completa.

## Pregunta e hipótesis

**Pregunta primaria:** ¿GFS mantiene su ventaja predictiva o su equivalencia con
menor dimensionalidad cuando la selección se realiza exclusivamente dentro de
los datos de entrenamiento?

**Hipótesis primaria:** GFS alcanzará un macro-F1 no inferior al mejor descriptor
individual dentro de un margen práctico de 0.01 y utilizará menos extractores y
menos dimensiones que la concatenación completa.

**Hipótesis secundaria:** los subconjuntos heterogéneos seleccionados superarán
la distribución de subconjuntos aleatorios del mismo tamaño y mostrarán
estabilidad parcial entre particiones, sin requerir una composición universal.

## Alcance congelado

- Bloque principal: DTD, FMD y CUReT. Outex_TC_00013 se incorporó después
  mediante la enmienda oficial de 2026-08-11. Soil y VisTex permanecen como
  extensiones suplementarias.
- Clasificadores confirmatorios primarios: SVM lineal y ResMLP.
- Clasificadores secundarios: KNN y Random Forest, únicamente si el costo lo
  permite después de completar el análisis primario.
- Extractores: todos los embeddings disponibles de forma consistente para cada
  dataset. El conjunto exacto y las dimensiones deben registrarse antes de la
  primera corrida.
- Métrica primaria: macro-F1 en datos outer-test no utilizados por GFS.
- Métricas secundarias: accuracy, número de extractores, dimensionalidad,
  tiempo, frecuencia de selección y estabilidad de Jaccard.
- No se agregarán nuevos modelos durante la fase confirmatoria.
- Los resultados exploratorios existentes no se sobrescribirán.

## Enmienda de protocolo posterior a la auditoría (2026-07-19)

Esta enmienda se registró antes de ejecutar cualquier clasificación
confirmatoria sobre CUReT. No modifica hipótesis, comparadores, extractores,
clasificadores, `max_k`, métricas ni controles aleatorios; únicamente adapta la
partición a la estructura demostrable de cada fuente y documenta exclusiones
impuestas por el gate de datos.

- **DTD:** se conservan los diez splits oficiales. GFS se selecciona en
  `train+val` y el `test` oficial se consulta una sola vez por split. Los
  duplicados byte-idénticos que cruzan roles se purgan del entrenamiento,
  conservando el test.
- **FMD:** se conservan 5 outer folds repetidos con semillas 42, 123 y 2026, y
  4 inner folds. Como las 1.000 imágenes oficiales tienen SHA-256 único, el
  grupo es la imagen fuente.
- **CUReT:** se usa exclusivamente la distribución gris recortada de Oxford
  VGG: 61 materiales, 92 condiciones comunes y 5.612 imágenes de 200x200. El
  grupo es el identificador de condición compartido por las 61 clases. Se
  evalúan dos mitades complementarias deterministas de 46 condiciones cada
  una: A para selección/entrenamiento y B para test, y luego B para
  selección/entrenamiento y A para test. La asignación alterna reproduce de
  forma transparente el tamaño 46/46 publicado, pero **no se presenta como
  recuperación del split histórico exacto**, que la fuente no identifica. La
  selección interna usa 4 folds agrupados por condición dentro de la mitad de
  entrenamiento. Debido a que solo hay dos evaluaciones complementarias y no
  independientes, se reportarán resultados descriptivos y no un test de
  significación entre splits. Fuentes primarias: [distribución de Oxford
  VGG](https://www.robots.ox.ac.uk/~vgg/research/texclass/) y [configuración
  experimental](https://www.robots.ox.ac.uk/~vgg/research/texclass/setup.html).
- **VisTex:** se excluye del nested-GFS principal. La distribución oficial
  tiene clases con solo dos unidades independientes; un outer split deja una
  sola unidad de entrenamiento y hace imposible la validación interna. Crear
  patches no aumenta el tamaño muestral independiente. Fuente primaria:
  [MIT Vision Texture](https://vismod.media.mit.edu/vismod/imagery/VisionTexture/vistex.html).
- **Outex_TC_00013:** se utiliza exclusivamente la colección completa de 1.360
  imágenes y la partición oficial 680/680 auditada en la enmienda de
  2026-08-11.
- **Soil:** se excluye mientras existan archivos ilegibles o de procedencia no
  demostrable.

En consecuencia, el bloque confirmatorio primario queda compuesto por DTD, FMD
y CUReT; Outex se incorpora como una extensión oficial directamente comparable
con RGB Pixel N-grams. Las exclusiones restantes son resultados de control de
calidad, no decisiones basadas en desempeño.

## Enmienda oficial de Outex_TC_00013 (2026-08-11)

- Fuente canónica: `Outex_TC_00013-20260120T014101Z-3-001.zip`.
- Integridad: 1.360 BMP RGB, 68 clases balanceadas, IDs continuos, cero
  duplicados y cero archivos corruptos.
- Protocolo externo: 680 imágenes oficiales de entrenamiento y 680 de prueba,
  diez por clase en cada rol.
- Selección: cuatro folds estratificados construidos únicamente dentro del
  entrenamiento oficial; el test no interviene en selección ni parada.
- Clasificadores: SVM lineal y ResMLP; una condición externa por clasificador.
- Debido a que existe una sola partición, se reporta el efecto observado y se
  omite inferencia entre splits.

## Fase 0 — Auditoría de datos y particiones

1. Verificar correspondencia exacta de muestras, etiquetas y orden entre todos
   los embeddings de un dataset.
2. Calcular hashes o identificadores que permitan detectar duplicados.
3. Identificar imágenes, parches o vistas que provengan de una misma fuente.
4. Preferir splits oficiales. Cuando exista dependencia por fuente, utilizar
   grupos y garantizar que un grupo no aparezca en train y test.
5. Producir `results/confirmatory/data_audit.csv` y
   `results/confirmatory/data_audit.md`.

**Gate:** no ejecutar el benchmark confirmatorio para un dataset si no puede
demostrarse que su outer split evita fugas directas entre muestras relacionadas.

## Fase 1 — Nested CV confirmatorio

- Outer CV: 5 folds, repetidos con semillas 42, 123 y 2026.
- Inner CV: 4 folds sobre el outer-train.
- Todo preprocesamiento se ajusta dentro del inner/outer train correspondiente.
- GFS completo dentro del inner CV, sin screening de un solo fold.
- `max_k = 8`.
- Regla de parada: detener cuando la mejora inner sea menor que 0.001 durante
  dos pasos consecutivos; conservar también el mejor paso histórico.
- Evaluar una sola vez en outer-test:
  1. mejor descriptor individual seleccionado en inner CV;
  2. concatenación completa fija;
  3. GFS;
  4. mejor familia homogénea de igual o menor `k`, cuando exista.

**Outputs:**

- `results/confirmatory/nested_fold_results.csv`
- `results/confirmatory/selected_subsets.jsonl`
- `results/confirmatory/nested_summary.csv`
- `results/confirmatory/run_manifest.json`
- `results/confirmatory/logs/`

## Fase 2 — Control contra subconjuntos aleatorios

- Para cada condición outer-test, generar 100 subconjuntos aleatorios sin
  reemplazo, del mismo `k` que GFS.
- Usar exactamente los mismos folds, clasificador y preprocesamiento.
- Si el tiempo estimado es aceptable, ampliar a 500 sin cambiar ningún otro
  parámetro.
- Calcular percentil de GFS y p-valor empírico
  `(1 + count(random >= GFS)) / (B + 1)`.
- No utilizar un z-test basado en diez subconjuntos.

**Output:** `results/confirmatory/random_subset_results.csv`.

## Fase 3 — Estabilidad y ablación

1. Frecuencia de selección de cada extractor y familia.
2. Jaccard medio y distribución entre folds y semillas.
3. Comparación de subconjuntos heterogéneos frente a subconjuntos homogéneos.
4. Comparación de macro-F1 frente a `k`, dimensionalidad y tiempo.

**Outputs:**

- `results/confirmatory/selection_frequency.csv`
- `results/confirmatory/stability_summary.csv`
- `results/confirmatory/family_ablation.csv`
- `results/confirmatory/cost_summary.csv`

## Análisis estadístico congelado

- Unidad primaria: resultado outer-test pareado por dataset, clasificador,
  semilla y fold.
- Reportar diferencia media, IC 95% por bootstrap pareado y tamaño de efecto.
- Contrastes primarios: GFS vs. mejor individual y GFS vs. concatenación
  completa, para seis datasets y dos clasificadores.
- Corrección Holm sobre los 24 contrastes primarios.
- Los cuatro clasificadores completos, si se ejecutan, se reportarán como
  análisis secundario separado.
- Una diferencia con `|delta macro-F1| < 0.01` se considerará prácticamente
  equivalente; no se interpretará `p > 0.05` como prueba de equivalencia.

## Criterios de cierre

El bloque experimental queda cerrado cuando:

1. la auditoría de cada dataset confirma un split aceptable o documenta su
   exclusión;
2. finalizan todas las condiciones primarias de nested CV;
3. no hay filas faltantes, NaN ni discrepancias de etiquetas;
4. una corrida de verificación reproduce una condición determinista y las
   condiciones estocásticas quedan dentro de 5% de diferencia relativa;
5. se generan los controles aleatorios, estabilidad y costo;
6. las conclusiones se redactan usando exclusivamente la evidencia outer-test.

## Entorno y monitoreo

- Working directory: `/home/joaquin/tesis_claude`
- Dependencias: `requirements.txt`
- Hardware esperado: RTX 4060 y CPU de 8 núcleos.
- Timeout inicial por corrida: 12 horas; revisar estimación después de un smoke
  test de un dataset, un clasificador y un outer fold.
- Nunca sobrescribir `results/tables/`; todos los outputs van a
  `results/confirmatory/`.
- Registrar comando, commit o hash de archivos, semillas, versiones, duración y
  estado de cada condición.

## Regla para actualizar el paper

El paper se actualizará solo después de validar los outputs. Se reemplazarán las
afirmaciones basadas en selección naive por resultados outer-test, se reducirán
las afirmaciones estadísticas masivas y se incluirán una tabla confirmatoria,
un análisis de estabilidad y una discusión explícita sobre particiones y fuga
de datos.
