# Integración del descriptor RGB N-grams en el evaluador de rescate

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: implementación autorizada y análisis de corridas de desarrollo.
- Origin Date: 2026-10-21.
- Verification Status: ANALYZED. Pruebas de aislamiento e integración y tres corridas técnicas realizadas; recálculo de sus artefactos. Sin reproducción independiente del estudio histórico ni nueva evaluación externa canónica.
- Version Label: P1-A / integración de ejecución v4.
- Alcance: FMD, seed42, fold externo 0, 800 filas de entrenamiento; tres folds productores y dos de ranking/calibración. Seis datasets principales conservados; VisTex excluido.

## Cambio aplicado

`src/run_rescue_nested_selection.py` admite `--include-rgb-ngram` junto con una ruta explícita a un cache existente de conteos. La lectura comprueba identidad del manifiesto, implementación/configuración y estructura de índices. Abre los conteos en modo lectura y registra hashes de los cuatro archivos. Esta validación identifica los conteos usados; no vuelve a calcularlos desde las imágenes ni rehasha sus bytes fuente.

El ranking evalúa `rgb_ngram_svd` como un candidato adicional mediante el `inner_score` existente, que ajusta la SVD en cada entrenamiento interno. La misma transformación por entrenamiento se usa cuando N-gram participa en la base, la calibración o un rescate. La biblioteca nominal queda en 22 bloques y 20.652 dimensiones con 256 componentes. El modo de 21 bloques/20.396 dimensiones sigue disponible omitiendo la opción.

`src/singleton_ranking.py` firma la configuración y código de la transformación, además de los conteos de las filas de entrenamiento. Cambiar conteos de filas externas no invalida ni interviene en ese ranking. Los nombres de caché distinguen bibliotecas de 21 y 22. El lector de matrices no crea una SVD global.

`RGBNgramSVDBlock.transformation_audits()` permite guardar índices y hashes de cada proyección ejecutada. Antes de escribir resultados, el evaluador comprueba que las filas de fit y evaluación no se solapen y pertenezcan al outer-train. La dimensión efectiva se guarda por proyección porque una partición pequeña podría admitir menos de 256 componentes.

## Verificación y corridas técnicas

Las cuatro pruebas nuevas comprueban: invariancia de la representación entrenada frente a cambios en conteos de evaluación; identidad de caché dependiente solo de los conteos entrenados; ranking, calibración y clasificación con bloque dinámico; rechazo de un cache con manifiesto diferente. Junto a las dos pruebas existentes de puntuaciones y agrupación KTH, terminaron **6/6 aprobadas**.

Se reutilizó `results/confirmatory/rgb_ngram_count_cache/FMD/rgb_ngram_impl1`, correspondiente a las 1.000 imágenes del manifiesto. Las tres corridas usan el mismo outer-train canónico de FMD, los mismos folds productores, seed42, cinco miembros y SVM:

| Corrida | Biblioteca/base | Proyecciones SVD ejecutadas | Dimensión SVD |
|---|---|---:|---:|
| `smoke22_fmd_20261021` | 22, base automática SigLIP | 6 del ranking | 256 en todas |
| `smoke22_fmd_ngram_base_20261021` | 22, base N-gram impuesta como diagnóstico | 9 de calibración/base; ranking reutilizado con firma coincidente | 256 en todas |
| `smoke21_fmd_matched_20261021` | 21, base automática SigLIP | 0 | — |

Raíz de salidas: `results/exploratory/integration_v4/`. Las 15 proyecciones ejecutadas tienen lados disjuntos y ningún índice de test externo. Los hashes de los módulos registrados al lanzar las corridas coinciden con el código usado en esta auditoría.

`src/audit_ngram_rescue_integration.py` recalculó **63 macro-F1 y exactitudes** desde sus predicciones, con error máximo de macro-F1 de **1,11×10⁻¹⁶**. Verificó que cada compuerta coincide con `margen < umbral`, que la predicción adaptativa corresponde a la base o al rescate según esa compuerta y que el costo medio reconstruido por imagen coincide con el guardado (error máximo **8,53×10⁻¹⁴ ms**). Las 800 filas OOF de cada corrida están completas. El auditor produce `results/analysis/integration_v4/ngram_integration_20261021/`.

## Hallazgo observado y límites

N-grams ocupa los puestos **18, 18 y 17 entre 22** en los tres rankings internos del piloto FMD. No aparece en los rescates Top-3/4/5 ni en los miembros sorteados del piloto automático. La base y los Top-k tienen las mismas predicciones en el control emparejado de 21 bloques. Cambian algunos ensambles porque ampliar el conjunto de candidatos modifica el sorteo ponderado; una diferencia entre ellos no puede atribuirse a haber concatenado el N-gram si este no fue seleccionado.

Como base impuesta, N-gram obtuvo macro-F1 OOF **0,255538**, frente a **0,970082** de SigLIP en estas particiones. La variante impuesta se ejecutó para comprobar la ruta de calibración del bloque dinámico; este resultado no respalda elegirlo como base en FMD. Su bajo ranking individual tampoco descarta una contribución complementaria al combinarlo con otros bloques.

Los folds internos reducidos hacen que estos valores sean de desarrollo. No sustituyen las tablas del manuscrito ni demuestran superioridad, equivalencia o ausencia universal de fuga. El costo usa el perfil guardado y excluye latencias variables de clasificación, residencia/carga y medición física. No hubo contraste estadístico nuevo ni barrido de los seis datasets. El historial de exposición externa de los benchmarks permanece.

## Estado del plan

P1-A queda implementado y ejercitado con FMD real. La integración reutiliza las interfaces y los conteos existentes; los otros datasets aún requieren su corrida con el mismo contrato. P1-B sigue pendiente: el evaluador actual selecciona por ranking y calcula costo posteriormente. El siguiente avance es construir la selección bajo presupuesto y costo marginal de unión, incluyendo su ablación de relevancia, antes de extender el barrido canónico.

**Seguimiento posterior:** P1-B ya se implementó en un ejecutor separado y se evaluó en dos pilotos, incluido Outex con N-grams. El [reporte del selector](PILOTOS_SELECTOR_PRESUPUESTO_2026-10-21.md) y el plan integración v6 definen el estado vigente; el párrafo anterior conserva el cierre original de P1-A.
