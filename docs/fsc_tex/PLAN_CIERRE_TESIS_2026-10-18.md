# Plan de cierre experimental y editorial de la tesis

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: plan; actualización de la dirección ya acordada.
- Origin Date: 2026-10-18.
- Verification Status: UNVERIFIED para las tareas propuestas; estado existente consultado en archivos locales, sin reproducción independiente.
- Version Label: cierre_v1; acompaña al plan maestro v1.8.
- Corte del repositorio: `5685be3` antes de esta edición documental.

## 1. Objetivo y alcance

Cerrar la tesis sobre adquisición condicional de descriptores para clasificación de texturas. El aporte candidato es la cascada de dos etapas y su evaluación calidad–costo frente a composición estática, no una afirmación de superioridad universal o de originalidad certificada.

Se mantienen 22 descriptores, 20.652 dimensiones y seis datasets: DTD, FMD, CUReT, Outex13Official1360, SoilOriginal y KTH-TIPS-2b. La evaluación estática usa SVM/ResMLP; la cascada estudiada usa SVM. VisTex queda fuera por decisión del autor. No ampliar el método a ResMLP ni introducir nuevas arquitecturas como condición de cierre.

## 2. Estado que no debe volver a marcarse como pendiente

| Componente | Estado comprobado | Límite |
|---|---|---|
| Predicciones de cascada | 27 condiciones, 31.984 observaciones de test acumuladas | No son 27 datasets ni 31.984 imágenes necesariamente únicas |
| Pilotos físicos | Seis procesos con exit code 0; 204 imágenes y 612 parejas | Una condición por dataset; tres repeticiones por imagen |
| Top-k corregido KTH SVM | Cuatro folds guardados | No demuestra que la cascada histórica use esa selección |
| Manuscrito y entrega | PDF y ZIP actualizados el 18-10; presentación y guion disponibles | Existencia/compilación no certifica coherencia científica |

Resultados físicos archivados, no recalculados en esta edición:

| Dataset | Imágenes | Parejas | Reducción de latencia vs. Top-k | Estado de fidelidad del registro |
|---|---:|---:|---:|---|
| DTD | 47 | 141 | 69,36% | Piloto coincidente |
| FMD | 10 | 30 | 93,75% | Piloto coincidente |
| CUReT | 61 | 183 | 65,81% | Discrepancias en embeddings |
| Outex | 68 | 204 | 68,54% | Piloto coincidente |
| SoilOriginal | 7 | 21 | 61,51% | Discrepancias en embeddings |
| KTH-TIPS-2b | 11 | 33 | 75,53% | Piloto coincidente de la variante histórica |

Fuentes: `results/exploratory/fsc_tex/physical_six_20261012/{dataset}/status.json`, `measurements.jsonl`, `parity.json` y `suite.json`. No promediar estos porcentajes como si fueran una reducción global sin declarar la ponderación.

## 3. P0 — Cerrar fidelidad físico–caché

**Entradas:** registros físicos anteriores; embeddings, manifiestos y código de extracción usado por CUReT y Soil; `scripts/benchmark_cascade_multidataset.py`, `src/01_extract_features.py`, `src/extract_sota_2024.py` y `src/fsc_tex/executor.py`.

**Trabajo:**

1. Localizar por descriptor e imagen las discrepancias de `parity.json`; comprobar norma, forma, orden y hash de imagen.
2. Comparar checkpoint, pesos efectivamente cargados, versión de librerías, resize/interpolación, normalización y salida empleada (CLS/pooler). Registrar advertencias de pesos ausentes o inicializados.
3. Reproducir la extracción con configuración fuente. Cambiar un factor por comparación diagnóstica cuando se investigue una causa; no elegir transformaciones por mejorar el F1 del test.
4. Guardar vectores o diferencias verificables, configuración y hashes. Repetir la inferencia para detectar salidas no deterministas.
5. Si hay una corrección fundada, ejecutar nuevamente solo las condiciones afectadas en una carpeta nueva; mantener el registro anterior.

**Criterio de cierre:** causa documentada y ruta reproducible; verificar por imagen dimensiones, finitud, errores numéricos y acuerdos de decisiones. El umbral de coseno ≥0,999 del piloto es una comprobación operativa, no prueba de identidad. Cualquier discrepancia residual debe quedar cuantificada y delimitada. Si no puede reproducirse la representación, no etiquetar esas mediciones como validación fiel del sistema cacheado.

**Salida propuesta:** `docs/fsc_tex/DIAGNOSTICO_FIDELIDAD_CURET_SOIL.md` y artefactos nuevos bajo `results/exploratory/fsc_tex/fidelity_diagnostic_v1/`.

## 4. P1 — Reconciliar KTH sin mezclar variantes

**Entradas:** los cuatro controles en `results/extensions/kth_tips2b/ngram22_beitv2_innergrp_sample_v1/topk_individual_control/`; GFS que fija k; manifiesto físico por muestras; selección y predicciones de la cascada archivada.

**Trabajo:** construir una tabla por fold con índices train/test, grupos internos, semilla, k, bloques, transformaciones y fuentes de cada variante. Verificar que cada selección fue calculada únicamente dentro del entrenamiento externo. Si la ruta cara cambia, volver a ajustar/calibrar la cascada en entrenamiento para esa ruta y evaluar una vez en el test correspondiente. El resultado será una variante reconciliada, no una confirmación independiente del desarrollo previo.

**Criterio de cierre:** cuatro condiciones comparables con selecciones y predicciones persistidas; no cambiar solo el valor Top-k de la tabla conservando una cascada construida con otros bloques. Hasta entonces, KTH histórico permanece descriptivo y separado de la inferencia conjunta reconciliada.

**Salida propuesta:** `docs/fsc_tex/RECONCILIACION_KTH_CASCADA.md` y una carpeta nueva `results/exploratory/topk_cascade/kth_reconciled_v1/`.

## 5. P2 — Métricas y estadística coherentes

Depende de P1 para ampliar la inferencia conjunta a KTH.

- Recalcular macro-F1 y accuracy desde etiquetas/predicciones, con la misma definición de clases y particiones para cada comparación.
- Agregar primero las condiciones de cada dataset; declarar ponderación. No usar folds solapados como réplicas independientes.
- Mantener separados clasificadores y familias de hipótesis. Declarar corrección por comparaciones múltiples y diferencias observadas.
- Regenerar los contrastes pertinentes cuando cambie la variante; si se usa la herramienta Java del proyecto, conservar entrada, versión, comando y salida, y contrastar cálculos con la implementación disponible.
- No convertir un p no significativo en equivalencia, ni añadir retrospectivamente un margen para afirmar no inferioridad confirmatoria.
- Para latencia, conservar imagen como unidad de muestreo y tratar las repeticiones como medidas de la misma imagen; no inflar N multiplicando por tres.

**Criterio de cierre:** cada celda y contraste debe ser trazable a archivos fuente y al protocolo identificado; discrepancias numéricas explicadas, sin mezclar medidas físicas y costo proyectado.

## 6. P3 — Alcance de la validación física

**Lo mínimo para cerrar con el alcance actual:** resolver P0 y describir los seis pilotos como pilotos. No es obligatorio medir todos los splits si las conclusiones se limitan expresamente al muestreo realizado.

**Ampliación recomendada si se afirma ahorro sobre las 27 condiciones:** ejecutar esas condiciones con selección de imágenes fijada antes de medir, mismo hardware, warmup, número de repeticiones, orden aleatorio/balanceado y alcance del cronómetro. Registrar interferencia de otros procesos y memoria. Separar carga de modelos, decodificación y ejecución residente.

**Si se afirma ventaja física frente a Completa/GFS:** implementar y verificar sus rutas, incluyendo el SVD de n-gramas ajustado exclusivamente en entrenamiento. Si los modelos no caben simultáneamente en GPU, definir un régimen de residencia comparable; no comparar una ruta con cargas incluidas y otra sin ellas. No presentar suma de tiempos por extractor como cronometraje directo de la ruta completa.

**Criterio de cierre:** todas las condiciones previstas con estado explícito (completa, bloqueada o fallida), mediciones crudas y agregación reproducible; nunca ocultar condiciones desfavorables.

## 7. P4 — Actualización editorial coordinada

Puede adelantarse la revisión textual mientras se resuelven P0/P1, sin introducir cifras provisionales como resultados finales.

Revisar `paper/tesis.tex`, los seis capítulos, tablas/figuras, `paper/presentacion_defensa.tex`, guion y dossier. Buscar especialmente afirmaciones de que el benchmark «demuestra reproducibilidad» en todos los conjuntos pese a alertas de fidelidad, «descarta» limitaciones de generalización, garantiza ausencia de fuga o demuestra saturación dimensional general.

En tablas que combinan F1 de múltiples particiones y tiempos de un piloto, indicar ambos denominadores y protocolos. Evitar que el lector interprete las latencias como medidas de todo el benchmark. Separar claramente resultados estáticos, cascada histórica, variante KTH reconciliada y costos proyectados.

**Criterio de cierre:** mismo número de descriptores/datasets y mismas cifras en todos los entregables; sin contradicciones con `status.json`; cada limitación importante aparece también en conclusiones y defensa.

## 8. P5 — Empaquetado y entrega

1. Ejecutar pruebas pertinentes y registrar comando, fecha y salida, sin atribuir tests históricos a la revisión nueva.
2. Compilar tesis y presentación; revisar citas, referencias, desbordes y páginas afectadas visualmente.
3. Regenerar el ZIP desde fuentes vigentes; comprobar integridad y correspondencia de capítulos, bibliografía, tablas y figuras.
4. Guardar hashes del PDF, ZIP y resultados utilizados; documentar entorno y comandos de reproducción.
5. Revisar diff y separar cambios de evidencia de cambios editoriales. Commit/push solo según autorización vigente; este plan no los ejecuta.

**Entrega terminada:** PDF y ZIP coherentes, resultados identificados por variante, límites explícitos y ningún pendiente crítico presentado como resuelto.

## 9. Orden de ejecución y límites

Orden: P0 → P1 → P2 → decisión de alcance P3 → P4 → P5. La preparación editorial puede avanzar en paralelo sin alterar resultados. No es necesario volver a ejecutar los cuatro controles Top-k KTH ya existentes salvo fallo de auditoría concreto.

Las rutas de salida propuestas todavía no son resultados existentes. Los comandos de nuevas corridas se fijarán tras inspeccionar dependencias y protocolos; no se inventan opciones CLI ni duraciones. Usar carpetas versionadas, registro de PID/log/timeout, sin sobrescrituras ni reintentos silenciosos. Este pedido actual autoriza escribir el plan; no lanza corridas, cambia la tesis ni publica archivos.
