# Revisión simulada, ronda 2 (verificación) — `carlos/main.tex`

Fecha: 2026-11-15. Skill: `academic-paper-reviewer`, modo `re-review`. Se usó el mismo panel de la ronda 1, sin regenerarlo. Cada punto se verificó contra el PDF compilado (lectura completa del texto extraído), no contra el registro de cambios.

## Matriz de verificación

| ID | Pedido en la ronda 1 | ¿Verificado en el PDF? | Evidencia |
|---|---|---|---|
| R1 | No inferioridad de la cascada | Sí | §4.4 define el análisis y aclara que es posterior; §4.7 da la diferencia por dataset, el IC 95 % [−0,0017; 0,0019], la cota −0,0013 y los valores p; resumen, aspecto destacado 5, discusión, limitaciones y conclusión son coherentes |
| R2 | La etapa barata pertenece a Top-4 | Sí | §4.7: 26/27, con la excepción de CUReT A→B; la discusión lo retoma |
| R3 | Cita de RADAM | Sí | §4.1 [49]; entrada verificada |
| R4 | Resumen ≤ 250 palabras | Sí | ≈ 240 palabras en el PDF (252 unidades en la fuente, contando comandos de LaTeX) |
| R5 | Dirección del cambio de métrica | Sí | §4.6 (rangos invertidos en macro-F1) y limitaciones |
| R6 | Precisar «similar» | Sí | Resumen, discusión y conclusión dan −0,0027 y +0,0037. En §4.9 queda «similares» solo para los percentiles de FMD, que es correcto |
| R7 | Antecedentes de compuertas | Sí | §2.2 [25–27], §3.4 [27]. El puntaje máximo de la SVM se presenta como *análogo* a la probabilidad máxima del softmax, no como lo mismo |
| R8 | Rótulos en español | Sí | «Información», «Palabras clave», «Resumen», «Página x de 21», «Contribución de los autores (CRediT)»; separación silábica española |
| R9 | Declaraciones | Sí, como pendientes | Conflicto de intereses, financiamiento e IA generativa marcados «Pendiente de confirmación por los autores» |
| R10 | Outex_TC_00013 | Sí | §4.1 |
| R11 | Entropía sobre puntuaciones crudas | Sí | §3.4 |
| R12 | Inferencia por lotes | Sí | Discusión, párrafo de costos |

## Problemas nuevos encontrados en esta ronda (todos corregidos)

| Problema | Corrección |
|---|---|
| Referencia [3]: «Pietik"ainen» con el acento roto | `Pietik{\"a}inen` |
| Títulos sin mayúsculas: EfficientNet, ConvNeXt V2, Swin Transformer, DINOv2, KTH-TIPS, Fisher, Outex, EVA-02, RGB Pixel N-grams, BEiT v2, BranchyNet | Protegidas con llaves en `references.bib` |
| Fechas con el mes como número («06 2014») | Se quitaron los 30 campos `month` |
| Han et al. con año 2021, aunque el volumen 44 es de 2022 | Año 2022 |
| La introducción no mencionaba la no inferioridad entre los aportes, y una oración empezaba con «Y» | Se agregó; «Por último, contrasta…» |
| Tabla 7: el costo de la ruta con ResNet-50 en DTD y CUReT estaba redondeado desde un valor ya redondeado (445,2 y 151,2) | 445,1 y 151,1, recalculados desde `e1_condiciones.csv` |

## Comprobaciones de forma

- La compilación con pdfLaTeX + BibTeX termina sin errores, sin referencias ni citas indefinidas y sin cajas desbordadas. Hay un aviso menor de caja poco llena en el apéndice, causado por las rutas largas.
- Son 22 páginas: aspectos destacados + 21 numeradas.
- Los aspectos destacados tienen 85 caracteres o menos.
- Las filas de las Tablas 5, 7, 8, 9 y 11 se regeneraron desde los datos y se compararon de forma automática con el `.tex`; coinciden todas las celdas. Fuentes:
  - `results/analysis/thesis_accuracy_primary_20261115_v3/` (tablas 5 y 11);
  - `carlos/analisis_paper/e1_condiciones.csv` y `e1_medias_por_dataset.csv` (tablas 7 y 8);
  - `results/analysis/top4_fixed_kth_completion_audit_20261115_v1/e2_complete_dataset_means.csv` (tabla 9).
- Las Tablas 4 y 6 salen de `carlos/analisis_paper/reglas_k.txt` y `estadistica_3_metodos_accuracy.txt`.

## Decisión

**Aceptable como primera versión para el tutor.** No quedan problemas críticos ni mayores abiertos que se resuelvan escribiendo.

Pendientes que no dependen de la redacción:
1. Las declaraciones de conflicto de intereses, financiamiento, uso de IA generativa y ética las tienen que completar los autores.
2. La cascada con Top-4 no tiene latencia online medida; el paper lo declara. Joaquín la tiene como próximo paso.
3. Hay dos decisiones para conversar con el tutor:
   - El cambio de mensaje en la evaluación estática: con accuracy y SVM, Completa-22 queda primera en el ranking.
   - Si el paper se queda en español o se traduce para enviarlo a una revista.
