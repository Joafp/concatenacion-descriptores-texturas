# Reunión con el profesor: optimización del ensamble de Carlos

26 de octubre de 2026. Guía de apoyo para una exposición de diez minutos, sin declaración de cierre.

**Actualización para la reunión de las 22:00:** la exposición solicitada dura diez minutos y ya tiene una presentación editable de diez diapositivas. Outex/42, Outex/123 y Outex/2026 completaron y pasaron auditoría. El [registro nuevo](CIERRE_CONTROLES_Y_MEDICION_2026-10-26.md) documenta el informe conjunto y la fidelidad física pendiente. Las cifras nuevas de GFS/Top-k Outex se incorporan a continuación.

## Material Passport

- Origin Skill: academic-research-suite, guía local de argumentación sustentada en datos del proyecto.
- Origin Mode: preparación de comunicación de resultados, no revisión institucional ni pipeline formal.
- Verification Status: ANALYZED; hashes del informe FMD y de las auditorías Outex comprobados, 170 filas reconciliadas con sus registros.
- Version Label: reunion_carlos_optimizacion_v1.
- Alcance: desarrollo exploratorio; sin evaluación nueva del test externo, sin cronometraje físico del híbrido y sin pruebas inferenciales nuevas.

## 1. De dónde retomar la conversación

Según lo informado por los autores, el profesor ya vio el ensamble, Top-k y las concatenaciones de Carlos. La reunión debe mostrar qué se hizo después de proponer optimizar ese trabajo, no volver a presentar la concatenación como novedad.

**Apertura sugerida:**

> Partimos del ensamble que ya habíamos presentado. La pregunta fue si necesitamos ejecutar todos sus modelos y adquirir todos sus descriptores para cada imagen. Implementamos una selección de un rescate reducido y una compuerta que lo activa solo cuando la base tiene un margen bajo. Hoy traemos resultados de esa optimización, sus controles y los casos donde no mejora.

Los números siguientes corresponden a la **versión emparejada del método de Carlos implementada en este protocolo**. No se afirma que reproduzcan los números de su exposición anterior: no contamos aquí con esas diapositivas para cotejarlas.

## 2. Qué conservamos y qué agregamos

| Parte | Método de referencia | Optimización implementada |
| --- | --- | --- |
| Representación | Biblioteca común de 22 bloques; cada miembro concatena un subconjunto | Misma biblioteca, sin agregar un nuevo extractor |
| Candidatos de Carlos | Ensamble de diversidad: 15 sorteos de cuatro bloques; un SVM por subconjunto único | Se reutilizan sus miembros como candidatos de rescate |
| Combinación | Voto soft de scores normalizados; se conservan multiplicidades de sorteos | Rescate de hasta tres modelos únicos seleccionados internamente; promedio con igual peso |
| Ejecución | Ensamble permanente para todas las imágenes | Base individual y rescate condicional según el margen de sus dos mayores scores |
| Costo | Unión de bloques necesarios, sin cobros duplicados | Base más adquisición adicional solo en imágenes derivadas, según el perfil fijo |

También se conservan como controles las variantes de lotería y voto hard. Los 15 sorteos no implican necesariamente 15 modelos distintos. Los scores normalizados no son probabilidades calibradas.

### Diagrama para explicar la inferencia

```text
Imagen → descriptor base → SVM base → margen entre los dos mayores scores
                                      │
                         ┌────────────┴─────────────┐
                         │                          │
                   margen ≥ umbral            margen < umbral
                         │                          │
                   aceptar la base        adquirir bloques adicionales
                                          de los miembros seleccionados
                                                    │
                                          hasta tres SVM de rescate
                                                    │
                                          promedio de scores → clase
```

La clase del rescate reemplaza a la de la base; no se añade otro voto base. Un bloque compartido se cuenta una sola vez. La base no es una ResNet impuesta: se selecciona dentro del entrenamiento. Base, rescate y umbral se eligen con scores OOF internos antes de evaluar cada pliegue productor. En el experimento actual se usan características y scores guardados; el diagrama expresa la ruta a implementar y cronometrar físicamente, no una medición online ya realizada.

## 3. Resultado principal: comparación directa con Carlos

Punto ilustrativo: regla de relevancia con presupuesto interno B60. Se conservaron también B15/B30/B120 y las otras reglas; B60 no se presenta como ganador elegido de forma ciega. F1 se calcula reuniendo predicciones productoras por condición y luego se promedia entre semillas del mismo dataset.

**Todos los costos de esta guía son adquisición proyectada en ms por imagen, no latencia física medida.** Tampoco incluyen toda la latencia de clasificadores, carga o residencia en memoria. El presupuesto limita la media interna de selección, no cada imagen ni garantiza la media de una muestra nueva.

| Dataset y semillas | Ensamble de diversidad de Carlos, soft: F1 / costo | Híbrido podado-condicional B60: F1 / costo | Diferencia de F1, puntos porcentuales | Reducción proyectada |
| --- | ---: | ---: | ---: | ---: |
| FMD: 42, 123, 2026 | 0,973809 / 364,712 | 0,977489 / 35,689 | +0,368 | 90,21 % |
| Outex: 123, 2026 | 0,909840 / 370,575 | 0,905991 / 40,750 | −0,385 | 89,00 % |

**Qué decir:** en FMD mejora el F1 medio frente a esa referencia mientras reduce la adquisición proyectada. En Outex intercambia una pérdida observada de F1 por menor adquisición. No afirmar que supera a Carlos en todos los datasets, que la pérdida es estadísticamente despreciable ni que ya corre diez veces más rápido.

Outex/42 es un piloto histórico separado: diversidad permanente 0,914389/365,196 frente a híbrido B60 0,910742/53,316. No está incluido silenciosamente en la media de las dos semillas nuevas de la tabla. Las semillas reutilizan imágenes y no cuentan como datasets independientes. FMD utiliza 800 imágenes de desarrollo por condición y Outex 680; sus tests externos se excluyen.

## 4. ¿Y frente a Top-k, GFS y otras optimizaciones?

En FMD ya están completos los controles concatenados sobre las mismas particiones. Media de las tres semillas:

| Método | Macro-F1 | Adquisición proyectada, ms |
| --- | ---: | ---: |
| Individual por ranking interno | 0,970011 | 11,680 |
| Concatenación completa de 22 bloques | 0,961704 | 1.706,420 |
| Carlos, diversidad soft permanente | 0,973809 | 364,712 |
| Carlos, lotería hard permanente | 0,976688 | 363,999 |
| Top-4 fijo concatenado | 0,977535 | 248,962 |
| Top-k con k heredado de GFS | 0,975444 | 210,751 |
| GFS concatenado sin presupuesto | 0,975410 | 197,414 |
| GFS concatenado bajo B60 | 0,970436 | 30,902 |
| Ensamble estático seleccionado bajo B60 | 0,974600 | 41,888 |
| Cascada sobre el pool emparejado anterior, relevancia/B60 | 0,977503 | 33,252 |
| Híbrido con miembros de Carlos, relevancia/B60 | 0,977489 | 35,689 |

Lecturas necesarias:

- Frente a GFS libre y Top-k con tamaño GFS, el híbrido tiene mayor F1 medio y 81,92 % / 83,07 % menos adquisición proyectada en FMD. No son ahorros físicos.
- Frente al estático B60, mejora el promedio, pero **FMD/42 favorece al estático en ambas medidas**: 0,978772/35,078 frente a 0,977506/38,282. En FMD/123 el estático también tiene un F1 ligeramente mayor, con mayor costo.
- GFS B60 consume menos que el híbrido a cambio de menor F1. No hay dominancia del híbrido frente a ese rival.
- Top-4 fijo tiene un F1 medio ligeramente mayor. Top-4 no es el Top-k con k heredado de GFS.
- **El híbrido con Carlos no mejora la cascada del pool anterior en FMD:** esta tiene F1 apenas mayor y menor costo medio. Ambas usan selección de base, rescate y compuerta; cambia el pool candidato. No se debe ocultar ese control ni atribuir una ventaja ya demostrada a incorporar diversidad.

En las dos semillas nuevas de Outex, el control del pool anterior obtiene 0,911895/42,845 frente a 0,905991/40,750 del híbrido con Carlos: mayor F1 por un costo algo mayor. El ensamble estático B60 obtiene 0,889152/49,047. GFS libre ya auditado obtiene 0,908080/274,047; Top-k con tamaño GFS, 0,897153/318,805; GFS B60, 0,878574/55,426. Frente a GFS libre, el híbrido pierde F1 y reduce adquisición proyectada; frente a Top-k tiene mayor F1 y menor adquisición. El panel concatenado está auditado en las seis condiciones. La media Outex de esta comparación usa solo 123/2026, conservando 42 como piloto histórico separado.

Se mantienen las 44 variantes FMD en el archivo de evidencia; la tabla de reunión es una selección explicativa que incluye rivales fuertes y resultados adversos, no un ranking que certifique un método ganador.

## 5. ¿El ahorro viene de la poda o de la compuerta?

Mostrar la ablación del piloto Outex/42 por separado:

| Etapa | Macro-F1 | Adquisición proyectada, ms |
| --- | ---: | ---: |
| Ensamble completo permanente de Carlos | 0,914389 | 365,196 |
| Mismo rescate podado, permanente | 0,911993 | 110,421 |
| Mismo rescate podado, condicional | 0,910742 | 53,316 |

La poda reduce el costo proyectado 69,76 %; activar condicionalmente ese mismo rescate reduce otro 51,72 % respecto del rescate podado permanente, con una pérdida adicional de F1 de 0,001251. Total: 85,40 % respecto del ensamble completo. Las reducciones son sucesivas, no sumables.

Este contraste fija los miembros para aislar funcionalmente la compuerta, pero no compara contra el mejor estático posible. Por eso también ajustamos el estático presupuestado de la sección anterior. La compuerta no mejora siempre el F1: en la réplica cambia su efecto entre FMD y Outex.

## 6. Respuestas cortas para la reunión

**¿Usaron realmente el método de Carlos?** Sí: el control utiliza sus funciones de generación por diversidad y sus miembros forman el pool de rescate del híbrido. No es solamente un cambio de nombre de Top-k.

**¿Ya lo mejoraron?** Observamos una reducción fuerte de adquisición proyectada; el efecto sobre F1 depende del dataset y de la referencia. FMD mejora frente al ensamble permanente de diversidad; Outex pierde F1. La incorporación de ese pool no ha demostrado superar al pool anterior.

**¿La mejora es significativa?** No ejecutamos pruebas inferenciales nuevas para este contraste. Los p-valores del benchmark estático no se transfieren al híbrido. Tres semillas FMD no son tres datasets independientes.

**¿Son resultados del test oficial?** No. Son resultados exploratorios de desarrollo con evaluación productora y selección interna separadas. No se elige la política mirando las etiquetas productoras, pero los benchmarks ya eran conocidos: no es una prueba confirmatoria ciega.

**¿Ya hay ahorro real de tiempo?** No hay una medición validada de esta ruta exacta incorporada en la presentación. El nuevo ejecutor físico tiene puertas de fidelidad; los pilotos CPU FMD/42 y Outex/123 se detuvieron por diferencias numéricas de DINOv2-small superiores a su tolerancia, sin publicar tiempos válidos. La latencia de una cascada histórica distinta no valida esta versión.

**¿Se probó en seis datasets?** El benchmark histórico tiene seis; este híbrido está evaluado en FMD y Outex. No atribuirle la cobertura del benchmark. Los controles concatenados ya están auditados en tres semillas de cada uno de esos dos datasets, no en seis dominios distintos.

**¿Cuál elegiríamos hoy?** No hay evidencia para declarar ganador universal. La cascada del pool anterior sigue siendo un rival muy fuerte; el híbrido de Carlos es una alternativa de optimización en evaluación. La elección final debe basarse en el compromiso calidad–costo y medición física, no en la complejidad del nombre ni en una fila favorable.

## 7. Guion oral de unos 90 segundos

> La última vez presentamos el ensamble y las concatenaciones de Carlos. Mi siguiente trabajo fue intentar evitar su ejecución completa para cada imagen. Implementamos una base elegida en entrenamiento y un rescate de hasta tres modelos derivados de su ensamble, que solo se activa cuando el margen de la base es bajo. Los bloques compartidos se cuentan una vez.
>
> En FMD, sobre tres semillas de desarrollo, el ensamble de diversidad permanente tiene F1 medio 0,97381 y el híbrido 0,97749. La adquisición proyectada baja de 364,71 a 35,69: cerca de 90 % menos. En las dos semillas nuevas de Outex baja de 370,58 a 40,75, pero el F1 cae de 0,90984 a 0,90599. Por eso no decimos que siempre mejore la precisión: estamos cuantificando un compromiso.
>
> Para no atribuir todo a la cascada, separamos poda y activación y ajustamos un ensamble estático con presupuesto, además de GFS y Top-k emparejados en FMD. También encontramos un límite importante: nuestra cascada con el pool anterior tiene un F1 apenas mayor y menor costo que el híbrido con Carlos en FMD. No damos por demostrado que incorporar diversidad sea la mejor opción.
>
> Lo que traemos hoy es una optimización implementada y auditada con resultados y contraejemplos. Los controles concatenados Outex ya terminaron: frente a GFS libre perdemos algo de F1 por menor adquisición proyectada, mientras frente a Top-k mejoramos ambas medidas. Falta resolver la fidelidad y medir el tiempo físico de esta ruta, y después ampliar dominios antes de cerrar la elección final.

## 8. Orden de lo que conviene mostrar

1. Abrir con la continuidad respecto del ensamble ya presentado.
2. Explicar el diagrama y las dos decisiones agregadas: qué modelos conservar y cuándo ejecutarlos.
3. Mostrar la comparación directa con Carlos, tanto FMD como Outex.
4. Mostrar los rivales de FMD y el control del pool anterior; no esconder el resultado adverso.
5. Separar poda y compuerta con la ablación de Outex/42.
6. Cerrar con los controles pendientes y pedir feedback sobre la tolerancia de pérdida relevante para la aplicación. No fijarla retrospectivamente para declarar éxito en estas mismas corridas.

## 9. Fuentes y alcance

- [Evidencia numérica de esta reunión](../../results/analysis/reunion_profesor_20261026/evidence.json): medias completas, diferencias y hashes; 170 filas de la réplica reconciliadas con sus registros.
- [Informe FMD, 44 medias](../../results/analysis/matched_concat_20261026/comparison_fmd/dataset_means.csv) y [procedencia](../../results/analysis/matched_concat_20261026/comparison_fmd/summary.json).
- [Informe conjunto actualizado, 88 medias](../../results/analysis/matched_concat_panel_20261026/dataset_means.csv) y [procedencia de la recuperación](../../results/analysis/matched_concat_panel_20261026/summary.json). El archivo de evidencia de reunión anterior conserva su corte previo a Outex, no se lo reescribe como si incluyera estos controles.
- [Réplica FMD/Outex](AVANCE_REPLICA_MESA_2026-10-26.md) y [auditoría](../../results/analysis/mesa_replication_20261026/summary.json).
- [Ablación de poda y compuerta](CONTROL_PODA_COMPUERTA_OUTEX_2026-10-25.md).
- [Explicación técnica de extracción, Top-k, ensamble y cascada](GUIA_METODO_FEATURES_TOPK_ENSAMBLE_CASCADA.md).
- [Reintento autorizado de Outex](ENMIENDA_REINTENTO_OUTEX_2026-10-26.md). Su estado cambia con el tiempo y debe comprobarse antes de la reunión.

No se modificó el manuscrito ni se lanzaron entrenamientos para preparar esta guía. No se certifica novedad bibliográfica ni aprobación del profesor. Los datos de controles nuevos FMD se muestran aquí, no se presentan como si ya estuvieran incorporados al PDF.
