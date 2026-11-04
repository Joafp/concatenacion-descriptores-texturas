# Reauditoría del manuscrito y dictamen de cierre — 25-10-2026

## Material Passport y alcance

- Marco: academic-research-suite (ARS), revisión local de evidencia y escritura.
- Estado: **ANALYZED; cierre experimental pendiente**. No es un dictamen de revisión independiente, certificación de originalidad ni un PASS del pipeline formal completo de ARS.
- Corte de código: HEAD `bf5e7f9`, más el árbol local con cambios anteriores y los de esta revisión. HEAD por sí solo no identifica el material auditado.
- Material revisado: `paper/tesis.tex`, los seis capítulos activos, tablas incluidas, scripts y artefactos de las evaluaciones estática, de cascada histórica, física e integración con el ensamble de diversidad.
- Modalidad: recálculo desde CSV/predicciones/mediciones y replay desde scores guardados; no extracción ni ajuste independientes. No hubo nuevos entrenamientos, ejecución GPU, pruebas Java nuevas ni evaluación del test oficial del híbrido.
- Bibliografía: se comprobó la resolución local de citas al compilar. No se releyó ni verificó en línea toda la bibliografía ni todo el corpus de PDFs; no se certifican existencia, actualidad y soporte semántico de cada referencia mediante esa comprobación estructural.

## 1. Dictamen

La tesis ya tiene una dirección más específica que concatenar descriptores: **selección de bloques y adquisición condicional con rescate mediante ensambles de subconjuntos**. El manuscrito anterior no describía suficientemente la integración reciente. Se reescribió para separar tres niveles de evidencia:

| Nivel | Cobertura comprobada | Lo que permite afirmar |
| --- | --- | --- |
| Benchmark estático | 22 bloques, 20.652 dimensiones nominales, seis datasets, 47 condiciones por clasificador | Comparación de Individual, Completa, Top-k, GFS y Homogénea con SVM y ResMLP |
| Cascada histórica | 27 condiciones; 27 archivos de predicciones; piloto físico de una condición por dataset | Resultados archivados con reservas KTH y de fidelidad CUReT/Soil |
| Rescate de diversidad nuevo | Outex, 680 imágenes de entrenamiento oficial, semilla 42, 3 folds productores y 3 internos | Resultados OOF de desarrollo; todavía no cobertura en seis datasets ni ahorro físico del nuevo método |

**No se declara cerrada la fase experimental.** Falta aislar poda frente a compuerta, replicar el híbrido y medir su implementación física. No se reemplazan esas verificaciones con pruebas unitarias o con un valor favorable de F1.

## 2. Comprobaciones ejecutadas de nuevo

| Comprobación | Resultado | Salida nueva |
| --- | --- | --- |
| Fuentes estáticas y estadísticas | 470 filas; 47 condiciones por clasificador; Friedman y post-hoc de rangos con Holm recalculados | `results/analysis/thesis_reaudit_20261025/` |
| Predicciones de la cascada histórica | 27 condiciones, 81 filas métricas de tres métodos, 31.984 observaciones de test acumuladas | `results/analysis/thesis_reaudit_20261025/canonical_predictions/` |
| Desarrollo histórico de integración | 147 métricas; error máximo de F1/exactitud 1,11×10⁻¹⁶; 56 costos corregidos por ponderación, sin cambio de Pareto | `results/analysis/integration_v2/reaudit_20261025/` |
| Selección bajo presupuesto, FMD/Outex | 48 decisiones, 26 resultados, 21 proyecciones SVD auditadas | `results/analysis/integration_v8/reaudit_20261025_budget/` |
| Pool emparejado con/sin N-gramas | Tres folds emparejados y 26 filas de políticas; cierre de candidatos y scores comunes verificados | `results/analysis/integration_v7/reaudit_20261025_paired/` |
| Híbrido con diversidad | 36 decisiones reproducidas, 13 resultados, nueve SVD internas, una excedencia de presupuesto en validación | `results/analysis/integration_v8/reaudit_20261025_hybrid/` |
| Registros físicos históricos | 204 imágenes, 612 pares; se mantienen alertas de representación en CUReT y Soil | `results/analysis/thesis_reaudit_20261025/physical_recalculated.csv` |
| Suite de código completa | **80 aprobadas en 32,48 s** | `PYTHONPATH=.:src .venv-confirmatory/bin/python -m pytest -q tests/` |
| Coherencia de tablas y dependencias | 120 celdas de F1/exactitud coinciden con las fuentes recalculadas; 41 claves citadas resueltas en 51 entradas; 16 inclusiones/figuras existentes | Comprobación estructural local del manuscrito activo |
| Compilación y revisión visual | PDF de 39 páginas; sin errores, citas/referencias indefinidas ni overfull; dos underfull en tablas de descriptores | `paper/tesis.pdf`; vistas de control en `tmp/pdfs/reaudit_20261025/final/` |

Scripts nuevos de auditoría: `scripts/audit_thesis_state_20261025.py` y `scripts/audit_archived_cascade_predictions.py`. Los demás auditores existentes se ejecutaron contra directorios nuevos. Los hashes de entradas experimentales quedan en los artefactos de auditoría. Los hashes del manuscrito en `thesis_reaudit_20261025/summary.json` corresponden a la versión **anterior** a la reescritura, no al PDF final.

La comprobación posterior de dependencias/celdas y los hashes de fuentes y PDF revisados se registran con `scripts/check_thesis_revision.py` en `results/analysis/thesis_reaudit_20261025/post_revision_manifest.json`. Esta comprobación estructural no verifica semánticamente las referencias bibliográficas.

### Cifras que deben conservarse sin reinterpretación

- Estadística estática: con SVM, Individual–Completa e Individual–Top-k tienen Holm ≈0,0617; Individual–GFS ≈0,8028. Con ResMLP, Individual–GFS tiene Holm ≈0,0191. Son post-hoc de diferencias de rangos de Friedman, no Wilcoxon exacto.
- Híbrido relevancia/B60: macro-F1 **0,910742**, costo **proyectado** 53,316 ms; diversidad permanente: 0,914389/365,196 ms. Diferencia −0,003646 y reducción estimada de costo 85,40 %. No prueba equivalencia ni ahorro físico del 85,40 %.
- El mismo punto supera numéricamente Top-5 del piloto (0,900824), no a Completa-22 (0,913957) ni a diversidad permanente. Top-5 no sustituye toda búsqueda Top-k ni un control GFS.
- Relevancia es mejor que marginal en calidad y costo en B60 y B120 de este piloto. No está demostrada la ventaja de la razón ganancia/costo.
- El rescate completo/B60/fold1 excede el presupuesto en validación: 70,019604 ms proyectados frente a 59,602804 internos. No se elimina esa observación.

## 3. Correcciones del manuscrito

Se actualizaron resumen bilingüe, introducción, antecedentes, metodología, resultados, discusión, conclusión y README. Los cambios principales son:

1. Incorporar la construcción del ensamble de diversidad, votos repetidos frente a modelos únicos, escalas congeladas, poda, base y compuerta. Separar ese algoritmo del rescate Top-k histórico.
2. Incluir las 13 políticas del híbrido, todos los presupuestos y sus límites; no seleccionar solo el punto favorable como resultado confirmatorio.
3. Explicar las 47 condiciones estáticas por clasificador frente a las 27 canónicas históricas. Soil y FMD tienen tres semillas en la evaluación estática, no en el resumen canónico de 27.
4. Distinguir la biblioteca histórica de 21 de la ablación reciente de 21 sin N-gramas. Mantener seis datasets; no incorporar VisTex.
5. Precisar LBP uniforme y el checkpoint de BEiT-v2; describir el ajuste de SVD por fit y no como una matriz universal.
6. Corregir afirmaciones excesivas sobre saturación, generalización física, ausencia de alternativas en la literatura, prospectividad y causalidad de discrepancias de representación.
7. Mantener KTH histórico separado de la cascada aún no reconciliada con su control Top-k corregido. Conservar las alertas de CUReT y Soil sin atribuirlas a un pooler o interpolación no diagnosticados.
8. Explicitar que no rechazo no es equivalencia; no atribuir p-valores estáticos al híbrido, ni tratar folds/repeticiones como datasets independientes.
9. Separar costos por componentes, llamadas a modelos y latencias físicas. Los pilotos físicos anteriores no miden el rescate nuevo.

El manuscrito usa denominaciones metodológicas, no atribuciones personales para justificar los resultados. No se modificaron las métricas para hacerlas coincidir con una narrativa.

## 4. Reservas que siguen abiertas

- **Poda frente a adaptación:** falta el control del mismo rescate podado siempre activo en los mismos folds. Menos modelos y una base mejor podrían explicar parte de la ventaja.
- **Cobertura:** el híbrido solo tiene este piloto Outex. No hereda las 27 condiciones, las seis mediciones físicas ni la estadística del método anterior.
- **Selección y exposición:** el diseño se ha informado de evaluaciones previas; nuevos folds de entrenamiento no convierten el proyecto retrospectivamente en confirmatorio ciego. Documentar cada exposición.
- **Costo:** el presupuesto es una media proyectada de selección, no una cota dura por imagen ni una garantía fuera de muestra. Falta medir clasificadores, compuerta, transferencia, memoria y extracción efectiva del híbrido.
- **Procedencia:** el desarrollo histórico DTD usa SGKF y comparte 1.501 imágenes con el test oficial 1 en su entrenamiento; no es una comparación oficial ciega. Hay 101/102 caches de conteos de N-gramas coincidentes con manifiestos actuales; el restante de KTH debe resolverse antes de usarlo, sin invalidar por ello todos los caches.
- **KTH:** identidad de particiones, selección interna y transformaciones de la cascada histórica frente al Top-k corregido siguen pendientes. Coincidencia de medias no basta.
- **Fidelidad física:** los cosenos mínimos de CUReT/Soil (≈−0,0707/0,0085) no permiten declarar identidad con el caché, aun coincidiendo predicciones.
- **Novedad:** esta revisión no establece prioridad bibliográfica. La contribución candidata debe contrastarse específicamente con adquisición activa por bloques, cascadas y selección de ensambles bajo presupuesto después de fijar su mecanismo y controles.

## 5. Control ARS de riesgos de razonamiento

Este control es una revisión interna acotada, no una certificación exhaustiva. Se examinaron siete modos de fallo: implementación defectuosa, citas no comprobadas, resultados inventados, atajos experimentales, presentar un error como novedad, discordancia entre método y ejecución, y perseverar en una explicación refutada. Los replays/tests respaldan las rutas auditadas; la ausencia universal de errores y la novedad no se deducen de ellos. La mejora de relevancia frente a marginal y la ablación de poda pendiente impiden dar por probado el mecanismo preferido.

En estadística se revisaron once riesgos: (1) folds dependientes como réplicas, (2) mezcla de clasificadores, (3) mezcla de protocolos, (4) selección retrospectiva del mejor presupuesto, (5) múltiples comparaciones sin familia explícita, (6) no rechazo como equivalencia, (7) p-valores del benchmark atribuidos al híbrido, (8) ajuste y evaluación en las mismas muestras, (9) medidas repetidas como imágenes nuevas, (10) confundir significancia con magnitud práctica y (11) convertir desarrollo expuesto en confirmación ciega. Se corrigió el texto y se conservaron los límites; no se fabricaron nuevos contrastes para cerrar estos riesgos.

## 6. Preservación, entrega y siguiente paso

El respaldo previo de fuentes está en `paper/revision_20261025_before.tar.gz`. Los resultados experimentales originales no se sobrescribieron. El PDF es una revisión de trabajo, no una entrega final experimentalmente cerrada. No se actualizaron automáticamente ZIP de Overleaf, presentación, todo documento histórico ni el repositorio remoto. No se hicieron commit ni push.

Rige el [plan de cierre v11](PLAN_CIERRE_VIGENTE_2026-10-25.md). El siguiente experimento prioritario es **el mismo ensamble podado, siempre activo frente a condicional**, no iniciar indiscriminadamente otras 27 condiciones.
