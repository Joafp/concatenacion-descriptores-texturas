# Propuesta de tesis: fusión secuencial de descriptores de textura con utilidad predictiva y costo real

**Versión:** 1.1 — 8 de octubre de 2026; incorpora auditoría de la primera implementación.

**Estado:** prototipo implementado y 27 condiciones exploratorias guardadas; validación del método multietapa y de eficiencia real pendiente por defectos de implementación/evaluación.

**Nombre de trabajo:** FSC-Tex, *Fusión Secuencial Costo-consciente para Texturas*. Es un identificador interno, no una declaración de novedad.  
**Alcance de este documento:** elegir una dirección, definir su aporte verificable y preparar tareas para futuros subagentes. No autoriza por sí mismo lanzamientos, publicaciones, cambios de datos ni ejecuciones costosas.  
**Marco de revisión:** ARS, planificación metodológica y revisión crítica realizadas en esta conversación. No hubo revisión independiente ni certificación de originalidad. Las metas numéricas siguientes son propuestas de diseño, no resultados.

## 0. Actualización operativa: leer antes de continuar

Se auditaron los commits `2bf1604` y `136532c` y los artefactos de `results/exploratory/fsc_tex/phase3_full_suite/`. La auditoría detallada, con fuentes de código, comprobaciones y estadística, está en `docs/fsc_tex/AUDITORIA_FASE3_2026-10-08.md`.

**Qué se verificó:** existen 27 condiciones únicas; macro-F1 y exactitud recalculados desde 459 vectores de predicción coinciden exactamente con las métricas. Las etiquetas externas son compatibles con los manifiestos y particiones reconstruidos. Pasan las nueve pruebas unitarias existentes.

**Qué no se puede concluir:** que la Fase 3 del protocolo original esté completada, que se midió ahorro físico del 83 %, que H2 demostró planificación multietapa, o que el método superó a Completa-22, Top-k22 o GFS.

Hallazgos que cambian el orden de trabajo:

1. El presupuesto por defecto de 1, normalizado por ResNet, deja factible únicamente SigLIP. En inferencia solo se ejecutan las alternativas ResNet o ResNet+SigLIP; no se actualiza presupuesto restante.
2. Los objetivos futuros usan mínimos de pérdidas reales por muestra, equivalentes a decisiones oraculares retrospectivas, no al riesgo de una continuación desplegable.
3. «Completa» es una concatenación de seis bloques. RGB N-grams y otros 15 bloques de la biblioteca original están fuera de esta suite.
4. Los tiempos son sumas de constantes de perfiles anteriores y overhead supuesto. No se cronometró la nueva política imagen→predicción.
5. La mejor cascada se seleccionó en test; falta la validación interna completa que anuncia el encabezado del evaluador.
6. H2 lambda=0 obtiene 0,8887 frente a 0,9137 de Completa-6: pierde 2,50 p.p., no satisface el margen práctico de 0,5 p.p. DTD gana 9/10 frente a la cascada retrospectiva, no 10/10; FMD gana F1 pero consume más costo estimado.
7. H1 y H2 coinciden en las 22 condiciones de cuatro datasets. El contraste unilateral H2>H1 pasa de p=0,0216 al tratar folds como unidades a p=0,25 usando una media por cada uno de los seis datasets. Ambos son cálculos exploratorios, no una confirmación del mecanismo.

**Decisión:** preservar v1 como exploración; corregir y auditar antes de ampliar bases o repetir el barrido. La sección 12.0 define el nuevo camino crítico y tiene prioridad sobre el calendario inicial. No se modificó el código experimental ni se lanzaron entrenamientos durante esta actualización.

## 1. Decisión: esta es la línea que recomiendo

Recomiendo convertir la tesis de concatenación de descriptores en una tesis sobre **cómo construir una representación de textura progresivamente, decidiendo para cada imagen qué información adicional vale la pena calcular y cuándo dejar de hacerlo**.

La pregunta ya no sería «¿concatenar mejora a un descriptor individual?», sino:

> ¿Puede una política de adquisición de bloques, entrenada sobre su utilidad predictiva condicional y el costo incremental de ejecutarlos, mejorar el compromiso entre macro-F1 y latencia real frente a una selección estática y una cascada de dos etapas?

La representación sigue siendo una concatenación, pero **su composición y su costo dependen de la imagen, de los bloques ya observados y del presupuesto disponible**. Una imagen podría resolverse con un bloque económico; otra necesitar BEiTv2; otra justificar un extractor más costoso; y otra terminar sin adquirir más bloques porque el beneficio esperado no compensa el costo.

No recomiendo declarar a DynaTex ganador con la evidencia actual ni agregar atención, PCA o una compuerta y presentarlos como una contribución nueva. Tampoco propongo abandonar esos experimentos: son antecedentes y controles necesarios para justificar esta dirección.

### 1.1. Por qué puede constituir un tema de tesis

El problema reúne decisiones científicas y de sistemas que deben resolverse conjuntamente:

1. **Complementariedad dependiente de la imagen:** un descriptor globalmente fuerte puede no corregir los errores que quedan después de otro.
2. **Utilidad no necesariamente monótona:** añadir un bloque puede corregir algunas predicciones y perjudicar otras.
3. **Decisiones secuenciales:** un bloque poco útil inmediatamente puede orientar una adquisición posterior.
4. **Costos de ejecución heterogéneos:** dimensiones, parámetros y milisegundos no son intercambiables; el costo depende de lo ya calculado y del hardware.
5. **Validación bajo dependencia y selección adaptativa:** hay que evitar aprender rutas, presupuestos o umbrales a partir del test.

El aporte defendible sería **un método de adquisición por bloques implementable, una evaluación que aísle sus mecanismos y evidencia de cuándo mejora o no la frontera calidad–costo**. No basta con combinar componentes conocidos y darles un nombre.

### 1.2. Qué no se promete

- No se promete superar todos los papers ni ganar en los seis datasets.
- No se promete un porcentaje de ahorro o un valor p antes de ejecutar el protocolo.
- No se promete que la selección secuencial, la complementariedad o las compuertas sean ideas inéditas.
- No se promete una garantía de macro-F1 a partir de una regla de confianza por imagen.
- No se llamará ahorro de extracción a reducir únicamente el tamaño del clasificador final.
- No se llamará confirmatorio a reutilizar benchmarks cuyos resultados ya guiaron el diseño.

## 2. Punto de partida: qué existe y qué falta

Los archivos citados en esta sección son evidencia local del proyecto, no artículos revisados por pares. Las cifras históricas no deben copiarse como resultados del método propuesto.

| Línea existente | Qué aporta | Qué impide tomarla ya como solución principal |
| --- | --- | --- |
| Concatenación de 22 bloques, Individual, Top-k, GFS y Homogénea | Biblioteca, particiones y referencias predictivas | Selección generalmente estática; no decide el costo de extracción por imagen |
| DynaTex-MoD | Fusión aprendida y ponderación por familias | Necesita los bloques de entrada antes de ponderarlos; hay que igualar biblioteca, particiones y selección de hiperparámetros antes de proclamar ventajas |
| PCA+LDA con presupuesto dimensional | Representaciones compactas y selección de dimensiones | Compactar después de extraer no demuestra ahorro imagen→predicción; resultados mixtos |
| Cascada Top-k por margen y costo | Decisión de escalamiento y ruta directa cuando la cascada no conviene | Pocas decisiones; ahorro sensible al costo de la base y al umbral; algunas mediciones reales contradicen el costo estimado |
| Compuerta condicional de ganancia/costo | Ya predice qué ampliación conviene usando información disponible | Es un antecedente interno directo: no puede renombrarse como si fuera la nueva contribución |

### 2.1. Evidencia que orienta la elección

- El plan condicional ya documenta un predictor Ridge de ganancia/pérdida, con márgenes y una proyección de la representación base. «Predecir mejora por costo» **ya se probó** en el proyecto.
- Los oráculos retrospectivos muestran margen entre rutas, pero usan etiquetas verdaderas: sirven como diagnóstico de posibilidad, no como política desplegable.
- El avance de cascadas documenta ahorros reales en algunas condiciones y una ralentización de aproximadamente 31,6 % en una medición pequeña de KTH-TIPS2-b. Eso justifica modelar y medir el costo completo, no extrapolar desde la cantidad de bloques.
- Una mejora de atención frente a una referencia no implica mejora frente a la mejor referencia disponible. Tampoco un contraste global Iman–Davenport demuestra por sí solo que DynaTex supera a cada competidor.

Fuentes locales principales:

- `docs/PLAN_ADQUISICION_CONDICIONAL_TEXTURAS.md`.
- `docs/AVANCE_CASCADA_COSTO_CONSCIENTE.md`.
- `docs/PROPUESTA_FUSION_COMPLEMENTARIA_BUDGET.md`.
- `docs/INFORME_PROPUESTA_DYNATEX_PROFESOR.md`, que debe contrastarse con código y resultados, no tratarse como autoridad final.
- `src/dynatex_mod_classifier.py` y `scripts/run_dynatex_sci2s_tests.py`.
- `scripts/run_primary22_beitv2.sh` y `src/run_confirmatory_nested.py`.

### 2.2. Diferencia exigida frente a nuestro piloto anterior

La nueva línea debe superar la compuerta actual mediante **una política multietapa con parada explícita y costos incrementales medidos**, no simplemente cambiar Ridge por una red. Debe demostrar con ablaciones que mirar más de un paso o modelar el costo dependiente del estado aporta algo. Si no lo hace, se conserva la solución más sencilla y se informa el resultado negativo.

## 3. Antecedentes y frontera de novedad

La revisión realizada para este plan es dirigida, no sistemática ni exhaustiva. Se verificaron páginas primarias; para los antecedentes más cercanos se consultaron también las secciones indicadas. Una ficha bibliográfica o un resumen no equivale a lectura integral.

| Antecedente | Solapamiento relevante | Consecuencia para esta tesis |
| --- | --- | --- |
| [EDDI, ICML 2019](https://proceedings.mlr.press/v97/ma19c.html) | Adquisición de información mediante un modelo de observaciones parciales | No reclamar como nueva la elección del siguiente atributo |
| [Active Feature Acquisition: A Survey, versión 2026](https://arxiv.org/abs/2502.11067v2) | Organiza el problema de adquisición activa y sus familias metodológicas | Ubicar el trabajo dentro de AFA, no inventar una categoría sin antecedentes |
| [Explainability-driven ranking, ICML 2025](https://proceedings.mlr.press/v267/guney25a.html) | Aprende políticas secuenciales a partir de ordenamientos locales | Comparar con políticas aprendidas, no solamente con concatenación completa |
| [BRiG-AFA, preprint de agosto de 2026](https://arxiv.org/html/2608.02305v1) | Regresión supervisada de riesgo futuro mediante objetivos de Bellman | Es el antecedente algorítmico más cercano; una recurrencia de Bellman por sí sola no es aporte nuestro |
| [SynAFA, preprint de septiembre de 2026](https://arxiv.org/html/2609.32301v1) | Adquisición dependiente del estado, información conjunta y propuestas de pares | «Considerar sinergias» tampoco basta como novedad; debe medirse utilidad predictiva y no asumir que mayor información mejora al clasificador |
| [Learning-to-Measure, ICML 2026](https://proceedings.mlr.press/v306/kobayashi26a.html) | Adquisición guiada por incertidumbre con datos parcialmente observados | La incertidumbre es un antecedente, no nuestra contribución exclusiva |
| [Learn then Test](https://arxiv.org/abs/2110.01052) | Selección/calibración de procedimientos bajo control de riesgo | Inspira una extensión de validación; sus garantías no se trasladan automáticamente a macro-F1 o grupos dependientes |
| [Gated Multimodal Units](https://arxiv.org/abs/1702.01992) | Compuertas aprendidas para fusionar representaciones | La ponderación dinámica de familias debe presentarse como adaptación o componente, no como invención por sí sola |

**Hallazgo concreto:** BRiG-AFA declara en su formulación y limitaciones que sus experimentos usan costos unitarios y horizonte fijo; deja costos heterogéneos y parada para extensión. SynAFA informa resultados heterogéneos y una desconexión entre objetivos informacionales locales y utilidad predictiva. Esto motiva estudiar bloques de textura con costo físico y pérdida del clasificador, pero no demuestra que nadie haya resuelto ya esa combinación. Fuentes: secciones 3 y 7 de [BRiG-AFA](https://arxiv.org/html/2608.02305v1), y resumen, método y discusión de [SynAFA](https://arxiv.org/html/2609.32301v1).

### 3.1. Aporte candidato, formulado sin exagerar

> Extender la adquisición supervisada no miope a una biblioteca heterogénea de descriptores de textura, con decisiones de parada, costos incrementales derivados de la ejecución real y evaluación de la utilidad predictiva condicional, separando el efecto de la política del efecto del clasificador.

Lo distintivo que se intentará demostrar es **cómo cambia la decisión óptima cuando las acciones son extractores completos, tienen costos no uniformes y parcialmente reutilizables, y su incorporación puede perjudicar la predicción**. La contribución debe quedar respaldada por una formulación precisa, una implementación trazable y comparaciones directas.

Antes del experimento final, el responsable de literatura debe buscar específicamente adquisición por grupos/bloques, costos dependientes del estado, selección dinámica de expertos, cascadas, clasificación con presupuesto y adquisición no miope con parada. Si encuentra un método equivalente, se cita y se usa como referencia; se reformula el aporte como extensión o evaluación, no se oculta el antecedente.

### 3.2. Relación con los papers de textura entregados

Los PDFs de `docs/referencias/`, incluidos AsTexNet, HyTexNet, DeepLumina, métodos multiescala y selección/integración de características, deben entrar en una matriz de comparación con: tarea, datasets, protocolo, extracción, fusión, costo publicado, limitaciones y trabajo futuro literal con página.

**Pendiente:** esta propuesta no atribuye a todos esos artículos una misma recomendación de trabajo futuro. Tampoco supone que compartir el nombre de un dataset implique compartir particiones. Se debe incluir además la comparación pertinente con los papers de Electronics, Journal of Imaging y RGB N-grams usados en el proyecto.

## 4. Preguntas, hipótesis y criterios de refutación

| ID | Pregunta/hipótesis a contrastar | Qué la debilita o refuta |
| --- | --- | --- |
| H1 | La política mejora la frontera macro-F1–latencia respecto de la mejor selección estática elegida con entrenamiento | No mejora a igual presupuesto, o el ahorro desaparece al medir imagen→predicción |
| H2 | Mirar más de una adquisición aporta frente a la compuerta miope y la cascada actual | Horizonte 1 obtiene la misma calidad/costo dentro de la incertidumbre |
| H3 | El costo incremental medido cambia decisiones útiles frente a costos constantes o suma de bloques | No mejora la predicción de tiempo ni las rutas desplegadas |
| H4 | La complementariedad es suficientemente dependiente de la imagen | Un orden global fijo o una política que ignora los valores observados rinde igual |
| H5 | La ventaja se mantiene fuera de las condiciones que guiaron el diseño | Desaparece en datos no usados para desarrollar la política |

H1 es la pregunta principal. H2–H4 explican el mecanismo; H5 delimita la generalización. La posible mejora de macro-F1 con el mismo costo es una segunda vía de éxito: no se exige que toda mejora adopte la forma de «igual precisión, menos tiempo».

## 5. Método propuesto

### 5.1. Biblioteca y unidad de adquisición

Cada acción adquiere un **bloque descriptor completo**, no una dimensión aislada. La biblioteca candidata inicial conserva exactamente los 22 bloques del experimento principal:

- Clásicos: `lbp`, `drlbp`, `gabor`, `glcm`, `hog`.
- CNN: `resnet50`, `resnet101`, `vgg16`, `densenet121`, `efficientnet_b0`, `convnext_v2_t`.
- Transformers supervisados: `vit_b16`, `deit_s`, `swin_t`, `eva02_base`, `beitv2_base_final`.
- Autosupervisados y relacionados: `dinov2`, `dinov2_small`, `dinov2_large`, `mae_base`, `siglip_base`.
- Color secuencial: `rgb_ngram_svd`.

Esta agrupación sirve para organizar el registro, no para afirmar una taxonomía exhaustiva de los preentrenamientos. El registro debe guardar modelo, pesos, preprocesamiento, dimensión y hash. No debe cargar automáticamente todos los `.npy` encontrados: existen variantes y archivos exploratorios fuera de la biblioteca principal.

**RGB N-grams permanece elegible.** La parte aprendida, incluida SVD, se ajusta exclusivamente con entrenamiento del nivel correspondiente. Si aún no se reproduce un bloque online, se declara la limitación y se ofrece una comparación de soporte común; no se lo elimina silenciosamente ni se llama «22 bloques» a una biblioteca reducida.

### 5.2. Representación y clasificación

Para un conjunto adquirido S y una imagen x:

\[
z_S(x)=\operatorname{concat}_{j\in S}\;\phi_j(x),\qquad
\widehat y_S=f_S(z_S).
\]

El núcleo inicial utiliza SVM lineal por estado permitido, con normalización y búsqueda de hiperparámetros comunes a los controles. Esto aísla la contribución de adquirir información de la contribución de cambiar el clasificador.

ResMLP se evalúa después como réplica de generalidad con presupuesto de ajuste equivalente. Una versión de DynaTex capaz de manejar bloques ausentes es una **extensión opcional**, no requisito del núcleo. Multiplicar entradas ausentes por cero después de haberlas calculado no cuenta como omisión de extracción.

### 5.3. Estado observable

El estado de decisión contiene exclusivamente:

- Máscara de bloques ya adquiridos y operaciones ya ejecutadas.
- Valores/resúmenes de los bloques adquiridos; se permiten proyecciones pequeñas ajustadas solo con entrenamiento.
- Salidas del clasificador actual: margen, separación entre primeras clases y probabilidades solo si están calibradas válidamente.
- Presupuesto restante y costos incrementales estimados en el hardware objetivo.

La política **no** puede recibir etiquetas, embeddings de bloques no adquiridos, resultados futuros de una ruta ni metadatos que revelen clase o partición. Identificadores y grupos sirven para dividir y auditar, no como predictores.

### 5.4. Acciones y espacio de búsqueda acotado

Acciones principales: `STOP` o adquirir un bloque nuevo permitido. La ruta puede tener más de dos etapas. El conjunto de bloques crece; no se devuelve tiempo por retirar una característica ya calculada.

Para evitar enumerar los 2^22 subconjuntos:

1. El piloto usa un grafo pequeño de hasta 16 estados y hasta 3 adquisiciones posteriores a la base. Es un límite inicial de ingeniería, no un resultado científico.
2. Los candidatos se seleccionan usando solo entrenamiento, desempeño/costo y diversidad de errores; o se fija un grafo a priori para aislar la política.
3. La ampliación a hasta 32 estados requiere medir costo de entrenamiento, memoria y cobertura; no se expande porque un test haya salido mal.
4. Se incluye siempre una ruta de referencia estática elegida con entrenamiento. El sistema puede optar por ella **antes de pagar una base innecesaria**.
5. Los pares de bloques son una ablación opcional si el horizonte secuencial no representa bien complementariedades cortas. No se añade esta complejidad antes de validar el núcleo.

La biblioteca elegible sigue siendo de 22 bloques aunque una política de un fold utilice menos. Deben publicarse tanto los candidatos elegibles como los finalmente utilizados.

### 5.5. Utilidad: corregir y también evitar perjudicar

Definir una pérdida por imagen L_S(x,y), inicialmente error de clasificación ponderado por clase. Los pesos se calculan con entrenamiento y se normalizan para que la pérdida esté en [0,1]. La reducción observada al añadir a es:

\[
g(x,y,S,a)=L_S(x,y)-L_{S\cup a}(x,y).
\]

Un valor positivo indica mejora; uno negativo, perjuicio. El dataset de entrenamiento de la política debe conservar ambos, no solo los ejemplos corregidos. Se obtienen de predicciones fuera de muestra dentro del entrenamiento externo.

Como análisis secundario se puede usar log-loss con probabilidades calibradas; la elección entre pérdidas se congela usando validación interna. **No existe un macro-F1 individual aditivo**: macro-F1 se calcula sobre las predicciones del conjunto de evaluación. Optimizar esta pérdida sustituta no garantiza optimizar macro-F1.

### 5.6. Costo incremental de operaciones

Construir un registro de operaciones: lectura/decodificación, transformaciones, transferencia CPU/GPU, forward de cada extractor, transformación aprendida, concatenación, clasificador y compuerta. El costo incremental de una acción debe estimarse con las operaciones ya disponibles:

\[
\Delta t(a\mid S,r,\kappa)
=\text{tiempo adicional medido para adquirir a y actualizar el estado},
\]

donde r describe operaciones reutilizables y kappa el perfil de hardware/ejecución. La suma de tiempos aislados es solo un control simplificado; la latencia completa es la referencia de evaluación.

Dos modelos DINOv2 de tamaños distintos no comparten automáticamente un forward. Dos descriptores que usan escala de grises pueden compartir una transformación solo si la implementación realmente la reutiliza. La compuerta, los clasificadores intermedios y la sincronización también cuestan.

### 5.7. Política no miope con parada

Se propone adaptar el aprendizaje supervisado de valor futuro a un grafo de bloques, incorporando costo y `STOP`. La idea de aprender objetivos de Bellman proviene de antecedentes como BRiG-AFA; **no se presenta como invención nuestra**.

Una formulación de referencia, con horizonte restante h y presupuesto b, es:

\[
V_h(s,b)=\min\left\{
\widehat R_{\mathrm{stop}}(s),\;
\min_{a\in A(s,b)}\left[
\lambda\,\widehat{\Delta t}(a\mid s)
+\widehat{\mathbb E}\{V_{h-1}(s',b-\widehat{\Delta t})\mid s,a\}
\right]\right\}.
\]

`R_stop` estima la pérdida de emitir la predicción actual. La expectativa se aprende con transiciones y predicciones internas fuera de muestra; no se obtiene observando gratuitamente el bloque futuro en inferencia. El parámetro lambda tiene unidades coherentes de pérdida por milisegundo, o se normaliza explícitamente el tiempo por el costo de referencia.

La condición terminal es `V_0 = R_stop`; también se detiene si no queda ninguna acción factible. El costo hundido de los bloques ya ejecutados no se vuelve a cobrar. La evaluación del selector se cobra en cada decisión, incluida la última: se incorpora como costo común del estado o como evento explícito del ejecutor, nunca se omite por ser común a las acciones.

Implementación inicial:

1. Ajustar modelos de parada/ganancia de horizonte 1 con transiciones internas.
2. Ajustar horizontes 2 y 3 hacia atrás, congelando el horizonte previo al construir sus objetivos.
3. En inferencia, evaluar solo acciones factibles, ejecutar la elegida y repetir; el valor real del nuevo bloque aparece únicamente después de pagarlo.
4. Comparar con horizonte 1 utilizando idénticos predictores, estados y candidatos.
5. Registrar sobreestimación, daño y arrepentimiento respecto del oráculo diagnóstico; no confundir ese oráculo con un sistema implementable.

La máscara de factibilidad utiliza costos conservadores estimados. **Esto no garantiza un deadline físico duro**, porque la latencia varía. Se debe informar tasa de exceso de presupuesto y p95. Si se necesita tiempo real estricto, hará falta otro modelo de ejecución y admisión.

### 5.8. Parada y validación de riesgo

El núcleo usa parada aprendida y selección interna del punto operativo. Una extensión posterior puede calibrar una familia finita de políticas congeladas sobre datos independientes, siguiendo principios de control de riesgo. Debe identificar exactamente la pérdida controlada, las unidades independientes, la multiplicidad y los supuestos.

No se otorgará una garantía de macro-F1 usando una cota de error promedio. Si no hay suficientes grupos independientes, se informará validación empírica con incertidumbre; no se romperán grupos físicos para fabricar un conjunto de calibración. Cualquier reentrenamiento posterior a una calibración formal obliga a revisar su validez.

### 5.9. Flujo desplegable

```text
Imagen
  └─ Regla de entrada fijada con entrenamiento
       ├─ Ruta estática directa, si la política no compensa su sobrecosto
       └─ Bloque base → estado observable
                         ├─ STOP → predicción
                         └─ adquirir bloque permitido → actualizar estado
                                                       └─ repetir hasta STOP/límite
```

La regla inicial sin observar la imagen no puede ser personalizada salvo que mida un resumen visual; en ese caso, su extracción debe contabilizarse. El diagrama no concede información gratuita.

### 5.10. Configuración inicial para que los subagentes no improvisen

Estos valores son un punto de partida de desarrollo; cualquier cambio se registra antes de evaluar su efecto externo:

- Clasificador por estado: SVM lineal, pesos de clase balanceados, C en `{0.1, 1, 10}` mediante validación interna. La normalización debe ser idéntica en métodos comparados.
- Representación del estado: máscara de 22 posiciones, scores con orden de clases fijo y hasta 16 coordenadas de proyección aleatoria fija por bloque observado. La matriz de proyección se determina por semilla y dimensión, sin etiquetas ni ajuste a los datos, y es común a los folds. No se usa para reemplazar silenciosamente los bloques del clasificador. Una variante con PCA debe resolver explícitamente la compatibilidad entre bases de folds: no se pueden apilar como equivalentes coordenadas PCA con rotaciones distintas.
- Estimador de utilidad: Ridge regularizado como control. Para el núcleo, MLP pequeña de dos capas de 64 unidades, con máscara, identidad de acción y presupuesto como entradas adicionales; máximo 100 épocas y parada temprana usando solo datos internos factibles. No aumentar capacidad mirando el test.
- Horizontes `{1, 2, 3}`; evaluar lambda en `{0, 0.01, 0.05, 0.1, 0.25}` cuando el costo se normalice por el tiempo de la referencia. Congelar esta grilla o sus cambios después del piloto interno.
- Construcción del grafo: empezar por una base elegida con entrenamiento entre candidatos reproducibles; ordenar ampliaciones de los 22 bloques por utilidad interna y costo, retener rutas diversas y limitar estados. El algoritmo exacto de poda y desempate se fija en Fase 0. Una ablación con el mismo grafo fijo compara las políticas sin confundirlas con la búsqueda de estados.
- Cada estado se identifica por el conjunto de bloques, no por el orden de llegada; el estado de operaciones puede distinguir costos cuando el orden sí importe. No mezclar predicciones de clasificadores distintos bajo un mismo identificador de modelo.
- Semilla inicial de implementación: 42. Si se estudia variabilidad de entrenamiento, usar también 123 y 2026 para todos los modelos afectados; no seleccionar la mejor semilla.

No se presupone que esa MLP sea mejor que Ridge. Si no mejora con costo total comparable, se conserva Ridge. El objeto de estudio es la adquisición y no hacer más grande la compuerta.

### 5.11. Elección de la base: ni ResNet fija ni «el mejor F1» automáticamente

ResNet-50 es un **control fijo útil**, no la base definitiva. El descriptor con mayor F1 individual también debe ser un control, pero puede ser demasiado costoso para ahorrar después. La base principal se elige por el resultado de la **tubería completa de adquisición**, evaluada dentro del entrenamiento.

Dos bases con igual F1 pueden dejar errores muy distintos: una puede fallar en imágenes que otra ruta corrige fácilmente; la otra puede dejar errores irreparables. Por eso importan costo, incertidumbre utilizable y complementariedad posterior, además de calidad individual.

Protocolo de selección:

1. Auditar los 22 bloques y medir los costos sobre imágenes de entrenamiento y hardware común.
2. Obtener predicciones OOF de individuales y una frontera interna de calidad–costo. Mantener ResNet como control aunque quede dominada, y el mejor individual de calidad como referencia.
3. Retener un máximo inicial de tres bases de la frontera para construir políticas; este límite controla cómputo, no excluye bloques por resultados de test. SigLIP, BEiTv2-final y DINOv2-small son candidatos razonables a evaluar, no ganadores ya elegidos.
4. Entrenar y validar cada combinación base+política+presupuesto en los mismos folds internos, contabilizando base, compuerta, adquisiciones y fallback.
5. Elegir la configuración de menor costo que cumpla el criterio interno de calidad frente a una referencia fuerte. Si ninguna lo cumple, seleccionar la ruta estática directa y declarar que no hay ahorro aceptable.
6. Congelar la elección por dataset/partición de entrenamiento y punto operativo antes de test. No escoger retrospectivamente una base distinta según la etiqueta de cada imagen.

Formulación de selección empírica, no garantía estadística:

\[
(b^*,\pi^*)=\arg\min_{b,\pi}\widehat T_{\mathrm{val}}(b,\pi)
\quad\text{sujeto a}\quad
\widehat F_{1,\mathrm{macro,val}}(b,\pi)
\geq\widehat F_{1,\mathrm{macro,val}}(r)-\epsilon.
\]

La referencia r se escoge dentro del entrenamiento entre Individual fuerte, Completa-22, Top-k22 y GFS, según el objetivo/presupuesto. Cada uno se sigue reportando por separado en test. Si se usan intervalos para decidir, su cálculo y factibilidad se fijan antes; una desigualdad de estimaciones puntuales no prueba no inferioridad.

**Control crítico de unidades:** al comparar bases, usar presupuestos comunes en milisegundos o normalizados por la misma referencia r. No normalizar cada política por su propia base y mantener `budget=1`, porque eso da límites físicos distintos y reproduce el defecto de v1.

Comparación mínima de bases: ResNet fija; mejor individual por F1 interno; mejor individual bajo costo; base elegida conjuntamente con la política. No adquirir todos los candidatos para decidir qué base era barata.

### 5.12. Estrategia para competir con Completa, Top-k y GFS

Hay dos objetivos diferentes: **preservar calidad ahorrando costo** y **mejorar calidad a costo igual o menor**. El primero no demuestra automáticamente el segundo. La v1 todavía no alcanza ninguno frente a los comparadores principales de 22 bloques.

La ampliación prioritaria del método será una política de **adquisición por corrección residual, con rutas fuertes de respaldo**:

- Base elegida internamente como en 5.11, no una referencia débil para facilitar una ganancia aparente.
- Estado con scores identificados por clase y proyecciones fijas de los bloques observados, además de margen/máscara/costo. Esto permite distinguir tipos de error, no solo niveles de incertidumbre. Evaluar contra el estado de solo incertidumbre como ablación.
- Objetivos que modelen tanto corrección como perjuicio al añadir información, con pérdida balanceada y selección interna por macro-F1. El mínimo oracular no se usará como riesgo alcanzable.
- Candidatos de continuación elegidos por complementariedad interna, conservando elegibilidad de los 22 bloques y RGB N-grams ajustado por fold.
- Acciones de respaldo a Top-k/GFS u otra ruta fija fuerte: pagar únicamente los bloques faltantes, pero conservar también el costo hundido de la base y los pasos anteriores.
- Si la base no pertenece al subconjunto de la referencia, la clasificación de respaldo utiliza exactamente los bloques de esa referencia. No añadir la base a su vector y afirmar que se reprodujo el mismo clasificador.
- Regla de entrada capaz de optar por la referencia directa si el ahorro esperado no compensa base y compuerta. `STOP` se selecciona por validación de calidad, no solo por elevar lambda hasta que el sistema parezca rápido.

**Cómo podría mejorar F1 además de ahorrar:** un subconjunto especializado puede evitar bloques perjudiciales para cierto tipo de imagen y usar información complementaria en otras. Pero esto solo se sostiene si un enrutador puede identificar esos casos sin etiquetas externas. El oráculo muestra margen potencial, no que sea aprendible. Las rutas especializadas deben vencer también a la mejor ruta fija elegida internamente y a un enrutador que ignore el contenido observado.

En el siguiente piloto se fijan dos salidas, sin escoger después la que convenga:

1. Punto de eficiencia: margen de calidad epsilon=0,005 propuesto y ahorro físico objetivo >=20 % frente a r; además, comparación explícita contra la cascada fuerte.
2. Frontera calidad–costo: comparar los puntos de presupuesto congelados contra todos los controles. Una afirmación de mejora simultánea requiere diferencia de F1 favorable y menor latencia real, con incertidumbre y límites reportados.

No se incorporará todavía destilación, fine-tuning masivo ni una nueva arquitectura de fusión para tapar el problema de adquisición. Si una política válida no puede aprovechar el margen entre rutas, se documentará ese límite antes de abrir otra línea.

## 6. Entrenamiento y prevención de filtraciones

### 6.1. Contrato general

Para cada partición externa, mantener `T_train` y `T_test` separados desde el principio. El test no participa en elección de candidatos, construcción del grafo, selección del clasificador, ajuste de transformaciones, entrenamiento de la política, perfilado que modifique decisiones ni elección del presupuesto.

Se requieren dos niveles dentro de `T_train`:

1. **Validación de la tubería completa:** cada fold interno de validación queda fuera de todos los pasos de ajuste de la variante que se está evaluando.
2. **Predicciones para entrenar la política:** dentro del entrenamiento de ese fold, generar predicciones cruzadas de rutas para construir objetivos de corrección/perjuicio y valor futuro.

No basta con hacer OOF de los clasificadores si Top-k, PCA o el grafo se eligieron previamente usando también las etiquetas de sus filas OOF. Toda selección aprendida debe pertenecer al nivel de entrenamiento correspondiente. Para el primer piloto es preferible un grafo fijo, definido antes del ajuste, que una búsqueda grande difícil de auditar.

### 6.2. Pseudocódigo del evaluador

```text
para cada condición externa:
    obtener T_train, T_test desde manifiestos auditados
    para cada configuración candidata predefinida:
        para cada partición interna agrupada R / V:
            fijar un grafo a priori o definir su selector usando solo R
            para cada fold productor A / B dentro de R:
                ajustar selección aprendida, transformaciones y rutas solo en A
                producir estados/transiciones para B sin usar sus etiquetas al ajustar
            reunir transiciones con sus modelos y máscaras de procedencia
            entrenar política con esas transiciones
            ajustar clasificadores finales de las rutas usando R
            evaluar la tubería completa en V
        resumir macro-F1 y costo interno de la configuración
    seleccionar configuración y presupuesto con la regla congelada
    repetir ajuste completo usando T_train
    congelar modelos, registro, hashes y decisión de ruta directa
    evaluar una vez en T_test y guardar predicciones/trazas
```

El ajuste final sobre más datos puede cambiar la distribución de márgenes respecto de las predicciones cruzadas. Se debe medir esa sensibilidad dentro del entrenamiento; no asumir que desaparece. Una variante con calibración formal reservará además un conjunto independiente y no reentrenará después de calibrar.

Si la selección interna genera grafos distintos, no se inventan transiciones faltantes ni se reutilizan predicciones ajustadas con sus propias etiquetas. Se registra cobertura por estado/acción y se entrena una política condicionada por máscara con soporte suficiente; de lo contrario se reduce a un grafo fijo. La primera implementación debe preferir esta última opción hasta demostrar que el selector de grafos también se valida correctamente.

### 6.3. Pocos grupos: actuar de forma explícita

KTH-TIPS2-b, en la dirección tres muestras para entrenar y una para evaluar, tiene muy pocas muestras físicas por clase. No permite arbitrariamente cuatro reservas independientes grandes. El generador debe comprobar factibilidad real, conservar grupos y fallar con un mensaje si una configuración de anidamiento es imposible.

Alternativas válidas: reducir la grilla, fijar el grafo e hiperparámetros con datos de desarrollo ajenos a esa evaluación, usar anidamiento agrupado factible o declarar que no se puede sostener la garantía de calibración. **No es válido** sustituir silenciosamente división por muestra física por división aleatoria de imágenes.

### 6.4. Historial de exposición al test

Los seis benchmarks ya han sido inspeccionados durante el desarrollo. Congelar un método ahora mejora reproducibilidad, pero no borra esa exposición. Se llevará un registro `exposure_ledger` con datasets/particiones vistos y decisiones posteriores.

La fase final necesita, idealmente, datos o un dominio no usados en el diseño, escogidos por disponibilidad, licencia y protocolo antes de conocer resultados. El nombre se decide en la auditoría de datos, no se inventa en este documento. Si no se consigue, la conclusión se limita explícitamente a una evaluación retrospectiva exploratoria robusta.

## 7. Datos y condiciones experimentales

| Dataset canónico | Protocolo del proyecto que debe preservarse | Condiciones con semilla de partición 42 |
| --- | --- | ---: |
| DTD | Diez particiones oficiales; auditar duplicados y uso de train/val | 10 |
| FMD | Cinco folds agrupados; repetir otras semillas solo según plan | 5 |
| CUReT | A→B y B→A, sin tratarlas como datasets independientes | 2 |
| Outex13Official1360 | Una partición oficial de la versión RGB auditada | 1 |
| SoilOriginal | Cinco folds del manifiesto, preservando grupos cuando corresponda | 5 |
| KTHTIPS2b | Cuatro particiones; dirección invertida 3→1 del proyecto; agrupación interna por muestra física | 4 |
| **Total inicial** | Condiciones de evaluación, no 27 datasets independientes | **27** |

Ampliar FMD y Soil a semillas 42, 123 y 2026 da **47 condiciones por método**, antes de réplicas de inicialización. Las semillas de partición y de entrenamiento se registran por separado. Dos clasificadores no duplican el número de datasets para una prueba estadística.

Fuentes de embeddings esperadas, sujetas a auditoría:

- DTD: `embeddings/DTD`.
- FMD/CUReT: `embeddings_confirmatory/FMD` y `embeddings_confirmatory/CUReT`.
- Extensiones: `embeddings_extensions/Outex13Official1360`, `embeddings_extensions/SoilOriginal`, `embeddings_extensions/KTH-TIPS2-b`.
- Manifiestos: `results/confirmatory/sample_manifests/` y los directorios `sample_manifests/` de cada extensión.

Antes de correr: resolver rutas reales, contar filas/clases/grupos, comprobar alineación exacta imagen–etiqueta–embedding, finitud, hashes, procedencia y disponibilidad de imágenes fuente. La presencia de un embedding no demuestra que su extractor online sea reproducible. Un mensaje histórico sobre Outex pendiente no sustituye comprobar los archivos actuales.

## 8. Comparadores y ablaciones obligatorias

### 8.1. Comparadores internos

| Comparador | Qué controla |
| --- | --- |
| Mejor Individual elegido internamente | Necesidad de fusionar frente a un extractor fuerte |
| Completa-22 | Máxima biblioteca fija, con su costo completo |
| Top-k22 y GFS | Selección estática competitiva |
| Ruta fija de costo comparable elegida internamente | Que la ventaja no sea simplemente usar un subconjunto barato |
| Cascada por margen con opción directa y umbral seleccionado internamente | Valor añadido frente a lo más útil ya desarrollado |
| Compuerta condicional previa | Que la nueva propuesta no sea un renombramiento del piloto |
| Orden global, orden aleatorio y política sin valores observados | Necesidad de adaptación por imagen |
| DynaTex y PCA+LDA presupuestada | Alternativas de fusión/compresión, solo bajo biblioteca y protocolo armonizados |

Los resultados archivados sirven para regresión y contexto. Los contrastes causales entre métodos nuevos requieren reentrenamiento comparable, misma información disponible y presupuesto razonablemente equivalente de ajuste.

### 8.2. Comparadores externos cercanos

Se necesita al menos una adaptación reproducible de adquisición activa moderna al mismo problema. Prioridad: BRiG-AFA como referencia no miope, con versión de costos unitarios y adaptación explícitamente etiquetada. SynAFA o una referencia informacional constituye un control adicional si su implementación y dimensionalidad son viables.

Una adaptación por bloques no se presentará como reproducción exacta del paper original. Se conservará una prueba pequeña del comportamiento original cuando exista código utilizable, y se documentará cada cambio. Si no se logra una referencia externa suficientemente fiel, la comparación con el estado del arte queda pendiente; no se reemplaza por cifras publicadas con otro protocolo.

### 8.3. Ablaciones mínimas

1. Horizonte 1 frente a horizonte 2/3, mismos estados y modelos.
2. Costos unitarios, suma de costos aislados y costo incremental medido.
3. Parada aprendida frente a presupuesto fijo y frente a margen.
4. Estado con solo incertidumbre frente a incertidumbre más representación observada.
5. Política global por dataset frente a política dependiente de la imagen.
6. Biblioteca de 21 sin BEiTv2 frente a 22, y ablación sin RGB N-grams, sin convertir esta última en configuración principal silenciosa.
7. Opcional: acciones simples frente a pares y SVM frente a un clasificador con máscara/DynaTex.

No se ejecutará un factorial de todas las combinaciones. Las seis primeras preguntas se estudian con cambios de un componente respecto del método congelado; las opcionales requieren justificación del piloto.

## 9. Medición de eficiencia: de la imagen a la predicción

Separar tres niveles en todos los archivos y tablas:

1. `cached`: simulación de decisiones con embeddings precalculados; útil para investigar, no prueba ahorro real.
2. `profile_estimate`: costo estimado a partir de perfiles; debe validarse fuera de las imágenes utilizadas para ajustarlo.
3. `online_measured`: lectura/preprocesamiento según alcance declarado, extracción real, decisión y clasificación.

Protocolo online mínimo:

- Identificar CPU, GPU, RAM, versiones, precisión numérica, batch y residencia de modelos.
- Medir batch=1 como caso principal; throughput por lotes es otro experimento.
- Separar calentamiento/carga inicial de inferencia con modelos residentes; informar ambos si la aplicación requiere arranque en frío.
- Alternar o aleatorizar el orden de métodos en varias repeticiones, sin otros trabajos compitiendo por GPU.
- Sincronizar correctamente CUDA al medir; no usar solo el tiempo de envío de kernels.
- Informar media, mediana, p95, memoria pico, bloques ejecutados y exceso de presupuesto. Energía solo si se mide con instrumentación adecuada.
- Comparar exactamente las mismas imágenes. Un muestreo piloto de 30 imágenes no sustituye el benchmark final; tamaño final se fija con variabilidad y costo observados, nunca según dónde gane el método.
- Comprobar equivalencia de preprocesamiento, embeddings, decisiones de ruta y predicciones. Una ruta distinta cerca del umbral también es una discrepancia, aunque la clase final coincida.
- No recalcular una base adicional en el competidor estático si ese competidor no la necesita.

Las tolerancias numéricas se fijan por extractor antes de inspeccionar ventajas de rendimiento. Las desviaciones de ruta se cuentan y explican; no se aumentan tolerancias hasta que desaparezcan.

## 10. Plan estadístico y regla de decisión

### 10.1. Variables principales

- Calidad: macro-F1 externo; exactitud y resultados por clase como secundarios.
- Costo: latencia completa media y p95; la media permite cuantificar ahorro agregado, p95 revela colas.
- Efectos: diferencia pareada de macro-F1 y razón de latencias respecto de cada referencia.
- Frontera: puntos operativos fijados con entrenamiento; no escoger el mejor presupuesto con el test.

Puntos candidatos iniciales de presupuesto: 25 %, 50 %, 75 % y 100 % del costo de la ruta estática de referencia perfilada en entrenamiento. Si un punto es físicamente imposible, se informa como tal. La misma cota de presupuesto no garantiza que ambos métodos consuman lo mismo: informar consumo observado.

### 10.2. No inferioridad no es ausencia de significancia

Como criterio práctico inicial se propone tolerar una pérdida de hasta **0,005 de macro-F1, equivalente a 0,5 puntos porcentuales**, a cambio de al menos **20 % de reducción de latencia media** frente a la referencia estática. Son metas de ingeniería pendientes de ratificación, no umbrales universales ni hallazgos.

Para afirmar no inferioridad se necesita una inferencia compatible con esa hipótesis: por ejemplo, que el límite inferior de un intervalo válido para F1_nuevo−F1_ref quede por encima de −0,005. Un p>0,05 en una prueba de igualdad no lo demuestra. Un intervalo demasiado amplio produce «inconcluso».

Además se exige una ventaja frente a **la cascada actual**, no solo frente a Completa. Como filtro de continuidad del piloto, buscar al menos 5 % de ahorro adicional con calidad dentro del margen, o una mejora de calidad a costo comparable, en más de una condición de desarrollo. Ese filtro no equivale a significancia ni a confirmación.

### 10.3. Dependencia, multiplicidad y clasificadores

- Calcular diferencias pareadas con los mismos ejemplos y particiones. Usar remuestreo por grupos cuando esos sean las unidades independientes; no bootstrap de imágenes como si vistas de la misma muestra fueran independientes.
- Con muy pocos grupos, como en ciertos contrastes de KTH, reconocer que los intervalos y pruebas tienen resolución limitada. No fabricar certeza con miles de remuestreos de cuatro unidades.
- Entre datasets, resumir primero por dataset y clasificador. Para dos métodos considerar Wilcoxon pareado; para varios, Friedman/Iman–Davenport y contrastes posteriores definidos de antemano, con corrección de Holm cuando corresponda. Seis datasets implican baja potencia y alcance limitado.
- Los folds solapados, semillas e iteraciones de latencia no son datasets adicionales. Las repeticiones de hardware estiman ruido de tiempo, no generalización estadística.
- Separar SVM y ResMLP. Una comparación entre clasificadores debe ser un contraste propio con biblioteca y adquisición equiparables.
- No declarar superioridad por un omnibus significativo; identificar qué comparaciones lo sostienen. La orientación metodológica general sigue [Demšar, 2006](https://www.jmlr.org/beta/papers/v7/demsar06a.html).
- Si se usa SCI2S/Java, generar sus entradas desde resultados validados, guardar comandos/versión/salidas y contrastar con otra implementación cuando sea factible. No insertar medias manualmente en el script.

### 10.4. Posibles conclusiones legítimas

1. **Mejora comprobada:** ventaja calidad–costo frente a controles fuertes y evidencia del mecanismo.
2. **Ventaja limitada:** funciona solo bajo ciertos presupuestos, dominios o clases; se caracteriza ese límite.
3. **No aporta frente a la cascada:** se rechaza la complejidad extra y se publica el análisis comparativo; no se fuerza una conclusión favorable.
4. **Evidencia insuficiente:** potencia, acceso a datos o paridad online no permiten decidir; se informa qué falta.

## 11. Implementación prevista y contratos de artefactos

**Este árbol sigue siendo la arquitectura objetivo, no una certificación de que todo existe.** Al 8 de octubre existen `cost_model.py`, `utility.py`, `state_graph.py`, `policy.py`, registro/protocolo y scripts de fases 1–3; su cumplimiento está limitado por la auditoría de v1. Los módulos restantes y los contratos completos siguen pendientes. Reutilizar lo válido sin alterar resultados históricos.

```text
configs/fsc_tex/
  descriptor_registry_v1.json        # allowlist, pesos, transformaciones y hashes
  protocol_v1.yaml                   # splits, grillas, métricas y límites
src/fsc_tex/
  registry.py                       # bloques y operaciones permitidas
  state_graph.py                    # estados/acciones/factibilidad
  crossfit.py                       # transiciones internas sin filtración
  utility.py                        # pérdida, reparación y perjuicio
  cost_model.py                     # costos incrementales/perfiles
  policy.py                         # horizonte 1 y recurrencia con STOP
  executor.py                       # ejecución real bajo demanda
scripts/
  audit_fsc_tex_inputs.py
  run_fsc_tex_pilot.py
  run_fsc_tex_suite.py
  benchmark_fsc_tex_online.py
  report_fsc_tex.py
tests/
  test_fsc_tex_registry.py
  test_fsc_tex_no_leakage.py
  test_fsc_tex_policy.py
  test_fsc_tex_costs.py
  test_fsc_tex_online_parity.py
results/exploratory/fsc_tex/<version>/<dataset>/<condition>/
```

### 11.1. Contratos mínimos

| Artefacto | Campos/propiedades obligatorias |
| --- | --- |
| `run_manifest.json` | schema_version, commit y huella del árbol sucio, config_hash, registro_hash, dataset_hash, split_id, semillas, versiones, hardware, estado y fechas |
| `splits.json` | IDs de filas y grupos por nivel, hashes y resultados de controles de solapamiento |
| `state_graph.json` | estados canónicos, bloques, acciones, procedencia de selección y operaciones reutilizables |
| `transitions.parquet` | sample_id, fold productor, estado, acción, predicciones/pérdidas, objetivo, costo; solo entrenamiento y con procedencia verificable |
| `predictions.parquet` | sample_id, y_true, y_pred, scores, método, condición, presupuesto y modelo_hash |
| `traces.jsonl` | eventos reales de adquisición, estado anterior/posterior, costo previsto/medido, razón de parada y fallback |
| `metrics.json` | soporte/clases, macro-F1, exactitud, costos, uncertainty_method y modo cached/estimated/online |
| `audit.json` | integridad, agrupación, paridad, biblioteca, fallos y limitaciones; no aprobar si faltan controles |

Las trazas pueden contener etiquetas únicamente en el archivo de evaluación escrito por el evaluador; nunca se pasan al objeto de política. Los estados y acciones deben usar IDs estables para que un reporte pueda rastrear cada predicción hasta los modelos que la produjeron.

### 11.2. Pruebas que bloquean una corrida grande

1. Cambiar o permutar las etiquetas externas no modifica el ajuste ni las decisiones de adquisición.
2. Un extractor no adquirido lanza error si la política intenta leer su embedding.
3. No hay cruces de grupos entre entrenamiento y validación del nivel correspondiente.
4. SVD/PCA/escalado no acceden a filas reservadas.
5. Ningún bloque se cobra o ejecuta dos veces; una operación compartida se reutiliza solo cuando corresponde.
6. `STOP`, ausencia de acciones factibles, referencia directa y presupuesto imposible tienen comportamiento definido.
7. Un ejemplo sintético con complementariedad diferida distingue horizonte 1 de horizonte 2; otro sin complementariedad no crea ventajas ficticias.
8. Reiniciar reproduce resultados con las mismas semillas y no duplica condiciones.
9. Los reportes rechazan bibliotecas/splits distintos y condiciones incompletas en comparaciones pareadas.
10. La paridad online/cacheada se verifica antes de informar ahorro real.

## 12. Fases, entregables y puertas de continuidad

### 12.0. Camino crítico actualizado tras auditar v1

Estas tareas sustituyen la secuencia «medir online y redactar inmediatamente» sugerida por el reporte de Fase 3. No se ejecutan por el solo hecho de figurar en el plan.

| Orden | Trabajo | Entrega verificable | Puerta de avance |
| --- | --- | --- | --- |
| R0 | Preservar v1 y corregir su presentación | Manifiesto de archivo; reporte/generador con costos estimados, Completa-6, 9/10 DTD y selección retrospectiva visibles | Ninguna afirmación de garantía/latencia física respaldada solo por v1 |
| R1 | Corregir presupuesto, factibilidad y objetivos H2 | Presupuesto explícito decreciente; valor de continuación desplegable; pruebas de regresión | Una prueba alcanza >=2 adquisiciones reales; acciones imposibles no entran en objetivos ni inferencia |
| R2 | Implementar validación anidada de la tubería y trazabilidad | Configuración efectiva guardada, IDs/grupos, modelos, trazas, hashes y checkpoints compatibles | Selección de base, rutas, q y lambda sin leer test; pruebas de permutación de etiquetas externas |
| R3 | Comparar bases y controles fuertes | Individuales, base conjunta y referencias Completa/Top-k/GFS; biblioteca explícita | La ventaja no se explica por sustituir ResNet por un mejor descriptor solo |
| R4 | Piloto de adquisición residual con respaldo | Estado enriquecido, reparación/perjuicio, H1/H2 y ruta directa, con ablaciones | Cumple calidad/costo interno y supera controles; si no, detener expansión |
| R5 | Benchmark físico pequeño | Extracción bajo demanda, acuerdo de rutas/predicciones y tiempos pareados | La ventaja del simulador persiste contando overhead y fallback |
| R6 | Nueva suite congelada y análisis | Nuevo directorio `phase3_v2_*`, 27 condiciones; ampliación a 47 según plan previo | Auditoría metodológica y física completa antes de resultados principales |

Pruebas adicionales obligatorias que faltan en v1:

- Regresión del caso real: BEiTv2/DINO deben ser adquiribles cuando el presupuesto físico alcance; al cambiar base no cambia artificialmente el presupuesto permitido.
- El presupuesto baja en cada paso y también cubre clasificador/selector; no se restablece a 1.
- Con acciones futuras indistinguibles y aciertos opuestos, el modelo no aprende como alcanzable el error cero del oráculo.
- La continuación entrenada y la desplegada usan la misma máscara de factibilidad y unidades.
- `Full_Fusion_6` y `Full_Fusion_22` no pueden etiquetarse igual; bloque ausente/costo desconocido produce error visible, no una constante inventada.
- Una comparación del selector adaptativo incluye el mejor descriptor solo y la ruta estática ResNet+SigLIP, además de las referencias fuertes.
- El generador no contiene frases de éxito ni cifras de conclusiones codificadas manualmente; las afirmaciones dependen de resultados y del alcance del protocolo.

Asignación futura: el paquete C se responsabiliza de R1; A y C de R2; D de costos/paridad; E de reporte/estadística. El coordinador aprueba cada puerta antes de lanzar la siguiente. B mantiene la revisión de antecedentes sin certificar novedad por el nombre del método.

### Fase 0 — Auditoría y cierre del diseño

Entregables: registro de 22 bloques, inventario de fuentes, mapa de exposición al test, matriz de antecedentes cercanos y protocolo versionado. Revisar trabajo sucio y procesos activos antes de modificar nada.

**Avanzar si:** se identifica un aporte específico no presentado engañosamente como nuevo, hay datos alineados y al menos dos datasets pueden evaluarse online con las rutas piloto. Si no hay paridad de 22 bloques, delimitar explícitamente el soporte común del piloto.

### Fase 1 — Factibilidad dentro del entrenamiento

Usar inicialmente DTD y Soil como dominios de desarrollo; KTH como prueba explícita de generalización entre muestras físicas y viabilidad de anidamiento. Esta elección no los convierte en datos nuevos no vistos.

Medir con OOF: complementariedad, correcciones/perjuicios, margen del oráculo, costo de estados y capacidad de una política sencilla para predecir utilidad. No tocar tests externos para seleccionar acciones.

**Avanzar si:** hay margen predictivo y de costo en más de un dominio y la ventaja no depende de información no disponible. Si la referencia ya domina o el oráculo apenas puede mejorar, detener antes del barrido completo.

### Fase 2 — Piloto del mecanismo

Implementar horizonte 1 y 2/3, parada y costo incremental. Reproducir la cascada actual en el mismo evaluador. Validar primero con datos sintéticos y después con entrenamiento interno real.

**Avanzar si:** el método supera el filtro práctico frente a controles en validación interna, las mejoras no desaparecen al contabilizar compuerta y base, y las pruebas de no filtración pasan. Si solo mejora por un clasificador distinto, la evidencia no sostiene la hipótesis de adquisición.

### Fase 3 — Congelar y ejecutar los seis datasets

Congelar configuración, hipótesis, contrastes, puntos operativos y código antes del barrido. Ejecutar las 27 condiciones iniciales; extender a 47 solo si el presupuesto lo permite y según una decisión previa a inspeccionar resultados de esa ampliación.

Las semillas de inicialización sirven para estabilidad, no para escoger la mejor corrida. Registrar también fallos y rutas directas: no son automáticamente datos descartables.

### Fase 4 — Medición real y generalización

Medir las rutas en imágenes fuente con el protocolo online. Evaluar datos no utilizados para desarrollar el método si la auditoría logró incorporarlos con condiciones adecuadas. Mantener separado el resultado retrospectivo del resultado de esa evaluación nueva.

**Avanzar a afirmaciones de eficiencia si:** hay trazas de omisión real, paridad verificada y comparaciones equivalentes. Si el simulador gana y el sistema real no, se informa como fallo de transferencia del costo.

### Fase 5 — Estadística y escritura

Generar tablas desde predicciones; explicar mecanismo, incertidumbre, resultados negativos y límites. La contribución central será la decisión de adquisición y su evidencia, no una colección de nombres de modelos. Actualizar el paper únicamente con resultados auditados.

### 12.1. Plazo y recursos

Estimación organizativa inicial: 1 semana para auditoría/protocolo; 1–2 para piloto; 1–2 para implementación/evaluación; 1–2 para medición y análisis; 1 para escritura. Es un rango orientativo de **5–8 semanas**, condicionado a disponibilidad de datos, hardware y hallazgos; no un tiempo de cómputo medido.

El primer piloto debe producir tiempos por fold, memoria y cantidad de ajustes. Con eso se calcula el costo del barrido y se decide la ampliación. No programar de entrada cientos de entrenamientos ni competir simultáneamente por la misma GPU.

## 13. Organización para futuros subagentes

No se lanzan subagentes por la creación de este documento. Cuando se solicite implementar, el coordinador asignará trabajo con propiedad explícita de archivos y validará cada entrega.

### 13.1. Paquetes de trabajo

| Paquete | Responsable lógico | Entregable | Dependencias | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| A | Auditor de datos/protocolo | Registro, manifiestos y pruebas de no filtración | Ninguna | 22 bloques trazables, grupos y exposición documentados |
| B | Revisor de antecedentes | Matriz de novedad y contratos de baselines externos | Ninguna | Fuentes primarias, páginas/secciones y comparación específica, sin afirmar ausencia universal |
| C | Implementador de política | Grafo, transiciones, horizonte 1/2/3 y STOP | A; decisión metodológica de B | Pruebas sintéticas y validación interna sin test |
| D | Implementador de ejecución/costo | Perfilador, ejecutor y auditor de paridad | Registro A; interfaz C | Omisión real, costo completo y trazas reproducibles |
| E | Evaluador estadístico | Reporte pareado y auditoría de afirmaciones | C+D congelados y resultados completos | Métricas reproducibles, incertidumbre válida y límites explícitos |
| Coordinación | Agente principal | Integración, decisiones de continuidad y escritura | Todas | No cambiar hipótesis para acomodar resultados |

Olas sugeridas con hasta tres subagentes simultáneos: A+B y revisión del coordinador; luego C+D; después E y revisión crítica separada. Mantener un único propietario de la GPU. No usar el mismo directorio de salida para corridas distintas.

### 13.2. Reglas comunes de ejecución

- Leer instrucciones del repositorio y el documento vigente antes de actuar.
- Conservar cambios existentes; el árbol de trabajo no estaba limpio al redactar esta propuesta.
- No modificar resultados `ngram22_beitv2` ni reinterpretar sus archivos como resultados nuevos.
- Crear salidas versionadas y un manifiesto; escribir primero archivos temporales y finalizar de forma atómica.
- No hacer push, publicar, subir datos ni ejecutar servicios externos sin que forme parte del encargo vigente.
- No instalar paquetes o cambiar entornos compartidos sin documentar necesidad e impacto.
- No matar procesos de otros trabajos; usar reserva explícita de recurso.
- No leer métricas externas durante selección interna. Reportar cualquier exposición accidental.
- Reportar fallos completos, comandos exactos, semillas, tiempo y límites; un log sin error no equivale a experimento válido.
- Cada entrega incluye archivos, pruebas ejecutadas, resultados, asuntos pendientes y riesgos. Una revisión del mismo agente no se describe como independiente.

### 13.3. Encargos listos para adaptar

**A — Datos y protocolo**

> Audita las entradas de FSC-Tex siguiendo esta propuesta. No entrenes ni cambies datasets. Verifica los 22 bloques, alineación, pesos, transformaciones aprendidas, imágenes fuente, grupos, particiones y exposición previa al test. Propón el registro y pruebas de integridad. Entrega un inventario con evidencias y bloqueos; no declares listo lo que solo tiene embeddings pero no reproducción online.

**B — Novedad y comparadores**

> Revisa BRiG-AFA, SynAFA, antecedentes de AFA por grupos/costos/parada y los PDFs de textura del proyecto. Separa lectura de resumen de lectura completa. Para cada afirmación de trabajo futuro guarda pasaje breve permitido, página y fuente. Identifica solapamientos y qué extensión concreta seguiría siendo defendible. No prometas originalidad ni superioridad; recomienda al menos un comparador externo reproducible y explica sus adaptaciones.

**C — Núcleo de política**

> Implementa únicamente los módulos de grafo, utilidad, transiciones y política acordados tras A/B. Conserva SVM como clasificador inicial y el grafo acotado. Construye horizonte 1 como control antes de horizonte 2/3. La política solo puede leer bloques adquiridos. Añade pruebas de STOP, complementariedad diferida, daño y ausencia de filtración. No ejecutes el test externo ni el barrido completo.

**D — Ejecución real**

> Implementa perfiles incrementales y ejecución bajo demanda conforme al registro. Contabiliza preprocesamiento, transferencia, extractores, compuerta y clasificadores. Verifica equivalencia online/cacheada y registra discrepancias de ruta. No supongas reutilización entre modelos distintos. Reserva la GPU con el coordinador y entrega mediciones piloto pareadas, sin extrapolarlas como resultado final.

**E — Evaluación y estadística**

> Audita resultados congelados de FSC-Tex y baselines. Rechaza mezclas de biblioteca, split o modo de costo. Genera métricas desde predicciones, diferencias pareadas, incertidumbre según grupos y contrastes predefinidos separados para SVM/ResMLP. No confundir no significancia con equivalencia ni prueba global con superioridad individual. Documenta todas las desviaciones y resultados negativos.

## 14. Cómo debería cambiar la tesis si la propuesta funciona

Título orientativo: **«Fusión secuencial de descriptores de textura mediante adquisición adaptativa con costo de ejecución»**.

Estructura del aporte:

1. Problema: la fusión estática paga información redundante y no adapta la representación al caso.
2. Formulación: adquisición de bloques con parada y utilidad futura bajo costos medidos.
3. Método: construcción del estado, ajuste sin filtración y ejecución bajo demanda.
4. Evaluación: controles estáticos, cascada, AFA y ablaciones del mecanismo.
5. Discusión: en qué dominios la complementariedad paga su costo y en cuáles no.

PCA/LDA, DynaTex y las cascadas previas entrarían como antecedentes experimentales o comparadores. Sus resultados negativos se resumen para explicar decisiones, sin convertir el texto principal en una cronología personal de intentos.

Las rutas de adquisición ofrecen trazabilidad de decisiones. No son, por sí solas, explicación causal de la textura ni XAI validada. Para una afirmación de interpretabilidad se necesitarían intervenciones y evaluación específica; el problema de equiparar atención con explicación está discutido, por ejemplo, en [Serrano y Smith, 2019](https://aclanthology.org/P19-1282/).

## 15. Primeros pasos concretos al retomar

1. Leer la auditoría del 8 de octubre, revisar Git/procesos y preservar `phase3_full_suite` como exploración v1.
2. Resolver R1 y sus pruebas: presupuesto y valor futuro desplegable. No comenzar cambiando ResNet ni entrenando una red más grande.
3. Cerrar R2 y seleccionar bases conjuntamente con políticas usando solo validación interna y presupuestos físicos comunes.
4. Ejecutar un piloto contra individuales fuertes, ruta fija ResNet+SigLIP, cascada, Completa-22, Top-k22 y GFS con bibliotecas/alcance explícitos.
5. Confirmar adquisición multietapa y costo online antes de un nuevo barrido. No incorporar el reporte v1 al paper como conclusión validada.

**Conclusión de la propuesta:** esta es la dirección que recomiendo porque investiga cuándo adquirir y fusionar información, no solo cómo apilar vectores. Su mérito no dependerá del nombre ni de la complejidad del modelo, sino de demostrar una mejora reproducible frente a la cascada actual y a antecedentes de adquisición activa, o de establecer honestamente por qué esa mejora no se sostiene.
