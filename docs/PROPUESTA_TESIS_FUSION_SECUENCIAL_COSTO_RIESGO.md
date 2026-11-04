# Propuesta de tesis: fusión secuencial de descriptores de textura con utilidad predictiva y costo real

## Actualización operativa — 25 de octubre de 2026

**Plan vigente: integración v11, [plan de cierre del 25-10](fsc_tex/PLAN_CIERRE_VIGENTE_2026-10-25.md).** La [reauditoría](fsc_tex/AUDITORIA_TESIS_Y_CIERRE_2026-10-25.md) verifica el benchmark estático, las predicciones históricas, los pilotos de integración y las mediciones físicas archivadas. Aprobaron 80 pruebas; se reprodujeron las 36 selecciones/13 resultados del híbrido y el pool emparejado. No se reentrenó hoy. La [reestructuración editorial posterior](fsc_tex/REVISION_EDITORIAL_APLICADA_2026-10-25.md) organiza el manuscrito en siete capítulos y anexos (54 páginas), separa método y diseño e incorpora pseudocódigos, diagrama y curva desde datos guardados; `paper/tesis.pdf` describe ya el ensamble de diversidad como rescate, pero **no está cerrado experimentalmente**.

El [ensamble de Carlos como rescate](fsc_tex/CARLOS_RESCATE_HIBRIDO_OUTEX_2026-10-21.md) sigue evaluado únicamente en el piloto de desarrollo Outex: relevancia/60 obtiene F1 0,910742 y 53,316 ms proyectados, frente al ensamble permanente 0,914389/365,196. No lo supera en calidad ni demuestra ahorro físico. El próximo control es el mismo rescate podado siempre activo frente a su versión con compuerta. Después corresponden réplicas, sensibilidad de bases/controles y medición física del híbrido. Se conservan seis datasets, 22 bloques principales y la evaluación histórica; sus coberturas no se atribuyen al piloto nuevo.

La contribución candidata es la selección conjunta bajo presupuesto medio proyectado. P0, P1-A y P1-B están implementados; sigue P2, validar estabilidad, cumplimiento fuera de muestra y bases, además de completar controles. El [piloto corregido de pool emparejado](fsc_tex/POOL_EMPAREJADO_OUTEX_2026-10-21.md) terminó y pasó sus auditorías: Outex/120 ms con color obtiene 0,906690/83,772 ms con regla marginal y 0,907233/89,325 con relevancia, frente a Completa-22 0,913957. La cifra 0,909417 pertenece al pool anterior desigual y no sustituye esta comparación corregida. FMD muestra ventajas cambiantes por presupuesto. Esto respalda continuar investigando, no una conclusión de superioridad. La tesis conserva seis datasets y 22 descriptores principales; los pilotos no reemplazan sus tablas.

**Registro histórico:** versión 1.8 — 18 de octubre de 2026, referencia `5685be3`. El orden actual está en integración v11; las observaciones de fidelidad físico/cache de CUReT y Soil siguen pendientes.

## Registro del plan de cierre — 18 de octubre de 2026

Este bloque conserva el estado histórico de cierre. Para ejecutar trabajo nuevo rige integración v11; los pendientes de fidelidad aquí descritos se mantienen como requisitos de validación física. La especificación histórica está en [PLAN_CIERRE_TESIS_2026-10-18.md](fsc_tex/PLAN_CIERRE_TESIS_2026-10-18.md).

**Objetivo:** cerrar una evaluación trazable del compromiso calidad–costo de la cascada adaptativa, sin presentar coincidencia de predicciones como identidad de representaciones ni ausencia de significancia como equivalencia.

**Ya terminado:** evaluación predictiva archivada de 27 condiciones en seis datasets; piloto físico en los seis (204 imágenes, 612 parejas de mediciones); cuatro folds Top-k SVM de KTH con agrupación interna por muestra; actualización de tesis, ZIP, presentación y guion. Los registros físicos de CUReT y Soil tienen discrepancias de fidelidad; completar corridas no las resuelve.

**Secuencia vigente:**

1. Auditar y resolver la fidelidad físico–caché de CUReT y Soil con comparación controlada de extracción. No atribuir causalidad al pooler o a la interpolación sin evidencia reproducible.
2. Reconciliar la cascada KTH con los cuatro controles Top-k corregidos, verificando selección interna, particiones y transformaciones. No sustituir únicamente cifras en una tabla.
3. Recalcular métricas y contrastes únicamente desde variantes reconciliadas; conservar la exclusión inferencial de KTH hasta cumplir ese criterio.
4. Determinar el alcance físico: conservar el piloto de una condición por dataset o ampliar a las 27 condiciones. Medir Completa/GFS si se afirma ventaja física frente a ellos.
5. Sincronizar tesis, tablas, figuras, presentación, guion, dossier y auditoría; revisar particularmente afirmaciones de reproducibilidad, saturación y prospectividad.
6. Compilar y verificar PDF/ZIP, ejecutar pruebas pertinentes y registrar hashes y entorno para la entrega.

VisTex permanece fuera del manuscrito. No se añaden arquitecturas ni datasets nuevos en esta fase. El primer trabajo ejecutable es el diagnóstico de fidelidad, no repetir las seis corridas indiscriminadamente.

## Archivo histórico de diseño y decisiones (hasta 12-10-2026)

Las referencias siguientes a Top-k KTH faltante, piloto exclusivo de DTD o suite en ejecución describen estados anteriores y no son el estado vigente. Se conservan como trazabilidad del proceso.

### Actualización de inventario y alcance: VisTex

Verificación local: el original de VisTex ya está disponible. La colección Reference contiene **167 imágenes en 19 categorías**. VisTexReference12 conserva **140 imágenes de las 12 categorías con al menos 7 ejemplos**; no es un dataset independiente ni una reconstrucción sin originales: los 140 hashes del manifiesto coinciden con las imágenes originales presentes.

La extensión histórica dispone de **20 descriptores y 19.628 dimensiones**, no de la biblioteca principal de 22/20.652. No contiene BEiT-v2 ni RGB N-grams+SVD, y su resumen no incluye Top-k ni la cascada. Sus 15 particiones repetidas por clasificador no son 15 datasets independientes. Las rutas del manifiesto histórico están obsoletas (0/140 existen), aunque las fuentes se recuperan por categoría, nombre y SHA-256 en `data/confirmatory_sources/VisTex/extracted/VisionTexture/VisTex/Images/Reference`.

**Decisión del autor (12-10-2026): no incorporar VisTex todavía.** Se conservan los seis datasets principales; VisTex queda únicamente en el inventario y como evaluación histórica archivada. La falta de partición oficial no invalida por sí sola un benchmark: para una eventual incorporación se requiere fijar un protocolo válido, completar los dos descriptores faltantes, evaluar los mismos métodos y preservar independencia entre imágenes fuente y eventuales recortes. La colección completa tiene categorías de solo dos ejemplos; no trasladar automáticamente el esquema de cinco pliegues del subconjunto.

**Orden de trabajo actualizado:** (1) cerrar Top-k corregido de KTH y procedencia de los experimentos principales; (2) reconciliar la evidencia de discrepancias físico/caché entre el plan y el memorando; (3) ampliar la medición física si se ejecutan nuevos experimentos. VisTex queda fuera del manuscrito por decisión del autor y no se programan nuevas corridas para esa colección. Añadir datasets no sustituye la validación de la contribución costo-consciente.

Detalle y propuesta textual: [actualización ARS y resumen de tesis](fsc_tex/ACTUALIZACION_ARS_VISTEX_Y_ESTADO_2026-10-12.md). Esta actualización documental no modifica predicciones, métricas, particiones ni el PDF previamente compilado.

**Estado (12-10-2026):** Cascada con etapa económica seleccionada priorizada como candidata; escritura de resultados auditados habilitada en paralelo al cierre metodológico. La persistencia de predicciones de 27 condiciones y el piloto físico pareado en DTD/RTX 4060 (47 imágenes; 68,7% menos latencia; razón de sumas 3,19× frente a Top-k) están completados. Se corrigió el manuscrito: las cifras inferenciales sobre 27 particiones dependientes y el resumen físico multiconjunto de 136 imágenes se excluyen; el protocolo de latencia y los límites de reproducibilidad se ajustaron a los registros existentes. No están demostradas equivalencia predictiva, superioridad global ni eficiencia física en todos los datasets. La procedencia de las cuatro particiones de KTH quedó mapeada, pero la variante corregida carece de resultados Top-k para folds 1–3; siguen pendientes la trazabilidad completa de esa variante y la validación interna de los nuevos mecanismos. ROCF no tiene artefactos verificables localizados en esta revisión.

**Nombre de trabajo:** FSC-Tex, *Fusión Secuencial Costo-consciente para Texturas*. Es un identificador interno, no una declaración de novedad.  
**Alcance de este documento:** elegir una dirección, definir su aporte verificable y preparar tareas para futuros subagentes. No autoriza por sí mismo lanzamientos, publicaciones, cambios de datos ni ejecuciones costosas.  
**Marco de revisión:** ARS, planificación metodológica y revisión crítica realizadas en esta conversación. No hubo revisión independiente ni certificación de originalidad. La sección 0 identifica resultados comprobados; las metas del diseño inicial se conservan como criterios, no como resultados alcanzados.

## 0. Actualización operativa: leer antes de continuar

### Cobertura de la cascada (comprobada el 12-10-2026)

La evaluación predictiva archivada ya cubre los seis datasets: DTD 10 condiciones, FMD 5, CUReT 2, Outex13Official1360 1, SoilOriginal 5 y KTHTIPS2b 4. No falta iniciar la cascada en cinco datasets: falta completar su validación física comparable y resolver la referencia corregida de KTH.

Solo DTD dispone del piloto físico pareado detallado de 47 imágenes identificado para esta cascada. El script `scripts/benchmark_cascade_physical_pareado.py` no es un ejecutor universal: fija `embeddings`, el manifiesto de `results/confirmatory` y `official_split_indices`, y construye nombres `officialN`; los otros datasets requieren sus raíces, protocolos y selecciones propias. No lanzar cambiando únicamente `--dataset`.

Para ampliar la afirmación de ahorro real a los seis datasets se requiere medir cada uno bajo un protocolo común, conservar observaciones por imagen y repetición, controlar el orden y validar la fidelidad físico/caché. Completa y GFS necesitan medición propia si se comparará eficiencia física contra ellos. Las selecciones y umbrales deben mantenerse fijados desde entrenamiento, sin escoger variantes por los resultados del test. VisTex no forma parte de este trabajo.

El memorando se corrigió: la interpolación es una explicación pendiente de respaldo reproducible, no una causa ya demostrada. Las mediciones originales permanecen intactas.

**Ejecución autorizada:** se implementó y lanzó un [piloto físico para los seis datasets](fsc_tex/VALIDACION_FISICA_SEIS_DATASETS_2026-10-12.md), con una condición fija por dataset, una imagen por clase y tres repeticiones pareadas aleatorizadas. Salida nueva: `results/exploratory/fsc_tex/physical_six_20261012`. Su estado debe comprobarse en los registros; lanzamiento no equivale a validación completada. No reemplaza el piloto previo ni resuelve la referencia corregida de KTH.

Estado ARS **ANALYZED**: revisión local de código, artefactos y procedencia, con recálculo de métricas desde predicciones y mediciones guardadas; no reentrenamiento independiente ni certificación de originalidad. El corte incorpora `2ab97f5` (persistencia) y `e0d3564` (benchmark físico), posteriores a la auditoría hasta `08c3ebb`, más el árbol local con cambios preexistentes. El hash de HEAD no identifica por sí solo todos esos cambios sin commit. Actualizar el plan no equivale a certificar todo el pipeline ni a declarar cerrada la fase experimental.

- [Auditoría P0–P4/cascada hasta 08c3ebb](fsc_tex/AUDITORIA_P0_P4_CASCADA_2026-10-10.md): sus pendientes de persistencia y piloto físico se actualizan aquí, sin alterar el registro histórico.
- [Resultados internos P1–P3 y piloto físico P4](fsc_tex/RESULTADOS_PILOTOS_2026-10-10.md).
- [Reporte auditado de la cascada seleccionada](fsc_tex/REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md).
- [Predicciones por condición](../results/exploratory/topk_cascade/cheap_stage_selected_primary22/) y [generador de persistencia](../scripts/generate_cascade_predictions.py).
- [Mediciones físicas por imagen](../results/exploratory/fsc_tex/cascade_physical_paired_benchmark.json) y [ejecutor del benchmark](../scripts/benchmark_cascade_physical_pareado.py). El [reporte físico](fsc_tex/REPORTE_BENCHMARK_FISICO_GPU_CASCADA.md) requiere ajustar la interpretación del speedup y de la fidelidad; usar las precisiones siguientes al escribir.
- [Documento de transición a escritura, corregido](fsc_tex/CIERRE_FASE_EXPERIMENTAL_Y_DECISION_FINAL_2026-10-11.md). No es una certificación de cierre ni de novedad.
- Historia: [auditoría v2](fsc_tex/AUDITORIA_FASE3_V2_2026-10-10.md), [reporte v2](fsc_tex/FASE_3_V2_REPORTE_SUITE_COMPLETA.md) y [v1](fsc_tex/AUDITORIA_FASE3_2026-10-08.md). No sobrescribir sus predicciones.

**Avances comprobados desde v2:**

| Componente | Estado real |
| --- | --- |
| Registro 22 | Emparejamiento y fuentes corregidos; Completa/GFS 27/27, Top-k 24/27. Faltan KTH 1–3 en la variante corregida |
| P1/P2 | DTD y Soil en entrenamiento; seis individuales, tres bases diagnósticas y políticas con ResNet/SigLIP; a 45/75 ms aparecen ≥2 adquisiciones |
| P3 | Presupuesto coherente en las rutas inspeccionadas; PCA y permutación siguen sin validar el pipeline completo |
| P4 histórico | Piloto FSC sobre 20 imágenes DTD de banded; rutas 90%/predicción 95%. Se conserva separado del nuevo benchmark de cascada |
| Cascada seleccionada / A7 | 27 archivos de predicciones; 31.984 observaciones de test acumuladas entre particiones, no necesariamente imágenes únicas. Se recalcularon 81 valores de macro-F1 (tres métodos × 27) sin diferencias con los resultados archivados |
| Benchmark físico nuevo | DTD official1, una imagen por cada una de 47 clases, RTX 4060; cascada y Top-k sobre las mismas imágenes. Media 88,75 frente a 283,33 ms, reducción 68,7%; no mide Completa/GFS ni los otros datasets |
| Paridad físico/cache | Rutas 45/47 (95,74%) y predicciones 46/47 (97,87%) para ambos métodos. Supera el umbral piloto ≥95%, no es identidad exacta; hay discrepancias pendientes |
| ROCF y novedad | Afirmaciones presentes en el documento de cierre, pero sin resultados, configuración y ejecución ROCF localizados ni evidencia suficiente para un dictamen universal de originalidad |

**Resultados actuales, sin mezclar experimentos:**

- La suite histórica v2 conserva H2=0,918317 y Completa-6=0,934073 (media por dataset), con máximo una adquisición posterior a la base. No fue reentrenada.
- Los pilotos nuevos permiten varias adquisiciones, pero no muestran una ganancia sistemática H2 frente a H1/cascada. Son estimaciones internas de desarrollo con reutilización de datos de sintonización.
- La cascada seleccionada registra macro-F1 medio descriptivo de 0,934505 frente a 0,934091 del Top-k de origen, **0,940916 de Completa-22** y aproximadamente 0,9353 de GFS-22 (igual peso por dataset). Gana descriptivamente a Top-k en cuatro datasets y pierde en CUReT/Outex; esto no prueba ventaja global. La reducción de costo de 75,5% sigue siendo **proyectada**, no un cronometraje multidataset.
- El mapa de procedencia de las cuatro particiones de KTH está documentado: la diferencia de Top-k en fold 4 se asocia con la agrupación física de la validación interna y los folds 1–3 no tienen resultados de la variante corregida. El Top-k archivado se conserva como referencia descriptiva de otra variante y KTH se excluye de los contrastes conjuntos ($N=5$). Por tanto, el mapeo está resuelto, pero la referencia numérica de KTH no está completada ni puede mezclarse con el registro corregido.
- La inferencia de calidad usa los cinco datasets reconciliados: Friedman p=0,4518, Iman–Davenport p=0,4922 y los tres contrastes bilaterales ajustados por Holm p=1,0000. Las diferencias medias son −0,000397 frente a Top-k y −0,004567 frente a Completa-22. No se usan Wilcoxon sobre las 27 particiones repetidas como inferencia, ni se interpreta la falta de rechazo como equivalencia o no inferioridad.
- El piloto físico obtiene aceleración agregada `sum(t_topk) / sum(t_cascada) = 3,1923×`; **15,9784× es la media de cocientes por imagen**, una magnitud distinta. Los dos métodos físicos predicen lo mismo en 47/47 imágenes y aciertan 41/47; esa concordancia local no demuestra equivalencia poblacional.
- El cronómetro comienza con la imagen RGB ya decodificada y modelos residentes. Incluye la ejecución bajo demanda hasta la predicción, pero no lectura/decodificación del archivo ni carga inicial de modelos. Se usó orden fijo cascada→Top-k, una pareja por imagen, sin repeticiones aleatorizadas. El ahorro solo describe ese protocolo.
- Se encontró un resumen de latencia de 136 imágenes en cinco datasets, pero no sus mediciones por imagen ni un log de ejecución. Se excluye como evidencia del manuscrito. La media ponderada de sus cifras resumidas daría 71,4% y 3,50×, no los 76,0% y 4,17× publicados; el recálculo aritmético no verifica la medición original.
- Los vectores nuevos se reconstruyeron reajustando clasificadores desde caché con selecciones guardadas; verifican las métricas archivadas, no recuperan automáticamente checkpoints de la ejecución original ni demuestran por sí solos ausencia de fuga.

**Decisión operativa:** continuar con la cascada de dos etapas seleccionada como candidata principal y preparar la escritura de método, resultados y limitaciones ya sustentados. Mantener H1/H2 como controles históricos y la hipótesis no miope como pregunta abierta; no exigir que H2 gane para permitir escribir sobre la cascada. Priorizar reconciliación y validación sobre nuevas arquitecturas. Congelar una versión de artefactos significa preservar su trazabilidad, no certificar equivalencia, novedad o cierre científico.

**Bloqueos vigentes:**

1. Completar la referencia Top-k corregida de KTH para folds 1–3 si se decide mantener una comparación numérica homogénea; el mapa de procedencia de las cuatro particiones ya está documentado. Hasta entonces, conservar KTH como descriptivo de su variante archivada y fuera de Demšar.
2. Completar procedencia: folds productores, grupos, checkpoints, transformaciones y hashes. La persistencia y el recálculo de macro-F1 de las tres rutas ya están hechos; no repetirlos como si faltaran.
3. Corregir la puerta histórica H2 que omite dos criterios y documentar margen 0,005 y presupuesto común, sin editar retroactivamente resultados. Esa puerta no certifica la cascada ni debe bloquear por sí sola su escritura.
4. Validar la selección en cada fold evaluador, incluida la selección heredada Top-k; completar permutación de todo el pipeline si se sostiene una afirmación de integridad con esa prueba. PCA solo cuenta como ablación si se usa y evalúa.
5. Investigar discrepancias físico/cache (rutas: índices 1261 y 2016; predicción: 4551), igualar transformaciones/checkpoints y ampliar el protocolo físico únicamente con autorización. No extrapolar 47 imágenes a seis datasets.
6. Localizar artefactos ROCF y revisar antecedentes con fuentes primarias antes de citar sus cifras o afirmar originalidad. Registrar por separado lo no verificado.

La secuencia de 12.0 reemplaza las prioridades de versiones anteriores. Las secciones 1–11 y las fases generales conservan el diseño inicial multietapa como marco e hipótesis, no como descripción de lo ya implementado por la cascada de dos etapas. No autoriza por sí sola entrenamientos, nuevos agentes ni publicación.

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

La hipótesis inicial multietapa exigía superar la compuerta actual mediante **una política multietapa con parada explícita y costos incrementales medidos**, no simplemente cambiar Ridge por una red. Requiere ablaciones para atribuir una mejora a mirar más de un paso o al costo dependiente del estado. Al corte v1.5 esa ventaja no está demostrada: se prioriza la cascada más sencilla y se preserva el resultado negativo, sin presentarla como una validación de la hipótesis no miope.

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

**Este árbol sigue siendo la arquitectura objetivo, no una certificación de que todo existe.** Al 10 de octubre existen también `crossfit.py`, `baselines.py`, `pilot.py`, `executor.py`, scripts de suite/reporte v2 y siete artefactos obligatorios por condición. Persistir esos siete archivos no satisface todavía todos los campos de 11.1: faltan procedencia completa de folds internos, modelos y hashes efectivos, entre otros. Reutilizar lo válido sin alterar resultados históricos.

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

### 12.0. Camino crítico v1.5: evidencia consolidada y escritura en paralelo

Los títulos de commits y booleanos PASS no son criterios de aceptación. Estado al corte de esta auditoría:

| Hito | Avance comprobado | Estado |
| --- | --- | --- |
| R0 | v1/v2 conservadas y auditadas | Cerrado para preservación histórica |
| R1 | Costos descontados; piloto45/75 observa múltiples adquisiciones | Factibilidad demostrada en entrenamiento, utilidad no miope no demostrada |
| R2 | Presupuesto coherente y separación train/test en las rutas revisadas | Parcial: sintonización interna reutilizada en pilotos, PCA sin uso y permutación incompleta; no certifica anidamiento integral |
| R3 | Registro 22 y cascada con etapa económica seleccionada | Parcial: Top-k KTH de otra fuente; comparación física solo contra Top-k en DTD, sin selección conjunta H2 sobre 22 |
| R4 | Ablaciones y pilotos guardados | Abierto: puerta omite criterios, H2 no mejora consistentemente |
| R5 | Benchmark físico pareado de 47 clases DTD y paridad cache/online | Piloto completado: 68,7% de ahorro, rutas 95,74% y predicciones 97,87%. Falta explicar discrepancias y estimar variabilidad con un protocolo ampliado |
| R6 | Suite v2 y cascada27 guardadas; A7 persiste vectores de las tres rutas | Persistencia y recálculo de 81 macro-F1 completados. 31.984 observaciones acumuladas; procedencia completa y confirmación independiente siguen abiertas |
| R7 | Documento de cierre y resultados narrados ROCF | Cierre corregido a condicionado; ROCF permanece no verificado hasta localizar sus artefactos. No justificar decisiones con esa tabla |
| R8 | Material para método, resultados y limitaciones | Escritura parcial habilitada con evidencia existente; conclusión final y afirmaciones fuertes condicionadas a P0a–P5a según su alcance |

**Prioridades siguientes para futuros responsables, sin ejecutar por aparecer en el plan:**

| Prioridad / responsable | Trabajo | Entregable y aceptación |
| --- | --- | --- |
| P0a — A/E; mapa completado, resultados corregidos incompletos | Reconciliar Top-k KTH | Mapa de las cuatro particiones documentado. La divergencia en fold 4 se asocia con la agrupación física en inner CV; folds 1–3 no tienen cómputo de la variante corregida. KTH queda descriptivo según la variante archivada y fuera de Demšar ($N=5$); completar folds 1–3 requeriría nuevas corridas y una decisión explícita de conservar la comparación numérica homogénea. |
| P1a — A/C; completado | Cerrar trazabilidad y localizar ROCF | Resuelto: Búsqueda exhaustiva confirma ausencia de código, logs y modelos de ROCF. Queda formal y definitivamente excluido del manuscrito y de las conclusiones, preservando el rigor epistémico. |
| P2a — C/E; antes de certificar selección | Anidamiento y puerta histórica | Auditar la selección heredada Top-k y separar ajuste de evaluación interna; cualquier corrección produce una versión nueva. Para H2, puerta con cinco criterios y margen planificado 0,005, con tests donde cada fallo impida PASS. No exigir superioridad H2 como condición para la cascada ni corregir JSON antiguos |
| P3a — C/A; para afirmaciones de integridad | Pruebas del pipeline completo | Repetir selección, entrenamiento y evaluación con permutación en datos retenidos, si se mantiene esa prueba. Conectar y evaluar PCA o declararlo no evaluado. Adjuntar comando, commit y salida de tests; no mantener el conteo narrativo de 57 sin registro verificable |
| P4a — D/E; completado y explicado | Robustez de medición y paridad | Resuelto: Discrepancias en índices 1261, 2016 y 4551 demostradas experimentalmente por diferencia de interpolación de imagen (`torchvision.Resize` Bilinear en offline vs. `AutoImageProcessor` Bicubic en online; similitud coseno $1{,}00000000$ con Bilinear). Protocolo ampliado pareado diseñado. |
| P5a — coordinación/B/E | Decisión y alcance final | Integrar calidad, latencia y evidencia frente a antecedentes. Sin no inferioridad preespecificada y evaluada no escribir «preserva rendimiento». Sin comparación física contra Completa/GFS no escribir «los domina en costo». La elección práctica de cascada puede conservar resultados negativos, pero no certifica novedad por sí sola |
| W1 — coordinación/E; revisión editorial de esta ronda completada | Preparar escritura y sincronizar reportes | Manuscrito compilado en 38 páginas; se retiraron las inferencias sobre 27 particiones dependientes y el resumen físico no auditable de 136 imágenes, se acotó el protocolo a DTD y se actualizaron memorando y ZIP. El PDF fue revisado visualmente en las páginas de resultados, metodología y discusión. El log conserva una advertencia Underfull y dos avisos de ancla duplicada de portada; siguen pendientes la auditoría integral de referencias/figuras y los pendientes metodológicos de P0a–P5a. |

No repetir P0 entero, la persistencia A7 ni el piloto físico como si no existieran. Tampoco repetir los pilotos a 35 ms para probar un mecanismo que exige más de una adquisición. No mezclar costo del modelo FSC, proxy de cascada, piloto P4 monoclase y benchmark pareado nuevo. No abrir otra arquitectura por defecto; una ampliación debe responder un pendiente concreto y tener autorización.

**Regla para la escritura:** incorporar ahora evidencia y limitaciones auditadas. No trasladar 75,5% a tiempo real ni 68,7% a todos los datasets; no convertir p>0,05 en equivalencia, ni 15,98× en aceleración agregada. No llamar H2 horizonte infinito ni atribuir causalmente diferencias a «saturación» o «ruido dimensional» sin una prueba. Conservar KTH descriptivo con su procedencia: excluirlo de la inferencia reconciliada no elimina sus resultados.

**Criterio de cierre documental:** cada afirmación principal debe apuntar a un artefacto, protocolo y población; cada pendiente no resuelto debe quedar excluido de la afirmación o reconocido como limitación. Es posible entregar un manuscrito exploratorio delimitado sin nuevas corridas. No es posible presentar esos mismos datos como validación confirmatoria, equivalencia o eficiencia generalizada. Una actualización del plan no autoriza automáticamente editar el manuscrito o ejecutar los paquetes.

Las fases 0–5 siguientes conservan el diseño inicial; la tabla anterior determina qué está completado y qué continúa pendiente, evitando reiniciar el proyecto.

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

Estimación organizativa histórica, no plazo restante: 1 semana para auditoría/protocolo; 1–2 para piloto; 1–2 para implementación/evaluación; 1–2 para medición y análisis; 1 para escritura. El rango inicial de **5–8 semanas** no se reinicia en v1.5. El trabajo restante se estima por P0a–P5a y W1 tras identificar qué exige nuevos ajustes o mediciones; no se promete una fecha sin esa estimación.

Usar los tiempos y memoria de pilotos existentes para presupuestar cualquier ampliación, diferenciando entrenamiento y latencia de inferencia. No programar de entrada cientos de entrenamientos ni competir simultáneamente por la misma GPU.

## 13. Organización para futuros subagentes

No se lanzan subagentes por la creación o actualización de este documento. Cuando se solicite delegar, el coordinador asignará los pendientes concretos de 12.0 con propiedad explícita de archivos y validará cada entrega. Los paquetes y encargos iniciales no autorizan reconstruir lo terminado ni implementar H2/H3 de nuevo sin una decisión específica.

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

La estructura siguiente corresponde a la hipótesis multietapa original. Para escribir con la evidencia v1.5, describir la cascada seleccionada de dos etapas como candidata evaluada y H1/H2 como experimentos de contraste; no atribuir utilidad futura aprendida a una regla de escalado por margen. La novedad debe justificarse frente a antecedentes concretos, no presumirse por esta estructura.

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

1. Leer este plan **1.6**, la auditoría histórica y las precisiones del corte `e0d3564`; verificar cambios concurrentes y procesos antes de intervenir. No reiniciar predicciones ni el piloto físico de DTD ya completados.
2. El mapa de procedencia Top-k KTH ya está documentado. Si se necesita comparar todos los folds bajo la variante corregida, calcular los folds 1–3 en una nueva versión; hasta entonces, informar KTH por separado y mantener la inferencia en cinco datasets.
3. Cerrar P1a documental y preparar W1: manifiestos, búsqueda de artefactos ROCF y corrección de reportes. Escribir solo evidencia sustentada; sin ROCF verificado, excluir sus cifras del paper.
4. Resolver P2a/P3a con alcance acotado si se autoriza implementación; preservar versiones antiguas y registrar toda exposición al test. No convertir el diagnóstico negativo H2 en una promesa de futura superioridad.
5. El resumen físico de 136 imágenes queda excluido hasta recuperar las mediciones por imagen y el log de ejecución. Si se repite el estudio, controlar orden y repeticiones y elegir comparadores/datasets según la afirmación que se quiera probar; el piloto DTD actual solo respalda una reducción local frente a Top-k.
6. Cerrar P5a y la conclusión con calidad, costo, incertidumbre y comparación bibliográfica. Si quedan límites, delimitarlos: la redacción puede avanzar sin inventar equivalencia o declarar cerrados pendientes reales.

**Decisión sobre la base:** ResNet es un control, no una obligación. Tampoco fijar automáticamente el individuo de mejor F1. Seleccionar la ruta completa con información interna, costo total y complementariedad residual. SigLIP fue elegido 20 veces en la cascada guardada, BEiTv2 cinco, ResNet una y Top-k directo una; KTH solo tenía costos para dos bases candidatas. Eso describe esta búsqueda, no una regla universal.

**Conclusión de la propuesta:** la tesis investiga cuándo adquirir y fusionar información. La cascada seleccionada tiene resultados predictivos reproducibles desde vectores y evidencia física local de ahorro; es la candidata priorizada para completar la validación y avanzar con la escritura. Todavía no se demuestra superioridad sobre Completa/Top-k/GFS, equivalencia predictiva, ahorro físico multidataset ni originalidad universal. La hipótesis multietapa sigue abierta, sus resultados negativos se conservan y no impiden redactar honestamente el alcance ya sustentado.
