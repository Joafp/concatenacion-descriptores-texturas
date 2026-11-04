# Validación pareada de poda y compuerta — Outex, 25-10-2026

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-10-25
- Verification Status: ANALYZED
- Version Label: p0_gate_ablation_outex22_v1
- Source: integration_v8/carlos_hybrid_outex22_20261021
- Overall Confidence: CAUTION
- Alcance: recálculo descriptivo desde predicciones y puntuaciones OOF guardadas, sin entrenamiento independiente, test oficial ni cronometraje.

Este bloque es un registro local compatible con el formato de validación; no acredita el pasaporte formal completo ni la certificación de ARS.

## Pregunta y controles

Se compara cada política archivada con la ejecución permanente del **mismo rescate**, sin reseleccionar miembros, cambiar multiplicidades, escalas, particiones o modelos. La política fue seleccionada dentro de su entrenamiento productor con compuerta; no es un rescate reoptimizado para uso estático.

Se mantienen cuatro vistas de cada configuración:

1. **Base sola:** predicción de la base seleccionada para esa política, no el mejor individual global.
2. **Mismo rescate permanente:** su predicción guardada para cada imagen; costo de la unión de sus bloques, sin calcular una base innecesaria.
3. **Ruta forzada:** idéntica predicción del rescate, reteniendo base y sobrecosto de política, y forzando rescate en todas las imágenes. Controla la activación manteniendo la infraestructura; se informa aparte por su trabajo redundante frente a rescate solo.
4. **Condicional:** predicción, margen, umbral, costos y llamadas archivados sin cambios.

Cuando el rescate seleccionado es vacío, las cuatro vistas conservan la base. Es un caso degenerado sin evidencia sobre compuerta; no se fabrica un ensamble permanente inexistente.

Todas las cifras corresponden a las mismas 680 imágenes de entrenamiento oficial, 68 clases balanceadas, semilla 42 y tres pliegues productores. Se conserva fuera el test oficial. Las medias de costo se ponderan por imagen; F1 se calcula sobre las 680 predicciones reunidas.

## Barrido completo

F1 es macro-F1; los costos son **adquisición proyectada en ms**, no latencia física. Las cuatro configuraciones sin rescate se conservan visibles.

| Rescate | B | F1 base | F1 permanente | F1 condicional | Costo permanente | Costo condicional | Caso |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Completo | 15 | 0,858056 | 0,858056 | 0,858056 | 12,220 | 12,220 | Base sola |
| Completo | 30 | 0,854129 | 0,854129 | 0,854129 | 20,485 | 20,485 | Base sola |
| Completo | 60 | 0,859848 | 0,914389 | 0,891759 | 365,196 | 57,839 | Rescate activo |
| Completo | 120 | 0,852780 | 0,914389 | 0,908603 | 365,196 | 104,660 | Rescate activo |
| Podado marginal | 15 | 0,858056 | 0,858056 | 0,858056 | 12,220 | 12,220 | Base sola |
| Podado marginal | 30 | 0,858056 | 0,905034 | 0,893488 | 98,344 | 25,394 | Rescate activo |
| Podado marginal | 60 | 0,820226 | 0,905140 | 0,905140 | 97,282 | 55,365 | Rescate activo |
| Podado marginal | 120 | 0,823601 | 0,913072 | 0,908781 | 251,028 | 84,018 | Rescate activo |
| Podado relevancia | 15 | 0,858056 | 0,858056 | 0,858056 | 12,220 | 12,220 | Base sola |
| Podado relevancia | 30 | 0,858056 | 0,905034 | 0,893488 | 98,344 | 25,394 | Rescate activo |
| Podado relevancia | 60 | 0,840378 | 0,911993 | 0,910742 | 110,421 | 53,316 | Rescate activo |
| Podado relevancia | 120 | 0,822836 | 0,913895 | 0,909396 | 229,836 | 78,938 | Rescate activo |

Las 12 configuraciones son dependientes y reutilizan imágenes. En ocho hay rescate; en siete de esas ocho la ejecución condicional tiene menor F1 que el mismo rescate permanente, y en marginal/B60 las predicciones coinciden exactamente. Ninguna de las ocho mejora F1 respecto de su rescate permanente. Esto describe este archivo de desarrollo, no una regla poblacional.

## Descomposición del punto relevancia/B60

| Política | Macro-F1 | Costo proyectado ms | Llamadas medias |
| --- | ---: | ---: | ---: |
| Ensamble completo permanente | 0,914389 | 365,196 | 10,665 |
| Mismo rescate podado permanente | 0,911993 | 110,421 | 1,668 |
| Mismo rescate, ruta forzada con base | 0,911993 | 110,871 | 2,668 |
| Ruta condicional | 0,910742 | 53,316 | 1,654 |

La reducción del costo proyectado se descompone numéricamente así:

- Poda del ensamble permanente: 365,196 → 110,421 ms (**69,76 %** menos), con ΔF1 = -0,002395.
- Activación condicional del mismo rescate: 110,421 → 53,316 ms (**51,72 %** menos), con ΔF1 = -0,001251 (−0,1251 puntos porcentuales).
- Reducción total respecto del ensamble completo: 85,40 %. Los dos porcentajes parciales se aplican sucesivamente y **no se suman**.

Frente a la ruta forzada con base, el ahorro proyectado es 51,91 %. La referencia permanente eficiente omite esa base y constituye el denominador principal.

La compuerta deriva 278 imágenes y da salida base a 402. Frente al rescate permanente, solo cambian tres predicciones: se corrige una y se perjudican dos. La exactitud pasa de 0,914706 a 0,913235. El saldo de un acierto menos no debe confundirse con Δmacro-F1.

La reducción de llamadas frente al **mismo rescate podado** es apenas 0,79 %. Por tanto, la gran reducción de llamadas frente al ensamble completo corresponde principalmente a la poda; el ahorro adicional atribuido a la compuerta es de adquisición estimada, no una disminución proporcional del número de clasificadores.

## Caso marginal/B60

Las 680 predicciones condicionales coinciden exactamente con las del mismo rescate permanente: macro-F1 0,905140 y exactitud 0,907353. El costo estimado baja de 97,282 a 55,365 ms (**43,09 %** menos). No es una demostración de equivalencia poblacional.

Las llamadas aumentan de 1,334 a 1,672 por imagen (**25,36 %**), porque la base también se ejecuta. Este caso demuestra por aritmética del perfil que menos adquisición proyectada puede coexistir con más evaluaciones de clasificadores.

Los rescates permanentes B60 de ambos criterios superan 60 ms proyectados, mientras sus variantes condicionales quedan por debajo en la media reunida. No se ha probado que superen a una selección estática alternativa optimizada para ese mismo presupuesto. La excedencia histórica de completo/B60 en un pliegue permanece intacta.

## Verificaciones y trazabilidad

- Se comprobaron 31 hashes de entradas y código ligados al metadata de origen.
- Se contrastaron las predicciones permanentes con las puntuaciones originales de sus miembros en las 36 decisiones, manteniendo pesos y multiplicidades.
- Se verificaron alineación de índices, disyunción entrenamiento/validación productores, compuerta, unión de bloques y costos guardados.
- Cada configuración conserva 680 imágenes únicas; las 8.160 filas derivadas son 12 vistas sobre esas mismas imágenes, no imágenes nuevas.
- [Resumen con hashes y resultados por pliegue](../../results/analysis/integration_v9/p0_gate_ablation_outex22_20261025/validation_summary.json).
- [Resultados completos](../../results/analysis/integration_v9/p0_gate_ablation_outex22_20261025/results.csv).
- [Resultados por pliegue](../../results/analysis/integration_v9/p0_gate_ablation_outex22_20261025/fold_results.csv).
- [Vistas por imagen](../../results/analysis/integration_v9/p0_gate_ablation_outex22_20261025/prediction_views.csv).

Las vistas por imagen conservan la predicción base, del rescate y condicional. La ruta forzada comparte la predicción del rescate y tiene una columna de costo propia; no necesita otra copia de las clases.

## Revisión de falacias: 11/11

| Tipo | Estado | Interpretación acotada |
| --- | --- | --- |
| 1. Simpson | NOTE | Se conservaron resultados por pliegue y reunidos; marginal/B60 coincide en cada pliegue y relevancia/B60 difiere solo en el pliegue 0. La F1 reunida no es la media de F1 de pliegues |
| 2. Ecológica | CAUTION | Un solo dataset y una semilla; no se extrapola a otros dominios ni se usan pliegues como datasets |
| 3. Berkson / selección | CAUTION | El rescate fue seleccionado para la ruta condicional; el control no es el mejor ensamble estático posible |
| 4. Colisionador | NOTE | No hay ajuste de covariables causal; los subconjuntos de bajo margen son seleccionados, por lo que se compara la cobertura completa |
| 5. Tasas base | NOTE | Se verificaron 68 clases con diez imágenes cada una; se informan F1 macro y exactitud |
| 6. Regresión a la media | NOTE | No se usa un diseño pre/post ni se atribuye causalidad a resultados extremos; B60 sigue siendo un punto de desarrollo observado |
| 7. Supervivencia | NOTE | Se conserva todo el barrido y los casos sin rescate; cobertura completa en las doce configuraciones |
| 8. Look-elsewhere | CAUTION | No se selecciona solo el punto favorable ni se ejecutan pruebas de significancia de ese punto |
| 9. Caminos analíticos | CAUTION | Diseño exploratorio y previamente observado; no se convierte en confirmatorio por añadir este control |
| 10. Correlación/causalidad | CAUTION | La ablación funcional fija modelos en este archivo; no estima un efecto causal poblacional ni prueba ahorro físico |
| 11. Causalidad inversa | NOTE | No se infiere una relación temporal de fenómenos observacionales; selección y evaluación se identifican por sus índices guardados |

## Reproducibilidad y límites

- Método: recálculo determinista desde predicciones guardadas y contraste con puntuaciones originales.
- Estado: **ANALYZED**, no entrenamiento independiente verificado.
- Pruebas inferenciales nuevas: **cero**. No se calculan p-valores ni se declara no inferioridad.
- No se lanzó un barrido GPU ni se evaluó el test oficial.
- No se modifica el manuscrito todavía: sus frases que declaran pendiente este control corresponden al corte anterior. La siguiente actualización editorial debe incorporar estos resultados y conservar réplica y medición física como pendientes.

