# Qué podemos mostrar al profesor hoy

**Corte vigente posterior:** los tres controles Outex ya terminaron y pasaron auditoría. Para la reunión de las 22:00 y exposición de diez minutos, usar la [guía actualizada](REUNION_PROFESOR_CARLOS_OPTIMIZACION_2026-10-26.md) y el [registro de cierre de controles](CIERRE_CONTROLES_Y_MEDICION_2026-10-26.md). El informe conjunto ya incorpora GFS/Top-k Outex. Los estados parciales de este resumen se conservan como corte histórico. Los dos pilotos físicos CPU no pasaron todas las puertas de fidelidad y no publicaron latencias válidas.

Fecha: 26 de octubre de 2026. Resumen de trabajo, no declaración de cierre o superioridad general.

**Contexto actualizado de la reunión:** el profesor ya vio el ensamble, Top-k y concatenaciones de Carlos. La [guía de continuidad y resultados directos](REUNION_PROFESOR_CARLOS_OPTIMIZACION_2026-10-26.md) organiza qué se agregó desde entonces, la comparación numérica contra Carlos, un guion oral y los contraejemplos. Incluye un control fuerte que no debe omitirse: en FMD la cascada del pool emparejado anterior alcanza 0,977503/33,252 ms proyectados frente a 0,977489/35,689 del híbrido con miembros de Carlos. La incorporación de diversidad no tiene una ventaja demostrada frente a ese pool en este corte.

## 1. La pregunta de tesis ya no es «concatenar más»

Estudiamos cómo seleccionar bloques y adquirirlos condicionalmente bajo un presupuesto: **qué representaciones combinar, qué clasificadores conservar y para qué imágenes ejecutar el rescate**. Se comparan decisiones estáticas con una política adaptativa, contabilizando una sola vez los bloques compartidos.

La ruta funciona así: una base elegida dentro del entrenamiento predice primero; si su margen no supera el umbral seleccionado internamente, se adquieren los bloques adicionales y predice un ensamble reducido. No se impone ResNet como base. El trabajo de diversidad del proyecto está integrado como generador de candidatos, rescate y referencia permanente. La poda y la compuerta se evalúan por separado para no atribuir todo el ahorro al enrutamiento.

El aporte candidato es ese procedimiento implementado y su evaluación con controles comparables. No afirmamos que cada componente sea nuevo, que su combinación sea inédita en la literatura o que ya esté demostrada una superioridad general.

## 2. Qué evidencia está terminada

- Biblioteca de 22 bloques, 20.652 dimensiones nominales y seis datasets en el benchmark histórico: DTD, FMD, CUReT, Outex13Official1360, SoilOriginal y KTH-TIPS-2b. Los resultados estáticos incluyen SVM y ResMLP; el híbrido nuevo utiliza SVM.
- Híbrido, ensamble estático presupuestado y ablación permanente/condicional evaluados en desarrollo sobre FMD y Outex con tres semillas al incluir el piloto Outex/42. La réplica nueva de cinco condiciones está auditada e incorporada en el manuscrito de 67 páginas.
- Nuevos GFS y Top-k concatenados ya ajustados y auditados en **las tres semillas FMD**. Los controles Outex no terminaron por el límite de tiempo; no hay una comparación completa GFS/Top-k del híbrido en dos datasets todavía.

La cobertura del benchmark de seis datasets no debe atribuirse al híbrido. Las semillas comparten imágenes y no son dominios independientes.

## 3. Tabla nueva defendible: FMD, tres semillas

Cada semilla usa 800 imágenes de desarrollo, tres pliegues productores y tres internos; su test externo queda excluido. La tabla promedia el macro-F1 reunido por condición y su adquisición proyectada. **Los ms son parámetros del modelo de costos, no un cronometraje físico.** GFS/Top-k libres no están restringidos a B60. B60 se conserva como ejemplo del barrido, no como presupuesto de despliegue seleccionado de forma ciega.

| Método | Macro-F1 medio | Costo proyectado medio, ms |
| --- | ---: | ---: |
| Individual por ranking interno | 0,970011 | 11,680 |
| Completa-22 | 0,961704 | 1.706,420 |
| GFS sin presupuesto | 0,975410 | 197,414 |
| Top-k con tamaño heredado de GFS | 0,975444 | 210,751 |
| GFS restringido a B60 | 0,970436 | 30,902 |
| Prefijo factible seleccionado bajo B60 | 0,971255 | 18,120 |
| Ensamble estático seleccionado bajo B60 | 0,974600 | 41,888 |
| Híbrido de relevancia bajo B60 | 0,977489 | 35,689 |

Frente a GFS libre, el híbrido/B60 tiene una diferencia media de F1 de +0,002079 (aproximadamente +0,208 puntos porcentuales) y 81,92 % menos adquisición proyectada, calculado como razón de costos medios. Frente a Top-k con tamaño GFS, la diferencia es +0,002045 y la reducción proyectada es 83,07 %. Estas cifras describen FMD en este protocolo, no una aceleración física ni significancia poblacional.

La comparación tiene contraejemplos que deben mostrarse. Frente a GFS B60, el híbrido tiene mayor F1 pero también mayor costo medio. En FMD/42, el ensamble estático B60 obtiene 0,978772/35,078 ms, frente a 0,977506/38,282 ms del híbrido: lo supera en ambas medidas. En FMD/123, el estático tiene una ventaja pequeña de F1 con mayor costo. El promedio no implica que el híbrido domine cada semilla ni que la adaptación sea siempre necesaria.

Se guardan las 132 filas de políticas/condiciones FMD, las 44 medias y 42 diferencias emparejadas en `results/analysis/matched_concat_20261026/comparison_fmd`. No se ocultan las otras reglas ni los presupuestos 15/30/120. El [registro de controles](AVANCE_CONTROLES_CONCATENADOS_2026-10-26.md) detalla el protocolo y los estados.

## 4. El mecanismo está mejor identificado

En el piloto Outex/42, la poda reduce la adquisición proyectada un 69,76 % frente al ensamble permanente; la activación del mismo rescate podado reduce otro 51,72 % respecto de su ejecución permanente, con una pérdida adicional de F1 de 0,001251. Las reducciones son sucesivas, no sumables. Esto separa poda y compuerta, pero no es ahorro físico medido.

La réplica muestra que la compuerta no tiene un efecto predictivo uniforme: para relevancia/B60, el promedio FMD pasa de F1 0,974596 con el mismo rescate permanente a 0,977489 condicional; en las dos semillas nuevas Outex pasa de 0,912135 a 0,905991. Los miembros permanecen fijos en ese contraste; no se compara contra otro rescate reoptimizado. Ya no corresponde generalizar a toda la réplica la frase «la compuerta nunca mejora F1» del piloto original.

## 5. Qué sigue abierto y cómo decirlo

Los tres controles concatenados Outex originales llegaron al límite de 30 minutos y se terminaron sin predicciones finales. Es una limitación de ejecución, no evidencia de bajo F1. El autor autorizó un reintento exclusivo de esas condiciones en salidas nuevas, hasta 120 minutos cada una y sin cambiar el método. Outex/42 y Outex/123 ya iniciaron; Outex/2026 quedó en cola al corte. Se verificaron los 48 archivos del congelamiento anterior y se preservan los intentos originales. FMD no se repite. El panel no se considera completo hasta auditar la recuperación; véase la [enmienda operativa](ENMIENDA_REINTENTO_OUTEX_2026-10-26.md).

También faltan mediciones físicas de la ruta exacta, ampliar el híbrido a otros dominios, reconciliar KTH y resolver/delimitar fidelidad de representación CUReT/Soil. Los tiempos de la cascada histórica no validan físicamente este híbrido. Los valores p del benchmark estático no se transfieren a la propuesta nueva. No se declara equivalencia ni una mejora significativa del híbrido a partir de tres semillas de FMD.

## 6. Explicación oral de un minuto

> La tesis pasó de comparar concatenaciones a estudiar cómo adquirir información de forma selectiva. Seleccionamos dentro del entrenamiento una base, una compuerta y un rescate reducido del ensamble de diversidad, contando una sola vez los extractores compartidos. Ya separamos experimentalmente qué aporta podar y qué aporta activar el rescate por imagen.
>
> El híbrido está evaluado en desarrollo en FMD y Outex. Ahora completamos GFS y Top-k realmente ajustados en las mismas particiones para tres semillas FMD. El híbrido/B60 promedia F1 0,97749, frente a 0,97541 de GFS libre y 0,97544 de Top-k, con aproximadamente 82–83 % menos adquisición proyectada. No lo presentamos como una aceleración física ni como superioridad en todos los rivales: el estático gana en una semilla y GFS presupuestado utiliza todavía menos recursos a cambio de menor F1.
>
> Lo pendiente es terminar los controles de Outex, medir la ruta real y ampliar dominios. La contribución que estamos poniendo a prueba es la selección y adquisición conjunta bajo presupuesto, no simplemente añadir descriptores.

## 7. Material concreto para la reunión

Mostrar el diagrama del método y la sección de réplica del manuscrito vigente; después, la tabla FMD de este resumen y la comparación de poda/compuerta. Mantener a mano las pérdidas por semilla y el estado Outex. La pregunta útil para el profesor es si esta evidencia y el contraste pendiente delimitan adecuadamente el aporte de grado, y qué protocolo de evaluación final exige para considerarlo suficiente.

### Fuentes y alcance de verificación

`results/analysis/matched_concat_20261026/summary.json` registra 3/6 condiciones de concatenaciones auditadas y las tres interrupciones. `comparison_fmd/summary.json` liga por hashes las auditorías anteriores y nuevas, comprueba que las particiones productoras coincidan y conserva todas las variantes. La réplica del híbrido procede de `results/analysis/mesa_replication_20261026`; no se entrenaron modelos ni se añadieron nuevos tests inferenciales para preparar este resumen.

La suite de software actual registra **109 pruebas aprobadas en 45,87 s**, incluyendo reconstrucción del informe sin omitir las interrupciones o el resultado desfavorable. Es una comprobación de software y trazabilidad, no prueba de superioridad científica. El nuevo cuadro GFS/Top-k FMD se presenta en este resumen; todavía no está incorporado al PDF de 67 páginas.
