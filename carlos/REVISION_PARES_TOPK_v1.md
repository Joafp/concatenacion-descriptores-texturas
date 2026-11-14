# Revisión por pares simulada — Ronda 1

- **Manuscrito**: «Concatenación Top-k de descriptores para clasificar texturas: comparación del uso directo y la activación por margen»
- **Archivo revisado**: `carlos/main.tex` (PDF: `carlos/main_topk_margen.pdf`, 18 páginas + aspectos destacados)
- **Fecha**: 14-11-2026
- **Modo**: `full` (skill `academic-paper-reviewer` v1.10.0)
- **Revista objetivo supuesta**: Pattern Recognition Letters o Expert Systems with Applications (Elsevier)

## Procedencia del panel (léase primero)

Los cinco revisores son personajes simulados por un único modelo (Claude, familia Opus) en una sola sesión. La diversidad de personajes no equivale a diversidad de modelos: los puntos ciegos pueden estar correlacionados entre revisores (Ren et al. 2026, arXiv:2607.13104 §5.2). Además, el mismo modelo redactó el borrador en esta sesión, por lo que **la independencia exigida por la skill no se cumple**: hay riesgo de que los revisores no vean errores que el redactor tampoco vio. Para compensar, los revisores se escribieron con sesgo deliberado hacia la crítica, y cada observación lleva un ancla verificable en el manuscrito. Conviene que Joaquín o el tutor hagan una lectura humana independiente.

El manuscrito no se modificó durante la revisión.

---

## Fase 0 — Configuración del panel

| Rol | Identidad | Foco |
|---|---|---|
| EIC | Editor asociado de una revista Elsevier de reconocimiento de patrones con perfil aplicado, especialista en representación de imágenes | Encaje en la revista, originalidad, coherencia entre título, pregunta y evidencia |
| R1 — Metodología | Investigador en evaluación experimental de aprendizaje automático (comparaciones entre datasets, pruebas no paramétricas, fuga de información) | Diseño anidado, selección con datos de test, inferencia con N=5–6, reproducibilidad de costos |
| R2 — Dominio | Investigador en análisis de texturas y extractores preentrenados congelados | Cobertura de literatura, comparadores, novedad dentro de clasificación de texturas |
| R3 — Perspectiva | Ingeniero/investigador en inferencia eficiente y despliegue (sistemas, cascadas, latencia) | Validez práctica de las mediciones de latencia y de la regla de costo |
| DA — Abogado del diablo | Revisor que busca la contraargumentación más fuerte | Rupturas lógicas, selección favorable de evidencia, distancia entre lo que se promete y lo que se demuestra |

---

## Informe EIC

**Recomendación**: Major Revision — **Confianza**: 4 (representación de imágenes y evaluación; no especialista en despliegue)

**Resumen.** El artículo estudia dos usos de una concatenación Top-k de descriptores congelados para texturas: calcularla siempre o activarla cuando una etapa barata tiene margen bajo. Fija k=4 a partir de curvas de desempeño, compara Top-4 con el mejor descriptor individual y con la concatenación completa en 47 condiciones por clasificador, evalúa una cascada por margen en 27 condiciones y reporta latencias online en 94. El trabajo es cuidadoso con la procedencia y honesto con sus limitaciones, algo poco frecuente. Su problema central es de coherencia: el título y la sección 3.3 construyen el estudio sobre Top-4, pero la comparación pareada que da nombre al artículo usa una Top-k de tamaño variable (1–8), y la medición online usa una etapa cara que tampoco es Top-4. El lector termina con dos estudios yuxtapuestos. La contribución metodológica es incremental (ranking por filtro y cascada por margen son técnicas conocidas); el valor está en la evaluación, y eso exige que la pregunta y la evidencia coincidan.

### Fortalezas
**S1: Transparencia excepcional sobre la procedencia y los límites.** El texto declara que k=4 se leyó del test, que la tolerancia 0,005 es post hoc y que KTH-TIPS2-b no está reconciliado.
Ancla: `text: §5.1 «El valor k=4 se leyó de la curva externa de SVM»`.

**S2: Control con escalamiento aleatorio de igual cantidad.** Separa el efecto del margen del efecto de gastar más presupuesto.
Ancla: `table: Tabla 8 — cascada > aleatorio en 27/27 por cuantil`.

**S3: Mediciones de latencia por imagen, con F1 y tiempo de las mismas llamadas.**
Ancla: `table: Tabla 10`.

### Debilidades
**W1: El título promete una comparación que el diseño no realiza con el k elegido.**
- **Problema**: el artículo fija k=4 (§3.3, §4.5), pero la comparación directo frente a margen usa la Top-k archivada con k entre 1 y 8, y el panel usa un rescate por ensamble.
- **Ancla**: `text: §3.4 «pero no se realizó con k=4 fijo»`; `text: §3.5 «No calcula Top-4»`.
- **Por qué importa**: el lector espera «Top-4 directo frente a Top-4 activado por margen». Ese contraste no existe en ninguna tabla.
- **Sugerencia**: o bien (a) reencuadrar título, resumen y contribuciones en torno a «Top-k» con k interno por condición, presentando k=4 como recomendación para el uso directo; o bien (b) agregar la cascada con Top-4 fijo, que es computable con los embeddings almacenados.
- **Severidad**: Critical — **Confianza**: 5.

**W2: Encaje y extensión.**
- **Problema**: el manuscrito está en castellano y tiene 18 páginas con 11 tablas.
- **Ancla**: `dataset: PDF compilado — 18 páginas, Tablas 1–11`.
- **Por qué importa**: las dos revistas candidatas publican en inglés. Pattern Recognition Letters es de artículos cortos.
- **Sugerencia**: definir la revista antes de traducir. Si es PRL, mover las Tablas 1, 2, 9 y 11 a material suplementario. Si es ESWA, reforzar el ángulo aplicado: guía de cuándo usar la cascada.
- **Severidad**: Major — **Confianza**: 4.

**W3: Faltan declaraciones exigidas por Elsevier.**
- **Problema**: no hay declaración de conflicto de intereses, financiación ni uso de IA generativa, y la declaración ética figura como pendiente.
- **Ancla**: `absence: secciones finales — revisé Disponibilidad, Declaración ética y CRediT`.
- **Sugerencia**: agregar las tres declaraciones.
- **Severidad**: Major — **Confianza**: 5.

**W4: Contribución incremental poco delimitada.**
- **Problema**: las tres contribuciones de §1 describen mediciones, pero no qué aprende el lector que no supiera.
- **Ancla**: `text: §1 «El trabajo aporta tres resultados»`.
- **Sugerencia**: formular la contribución como una regla práctica respaldada por evidencia. Por ejemplo: «con extractores congelados de este tipo, 3–4 bloques bastan, y la cascada solo conviene si C_b ≪ C_Top-k», y mostrar dónde se cumple y dónde no.
- **Severidad**: Major — **Confianza**: 4.

### Preguntas
1. ¿Cuál es la pregunta principal del artículo: cuántos bloques usar, o cuándo calcularlos? Hoy ambas compiten por el título.
2. ¿Es posible correr la cascada con Top-4 fijo sobre los embeddings almacenados? Si no, ¿por qué?

### Puntuaciones
| Dimensión | Puntaje | Descriptor |
|---|---|---|
| Originalidad (20 %) | 52 | Weak/Adequate |
| Rigor metodológico (25 %) | 58 | Adequate |
| Suficiencia de evidencia (25 %) | 62 | Adequate |
| Coherencia argumental (15 %) | 50 | Weak |
| Calidad de redacción (15 %) | 72 | Strong |
| **Promedio ponderado** | **58,8** | **Major Revision** |

---

## Informe R1 — Metodología

**Recomendación**: Major Revision — **Confianza**: 5 (evaluación experimental y estadística comparativa)

**Resumen.** El protocolo anidado está bien construido para la selección de bloques. La auditoría de grupos y la separación entre evaluaciones también están bien hechas. Los problemas aparecen en tres puntos donde el test o decisiones posteriores influyen en lo que se informa: la elección de k, la tolerancia de la ruta y la inclusión de KTH-TIPS2-b en las medias del resumen. La inferencia descansa en 5–6 datasets, y el texto lo reconoce. Aun así, algunas frases del resumen y de los aspectos destacados leen la ausencia de rechazo como resultado. La proyección de costos usa un perfil de otro dataset, y el piloto físico muestra discrepancias de representación que no se explican.

### Fortalezas
**S1: Selección dentro del entrenamiento con folds agrupados y verificación programática de grupos.**
Ancla: `text: §4.3 «Se verifica programáticamente que ningún grupo aparezca en entrenamiento y prueba»`.

**S2: Pruebas sobre medias por dataset, sin tratar particiones como réplicas.**
Ancla: `text: §4.4 «no trata las particiones repetidas como problemas independientes»`.

**S3: No inferioridad con margen explícito, en lugar de inferir equivalencia del no rechazo.**
Ancla: `table: Tabla 6`.

### Debilidades
**W1: k=4 se eligió mirando el test, y luego se evalúa Top-4 sobre ese mismo test.**
- **Problema**: la Tabla 5 y la Tabla 6 evalúan una configuración cuyo hiperparámetro se fijó con la curva externa.
- **Ancla**: `text: §4.5 «El valor k=4 se fijó al observar la curva externa de SVM»`.
- **Por qué importa**: hay sesgo optimista en Top-4 frente a Completa-22. La curva es plana entre 3 y 10, así que el sesgo probablemente es pequeño, pero no está cuantificado.
- **Sugerencia**: informar como sensibilidad el resultado con k=3 y k=6 frente a Completa-22. Ya figuran en la Tabla 4: 0,9339 y 0,9348 con SVM. Hay que decirlo explícitamente: «cualquier k entre 3 y 10 queda a menos de 0,005 de Completa-22 con SVM». Otra opción es usar la regla del codo sobre la curva interna media como criterio declarado.
- **Severidad**: Major — **Confianza**: 5.

**W2: La media del resumen incluye KTH-TIPS2-b, que se excluye de las pruebas, y sin él el orden se invierte.**
- **Problema**: el resumen afirma 0,9345 frente a 0,9341, cascada por encima de Top-k. Con los cinco datasets reconciliados es 0,9325 frente a 0,9329: la cascada queda por debajo.
- **Ancla**: `table: Tabla 7 — fila Media incluye KTH-TIPS2-b (0,9445 frente a 0,9400)`; `text: §4.4 «KTH-TIPS2-b se excluye de las pruebas»`.
- **Por qué importa**: la cifra principal depende de la variante no reconciliada. La conclusión cualitativa («conserva el macro-F1») se mantiene, pero el signo no.
- **Sugerencia**: informar en el resumen y en la conclusión las medias de los cinco datasets reconciliados, con KTH-TIPS2-b aparte. O bien informar ambas cifras.
- **Severidad**: Major — **Confianza**: 5.

**W3: La proyección de costos usa el perfil de Outex para cinco datasets.**
- **Problema**: los costos de DTD, FMD, CUReT y Soil provienen de tiempos medidos en imágenes de entrenamiento de Outex, que son de 128×128.
- **Ancla**: `text: §4.3 «medidos en KTH-TIPS2-b para ese dataset y en imágenes de entrenamiento de Outex para los demás»`.
- **Por qué importa**: el costo de extracción depende del tamaño de entrada y del preprocesamiento. El 75,5 % es una estimación con un perfil ajeno.
- **Sugerencia**: declararlo junto a la cifra en el resumen («costo proyectado con un perfil de latencias de referencia»). Mostrar que el piloto físico (69 %) es la cifra medida.
- **Severidad**: Major — **Confianza**: 4.

**W4: El piloto físico muestra representaciones no idénticas.**
- **Problema**: el coseno mínimo es −0,0707 en CUReT entre la representación extraída y la almacenada, aunque «las rutas y predicciones coincidieron».
- **Ancla**: `text: §4.8 «los cosenos mínimos ... fueron −0,0707 en CUReT y 0,0085 en Soil»`.
- **Por qué importa**: un coseno negativo indica vectores prácticamente distintos. Que las predicciones coincidan con vectores tan distintos requiere explicación; si no, la validez del piloto es dudosa en esos datasets.
- **Sugerencia**: explicar el origen o informar el piloto sin CUReT y Soil como sensibilidad.
- **Severidad**: Major — **Confianza**: 4.

**W5: La familia estadística incluye métodos que el artículo no muestra.**
- **Problema**: Friedman y Holm se calculan sobre ocho estrategias, entre ellas dos ensambles, GFS y Homogénea, que no aparecen en ninguna tabla.
- **Ancla**: `text: §4.4 «La familia contiene ocho estrategias»`; `absence: §4.6 y Tablas 5–6 — no hay resultados de ensambles, GFS ni Homogénea`.
- **Por qué importa**: el lector no puede verificar los rangos. La corrección por 28 pares penaliza a Top-4 por comparaciones ajenas al artículo.
- **Sugerencia**: restringir la familia a Individual, Completa-22 y Top-4 (tres pares), recalculando con los CSV de `results/analysis/selection_stats/`, o incluir la tabla de las ocho estrategias en un apéndice. La primera opción no requiere experimentos nuevos.
- **Severidad**: Major — **Confianza**: 5.

**W6: Discrepancia sin explicar entre el panel y la evaluación estática.**
- **Problema**: Top-4 con SVM en Soil da 0,8594 en el panel y 0,8864 en la Tabla 5.
- **Ancla**: `text: §4.9 «la mayor diferencia corresponde a Top-4 con SVM en Soil (0,8594 frente a 0,8864)»`.
- **Por qué importa**: una diferencia de 0,027 es mayor que casi todos los efectos que el artículo discute.
- **Sugerencia**: explicar el mecanismo (normalización congelada, reconstrucción del bloque de color u otro) o tratar el panel solo como evidencia de latencia.
- **Severidad**: Major — **Confianza**: 4.

**W7: Una sola semilla y un solo clasificador en la comparación central.**
- **Problema**: la cascada se evalúa con SVM y semilla 42.
- **Ancla**: `text: §4.3 «27 condiciones con SVM y semilla 42»`.
- **Sugerencia**: declararlo en el resumen. Si no se agrega ResMLP, limitar la conclusión a SVM.
- **Severidad**: Minor — **Confianza**: 5.

### Preguntas
1. ¿Qué produce el coseno negativo en CUReT en el piloto, si las predicciones coinciden?
2. ¿Con qué normalización se evaluó la Tabla 5 y con cuál el panel? ¿Explica eso la diferencia en Soil?
3. ¿Se puede recalcular Friedman y Holm solo con los tres métodos reportados?

### Problemas menores
- La Tabla 7 muestra Completa-22 = 0,9409 y la Tabla 5 muestra 0,9391. Son conjuntos de condiciones distintos (27 frente a 47); conviene señalarlo en ambas leyendas.
- El Wilcoxon «mínimo posible» de la Tabla 8 debe acompañarse del tamaño del efecto por dataset.

### Puntuaciones
| Dimensión | Puntaje | Descriptor |
|---|---|---|
| Originalidad (20 %) | 55 | Adequate |
| Rigor metodológico (25 %) | 52 | Weak/Adequate |
| Suficiencia de evidencia (25 %) | 58 | Adequate |
| Coherencia argumental (15 %) | 58 | Adequate |
| Calidad de redacción (15 %) | 72 | Strong |
| **Promedio ponderado** | **58,1** | **Major Revision** |

---

## Informe R2 — Dominio (texturas y extractores congelados)

**Recomendación**: Major Revision — **Confianza**: 4

**Resumen.** Para la comunidad de texturas, el resultado más útil es que cuatro Transformers preentrenados (SigLIP-B, EVA-02, DINOv2, BEiTv2) concentran casi todo el beneficio de una biblioteca de 22 bloques. La comparación con cuatro métodos recientes reimplementados sobre particiones libres de fuga también es valiosa, y la auditoría de los protocolos originales es una contribución en sí misma. Faltan antecedentes sobre selección de vistas o bloques y sobre clasificación selectiva. Algunos protocolos se mencionan sin cita. El artículo depende además de una «matriz principal del proyecto» que el lector externo no puede consultar.

### Fortalezas
**S1: Comparadores reimplementados en particiones comunes y libres de fuga, con auditoría de los protocolos originales.**
Ancla: `text: §4.10 «HyTexNet alcanza 0,9394 ... en el protocolo de un tercio ... y 0,8259 en el panel»`.

**S2: Identificación de qué bloques componen Top-4.**
Ancla: `text: §5 «SigLIP-B y EVA-02 aparecen en 41 de los 47 subconjuntos Top-4»`.

**S3: Biblioteca amplia y bien especificada.**
Ancla: `table: Tablas 1–2`.

### Debilidades
**W1: Dependencia de un estudio no publicado.**
- **Problema**: Individual, Completa-22, la Top-k de la cascada (k heredado de GFS) y la familia estadística provienen de «la matriz principal del proyecto», que no se cita ni se describe.
- **Ancla**: `text: §3.4 «se heredó de la selección secuencial hacia adelante (GFS) de la matriz principal del proyecto»`; `text: §4.3 «Individual y Completa-22 provienen de la matriz principal del proyecto»`.
- **Por qué importa**: un revisor externo no puede evaluar cómo se obtuvo el k de la cascada ni la configuración de GFS.
- **Sugerencia**: describir GFS en un apéndice (criterio, parada, tope de 8) y explicar que la matriz principal es una evaluación previa del mismo protocolo, o citar la tesis o un preprint.
- **Severidad**: Major — **Confianza**: 5.

**W2: Faltan antecedentes de clasificación selectiva y medidas de confianza.**
- **Problema**: el margen top-1/top-2 es una medida de confianza clásica (opción de rechazo, clasificación selectiva, muestreo por margen en aprendizaje activo). El artículo no la sitúa frente a alternativas como la puntuación máxima o la entropía.
- **Ancla**: `absence: §2.2 — revisé §2.2, §3.4 y §5; solo se citan cascadas y redes dinámicas`.
- **Por qué importa**: sin ese contexto, la elección del margen parece arbitraria.
- **Sugerencia**: agregar un párrafo con referencias verificadas sobre opción de rechazo y clasificación selectiva, y justificar el margen frente a otras medidas.
- **Severidad**: Major — **Confianza**: 4.

**W3: Protocolos y recursos mencionados sin cita.**
- **Problema**: el protocolo de RADAM para KTH-TIPS2-b y el repositorio de Soil de ai4a-lab no tienen referencia.
- **Ancla**: `text: §4.1 «Se emplea el protocolo de cuatro particiones usado por RADAM»`; `absence: references.bib — no hay entrada de RADAM`.
- **Sugerencia**: agregar ambas referencias.
- **Severidad**: Minor — **Confianza**: 5.

**W4: El bloque de color quedó fuera del ranking sin justificación metodológica.**
- **Problema**: N-gramas + SVD no participó del ranking por una razón técnica: se reconstruye por partición. Sin embargo, aporta en Soil y en KTH-TIPS2-b.
- **Ancla**: `text: §3.3 «N-gramas + SVD ... no participó del ranking»`; `text: §5 «aporta 0,0078 en Soil y 0,0105 en KTH-TIPS2-b»`.
- **Por qué importa**: la comparación Top-4 frente a Completa-22 no es entre bibliotecas iguales, porque Completa-22 tiene un bloque que Top-4 no pudo elegir.
- **Sugerencia**: declararlo en la §4.6, no solo en la §5, y comparar también con los 21 bloques. El README del barrido ya lo hace: Top-4 supera a los 21 bloques por 0,0018.
- **Severidad**: Major — **Confianza**: 4.

**W5: La Figura 1 muestra estrategias que el artículo no usa.**
- **Problema**: la figura etiqueta «Completa / GFS / Top-k / Homogénea».
- **Ancla**: `figure: Figura 1 — caja «Bloques S»`.
- **Sugerencia**: rehacerla con «Completa / Top-k» y un desvío hacia la etapa barata.
- **Severidad**: Minor — **Confianza**: 5.

### Preguntas
1. ¿La matriz principal se va a publicar? Si no, ¿qué parte de su protocolo hay que trasladar a este artículo?
2. ¿Por qué el margen y no la puntuación máxima o la entropía como medida de duda?

### Puntuaciones
| Dimensión | Puntaje | Descriptor |
|---|---|---|
| Originalidad (20 %) | 55 | Adequate |
| Rigor metodológico (25 %) | 60 | Adequate |
| Suficiencia de evidencia (25 %) | 62 | Adequate |
| Coherencia argumental (15 %) | 60 | Adequate |
| Calidad de redacción (15 %) | 72 | Strong |
| Integración de literatura | 52 | Adequate/Weak |
| **Promedio ponderado (5 dimensiones)** | **61,1** | **Major Revision** |

---

## Informe R3 — Perspectiva (inferencia eficiente y despliegue)

**Recomendación**: Major Revision — **Confianza**: 4

**Resumen.** Desde el despliegue, el artículo hace lo correcto al medir latencia por imagen y al reconocer que la cascada puede ser más lenta cuando Top-k es liviana. Esa observación, con la regla de costo de la ecuación 5, es probablemente lo más útil para un practicante. Pero las mediciones cubren un único escenario: GPU de escritorio, modelos residentes y lote unitario. Faltan la memoria, los percentiles altos de latencia y el comportamiento con lotes, que deciden si una cascada sirve en producción.

### Fortalezas
**S1: Reconoce el caso en que la cascada empeora.**
Ancla: `text: §5 «la cascada fue más lenta que Top-k directo en las dos particiones cuyo Top-k tenía un solo bloque»`.

**S2: Regla de costo explícita y elegida con entrenamiento.**
Ancla: `equation: Ec. 5`.

### Debilidades
**W1: Solo se informan medias y medianas de latencia.**
- **Problema**: una cascada tiene latencia bimodal: la mayoría de las imágenes sale temprano y unas pocas pagan la etapa cara más la barata.
- **Ancla**: `table: Tabla 10 — solo medias`; `text: §4.9 «con medianas entre 2,81 y 25,18 ms»`.
- **Por qué importa**: en aplicaciones con requisitos de tiempo real importa el percentil 95 o 99, y ahí la cascada puede ser más lenta que Top-4 directo.
- **Sugerencia**: informar el percentil 95 por política. Se puede calcular con los `online_calls.csv` ya guardados, sin correr nada nuevo.
- **Severidad**: Major — **Confianza**: 4.

**W2: No se discute la memoria.**
- **Problema**: la cascada necesita tener cargados la etapa barata y todos los extractores de Top-k.
- **Ancla**: `absence: §4.8, §4.9 y §5 — revisé las tres secciones`.
- **Por qué importa**: la cascada ahorra tiempo, no memoria. En equipos con poca memoria eso puede ser decisivo.
- **Sugerencia**: agregar una oración en la discusión y la memoria de modelos si está registrada.
- **Severidad**: Minor — **Confianza**: 4.

**W3: Solo se mide con lote unitario.**
- **Problema**: con lotes, la cascada rompe la homogeneidad del lote, porque solo algunas imágenes van a la etapa cara.
- **Ancla**: `text: §4.3 «cada imagen se procesa individualmente (batch=1)»`.
- **Por qué importa**: el ahorro relativo puede cambiar mucho en servidores que procesan por lotes.
- **Sugerencia**: declararlo como alcance. Si existen mediciones con lote 32 en el proyecto, mencionarlas aunque sean de otro equipo.
- **Severidad**: Minor — **Confianza**: 4.

**W4: La tasa de escalamiento puede cambiar con un cambio de distribución.**
- **Problema**: el umbral es un cuantil de márgenes del entrenamiento. Si la distribución de test cambia, la fracción escalada y el costo también cambian.
- **Ancla**: `text: §3.4 «en el test, la fracción observada ρ_q puede diferir de q»`.
- **Sugerencia**: informar la diferencia entre q y ρ_q (la Tabla 8 ya lo muestra: 0,25→0,217 y 0,75→0,687) y comentarla como garantía débil de presupuesto.
- **Severidad**: Minor — **Confianza**: 4.

### Preguntas
1. ¿Se guardaron latencias por llamada para calcular percentiles?
2. ¿Cuál es la memoria de GPU de Top-4 y de la política por margen con todos los modelos cargados?

### Puntuaciones
| Dimensión | Puntaje | Descriptor |
|---|---|---|
| Originalidad (20 %) | 58 | Adequate |
| Rigor metodológico (25 %) | 60 | Adequate |
| Suficiencia de evidencia (25 %) | 60 | Adequate |
| Coherencia argumental (15 %) | 65 | Adequate |
| Calidad de redacción (15 %) | 72 | Strong |
| Significancia e impacto | 60 | Adequate |
| **Promedio ponderado (5 dimensiones)** | **62,1** | **Major Revision** |

---

## Revisión del abogado del diablo

### Contraargumento más fuerte

El artículo afirma comparar el uso directo de Top-k con su activación por margen, y elige k=4 como el valor en que la curva se aplana. Sin embargo, ninguna tabla compara Top-4 directo con Top-4 activado por margen. La comparación pareada usa una Top-k cuyo k va de 1 a 8, heredado de un procedimiento distinto (GFS), y la medición online compara Top-4 con una política cuya etapa cara es un ensamble de otros subconjuntos. Los dos hallazgos principales («cuatro bloques bastan» y «el margen ahorra costo sin perder F1») provienen de experimentos distintos, con conjuntos de condiciones distintos (47, 27 y 94), costos medidos de formas distintas y, en el caso del panel, macro-F1 que no coincide con la evaluación estática. Un escéptico diría que el artículo une dos estudios que no se cruzan bajo un título que sugiere que sí. Además, la cifra principal de la cascada (0,9345 frente a 0,9341) solo favorece a la cascada si se incluye un dataset que el propio artículo excluye de las pruebas. Y el único control del margen es un sorteo, un rival débil: cualquier medida razonable de confianza debería superarlo. Lo que queda demostrado es más modesto: con este protocolo, un descriptor barato más un umbral de margen recupera casi todo el macro-F1 de una concatenación más cara, con ahorros que dependen de la razón de costos. Es útil, pero no es lo que el título promete.

### Lista de observaciones

#### CRITICAL
| # | Dimensión | Observación | Ancla | Confianza |
|---|---|---|---|---|
| DA-C1 | Ruptura de la cadena lógica | El título y la §3.3 fijan Top-4, pero la comparación directo frente a margen no usa Top-4 en ninguna evaluación. La conclusión «Top-4 ... y su activación por margen conviene cuando...» (§6) combina evidencias que nunca se cruzaron. | `text: §6 «Top-4 es una alternativa compacta ..., y su activación por margen conviene cuando»`; `text: §3.4 «pero no se realizó con k=4 fijo»` | 5 |

#### MAJOR
| # | Dimensión | Observación | Ancla | Confianza |
|---|---|---|---|---|
| DA-M1 | Selección favorable | El resumen y la conclusión usan la media con KTH-TIPS2-b (cascada 0,9345 > Top-k 0,9341). Sin KTH, la cascada queda por debajo (0,9325 < 0,9329). | `table: Tabla 7 — fila Media` | 5 |
| DA-M2 | Interpretación del no rechazo | Un aspecto destacado presenta como hallazgo que «las pruebas no detectan diferencias», con N=5 y poca potencia. | `text: Aspectos destacados, ítem 5` | 5 |
| DA-M3 | Rival débil | El margen se compara solo con un sorteo. Superar al azar en 27/27 era esperable y no muestra que el margen sea una buena compuerta frente a alternativas. | `table: Tabla 8` | 4 |
| DA-M4 | Lenguaje que suaviza pérdidas | «con un macro-F1 medio similar» (resumen y §6): con SVM, la política por margen pierde frente a Top-4 en 5 de 6 datasets, hasta −0,0154 en KTH-TIPS2-b. | `text: Resumen «con un macro-F1 medio similar»`; `table: Tabla 10` | 4 |

#### MINOR
| # | Dimensión | Observación | Ancla | Confianza |
|---|---|---|---|---|
| DA-m1 | Generalización | «la curva se aplana alrededor de k=4» se sostiene con SVM. La curva externa de ResMLP es irregular (0,9277 en k=9, máximo en k=5) y el codo interno da k=6. | `figure: Figura 3 — curva ResMLP` | 4 |
| DA-m2 | Causalidad no demostrada | La explicación de por qué la cascada supera a Top-k («conserva la predicción barata cuando esta es correcta») es plausible, pero no se muestra con un análisis por imagen. | `text: §5, párrafo 2` | 3 |

### Explicaciones alternativas ignoradas
- La ventaja de la cascada en FMD, Soil y KTH-TIPS2-b puede deberse a que la etapa barata elegida (SigLIP-B o BEiTv2-B) es por sí sola casi tan buena como Top-k en esos datasets, más que a que el margen sea un buen selector. Habría que informar el F1 de la etapa barata sola por dataset en la ruta elegida.

### Observaciones (no son defectos)
- La honestidad de la §5.1 desactiva varias críticas posibles. El problema no es que se oculte información, sino que el resumen y la conclusión no reflejan la cautela del cuerpo del texto.

---

## Decisión editorial

**Procedencia del panel**: los cinco personajes corrieron sobre una sola familia de modelos, que además redactó el borrador. La diversidad de personajes no es diversidad de modelos (ver arriba).

### Decisión: **Major Revision**

### Problemas que bloquean la aceptación
| Rango | Problema | Revisores | Ancla | Ítem del plan |
|---|---|---|---|---|
| 1 | La comparación del título no se realiza con el k elegido: Top-4 nunca se activa por margen | EIC W1, DA-C1, R1 (implícito en W2) | `text: §3.4 «pero no se realizó con k=4 fijo»` | R1 |
| 2 | La cifra principal de la cascada depende de KTH-TIPS2-b no reconciliado, y el resumen suaviza pérdidas y lee el no rechazo como hallazgo | R1 W2, DA-M1, DA-M2, DA-M4 | `table: Tabla 7 — fila Media` | R2 |
| 3 | Familia estadística con métodos no mostrados y dependencia de un estudio no publicado | R1 W5, R2 W1 | `text: §4.4 «La familia contiene ocho estrategias»` | R3 |

### Resumen de recomendaciones
| Revisor | Recomendación | Confianza | Promedio |
|---|---|---|---|
| EIC | Major | 4 | 58,8 |
| R1 Metodología | Major | 5 | 58,1 |
| R2 Dominio | Major | 4 | 61,1 |
| R3 Perspectiva | Major | 4 | 62,1 |
| DA | 1 CRITICAL, 4 MAJOR | — | — |

### Consenso
- **Todos (4/4 + DA)**: la transparencia sobre los límites es una fortaleza real. La redacción es clara (72 en todos).
- **EIC, R1 y DA**: el resumen y la conclusión son menos cautos que el cuerpo del texto.
- **R1 y R2**: el artículo no es autocontenido. Usa métodos y fuentes que no muestra: la familia de ocho estrategias y la matriz principal.

### Desacuerdos
**Severidad de la falta de Top-4 en la cascada.** EIC y DA la consideran crítica; R1 la trata como parte de un problema de presentación.
- **Resolución del editor**: se valida como crítica para la aceptación, pero **puede resolverse sin experimentos nuevos** reencuadrando el artículo. El título habla de «Top-k», no de «Top-4». Si el texto presenta k=4 como recomendación para el uso directo y la comparación con margen como evaluación de la Top-k dimensionada internamente, la promesa y la evidencia coinciden. La alternativa experimental (cascada con Top-4 sobre embeddings almacenados) fortalecería el artículo, pero no es imprescindible.

**Adjudicación de DA-C1**: **validada**. Bloquea la aceptación hasta que se aplique R1, sea por texto o por experimento.

### Fundamento de la decisión
Los cuatro revisores coinciden en Major Revision, con promedios entre 58 y 62. El artículo no tiene un defecto fatal: los datos están bien procedentes, la selección es anidada y las limitaciones están declaradas. Por eso no corresponde Reject. Tampoco alcanza Minor Revision, porque la coherencia entre título, diseño y conclusiones requiere reescribir el encuadre (R1). Hay que corregir cifras del resumen y de la conclusión (R2), y la estadística de la §4.6 debe recalcularse o completarse (R3). La mayoría de las revisiones pueden hacerse con los resultados ya guardados.

### Revisiones obligatorias
| # | Revisión | Severidad | Ancla | Fuente | Sección | ¿Requiere experimento? |
|---|---|---|---|---|---|---|
| R1 | Reencuadrar título, resumen, contribuciones y conclusión: k=4 es la recomendación para el uso directo; la comparación directo frente a margen usa la Top-k dimensionada internamente (k 1–8). Eliminar de la §6 la frase que atribuye a Top-4 la conveniencia de la activación por margen. | Critical | `text: §6` | EIC W1, DA-C1 | Resumen, §1, §3.3, §6 | No (opcional: cascada con Top-4) |
| R2 | Informar en el resumen y en la conclusión las medias de cinco datasets (cascada 0,9325, Top-k 0,9329), con KTH-TIPS2-b aparte. Quitar el aspecto destacado 5. Reemplazar «macro-F1 medio similar» por las diferencias concretas. | Major | `table: Tabla 7` | R1 W2, DA-M1, M2, M4 | Resumen, Aspectos destacados, §6 | No |
| R3 | Restringir la familia estadística a los métodos mostrados (Individual, Completa-22, Top-4) recalculando con los CSV existentes, o agregar el apéndice con las ocho estrategias. Describir GFS y la matriz principal en un apéndice. | Major | `text: §4.4` | R1 W5, R2 W1 | §4.4, §4.6, Apéndice | No (recalcular) |
| R4 | Explicar o aislar la discrepancia panel–estática en Soil y los cosenos del piloto en CUReT y Soil. | Major | `text: §4.8, §4.9` | R1 W4, W6 | §4.8, §4.9 | No (consultar a Joaquín) |
| R5 | Agregar declaraciones de conflicto de intereses, financiación y uso de IA. | Major | `absence: secciones finales` | EIC W3 | Final | No |
| R6 | Declarar en la §4.6 que Top-4 no pudo elegir el bloque de color, e informar la sensibilidad con k=3 y k=6 frente a Completa-22. | Major | `text: §3.3`, `table: Tabla 4` | R1 W1, R2 W4 | §4.5, §4.6 | No |

### Revisiones sugeridas
| # | Revisión | Severidad | Fuente | ¿Requiere experimento? |
|---|---|---|---|---|
| S1 | Párrafo sobre clasificación selectiva y medidas de confianza; justificar el margen. | Major | R2 W2, DA-M3 | No (solo referencias verificadas) |
| S2 | Percentil 95 de latencia por política, desde los `online_calls.csv`. | Major | R3 W1 | No (cálculo) |
| S3 | Declarar como alcance la proyección de costos con el perfil de Outex, y que el 69 % del piloto es la cifra medida. | Major | R1 W3 | No |
| S4 | F1 de la etapa barata sola en la ruta elegida, por dataset. | Minor | DA (alternativas) | No (cálculo con resultados guardados) |
| S5 | Memoria, lote unitario y cambio de distribución como alcance en §5.1. | Minor | R3 W2–W4 | No |
| S6 | Citas de RADAM y del repositorio de Soil; rehacer la Figura 1. | Minor | R2 W3, W5 | No |
| S7 | Matizar «se aplana alrededor de k=4» para ResMLP. | Minor | DA-m1 | No |

### Plan de revisión
**Prioridad 1: estructura (2–3 días)**
- [ ] R1 Reencuadre título/resumen/contribuciones/conclusión
- [ ] R2 Cifras de cinco datasets; aspectos destacados; lenguaje de pérdidas
- [ ] R3 Familia estadística y apéndice GFS/matriz principal

**Prioridad 2: contenido (2–4 días)**
- [ ] R4 Discrepancias del panel y del piloto (con Joaquín)
- [ ] R5 Declaraciones finales
- [ ] R6 Bloque de color y sensibilidad de k
- [ ] S1–S4

**Prioridad 3: texto y formato (1 día)**
- [ ] S5–S7
- [ ] Leyendas de las Tablas 5 y 7 (conjuntos de condiciones distintos)
- [ ] Decidir revista y traducción al inglés

**Esfuerzo total estimado**: 1–2 semanas sin experimentos nuevos.

### Ítems que necesitarían experimentos (fuera de alcance según la decisión de no correr más)
- Cascada con Top-4 fijo sobre embeddings almacenados (fortalece R1).
- Compuerta con otra medida de confianza (puntuación máxima o entropía) frente al margen (fortalece S1/DA-M3).
- Cascada con ResMLP (amplía R1 W7).
