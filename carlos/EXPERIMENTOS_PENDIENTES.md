# Experimentos pendientes para el paper Top-k directo vs activación por margen

Fecha: 2026-11-14 · De: Carlos · Para: Joaquín

Joaco, con tus respuestas a [CONSULTAS_JOAQUIN.md](CONSULTAS_JOAQUIN.md) el paper (`carlos/main.tex`) ya
está consistente con lo que hay en el repo. Esta lista junta lo que **solo se resuelve corriendo algo**.
Ninguno se corrió.

> **Estado de la decisión:** el equipo acordó no correr experimentos nuevos. Esta lista es para decidir con
> el profesor qué se corre, si se corre algo. **No lances nada hasta que lo confirmemos.**

## Resumen

| ID | Experimento | Qué resuelve en el paper | Prioridad |
|---|---|---|---|
| E1 | Cascada con Top-4 fijo en las 27 condiciones | La comparación central del título con Top-4. También reconcilia KTH y da la etapa barata sola en test | **Alta** |
| E2 | Compuerta con otras medidas de confianza | Si el margen es mejor que otras compuertas, no solo mejor que un sorteo | Media (casi gratis si E1 guarda puntajes) |
| E3 | Cascada Top-k original con KTH corregido | Volver a N=6 datasets en las pruebas de la cascada actual | Media (innecesario si se corre E1) |
| E4 | Cascada con ResMLP | Hoy la cascada solo tiene SVM | Baja |
| E5 | Top-4 más `rgb_ngram_svd` | Si el bloque de color, excluido del ranking, mejora Top-4 | Baja |
| E6 | Diagnóstico de ViT-B/16 online frente a guardado | Causa de la diferencia en Soil (panel 0,8594 frente a estático 0,8864) y de los cosenos del piloto | Baja (no cambia resultados) |
| E7 | Memoria de GPU por política | La limitación declarada: no se registró | Opcional |
| E8 | Variación entre equipos de Top-4 con ResMLP | La limitación declarada: no se midió | Opcional |

Si solo se corre uno, que sea **E1**. Bien diseñado, cubre también E3, deja listos los datos de E2 y da la
etapa barata sola en test.

---

## E1. Cascada con Top-4 fijo en las 27 condiciones

**Por qué.** Hoy no existe una comparación completa entre Top-4 directo y Top-4 activado por margen.

- La cascada de las 27 condiciones usa la Top-k archivada, con k heredado de GFS (de 1 a 8; mediana 5).
- El panel online rescata con subconjuntos de cuatro bloques del ensamble de diversidad, no con Top-4.
- Solo 5 condiciones coinciden con Top-4 (`results/analysis/topk_margin_rewrite_20261113_v1/top4_margin_subset.json`). En ellas la cascada da 0,9400 frente a 0,9396 de Top-4 directo, con 148 frente a 598 ms. Es evidencia parcial.

**Entrada.**

- Las mismas 27 condiciones de `cheap_stage_selected_primary22`: SVM, semilla 42 (DTD 10, FMD 5, CUReT 2, Outex 1, Soil 5 y KTH-TIPS2-b 4).
- Etapa cara: la Top-4 de cada fold, tomada de `results/exploratory/k_sweep/<dataset>/k_sweep.csv`, con `classifier=svm`, `seed=42` y `k=4` (columna `selected`).
- En KTH el barrido ya agrupa la validación interna por muestra física (`--inner-group-column sample`). Por eso esta cascada queda reconciliada con el control corregido y KTH vuelve a las pruebas.

**Protocolo.** El mismo de `scripts/run_cheap_stage_selected_cascade.py`, cambiando solo la etapa cara:

- las mismas etapas baratas candidatas (ResNet-50, SigLIP-B, BEiTv2-B y ConvNeXt V2-T; en KTH, ResNet-50 y BEiTv2-B);
- los mismos cuantiles q ∈ {0,25; 0,50; 0,75};
- los mismos márgenes OOF agrupados en el entrenamiento externo;
- la misma regla de ruta (tolerancia 0,005) y el mismo perfil de costos;
- la ruta restringida a ResNet-50, como referencia;
- el control aleatorio con la misma cantidad de imágenes y 100 repeticiones, para la ruta elegida y para cada q con ResNet-50.

**Qué guardar, además de lo que ya guarda el script.** Esto evita reentrenar para E2 y para el F1 de la etapa barata:

- `y_pred` en test de **cada etapa barata candidata sola**. Hoy no se guarda, y por eso el paper solo puede dar su F1 fuera de fold;
- los **puntajes de decisión completos** (todas las clases) de cada etapa barata, en OOF y en test;
- la predicción de Top-4 directo en test.

**Salida sugerida.** `results/exploratory/topk_cascade/top4_fixed_primary22/`:

- `rows.csv` con una fila por condición: `dataset, protocol, top4_blocks, route, cheap, budget, request_fraction, top4_direct_f1, cascade_f1, cheap_only_f1, resnet_route_f1, random_mean_f1, top4_direct_ms, cascade_ms, resnet_route_ms`;
- un `*_predictions.json` por condición con lo de arriba;
- `summary.json` con medias por dataset y con 5 y 6 datasets;
- hashes de manifiestos y embeddings, como en tus auditorías.

**Qué cambia en el paper.** La tabla central pasa a ser «Top-4 directo frente a Top-4 por margen» en 6 datasets. Se suman el F1 de la etapa barata sola en test y el control aleatorio sobre la ruta elegida.

## E2. Compuerta con otras medidas de confianza

**Por qué.** El único control actual es el sorteo, y lo hiciste sobre el piloto con ResNet-50. Cualquier
medida de confianza le gana a un sorteo; la pregunta es si el margen le gana a otras.

**Protocolo.** Con los puntajes guardados en E1, sin reentrenar, comparar tres compuertas:

- margen s(1) − s(2), la actual;
- puntaje máximo s(1);
- entropía del softmax de los puntajes.

Cada umbral se fija como cuantil sobre OOF, para que las tres escalen la misma fracción. Hay que reportar el macro-F1 de cada una a igual fracción escalada (q = 0,25, 0,50 y 0,75), con Wilcoxon exacto sobre las medias por dataset y Holm.

**Salida sugerida.** `results/exploratory/topk_cascade/top4_fixed_primary22/gates.csv`, con las columnas
`dataset, protocol, q, gate, request_fraction, macro_f1`.

## E3. Cascada Top-k original con KTH corregido (solo si no se corre E1)

Volver a correr `cheap_stage_selected_primary22` en las 4 particiones de KTH con el control Top-k corregido
(`results/extensions/kth_tips2b/ngram22_beitv2_innergrp_sample_v1/topk_individual_control/`). Así, las
pruebas de la cascada actual vuelven a 6 datasets (hoy son 5 y 23 condiciones).

## E4. Cascada con ResMLP

El mismo protocolo de E1, con el margen tomado de los logits de ResMLP. Mismas condiciones y mismas salidas.
Hoy toda la comparación pareada es con SVM.

## E5. Top-4 más `rgb_ngram_svd` (5 bloques)

Pendiente en `results/exploratory/k_sweep/README.md:64`. El ranking del barrido usó 21 bloques, así que Top-4
nunca pudo elegir el bloque de color, que dentro de Completa-22 aporta en Soil y KTH. Hay que concatenar la
Top-4 de cada fold con `rgb_ngram_svd` (reconstruido por fold) y evaluarla en las 47 condiciones con SVM, y
con ResMLP si es barato.

## E6. Diagnóstico de ViT-B/16 online frente a guardado

**Síntoma.** En Soil, las 8 condiciones cuyo Top-4 incluye `vit_b16` cambian de F1 al extraer en línea; las
7 sin ese bloque no cambian. En el piloto, CUReT y Soil tienen coseno < 0,99 solo en `vit_b16`, en todas
las imágenes.

**Protocolo.** Tomar unas pocas imágenes de CUReT y Soil y comparar la extracción online con la que generó
los embeddings guardados, paso por paso:

- redimensionado y recorte;
- normalización de color;
- *pooler* o token usado;
- versión de `timm`/`torch` y pesos del modelo.

**Salida.** Una nota con la causa. Si se corrige, conviene volver a medir el panel de Soil con Top-4.

## E7. Memoria de GPU por política (opcional)

Medir `torch.cuda.max_memory_allocated()` con cada política cargada por separado (Top-4, política por
margen y Completa-22), con `batch=1`, en la RTX 4060.

## E8. Variación entre equipos de Top-4 con ResMLP (opcional)

Correr una misma condición de Top-4 con ResMLP en los dos equipos que se usaron (GPU y CPU) y reportar la
diferencia de macro-F1.

---

## Reglas para cualquier corrida

- Toda selección (bloques, umbral, ruta, compuerta) solo con el entrenamiento externo. El test se consulta una vez, al final.
- Mismas particiones, semillas y perfiles de costo que la evaluación que se reemplaza. Si algo cambia, documentarlo.
- Registrar hashes de entradas y salidas, como en `results/analysis/consultas_joaquin_20261114_v1/`.
- Avisame qué carpeta queda como canónica; yo actualizo el paper.
