contract_role: domain
## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: warn
trigger: "incomplete contextualization of prior work needs correction but does not materially alter the central scientific interpretation."

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

La revisión de D2 mantiene el compromiso de Phase 1. Se leyeron completos los dos insumos de manuscrito, incluida la bibliografía y las tablas del PDF; se consultaron el índice y copias pertinentes de docs/referencias, las recetas Neshov, CellNN y DeepLumina, y la especificación local HyTex. Se contrastaron afirmaciones materiales con fuentes primarias públicas. No se consultaron informes de otros revisores ni revisiones históricas, ni se ejecutaron modelos o experimentos. La concordancia documental no sustituye una reproducción desde imágenes.

La contribución defendible es una comparación empírica situada de selección de bloques y activación condicional. El manuscrito no necesita demostrar prioridad mundial para sostener esa contribución. No encontré una falsedad técnica fundamental, una atribución que invalide la pregunta central ni fundamento para un bloqueo de D2. Los dos reparos siguientes son de contextualización y se resuelven mediante escritura. No convierto las reservas declaradas de procedencia, convergencia o exposición a benchmarks en defectos fatales cuando las conclusiones ya respetan esos límites. Las dimensiones ajenas a este asiento quedan sin puntuar; no se formula ajuste a criterios institucionales ausentes.

### S1: Contribución empírica delimitada frente a selección y cascadas conocidas

**Evidence Anchor**: text: paper/chapters/01_introduccion.tex:45, §1.6 — "Su contribución reside en esa comparación trazable sobre la biblioteca y los datasets evaluados"

La formulación reconoce que ranking y adquisición condicional tienen antecedentes y localiza el aporte en la comparación. La distinción entre selección de representación y decisión de adquirirla es consistente con la clasificación adaptativa de [Nan y Saligrama](https://proceedings.neurips.cc/paper_files/paper/2017/hash/d9ff90f4000eacd3a6c9cb27f78994cf-Abstract.html), que aprende compuerta y predictor bajo restricciones de costo. El método local por cuantiles de margen no se presenta como reproducción de ese aprendizaje conjunto.

**Confidence**: 5/5 — comparación directa entre la definición del aporte y el antecedente primario.
**Minimum Remedy**: Ninguno; conservar esta delimitación en resumen y defensa.

### S2: Definiciones correctas de margen, rescate y costo incremental

**Evidence Anchor**: text: paper/chapters/03_metodologia.tex:99 y 132, §§3.5–3.7 — "su predicción reemplaza a la base" y "Un bloque base se reutiliza únicamente si su representación coincide"

Las ecuaciones distinguen concatenación de voto, margen de probabilidad calibrada y adquisición proyectada de latencia física. El costo de la base se cuenta aun cuando no pertenece al rescate; descontar su bloque solo si coincide evita atribuir una reutilización imposible. También es correcta la advertencia de que el predictor condicional puede superar al directo al conservar aciertos de la base. La condición de ahorro de §6.3 se deduce del modelo declarado y trata explícitamente el caso de costo incremental cero.

**Confidence**: 5/5 — inspección de las definiciones y derivación algebraica de las ecuaciones.
**Minimum Remedy**: Ninguno; mantener los calificativos de adquisición proyectada y la exigencia de identidad de representación.

### S3: Adaptación y aproximación se distinguen de reproducción fiel

**Evidence Anchor**: text: paper/chapters/06_discusion.tex:42, §6.5 — "No demuestra que nuestras recetas reproduzcan íntegramente los artículos ni que las cifras publicadas sean incorrectas."

La descripción general de Neshov como agregación de capas seguida de MLP coincide con el [artículo primario](https://www.mdpi.com/2079-9292/14/23/4779); su Tabla 3 respalda el 96,7 % publicado para FMD. La combinación RGB/luminancia atribuida a DeepLumina coincide con [Simon y Uma](https://pmc.ncbi.nlm.nih.gov/articles/PMC9023203/). La fusión de LBP y contornos atribuida a Chang coincide con la [publicación de CellNN](https://www.sciencedirect.com/science/article/pii/S0957417423026027). Las recetas consultadas documentan elecciones locales en pesos, entradas, clasificador y partición. Que existan diferencias predictivas importantes no demuestra, por sí solo, implementación incorrecta ni refutación del artículo.

**Confidence**: 5/5 — contraste con publicaciones primarias y recetas locales identificadas.
**Minimum Remedy**: Ninguno sobre el alcance declarado; conservar los estados incompleto y no convergente al reutilizar las tablas.

### S4: Las variantes de descriptores conservan su identidad técnica

**Evidence Anchor**: text: paper/chapters/A_especificaciones.tex:78 y 82, §A.1 — "no una reproducción del DRLBP de Mehta y Egiazarian" y "Esta parametrización comprimida se identifica como N-gramas + SVD"

Se explicitan el truncamiento del histograma LBP-rot y el procedimiento de conteos, agrupación modular y SVD de N-gramas. La separación de bibliotecas de 20, dos variantes de 21 y 22 bloques impide atribuir al número de bloques un efecto que también cambia los candidatos. El texto no identifica ausencia de N-gramas en el ranking con falta de complementariedad, ni presenta como ejecutado el control Top-4 más N-gramas que reconoce pendiente.

**Confidence**: 5/5 — lectura de parámetros, ecuaciones y límites explícitos.
**Minimum Remedy**: Ninguno; mantener los nombres de variante en futuras tablas.

### W1: Faltan antecedentes próximos de integración y selección de métodos de textura

**Severity**: Minor
**Evidence Anchor**: absence: paper/chapters/02_literatura.tex:10–17, §2.2, y paper/articulo/borrador_profesor/references.bib — expected contextualización de selección de métodos de textura y compresión de descriptores combinados; checked capítulo 2 completo, bibliografía completa, docs/referencias/README.md y resúmenes de las copias locales Puig 2010 y Khan 2015
**Confidence**: 5/5 — ausencia comprobada en los insumos completos y antecedentes disponibles en fuentes primarias.
**Minimum Remedy**: writing — añadir un párrafo breve con ambos antecedentes y una comparación explícita de unidad de selección, protocolo y mecanismo de compacidad; no exige análisis nuevo ni experimento.

§2.2 explica wrappers mediante referencias generales, pero omite antecedentes que abordan de manera especialmente cercana la integración de varias familias y la selección de métodos de textura. [Puig, García y Meléndez](https://www.sciencedirect.com/science/article/abs/pii/S0031320310002062) seleccionan métodos de textura con un objetivo independiente de la aplicación; su problema y evaluación por píxel difieren de la selección local por dataset de esta tesis. La copia local de Khan et al., DOI 10.1016/j.patrec.2014.07.020, estudia combinación de descriptores y compresión de su representación; eso se distingue de seleccionar pocos extractores y de decidir su adquisición por imagen. Incorporarlos permitiría precisar el aporte sin ampliar las afirmaciones ni exigir ejecutar esos métodos. La omisión reduce contexto histórico, pero no invalida la contribución empírica ya acotada.

### W2: La identidad técnica de cada comparador queda demasiado fuera del manuscrito

**Severity**: Minor
**Evidence Anchor**: text: paper/chapters/02_literatura.tex:22, §2.3 — "Las dimensiones, checkpoints y cabezas utilizados en nuestras adaptaciones se identifican en las recetas del proyecto."
**Confidence**: 5/5 — comparación del capítulo, anexos completos y recetas locales consultadas.
**Minimum Remedy**: writing — incorporar una tabla compacta por comparador con representación/dimensión, peso/capa, cabeza, protocolo local y diferencias verificadas o no verificadas respecto de la publicación; enlazar la receta exacta y su versión. No requiere nuevas ejecuciones.

Las etiquetas de adaptación son correctas, pero el lector del PDF todavía debe salir del documento para saber qué sistema produjo cada columna. El anexo A especifica ampliamente los candidatos locales y GFS; no ofrece una ficha equivalente para los cuatro comparadores externos. Las recetas ya disponibles contienen información suficiente: Neshov usa 3.072 componentes de cuatro capas y una MLP propia; DeepLumina concatena dos salidas de 1.000 componentes con elecciones explícitas de peso y ECOC; CellNN fija entrada por canal B y una cabeza MLP concreta. Trasladar las distinciones materiales a una tabla facilitaría interpretar diferencias muy grandes sin atribuirlas a la idea original. Este reparo no demuestra un error de implementación, no exige alcanzar porcentajes publicados y no cuestiona las reservas que el manuscrito ya expresa.

