# Mesa evaluadora simulada — tesis de grado, ronda 1

Fecha: 25 de octubre de 2026. Estado: **REVISIÓN MAYOR antes de considerar cerrada esta versión para defensa**, como dictamen técnico simulado; no es una decisión de la universidad.

## 1. Qué se evaluó y qué significa el dictamen

El autor confirmó que se trata de una **tesis de grado**. Se revisaron los siete capítulos, resúmenes, anexos y tablas activas del manuscrito, y el control P0 posterior sobre poda y compuerta. El PDF conserva el corte editorial anterior a P0. Las observaciones distinguen problemas de ese PDF de evidencia ya disponible fuera de él.

La revisión aplica criterios generales de ingeniería y las orientaciones de ARS sobre soporte de afirmaciones, validez, coherencia y límites. No se proporcionó una rúbrica institucional. Estado: **NOT_CALIBRATED** y **criteria_binding_unavailable**.

Esta es una revisión formativa realizada por un asistente con cinco lentes críticos, no cinco revisores humanos ni cinco procesos de error independientes. **No se ejecutó el panel contractual reviewer_full de ARS, su sprint de cinco asientos o una certificación formal de aceptación.** No se simulan reportes independientes para aparentar consenso. Tampoco se hicieron nuevas búsquedas exhaustivas de originalidad, ensayos, entrenamiento o modificaciones al manuscrito.

El [snapshot de 32 archivos](../../results/analysis/mesa_grado_20261025_r1/snapshot.json) fija la versión examinada. El [registro de objeciones](../../results/analysis/mesa_grado_20261025_r1/issue_ledger.json) es una lista local de trabajo, no una adjudicación formal del autor ni permiso automático para editar cada superficie.

**Por qué no doy un “100 %”:** un porcentaje no acredita que una tesis sea correcta o que la mesa real la aprobará. El objetivo verificable será resolver las objeciones centrales con cambios o evidencia, o delimitar con el autor las afirmaciones que no se sostendrán. No se convertirán categorías de revisión en una nota.

## 2. Dictamen directo

El trabajo tiene material técnico suficiente para sostener una tesis de grado que valga la pena terminar: representación por bloques, selección, implementación de una ruta adaptativa, evaluación estática y un control funcional del enrutamiento. **No hace falta inventar una arquitectura fundacional ni ganar al estado del arte para que ese aporte sea legítimo a nivel de grado.**

Sin embargo, la versión todavía deja sin responder una pregunta decisiva: **¿la complejidad adaptativa compra una ventaja útil frente a una selección estática bien elegida bajo los mismos recursos?** El control P0 avanza mucho más que otra mejora de prosa, pero no responde por sí solo a esa comparación.

No recomendaría declarar el trabajo terminado por tener un PDF pulido, ecuaciones y muchos archivos de resultados. Recomendaría una revisión mayor, proporcionada a grado, centrada en comparación, evidencia y entrega reproducible. La falta de rúbrica impide transformar este dictamen en una conclusión sobre requisitos oficiales o probabilidad de aprobación.

## 3. Las cinco preguntas incómodas de la mesa

| Perspectiva | Pregunta de defensa |
| --- | --- |
| Contribución académica | ¿Cuál es el resultado de ingeniería que aporta la integración, más allá de ensamblar técnicas conocidas y reducir una suma de costos? |
| Metodología y estadística | ¿Qué comparación descarta que la misma biblioteca, seleccionada estáticamente bajo B, consiga un compromiso igual o mejor? |
| Reconocimiento de texturas | ¿Qué evidencia del algoritmo nuevo se transfiere fuera de Outex, y qué parte pertenece solo al benchmark histórico? |
| Eficiencia de sistemas | ¿Dónde están los tiempos de la ruta exacta, incluidos base, extractores, SVM, transferencias y residencia de modelos? |
| Abogado del diablo | Si el método marginal no es el mejor y parte del ahorro procede de la poda, ¿por qué es necesaria la compuerta y qué criterio vuelve útil su pérdida predictiva? |

Estas son lentes de una misma revisión, no votos independientes de un panel.

## 4. El argumento más fuerte en contra

Una mesa exigente podría plantear lo siguiente:

> El argumento central puede estar apoyándose en una comparación demasiado cómoda. Concatenar 22 bloques o ejecutar un ensamble permanente cuesta mucho en el perfil elegido; omitir parte de ese trabajo reduce automáticamente la suma proyectada. Eso no basta para demostrar que la política adaptativa sea la mejor utilización de un presupuesto. Los controles estáticos del piloto cuestan entre 177,300 y 1.706,420 ms, todos por encima del punto B60 utilizado como ejemplo. Falta un rival estático que también haya sido seleccionado para ese presupuesto.
>
> P0 muestra un efecto adicional del enrutamiento sobre la adquisición estimada, lo cual sí es evidencia relevante. Pero en relevancia/B60 la compuerta pierde algo de F1 frente al mismo rescate permanente; en marginal/B60 conserva las clases, aunque ejecuta más clasificadores por imagen. Por tanto, no deben confundirse poda, adquisición, número de llamadas y latencia real.
>
> La propuesta nueva sigue siendo un desarrollo de un dataset y una semilla. Los resultados de seis datasets corresponden a otros procedimientos y no amplían mágicamente esa cobertura. Hasta comparar alternativas con recursos compatibles y cerrar o delimitar la eficiencia práctica, la evidencia respalda un prototipo y un compromiso exploratorio, no una superioridad general del método.

**Adjudicación del argumento:** es una objeción importante y reparable; no prueba que el método sea malo ni que la compuerta sea inútil. P0 marginal/B60, con mismas 680 predicciones y 43,09 % menos adquisición proyectada que su rescate fijo, es evidencia contra la afirmación extrema de que “todo es poda”. Lo que continúa abierto es su competitividad frente a otros métodos factibles y su traducción a ejecución física.

## 5. Juicios por criterio, sin puntuación agregada

Fuente de los criterios: marco general de revisión ARS, aplicado a un trabajo empírico de ingeniería de grado, sin fuerza de reglamento institucional.

| Criterio | Juicio | Base y límite | Incidencia |
| --- | --- | --- | --- |
| Contribución definida | PARTLY_MEETS | Introducción y método identifican la integración; falta discriminar su utilidad frente a un control estático factible | Alta, J01/J06 |
| Rigor del diseño | PARTLY_MEETS | La selección y evaluación productoras se distinguen; siguen reservas KTH y falta comparación competitiva | Alta, J01/J05 |
| Suficiencia de evidencia | PARTLY_MEETS | Hay benchmark estático y P0; el híbrido sigue limitado a desarrollo Outex y costo proyectado | Alta, J02/J03 |
| Coherencia documental | PARTLY_MEETS | Los capítulos separan evaluaciones, pero declaran ausente un control que ya existe en el suplemento P0 | Alta, J04 |
| Claridad de escritura | MEETS | Método, ecuaciones y alcance se pueden seguir; no se identifica un defecto lingüístico fatal | No compensa los huecos experimentales |
| Integración de literatura | PARTLY_MEETS | Se reconocen antecedentes relevantes; la ventaja de la integración debe probarse, no derivarse del uso de componentes distintos | J01/J06; originalidad mundial NOT_ASSESSED |
| Reproducibilidad de la entrega | PARTLY_MEETS | Existen manifiestos y resultados; falta consolidar la receta y la identificación de datos para una entrega autónoma | Alta, J07 |
| Contención de afirmaciones | MEETS | El manuscrito distingue costo proyectado, no equivalencia y exploración | Mérito real; debe conservarse |

La originalidad frente a toda la literatura, el cumplimiento del reglamento local y la aprobación por un tribunal real quedan **NOT_ASSESSED**. No se reemplazan por una estimación intuitiva.

## 6. Objeciones y criterios de cierre

### J01. Comparación competitiva bajo recursos comparables

Severidad: **MAYOR**. Estado: **ABIERTO**.

Anclajes: `paper/generated_editorial/controles_hibrido.tex:8`; `paper/chapters/04_diseno_experimental.tex:67`; `paper/chapters/05_resultados.tex:128`.

**Objeción:** Los controles estáticos del piloto cuestan más que B60 y no incluyen selección estática optimizada bajo el mismo presupuesto. P0 aísla la compuerta respecto de un rescate fijo, pero no sustituye ese competidor.

**Corrección mínima:** Comparar con un control estático elegido dentro del entrenamiento con la misma biblioteca y presupuesto proyectado, usando las mismas particiones, y reportar la curva completa.

**Criterio de cierre:** Tabla y predicciones emparejadas con selección sin validación productora, mismo perfil y presupuestos; reconocer empates o derrotas sin cambiar la métrica a posteriori.

**Límite de la crítica:** Necesario para sostener ventaja frente a selección estática bajo presupuesto; no para afirmar solo que se implementó una política.

### J02. Validez de la eficiencia práctica

Severidad: **MAYOR_CONDICIONAL**. Estado: **ABIERTO**.

Anclajes: `paper/chapters/03_metodologia.tex:85`; `paper/chapters/04_diseno_experimental.tex:82`; `paper/chapters/A_especificaciones.tex:129`.

**Objeción:** La ruta híbrida no tiene cronometraje físico propio; el perfil omite la latencia completa de los clasificadores y el régimen de carga. Las mediciones históricas pertenecen a otra política.

**Corrección mínima:** Si se reclama eficiencia práctica, medir la ruta exacta y sus controles; si el alcance se limita al modelo proyectado, acordarlo expresamente y conservar esa limitación sin convertirla en validación física.

**Criterio de cierre:** O bien tiempos pareados y fidelidad de representación de la ruta nueva, con protocolo de residencia/carga; o bien alcance aprobado como estudio bajo modelo de adquisición, sin afirmaciones de aceleración real.

**Límite de la crítica:** No invalida la aritmética del costo proyectado; impide inferir ahorro físico del híbrido.

### J03. Estabilidad y alcance del resultado central

Severidad: **MAYOR**. Estado: **ABIERTO**.

Anclajes: `paper/chapters/01_introduccion.tex:28`; `paper/chapters/04_diseno_experimental.tex:27`; `paper/chapters/05_resultados.tex:91`; `paper/chapters/06_discusion.tex:49`.

**Objeción:** El algoritmo nuevo se evalúa en un dataset y una semilla. La cobertura histórica de seis datasets no valida la nueva integración ni permite estimar estabilidad del punto B60.

**Corrección mínima:** Fijar antes de nuevas corridas un protocolo de réplica con semillas adicionales y al menos un dominio contrastante si se mantiene una conclusión de método transferible; alternativamente acordar alcance de caso exploratorio.

**Criterio de cierre:** Resultados íntegros de la réplica con selección congelada y exposición previa declarada, o reformulación explícita y aprobada como caso único sin generalización; no exigir victoria ni significancia.

**Límite de la crítica:** La suficiencia institucional de un caso único no se decide sin rúbrica; la limitación es técnica, no un rechazo automático de una tesis de grado.

### J04. Correspondencia manuscrito-evidencia y atribución de componentes

Severidad: **MAYOR_DOCUMENTAL**. Estado: **ABIERTO**.

Anclajes: `paper/chapters/01_introduccion.tex:21`; `paper/chapters/04_diseno_experimental.tex:67`; `paper/chapters/05_resultados.tex:130`; `paper/chapters/05_resultados.tex:135`; `paper/chapters/07_conclusion.tex:10`; `paper/chapters/07_conclusion.tex:13`; `docs/fsc_tex/CONTROL_PODA_COMPUERTA_OUTEX_2026-10-25.md`.

**Objeción:** El PDF sigue declarando pendiente el control P0 ya disponible. Su comparación 10,665 a 1,654 llamadas no separa la reducción por poda de la compuerta.

**Corrección mínima:** Incorporar P0 y sincronizar resumen, diseño, resultados, discusión y conclusión; separar el 69,76 % de poda del 51,72 % adicional de adquisición y distinguir llamadas.

**Criterio de cierre:** Tabla de mismo rescate permanente/condicional y ruta forzada con denominadores claros; ninguna frase obsoleta de ausencia; marginal/B60 con más llamadas queda explícito.

**Límite de la crítica:** El control ya existe en caché y no requiere un nuevo entrenamiento para su incorporación.

### J05. Comparabilidad y alcance de la inferencia histórica

Severidad: **MAYOR**. Estado: **ABIERTO**.

Anclajes: `paper/chapters/04_diseno_experimental.tex:44`; `paper/chapters/04_diseno_experimental.tex:87`; `paper/chapters/05_resultados.tex:24`; `paper/chapters/B_procedencia.tex:9`.

**Objeción:** La inferencia estática N=6 mantiene una variante KTH con reserva de protocolo, mientras la cascada excluye KTH. La reserva se reconoce, pero falta mostrar su impacto sobre la conclusión inferencial.

**Corrección mínima:** Añadir sensibilidad excluyendo KTH o reconciliar el protocolo antes de sostener una conclusión principal; conservar el análisis archivado identificado.

**Criterio de cierre:** Todos los contrastes distinguen protocolo y unidad; se muestra si la conclusión cambia al excluir KTH, sin sustituir solo una media ni tratarlo como otra réplica.

**Límite de la crítica:** No se afirma que todos los resultados KTH sean falsos ni que incluir ese dataset viole por sí mismo independencia entre datasets.

### J06. Definición de utilidad del compromiso y selección de política

Severidad: **MAYOR_DE_ARGUMENTACION**. Estado: **ABIERTO**.

Anclajes: `paper/chapters/01_introduccion.tex:19`; `paper/chapters/03_metodologia.tex:87`; `paper/chapters/05_resultados.tex:128`; `paper/chapters/05_resultados.tex:132`.

**Objeción:** Ventaja mezcla costo y calidad sin un criterio operativo de aceptación. B60 es descriptivamente favorable y retrospectivo; B120 no mejora monotónicamente y hay una excedencia fuera de selección.

**Corrección mínima:** Definir qué se entiende por utilidad y factibilidad para el estudio; separar selección de presupuesto de evaluación, y fijar la regla antes de la réplica.

**Criterio de cierre:** Regla de comparación y selección explícita, curva completa, incumplimientos visibles y tratamiento predefinido; no introducir un margen de no inferioridad retroactivo ni exigir que el p sea significativo.

**Límite de la crítica:** Las curvas descriptivas actuales siguen siendo válidas; falta criterio para recomendar una política operativa.

### J07. Identificación de datos y entrega técnica reproducible

Severidad: **MAYOR_DE_REPRODUCIBILIDAD**. Estado: **ABIERTO**.

Anclajes: `paper/chapters/04_diseno_experimental.tex:42`; `paper/chapters/A_especificaciones.tex:12`; `paper/chapters/D_reproducibilidad.tex:4`; `paper/chapters/D_reproducibilidad.tex:6`.

**Objeción:** El manuscrito identifica SoilOriginal por tamaño y deduplicación, pero no su proveedor/versión en ese pasaje. El paquete reproducible requiere relacionar datos, extractores y artefactos con una receta ejecutable y una versión identificable, no solo un enlace general al repo.

**Corrección mínima:** Documentar fuente y versión del dataset, manifiesto y selección de originales; preparar una receta mínima para reconstruir una tabla del híbrido/P0 y detallar extracción/checkpoints, separando datos redistribuibles de no incluidos.

**Criterio de cierre:** Otra persona puede identificar las mismas imágenes y reproducir una tabla desde una entrega identificada; los pasos desde caché y desde RGB se distinguen. Se documentan dependencias y archivos faltantes sin inventar licencias.

**Límite de la crítica:** No se afirma que esos materiales no existan en algún archivo del repositorio; el punto es la entrega y su trazabilidad explícita.

### J08. Justificación e interpretación de la batería estadística

Severidad: **MENOR**. Estado: **ABIERTO**.

Anclajes: `paper/chapters/04_diseno_experimental.tex:87`; `paper/chapters/05_resultados.tex:22`; `paper/articulo/borrador_profesor/generated/classifier_global.tex:12`.

**Objeción:** La batería informa Friedman, Iman-Davenport, alineado y Quade, pero debe dejar claro cuál fundamenta la comparación principal y cómo leer su desacuerdo. Iman-Davenport no es una réplica independiente de evidencia.

**Corrección mínima:** Explicar elección del contraste principal y papel de las comprobaciones complementarias, manteniendo visibles los no rechazos del Friedman alineado.

**Criterio de cierre:** Una lectura permite distinguir prueba principal, familia Holm y sensibilidad sin contabilizar varias pruebas relacionadas como confirmaciones independientes.

**Límite de la crítica:** No se exige coincidencia de todos los tests ni se denuncia un p-valor aritméticamente incorrecto.


## 7. Qué NO rechazaría por deporte

- **No exigiría ganar en todos los datasets.** Un compromiso calidad–costo bien demostrado puede ser una contribución de grado.
- **No exigiría que toda diferencia sea significativa.** Una prueba con poco poder no debe convertirse en objetivo a manipular; importan magnitud, estabilidad y alcance.
- **No invalidaría la integración por utilizar métodos conocidos.** Su justificación y evaluación constituyen el punto de examen.
- **No diría que hay fuga del test oficial del híbrido sin evidencia.** El diseño declarado mantiene fuera ese test. La adaptación del proyecto a resultados previos es una reserva distinta y ya reconocida.
- **No pediría ciegamente las 27 condiciones o seis datasets para cerrar cualquier tesis de grado.** El panel debe corresponder a la afirmación: un caso exploratorio puede delimitarse; una conclusión transferible requiere evidencia adicional.
- **No presentaría p = 0,0191 como un error aritmético descubierto.** La cuestión aquí es alcance y sensibilidad del archivo, no una atribución cruzada ya corregida.
- **No confundiría coincidencia de rutas con identidad de representaciones.** La advertencia CUReT/Soil ya está bien formulada y debe preservarse.
- **No exigiría redistribuir datos o pesos contra sus condiciones de uso.** Sí identificar qué se entrega y cómo obtener lo restante.

## 8. Orden razonable para corregir después de esta revisión

1. **Cerrar la incoherencia documental J04 con evidencia existente.** Integrar P0, incluidos su denominador eficiente, la ruta forzada y los resultados desfavorables. No necesita entrenamiento.
2. **Acordar el criterio operativo J06 y el alcance de J02/J03.** No elegir retrospectivamente un margen para declarar éxito ni modificar el aporte sin decisión de los autores.
3. **Ejecutar el control competitivo J01 con selección interna y presupuesto común.** Si empata o gana el estático, documentarlo; eso modifica la conclusión, no autoriza ocultar el rival.
4. **Completar la evidencia que corresponda al alcance acordado.** Estabilidad/replicación de J03 y medición física de J02 si se defenderá eficiencia práctica.
5. **Cerrar J05/J07/J08.** Reconciliar o analizar sensibilidad, preparar la entrega reproducible y aclarar el papel de los contrastes.
6. **Reevaluar solo la versión modificada.** Cada respuesta debe indicar qué cambió, dónde, qué artefacto lo respalda y qué reserva permanece.

## 9. Protocolo de rondas y parada

Esta es la **ronda 1** y su dictamen queda conservado. No se ha modificado el manuscrito, recalculado un experimento ni lanzado una corrida científica durante esta revisión.

La ronda siguiente empieza cuando existan correcciones aprobadas o evidencia nueva que verificar. Cada objeción mantendrá su ID y criterio de cierre; una objeción nueva debe justificarse como tal, sin mover silenciosamente la meta. Un cambio de alcance requiere decisión explícita, no una aprobación fabricada por el asistente.

Si no hay evidencia adicional ni decisión de alcance, el estado se mantiene abierto y la revisión se detiene allí: repetir evaluaciones del mismo PDF no lo mejora. El cierre será un registro de objeciones centrales resueltas o delimitadas de forma explícita, **no un “100 %” inventado ni una promesa de aprobación institucional**.

