# Plan de cierre vigente — revisión de mesa R2, 25-10-2026

## Prioridad nueva del 28-10: comparación local F1 y ms

Régimen de tiempo aprobado: **latencia individual y F1 de esa misma ejecución**.
Se inició el piloto batch1 desde imágenes, con pesos residentes y cinco
métodos congelados sobre las 200 imágenes FMD/42/0 SVM. No se copia F1 del
archivo batch16, no se relaja la tolerancia y no se declara paridad archivada.
Véase `PROTOCOLO_BATCH1_F1_MS_2026-10-28.md`. Los resultados físicos permanecen
pendientes hasta finalizar y auditar las llamadas; contexto GPU compartido.

Primer avance ejecutado: [FMD/42/0, SVM y ResMLP](RESULTADO_PANEL_EXTERNO_LOCAL_2026-10-28.md),
cinco métodos por clasificador y 2.000 predicciones/compuertas reproducidas
desde cabezas sobre 200 imágenes. ResMLP completado con selección propia;
sus pérdidas frente a Top-4/tómbola se conservan. Preflight online detenido
en DeiT; CLS tampoco reconcilia el vector. Sin latencias publicadas ni medias
de dataset completas.

Actualización de extracción: se recuperó el pooling histórico de DeiT con
semilla 42 y se validó su adaptador local en ambas imágenes originales. El
preflight repetido pasó tres extractores y se detuvo en DenseNet121
(0,000112459 > 0,0001), sin modificar tolerancias. Véase el
[registro de recuperación y nuevo bloqueo](RESULTADO_DIAGNOSTICO_DEIT_SEED42_2026-10-28.md).

Continuación en ejecución: se iniciaron por separado SVM y ResMLP para FMD/42,
pliegues 1–4. El diagnóstico DenseNet reproduce los vectores archivados en los
lotes originales, no en batch1 ni desactivando TF32. Se consultó por el régimen
de la tabla; no se mezclará F1 archivado batch16 con supuesta latencia batch1.
Véase [diagnóstico DenseNet](RESULTADO_DIAGNOSTICO_DENSENET_2026-10-28.md).

FMD/SVM/42 ya completó cinco pliegues, auditoría y agregación. La media de F1
adaptativa es 0,977976, inferior a Top-4 (0,981922) y a ambos ensambles
(~0,978912), superior a Completa (0,965099). Se conserva esa pérdida y no se
infiere equivalencia o ahorro físico. [Resultado](RESULTADO_FMD_SEMILLA42_LOCAL_2026-10-28.md).

Por solicitud expresa, se pausa la ampliación de los papers y se prioriza
Completa-22, diversidad, tómbola, Top-4 y selección adaptativa con margen, en
los seis datasets y por separado SVM/ResMLP. Rige el
[plan de comparación local](PLAN_COMPARACION_LOCAL_F1_MS_2026-10-28.md).
Se reagregaron las 94 condiciones de referencia y verificaron 188 recetas;
esto reproduce las 48 medias archivadas, no sus predicciones. Las 60 celdas
de latencia y las 12 medias externas adaptativas nuevas siguen pendientes.
Los ensambles archivados parten de 21 candidatos sin N-grams, y sus recetas
no documentan las escalas que usa el código actualizado: reconciliar antes
de asociar su F1 con tiempos de una implementación distinta.

## Avance del 28-10: primer comparador de paper entrenado en desarrollo

Se completó y auditó un piloto **adaptado** BEiTv2 multicapa + MLP de Neshov en FMD/42: tres pliegues productores, 800 predicciones OOF, macro-F1 agrupado 0,945993 y exactitud 0,94625. Se reprodujeron exactamente logits/clases de las cabezas guardadas. [Protocolo previo](PROTOCOLO_PILOTO_NESHOV_FMD_2026-10-28.md) y [resultados, comparación emparejada y límites](RESULTADO_PILOTO_NESHOV_FMD_2026-10-28.md).

La adaptación no supera a los controles locales en esta condición. Nuestra ruta con margen también queda ligeramente por debajo del ensamble permanente en FMD/42; la ganancia media anterior de tres semillas no es uniforme. No se ha reproducido el protocolo original 10 × 10-fold, medido nueva latencia o completado la variante nueva en seis datasets. Se conservan los resultados anteriores y el manuscrito. Las 26 pruebas focalizadas pasaron; eso no sustituye la última suite completa histórica registrada más abajo.

## 1. Decisión y objetivo de tesis

**Estado: P0, control estático presupuestado, sensibilidad sin KTH y réplica en dos datasets incorporados al PDF; cierre experimental pendiente.** Este documento sustituye las prioridades operativas anteriores, conservándolas como historia. Evidencia y límites: [reauditoría inicial](AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md), [P0](CONTROL_PODA_COMPUERTA_OUTEX_2026-10-25.md), [incorporación P0](INCORPORACION_P0_TESIS_2026-10-25.md), [correcciones de la mesa R2](MESA_EVALUADORA_GRADO_R2_2026-10-25.md), [avance de réplica](AVANCE_REPLICA_MESA_2026-10-26.md) e [incorporación al manuscrito del 26-10](INCORPORACION_REPLICA_TESIS_2026-10-26.md).

La pregunta central es cómo **seleccionar, combinar y adquirir condicionalmente bloques de descriptores para mejorar el compromiso calidad–costo**. La hipótesis candidata es un rescate de pocos subconjuntos derivados del ensamble de diversidad, con base y compuerta seleccionadas en entrenamiento y costo de unión sin contar dos veces un bloque. P0 distingue poda y activación para rescates fijados. Ya se evaluó un ensamble estático optimizado bajo presupuesto dentro del pool de individuales y diversidad, con hasta tres miembros, y se replicó en FMD y semillas adicionales Outex. Ampliar familias a Top-k/GFS concatenados y evaluar otros dominios siguen pendientes.

No se promete superar a Completa en F1. Si el aporte es menor costo para una pérdida explícita, la tesis debe demostrar ese compromiso y sus límites. No se presume novedad por combinar piezas conocidas.

## 2. Qué está terminado y qué no

| Componente | Estado al corte |
| --- | --- |
| Biblioteca y datasets principales | 22 bloques, 20.652 dimensiones nominales; DTD, FMD, CUReT, Outex13Official1360, SoilOriginal y KTH-TIPS-2b. VisTex excluido |
| Benchmark estático | 470 filas verificadas, 47 condiciones por clasificador; post-hoc por clasificador recalculado |
| Cascada histórica | 27 predicciones archivadas y métricas recalculadas; KTH conserva reserva de reconciliación |
| Piloto físico histórico | Seis condiciones medidas; alertas CUReT/Soil no resueltas |
| Híbrido de diversidad | Piloto Outex/42 más cinco condiciones nuevas FMD/Outex, 3/3 pliegues; dos datasets con tres semillas al incluir el piloto, no seis dominios independientes |
| Código | 109 tests aprobados el 26-10 (45,87 s); incluyen informe FMD sin excluir timeouts, GFS/Top-k emparejados, prefijos inviables, auditor, congelamiento previo a evaluación y reconstrucción de tablas. El corte del PDF registró 97; fuentes experimentales preservadas |
| Manuscrito | Siete capítulos y anexos; PDF de 67 páginas con réplica completa, P0, sensibilidad KTH, control presupuestado y receta de reconstrucción |
| Ablación de compuerta P0 | Recálculo pareado completo de 12 configuraciones y 36 decisiones sobre predicciones OOF guardadas; ocho configuraciones con rescate, cuatro degeneradas a base sola |
| Control estático presupuestado | Cuatro presupuestos, doce selecciones internas congeladas antes de evaluación; nueve modelos reutilizados y nueve reajustados; doce presupuestos por pliegue cumplidos |
| Sensibilidad KTH | N=6 reproducido con SCI2S y N=5 recalculado, cuatro pruebas globales y diez pares Holm por clasificador; no reconcilia el protocolo original |
| Reproducción mínima | Dos tablas P0 byte-idénticas desde diez archivos en carpeta aislada; ZIP Soil v1 y 1.140 hashes de imagen comprobados |
| Réplicas | Cinco condiciones nuevas completas y auditadas: FMD semillas 42/123/2026 y Outex 123/2026. Los tres estáticos FMD se recuperaron una vez con autorización explícita en salidas nuevas, conservando decisiones idénticas y los fallos originales. Réplica mínima P1 atendida, no generalización a los seis datasets |
| Otras familias estáticas | **6/6 controles concatenados completos y auditados**, 180 decisiones: tres FMD originales y tres Outex recuperados con autorización. Informe conjunto de cinco condiciones nuevas: 220 filas / 88 medias, con Outex/42 histórico separado e inviabilidades explícitas. Los timeouts originales permanecen intactos |
| Física del híbrido | Ejecutor de cuatro rutas implementado. Fallos CPU preservados. Diagnóstico GPU autorizado de DINOv2-small: 4/4 vectores pasan con tolerancia intacta; error máximo 0,000000488013. Falta fidelidad completa de todos los bloques, clases y compuertas, y cronometraje en recursos documentados. Sin ahorro físico validado. Última suite completa: 114 pruebas en 52,89 s; dos tests nuevos focalizados del diagnóstico pasan |
| Entrega final, ZIP y sincronización remota | **No realizados en este corte** |

P0 documenta una validación desde archivos guardados, no un reentrenamiento. R2 añade nueve reajustes SVM del control estático desde embeddings; no se entrenaron extractores ni se inició un barrido GPU. P1–P5 mantienen tareas pendientes; los avances concretos de R2 no implican que esas fases estén cerradas.

**Actualización editorial histórica:** [registro del 25-10](REVISION_EDITORIAL_APLICADA_2026-10-25.md). Describe un corte anterior a P0 y R2, no el estado vigente de sus controles. La revisión local guiada por ARS no constituye certificación formal de cierre o novedad.

**Mejora integral anterior a P0:** [detalle de cambios](MEJORA_INTEGRAL_TESIS_2026-10-25.md). Precisó objetivo restringido, condición de ahorro, agregación de F1, transferencia del umbral y niveles OOF. Ese registro histórico no incluía la evidencia nueva de P0/R2.

## P0 — Separar poda de compuerta antes de ampliar el panel

**Pregunta:** ¿la adquisición condicional aporta frente a ejecutar siempre exactamente el mismo rescate podado?

**Estado: completado como recálculo de desarrollo Outex desde archivos guardados.** [Informe y tablas](CONTROL_PODA_COMPUERTA_OUTEX_2026-10-25.md). Se mantuvieron miembros, modelos, escalas y particiones; las 36 predicciones de rescate por pliegue/configuración coinciden con las puntuaciones originales. No se reentrenó ni se midió físicamente la ruta.

- Relevancia/B60: mismo rescate permanente 0,911993/110,421 ms frente a condicional 0,910742/53,316 ms; 51,72 % menos adquisición estimada con ΔF1 = −0,001251. Tres predicciones cambian (una mejora y dos perjuicios).
- Marginal/B60: las 680 predicciones coinciden; 0,905140 de F1 en ambas rutas y costo 97,282 → 55,365 ms (−43,09 %). No demuestra equivalencia poblacional.
- La compuerta no mejora F1 en ninguna de las ocho configuraciones con rescate; proporciona otro compromiso de costo. En marginal/B60 aumenta el número de llamadas a clasificadores pese a reducir adquisición. No atribuir toda la reducción de llamadas frente al ensamble completo al enrutamiento.
- La ruta forzada con base se informa separadamente del rescate permanente eficiente que omite la base. La comparación todavía no incluye un rescate estático reoptimizado bajo el mismo presupuesto.

La especificación original del control queda como registro de sus criterios:

1. Reutilizar los índices productores y decisiones del piloto Outex como control emparejado, sin sobrescribirlos. Registrar hashes de código, manifiesto, bloques, scores y selección.
2. Para cada fold, presupuesto y regla, evaluar: base sola; rescate podado siempre activo; base seguida del mismo rescate con compuerta; ensamble completo permanente; ensamble completo como rescate.
3. Mantener idénticos miembros, pesos, escalas y ajustes entre siempre activo y condicional. Si se añade una nueva selección estática optimizada, etiquetarla como **otro** control, no como la ablación exacta.
4. Fijar miembros, base y umbral sin usar las etiquetas de validación productora. Guardar scores internos y externos separados, índices, rutas y razones de inviabilidad.
5. Reportar macro-F1, exactitud, imágenes derivadas, errores corregidos/perjudicados, unión de bloques, llamadas únicas y costo proyectado ponderado por número de imágenes. Conservar todos los presupuestos 15/30/60/120, incluidos base sola y excedencias.

**Criterio de salida atendido en caché:** tabla completa y recálculo de la comparación exacta, con vistas por imagen y costos separados. En el piloto Outex/42, la compuerta conserva un efecto adicional sobre adquisición proyectada, pero no una ganancia predictiva ni ahorro físico demostrado. La réplica posterior FMD/Outex de P1 cambia el signo de F1 en algunas condiciones; no se generaliza a ella la ausencia de mejora predictiva del piloto.

**Artefactos guardados:** directorio de análisis integration_v9/p0_gate_ablation_outex22_20261025, con resumen de validación y hashes, tabla de doce configuraciones, tabla de 36 decisiones por pliegue y 8.160 vistas por imagen ligadas a las fuentes originales. No son 8.160 imágenes distintas. **Incorporación al PDF completada:** diseño, tabla de descomposición B60, barrido íntegro en anexo e interpretación de pérdidas de F1, llamadas y costo proyectado. P0 no sustituye P1–P4.

## P1 — Robustez y controles competitivos en desarrollo

**Avance R2 completado:** [protocolo del control estático](PROTOCOLO_CONTROL_ESTATICO_MESA_2026-10-25.md), definido antes de sus nuevas predicciones. Dentro de cada pool se enumeraron todos los ensambles de uno a tres miembros con costos factibles. En B60 se evaluaron 617 combinaciones por pliegue. Relevancia obtiene 0,910742/53,316 ms frente a 0,892923/44,831 ms del control. En B15/B120 el estático logra mayor F1 con mayor costo; no hay superioridad uniforme. La comparación no sustituye GFS concatenado ni demuestra optimalidad sobre toda la biblioteca.

La réplica mínima posterior a P0 en otro dataset y más de una semilla se completó el 26-10 con lista de condiciones fijada antes de ejecutar. Se mantuvieron tres folds productores/tres internos. La ampliación futura a otros dominios debe seguir fijando semillas y protocolo sin escogerlos por el resultado; si faltan grupos, justificar la alternativa y no mezclar estimandos.

**Réplica completada y auditada el 26-10:** [protocolo congelado](PROTOCOLO_REPLICA_MESA_2026-10-26.md) y [resultados completos, recuperación y límites](AVANCE_REPLICA_MESA_2026-10-26.md). Se mantienen 22 bloques, 3/3 pliegues y presupuestos 15/30/60/120. Outex semilla 42 continúa siendo la referencia histórica, no una sexta ejecución nueva. Los tests externos quedan excluidos. Las semillas modifican también particiones y generación de candidatos, por lo que esto no es una ablación aislada de inicialización. El costo es proyectado desde el perfil fijo, no una medición física en FMD. El usuario autorizó recuperar únicamente los controles estáticos fallidos de FMD; se guardaron en `static_recovery/`, sin modificar las fuentes congeladas ni el estado histórico de la cola. Auditoría: 5/5 condiciones, 60 selecciones estáticas, 180 decisiones de enrutamiento y 170 filas de métricas. Las doce decisiones por semilla recuperada son byte-idénticas a las del intento original. En B60, relevancia tiene mejor F1 medio y menor adquisición media que el estático en los dos datasets, pero FMD semilla 42 favorece al estático en ambas medidas. No hay dominancia uniforme ni ahorro físico nuevo demostrado. El PDF de 67 páginas ya incorpora esta réplica, con las tres reglas, los cuatro presupuestos y el contraste P0.

Controles mínimos con idéntica biblioteca y particiones:

**Avance de concatenaciones emparejadas (26-10):** [protocolo congelado](PROTOCOLO_GFS_TOPK_EMPAREJADO_2026-10-26.md), [registro de ejecución](AVANCE_CONTROLES_CONCATENADOS_2026-10-26.md) y [resumen para el profesor](RESUMEN_PARA_PROFESOR_2026-10-26.md). Se implementaron GFS libre y Top-k con tamaño GFS, más GFS restringido por costo y prefijo factible explícitamente diferenciados. Se mantienen tres pliegues productores/tres internos y treinta decisiones congeladas por condición. Las tres semillas FMD están auditadas; los tres controles Outex originales terminaron por límite temporal, no por un resultado predictivo. El reintento exclusivo de Outex fue autorizado e iniciado según la [enmienda operativa](ENMIENDA_REINTENTO_OUTEX_2026-10-26.md), con el mismo método y 7.200 segundos por condición. Se verificaron los 48 archivos del congelamiento original, sin cambios. Se conservan los fallos originales y el panel incompleto hasta auditar las salidas nuevas de `integration_v13/matched_concat_outex_retry_20261026`; FMD no se repite. No sustituir GFS/Top-k por Top-3/4/5 ni presentar un prefijo inviable como si cumpliera el presupuesto.

- Base de mayor F1 interno frente a selección sobre frontera de bases; no imponer ResNet como supuesto ganador.
- Poda por relevancia frente a ganancia/costo, sin cambiar el generador. Mantener relevancia porque es competitiva en Outex.
- Top-3/4/5 como referencias fijas y **Top-k/GFS realmente reajustados bajo el mismo protocolo**, no cifras oficiales de otra partición.
- Ensamble de diversidad y de relevancia de Carlos, misma receta y escalas congeladas; el ensamble de Carlos ya está integrado como componente/control, pero no sustituye estas comparaciones.
- Mismo rescate estático y condicional; base sola; Completa-22.
- Pool emparejado con/sin N-gramas si se mantiene una afirmación sobre color. Separar ruta fija de reselección.

**Criterio de salida:** estabilidad por dataset/semilla, curva calidad–costo íntegra y explicación de los fallos. No usar p-valores de folds dependientes como prueba poblacional. No descartar puntos negativos.

## P2 — Congelar algoritmo y reconciliar el panel

1. Resolver las discrepancias de procedencia KTH, incluyendo muestras físicas, entrenamiento, selección interna, transformaciones y cache de N-gramas. Verificar filas, no solo medias.
2. Congelar generador, regla de selección, presupuestos, desempates, política de base y familia de comparaciones. Escribir qué datos ya influyeron en el diseño.
3. Ejecutar, cuando corresponda, el mismo algoritmo en las 27 condiciones canónicas de seis datasets. Ese número no equivale a 27 datasets independientes.
4. Mantener fuentes históricas y nuevas en directorios separados; cada ejecución registra índices y procedencia suficientes. Los tests ya observados no pasan a ser ciegos por reutilizarlos con un algoritmo nuevo.

**Criterio de salida:** registro de cobertura sin celdas ambiguas, evaluación comparable de todos los controles y explicación de cualquier exclusión. Hasta entonces, el híbrido se describe como desarrollo Outex/ampliaciones efectivamente realizadas.

## P3 — Medir el híbrido de extremo a extremo

1. Diagnosticar fidelidad físico–caché de CUReT/Soil con extracción controlada: mismo archivo, checkpoint, preprocesamiento, capa, normalización y orden de muestra. No asumir una causa antes del diagnóstico.
2. Medir base, rescate podado permanente, híbrido, ensamble completo y controles cuya eficiencia se compare. Completa y GFS necesitan medición propia si la tesis afirma ventaja física frente a ellos.
3. Usar las mismas imágenes y orden pareado/aleatorizado, calentamiento, sincronización CUDA y repeticiones identificadas por imagen. Declarar hardware, carga, batch y régimen de modelos residentes o carga bajo demanda.
4. Incluir extracción efectiva de la unión, transferencias, clasificación, compuerta y agregación; no duplicar bloques compartidos. Registrar memoria y llamadas reales, además de medianas/colas de latencia y medias.
5. No contar repeticiones como imágenes nuevas. Distinguir latencia de cálculo con imagen decodificada de tiempo con entrada/salida y despliegue frío.

**Criterio de salida:** paridad de representación bajo criterio explícito, métricas físicas por ruta y reducción con denominador claro. Si no puede completarse, retirar la afirmación de ahorro físico del híbrido y conservar únicamente su costo proyectado.

## P4 — Análisis estadístico acorde al diseño

- **Sensibilidad R2 completada:** sin KTH, Friedman p=0,0342 (SVM) y 0,0199 (ResMLP). GFS–Individual con ResMLP mantiene p de Holm=0,0270; con SVM ningún par rechaza. Friedman alineado no rechaza en ninguno de los dos paneles. No se presenta la sensibilidad como réplica independiente ni se sustituye una media KTH para reconciliar su protocolo.
- Recalcular desde predicciones de variantes reconciliadas y con comparaciones fijadas antes de inspeccionar el panel nuevo.
- Mantener SVM y ResMLP separados; el híbrido actual es SVM, no atribuirle resultados de ResMLP.
- Para inferencia entre datasets, agregar dentro de cada dataset y declarar N efectivo. Las semillas/folds compartidos no son nuevos dominios independientes.
- Definir familia y corrección de comparaciones; separar post-hoc de rangos, Wilcoxon y contrastes de latencia. No reutilizar p-valores históricos para la propuesta nueva.
- Informar magnitudes y variabilidad, exposición previa y potencia limitada. No usar no significancia como equivalencia/no inferioridad sin un diseño y margen justificados.

**Criterio de salida:** tablas reproducibles con unidad de análisis, hipótesis, test, familia, ajustes y límites identificados. El carácter exploratorio del diseño actual se mantiene explícito.

## P5 — Cierre de escritura y entrega

1. Reconciliar literatura y contribución concreta; verificar fuentes primarias de cada afirmación de novedad o superioridad. La compilación sin citas indefinidas no sustituye ese control.
2. Actualizar tablas/figuras desde resultados finales, no manualmente para favorecer el método; sincronizar resumen, discusión, conclusión, guía y dossier.
3. Recompilar y revisar visualmente PDF final, comprobar referencias y rutas, pruebas pertinentes y hashes.
4. Crear un ZIP nuevo de Overleaf con fuentes, figuras y bibliografía necesarias, y comprobar que compile desde el ZIP. No reutilizar un paquete de fecha anterior como si incluyera esta revisión.
5. Revisar cambios locales del usuario y preparar commit/push únicamente dentro de la autorización vigente del usuario.

## 3. Decisión de cierre

La tesis puede cerrarse científicamente cuando la evidencia permita atribuir el aporte concreto, los controles sean comparables y las afirmaciones tengan el alcance realmente medido. No es obligatorio ganar en F1 a todos los rivales ni conseguir significancia en todos los datasets. Sí es obligatorio no confundir ahorro estimado con físico, poda con adaptación, ni un piloto seleccionado con validación general.

**Siguiente paso vigente:** resolver la fidelidad de extracción y medir físicamente las cuatro rutas congeladas, antes de elegir qué ampliar a otros dominios. La recuperación Outex ya completó y pasó auditoría 3/3; los seis controles concatenados están auditados. El [nuevo registro de cierre de controles](CIERRE_CONTROLES_Y_MEDICION_2026-10-26.md) sustituye el estado de ejecución anterior, sin alterar sus timeouts históricos. El informe conjunto compara FMD con tres semillas y Outex con dos nuevas, manteniendo el piloto Outex/42 separado. La cascada del pool anterior sigue siendo un rival fuerte; no se fuerza la elección del híbrido de Carlos. No se relaja la tolerancia de fidelidad para publicar tiempos ni se elige retrospectivamente una tolerancia de pérdida de F1. Portabilidad, escritura final y entrega siguen abiertas; no hay declaración institucional de cierre ni un “100 %”.
