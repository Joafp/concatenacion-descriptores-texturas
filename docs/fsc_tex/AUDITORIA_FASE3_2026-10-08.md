# Auditoría de resultados FSC-Tex: suite de 27 condiciones

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: validate; actualización del plan solicitada por el usuario.
- Origin Date: 2026-10-08.
- Verification Status: ANALYZED. Métricas recalculadas desde predicciones; no se repitió el entrenamiento completo ni la extracción online.
- Version Label: phase3_audit_v1.
- Alcance: revisión local de código, artefactos, aritmética, particiones y pruebas unitarias. No constituye una revisión independiente ni una certificación de ARS.

## 1. Veredicto

**Existen las 27 condiciones y las cifras de macro-F1 y exactitud de los métodos con predicciones guardadas coinciden exactamente. Sin embargo, el informe no demuestra todavía la propuesta multietapa, ahorro físico extremo a extremo ni superioridad frente a Completa-22, Top-k22 o GFS.**

La ejecución es una exploración con seis extractores candidatos y costos estimados. Un problema de presupuesto hace que la política ejecutable solo pueda usar ResNet-50 y, opcionalmente, SigLIP. La comparación H2–H1 no valida anticipación multietapa en esas condiciones.

**Estado recomendado:** preservar los resultados como `phase3_v1_exploratory`; cerrar los errores de implementación y evaluación antes de un nuevo barrido. No declarar completada la Fase 3 metodológica del plan original.

## 2. Evidencia y comprobaciones realizadas

Commits locales inspeccionados: `2bf1604` y `136532c`. El segundo contiene el reporte, el evaluador y los resultados mencionados por el usuario. No se hizo pull, push ni modificación del código experimental durante esta auditoría.

Artefacto: `results/exploratory/fsc_tex/phase3_full_suite/summary_27_conditions.json`.

SHA-256 del resumen auditado:

```text
d28972a33e9185e049054c579101e70bc1a5f00274d78f1dbf2c9f70d4bfbe19
```

Comprobaciones:

- 27 condiciones únicas: DTD 10, FMD 5, CUReT 2, Outex 1, Soil 5 y KTH 4.
- Los 27 `metrics.json` coinciden con sus registros en el resumen.
- Recalculados macro-F1 y exactitud de **459 vectores de predicción**: 17 métodos por condición. Diferencia máxima: **0** en ambas métricas.
- `Oracle_STOP` no tiene vector de predicciones guardado; su métrica no recibió esa comprobación independiente.
- Las etiquetas de test guardadas coinciden con la reconstrucción de las 27 particiones a partir de los manifiestos actuales. No hay solapamiento externo de `group` en esas reconstrucciones.
- DTD conserva la purga de duplicados del cargador. KTH usa las particiones 3→1 y `sample` para los grupos productores internos.
- Esta comprobación de etiquetas no sustituye una auditoría de píxeles, pesos y embeddings ni demuestra por sí sola la identidad de filas dentro de cada clase. Faltan IDs de muestra y hashes en las predicciones guardadas.
- Pruebas existentes: **9 passed** con `PYTHONPATH=src .venv-confirmatory/bin/python -m pytest -q -p no:cacheprovider tests/test_fsc_tex_policy.py tests/test_fsc_tex_utility.py`. No cubren los defectos de integración encontrados.

## 3. Resultados que sí se pueden reproducir

Las medias siguientes provienen de los artefactos, no de un nuevo entrenamiento. H2 y H1 usan lambda=0. La columna de cascada selecciona retrospectivamente la mejor variante en test y por eso **no es un comparador seleccionado válidamente para despliegue**.

| Dataset | Base ResNet | H1 | H2 | Cascada elegida en test | Completa-6 | H2 − Completa-6, p.p. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DTD | 0,7303 | 0,8402 | 0,8402 | 0,8346 | 0,8658 | −2,5613 |
| FMD | 0,8517 | 0,9651 | 0,9651 | 0,9551 | 0,9740 | −0,8891 |
| CUReT | 0,9625 | 0,9877 | 0,9877 | 0,9963 | 0,9989 | −1,1223 |
| Outex13 | 0,8809 | 0,8890 | 0,8929 | 0,9117 | 0,9322 | −3,9249 |
| SoilOriginal | 0,8070 | 0,8509 | 0,8509 | 0,8615 | 0,8787 | −2,7821 |
| KTHTIPS2b | 0,8577 | 0,9017 | 0,9114 | 0,9422 | 0,9548 | −4,3430 |
| Media de 27 condiciones | 0,8086 | 0,8872 | 0,8887 | 0,8927 | 0,9137 | −2,5004 |
| Media equiponderada de 6 datasets | 0,8483 | 0,9058 | 0,9080 | 0,9169 | 0,9341 | −2,6038 |

El promedio de 27 condiciones pondera DTD diez veces y Outex una. Es válido como resumen de condiciones si se identifica así; no es la media equiponderada por dataset.

Correcciones a las afirmaciones del informe:

- DTD: **9 victorias y 1 derrota**, no 10/10. En split 3, H2 pierde 0,00157517 de macro-F1 frente a `Cascade_q50`.
- FMD: 4/5 victorias en F1, pero el costo estimado aumenta de 17,9949 a 22,9188 ms. Hay un compromiso calidad–costo, no dominancia en ambas métricas.
- Outex y Soil: H2 lambda=0 tiene menor F1 y mayor costo estimado que la cascada seleccionada retrospectivamente.
- La pérdida media de 2,5004 p.p. frente a Completa-6 es cinco veces el margen práctico de 0,5 p.p. propuesto en el plan. Una razón «retiene el 97,3 % del F1» no demuestra no inferioridad.
- Ninguno de estos datos demuestra una comparación ganadora contra Completa-22, Top-k22 o GFS: no aparecen como métodos en esta suite.

## 4. Hallazgos de implementación y evaluación

### A. Presupuesto: la política solo puede adquirir SigLIP

Fuentes: `scripts/run_fsc_tex_phase3_suite.py`, llamadas a `select_action` en líneas 412 y 444; `src/fsc_tex/policy.py`, parámetro `remaining_budget=1.0` y filtro de acciones; `src/fsc_tex/cost_model.py`.

El ejecutor no pasa presupuesto y no lo actualiza tras adquirir. El costo está normalizado por ResNet más overhead: 12,39 ms. Por tanto:

| Acción | Costo incremental normalizado | Factible con presupuesto por defecto 1 |
| --- | ---: | --- |
| SigLIP | 0,9790 | Sí |
| BEiTv2-final | 1,0226 | No |
| ConvNeXt V2-T | 1,3019 | No |
| EVA02 | 1,5956 | No |
| DINOv2-base | 4,6893 | No |

Se comprobó llamando al grafo actual: acciones iniciales `['STOP', 'siglip_base']`; después de SigLIP: `['STOP']`.

Además, **los 270 costos medios guardados para variantes FSC-Tex** coinciden, dentro de 0,0001 ms, con esta fórmula de dos estados:

```text
costo_estimado = 12,39 + fracción_escalada × 12,13
```

No hay trazas de rutas guardadas para reconstruir cada decisión, pero el código y los agregados son consistentes con esa restricción. Cambiar la base ahora también cambiaría accidentalmente la factibilidad por la normalización: no se debe interpretar ese efecto como mérito de una base mejor.

**Acción pendiente:** presupuesto total explícito, unidades comunes, descuento por adquisición y validación de factibilidad coherente en entrenamiento e inferencia. No basta con aumentar el valor por defecto.

### B. Los objetivos H2 usan un oráculo retrospectivo, no el valor de la política desplegable

En `src/fsc_tex/policy.py:145`, `q_options` empieza con la pérdida real por muestra; se agregan objetivos basados en pérdidas reales futuras y se toma su mínimo en la línea 174. H2 aprende después a predecir ese mínimo. El entrenamiento tampoco aplica el presupuesto al construir esas opciones.

El problema no es usar etiquetas de entrenamiento para supervisar; eso es legítimo. El problema es optimizar el mejor resultado por muestra con conocimiento de opciones futuras, aunque la política no tenga información para elegirlo. En general:

```text
E[min_a pérdida_real(a) | estado] <= min_a E[pérdida_real(a) | estado]
```

La desigualdad puede ser estricta: con dos acciones indistinguibles que aciertan en mitades opuestas, el oráculo tiene error 0 y cualquier elección sin información tiene error esperado 0,5. Ese mínimo no es el riesgo alcanzable por la política.

**Acción pendiente:** usar valores estimados por la política de menor horizonte, congelada, con validación cruzada apropiada; o rollouts de una política congelada sobre muestras reservadas del entrenamiento. Conservar el mínimo de pérdidas reales exclusivamente como diagnóstico oracular. El antecedente de regresión de riesgo futuro distingue justamente el objetivo estimado de la adquisición desplegable: [BRiG-AFA, sección 4](https://arxiv.org/html/2608.02305v1).

### C. Latencia estimada, no medición de esta política

`HardwareCostModel` suma constantes por extractor y 0,45 ms por bloque. `cumulative_cost_ms` no cronometra una ejecución. `incremental_cost` recibe el estado pero no lo usa para reutilización de operaciones. Para nombres desconocidos hay un valor por defecto de 20 ms, que debe sustituirse por error explícito.

La tabla coincide en gran parte con perfiles antiguos de 50 imágenes de **test de Outex**, documentados en `Outex_official1_primary22_online_components.json`. Ese perfil excluye carga de modelos y contiene limitaciones explícitas; no demuestra la latencia del nuevo sistema en los seis datasets. El overhead de 0,45 ms no viene acompañado de una medición propia en esta suite.

Así, 131,19 ms, 22,35 ms y el ahorro cercano al 83 % son **estimaciones de un modelo aditivo de costo**, no mediciones online ni prueba de eliminación de colas p95. También se cobra overhead por bloque a la fusión fija aunque esta no ejecuta una compuerta por bloque: debe medirse el trabajo realmente realizado por cada método.

### D. Completa-6 y ausencia de controles competitivos

El evaluador fija ResNet y cinco candidatos: SigLIP, BEiTv2-final, DINOv2-base, ConvNeXt V2-T y EVA02. `Full_Fusion_5cand` concatena **seis bloques contando la base**.

No están RGB N-grams, DINOv2-small/large ni el resto de la biblioteca. No hay mejores individuales elegidos internamente, SigLIP solo, BEiTv2 solo, Top-k22, GFS ni la cascada Top-k completa anterior. Esto impide atribuir la ventaja frente a ResNet a una necesidad de adquisición adaptativa: un solo descriptor fuerte podría explicar parte de ella.

### E. No se ejecutó la selección interna completa descrita

El encabezado promete particiones internas R/V, pero el cuerpo solo genera predicciones con dos folds productores, ajusta los clasificadores finales y evalúa la grilla en test. `inner_cv_folds` se declara pero no se utiliza; C está fijado en 1; el YAML y el registro no gobiernan la corrida.

El reporte usa `max(... test_results[k]['macro_f1'])` para escoger la cascada por condición. Los umbrales numéricos sí se calculan con márgenes de entrenamiento; **la elección de cuál umbral reportar se hace con test**. Esta selección favorece a la cascada, no a FSC, pero sigue siendo inválida como elección prospectiva y contradice «cero filtración» del procedimiento completo.

No se encontró uso directo de etiquetas de test para ajustar los regresores FSC del script. Tampoco puede acreditarse que la biblioteca, lambda o las afirmaciones se congelaran antes de inspeccionar resultados. Diferenciar esas cuestiones evita acusar de filtración de entrenamiento algo que es selección posterior o falta de trazabilidad.

### F. Información de estado limitada y desalineación con macro-F1

La representación actual contiene máscara de seis posiciones, margen, presupuesto constante y tres scores ordenados. **No contiene embeddings observados ni identidad de las clases de esos scores.** Por eso no se ha probado la hipótesis de complementariedad dependiente del contenido frente a solo incertidumbre.

La función de pérdida admite pesos, pero el evaluador llama `compute_loss` sin ellos. La política usa error 0–1 no ponderado; el balanceo de clases del SVM no lo convierte en una pérdida macro-F1 ni balanceada para la compuerta.

### G. Reproducibilidad incompleta

Los estados finales se calculan pero no se guardan; faltan trazas, tiempos por evento, modelos congelados, IDs de fila y hashes/configuración en cada condición. La escritura llamada «atómica» usa directamente `open(..., 'w')`; el checkpoint se reutiliza por existencia, sin comprobar compatibilidad de configuración.

Las particiones oficiales de DTD, Outex y KTH, las mitades de CUReT y los folds construidos de FMD/Soil no deben describirse todos como «27 particiones oficiales». El manifiesto de Soil tiene 962 grupos para 1140 imágenes; esa estructura no prueba la descripción de «bandejas físicas» del informe.

## 5. Revisión estadística

Se reprodujeron los p-valores del informe con su misma elección de unidad y alternativa. Eso reproduce un cálculo; no valida sus supuestos.

| Contraste | Cálculo original: 27 condiciones | Diagnóstico: una media por dataset | Interpretación |
| --- | ---: | ---: | --- |
| H2 > H1, unilateral | p=0,0215572 | p=0,25 | La ventaja no queda respaldada por este contraste entre datasets |
| H2 > ResNet, unilateral | p=7,45058×10⁻⁹ | p=0,015625 | Mejora frente a esta base débil, no frente al mejor descriptor; exploratorio y sin ajuste de multiplicidad |
| H2 vs Completa-6, bilateral | p=1,49012×10⁻⁸ | p=0,03125 | H2 tiene menor F1 medio en los seis datasets; tampoco es una prueba de no inferioridad |

Las 27 condiciones contienen particiones dependientes, no 27 datasets independientes. H1 y H2 lambda=0 producen **predicciones idénticas en las 22 condiciones de DTD, FMD, CUReT y Soil**. Solo cambian Outex y las cuatro de KTH. El p=0,0216 no establece una ganancia multietapa general y menos aún resuelve el defecto de presupuesto.

Los p-valores por seis datasets también son diagnósticos posteriores, con baja potencia, ceros y sin corrección por todos los contrastes explorados. No sustituyen el protocolo pendiente. La comparación entre datasets debe identificar su unidad y los contrastes previstos: [Demšar, 2006](https://www.jmlr.org/beta/papers/v7/demsar06a.html). La selección de hiperparámetros necesita evaluación separada del ajuste: [documentación de validación anidada de scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

### Revisión de 11 riesgos estadísticos de ARS

Cobertura: **11/11 revisados**; no significa «ausencia de falacias».

| Riesgo | Evaluación en esta auditoría |
| --- | --- |
| Simpson | No se detecta inversión universal, pero el promedio global cambia de ponderación y oculta heterogeneidad |
| Falacia ecológica | No inferir corrección fiable de cada imagen a partir del F1 medio; rutas no guardadas |
| Berkson/selección | Biblioteca fija de seis bloques y base débil limitan la población de comparadores; no se establece paradoja concreta |
| Colisionador | No identificado en el diseño inspeccionado; no hay ajuste causal que permita certificarlo universalmente |
| Tasas base | Pérdida 0–1 sin pesos en la compuerta frente a métrica macro; se requiere desglose por clase |
| Regresión a la media | No es un estudio pre/post; vigilar selección posterior de condiciones favorables |
| Supervivencia | Las 27 condiciones están; faltan registros que permitan descartar reintentos o configuraciones previas omitidas |
| Comparaciones múltiples | Se exploran lambdas, horizontes y umbrales sin corrección integral ni contraste primario trazado |
| Caminos analíticos | Selección de mejor cascada en test y afirmaciones incrustadas manualmente en el generador |
| Correlación/causalidad | El control no aísla anticipación Bellman: H2 cambia objetivos pero no puede ejecutar una segunda adquisición |
| Causalidad inversa | No pertinente como explicación temporal del algoritmo; el problema relevante es el uso retrospectivo del test |

## 6. Consecuencia para el plan

Primero corregir y auditar presupuesto, objetivos de valor, controles y selección interna. Después comparar bases bajo la misma unidad de costo. Luego ejecutar un piloto genuinamente multietapa y medirlo online. Solo después procede repetir las 27 condiciones y redactar conclusiones de rendimiento.

Se preservan los artefactos originales; el informe previo no debe usarse como evidencia de eficiencia física o superioridad confirmatoria. El plan operativo actualizado está en `docs/PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md`, versión 1.1.
