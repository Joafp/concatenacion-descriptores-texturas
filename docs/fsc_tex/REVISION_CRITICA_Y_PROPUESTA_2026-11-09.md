# Revisión crítica y propuesta de enfoque — 09-11-2026

Documento de trabajo solicitado por Joaquín. Revisa la formulación científica
y propone un cierre experimental; no modifica el manuscrito, los planes
existentes, las fuentes selladas ni los resultados. No se ejecutaron fits,
extracciones o benchmarks para esta revisión. La extensión propuesta no es
un resultado obtenido ni una afirmación de novedad.

## Dictamen

La tesis tiene una base empírica defendible, pero no sostiene la afirmación
«inventamos un método único que es el mejor». Su aporte más sólido es estudiar
cuándo la selección estática y la adquisición por imagen producen un
compromiso útil entre macro-F1 y costo en una biblioteca heterogénea de
texturas. El texto actual ya reconoce antecedentes y separa poda de compuerta;
ese avance debe conservarse. El punto pendiente es cerrar la evidencia física
y competitiva de la nueva ruta de rescate de ensamble.

## Objeciones que plantearía un jurado

1. **La compuerta no establece novedad por sí sola.** La adquisición secuencial
   bajo presupuesto está documentada en Trapeznikov y Saligrama (2013). Nan y
   Saligrama (2017) aprenden un enrutamiento entre predictores con costos
   diferentes. Tampoco contar una sola vez cálculos compartidos basta para
   reclamar originalidad: Li et al. estudian dependencias computacionales de
   características. Estas coincidencias no demuestran identidad con nuestra
   implementación, pero sí descartan esas descripciones generales como
   justificación suficiente de novedad. Fuentes primarias al final.

2. **Mayor F1 no implica dominancia en calidad y tiempo.** En el panel común
   auditado, FMD/adaptativa-SVM obtiene 0,97760 y 38,63 ms frente a 0,94213 y
   16,89 ms de la adaptación Neshov BEiTv2+MLP. La diferencia de F1 favorece a
   la política local, mientras la media temporal favorece al comparador. Las
   latencias proceden de fechas distintas y hardware compartido: son
   descriptivas. No permiten generalizar una ventaja física universal.

3. **La referencia completa es insuficiente como principal rival de eficiencia.**
   Ahorrar frente a adquirir 22 bloques no prueba que la compuerta sea necesaria.
   Un subconjunto fijo o un único extractor fuerte puede ser competitivo.
   Ya existen una ablación del mismo rescate y un rival estático presupuestado:
   deben presentarse como evidencia central y ampliarse con familias estáticas
   pertinentes, no volver a describirse como trabajo inexistente.

4. **El aporte de la compuerta y el de la poda son diferentes.** En el piloto
   Outex/42 relevancia-B60, la poda reduce 69,76 % la adquisición proyectada;
   activar condicionalmente ese mismo rescate reduce otro 51,72 % respecto
   del rescate podado permanente y pierde 0,001251 de macro-F1. Los porcentajes
   son sucesivos, con denominadores distintos; no se suman. Ninguna de las
   ocho configuraciones con rescate del piloto mejora F1 al incorporar la
   compuerta. Eso no hace inútil la compuerta: puede ahorrar costo con una
   pérdida aceptable. La réplica además cambia de signo predictivo entre
   FMD y Outex. Debe estudiarse esa heterogeneidad.

5. **La evidencia del híbrido no hereda la cobertura del benchmark.** La
   introducción declara correctamente dos datasets de desarrollo, FMD y Outex,
   para la nueva ruta de rescate. Sus costos son proyectados. Las 94 condiciones
   físicas corresponden a las estrategias anteriores, incluida la cascada de
   referencia; no prueban automáticamente la latencia ni la generalización
   del híbrido. Semillas y pliegues compartiendo imágenes tampoco son dominios
   independientes. Los datos previamente observados siguen siendo exploratorios.

6. **Hay contradicciones materiales de alcance.** El resumen y el último
   párrafo de resultados de la conclusión afirman una validación frente a
   cuatro comparadores en seis datasets. La conciliación mantiene DeepLumina
   bajo revisión por no convergencia en las 46 condiciones terminadas y sin
   media DTD completa por un timeout. Las cifras observadas no desaparecen,
   pero no acreditan una réplica cerrada. La paridad de un componente tampoco
   acredita identidad del método, pesos, preprocesado y partición completos.
   Introducción y discusión son más cautas que ese cierre: hay que unificar
   la afirmación final con la cadena de evidencia antes de defenderla.

## Enfoque recomendado

**Título de trabajo:** «Cuándo conviene adquirir más descriptores: selección
y enrutamiento con costos compartidos para clasificación de texturas».

**Pregunta principal:** ¿Cuánto beneficio adicional aporta decidir por imagen
frente a seleccionar un subconjunto fijo, cuando ambas políticas utilizan la
misma biblioteca, tienen selección interna comparable y se evalúan con
latencia física y macro-F1 sobre las mismas llamadas?

**Objetivo operativo:** minimizar latencia media de extremo a extremo,
sujeta a una tolerancia predictiva definida antes de una evaluación nueva;
informar también latencia p95 y memoria residente. Una media dentro del
presupuesto no garantiza que todas las imágenes cumplan un límite.
La no inferioridad exige un diseño y un intervalo apropiados: una diferencia
puntual pequeña o un resultado no significativo no la prueban.

No es necesario abandonar lo desarrollado. Se conservan biblioteca, selección
de bloques, modelos, control estático, rescate, instrumentos de tiempo y
auditorías. El cambio principal es concentrar la tesis en una pregunta
comprobable y separar lo medido de lo proyectado.

## Extensión técnica acotada: predecir utilidad del rescate

La compuerta actual pregunta si el margen del predictor base es bajo. El
margen multiclase es la diferencia entre sus dos mayores puntuaciones; no es
automáticamente una probabilidad calibrada de acierto. Una base que duda no
implica que el rescate pueda corregirla, y una base confiada puede equivocarse.

La alternativa propuesta es aprender, con predicciones fuera de pliegue,
el beneficio esperado de activar el rescate:

`g(x) = P(base falla y rescate acierta | información base disponible)`
`       - P(base acierta y rescate falla | información base disponible)`

En entrenamiento, un ejemplo aporta +1 si el rescate corrige un error, -1 si
estropea un acierto y 0 si ambos tienen el mismo estado de acierto. Se aprende
una función barata a partir de puntuaciones, margen, clase predicha y, si se
justifica, rasgos ya adquiridos por la base. Los resultados del rescate se
usan para construir objetivos de entrenamiento, nunca como entrada disponible
antes de pagarlo durante la inferencia.

La política activa el rescate cuando el beneficio estimado justifica su costo
incremental. Este costo incluye los bloques del rescate que todavía no se
adquirieron, sus clasificadores y el propio enrutamiento. No se cuentan dos
veces los bloques reutilizados. La ganancia anterior es una diferencia de
probabilidades de acierto, no un cambio individual de macro-F1: este último
depende de matrices de confusión por clase. Cualquier ponderación o sustituto
de entrenamiento debe declararse y validarse con el macro-F1 real.

**No presentar esta extensión como una invención demostrada.** La predicción
del valor de usar un modelo más caro tiene antecedentes, por ejemplo Dynamic
Structured Model Selection (ICCV 2013). Su interés aquí sería comprobar el
beneficio adicional frente a nuestra compuerta de margen bajo costos de
extractores compartidos. Puede no superar al método actual; entonces se
conserva el resultado negativo.

## Experimento mínimo para decidir

| Control | Qué permite comprobar |
|---|---|
| Base sola y mejor extractor individual seleccionado internamente | Si el rescate aporta algo útil |
| Selección estática presupuestada, incluyendo concatenaciones pertinentes | Si una solución fija ya explica la eficiencia |
| Mismo rescate podado siempre activo | Cuánto aporta la poda |
| Mismo rescate con compuerta aleatoria a fracción de activación comparable | Si importa elegir las imágenes |
| Mismo rescate con compuerta de margen | Aporte del criterio actual |
| Mismo rescate con compuerta de utilidad | Beneficio de la extensión propuesta |

La ablación que aísla compuertas mantiene base, rescate, pesos y predicciones
potenciales fijos. La comparación competitiva permite selección interna propia
a cada familia bajo recursos comparables. No confundir esos dos experimentos.
Un límite que conoce la etiqueta y el resultado de ambos modelos puede ayudar
a diagnosticar el potencial, pero debe llamarse oráculo y no método desplegable.

Congelar antes de medir: versiones, representaciones, pesos, semillas,
particiones por muestra física, candidatos, presupuestos y tolerancias.
Aprender selección y compuertas dentro de los pliegues de entrenamiento.
Respetar las reservas KTH/DTD y no presentar como ciegos datos ya vistos.
Si no hay una evaluación nueva independiente viable, restringir las
conclusiones a la evidencia exploratoria; no fabricar independencia con otra
semilla.

Medir desde imagen a predicción, batch 1, una GPU y CPU de dos hilos, lock
global y ninguna extracción o fit concurrente. Comparar rutas en condiciones
temporales controladas, incluyendo residencia de pesos, sincronización,
transferencias, compuerta y clasificadores. Registrar F1 y tiempo de las
mismas llamadas, p95, tasa de rescate, correcciones, perjuicios por clase y
memoria. Guardar predicciones, errores y hashes en salidas nuevas. No repetir
el panel cerrado ni reintentar fallos científicos bajo esta propuesta.

Usar diferencias apareadas y una incertidumbre que respete imágenes/grupos
físicos y la dependencia entre particiones. Las seis semillas de dos datasets
no equivalen a seis datasets. Elegir un punto operativo por datos internos,
no por la mayor ventaja observada al mirar la evaluación.

## Criterios de cierre

- Si la compuerta ahorra latencia física con una pérdida dentro de la
  tolerancia predefinida y respaldada por la incertidumbre, se sostiene un
  beneficio condicional acotado al protocolo estudiado.
- Si la selección estática explica casi todo el ahorro y la compuerta no
  agrega una ventaja útil, se presenta ese resultado como conclusión central.
- Si la compuerta de utilidad supera a la de margen y al control aleatorio,
  se documenta esa mejora dentro del alcance evaluado; no implica dominancia
  universal ni establece originalidad por sí sola.
- Si la diferencia es incierta, no se declara equivalencia, no inferioridad o
  superioridad. Se informa el intervalo y el alcance disponible.

El cierre debe depender de resolver la pregunta y de la trazabilidad del
resultado, no de igualar porcentajes publicados ni de ganar todos los datasets.

## Evidencia interna revisada

- `paper/tesis.tex`: resumen y abstract; afirmación de validación externa.
- `paper/chapters/01_introduccion.tex`: preguntas, alcance y antecedentes.
- `paper/chapters/06_discusion.tex`: ablaciones, costos, dependencia y reservas.
- `paper/chapters/07_conclusion.tex`: resultados del piloto y réplica; cierre externo.
- `src/run_rescue_nested_selection.py`: umbral por cuantil OOF y margen base.
- `results/analysis/reconciliation_full_panel_20261104_v1/INFORME.md`:
  conciliación de llamadas y reserva DeepLumina.
- `docs/fsc_tex/PROPUESTA_GUION_Y_TABLERO_VERIFICADO_2026-11-04.md`:
  macro-F1, tiempos observados y distinción adaptación/réplica.

Las métricas anteriores se citan de sus documentos y llamadas auditadas; no
se recalculó ni amplió el benchmark para esta revisión.

## Antecedentes primarios consultados

- Trapeznikov y Saligrama (2013), [Supervised Sequential Classification Under
  Budget Constraints](https://proceedings.mlr.press/v31/trapeznikov13a.html).
- Nan y Saligrama (2017), [Adaptive Classification for Prediction Under a
  Budget](https://arxiv.org/abs/1705.10194).
- Li et al., [Large-scale Cost-aware Classification Using Feature Computational
  Dependency Graph](https://qingzheli.github.io/papers/TKDE_camera_ready_1015.pdf),
  DOI 10.1109/TKDE.2019.2948607; [código de los autores](https://github.com/qingzheli/ACAFH).
- Weiss, Sapp y Taskar (ICCV 2013), [Dynamic Structured Model
  Selection](https://openaccess.thecvf.com/content_iccv_2013/papers/Weiss_Dynamic_Structured_Model_2013_ICCV_paper.pdf),
  DOI 10.1109/ICCV.2013.330. Se consultó el extracto indexado del documento
  primario; su apertura directa devolvió HTTP 403. No se atribuye una
  verificación completa de su implementación.

Esta consulta dirigida identifica antecedentes suficientes para refutar una
afirmación amplia de exclusividad. No constituye una revisión sistemática
que certifique la novedad de la combinación propuesta.
