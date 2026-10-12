# Auditoría P0–P4 y cascada seleccionada — 10 de octubre de 2026

**Material Passport**

- Origen: academic-research-suite (ARS), experiment-agent, modo validate; revisión realizada en esta conversación.
- Versión: 1.0. Fecha: 2026-10-10. Estado: **ANALYZED**, no VERIFIED ni revisión independiente.
- Corte de código: `08c3ebb`. Cambios examinados: `17bbf0a`, `43cce0f`, `a8de0dd`, `cfb7605`, `08c3ebb`, además de cambios locales de documentación preservados. Los tres últimos aparecieron durante esta revisión y se incluyeron explícitamente en el corte.
- Método: inspección de implementación y artefactos, reconciliación de agregados/procedencia, recálculo de estadística desde agregados y tests. No se reentrenaron suites ni se repitió extracción GPU.

## 1. Dictamen

Hay avances reales después de v2: referencias alineadas, adquisiciones múltiples factibles y observadas en entrenamiento, seis extractores soportados online, un benchmark GPU pequeño y una cascada seleccionada evaluada en 27 condiciones. **No están cerrados todos los hitos P0–P4 ni demostrada la superioridad final de la tesis.**

La cascada con base seleccionada es la candidata prioritaria para una validación física y metodológica acotada. H2 sigue como hipótesis/ablación: no se justifica descartarlo universalmente, pero tampoco adoptarlo por complejidad. Los resultados nuevos no convierten automáticamente el trabajo en confirmatorio.

La auditoría anterior corresponde a [v2 en `f99115d`](AUDITORIA_FASE3_V2_2026-10-10.md). Sus referencias erróneas se preservan como historia; no deben atribuirse sin matices al importador ya corregido.

## 2. Evidencia y alcance de las comprobaciones

| Fuente | Comprobación | Alcance |
| --- | --- | --- |
| Registro canónico22 JSON | Reconstrucción en memoria coincide con archivo; hashes completos de fuentes coinciden; cada referencia presente corresponde a una única fila por dataset/clasificador/seed/fold/método | Completa y GFS 27/27; Top-k 24/27; faltan KTH 1–3 |
| Piloto P1–P3 | Lectura del código y JSON; sumas de pasos y porcentajes multietapa coherentes | DTD oficial1 y Soil fold0, solo entrenamiento; no nueva suite externa |
| P4 GPU | Código, agregados y reconstrucción del subconjunto evaluado | 20 imágenes DTD; no reproducción de mediciones |
| Cascada seleccionada | 27 claves únicas, CSV/JSON coherentes, hashes de 27 archivos de origen correctos, delta Top-k vs archivo 0 en todas las condiciones | Agregados consistentes, no recálculo desde predicciones ausentes |
| Selecciones de cascada guardadas | 54/54 decisiones (dos variantes por condición) coinciden con el mínimo costo entre candidatos elegibles y con la ruta/base/q del resultado | Reconciliación de decisiones desde agregados, no reproducción de OOF |
| Top-k cascada vs registro 22 | Coincidencia numérica exacta en las 23 condiciones no KTH | KTH: tres referencias ausentes y una diferente |

No se modificaron JSON originales, embeddings, manifiestos ni resultados experimentales. Se corrigieron documentos, generadores de reporte y etiquetas/gráficas derivadas. No hubo push, pull ni relanzamiento de suites.

### Huellas del corte

| Artefacto | SHA-256 |
| --- | --- |
| `results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.json` | `d9362a9cfa0d6f5babb1084ad9205da62951e33b0f5d9d688a063cd97f166f41` |
| `results/exploratory/fsc_tex/p1_p3_internal_pilot_report.json` | `6544a695d0c9cf47334199d9c72d1dbee40e1e9d14f96faa2c303c71f6cc1cd0` |
| `results/exploratory/fsc_tex/p4_physical_benchmark_report.json` | `60e783d7b4f7cfb88fbf6fe53ee0a6cf8301c90fa984339eacfb78767c49b86f` |
| `results/exploratory/topk_cascade/cheap_stage_selected_primary22/rows.csv` | `6920cead6e25fa6c6458165f04fc43cee994d18fc1069e5a9c0148a5c71ce902` |

## 3. Hallazgos por prioridad

### A1. KTH reutiliza un Top-k distinto del registro corregido

Los cuatro archivos de cascada declaran calibración interna por `sample`, pero sus subconjuntos caros provienen del control Top-k anterior de `ngram22_beitv2`. El hash de ese control es `c3dce2a317364f584306875dbb1edff6adfe3d44dd3d7539432525714b857e6d`. El registro P0 usa `ngram22_beitv2_innergrp_sample_v1`, hash Top-k `adf034aa893f4c7590302e62c42ac85288f7a38161001334f2fd2002fb24293f`.

En condición 4, Top-k anterior selecciona `vit_b16`, macro-F1 0,8736003166; el control corregido selecciona `beitv2_base_final`, 0,9194970486. Recalibrar márgenes por sample no rehace la selección del subconjunto original. No corresponde llamar a ambos la misma referencia canónica. Esto prueba una discrepancia de procedencia, no por sí solo que las nuevas predicciones externas estén filtradas.

**Corrección de reporte:** conservar las 27 condiciones descriptivas, identificar Top-k como «de origen» y excluir KTH del contraste conjunto de cuatro métodos hasta reconciliarlo. Las pruebas actualizadas usan cinco datasets, con exclusión motivada por procedencia y declarada como posterior a la ejecución. No se rellenaron los tres Top-k faltantes con otra variante.

### A2. No significancia se presentaba como equivalencia

El reporte anterior declaraba paridad, preservación exacta de precisión y cierre definitivo de la tesis. También destacaba p=0,0366 sobre 27 condiciones, aunque su Holm era 0,1097 y esas condiciones no son datasets independientes. Se retiraron esas conclusiones y la inferencia con N=27. No rechazar diferencias no demuestra equivalencia/no inferioridad. El margen interno de 0,005 no es una garantía externa: Outex pierde 0,0056248465 respecto de Top-k.

Los contrastes corregidos se reproducen en [reporte de cascada](REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md). Mantienen tres comparaciones bilaterales con Holm, ahora con cinco datasets reconciliados. GFS se incluye descriptivamente y no se añade retrospectivamente a la familia buscando significancia. No se ejecutó Java/SCI2S en esta auditoría.

### A3. El ahorro de 75,5% es proyectado, no cronometrado

La nueva cascada usa sumas de tiempos de componentes y tasas de escalamiento sobre embeddings. Los perfiles son KTH para KTH y Outex como proxy para los otros cinco datasets; ViT-B/16 puede heredar el costo KTH. Se omiten componentes de ejecución completa. La media equiponderada por dataset pasa aproximadamente de 529,9 a 130,0 ms modelados: reducción proyectada de 75,5%. No acredita «75,5% menos tiempo real», ahorro >90% frente a Completa, ni eficiencia sin precedentes.

Se corrigieron reporte y figuras: «costo proyectado», «Top-k de origen» y separación de Top-k directo respecto del escalamiento. Parar en etapa económica no implica clasificar correctamente. P4 pertenece a otra configuración y no valida estos porcentajes.

### A4. La puerta P1–P3 omite criterios calculados

En `scripts/run_fsc_tex_p1_p3_internal_pilot.py`, `evaluate_continuity_gate` calcula cinco criterios, pero `all_passed` usa 1, 2, 4 y permutación; omite 3 (par estático) y 5 (H2 vs H1). DTD a 45 aparece PASS aunque el criterio 5 es falso. DTD a 75 tiene los cinco verdaderos bajo esas reglas, pero la mejora H2–H1 es solo +0,000089928 con costo +0,804455 ms modelados. No demuestra una mejora robusta.

El margen local es 0,01 frente a 0,005 del plan; «beats best» admite más F1 aun con más costo. Soil45/75 conserva fallos en criterios 2/3/5. No se evalúa una puerta completa para la base SigLIP. **No se reparó la lógica experimental durante esta auditoría**: hacerlo requiere versión nueva, pruebas y evaluación interna consistente; no cambiar retroactivamente los PASS archivados.

### A5. El piloto interno no es una evaluación anidada independiente de toda la selección

- P1 estudia seis individuos, no los 22; compara tres bases con pares/oráculos. P2 ejecuta políticas con ResNet y SigLIP, no selección conjunta entre las tres bases.
- P2 selecciona hiperparámetros sobre todo `T_train` antes de evaluar sobre folds internos reutilizados. Esos folds influyen en la selección: los F1 internos no son una estimación externa a toda la sintonización. El test externo no forma parte de este piloto.
- P3 construye PCA16 por fold pero no conecta `pca_oof` al predictor/política final. No verifica el estado enriquecido de extremo a extremo.
- P3 baraja etiquetas una vez, ajusta clasificadores OOF y entrena/evalúa la política sobre sus mismas filas objetivo OOF. Es una comprobación de cordura, no permutación del pipeline completo ni p-valor formal. El corte 1,5/K es heurístico.
- No se guardan predicciones/trazas por fila para P1–P3. Las medias se transcriben del JSON y se comprueba su aritmética; no se certifican como métricas recalculadas desde vectores.

Sí está corregida la propagación coherente del presupuesto a features OOF/tuning/ejecución en las rutas inspeccionadas de `crossfit.py` y `pilot.py`. No confundir esto con cerrar todas las restantes verificaciones.

### A6. P4 es un piloto físico limitado y su PASS usa un umbral diferente

- RTX4060, DTD oficial1, presupuesto45; `test_idx[:20]` corresponde a **20 imágenes de la clase banded**. El perfil individual toma las primeras 10, también banded. No es muestra estratificada del dataset.
- Promedio guardado: extracción41,1044 + compuerta2,4585 + clasificador1,4695 =45,0323 ms. Es suma de temporizadores, no un reloj envolvente imagen→predicción. Quedan fuera operaciones como la predicción final repetida y trabajo externo al temporizador.
- Paridad: ruta final 18/20 (90%); predicción19/20 (95%). Se comparan estados finales, no secuencias ordenadas completas. El script considera PASS al 90%; el helper general exigía95% para ambas. No se declara paridad estricta.
- VRAM residente1974,4 MiB, pico2025,6 MiB. Son agregados reportados, no remedidos en esta auditoría.
- Hay soporte nuevo ConvNeXt/EVA. Debe verificarse identidad de preprocessing/checkpoint: EVA original usa transform de timm y el ejecutor una transformación manual, posible explicación a investigar, no causa demostrada.
- No hay tiempos físicos pareados de Completa/Top-k/cascada para estas 20 imágenes ni registros individuales persistidos. No permiten estimar ahorro físico relativo o dispersión fiable.

### A7. Persistencia y robustez incompletas

El registro P0 actual es consistente, pero el consumidor no valida automáticamente todos los hashes/duplicados y puede usar fallback silencioso. La cascada permite cache hit por existencia, sin comprobar configuración. Los nuevos JSON no conservan todos los modelos, índices, predicciones, trazas y hashes necesarios para una auditoría independiente integral. Hay que consolidar estos contratos antes de una suite nueva.

## 4. Resultados que sí pueden citarse

- [Pilotos P1–P4](RESULTADOS_PILOTOS_2026-10-10.md): separar resultados internos de medición física limitada.
- [Cascada en 27 condiciones](REPORTE_CASCADA_ADAPTATIVA_CANONICA_27.md): agregados de la variante archivada, costos proyectados y KTH identificado por separado.
- [Suite v2](FASE_3_V2_REPORTE_SUITE_COMPLETA.md): 27 condiciones históricas, con métricas auditadas desde predicciones; no sustituirlas por resultados internos nuevos.

## 5. Revisión ARS: 11/11 riesgos comprobados

| Riesgo | Evaluación en este corte |
| --- | --- |
| Simpson | No se detectó una inversión universal; resultados heterogéneos, reportados por dataset además de media equiponderada |
| Falacia ecológica | La media entre datasets no garantiza calidad/latencia por imagen; se retiraron garantías externas |
| Berkson/selección | P4 restringido a una clase; no generalizar a toda la población de texturas |
| Collider | No se identificó un ajuste causal de este tipo; la selección de rutas no justifica inferencia causal |
| Tasa base | Macro-F1 no es exactitud ni fracción de imágenes resueltas; clases/cobertura importan |
| Regresión a la media | No hay estudio pre/post causal; elegir tras resultados extremos podría sobreestimar mejora, por eso se mantiene como exploratorio |
| Supervivencia | Se conservan resultados negativos, Top-k directo y faltantes KTH explícitos; no ocultar condiciones difíciles |
| Búsqueda múltiple | p bruto27 no sostiene superioridad; familia de tres contrastes y Holm; no ampliar buscando rechazo |
| Caminos analíticos | Presupuestos/bases/cascada se diseñaron tras v2; exclusión KTH de esta auditoría es post hoc documentada |
| Correlación/causalidad | Se retira «causa fundamental: saturación»; no hubo ablación que aislara esa explicación |
| Causalidad inversa | No se detectó una hipótesis direccional de este tipo; no inferir causalidad de asociaciones de rutas/errores |

La evaluación original de equivalencia/eficiencia física requiere **corrección obligatoria (RED_FLAG)**. Los agregados reconciliados mantienen **CAUTION**: N pequeño, diseño exploratorio, predicciones nuevas ausentes y limitaciones de protocolo. No se certifica novedad bibliográfica en esta revisión local.

## 6. Verificación de software y siguiente puerta

**43 tests aprobados en 33,46 s**, incluyendo FSC-Tex, referencias, piloto, reporte y cascada. Se agregaron regresiones para claves duplicadas, discrepancias CSV/JSON y separación de KTH. Se regeneraron ambos reportes y las tres figuras (PNG/PDF), con inspección visual de los PNG. Las cuatro huellas de la sección 2 se comprobaron nuevamente sin cambios; `git diff --check` no informó errores.

Comando de verificación desde la raíz Linux:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-confirmatory/bin/python -m pytest -q -p no:cacheprovider tests/test_fsc_tex_policy.py tests/test_fsc_tex_utility.py tests/test_fsc_tex_no_leakage.py tests/test_fsc_tex_baselines.py tests/test_fsc_tex_pilot.py tests/test_fsc_tex_online_parity.py tests/test_fsc_tex_report.py tests/test_fsc_tex_reference_pairing.py tests/test_fsc_tex_p1_p3_internal_pilot.py tests/test_cheap_stage_selected_report.py
```

La primera pasada de los tests de reporte encontró una expectativa literal obsoleta sobre el importador histórico. Se actualizó para distinguir v2 del P0 corregido y la suite completa pasó. Tras el ajuste final de legibilidad de las figuras se repitieron sus tests y los del reporte de cascada: **9 aprobados en 4,53 s**. Ningún test automático certifica por sí solo integridad científica, novedad o ahorro físico.

Orden de continuación: reconciliar procedencia KTH; fijar contratos de predicción y selección; corregir la puerta y validación interna en una versión nueva; comparar físicamente la cascada y controles sobre imágenes estratificadas; solo entonces decidir otra suite o la adopción final. El plan v1.3 detalla entregables y criterios de aceptación. No añadir más extractores para compensar estas carencias metodológicas.
