# P2: controles de Carlos y ablación de N-grams

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: implementación y evaluación de controles emparejados de desarrollo.
- Origin Date: 2026-10-21.
- Verification Status: ANALYZED. Agregación de scores, predicciones, métricas y costos recalculada; selección de 21 bloques reproducida desde scores. Sin reproducción independiente del ajuste de modelos ni evaluación externa nueva.
- Version Label: avance P2 / ejecución `integration_v6`, plan integración v7.
- Alcance: FMD seed42/fold0 y Outex13 official1 dentro de sus respectivos entrenamientos externos. No se añaden datasets ni se reemplazan tablas del manuscrito.

## Qué usamos del trabajo de Carlos

El historial Git atribuye los scripts de muestreo/diversidad a `CarlosAyala00`: `ab1dd32` introduce las búsquedas, `5cb788e` fija subconjuntos de cuatro bloques y `409ed64` comparte el ranking individual y amplía a ResMLP. La integración ya usaba `rank_weights()` y su idea de muestrear subconjuntos por relevancia individual. Nuestro selector añade base, compuerta y elección de miembros bajo costo marginal de unión.

Ahora se incorpora una comparación directa con dos recetas estáticas: tómbola de 15 miembros y diversidad de 15 miembros. `src/run_carlos_paired_controls.py` importa `rank_weights()` y `draw_subset()` de los scripts existentes. Los parámetros k=4, beta=8 y lambda de diversidad=0,25 proceden de `results/analysis/selection_tables/svm.json`, cuyo hash queda guardado. La inferencia usa escalas de puntuación congeladas en entrenamiento, según la corrección ya implementada.

La CKA de diversidad se calcula exclusivamente con representaciones de fit productor. Se usa la expresión equivalente en matrices de Gram por filas para evitar repetir productos grandes por dimensión; una prueba verifica equivalencia numérica con `linear_cka()` de Carlos. N-grams aprende su SVD en ese mismo fit. Se guardan CKA, miembros, escalas, scores y predicciones; miembros repetidos conservan su peso de voto, con cada modelo único ejecutado una vez.

Estas son adaptaciones emparejadas de las recetas, no reproducciones de sus cifras históricas: aquí se utiliza la biblioteca común de 22 y los folds productores del piloto, con semilla extendida para identificar cada fold. No se ha corrido aún el control ResMLP en este protocolo. El aporte de Carlos se usa como componente y como referencia competitiva; no se ha demostrado que el método adaptativo lo supere globalmente.

## Comparación directa

Cada celda muestra macro-F1 OOF / ms de extracción proyectados. FMD conserva tres folds productores y dos de selección; Outex tres y tres. Dentro de cada dataset, los controles comparten exactamente fit, validación, manifiestos, matrices y etiquetas con el piloto previo. Las medias de costos ponderan imágenes y cobran la unión de bloques una sola vez.

| Dataset | Adaptativo ilustrativo | Carlos diversidad, soft | Carlos tómbola, soft | Completa-22 |
|---|---|---|---|---|
| FMD | B60: 0,977551 / 24,24 | 0,978777 / 350,66 | 0,977519 / 361,30 | 0,961310 / 1706,42 |
| Outex | B120: 0,909417 / 81,15 | 0,914389 / 365,20 | 0,898814 / 363,87 | 0,913957 / 1706,42 |

Los ensambles de diversidad tienen mayor F1 que los puntos adaptativos mostrados en ambos pilotos. El adaptativo tiene menor costo proyectado. La diferencia de Outex entre diversidad y adaptativo es aproximadamente 0,004972 de macro-F1. No hay prueba de equivalencia ni un criterio que permita declarar ganador absoluto sin fijar el compromiso de calidad/costo. Los votos duros también se conservaron como controles; no se elige entre soft y hard por cuál dio mejor resultado externo.

## Ablación de biblioteca y de ruta fija en Outex

Se volvió a ejecutar el selector con 21 bloques, mismos folds y parámetros. También se mantuvieron las rutas seleccionadas con 22, quitando únicamente N-grams de los miembros de rescate y reajustando esos clasificadores. En esta segunda ablación la base y el umbral quedan congelados; las decisiones de escalado coinciden con la referencia. Los modelos repetidos tras quitar el bloque mantienen su peso en el ensamble.

| Variante del selector marginal B120 | Macro-F1 | ms proyectados |
|---|---:|---:|
| 22 bloques, selección original | 0,909417 | 81,1483 |
| Misma ruta, rescates sin N-grams | 0,900328 | 76,7138 |
| 21 bloques, selección completa repetida | 0,895772 | 85,8746 |

En las rutas seleccionadas, retirar el color reduce F1 aproximadamente 0,009089 y ahorra 4,4346 ms proyectados por imagen. El cambio de costo coincide con 18,50 ms por imagen efectivamente escalada que requería el bloque. Esto respalda un aporte de color condicionado a estas rutas y esta condición de desarrollo.

La concatenación completa también mejora al añadir color: 0,902203 con 21 frente a 0,913957 con 22. Por tanto, el beneficio del descriptor no es exclusivo de la política adaptativa.

## Confusión detectada en el generador

El pool inicial contiene Top-2+N-grams, pero no Top-2 solo. Además, al cambiar el número de candidatos de la biblioteca cambia el sorteo ponderado. Por ello, la comparación entre selecciones completas de 21 y 22 mezcla el efecto del descriptor con cambios del generador y de las rutas elegidas. La ablación con ruta fija aísla mejor el efecto del bloque en las rutas ya seleccionadas, pero no prueba cuál es la mejor política posible sin color.

Antes de congelar el método debe existir un pool común de bloques estáticos con sorteos emparejados, incluyendo Top-2. Para cada rescate se considerarán sus versiones con y sin N-grams. Así, elegir color no será consecuencia de faltar su alternativa sin ese bloque. Esta corrección requiere una versión nueva y repetir el piloto; no se atribuirán retrospectivamente sus resultados a la corrida existente.

## Auditoría y archivos

Las 16 pruebas pertinentes aprobaron, incluyendo equivalencia de CKA y votos ponderados por multiplicidad. `src/audit_p2_controls.py` reconstruye los 15 miembros desde ranking, CKA y semillas; recalcula soft/hard desde scores guardados; comprueba miembros únicos, costos de unión y predicciones. También reconstruye las 24 decisiones de ablación fija, verificando base, margen, gate, predicción y diferencia exacta de costo por color.

El auditor de presupuestos reproduce otras 24 selecciones del piloto Outex-21 y sus 13 resultados. Junto al panel anterior, la tabla comparativa contiene 55 filas de método/dataset/variante, no 55 réplicas independientes. Se conservan presupuestos, resultados desfavorables y todos los votos auxiliares. No se calcularon p-valores nuevos.

Artefactos nuevos bajo `results/exploratory/integration_v6/`: `carlos_fmd22_20261021`, `carlos_outex22_20261021`, `budget_outex21_20261021` y `outex_fixed_no_ngram_20261021_final`. Auditorías: `results/analysis/integration_v6/p2_controls_20261021/` y `outex21_replay/`. La primera versión técnica de ablación se preserva; el sufijo `final` identifica la ejecutada con el manejo explícito de casos inelegibles.

## Seguimiento: pool emparejado cerrado

La comparación corregida finalizó y fue auditada en [POOL_EMPAREJADO_OUTEX_2026-10-21.md](POOL_EMPAREJADO_OUTEX_2026-10-21.md). El plan vigente es v8: 48 selecciones reproducidas, 26 resultados y scores comunes emparejados. Las cifras de este informe describen el pool anterior; no reemplazar la evidencia corregida por su mejor resultado histórico. Siguen pendientes las restantes ablaciones P2.

## Decisión histórica para continuar

P2 avanzó con los controles directos de Carlos y dos ablaciones de color. Quedan por cerrar el pool emparejado con/sin color, CV interno común, sensibilidad de bases/semillas, GFS y cascada histórica reconciliados, y validación de presupuesto fuera de muestra. La prioridad es corregir el generador antes del barrido de 27. Mantener ambos objetivos visibles: los controles estáticos aportan calidad; el adaptativo busca obtener una calidad útil con menor adquisición. La latencia de clasificación, residencia/carga y medición física siguen pendientes.

ARS: se revisaron los 11 riesgos de interpretación. Se evita mezclar datasets/objetivos (Simpson), extrapolar medias a cada muestra (falacia ecológica), seleccionar solo condiciones favorables (Berkson/supervivencia), atribuir mecanismos al gate o a CKA (colisionador/causalidad), confundir F1 con accuracy (tasas base), tomar un piloto como estabilidad (regresión a la media), elegir retrospectivamente un presupuesto/voto ganador (multiplicidad/caminos analíticos) o inferir ahorro físico/causalidad inversa desde proyecciones. Esta revisión es de la misma conversación, no un dictamen independiente.
