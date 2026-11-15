# Síntesis editorial de la tesis — 15 de noviembre de 2026

## Alcance, calibración y procedencia

calibration_status: NOT_CALIBRATED

Decisión de este ejercicio ARS: **Major Revision**. Es el resultado mecánico del contrato `reviewer/reviewer_full/v2`, no una decisión universitaria ni una recomendación de admisión a una revista. El objetivo declarado es una tesis de grado exploratoria sobre clasificación de texturas; no se suministró rúbrica institucional confirmada. El pase D6 evalúa la contribución empírica delimitada según ese encuadre, sin acreditar adecuación institucional o editorial.

Se leyeron íntegramente los cinco informes Phase2, el protocolo de síntesis, el contrato, la configuración y la procedencia; se consultaron además el cierre y el método principal para arbitrar el alcance de las observaciones. Se usa cada tarjeta como par Phase1+Phase2: según la comprobación de conformidad del orquestador, las cinco Phase1 contienen `criteria_binding_unavailable` y las cinco Phase2 pasaron con referencia a ese compromiso. No existe ReviewTargetContext ni vínculo #684. EIC, R1, R2, R3 y DA permanecen explícitamente **unbound / criteria_binding_unavailable / NOT_CALIBRATED**. La conformidad no aporta calibración ni aprobación externa.

## Review Panel Provenance (#540/#740)

Fuente: `panel_provenance.json`, esquema `review-panel-provenance/1.0`, panel `ars-thesis-review-20261115-v1`; validación/replay comunicados como PASS por el orquestador.

| Eje | Valor observado |
|---|---|
| role_separated | true |
| blind_to_peer_outputs | true |
| fresh_context | true |
| human_distinct | false |
| model_family_distinct | unknown |
| provider_distinct | unknown |

`fresh_context_scope: within_panel_attempt_only`. Este dato no certifica contextos nuevos respecto de intentos anteriores. Las cinco sedes son ejecuciones de modelo; los identificadores de familia y proveedor son desconocidos. Las personas/lentes diferentes y el mismo enrutamiento heredado no prueban independencia ni diversidad de modelos o proveedores. No se calcula independencia binaria, agregado entre familias ni una mayoría de un supuesto mismo modelo.

Model-family provenance is incomplete; cross-family separation is unknown, so correlated-error risk cannot be ruled out.

Contrato SHA-256: `e9712090d2469fea15a37b8e22d4e137afbcb2bf38d5789939c5df56738ef7af`. Manifiesto normalizado: `a129d039421a4f2cf60c53b32d0c303653e9bb1b03c3c9a4e4bdaabc12f6daa3`. Topología ejecutada: `0eff4322b1af13719a8a18769f247a0023e9d9c1d60aefa34ae778012c8886ee`.

## Auditoría mecánica del contrato

Solo participan los asientos elegibles. `—` representa `not_assessed` excluido, nunca un pase ni una abstención contada en el denominador. Ningún asiento elegible se abstuvo.

| Dimensión / prioridad | EIC | R1 metodología | R2 dominio | R3 perspectiva | DA | n elegible evaluado | Veredicto peor elegible |
|---|---|---|---|---|---|---|---|
| D1 metodología / mandatory | — | warn | — | — | — | 1 | warn |
| D2 dominio / mandatory | — | — | warn | — | — | 1 | warn |
| D3 coherencia / mandatory | — | warn | — | — | warn | 2 | warn |
| D4 relevancia adyacente / high | — | — | — | warn | — | 1 | warn |
| D5 escritura / normal | warn | — | — | — | — | 1 | warn |
| D6 contribución / mandatory | pass | — | — | — | — | 1 | pass |

| Condición | Evaluación | fired |
|---|---|---|
| F1, gravedad 95 | Ninguna dimensión mandatory contiene bloqueo fatal. | false |
| F2, gravedad 90 | Ninguna dimensión mandatory recibe block. | false |
| F3, gravedad 70 | Mayoría por dimensión: D1=1/1 warn, D2=1/1 warn, D3=2/2 warn, D6=0/1 warn o peor. Tres dimensiones mandatory satisfacen el átomo; se requieren dos. | true |
| F4, gravedad 60 | D4 no recibe block. | false |
| F5, gravedad 40 | Hay dimensiones warn. | true |
| F0, gravedad 10 | No todas las dimensiones pasan. | false |

dimension_verdicts: [D1=warn, D2=warn, D3=warn, D4=warn, D5=warn, D6=pass]
fired_conditions: [F3, F5]
da_critical_adjudications: []
editorial_decision=major_revision

F3 prevalece sobre F5 por gravedad contractual. No hay hallazgos DA CRITICAL que validar, rechazar o dejar sin resolver; las tablas CRITICAL y MAJOR están vacías. Tampoco hay bloqueos, fatalidades ni debilidades calificadas Major. **No se eleva ninguna observación Minor a Major:** la etiqueta global resulta del umbral de dos dimensiones mandatory con warn, incluso con un único propietario en D1 y D2. No es una mayoría narrativa de cinco revisores ni una prueba de que los reparos cambien el diseño central. Los informes no ofrecen un enum global de recomendación que deba sustituir ese cálculo.

## Carta de decisión y arbitraje

La contribución conservada es una comparación empírica situada de selección, concatenación y adquisición condicional. Las tarjetas reconocen que Top-4 es una alternativa compacta observada, que E1 completa 27 condiciones y seis datasets frente al mismo rescate directo, y que el ahorro del 75 % es adquisición proyectada, sin equivalencia predictiva ni aceleración física universal demostradas. El cierre de `paper/chapters/07_conclusion.tex:6–24` sostiene precisamente ese alcance. No procede exigir óptimo universal, superioridad confirmatoria, despliegue industrial o prioridad algorítmica para reparar el manuscrito presente.

Las reservas accionables son incertidumbre y sensibilidad de resultados existentes, explicación del nivel de selección OOF y procedencia Outex, contexto bibliográfico y descripción de adaptaciones, más correcciones locales de lectura. El no rechazo estadístico no se trata como equivalencia. Los recibos AR1–AR3 de metodología dicen `not_computable` para las verificaciones acotadas correspondientes; no denuncian p-valores incorrectos ni constituyen recomputación independiente. La coincidencia documental con un resumen archivado tampoco es reproducción desde imágenes.

**Acuerdo y silencio.** La resta ResMLP es un hallazgo corroborado por EIC y R1 (2/4 no-DA); R2 y R3 no lo mencionan. DA m2 lo confirma fuera del denominador. La claridad OOF reúne a R1 y DA en la necesidad de separar ajuste del SVM y selección del subconjunto; los anclajes distinguen E1 de la cascada histórica. No hay CONSENSUS-3 ni CONSENSUS-4 entre debilidades y no se fabrica consenso por ausencia de objeciones. Cada reparo restante es de un solo asiento no-DA. Los reconocimientos positivos compartidos no amplían la corroboración de una debilidad concreta.

**Desacuerdos.** No se identifica SPLIT de existencia, severidad o remedio entre tarjetas. Que otros asientos celebren una contribución delimitada no contradice una mejora local solicitada. La diferencia aparente entre reservas todas Minor y decisión global Major se resuelve mediante la precedencia contractual ya expuesta, sin reinterpretar los scores.

**Arbitraje OOF.** R1 W3 inspeccionó scripts de E1 y afirma que los bloques archivados se conservan entre pliegues internos; DA m1 cita una declaración del anexo histórico y pide precisar por separado E1, sin auditar su implementación. Son alcances compatibles, no dos verificaciones independientes del código E1. Se conserva como remedio la explicación de ambos niveles en el método principal. Ni tarjeta demuestra uso de etiquetas del test externo. La repetición plenamente anidada se conserva como opción para otra pregunta, no como reparación mínima.

**Arbitraje de límites y carga de revisión.** Las advertencias físicas, el cambio posterior de métrica, Top-4+N-gramas pendiente y las adaptaciones no fieles ya se declaran; los revisores no los convierten en defectos mayores. Las exigencias mínimas siguientes usan escritura, procedencia o datos existentes. No se requiere una nueva campaña para borrar una limitación honestamente delimitada. La reevaluación debe revisar si las advertencias dimensionales siguen vigentes después de las respuestas; no se promete aceptación ni aprobación institucional.

## Inventario atómico y acciones en orden de fuente

Convención de fuentes: EIC=`reports/eic_phase2.md`; R1=`reports/methodology_phase2.md`; R2=`reports/domain_phase2.md`; R3=`reports/perspective_phase2.md`; DA=`reports/da_phase2.md`. Los localizadores se transportan de las tarjetas. `Minor` y la confianza son metadatos del hallazgo, no pesos. Los números SC y R son referencias de transporte, nunca orden de trabajo. Se conservan las 15 observaciones originales, incluidos duplicados, en orden EIC W1–W4, R1 W1–W5, R2 W1–W2, R3 W1–W2, DA m1–m2.

| Fuente / subclaim | Severidad; confianza | Evidence Anchor transportado | Posición y remedio mínimo | Verificación / obligación editorial |
|---|---|---|---|---|
| EIC W1; SC-1 | Minor; 5 | text: paper/chapters/05_resultados.tex:38, §5.2.1 | raised. Corregir ganancia ResMLP con medias fuente, unidad puntos porcentuales. Escritura + aritmética. | Valores impresos implican 0,2305 pp; comprobar precisión fuente y concordancia con Tabla 5.3. must_fix; R1. |
| EIC W2; SC-2 | Minor; 5 | text: paper/chapters/05_resultados.tex:52, §5.3 | raised. Etiqueta única para tabla principal de accuracy y referencia separada a C.9 macro-F1. Escritura. | PDF enlaza a Tabla 5.6 para la explicación principal y a C.9 como complemento. should_fix. |
| EIC W3; SC-3 | Minor; 5 | text: results/analysis/ars_thesis_review_20261115_v1/inputs/manuscript_pdf_text.txt:1538, Tabla 5.8, PDF p.24 | raised. Actualizar pie de latencias: Tablas 5.7 y C.11 o llamadas comunes. Escritura. | Referencias y nombres de métricas corresponden a ambas tablas en PDF. should_fix. |
| EIC W4; SC-4 | Minor; 4 | text: paper/chapters/05_resultados.tex:109, §5.6 | raised. Dejar fallo inicial, receta corregida, criterio y alcance en cuerpo; trasladar infraestructura/secuencia al anexo D enlazado. Escritura. | E1 se lee sin repetición de bitácora; reservas interpretativas y evidencia permanecen visibles. should_fix. |
| R1 W1; SC-5 | Minor; 5 | absence: paper/chapters/05_resultados.tex:93–126, §§5.6–5.7 y Tablas 5.13–5.19; checked PDF, E1/E2, Anexo C | raised. Diferencias por condición o rangos y sensibilidad que respete dependencia; especificar variación objetivo. Análisis de datos existentes. | Se identifica unidad/estimando; ningún remuestreo trata particiones solapadas como independientes; no se infiere equivalencia. must_fix; R2. |
| R1 W2; SC-6 | Minor; 5 | absence: paper/chapters/04_diseno_experimental.tex:108 y paper/chapters/C_resultados_adicionales.tex:8–19, §4.8 y §C.2.1; checked Tablas 5.22–5.23, C.3–C.7 y Anexo B | raised. Sensibilidad sin KTH de la misma familia principal de accuracy Individual/Completa-22/Top-4 sobre cinco medias. Análisis de datos existentes. | Mismos pares y familia, bibliotecas identificadas, cambios visibles y reserva de agrupación interna; no sustituir KTH por otra variante. must_fix; R3. |
| R1 W3; SC-7 | Minor; 5 | text: paper/chapters/05_resultados.tex:93, §5.6; scripts/prepare_top4_fixed_cascade.py:166–200 y scripts/run_top4_fixed_e1_e2.py:125–145 | raised. Explicar OOF condicionado al subconjunto archivado de E1, cuyo ranking no se reaprende por pliegue, separado de selección de base/umbral. Escritura. | Método distingue ambos niveles y conserva evaluación externa descriptiva; no denomina al F1 OOF validación del procedimiento completo. must_fix; R4. |
| R1 W4; SC-1 | Minor; 5 | text: paper/chapters/05_resultados.tex:27 y :38, §5.2 | corroborated, duplicado de EIC W1. Misma corrección desde medias no redondeadas. Escritura + aritmética. | Una sola corrección satisface ambos; no contar como nuevo defecto ni recibo estadístico recomputado. must_fix; R1 compartido. |
| R1 W5; SC-8 y SC-9 | Minor; 4 (ambos subclaims) | text: paper/chapters/04_diseno_experimental.tex:48, §4.3 | raised. SC-8: matriz bloque/archivo/protocolo/tablas con correspondencias comprobadas y desconocidas, enlazando manifiestos. SC-9: si falta identidad comprobada de una fila, marcarla no validada y excluirla en sensibilidad. Escritura/procedencia; análisis existente condicional. | SC-8 delimita qué resultados alcanza la alerta. SC-9 solo se activa si esa trazabilidad identifica fila principal afectada; informar agregado sin ella. No presumir desalineación global. must_fix; R5 y R6 condicional. |
| R2 W1; SC-10 y SC-11 | Minor; 5 (ambos subclaims) | absence: paper/chapters/02_literatura.tex:10–17, §2.2 y paper/articulo/borrador_profesor/references.bib; checked capítulo, bibliografía, docs/referencias/README.md y resúmenes Puig 2010/Khan 2015 | raised. SC-10: contextualizar selección/integración de métodos de Puig, García y Meléndez; SC-11: contextualizar combinación/compresión de Khan et al., DOI 10.1016/j.patrec.2014.07.020. Escritura. | Párrafo compara unidad de selección, protocolo y mecanismo de compacidad; distingue evaluación por píxel y compresión de la adquisición por imagen local. Sin ejecutar métodos. must_fix; R7 y R8. |
| R2 W2; SC-12 | Minor; 5 | text: paper/chapters/02_literatura.tex:22, §2.3 | raised. Tabla de cada comparador: representación/dimensión, peso/capa, cabeza, protocolo local, diferencias verificadas o no verificadas y receta/versionado. Escritura desde recetas. | El PDF identifica qué sistema produce cada columna sin confundir adaptación con reproducción; incluye los cuatro comparadores. must_fix; R9. |
| R3 W1; SC-13 | Minor; 5 | absence: paper/tesis.tex:92–108 y paper/chapters/04_diseno_experimental.tex:11, siglas y §4.1; checked siglas, capítulos, anexos, PDF | raised. Expandir SFFS, CNN y MLP; oración funcional de SFFS y distinción extractor/cabeza. Escritura. | Primera aparición o listado accesible define siglas y función sin exigir teoría extensa. should_fix. |
| R3 W2; SC-14 | Minor; 5 | text: paper/chapters/05_resultados.tex:107 y 152, §§5.6 y 5.8 | raised. Definir similitud coseno al primer uso, vectores de misma imagen, escala y criterio registrado 0,999. Escritura documentada. | Explica cercanía a uno y valores negativos; mínimo de muestra no se presenta como identidad global ni recuperación de procedencia. should_fix. |
| DA m1; SC-15 y enlace SC-7 | Minor (Observación menor); 4 | text: paper/chapters/F_estudios_complementarios.tex:173 | raised SC-15: llevar a §3.6 la limitación histórica del subconjunto no reconstruido por pliegue. Corroboración DA de necesidad de claridad OOF, con petición separada sobre E1 (SC-7); no segunda auditoría de E1. Escritura. | §3.6 identifica la selección histórica y E1 separadamente; no atribuye contaminación del test. must_fix; R10 para SC-15, R4 para E1. |
| DA m2; SC-1 | Minor (Observación menor); 5 | text: paper/chapters/05_resultados.tex:38 | corroborated, duplicado de EIC W1/R1 W4, fuera del cómputo no-DA. Escritura + aritmética. | Misma verificación de R1; no sumar una tercera debilidad ni consenso 3/4. must_fix; R1 compartido. |

La obligación `must_fix` exige respuesta y reparación mínima sustentada, o una justificación explícita que la reevaluación deba resolver; no representa triage ni decisión del autor. `should_fix` conserva los reparos de D4/D5 sin convertirlos individualmente en fatalidades. SC-9 es una condición de sensibilidad, no una constatación de que haya filas desalineadas.

Para cada SC distinto, los cuatro no-DA no listados en su fila son `not-mentioned`, salvo SC-1: EIC raised, R1 corroborated, R2/R3 not-mentioned. SC-7 es de R1 solamente entre no-DA; DA aporta el alcance ya delimitado. SC-15 es exclusivamente DA y no recibe etiqueta de consenso no-DA. No hay posiciones `disputed`. La evaluación de sustancia, anclajes y remedios sería la misma con redacción menos técnica; la precisión verbal y la confianza declarada no cuentan como evidencia adicional.

## Problemas que actualmente impiden cerrar la revisión

Estos tres grupos explican las dimensiones mandatory con warn; no añaden hallazgos ni cambian sus severidades. El contrato no permite suavizar F3 por ser locales.

| Grupo en orden de fuente | Anclajes / fuentes | Respuestas mínimas que lo atienden |
|---|---|---|
| Coherencia y alcance de selección | EIC W1 y R1 W4 / §5.2; R1 W3 / §5.6 y scripts; DA m1 / Anexo F:173 | R1, R4 y R10: cifra correcta y explicación OOF específica por estudio. |
| Incertidumbre, sensibilidad y procedencia | R1 W1 / §§5.6–5.7; W2 / §4.8 y C.2.1; W5 / §4.3 | R2, R3, R5 y R6 condicional: información de variación, sensibilidad relevante y alcance de alertas. |
| Contexto e identidad de comparadores | R2 W1 / §2.2 y bibliografía; W2 / §2.3 | R7–R9: antecedentes próximos y fichas de adaptaciones dentro del PDF. |

## Carga mínima y opciones fuera del cierre exigido

| Tipo de trabajo | Qué se solicita | Qué cuenta como comprobación |
|---|---|---|
| Escritura y comprobación documental | SC-1–4, SC-7–8, SC-10–15: aritmética local, referencias, jerarquía, OOF, procedencia, antecedentes, recetas y definiciones. | PDF compilado con enlaces correctos y texto coherente con fuentes/recetas; sin borrar reservas materiales. |
| Análisis de datos existentes | SC-5 y SC-6; SC-9 únicamente si se identifica fila principal afectada. | Tabla/sensibilidad con unidad y dependencia justificadas y mismos contrastes/bibliotecas pertinentes. No exige nuevos ajustes de modelos. |
| Experimentos opcionales | R1 W1: dominios reservados prospectivos; R1 W3/DA m1: ranking plenamente anidado. DA discute además selección estática a igual presupuesto y base reoptimizada por compuerta como fortalecimientos de otras preguntas. | Solo serían necesarios para ampliar el estimando o las afirmaciones; no son condiciones mínimas de esta decisión. |

No se solicita Top-4+N-gramas, nueva compuerta por cada base, campaña física completa ni reproducción de porcentajes publicados para sostener el cierre exploratorio actual. Ningún experimento, modificación del manuscrito o verificación estadística nueva fue ejecutado por esta síntesis.

## Resumen de los cinco informes y entrega al autor

| Asiento | Contribución de su tarjeta | Debilidades conservadas |
|---|---|---|
| EIC | Aporte identificable y exposición reconstruible; D5 warn, D6 pass. | W1–W4: cuatro Minor. |
| R1 metodología | E1 completo y control identificable; inferencia por dataset y límites físicos preservados; D1/D3 warn. | W1–W5: cinco Minor; dos análisis existentes y uno condicional. |
| R2 dominio | Definiciones/adaptaciones y aporte acotado defendibles; D2 warn. | W1–W2: dos Minor de contextualización. |
| R3 perspectiva | Método comprensible e implicaciones acotadas; D4 warn. | W1–W2: dos Minor de accesibilidad. |
| DA | No refutación de la proposición central; D3 warn. | m1–m2: dos menores; cero MAJOR/CRITICAL. |

La confianza se transporta por hallazgo en la tabla; no se inventa un score global ni se promedia. Las respuestas deben citar cada SC y observación de origen, describir cambio o justificación, y señalar el nuevo localizador verificable, siguiendo `templates/revision_response_template.md`. Una corrección compartida puede responder varios duplicados con referencias cruzadas. Esta síntesis no infiere aceptación, rechazo, orden de trabajo ni autorización de ampliación de afirmaciones por parte del autor. El orquestador emitirá el núcleo JSON canónico y su recibo de integridad por separado.
