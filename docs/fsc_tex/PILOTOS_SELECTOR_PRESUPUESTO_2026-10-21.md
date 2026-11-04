# Selector de base y rescate bajo presupuesto: implementación y pilotos

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: implementación autorizada, corridas de desarrollo y recálculo de artefactos.
- Origin Date: 2026-10-21.
- Verification Status: ANALYZED. Selecciones reproducidas desde scores guardados y métricas/costos recalculados; los ajustes de modelos no se reprodujeron de forma independiente.
- Version Label: P1-B, ejecución `integration_v5`; plan de trabajo integración v6.
- Alcance: dos condiciones canónicas de entrenamiento externo, FMD seed42/fold0 y Outex13 official1. Evaluación nueva limitada al outer-train; los benchmarks ya estuvieron expuestos históricamente.

## Método implementado

`src/budgeted_rescue.py` implementa una búsqueda greedy con costo marginal de unión. Para cada presupuesto medio de extracción, considera bases en la frontera interna de macro-F1 individual y costo, umbrales de margen y hasta tres miembros de rescate. El objetivo de cada paso es una ganancia positiva de macro-F1 dividida por el aumento del costo proyectado. Un miembro que reutiliza todos los extractores ya adquiridos puede tener costo marginal de extracción cero, aunque agrega clasificación. Los pasos sin mejora se detienen.

Para una base `b`, miembros `S`, tasa interna de escalado `p` y unión de bloques `U`, el costo es `t(b) + t(compuerta) + p × suma[t(j), j en U sin b]`. Una base sin rescate solo paga su extractor. Cada bloque compartido se cobra una vez. La latencia de clasificadores no está incluida y sus llamadas se registran aparte. El límite de tres miembros evita crecimiento ilimitado; no sustituye una medición de esa latencia.

La regla conserva todos los puntos visitados que cumplen el presupuesto en las filas de selección y elige por mayor macro-F1 interno; desempata por menor costo, menos miembros y orden determinista de base/umbral/miembros. No garantiza el óptimo global. Una opción sin base factible se informa como inviable, con cobertura incompleta y métricas ausentes, en vez de omitirla.

La ablación `relevance` usa los mismos presupuestos, bases, candidatos, compuertas y límite de miembros. Cambia únicamente el mérito greedy a ganancia de macro-F1 sin dividir por costo. Por tanto, es relevancia bajo el mismo presupuesto, no una réplica de los ensambles históricos de Carlos sin restricciones.

El generador común contiene Top-3/4/5, cinco sorteos de cuatro bloques con beta=8, los tres bloques menos costosos y Top-2+N-grams. Se deduplican los subconjuntos. Incluir el candidato con N-grams permite evaluar complementariedad aunque el descriptor tenga un ranking individual bajo. Este generador es acotado y no explora todos los subconjuntos.

## Protocolo y trazabilidad

`src/run_budgeted_rescue.py` genera OOF de todos los individuales y candidatos usando únicamente el fit de cada fold productor. Selecciona base, miembros y umbral con esos scores y etiquetas. Luego reajusta los modelos seleccionados sobre el fit completo y evalúa la política en la validación productora. Esas etiquetas de validación no se pasan al selector. El mismo esquema evalúa Individual, Top-3/4/5 y Completa-22.

Se fijó la grilla de desarrollo de presupuestos 15, 30, 60 y 120 ms y cuantiles 0,10/0,25/0,50 antes de estas corridas. Es una grilla de costo proyectado, sin preregistro ciego. FMD usa tres folds productores y dos de selección; Outex usa tres y tres para conservar 256 componentes SVD en las particiones internas. Cada comparación entre reglas dentro del dataset comparte exactamente esas particiones. Esta diferencia entre datasets debe armonizarse por razones de protocolo en P2 antes de congelar la configuración consolidada.

Los dos pilotos usan 22 bloques/20.652 dimensiones. Se guardan fuente y entorno, manifiestos, hashes train/test, folds, pool de candidatos, scores OOF de selección, márgenes, rutas greedy, decisiones por presupuesto, predicciones y costos por imagen. La SVD se aprende por fit; las 21 proyecciones ejecutadas tienen 256 componentes y lados disjuntos dentro del outer-train. No se evaluó el test externo de estas condiciones.

Salidas: `results/exploratory/integration_v5/budget_pilot_fmd_20261021/` y `budget_pilot_outex_20261021/`. `src/audit_budgeted_rescue.py` reproduce las 48 selecciones desde `selection_oof_scores.npz`, comprueba sus presupuestos de entrenamiento y recalcula 26 filas de resultados. También verifica grupos, identidad con el registro canónico, manifiestos/fuente, rutas y costos por imagen. Artefactos de auditoría: `results/analysis/integration_v5/budget_pilots_20261021/`.

Las pruebas pertinentes suman 13 aprobadas: siete del selector, cuatro de integración N-gram, una de escala de puntuaciones y una de agrupamiento KTH. No se ejecutó la suite completa.

## Resultados de desarrollo

Macro-F1 calculado sobre predicciones OOF productoras agrupadas; costo medio proyectado por imagen. Las columnas «costo» y «relevancia» son las dos reglas de selección bajo la misma restricción interna.

| Dataset | Presupuesto | F1 costo | F1 relevancia | ms costo | ms relevancia |
|---|---:|---:|---:|---:|---:|
| FMD | 15 | 0,970082 | 0,970082 | 11,6800 | 11,6800 |
| FMD | 30 | 0,977560 | 0,978802 | 18,4348 | 17,9542 |
| FMD | 60 | 0,977551 | 0,976293 | 24,2395 | 25,3290 |
| FMD | 120 | 0,976293 | 0,976293 | 46,3776 | 39,3852 |
| Outex | 15 | 0,858056 | 0,858056 | 12,2200 | 12,2200 |
| Outex | 30 | 0,857483 | 0,857483 | 19,9694 | 19,9694 |
| Outex | 60 | 0,887495 | 0,889190 | 46,4564 | 49,9126 |
| Outex | 120 | 0,909417 | 0,900622 | 81,1483 | 80,2627 |

Controles emparejados: cada celda presenta macro-F1 / ms proyectados.

| Dataset | Individual | Top-3 | Top-5 | Completa-22 |
|---|---|---|---|---|
| FMD | 0,970082 / 11,68 | 0,981270 / 128,43 | 0,976253 / 290,55 | 0,961310 / 1706,42 |
| Outex | 0,871642 / 177,30 | 0,882967 / 236,86 | 0,900824 / 288,43 | 0,913957 / 1706,42 |

En Outex a 120 ms la regla marginal mejora 0,008795 de macro-F1 frente a relevancia, con 0,886 ms más de costo observado. Frente a Top-5, la diferencia es +0,008593 con menor costo proyectado; frente a Completa-22 queda −0,004540. Es un punto prometedor de este piloto, no una conclusión de superioridad global o equivalencia con Completa.

En FMD a 60 ms la regla marginal mejora aproximadamente 0,001258 frente a relevancia y reduce su costo; a 30 ms relevancia tiene mejor calidad y menor costo. En Outex a 60 ms relevancia tiene mejor calidad y mayor costo. La calidad de validación no aumenta monótonamente con el presupuesto: la búsqueda puede optimizar el criterio interno sin reproducir la mejora en la validación productora.

La selección marginal a 120 ms usa SigLIP como base en FMD. En Outex usa DINOv2-small en dos folds y BEiT-v2-final en el tercero; sus rescates incluyen N-grams en los tres. Esto muestra que el bloque puede incorporarse como complemento; atribuirle una mejora causal requiere la ablación emparejada de 21 bloques.

## Presupuesto y límites

Las 48 selecciones cumplen el presupuesto en sus filas de entrenamiento. En validación hubo una excedencia: relevancia/60 ms, fold 1 de Outex, pasó de 55,081 ms internos a 64,135 ms observados. La media agrupada de esa política fue 49,913 ms; esa media no elimina la excedencia del fold. La regla marginal tuvo cero excedencias en estos 24 casos, sin garantía para datos nuevos.

El presupuesto controla una media estimada en selección, no el costo máximo por imagen ni una restricción garantizada fuera de muestra. Las proyecciones excluyen clasificadores, residencia/carga y lectura de imágenes. El ejecutor entrena y evalúa con embeddings para estudiar las políticas; estos tiempos no acreditan ahorro físico por extracción condicional.

Faltan la comparación reconciliada con GFS, la cascada anterior y ensambles de Carlos en el mismo protocolo, la estabilidad por semillas/folds, la ablación de biblioteca y la evaluación externa. La restricción a bases no dominadas individualmente puede excluir bases con incertidumbre útil; el greedy puede perder combinaciones cuya ganancia solo aparezca al agregar varios miembros juntos. No se realizaron contrastes estadísticos nuevos ni una verificación bibliográfica de novedad.

## Decisión para el plan

P1-B queda implementado y ejercitado en dos condiciones. La evidencia justifica continuar con P2: armonizar CV interno, comprobar sensibilidad y desviación del presupuesto, completar ablaciones de base/biblioteca y controles, y fijar una configuración antes del panel de 27. Los resultados actuales no justifican reemplazar las tablas ni la conclusión del manuscrito.

**Seguimiento P2:** los [controles directos de Carlos y ablaciones de color](P2_CARLOS_Y_ABLACION_COLOR_2026-10-21.md) ya están ejecutados. El plan integración v7 prioriza corregir el generador para emparejar rescates con/sin N-grams antes de congelar.

## Escaneo ARS de interpretación: 11/11 revisados

| Riesgo | Evaluación |
|---|---|
| Simpson | Resultados por dataset y presupuesto; no se elige ganador a partir de una media mezclada |
| Falacia ecológica | Una media por política no garantiza calidad o costo en cada imagen/fold |
| Berkson/selección | Dos condiciones de desarrollo no representan el panel completo; el pool acotado limita generalización |
| Colisionador | No hay estimando causal; el escalado selecciona rutas y puede cambiar la composición de sus errores |
| Tasas base | Se conservan macro-F1, accuracy y etiquetas; no confundir ambas métricas |
| Regresión a la media | Ventajas puntuales pueden no repetirse; se requiere estabilidad fuera de estas condiciones |
| Supervivencia | Se registran inviabilidad y cobertura incompleta; se documenta la excedencia observada y los resultados desfavorables |
| Búsqueda múltiple | Cuatro presupuestos y dos reglas son desarrollo; sin p-valores ni selección retrospectiva de un único punto como prueba |
| Caminos analíticos | Se guardan configuración, candidatos y paths; el historial de exposición impide una etiqueta confirmatoria ciega |
| Correlación/causalidad | N-gram seleccionado no acredita que cause la ganancia; proyección no acredita ahorro físico |
| Causalidad inversa | No aplica una conclusión causal observacional; el presupuesto es una entrada fijada antes de estas corridas |
