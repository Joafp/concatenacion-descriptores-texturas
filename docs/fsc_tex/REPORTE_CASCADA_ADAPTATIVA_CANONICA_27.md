# Reporte auditado: cascada con etapa económica seleccionada

**Fecha:** 10 de octubre de 2026. **Estado ARS:** ANALYZED. Revisión de artefactos y código, no reentrenamiento ni validación física independiente.

## 1. Alcance

Hay 27 condiciones guardadas sobre seis datasets. CSV y JSON coinciden en las métricas y costos revisados. Los vectores de predicción por imagen (31.984 muestras) están persistidos en los 27 archivos JSON de predicciones adyacentes; el macro-F1 y exactitud de cada condición se recalculan y verifican con tolerancia nula (1e-12).

La etapa económica y q se seleccionan con predicciones OOF de entrenamiento. Top-k se hereda de archivos previos; su selección no se rehace en cada fold productor OOF. El código evalúa el test después de seleccionar las rutas, pero estos benchmarks ya se observaron durante el desarrollo. No se certifica ausencia absoluta de fuga ni confirmación independiente.

**Procedencia KTH:** la cascada reutiliza Top-k de ngram22_beitv2; el registro corregido usa ngram22_beitv2_innergrp_sample_v1. En condición 4, el primero usa ViT-B/16 (F1 0,873600) y el segundo BEiTv2 (0,919497). Las condiciones 1–3 no tienen Top-k en el registro corregido. Agrupar por sample al calibrar la cascada no rehace la selección original del subconjunto. KTH se conserva como resultado de su variante archivada, no como Top-k canónico reconciliado.

**Costos:** proyecciones por componentes sobre embeddings. Perfil KTH en KTH y perfil de imágenes de entrenamiento Outex como proxy en los otros cinco datasets, con fallback KTH para ViT-B/16. No son tiempos online imagen→predicción ni incluyen necesariamente todo el overhead.

## 2. Resultados descriptivos por dataset

Medias de particiones externas; igual peso por dataset en la última fila. Solo medias en todas las celdas: Outex tiene una sola condición. Completa/GFS son referencias del registro; KTH requiere reconciliación antes de un contraste conjunto.

| Dataset | N | Cascada seleccionada F1 | Cascada ResNet F1 | Top-k de origen F1 | Completa-22 F1 | GFS-22 F1 | Costo proyectado cascada / Top-k (ms) | Reducción proyectada |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DTD | 10 | 0.8700 | 0.8694 | 0.8700 | 0.8639 | 0.8703 | 172.0 / 661.8 | 74.0% |
| FMD | 5 | 0.9840 | 0.9789 | 0.9829 | 0.9651 | 0.9800 | 138.7 / 583.4 | 76.2% |
| CUReT | 2 | 0.9982 | 0.9979 | 0.9989 | 0.9989 | 0.9988 | 153.4 / 655.6 | 76.6% |
| Outex13Official1360 | 1 | 0.9369 | 0.9426 | 0.9426 | 0.9656 | 0.9589 | 165.9 / 729.5 | 77.3% |
| SoilOriginal | 5 | 0.8734 | 0.8663 | 0.8701 | 0.8919 | 0.8681 | 85.2 / 271.3 | 68.6% |
| KTHTIPS2b (referencias distintas) | 4 | 0.9445 | 0.9381 | 0.9400 | 0.9601 | 0.9355 | 64.9 / 278.0 | 76.7% |
| Media descriptiva (6) | 27 | 0.9345 | 0.9322 | 0.9341 | 0.9409 | 0.9353 | 130.0 / 529.9 | 75.5% |

El cociente de medias proyecta una reducción de 75.5% frente a Top-k y 53.3% frente a la cascada ResNet. No equivale a una reducción física medida. La diferencia media descriptiva de F1 es +0.000414 frente al Top-k de origen; no demuestra equivalencia.

Selección observada: siglip_base: 20, beitv2_base_final: 5, resnet50: 1, Top-k directo: 1. En KTH solo hay costos para dos candidatos económicos; no se evaluaron cuatro candidatos en cada condición.

## 3. Contrastes exploratorios con referencias reconciliadas

Se excluye KTH por procedencia, no por su resultado: N=5 datasets, 23 condiciones. Se promedian las particiones externas dentro de cada dataset. Este cambio respecto del reporte anterior es una corrección de auditoría, no un protocolo confirmatorio predefinido. La familia conserva tres contrastes bilaterales, con Holm a 0,05. GFS se informa descriptivamente, sin ampliar post hoc la familia. N pequeño y benchmarks reutilizados limitan la inferencia.

Friedman: estadístico 2.6327, p=0.4518. Iman–Davenport: F=0.8515, p=0.4922.

Rangos medios: Cascada seleccionada 2.200; Cascada ResNet 3.300; Top-k de origen 2.300; Completa-22 2.200. Un rango favorable no prueba superioridad.

| Comparador | Δ F1 | V–D–E | W | p bilateral | p Holm | Decisión (0,05) |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| Cascada ResNet | +0.001479 | 4–1–0 | 4.0 | 0.4375 | 1.0000 | No rechazo |
| Top-k de origen | -0.000397 | 3–2–0 | 7.0 | 1.0000 | 1.0000 | No rechazo |
| Completa-22 | -0.004567 | 2–3–0 | 6.0 | 0.8125 | 1.0000 | No rechazo |

No rechazar no demuestra igualdad, equivalencia ni no inferioridad. No se calculan p-valores tratando las 27 particiones solapadas como datasets independientes. Los p-valores del reporte anterior con N=27 no sustentan la conclusión de superioridad.

## 4. Detalle de las 27 condiciones

| Dataset | Protocolo | Ruta / base | q | F1 cascada | F1 Top-k de origen | Δ F1 | Costo proyectado (ms) | Top-k frente al registro |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| DTD | official10 | cascade / siglip_base | 0.25 | 0.864968 | 0.860440 | +0.004529 | 163.32 | matched |
| DTD | official1 | cascade / siglip_base | 0.25 | 0.868100 | 0.871965 | -0.003864 | 172.39 | matched |
| DTD | official2 | cascade / siglip_base | 0.25 | 0.866160 | 0.866115 | +0.000045 | 163.24 | matched |
| DTD | official3 | cascade / siglip_base | 0.25 | 0.873977 | 0.874700 | -0.000723 | 183.40 | matched |
| DTD | official4 | cascade / siglip_base | 0.25 | 0.873946 | 0.870244 | +0.003703 | 164.95 | matched |
| DTD | official5 | cascade / siglip_base | 0.25 | 0.878828 | 0.872601 | +0.006226 | 169.11 | matched |
| DTD | official6 | cascade / siglip_base | 0.25 | 0.869537 | 0.871462 | -0.001926 | 186.97 | matched |
| DTD | official7 | cascade / siglip_base | 0.25 | 0.880246 | 0.884498 | -0.004253 | 179.84 | matched |
| DTD | official8 | cascade / siglip_base | 0.25 | 0.853492 | 0.854571 | -0.001079 | 151.39 | matched |
| DTD | official9 | cascade / siglip_base | 0.25 | 0.871211 | 0.873597 | -0.002387 | 184.92 | matched |
| FMD | stratified_group_kfold5_fold0 | cascade / siglip_base | 0.25 | 0.964670 | 0.964670 | +0.000000 | 153.38 | matched |
| FMD | stratified_group_kfold5_fold1 | cascade / siglip_base | 0.25 | 0.994997 | 0.994997 | +0.000000 | 143.26 | matched |
| FMD | stratified_group_kfold5_fold2 | cascade / siglip_base | 0.25 | 0.984994 | 0.984994 | +0.000000 | 121.43 | matched |
| FMD | stratified_group_kfold5_fold3 | cascade / siglip_base | 0.25 | 1.000000 | 1.000000 | +0.000000 | 135.46 | matched |
| FMD | stratified_group_kfold5_fold4 | cascade / siglip_base | 0.25 | 0.975107 | 0.969972 | +0.005135 | 140.18 | matched |
| CUReT | curet_half_indices:a_to_b | cascade / resnet50 | 0.25 | 0.996792 | 0.998218 | -0.001426 | 168.39 | matched |
| CUReT | curet_half_indices:b_to_a | cascade / beitv2_base_final | 0.25 | 0.999644 | 0.999644 | +0.000000 | 138.50 | matched |
| Outex13Official1360 | official1 | cascade / beitv2_base_final | 0.25 | 0.936950 | 0.942574 | -0.005625 | 165.90 | matched |
| SoilOriginal | stratified_group_kfold5_fold0 | cascade / siglip_base | 0.25 | 0.887793 | 0.879704 | +0.008089 | 63.61 | matched |
| SoilOriginal | stratified_group_kfold5_fold1 | cascade / siglip_base | 0.25 | 0.853001 | 0.847681 | +0.005320 | 183.41 | matched |
| SoilOriginal | stratified_group_kfold5_fold2 | cascade / siglip_base | 0.25 | 0.833096 | 0.833096 | +0.000000 | 40.99 | matched |
| SoilOriginal | stratified_group_kfold5_fold3 | cascade / siglip_base | 0.25 | 0.895247 | 0.895247 | +0.000000 | 53.89 | matched |
| SoilOriginal | stratified_group_kfold5_fold4 | cascade / siglip_base | 0.25 | 0.897670 | 0.894578 | +0.003093 | 84.12 | matched |
| KTHTIPS2b | official1_inverted | cascade / beitv2_base_final | 0.25 | 0.992411 | 0.994102 | -0.001691 | 94.24 | missing |
| KTHTIPS2b | official2_inverted | topk_direct / — | — | 0.903999 | 0.903999 | +0.000000 | 33.33 | missing |
| KTHTIPS2b | official3_inverted | cascade / beitv2_base_final | 0.25 | 0.990847 | 0.988426 | +0.002421 | 80.61 | missing |
| KTHTIPS2b | official4_inverted | cascade / beitv2_base_final | 0.25 | 0.890744 | 0.873600 | +0.017143 | 51.39 | different |

## 5. Conclusión y pendientes

La selección de etapa económica es una candidata útil para optimizar el compromiso calidad–costo. En los resultados archivados gana descriptivamente a Top-k en cuatro datasets y pierde en CUReT y Outex. En Outex la caída es aproximadamente 0,005625 de macro-F1, mayor que la tolerancia interna de 0,005: la regla interna no garantiza no inferioridad externa.

No queda demostrado que supere a Completa-22, Top-k o GFS, ni que mantenga exactamente la precisión. H2 es un horizonte finito de dos pasos, no infinito; estos resultados no identifican una causa de saturación ni descartan toda planificación secuencial. Antes de elegir el método final: reconciliar KTH, guardar predicciones y trazas, verificar selección anidada y medir métodos pareados imagen→predicción.

El benchmark físico P4 corresponde a otra configuración FSC-Tex sobre 20 imágenes DTD; no valida los porcentajes de esta cascada. Véase [auditoría actual](AUDITORIA_P0_P4_CASCADA_2026-10-10.md) y [plan](../PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md).

Fuentes: results/exploratory/topk_cascade/cheap_stage_selected_primary22/rows.csv, JSON adyacentes y results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv. Hashes y alcance de verificación registrados en la auditoría.
