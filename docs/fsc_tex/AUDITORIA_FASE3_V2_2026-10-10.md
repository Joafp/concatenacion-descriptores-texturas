# Auditoría de FSC-Tex Fase 3 v2 — 10 de octubre de 2026

**Corte histórico: `f99115d`.** Para el estado posterior hasta `08c3ebb`, consultar [auditoría P0–P4 y cascada](AUDITORIA_P0_P4_CASCADA_2026-10-10.md). Los defectos descritos aquí corresponden a los artefactos v2; no se atribuyen automáticamente al código posterior.

**Estado ARS: ANALYZED.** Revisión de código y artefactos, recálculo de métricas/estadística y ejecución de tests. No se reentrenaron las 27 condiciones ni se reprodujo la extracción física; no es certificación de originalidad ni revisión independiente.

**Dictamen:** los resultados predictivos guardados son reproducibles desde sus predicciones. La v2 corrige problemas importantes de v1, pero no demuestra aún ventaja multietapa ni ahorro físico. No deben marcarse todos los hitos R0–R6 como completados científicamente.

## 1. Alcance y evidencia

- HEAD revisado: `f99115d`; commits nuevos: `fad8a6d`, `c650dd4`, `fdf845c`, `7189915`, `17ffd1a`, `5c1a662`, `f99115d`.
- Directorio: `results/exploratory/fsc_tex/phase3_v2_suite/`.
- Los manifiestos guardan el commit `5c1a662` y fechas entre 2026-10-08 18:16:51 UTC y 2026-10-09 00:51:54 UTC. No incluyen una huella completa del árbol de trabajo usado para entrenar.
- Inspección de procesos WSL durante esta revisión: no había una corrida FSC-Tex activa. No se iniciaron entrenamientos de datasets; los tests sí ajustan modelos sintéticos pequeños.
- Se preservaron las predicciones, métricas, manifiestos, trazas y cambios ajenos a esta revisión. Las modificaciones de reporte/plan no sustituyen la reparación posterior del evaluador.

### Comprobaciones realizadas

| Control | Resultado |
| --- | --- |
| Condiciones | 27: DTD 10, FMD 5, CUReT 2, Outex13Official1360 1, SoilOriginal 5, KTHTIPS2b 4 |
| Artefactos | Siete contratos obligatorios presentes por condición, más ablaciones y puerta de avance |
| Métricas de los ocho métodos | 216 vectores; macro-F1 y exactitud recalculados con diferencia máxima **0,0** respecto de `metrics.json` |
| Particiones y etiquetas externas | 27/27 reconstruidas desde manifiestos; coinciden índices y `y_true`; sin solapamiento de grupos fuente externos |
| KTH | Cuatro particiones con tres grupos `sample` en train y uno en test; sin cruce entre ambos |
| Trazas H2 | 31.984 exposiciones de test; IDs cubren exactamente cada test; presupuesto decrece sin infracciones detectadas |
| Costo H2 reconstruido | Diferencia máxima de 0,000003 ms respecto del promedio guardado, atribuible a redondeo float32; sigue siendo costo **modelado** |
| Tests del núcleo | **25 passed in 56.16s**; seis archivos de política, utilidad, integridad, controles, piloto y paridad |
| Tests nuevos del reporte | **4 passed in 1.62s**; rechazan métricas inconsistentes/artefactos ausentes y evitan certificar no inferioridad/eficiencia desde estimaciones puntuales |

31.984 son exposiciones en condiciones, no necesariamente imágenes únicas independientes. Los tests son necesarios, pero no suficientes para certificar la tubería: la paridad online usa mocks y el test de permutación no llama al piloto completo.

Comando de tests ejecutado desde la raíz Linux:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-confirmatory/bin/python -m pytest -q -p no:cacheprovider tests/test_fsc_tex_policy.py tests/test_fsc_tex_utility.py tests/test_fsc_tex_no_leakage.py tests/test_fsc_tex_baselines.py tests/test_fsc_tex_pilot.py tests/test_fsc_tex_online_parity.py
PYTHONDONTWRITEBYTECODE=1 .venv-confirmatory/bin/python -m pytest -q -p no:cacheprovider tests/test_fsc_tex_report.py
PYTHONDONTWRITEBYTECODE=1 .venv-confirmatory/bin/python scripts/report_fsc_tex_phase3_v2.py
```

El generador revisado `scripts/report_fsc_tex_phase3_v2.py` recalcula ahora F1/exactitud antes de reportar y falla si faltan artefactos o no coinciden métricas. La auditoría de splits y trazas de esta revisión se realizó adicionalmente; no debe confundirse con los booleanos preexistentes de `audit.json`.

## 2. Qué mejoró realmente desde v1

1. `policy.py`: presupuesto en unidades consistentes, resta de base y acciones, máscaras de factibilidad y continuación H2 con valores predichos. Ya no se usa literalmente el mínimo de pérdidas futuras reales por muestra como valor desplegable.
2. `crossfit.py`: selección interna de lambda, cuantil y aumentador; generación OOF de rutas y persistencia atómica de contratos.
3. `baselines.py`/`pilot.py`: mejor individual interno de seis candidatos, par fijo ResNet+SigLIP, cascada de dos etapas, H1/H2 y estado enriquecido.
4. `executor.py`: infraestructura de extracción bajo demanda y cronometraje por componentes; test sintético de paridad.
5. Reporte v2: agregación equiponderada por dataset y seis contrastes Wilcoxon bilaterales con Holm. Se evita tratar los 27 folds como 27 datasets.

Son avances de implementación y evaluación. No se borran porque la hipótesis central no esté confirmada.

## 3. Resultados recalculados

Macro-F1 medio dentro de cada dataset; media final equiponderada entre seis datasets. No se mezclan clasificadores: esta suite usa clasificadores lineales SVM por ruta.

| Dataset | Mejor individual (6) | Cascada base+1 | H1 | H2 | H2 enriquecido | Completa-6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DTD | 0,844691 | 0,831040 | 0,839305 | 0,840143 | 0,836103 | 0,865810 |
| FMD | 0,969997 | 0,950951 | 0,965984 | 0,968914 | 0,967902 | 0,973978 |
| CUReT | 0,993763 | 0,996086 | 0,993778 | 0,993778 | 0,993778 | 0,998931 |
| Outex oficial | 0,893410 | 0,913124 | 0,910104 | 0,910082 | 0,910082 | 0,932183 |
| Soil | 0,856588 | 0,846509 | 0,865229 | 0,857948 | 0,850384 | 0,878746 |
| KTH-TIPS2-b | 0,932607 | 0,939946 | 0,935749 | 0,939040 | 0,932266 | 0,954787 |
| Media de datasets | 0,915176 | 0,912943 | 0,918358 | 0,918317 | 0,915086 | 0,934073 |

Costos estimados medios: individual 32,3478 ms; cascada 25,8750; H1 24,8357; H2 25,8908; enriquecido 25,6485; Completa-6 131,19. Estos números **no son mediciones online de la política**.

- H2−Completa-6: −0,015755, es decir **−1,5755 puntos porcentuales**, con ahorro estimado 80,3 %. Pierde F1 en los seis datasets y no satisface el margen puntual de 0,5 p.p.
- H2−H1: −0,00004075; H2 consume aproximadamente 1,0551 ms modelados más. No hay ventaja media de H2 en esta suite.
- Enriquecido−H2: −0,003232. Agregar PCA de contenido no mejora el promedio observado.
- H2−mejor individual: +0,003142, pero gana en cuatro datasets y pierde en dos. En DTD y FMD el individual tiene mayor F1 y menor costo modelado que H2.
- H2−cascada: +0,005375; gana tres datasets y pierde tres, con costo medio prácticamente igual. No es superioridad general ni comparación contra Top-k22.

### Estadística reproducida

Wilcoxon bilateral sobre seis diferencias de medias por dataset; `scipy.stats.wilcoxon`, comportamiento por defecto, ceros eliminados en H2–H1. Holm sobre los seis contrastes del reporte v2. W–D–E es conteo de victorias/derrotas/empates, no el estadístico de Wilcoxon. No se ejecutó SCI2S/Java en esta revisión.

| H2 frente a | Delta medio | W–D–E | p crudo | p Holm |
| --- | ---: | ---: | ---: | ---: |
| ResNet fija | +0,069969 | 6–0–0 | 0,03125 | 0,1875 |
| Mejor individual interno (6) | +0,003142 | 4–2–0 | 0,43750 | 1,0000 |
| Par fijo ResNet+SigLIP | +0,009995 | 5–1–0 | 0,06250 | 0,2500 |
| Cascada base+1 | +0,005375 | 3–3–0 | 0,43750 | 1,0000 |
| H1 | −0,000041 | 3–2–1 | 0,81250 | 1,0000 |
| Completa-6 | −0,015755 | 0–6–0 | 0,03125 | 0,1875 |

Ningún contraste ajustado rechaza a 0,05. No se concluye equivalencia ni no inferioridad. Los seis datasets y la exposición histórica limitan potencia y generalización; la corrección de seis p-valores no neutraliza todas las decisiones exploratorias anteriores.

## 4. Hallazgos que mantienen abiertas las puertas del plan

### A. La suite no ejercita dos adquisiciones adicionales

Todas las condiciones guardan presupuesto 35,0 ms y lambda seleccionado 0,001 (extremo inferior de la grilla). Con los costos actuales:

```text
ResNet: 12,39
ResNet + SigLIP: 24,52
ResNet + SigLIP + BEiTv2: 37,19 > 35
ResNet + DINOv2: 70,49 > 35
```

Trazas H2: 1.722 STOP en base; 30.262 imágenes con una adquisición; cero con dos. Acciones adquiridas: BEiTv2 9.546, EVA02 10.328, SigLIP 10.319, ConvNeXt 69; DINOv2 ninguna.

Esto no es el antiguo error de restablecer el presupuesto: **el límite actual sí se respeta**, pero impide probar el mecanismo propuesto. Diferencias H1/H2 pueden provenir de usar pérdida observada frente a riesgo STOP predicho, sin ninguna continuación de dos adquisiciones. El extremo de lambda tampoco autoriza bajar su valor mirando test; cualquier nueva grilla pertenece al siguiente piloto interno documentado.

### B. Error de emparejamiento de referencias22

`find_confirmatory_reference_metrics` en `src/fsc_tex/baselines.py` usa `int(condition)` como fold; para strings no numéricos usa 0. En cambio `src/run_confirmatory_nested.py` guarda `official_split - 1` y CUReT `a_to_b:0`, `b_to_a:1`.

Ejemplos comprobados:

- DTD condición 1 importa Completa-22 **0,87009487** (fold 1), cuando su condición corresponde al fold 0 (**0,86628328**).
- CUReT `b_to_a` importa **0,99786151** del fold 0; corresponde al fold 1 (**1,0**).
- Cobertura de cada referencia importada: DTD 9/10, FMD 5/5, CUReT 2/2 (no ambos bien emparejados), Outex 0/1, Soil 5/5, KTH 3/4. Existir no implica ser comparable.

Además, el importador recorre varios directorios por glob, puede sobrescribir una referencia con otra variante y no fija seed, protocolo, hashes ni fuente de cada fila. KTH requiere distinguir 3→1 y validación interna agrupada de otras variantes. **Poner estos valores en cuarentena; no promediarlos, rellenar ausentes con cero ni corregir silenciosamente los JSON históricos.** Generar después una unión validada en artefacto nuevo. No requiere volver a entrenar para reparar el índice.

### C. Ahorro físico y paridad real todavía pendientes

La suite llama a `HardwareCostModel`: suma constantes históricas más overhead supuesto de 0,45 ms por bloque. No ejecuta `benchmark_physical_online_parity` ni guarda tiempos de extracción por imagen.

El test `test_fsc_tex_online_parity.py` usa vectores sintéticos devueltos por funciones mock para ResNet/SigLIP. No valida equivalencia de pesos, transformaciones ni rutas con imágenes reales. El registro online solo implementa ResNet, BEiTv2, DINOv2 y SigLIP: **faltan ConvNeXt y EVA02**, ambos presentes en las rutas de v2. El warmup del grafo completo los solicita y no puede completar esa configuración sin implementación adicional.

El tiempo total del ejecutor suma cronómetros parciales y deja fuera, entre otras operaciones, la predicción final repetida al salir del bucle. Antes de llamarlo end-to-end, medir también un cronómetro envolvente. Registrar residencia/modelos, warmup, VRAM y condiciones de hardware; costos previstos no garantizan un límite físico por imagen.

### D. La puerta R4 no prueba lo que su PASS sugiere

En `pilot.py`, PASS depende solo de mejorar a ResNet y ahorrar al menos 20 % del costo estimado de Completa-6. El booleano `epsilon_margin_satisfied` usa 0,01, no el 0,005 del plan, y **no participa en PASS**.

De 27 condiciones: 26 PASS; de esos 26, **18 incumplen incluso 0,01**. La restante es INCONCLUSIVE. No se exige superar individual/cascada, ni paridad física. No interpretar esos PASS como aprobación científica de R4.

### E. Validación y alcance aún parciales

- Base fija ResNet; cinco aumentadores predefinidos; mejor individual entre esos seis. No hay búsqueda conjunta base+política entre 22 ni respaldo residual de Top-k/GFS.
- La cascada llamada `Cascade_TopK_Prospective` es base más un aumentador seleccionado internamente. En DTD condición 1 su p95 modelado es 70,49 ms; H2 no puede superar 35 por ruta. Comparar contrato de presupuesto medio vs duro antes de atribuir ventaja a la política.
- H1 y enriquecido reutilizan lambda de H2. El enriquecimiento PCA se ajusta sobre todo T_train, no se valida con la misma tubería enriquecida en cada fold del tuning; no demuestra fuga de test, pero no satisface el cross-fitting completo del plan.
- Las features OOF de presupuesto toman por defecto 1,0, mientras las features de inferencia reciben milisegundos restantes. La máscara de acciones sí respeta el presupuesto; falta coherencia en la representación aprendida, especialmente antes de mezclar presupuestos.
- `audit.json` fija a `true` varias garantías; el criterio efectivo no comprueba toda la procedencia. Los splits guardan índices externos y hash de grupos, pero no las asignaciones internas completas ni los modelos finales.
- El test de permutación crea `y_te_permuted` pero repite llamadas con los mismos argumentos a funciones que no reciben esas etiquetas; es útil como prueba de interfaz/determinismo, no prueba integral de que el pipeline no utiliza etiquetas externas en otro paso.
- La reanudación verifica existencia/tamaño de siete archivos, no igualdad de configuración/hash. Cambiar presupuesto y reutilizar el directorio podría conservar resultados incompatibles. La v3 debe tener namespace/configuración explícitos.

## 5. Estado del plan y decisión

R0 está cerrado para archivo histórico. R1 tiene el núcleo corregido, pero el mecanismo no está validado en datos reales. R2/R3/R4 son parciales; R5 es prototipo sin benchmark físico de esta suite; R6 está completo como corrida exploratoria, no como cierre confirmatorio.

Orden recomendado: (1) reparar referencias; (2) piloto interno de base+política y adquisición residual; (3) presupuestos que permitan varias adquisiciones, ablaciones equiparables y puerta de calidad/costo coherente; (4) paridad/medición real; (5) decidir si merece una suite v3. No ampliar automáticamente a 47 ni cambiar la arquitectura por el resultado observado.

La base debe seleccionarse **con** la política en entrenamiento, según calidad, costo y complementariedad residual. Mantener ResNet como control. Elegir siempre el mejor individual de F1 tampoco resuelve el problema: puede ser caro o dejar poco margen de mejora. Si H1 o una ruta estática domina, conservar la solución sencilla; no imponer H2 para sostener el nombre del método.

## 6. Revisión ARS de interpretación — 11/11 comprobadas

| Riesgo | Evaluación de esta revisión |
| --- | --- |
| Simpson | Se desagregó por dataset y se equiponderó; la media favorable frente a cascada no oculta que pierde 3/6. No se diagnosticó una paradoja formal |
| Falacia ecológica | No trasladar la media de seis datasets a garantía para cada imagen o dominio |
| Berkson | No se detectó mecanismo de selección que permita diagnosticarla; seis benchmarks seleccionados limitan alcance |
| Collider | No se identificó ajuste causal por colisionador; no se formula inferencia causal poblacional |
| Tasas base | Macro-F1 y exactitud recalculadas; no equivalen a rendimiento por clase ni garantía en clases raras |
| Regresión a la media | La mejora v1→v2 no se usa como prueba controlada de mecanismo; protocolos/tuning cambiaron |
| Supervivencia | 27/27 presentes; el generador deja de omitir silenciosamente condiciones inválidas. No usar solo los PASS |
| Búsqueda múltiple | Holm cubre seis contrastes actuales, no todo el historial experimental ni la búsqueda de diseños |
| Caminos de análisis | Exposición previa registrada; revisión de diseño posterior a resultados sigue siendo exploratoria |
| Correlación/causalidad | No atribuir diferencias H1/H2 a planificación multietapa no ejercitada; no atribuir ahorro físico a sumas de costos |
| Causalidad inversa | No aplicable como relación temporal poblacional; sí evitar justificar decisiones de diseño como si precedieran a resultados ya vistos |

**Confianza:** alta para recálculo de métricas almacenadas y diagnósticos de índices/presupuesto; cautela para generalización; afirmaciones de superioridad, no inferioridad formal y ahorro online no están respaldadas por estos artefactos.
