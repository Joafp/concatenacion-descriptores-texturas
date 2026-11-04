# Auditoría editorial: qué debe contar la tesis y cómo organizarlo

Fecha: 25-10-2026. Documento de recomendaciones; **no se aplicaron cambios al manuscrito ni al PDF en esta pasada**.

## Alcance y marco ARS

Se leyeron `paper/tesis.tex`, los seis capítulos activos, la auditoría técnica del corte anterior y código/metadatos puntuales del ensamble para distinguir detalle omitido de trabajo todavía no realizado. ARS se utilizó para arquitectura del documento, correspondencia pregunta–evidencia y diagnóstico de escritura. Esta es una revisión interna en el mismo contexto que produjo la última revisión: no es revisión independiente, panel de cinco revisores, certificación de novedad ni dictamen de una revista.

`criteria_binding_unavailable`: no se aportó un reglamento institucional o destino editorial confirmado para evaluar conformidad. Las guías consultadas orientan la comunicación científica; no sustituyen las exigencias de la Facultad Politécnica. No se reauditaron todos los PDFs de antecedentes ni se ejecutaron nuevos experimentos, tests o contrastes en esta pasada.

## 1. Dictamen principal

**Sí cambiaría la estructura y parte de la escritura.** La revisión anterior mejoró la transparencia y corrigió la mezcla de evidencias, pero el texto todavía funciona parcialmente como informe de evolución del proyecto. Eso es útil para trabajar; no es la mejor organización para explicar una investigación al lector.

El cuerpo debe explicar el problema, el método, las comparaciones y las conclusiones que permiten los datos. La historia de versiones, los recuentos de tests y las reauditorías respaldan trazabilidad, pero no deben dirigir la narrativa científica. PLOS recomienda organizar por la lógica que sostiene la conclusión, no por la cronología de los experimentos. Esta recomendación no autoriza eliminar resultados desfavorables. [Mensh y Kording, 2017](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005619).

La dirección actual que ya consta en el manuscrito es selección de bloques y adquisición condicional con un ensamble de subconjuntos como rescate. **Todavía no está demostrado cuánto aporta la compuerta frente a la poda estática.** Reescribir mejor no resuelve ese vacío experimental ni convierte el piloto Outex en validación en seis datasets.

### Lo que sí conservaría

- La biblioteca de 22 bloques y el panel principal de seis datasets; no añadir VisTex para aumentar volumen.
- La comparación estática como fundamento empírico y referencia competitiva, no como única contribución original.
- La distinción entre benchmark estático, cascada anterior y piloto híbrido. Su cobertura debe poder verse de inmediato.
- Los puntos negativos: menor F1 que Completa/ensamble permanente en el piloto, ventaja de relevancia sobre marginal en B60/B120 y excedencia de presupuesto del rescate completo.
- Las reservas de procedencia KTH, fidelidad CUReT/Soil y exposición previa de benchmarks, en los lugares donde afectan a la interpretación.
- Estadística separada por clasificador y ausencia de equivalencia cuando solo hay no rechazo.

### Lo que no presentaría como resultado central

- Tests aprobados, número de replays, filas recalculadas o estado de cierre del trabajo.
- El mayor número de extractores como evidencia de novedad por sí mismo.
- Un punto OOF elegido después de comparar presupuestos como ganador confirmatorio o configuración final de despliegue.
- El ahorro proyectado del híbrido como latencia física; ni las mediciones de la cascada anterior como mediciones de este método.
- Una lista completa de intentos fallidos solo porque consumieron tiempo de desarrollo.

## 2. Cuerpo, anexos y documentación del proyecto

| Material | Destino recomendado | Razón y condición |
| --- | --- | --- |
| Problema, preguntas, alcance y aporte implementado | Cuerpo | Son el contrato con el lector; distinguir procedimiento implementado de ventaja aún no demostrada |
| Definición de concatenación, ensamble y adquisición condicional | Cuerpo | Evita confundir fusión temprana de características con agregación de scores |
| Método actual: base, rescate, poda, compuerta, costo compartido | Cuerpo, con ecuaciones y pseudocódigo | Es el mecanismo que se quiere evaluar; no basta una descripción general |
| Seis datasets y protocolos efectivos | Tabla en cuerpo; detalle/manifiestos en anexos | Mostrar qué condiciones alimentan cada evaluación, sin mezclar 47, 27 y el piloto de 680 imágenes |
| Resultados estáticos principales y controles del piloto | Cuerpo | Permiten juzgar calidad y compromiso de costo, incluidos los resultados negativos |
| Todas las políticas y presupuestos evaluados | Tabla/curva principal y detalle en anexo | Puede simplificarse la visualización, pero no ocultar puntos desfavorables o inviables |
| 22 checkpoints, parámetros completos y perfil de costos | Síntesis en cuerpo; tablas completas en anexos | Conservar reproducibilidad sin desplazar la explicación del algoritmo |
| Cascada anterior y pilotos físicos | Resumen comparativo en cuerpo si responde a una pregunta; detalle en anexos | Mantener etiqueta de variante/protocolo y sus límites; no apropiarse de su cobertura para el híbrido |
| N-gramas con/sin color | Anexo o análisis secundario, salvo que se mantenga una afirmación central sobre color | Separar ablación de ruta fija de reselección del pool |
| PCA/LDA, DynaTex, residuos u otros pilotos | Anexo de alternativas exploradas, únicamente con evidencia trazable | Describir diseño, alcance, resultado y motivo de descarte; no afirmar inferioridad universal |
| Error detectado o protocolo no comparable | Limitación relevante en cuerpo y detalle técnico aparte | No esconder su efecto; tampoco tratarlo como evidencia contra una familia metodológica |
| 80 tests, 147 métricas, hashes, comandos y replays | Anexo de reproducibilidad / repositorio / auditoría | Son control de implementación y procedencia, no efecto científico |
| Cronología, tareas pendientes y plan P0–P5 | Documentación de proyecto | En la tesis solo permanecen las limitaciones y el trabajo futuro científicamente pertinentes |

Esta distribución es coherente con una tesis técnica: el cuerpo desarrolla problema–método–resultados–discusión y los anexos conservan detalles de procedimientos/datos. No se adopta automáticamente la extensión ni el formato particular de otra universidad. [Guía de tesis de MIT](https://web.mit.edu/21.guide/th-form.htm).

## 3. Revisión de los capítulos actuales

### Portada, título y resumen

**Anclas:** `paper/tesis.tex:34`, `:41`, `:46`, `:79` y `:85`.

El título actual une concatenación sistemática, fusión adaptativa y adquisición guiada por incertidumbre. Es informativo, pero largo y todavía da mucho protagonismo al estudio estático. Además, el margen SVM no es una probabilidad calibrada de certeza.

Consideraría, para decisión del autor, el título de trabajo **«Fusión costo-consciente de descriptores de textura mediante ensambles y adquisición condicional»**. No implica optimalidad ni superioridad. El título definitivo debe depender del método y alcance que finalmente queden sustentados.

El resumen debe priorizar problema, enfoque, diseño efectivo, hallazgo principal y límite determinante. Hoy contiene bastante historia de la cascada anterior y una lista de tareas de cierre. Reduciría esa cronología y conservaría claramente: seis datasets para el benchmark; Outex/entrenamiento oficial para el piloto nuevo; costo proyectado y pérdida observada de F1. No omitiría que el híbrido aún carece de medición física.

La selección de B60 debe presentarse como punto ilustrativo del barrido de desarrollo, no como configuración preespecificada antes de observar sus resultados. La coincidencia entre resumen e introducción y el alcance realmente evaluado es una práctica explícita de reporte en aprendizaje automático. [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist).

Hay dos construcciones de portada (`maketitle` y `titlepage`). Revisaría si ambas responden a una exigencia institucional; no asumiría que son dos páginas obligatorias. También revisaría listas de figuras/tablas, nomenclatura y selección de idioma de LaTeX según la plantilla local, sin cambiarlo a ciegas.

### Capítulo 1 — Introducción

**Anclas:** `paper/chapters/01_introduccion.tex:7`, `:14` y `:16`.

Conservaría la distinción conceptual entre concatenación y ensamble. Cambiaría el orden: el lector necesita primero el problema práctico de ejecutar extractores para todas las imágenes, después el vacío específico y finalmente el enfoque del estudio. El inventario de 22/47/27 y las reservas de todas las variantes llegan demasiado pronto y dominan la motivación.

Añadiría objetivos explícitos y una correspondencia entre las tres preguntas ya formuladas y sus evaluaciones. No generaría una nueva contribución ni objetivos retrospectivos que prometan superar a todos los comparadores. La tercera pregunta debe seguir abierta hasta completar la ablación.

Las contribuciones deben describir artefactos/procedimientos realmente implementados y hallazgos con su alcance, no certificados de originalidad ni una enumeración de tareas realizadas. Las limitaciones esenciales deben seguir visibles, pero su desarrollo detallado corresponde al diseño experimental y la discusión.

### Capítulo 2 — Fundamentos y trabajos relacionados

**Anclas:** `paper/chapters/02_literatura.tex:5`, `:13`, `:19`, `:23` y `:33`.

Es el capítulo que más reforzaría en contenido científico. Actualmente repasa descriptores, redes, GFS, early exits y EDDI, pero no construye una comparación suficientemente específica para el rescate por ensamble.

Añadiría un hilo comparativo entre: selección estática de bloques; ensambles y poda de miembros; adquisición bajo costo; cascadas/selección condicional de modelos. Para los antecedentes más cercanos, usaría una matriz con unidad adquirida, señal de selección, costo contabilizado, activación por muestra, tipo de ensamble y protocolo de evaluación. **La matriz exige leer/verificar esos trabajos; no se pueden rellenar sus celdas por su título o resumen.**

Faltan definición y referencia de CKA, pese a ser parte del método. Un punto de partida primario verificable es [Kornblith et al., ICML 2019](https://proceedings.mlr.press/v97/kornblith19a.html). Esto no convierte CKA en una contribución propia ni demuestra que una menor similitud de representaciones cause mejores errores complementarios.

Eliminaría el tono de brecha universal: dos ejemplos de early exit y un método AFA no prueban que no exista trabajo sobre adquisición por bloques o selección de ensambles bajo presupuesto. La comparación crítica debe delimitar qué se toma de los antecedentes y qué diferencia se pondrá a prueba.

No ampliaría una enciclopedia de arquitecturas ni incluiría todos los PDFs del directorio solo porque están disponibles. Cada fuente debe cumplir una función argumental.

### Capítulo 3 — Método

**Anclas:** `paper/chapters/03_metodologia.tex:22`, `:34`, `:156`, `:178`, `:184`, `:196` y `:239`.

El capítulo mezcla representación, catálogos, datos, clasificadores, estadística y dos generaciones de cascada. La variante nueva aparece al final, mientras que la cascada anterior tiene más desarrollo formal. Si la dirección actual se mantiene, invertiría ese énfasis.

Hacen falta, a partir de la implementación y no de una reformulación idealizada:

- Notación única para bloques, miembros, base, compuerta, presupuesto y costo marginal.
- Fórmulas de relevancia normalizada, utilidad con penalización CKA, muestreo por ranking y combinación de scores. El código calcula una desviación estándar global de scores de entrenamiento por modelo; «escala escalar» no especifica esa operación.
- Descripción exacta de la poda, parada, base sola, desempates y candidatos inviables. Distinguir modelo único de multiplicidad del voto.
- Un pseudocódigo de selección/entrenamiento y otro de inferencia. No presentar una búsqueda greedy como optimización global resuelta.
- Diagrama del método actual con flujo de entrenamiento e inferencia diferenciados. Las figuras presentes explican extracción/GFS o resultados de la cascada anterior, no el híbrido completo.
- Definición de cada término del costo y del perfil utilizado. Los metadatos del piloto registran `policy_overhead_ms=0.45` y latencias por descriptor; el manuscrito debe indicar su procedencia y qué parte no corresponde a tiempo medido del híbrido. Una tabla completa puede ir al anexo.
- Frontera de reutilización: qué bloques no se recalculan, cuántos clasificadores se ejecutan y cuándo el rescate reemplaza a la base.

Movería datos, protocolos, hardware, métricas y contrastes a un capítulo de diseño experimental. Mantendría la cascada anterior como comparador definido de manera suficiente, con detalles de implementación históricos en anexo.

### Capítulo 4 actual — Resultados

**Anclas:** `paper/chapters/04_resultados.tex:8`, `:20`, `:43`, `:87`, `:114` y `:152`.

Ordenaría los resultados por pregunta de investigación, no por antigüedad del ejecutor. La comparación estática responde a selección y dimensionalidad; la cascada anterior al primer estudio de adquisición; el híbrido a selección del rescate y activación. No combinaría sus métricas para construir un único ganador.

Conservaría controles negativos y todos los presupuestos. Añadiría una curva calidad–costo **del híbrido actual** con las variantes y referencias de su mismo protocolo. Las figuras existentes están correctamente etiquetadas como históricas, pero no sustituyen esta figura.

La tabla del híbrido no contiene columnas para Top-5 y Completa, aunque el texto los compara numéricamente. Los incorporaría en una tabla/figura común de controles del mismo piloto y marcaría GFS y poda sin compuerta como pendientes mientras no existan en ese protocolo. No rellenaría esas celdas con resultados de test externo.

Movería «Trazabilidad y estado de cierre» fuera del capítulo de resultados. Las 80 pruebas de software y los replays no deben competir con macro-F1 y costo como evidencia del aporte.

Mantendría el formato homogéneo de medias en las tablas principales, respetando la preferencia del autor. Pero añadiría variabilidad/valores por partición en anexos o figuras apropiadas: no hace falta imponer ± a todas las celdas. En Outex con un único split no se inventa una desviación entre splits. Debe distinguirse variación de particiones, semillas y repeticiones de ejecución; ninguna convierte folds compartidos en datasets independientes. [NeurIPS Paper Checklist, reporte de variabilidad](https://neurips.cc/public/guides/PaperChecklist).

También reduciría la recitación de muchos números ya visibles en las tablas: el texto debe destacar patrón, excepción y significado. Las tablas deben ser interpretables con sus leyendas. [Zhang, 2014](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003453).

### Capítulo 5 — Discusión

**Anclas:** `paper/chapters/05_discusion.tex:8`, `:13` y `:18`.

La discusión es honesta, pero repite las cifras de B60, el 85,40 %, el no rechazo y las advertencias. Desarrollaría más la interpretación: cuándo conviene adquirir bloques, qué ganancia puede deberse a poda, qué observaciones muestran complementariedad y qué no permiten atribuirla a CKA o a la compuerta.

Debe conversar con los trabajos cercanos del capítulo 2. Hoy casi todo el diálogo bibliográfico queda en dos referencias generales al final. Añadiría comparación conceptual basada en métodos/protocolos, sin afirmar que un porcentaje obtenido en otro hardware/split demuestra superioridad.

Concentraría amenazas a la validez en una sección estructurada: selección y exposición; dependencia de muestras; comparabilidad de variantes; costo estimado/físico; generalización a datasets/semillas. Conservaría las advertencias breves junto a tablas donde su ausencia cambiaría la interpretación.

### Capítulo 6 — Conclusiones

**Anclas:** `paper/chapters/06_conclusion.tex:4`, `:8` y `:12`.

Concluiría respondiendo a las preguntas de la introducción: qué se sabe de selección estática, qué evidencia existe sobre adquisición y qué sigue sin aislarse en el híbrido. No copiaría de nuevo todas las cifras ni terminaría principalmente con el estado administrativo del proyecto.

Separaría resultados alcanzados, limitaciones del estudio y trabajo futuro. Para el borrador actual debe seguir explícita la falta de cierre experimental; en una futura versión final, las validaciones esenciales no pueden permanecer convertidas simplemente en «trabajo futuro» para sostener una afirmación que depende de ellas.

## 4. Precisiones científicas que la escritura todavía debe resolver

No requieren inventar nuevos resultados, pero sí corregir o verificar la formulación antes de la siguiente revisión del manuscrito:

1. **Certeza y margen.** En metodología, línea 212, aceptar una predicción no acredita que sea «suficientemente certera». Expresar la regla operativa de parada, sin convertir el margen en probabilidad calibrada.
2. **Familia de comparaciones de la cascada.** Metodología, línea 192, enumera Top-k y Completa; resultados, línea 71, incluye también la cascada ResNet. La especificación debe enumerar la misma familia efectiva y su ajuste.
3. **Hipótesis nulas distintas.** Metodología, línea 194, generaliza «igualdad de rangos» a todos los casos. Separar Friedman/post-hoc y Wilcoxon pareado, cuya formulación se refiere a la distribución de diferencias respecto de cero, con sus supuestos. [Documentación primaria de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).
4. **Una única evaluación externa.** La expresión en DTD (`03_metodologia.tex:160`) debe referirse a la separación dentro de cada corrida, sin sugerir que esos benchmarks nunca influyeron en decisiones posteriores. El mismo manuscrito reconoce exposición histórica.
5. **KTH estático frente a corregido.** Las líneas 170 y 180 señalan variantes distintas, pero conviene identificar explícitamente cuál alimenta cada tabla/contraste. Una referencia general a «protocolo anidado» no debe hacer pasar una selección anterior por la corregida.
6. **Términos y nivel de evidencia.** Definir OOF, CKA, fit productor y costo proyectado al primer uso; distinguir biblioteca histórica de 21 de la ablación reciente sin N-gramas. Una tabla de protocolos resuelve mejor esto que reiterar reservas por todo el texto.

Estos hallazgos no anulan las comprobaciones numéricas anteriores. Muestran que concordancia de cifras y calidad de exposición científica son verificaciones diferentes.

## 5. Estructura que propondría para la tesis

Propuesta editorial para decisión del autor, no requisito institucional ni reestructuración ya aplicada:

| Capítulo propuesto | Pregunta que debe resolver | Evidencia/material |
| --- | --- | --- |
| 1. Introducción | ¿Qué problema se estudia y con qué alcance? | Preguntas actuales, objetivos, contribución implementada y límites principales |
| 2. Fundamentos y trabajos relacionados | ¿Qué resuelven los antecedentes y qué diferencia se evaluará? | Fusión, selección, ensambles/poda, adquisición y comparación crítica verificada |
| 3. Método de fusión y adquisición condicional | ¿Cómo se construye y ejecuta? | Formulación, pseudocódigos, entrenamiento/inferencia, base/ensamble/gate/costo |
| 4. Diseño experimental | ¿Cómo se somete a prueba y contra qué? | Seis datasets, tabla de protocolos, 47/27/piloto, clasificadores, controles, métricas y recursos |
| 5. Resultados | ¿Qué respaldan los datos para cada pregunta? | Benchmark estático, cascada de referencia e híbrido; curvas/ablaciones efectivamente ejecutadas |
| 6. Discusión y amenazas a la validez | ¿Qué significa y hasta dónde se generaliza? | Interpretación, alternativas explicativas, contraste bibliográfico y limitaciones |
| 7. Conclusiones y trabajo futuro | ¿Qué se responde y qué no? | Respuestas a preguntas, contribuciones alcanzadas y líneas posteriores |

Anexos propuestos: A, especificaciones/perfil de costos; B, protocolos y procedencia; C, tablas completas y variabilidad; D, exploraciones alternativas trazables; E, reproducibilidad, comandos y auditorías.

No fijaría un número arbitrario de páginas o porcentajes por capítulo sin el reglamento y objetivo de entrega. Más extensión solo se justifica si desarrolla el método, los antecedentes o la interpretación que ahora faltan; no por rellenar.

## 6. Cómo cambiaría la escritura

- Un término por concepto: «conjunto de datos», «pliegue», «puntuación de decisión», «compuerta», «bloque» y «miembro». Definir términos ingleses necesarios, no alternar sin criterio.
- Presente para la definición del algoritmo y pasado para la ejecución realizada; futuro/condicional solo para trabajo no ejecutado.
- Resultados: observación y magnitud. Discusión: interpretación y explicación alternativa. No hacer que ambas secciones repitan la misma tabla en prosa.
- Precisar incertidumbre donde importa; no debilitar hechos observados ni llenar cada párrafo con «no demuestra» si ya quedó delimitado su estimando. Tampoco retirar una limitación local imprescindible.
- Evitar expresiones autoevaluativas como «se informan con rigor» (`03_metodologia.tex:194`). Mostrar el procedimiento y la evidencia.
- Reemplazar «escala escalar» por la operación matemática exacta. Definir qué significa cada sigla y símbolo antes de usarlo.
- Hacer cada tabla autosuficiente: población/protocolo, métrica, agregación, unidad de costo y significado de guiones. Un guion no debe significar indistintamente no evaluado, no aplicable o resultado faltante.
- No convertir observaciones de desarrollo en explicación causal: menos similitud CKA no prueba complementariedad útil y menos llamadas no prueba una reducción física idéntica.
- Nombres de autores, tutor y agradecimientos son legítimos en sus secciones. Evitar atribuciones personales como sustituto del método; las contribuciones de autoría se declaran de manera apropiada, no se borran.

## 7. Tesis y artículo no son el mismo entregable

La tesis puede desarrollar fundamentos, decisiones, resultados negativos y anexos. Un artículo derivado debe focalizar una pregunta y una contribución evaluada, con metodología y resultados suficientes para sostenerla. No comprimiría automáticamente los siete capítulos en un artículo ni daría a todos los pilotos el mismo protagonismo.

Para un eventual artículo del híbrido faltan los controles y validaciones ya identificados; podría existir un reporte exploratorio, pero no debe anunciar superioridad general o ahorro físico aún no observado. Elegir revista/conferencia y sus normas es una decisión posterior; no se declara alineación con NeurIPS por consultar su checklist.

ARS recuerda incluir disponibilidad de datos/código, autoría, financiación, conflictos, ética y uso de IA donde corresponda. Se debe revisar su aplicación con el reglamento/destino y los autores. **No inventar** que no hubo financiación, que los datos permiten redistribución, que hay aprobación ética o cómo se reparten contribuciones. La descarga pública de un dataset no acredita por sí sola permiso de redistribuirlo.

## 8. Qué puede hacerse ya y qué depende de evidencia nueva

**Puede editarse ahora, previa aprobación del esquema:** reorganización por preguntas; separación método/diseño; definición matemática de operaciones existentes; pseudocódigos y diagrama del flujo implementado; tabla de cobertura/protocolos; referencias metodológicas faltantes una vez verificadas; reducción de duplicación; anexos de trazabilidad; corrección de las seis precisiones señaladas.

**No puede escribirse como si estuviera terminado:** efecto específico de compuerta frente a poda, robustez multiconjunto del híbrido, ventaja propia de marginal sobre relevancia, GFS comparable del piloto, fidelidad física cerrada de todas las variantes o latencia real del nuevo híbrido. Son verificaciones experimentales, no problemas de redacción.

El siguiente paso editorial es decidir esta estructura y el alcance del manuscrito; el siguiente paso experimental sigue siendo el control exacto de poda sin compuerta. Ninguno sustituye al otro. Se preservan sin cambios el PDF, los capítulos, los resultados y el plan técnico vigente.
