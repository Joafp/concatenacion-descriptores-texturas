# Integración de seis datasets en la tesis

15-11-2026, America/Asuncion. El PDF vigente tiene **90 páginas** y el cierre
E1/E2 de 27/27 condiciones ya está incorporado. Se actualizaron los resúmenes
español/inglés, introducción, método de costos, diseño, resultados, discusión,
conclusiones y trazabilidad. Se generaron siete tablas desde la auditoría
cerrada, conservando las tablas del corte anterior.

Accuracy principal: 0,944449 directa y 0,944581 por margen; p exacto=0,5625.
El 75,00 % es reducción de adquisición proyectada, no latencia online. Se
conservan ganancias, pérdidas, selección histórica por macro-F1 y límites de
la validación KTH. No hubo fits, extracciones ni predicciones nuevas durante
esta integración.

Pasaron **102 pruebas en 24,72 s**. Compilación sin referencias indefinidas
ni desbordes; cero caracteres de reemplazo. Se inspeccionaron las ocho hojas
de contacto de las 90 páginas y las páginas físicas 41–44 en detalle.

- [PDF](../../paper/tesis.pdf).
- [Fuentes, tablas y hashes](../../results/analysis/thesis_six_dataset_integration_20261115_v1/tables_receipt.json).
- [Registro de entrega y revisión](../../results/analysis/thesis_six_dataset_integration_20261115_v1/manuscript_release.json).

También se preparó el [protocolo de latencia online](PROTOCOLO_LATENCIA_TOP4_DIRECTO_MARGEN_2026-11-15.md)
y un [manifiesto de insumos](../../results/analysis/top4_online_latency_preparation_20261115_v1/manifest.json)
con cabezas, selección, índices y hashes de los 27 casos. Prevé 63.968 llamadas
evaluadas y 270 calentamientos; **no fue ejecutado**. Todavía requiere
implementación validada, congelado del entorno/pesos y revisión de fidelidad.
CUReT fold 0 y Soil folds 1/4 están bloqueados por ViT-B/16. No se repetirán
automáticamente sus fallos ni se omitirán para declarar cobertura completa.

E5 (Top-4 más N-gramas) sigue pendiente; este trabajo no lo sustituye.
