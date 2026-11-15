contract_role: methodology
## Dimension Scores

### D1: methodology_rigor
score: warn
trigger: "reporting omissions or limited sensitivity and uncertainty analyses reduce confidence or reproducibility"

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: warn
trigger: "Local overstatements, ambiguous scope"

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

Revisión metodológica del manuscrito actual completo: fuente compilable y texto del PDF suministrado, incluidos siete capítulos, anexos y referencias. El PDF suministrado contiene el cierre de seis datasets; no se confunde con el PDF anterior de 87 páginas descrito en verification.json del cierre experimental. Se inspeccionaron de forma estática el resumen, CSV de medias y comparación con el archivo, README, verificación y scripts de preparación, ejecución y auditoría E1/E2. No se ejecutaron ajustes, extracción, inferencia ni benchmarks. No se consultaron informes de otros revisores. criteria_binding_unavailable: no se evalúa alineación institucional ni editorial.

La tesis conserva una conclusión exploratoria defendible: cuatro bloques constituyen una alternativa compacta observada, y la activación puede ganar o perder calidad frente al mismo rescate. Las limitaciones reconocidas no son, por sí solas, defectos fatales. No encontré evidencia inspeccionada que invalide todas las comparaciones principales. Las reservas siguientes requieren aclaraciones o análisis de resultados existentes; ninguna exige nuevas campañas para mantener ese alcance descriptivo.

### S1: La comparación E1 tiene un control directo identificable y cobertura completa

**Evidence Anchor**: text: paper/chapters/05_resultados.tex:93-95, §5.6 — "Los 27 Top-4 directos reproducen exactamente accuracy y macro-F1 de sus filas archivadas."

El control mantiene cuatro bloques y un SVM en cada condición, en lugar de atribuir la identidad Top-4 a todos los rescates históricos. La cobertura 27 y las diferencias de referencia nulas están respaldadas por results/analysis/top4_fixed_kth_completion_audit_20261115_v1/summary.json, claves completed_conditions y max_absolute_direct_accuracy_reference_delta, y las 27 filas de direct_reference_comparison.csv. Esto acredita consistencia con el archivo, no reproducción independiente desde RGB ni igualdad de cada predicción histórica.

### S2: La política se selecciona antes de evaluar el test y contabiliza la base

**Evidence Anchor**: text: paper/chapters/03_metodologia.tex:119-142, §§3.6-3.7 — "El umbral y la ruta quedan fijados antes de obtener"

La fórmula separa costo directo, base y bloques incrementales, y distingue tasas OOF y externas. scripts/run_top4_fixed_e1_e2.py:127-155 sitúa la selección y selection_pretest.json antes del ajuste final y la evaluación externa. La separación de scores internos y test evita interpretar la fracción realizada como ajuste retrospectivo del umbral. Las reservas sobre selección de representaciones se detallan en W3.

### S3: La interpretación evita pseudorreplicación y equivalencia por no rechazo

**Evidence Anchor**: text: paper/chapters/04_diseno_experimental.tex:35, §4.2 — "sus condiciones no son réplicas independientes."

El estimando equipondera datasets, la inferencia principal trabaja con seis medias y conserva Holm por familia. Los capítulos 5 a 7 no transforman p=0,5625 en equivalencia y no cuentan 31.984 observaciones o 612 pares físicos como imágenes independientes. La explicitación del cambio de métrica después de observar resultados también permite interpretar los contrastes como exploratorios.

### S4: Las discrepancias físicas se conservan sin extrapolar ahorro de latencia

**Evidence Anchor**: text: paper/chapters/06_discusion.tex:37-39, §6.4 — "La identidad de predicciones no resuelve esa diferencia."

La tesis mantiene separadas dimensión, adquisición proyectada y tiempo físico; identifica la fidelidad limitada CUReT/Soil y las sesiones distintas KTH. La recuperación de dos condiciones KTH no se presenta como reparación de todas las variantes históricas. El ahorro proyectado del 75 % coincide con el resumen del cierre dentro de su modelo de componentes.

### W1: Falta expresar la incertidumbre de las diferencias predictivas principales

**Severity**: Minor
**Evidence Anchor**: absence: paper/chapters/05_resultados.tex:93-126, §§5.6-5.7 y Tablas 5.13-5.19 — expected incertidumbre o sensibilidad cuantificada de las diferencias pareadas principales; checked texto completo del PDF, tablas E1/E2 y Anexo C
**Confidence**: 5 — inspección completa del reporte estadístico y del estimando por dataset.
**Minimum Remedy**: additional analysis — presentar las diferencias por condición o sus rangos junto con un análisis de sensibilidad que respete la dependencia; justificar expresamente qué variación se cuantifica. Si se propone un intervalo, especificar su población objetivo y unidad de remuestreo, sin tratar particiones solapadas como observaciones independientes.
**Impact**: El promedio de +0,0132 puntos y un p no significativo describen el resultado, pero no muestran por sí solos qué pérdidas son compatibles con la variabilidad observada. Las seis medias y los límites explícitos evitan una conclusión falsa de equivalencia, por lo que esta omisión no bloquea la conclusión exploratoria.
**Stronger Option**: new experiments — una evaluación prospectiva en dominios reservados permitiría otro estimando de generalización; es opcional para el alcance actual.

### W2: La sensibilidad sin KTH no acompaña el nuevo contraste principal de accuracy

**Severity**: Minor
**Evidence Anchor**: absence: paper/chapters/04_diseno_experimental.tex:108 y paper/chapters/C_resultados_adicionales.tex:8-19, §4.8 y §C.2.1 — expected sensibilidad de los contrastes de accuracy Individual/Completa-22/Top-4 excluyendo KTH archivado; checked Tablas 5.22-5.23 y C.3-C.7 y discusión de procedencia en Anexo B
**Confidence**: 5 — las tablas distinguen explícitamente el análisis secundario de macro-F1 del principal de accuracy.
**Minimum Remedy**: additional analysis — repetir sobre las cinco medias disponibles exactamente los pares y la familia del contraste principal de accuracy y mostrar el cambio, sin sustituir KTH por otra variante. Identificar las bibliotecas comparadas y la reserva de agrupación interna.
**Impact**: La tesis reconoce que los controles KTH estáticos no están completamente reconciliados, pero su sensibilidad publicada pertenece a cinco estrategias y macro-F1. Esa sensibilidad no establece la robustez de la nueva familia de tres estrategias en accuracy. No afirmo que el resultado cambie: la sensibilidad falta. La conclusión actual sigue siendo descriptiva y sin superioridad estadística.
**Scope**: Este hallazgo se refiere al benchmark estático archivado, no declara incompleto E1, cuyo cierre sí tiene cuatro condiciones KTH.

### W3: Conviene explicitar el nivel de selección que queda fijo en los OOF de E1

**Severity**: Minor
**Evidence Anchor**: text: paper/chapters/05_resultados.tex:93, §5.6 — "exactamente cuatro bloques por condición en ambas rutas"; scripts/prepare_top4_fixed_cascade.py:166-200 y scripts/run_top4_fixed_e1_e2.py:125-145.
**Confidence**: 5 — inspección directa del paso que carga bloques archivados y del bucle OOF.
**Minimum Remedy**: writing — añadir a §3.6 o §5.6 que los OOF son fuera de ajuste del SVM condicionado al subconjunto archivado: el ranking que definió ese subconjunto no se vuelve a aprender en cada pliegue OOF de E1. Diferenciar este hecho de reutilizar los OOF para escoger base y umbral, ya declarado.
**Impact**: La descripción actual reconoce la reutilización para selección de rutas, pero no expone con igual claridad la selección previa de representaciones. El código prepara top4 una vez por partición externa y reutiliza sus bloques en cada ajuste interno. Esto limita interpretar el F1 OOF como evaluación del procedimiento completo; no demuestra uso de etiquetas externas ni invalida la evaluación externa descriptiva. El anexo sobre la cascada histórica ya reconoce una dependencia análoga.
**Stronger Option**: new experiments — reconstruir el ranking dentro de cada entrenamiento OOF si se desea estimar el procedimiento completo; no es la reparación mínima del manuscrito actual.

### W4: Una ganancia ResMLP no coincide con los valores principales reportados

**Severity**: Minor
**Evidence Anchor**: text: paper/chapters/05_resultados.tex:27 y :38, §5.2 — "Top-4 registra accuracy media de 0,942022"; "con 0,944327"; "cinco aporta 0,212 puntos más que cuatro."
**Confidence**: 5 — contradicción entre la frase y los valores de la Tabla 5.3.
**Minimum Remedy**: writing — regenerar esa ganancia en puntos porcentuales desde las mismas medias no redondeadas utilizadas en la Tabla 5.3, conservando la precisión coherente. Los valores impresos implican aproximadamente 0,2305 puntos, no 0,212.
**Impact**: La discrepancia es local y no altera que el máximo ResMLP observado sea cinco ni que cuatro sea exploratorio. Se trata de una comprobación de coherencia de cifras, fuera de las cuatro familias de recomputación estadística acotadas; no se presenta como un recibo estadístico verificado.

### W5: La reserva Outex necesita delimitar las filas y bloques afectados

**Severity**: Minor
**Evidence Anchor**: text: paper/chapters/04_diseno_experimental.tex:48, §4.3 — "Existe una alerta de correspondencia de filas y bloques de características cuyo rastreo se conserva como reserva"
**Confidence**: 4 — la reserva es explícita, pero su propagación por tabla no queda determinada en el manuscrito.
**Minimum Remedy**: writing — incorporar una matriz breve que vincule la alerta con bloque, archivo, protocolo y tablas afectadas, indicando qué correspondencias se comprobaron y cuáles siguen desconocidas; enlazar los manifiestos pertinentes. Si una fila carece de identidad de muestra comprobada, marcarla como no validada en su tabla y proporcionar una sensibilidad que la excluya.
**Impact**: Una reserva genérica obliga al lector a inferir si alcanza al barrido, al benchmark de 22 bloques, al panel físico o a E1. No infiero que todos estén mal alineados: el problema demostrado es la falta de delimitación de la confianza por resultado. La reparación mínima usa la procedencia disponible y no exige repetir extracción.
**Escalation Condition**: additional analysis — solo si la trazabilidad identifica una fila principal afectada, recalcular el agregado sin ella; una comprobación futura de desalineación real justificaría reevaluar su gravedad.

El balance D1 es warn por incertidumbre y sensibilidad incompletas y por estos límites de trazabilidad. D3 es warn por una inconsistencia local y por el alcance ambiguo del OOF, conservando el argumento central. La ausencia de controles Top-4+N-gramas, una compuerta independiente por cada base o una campaña física completa se reconoce como límite de preguntas más amplias; no impongo esos experimentos para sostener los enunciados exploratorios presentes. La selección por macro-F1 y reporte por accuracy no es un error de implementación: su cronología está declarada y las métricas macro se conservan.

## Arithmetic Receipts

### AR1
procedure_id: p_from_test_statistic
evidence_anchor: table: inputs/manuscript_pdf_text.txt, Tabla 5.22, fila SVM y §4.8
reported_inputs: Friedman; estadístico 6,3333; p exacto 0,0521; seis datasets; tres métodos; 46.656 permutaciones de rangos
assumptions: El manuscrito especifica enumeración exacta y no la aproximación chi-cuadrado.
derivation: La cola chi-cuadrado estándar no reproduce por definición la enumeración exacta; la función acotada estándar no verifica este p de permutación.
derived_value_or_range: No derivado dentro del procedimiento acotado.
comparison_rule: No comparar una cola asintótica con un p exacto como si fueran el mismo procedimiento.
status: not_computable
not_computable_reason: nonstandard_p_procedure
tail_convention: upper-tail

### AR2
procedure_id: p_from_test_statistic
evidence_anchor: table: inputs/manuscript_pdf_text.txt, Tabla 5.22, fila RESMLP y §4.8
reported_inputs: Friedman; estadístico 2,3333; p exacto 0,4297; seis datasets; tres métodos; 46.656 permutaciones de rangos
assumptions: Se conserva la enumeración exacta declarada; no se sustituye por chi-cuadrado asintótico.
derivation: El p exacto requiere el algoritmo de enumeración, fuera del mapeo estándar de familia y estadístico de este recibo.
derived_value_or_range: No derivado dentro del procedimiento acotado.
comparison_rule: Una diferencia frente a la aproximación asintótica no establece incompatibilidad del p exacto.
status: not_computable
not_computable_reason: nonstandard_p_procedure
tail_convention: upper-tail

### AR3
procedure_id: p_from_test_statistic
evidence_anchor: text: paper/chapters/05_resultados.tex:95, §5.6 — "Wilcoxon exacto bilateral sobre esas seis medias"
reported_inputs: Wilcoxon pareado exacto bilateral; seis medias por dataset; p=0,5625; estadístico de rangos no impreso
assumptions: Pareamiento por dataset y bilateralidad expresamente indicados; no se supone aproximación normal ni independencia entre particiones.
derivation: No se dispone del estadístico reportado requerido para invertirlo mediante una distribución estándar del procedimiento acotado; no se inventa un estadístico ni un z.
derived_value_or_range: No derivado dentro del procedimiento acotado; el resumen archivado contiene el mismo p, que es corroboración documental.
comparison_rule: Distinguir coincidencia con summary.json de una recomputación acotada independiente del p.
status: not_computable
not_computable_reason: missing_reported_value
tail_convention: two-tailed

