# Revisión editorial para revista

**Candidato de referencia:** Pattern Recognition. El alcance editorial admite contribuciones originales de metodología y aplicación con respaldo en la literatura de reconocimiento de patrones. La contribución defendible aquí es la evaluación pareada de cuándo adquirir bloques adicionales para clasificar texturas. El ranking individual, las cascadas y el uso del margen tienen antecedentes. [Alcance editorial](https://shop.elsevier.com/journals/pattern-recognition/0031-3203)

## Afirmaciones centrales y evidencia

| Afirmación | Evidencia rastreable | Alcance |
|---|---|---|
| Cuatro bloques son un punto de operación compacto | [Curvas por dataset](../../results/analysis/thesis_accuracy_primary_20261115_v3/per_dataset_curves.csv), [SVM](../../results/analysis/thesis_accuracy_primary_20261115_v3/static_accuracy_svm.csv), [ResMLP](../../results/analysis/thesis_accuracy_primary_20261115_v3/static_accuracy_resmlp.csv) | Elección exploratoria. El mejor tamaño depende de la cabeza y del dataset. |
| El margen ordena imágenes cuyo rescate puede compensar el costo | [Medias E1](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e1_complete_dataset_means.csv), [conteos pareados](../analisis_paper/e1_mcnemar_compuerta.csv), [control por condición](../analisis_paper/e1_condiciones.csv) | La comparación con el sorteo usa igual número de activaciones. El contraste contra Top-4 directo debe incluir su intervalo y la reserva sobre la elección retrospectiva. |
| La adquisición de bloques se abarata en E1 | [Auditoría de E1](../../results/analysis/top4_fixed_kth_completion_audit_20261115_v1/README.md), [implementación de la proyección](../../scripts/run_top4_fixed_e1_e2.py) | Proyección de extracción. El ahorro físico de la cascada exacta sigue sin verificarse. |
| Otra política por margen reduce la latencia media medida en las doce combinaciones | [Panel online](../../results/analysis/blocker_resolution_20261101/full_panel_online_v1/coverage.json), [medias por política](../../results/analysis/thesis_accuracy_primary_20261115_v3/online_means.csv), [percentiles](../analisis_paper/latencia_p95_reunida.csv) | Rescate por ensamble. La latencia de cola en Soil y la caída de accuracy en KTH-TIPS2-b delimitan la utilidad. |

## Pendientes de envío

1. Adaptar el texto al inglés científico y verificar la versión maquetada con la guía del destino. La ficha editorial de Pattern Recognition indica formato de una columna y doble espacio. La guía completa enlazada desde la ficha no estuvo accesible en esta revisión, así que se mantienen abiertas las comprobaciones específicas del envío.
2. Confirmar con los autores contribuciones, financiamiento, conflictos y declaración de asistencia de IA. El borrador declara el uso confirmado de Codex en esta revisión. La política del editor también requiere verificar los detalles de herramientas empleadas en diagramas y visualizaciones, incluidos el modelo o versión y el uso concreto. [Política de IA de Elsevier](https://www.elsevier.com/en-gb/about/policies-and-standards/generative-ai-policies-for-journals)
3. Revisar qué material puede usar un tercero desde una copia del repositorio. Las predicciones por imagen y el análisis de E1 están versionados. Las cabezas serializadas y los embeddings citados por la auditoría tienen disponibilidad local. [Reconstrucción de conteos archivados](../analisis_paper/README.md)
4. Si la conclusión del artículo requiere una cifra de ahorro físico para la cascada Top-4 exacta, respaldarla con evidencia de esa implementación frente a su uso directo. La evidencia publicada en el manuscrito permite atribuir el ahorro del 75 % al modelo de costo y las mediciones físicas al ensamble.
