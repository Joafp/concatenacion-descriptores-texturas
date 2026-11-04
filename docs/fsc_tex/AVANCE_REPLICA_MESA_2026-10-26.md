# Avance de réplica de la mesa — 26-10-2026

## Material Passport

- Origin Skill: experiment-agent (ARS-Codex, ejecución local guiada)
- Origin Mode: run
- Origin Date: 2026-10-26
- Verification Status: ANALYZED — reproducción de selección/predicciones archivadas; no extracción independiente ni medición física
- Version Label: mesa_replica_recuperada_v2

## Alcance y estado

Se inició P1 del [plan vigente](PLAN_CIERRE_VIGENTE_2026-10-25.md), bajo el [protocolo fijado antes de ejecutar](PROTOCOLO_REPLICA_MESA_2026-10-26.md). Esta es una réplica exploratoria de desarrollo, no un ensayo confirmatorio ciego ni una evaluación nueva del test oficial. La revisión es local guiada por ARS; no constituye aprobación institucional de la tesis.

La cola está en `results/exploratory/integration_v11/replication_20261026`. Su `frozen_protocol.json` conserva comandos, configuración y hashes de fuentes. Cada condición tiene `state.json` y logs independientes; estos archivos son la fuente del estado actual, que puede avanzar después del corte de este informe.

| Condición nueva | Estado observado al corte |
| --- | --- |
| FMD, semilla 42 | Cuatro etapas completas y auditadas; estático recuperado con autorización |
| FMD, semilla 123 | Cuatro etapas completas y auditadas; estático recuperado con autorización |
| Outex, semilla 123 | Cuatro etapas completas y auditadas, sin reintentos |
| Outex, semilla 2026 | Cuatro etapas completas y auditadas, sin reintentos |
| FMD, semilla 2026 | Cuatro etapas completas y auditadas; estático recuperado con autorización |

Las cinco condiciones nuevas pasaron la auditoría de archivos, selecciones y predicciones. Outex semilla 42 pertenece al piloto histórico. El panel tiene dos datasets por tres semillas al incluir ese antecedente; no son seis datasets ni seis réplicas independientes entre dominios. Los resúmenes numéricos de abajo incluyen únicamente las cinco condiciones nuevas, sin mezclar silenciosamente el piloto histórico.

## Incidencia y recuperación autorizada completada

El programa histórico `scripts/run_static_budget_control.py` contiene al resumir cada política la comprobación `len(part) == part.row_index.nunique() == 680`. Es correcta para el desarrollo Outex del piloto, pero no para las 800 imágenes de desarrollo FMD. Las ejecuciones FMD 42/123/2026 llegaron a completar los tres pliegues del control y fallaron en esa comprobación final. No guardaron los resultados finales ni las predicciones estáticas; no se infirieron métricas de esas etapas fallidas.

Las salidas fallidas, decisiones y logs se conservan. Las fuentes congeladas no se corrigieron en caliente. `scripts/run_static_budget_control_general.py` conserva el selector y la receta de ajuste SVM originales, deriva la cobertura de los pliegues y la contrasta con `--expected-images`. Exige una salida nueva y registra el protocolo entre sus entradas verificadas.

El usuario confirmó: «Sí, corregir y repetir solo esas etapas». Se ejecutó una vez `scripts/recover_mesa_static.py --suite results/exploratory/integration_v11/replication_20261026 --execute`. Cada condición FMD guarda el resultado en `static_recovery/`, junto con `static_recovery.log` y `static_recovery_state.json`. La autorización, comandos y hashes se fijaron antes en `static_recovery_authorization.json`. Los tres procesos terminaron con código 0. Se reajustaron 6/5/8 modelos en semillas 42/123/2026, reutilizando 5/8/5 modelos, respectivamente. No se repitieron el pool, Carlos ni el híbrido.

Las doce decisiones estáticas de cada semilla coinciden byte por byte con las congeladas en su intento fallido. La corrección no cambió el método ni seleccionó un presupuesto nuevo. La cola original conserva su estado histórico `attention_required`; la auditoría resuelve explícitamente la recuperación, sin reescribir un fallo como éxito original.

## Verificaciones de software y auditoría

- Suite completa final: **94 aprobadas en 30,98 s**, incluidos los casos de recuperación sin autorización y decisiones idénticas/alteradas. Comando: `PYTHONPATH=.:src .venv-confirmatory/bin/python -m pytest tests/ -q`, con límites de dos hilos para BLAS. Los cinco tests del auditor también pasaron aisladamente en 6,73 s.
- El protocolo tiene pruebas de condiciones, parámetros y separación de salidas.
- La adaptación de cobertura tiene pruebas para 680 y 800 imágenes, rechazo de solapamientos y reutilización exacta del selector y la función de ajuste del control original.
- `scripts/audit_mesa_replication.py` reprodujo **60 selecciones estáticas y 180 decisiones de enrutamiento** entre las cinco condiciones nuevas, y recalculó métricas de 170 políticas/condiciones. Comprobó grupos, índices, transformaciones N-gramas, exclusión del test y hashes. Para FMD verificó además autorización y decisiones originales idénticas. Es auditoría de archivos guardados, no reproducción independiente de los extractores.
- Resultado: `results/analysis/mesa_replication_20261026/summary.json`, estado `ANALYZED`, **5/5 auditadas**. `metrics.csv` contiene todas las reglas y presupuestos; `p0.csv` contiene las doce variantes de rescate permanente por condición. Cada JSON individual registra las fuentes verificadas.

## Resultados descriptivos de desarrollo

Media aritmética de las semillas nuevas dentro de cada dataset. Macro-F1 se calcula primero agrupando las predicciones productoras de cada condición. El costo es adquisición proyectada en ms, no latencia medida. La tabla muestra la regla de relevancia ya conservada en el plan por su resultado histórico; **no es una elección de ganador nueva a partir de estas cinco condiciones**. Las otras dos reglas y las referencias están completas en `metrics.csv`.

| Dataset (semillas nuevas) | B | Híbrido relevancia F1 / costo | Estático presupuestado F1 / costo |
| --- | ---: | ---: | ---: |
| FMD (42, 123, 2026) | 15 | 0,970011 / 11,680 | 0,970011 / 11,680 |
| FMD | 30 | 0,974618 / 18,499 | 0,968776 / 14,777 |
| FMD | 60 | 0,977489 / 35,689 | 0,974600 / 41,888 |
| FMD | 120 | 0,977074 / 46,923 | 0,977082 / 100,929 |
| Outex (123, 2026) | 15 | 0,862953 / 12,220 | 0,866642 / 13,372 |
| Outex | 30 | 0,895551 / 24,224 | 0,874557 / 25,989 |
| Outex | 60 | 0,905991 / 40,750 | 0,889152 / 49,047 |
| Outex | 120 | 0,908323 / 77,365 | 0,905582 / 109,396 |

En B60, FMD semilla 42 favorece al estático tanto en F1 como en costo: 0,978772/35,078 frente a 0,977506/38,282 del híbrido de relevancia. La semilla 123 tiene una pérdida pequeña de F1 en el híbrido (0,974987 frente a 0,975028) con menor costo; la semilla 2026 favorece al híbrido en ambos. El promedio FMD no implica dominancia por semilla. En las dos semillas nuevas de Outex, relevancia/B60 obtiene mayor F1 y menor adquisición proyectada que el estático B60. B15 conserva una pérdida frente al estático en Outex. No hay superioridad uniforme del híbrido.

## Límites y siguiente decisión

Se conservarán los cuatro presupuestos y las tres reglas, incluidos resultados negativos y rutas degeneradas a base sola. El costo procede del perfil fijo de adquisición y no incluye una nueva medición física del híbrido. Las semillas varían particiones y generación de candidatos, no solo inicialización. No corresponde calcular significancia entre datasets contando semillas/pliegues como dominios independientes.

El manuscrito y el PDF no se modificaron durante la recuperación descrita en este registro. En una etapa posterior del mismo día se incorporó la réplica: véase [incorporación al manuscrito](INCORPORACION_REPLICA_TESIS_2026-10-26.md). La réplica mínima de P1 en otro dataset y semillas adicionales está ejecutada y auditada; esto atiende esa parte de J03, pero no demuestra generalización a seis datasets ni cierra el panel. Faltan Top-k/GFS concatenados bajo este protocolo y medición física de la ruta exacta (J02). El manuscrito actualizado conserva la curva completa, las pérdidas y el contraste P0, sin escoger retrospectivamente la configuración más favorable del test.
