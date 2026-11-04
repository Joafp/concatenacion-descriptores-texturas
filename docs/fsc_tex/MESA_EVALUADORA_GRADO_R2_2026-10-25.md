# Mesa simulada de grado: correcciones y comprobación de ronda 2

Fecha: 25 de octubre de 2026. Se continúa por solicitud del autor la revisión y corrección posterior a P0. Este registro comprueba cambios concretos; no representa una mesa institucional ni un panel independiente de cinco personas. Se utilizaron criterios de ARS de manera local y explícita, sin fabricar adjudicaciones exactas, pasaportes o certificación contractual. La rúbrica institucional sigue sin proporcionarse y el dictamen no se transforma en porcentaje.

## 1. Qué se hizo realmente

1. Se implementó y evaluó un control estático seleccionado dentro de cada entrenamiento productor, bajo los mismos cuatro presupuestos del híbrido. Las doce decisiones quedaron guardadas antes de las nuevas predicciones; se reutilizaron nueve modelos y se reajustaron nueve SVM, sin entrenar extractores ni usar test oficial.
2. Se recalcularon en SCI2S los análisis estáticos de seis y cinco datasets, excluyendo KTH en la sensibilidad. Se reprodujo exactamente el análisis Java original de N=6 y se comprobaron Friedman y Holm con Python. Se conservaron originales y resultados nuevos por separado.
3. Se identificó SoilOriginal con proveedor, versión, archivo y manifiesto. Se verificaron el ZIP v1 y los hashes de las 1.140 imágenes seleccionadas, siete clases y 962 grupos.
4. Las dos tablas P0 se reconstruyeron byte a byte en una carpeta aislada con diez archivos. Se documentaron entorno, entradas, límites desde caché y pendientes desde RGB.
5. Se modificaron resúmenes, método, diseño, resultados, discusión, conclusiones, anexos, README y plan. Se preservaron los resultados históricos y P0.

## 2. Control estático competitivo, sin ocultar derrotas

Se fijó el [protocolo](PROTOCOLO_CONTROL_ESTATICO_MESA_2026-10-25.md) antes de calcular sus predicciones, pero después de conocer el piloto: **no es una preinscripción ciega**. Se enumeran ensambles de hasta tres miembros únicos del pool de 22 individuales y modelos del ensamble de diversidad; no todas las concatenaciones o ponderaciones de la biblioteca.

| Presupuesto | F1 estático | F1 relevancia | Costo estático, ms | Costo relevancia, ms |
| --- | ---: | ---: | ---: | ---: |
| 15 | 0,859690 | 0,858056 | 13,752 | 12,220 |
| 30 | 0,861264 | 0,893488 | 28,463 | 25,394 |
| 60 | 0,892923 | 0,910742 | 44,831 | 53,316 |
| 120 | 0,909612 | 0,909396 | 103,040 | 78,938 |

Todos los costos son adquisición **proyectada**, no latencia física. En B30 relevancia domina descriptivamente al control observado. En B60 mejora F1 dentro del mismo presupuesto, pero también tiene mayor costo: no se presentan como puntos de idéntico tiempo. En B15/B120, el estático tiene mayor F1 y mayor costo. No hay superioridad uniforme.

Los pools tienen 31, 33 y 34 modelos; B60 permite 617 combinaciones por pliegue y B120 entre 1.287 y 1.701. Las doce decisiones y sus predicciones se reprodujeron desde scores guardados, comprobando uniones y presupuestos. El control satisface las doce restricciones por pliegue. Los tres pliegues no son tres datasets ni se utilizan para obtener significancia confirmatoria.

Fuentes nuevas: `results/exploratory/integration_v10/static_budget_outex22_20261025/`, análisis emparejado en `results/analysis/mesa_grado_20261025_r2/static_control/` y tabla `paper/generated_mesa_r2/estatico_presupuesto.tex`.

## 3. Sensibilidad de la inferencia estática

Sin KTH, Friedman registra p=0,0342 con SVM y p=0,0199 con ResMLP. GFS–Individual con ResMLP conserva p de Holm=0,0270, frente a 0,0191 con seis datasets. En SVM ningún par rechaza tras Holm: Top-k–Individual 0,0511, Completa–Individual 0,0839 y GFS–Individual 0,2225.

Friedman alineado no rechaza en ninguna versión; sin KTH registra 0,3901 y 0,3955. Quade rechaza a nivel nominal. El texto identifica Friedman como prueba principal del análisis histórico; Iman–Davenport es su transformación, no una réplica independiente, y alineado/Quade son comprobaciones complementarias. No se elige una prueba porque produzca el resultado favorable ni se declara unanimidad de la batería.

La sensibilidad conserva todas las familias de diez pares por clasificador. No reemplaza una media KTH por otra ni corrige automáticamente su selección interna. Fuentes y salidas Java: `results/analysis/mesa_grado_20261025_r2/kth_sensitivity/`.

## 4. Disposición de las ocho objeciones originales

| ID | Estado después de los cambios | Evidencia o reserva |
| --- | --- | --- |
| J01 | Atendida para el control acotado; alcance limitado | Rival estático presupuestado con selección interna y predicciones emparejadas. No se extiende a optimalidad global, GFS ni todas las ponderaciones |
| J02 | Abierta para eficiencia física | Se mantiene el alcance proyectado sin afirmar aceleración real. Falta medir la ruta nueva y sus controles con fidelidad de representación |
| J03 | Abierta para generalización | El método nuevo, P0 y el rival estático siguen en Outex/una semilla. La cobertura histórica no se transfiere al híbrido |
| J04 | Incorporación comprobada | P0 ya está en diseño, tablas, resultados y conclusiones; se distinguen poda, compuerta, llamadas y pérdidas predictivas |
| J05 | Sensibilidad atendida; reconciliación KTH abierta | N=6 reproducido y N=5 calculado con toda la batería y Holm. No se afirma que KTH haya sido corregido |
| J06 | Criterio de comparación explicitado; despliegue no decidido | Maximizar F1 interno por presupuesto; informar factibilidad y ambas magnitudes, sin margen retrospectivo de no inferioridad. No se recomienda un presupuesto operativo |
| J07 | Identidad y reconstrucción mínima atendidas; entrega completa parcial | Fuente Soil v1 e imágenes verificadas y tablas P0 byte-idénticas. Quedan portabilidad de corridas completas, publicación de materiales y reproducción RGB independiente |
| J08 | Aclaración atendida | Se distingue prueba principal, transformación Iman–Davenport, complementarias y no rechazos de alineado |

Este es un registro local de correcciones y evidencia, no una adjudicación formal del autor ni aprobación institucional. La ronda 1 permanece intacta como referencia histórica. No se asigna una nota y no se cierran problemas experimentales mediante prosa.

## 5. Revisión de falacias y alcance: 11/11

| Riesgo | Comprobación acotada |
| --- | --- |
| Simpson | SVM y ResMLP permanecen separados; sensibilidad N=5 y N=6 visible, sin promediar clasificadores |
| Ecológica | Se distingue inferencia entre datasets de observaciones por imagen en un piloto |
| Selección/Berkson | El pool está adaptado al entrenamiento productor y el nuevo control se diseñó tras conocer resultados previos; no se afirma optimalidad general |
| Colisionador | No se introducen ajustes de covariables ni se usa solo el subconjunto de bajo margen como población de evaluación |
| Tasas base | Cobertura de 680 imágenes balanceadas, misma etiqueta por índice; se conservan F1 macro y exactitud |
| Regresión a la media | No se interpreta B60 observado como mejora prospectiva garantizada ni se ofrece una comparación pre/post causal |
| Supervivencia | Se conservan los cuatro presupuestos, todas las variantes, casos base y derrota predictiva en B15/B120 |
| Look-elsewhere | No se añaden p-valores del punto favorable del híbrido. Holm sigue corrigiendo diez pares por clasificador |
| Caminos analíticos | Diseño exploratorio y posterior exposición declarados. Regla del control guardada antes de sus predicciones; no se cambia tras observarlas |
| Correlación/causalidad | P0 atribuye cambios funcionales en modelos fijados, no un efecto causal poblacional ni ahorro físico medido |
| Causalidad inversa | No se propone una explicación causal temporal de observaciones; se describe un algoritmo y su evaluación delimitada |

Esta lista documenta comprobaciones y límites; no convierte el estudio en una prueba confirmatoria ni acredita ausencia exhaustiva de sesgos.

## 6. Verificación y entrega

- Suite: **83/83 pruebas aprobadas**, incluidas tres nuevas del selector estático.
- Documento: **63 páginas**, sin errores, referencias indefinidas ni cajas overfull/underfull en la compilación final.
- Tablas nuevas: comparación estática bajo presupuesto, cuatro pruebas globales N=6/N=5 y todos los pares Holm N=5, con procedencia separada de los archivos históricos.
- [Receta mínima de reproducción](REPRODUCCION_MINIMA_MESA_2026-10-25.md): distingue reconstrucción desde caché de extracción desde RGB y enumera los archivos no presumidos públicos.
- Respaldo previo: `paper/revision_mesa_r2_20261025_before.tar.gz`. No se hizo commit, push, paquete Overleaf ni extracción GPU.

El siguiente trabajo sustantivo es la réplica predefinida en otro dominio/semillas y la validación física del híbrido. La versión está mejor respaldada que la de ronda 1, pero los límites J02/J03 siguen abiertos. No procede prometer “100 %” ni una aprobación real sin la mesa institucional.
