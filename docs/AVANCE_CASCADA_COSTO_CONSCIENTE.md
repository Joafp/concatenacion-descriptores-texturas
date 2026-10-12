# Avance experimental: cascada Top-k sensible al costo

## Material Passport

- Estado: **exploratorio / analizado**, no confirmatorio.
- Fecha: 2026-10-05.
- Alcance: SVM, semilla 42, biblioteca principal de 22 descriptores.
- Fuentes: `results/exploratory/topk_cascade/{dtd,fmd,curet,outex13_official1360,soil_original,kth_tips2b}/exact_archive/`; tabla regenerable con `scripts/report_cost_aware_topk.py`.
- Unidad de reporte: condiciones externas del protocolo archivado. Las particiones solapadas no son réplicas independientes.

## Decisión metodológica

La extensión principal propuesta para la tesis es **adquisición condicional de
descriptores hacia el Top-k seleccionado dentro del entrenamiento**, con una
salida directa a Top-k cuando la cascada no tiene ventaja de costo esperada.
El estudio estático de Individual, Completa, Top-k, GFS y Homogénea es el punto
de referencia; DynaTex-MoD no se adopta como método central.

La ruta de dos etapas clasifica primero con `resnet50`. El umbral de margen se
obtiene de predicciones fuera de fold sobre el entrenamiento externo con grupos
respetados. Si el margen es bajo, se extraen los bloques Top-k de la misma
partición; si no, se conserva la predicción barata. Para cada presupuesto
nominal `q`, la nueva salida por costo decide **antes del test**:

`usar cascada ⇔ C(barata) + q · C(Top-k incremental) < C(Top-k directo)`.

Si la desigualdad no se cumple, todas las imágenes toman Top-k directo, sin
extraer `resnet50`. El `q` es un presupuesto fijado de antemano, no la fracción
observada en el test. La selección de bloques Top-k y el umbral de margen
proceden solo del entrenamiento externo. Esta regla evita el costo fijo inútil
cuando el subconjunto Top-k ya es barato; **no garantiza** menor costo realizado
si la tasa de escalamiento cambia entre entrenamiento y test.

## Cobertura y reproducción

Se completaron 27 condiciones SVM externas: 10 splits DTD, 5 FMD, 2 direcciones
CUReT, 1 split oficial Outex13, 5 SoilOriginal y 4 splits oficiales invertidos
KTH-TIPS2-b. En todas, el clasificador Top-k reproducido con los bloques
archivados coincide con su macro-F1 previo dentro de `1e-10`. Cada artefacto
incluye huellas de auditoría, manifiesto y control Top-k; el consolidado vuelve
a comprobar que esas tres entradas no cambiaron.

Al presupuesto nominal `q=0,75`, los promedios descriptivos son:

| Dataset | Condiciones | Cascada con salida por costo | Top-k directo | Diferencia F1 | Menor costo de componentes estimado |
|---|---:|---:|---:|---:|---:|
| DTD | 10 | 0,8694 | 0,8700 | −0,0006 | 24,6 % |
| FMD | 5 | 0,9819 | 0,9829 | −0,0010 | 25,7 % |
| CUReT | 2 | 0,9989 | 0,9989 | 0,0000 | 26,7 % |
| Outex13 | 1 | 0,9426 | 0,9426 | 0,0000 | 33,6 % |
| SoilOriginal | 5 | 0,8701 | 0,8701 | 0,0000 | 21,8 % |
| KTH-TIPS2-b | 4 | 0,9396 | 0,9400 | −0,0004 | 29,7 % |

Estas cifras **no prueban equivalencia estadística**. El presupuesto de 75 %
se destaca porque mostró el mejor intercambio observado tras examinar los tres
presupuestos (`0,25`, `0,50`, `0,75`); por tanto, elegirlo ahora es una decisión
*post hoc*. La tabla completa por condición y presupuesto se encuentra en
`results/exploratory/topk_cascade/cost_aware_primary22/cost_aware_rows.csv`.

## Costo: qué se midió y qué no

Para KTH se usaron tiempos por bloque medidos con imágenes del conjunto que es
entrenamiento en la partición oficial 1 invertida. Para los otros cinco
datasets se midieron 20 imágenes del entrenamiento oficial de Outex; sus
tiempos se aplicaron como **proxy de hardware entre dominios**, no como latencia
específica de DTD, FMD, CUReT o Soil. El extractor Outex de ViT-B/16 no
reprodujo el embedding archivado y su costo se sustituyó por el benchmark
verificado de KTH. RGB N-gramas no se pudo medir con ese ejecutor, pero no
integra ninguno de los subconjuntos Top-k usados aquí. Todas estas decisiones
quedan registradas en el JSON de salida.

La cifra de ahorro de la tabla suma componentes de extracción medidos; excluye
carga de modelos y entrenamiento, y **no es una medición online de punta a
punta**. El benchmark de Outex usó entrenamiento para que la elección de ruta
no dependa de imágenes del test. Los modelos y embeddings del benchmark
presentaron verificaciones de concordancia; los bloques que no alcanzaron el
umbral de coseno 0,999 se excluyeron como evidencia de costo.

Se corrigió además el control online de KTH: la antigua ruta "Top-k siempre"
calculaba indebidamente `resnet50`. Con Top-k directo real, 30 imágenes
deterministas por partición, `q=0,50`, modelos residentes y carga/ajuste
excluidos:

| Partición KTH | Ruta seleccionada antes del test | Media seleccionada | Top-k directo | Predicciones concordantes |
|---|---|---:|---:|---:|
| 1 | Cascada | 196,03 ms | 447,49 ms | 100 % |
| 2 | Top-k directo | 42,61 ms | 42,61 ms | 100 % |
| 3 | Cascada | 238,42 ms | 441,05 ms | 100 % |
| 4 | Top-k directo | 40,07 ms | 40,07 ms | 100 % |

Sin la salida por costo, la cascada era 16,0 % más lenta que Top-k directo en
la partición 2 y 42,7 % más lenta en la 4. Los viejos porcentajes de ahorro
calculados contra Top-k más ResNet quedan **supersedidos**. Las trazas válidas
están en `results/exploratory/topk_cascade/kth_tips2b/online_fair_topk/`.

## Límite de la evidencia inicial y control posterior

Esto establece factibilidad exploratoria de una frontera desempeño–extracción,
no superioridad de clasificación ni ahorro universal. Antes de convertirlo en
la conclusión central del manuscrito faltan: (1) congelar la regla y el
presupuesto sin volver a elegirlos con el test; (2) medir latencia online en
los demás datasets con Top-k directo justo y conjuntos de imágenes mayores;
(3) estudiar variación entre corridas/hardware; y (4) contrastar el método
con la selección estática usando unidades estadísticas apropiadas. Outex tiene
un único split y no admite una desviación entre particiones.

Regeneración del consolidado:

```bash
.venv-confirmatory/bin/python scripts/report_cost_aware_topk.py
```

## Control posterior: presupuesto elegido dentro del entrenamiento

Se añadió `scripts/run_train_selected_topk_cascade.py`. Para cada una de las
27 condiciones SVM, calcula predicciones de ResNet-50 y Top-k fuera de fold
**únicamente en el entrenamiento externo** y compara tres umbrales de margen
(`q=0,25`, `0,50`, `0,75`) con Top-k directo. Elige la ruta de menor costo de
componentes estimado cuya macro-F1 interna no esté más de `0,005` por debajo
del Top-k interno; solo después de fijar la ruta consulta las predicciones
externas archivadas. Esas mismas particiones externas ya habían sido
inspeccionadas en pilotos anteriores, por lo que no son un test nuevo. El
subconjunto Top-k procede de la selección sobre todo el
entrenamiento externo, por lo que su puntaje fuera de fold todavía puede ser
optimista respecto a la elección de bloques. La tolerancia `0,005` fue fijada
**después de observar resultados exploratorios anteriores**; no constituye un
umbral prerregistrado ni una validación independiente.

| Dataset | Condiciones | Cascadas elegidas | Macro-F1 externo elegido / Top-k | Ahorro estimado de componentes |
|---|---:|---:|---:|---:|
| DTD | 10 | 10 | 0,8694 / 0,8700 | 24,6 % |
| FMD | 5 | 5 | 0,9789 / 0,9829 | 36,3 % |
| CUReT | 2 | 2 | 0,9979 / 0,9989 | 76,1 % |
| Outex13 | 1 | 1 | 0,9426 / 0,9426 | 52,7 % |
| SoilOriginal | 5 | 5 | 0,8663 / 0,8701 | 49,1 % |
| KTH-TIPS2-b | 4 | 3 | 0,9381 / 0,9400 | 42,3 % |

Los promedios son **descriptivos** y los porcentajes de cinco datasets siguen
siendo proyecciones basadas en tiempos de bloques medidos en Outex, no latencia
online propia de cada dataset. En algunas condiciones la pérdida externa fue
mayor que la tolerancia interna: FMD llegó a `−0,0100`, Soil a `−0,0113` y KTH
a `−0,0091` de macro-F1. No puede concluirse equivalencia estadística ni una
garantía de pérdida acotada. Los archivos por condición y el resumen están en
`results/exploratory/topk_cascade/train_selected_primary22/`.

Una sensibilidad **post hoc** de tolerancias `0`, `0,0025`, `0,005` y `0,01`
(`scripts/report_train_selected_sensitivity.py`) confirma el intercambio:
exigir igualdad interna reduce el ahorro en DTD a `2,5 %` y aun así no evita
toda pérdida externa en FMD (`−0,0050` en la peor condición) ni Soil
(`−0,0102`). No se debe escoger la tolerancia de la tesis mirando cuál fila de
esa sensibilidad rindió mejor en las mismas particiones.

La validación imagen→predicción con modelos residentes, ajuste y carga
excluidos, aceptó solo rutas con decisiones y predicciones idénticas a los
archivos y coseno mínimo de descriptor `≥0,999`. Para el presupuesto **elegido
por entrenamiento**, las muestras deterministas de 30 imágenes dieron:

| Condición | Cascada | Top-k directo | Menor latencia |
|---|---:|---:|---:|
| FMD, fold 0, `q=0,75` | 513,75 ms | 566,24 ms | 9,3 % |
| CUReT, A→B, `q=0,25` | 201,91 ms | 896,03 ms | 77,5 % |
| CUReT, B→A, `q=0,25` | 125,35 ms | 742,14 ms | 83,1 % |
| KTH-TIPS2-b, partición 4, `q=0,25` | 59,61 ms | 45,29 ms | **−31,6 % (más lenta)** |

Estas muestras son pequeñas, no cuantifican variación entre ejecuciones y no
validan DTD, Outex o Soil online. La partición 4 de KTH es un contraejemplo
observado al supuesto de que el menor costo por componentes asegure menor
latencia de la ruta: la cascada fue más lenta, aun con predicciones y
decisiones online concordantes. En KTH, una prueba de `q=0,75` en la
partición 1 coincidió en las 30 predicciones, pero solo en 29/30 decisiones de
escalamiento: la imagen 2598 tuvo margen archivado `1,82911` y margen online
`1,83207` alrededor del umbral `1,83026`. Esa corrida **falló** el criterio
estricto y no se reporta como latencia validada. La diferencia evidencia
sensibilidad del umbral a pequeñas variaciones de extracción. Las otras
mediciones previamente validadas de KTH corresponden a `q=0,50`, no siempre al
presupuesto seleccionado aquí.

**Decisión editorial actual:** la cascada aún no sustituye como método central
la comparación estática de 22 descriptores en el artículo. El ahorro online
observado es prometedor, pero la pérdida de macro-F1 por condición, la
tolerancia post hoc, la validación online parcial y la ausencia de repeticiones
independientes y el contraejemplo de latencia en KTH impiden una conclusión
de superioridad o equivalencia. Se
conserva como experimento exploratorio reproducible para diseñar una futura
evaluación confirmatoria con política fijada antes de nuevos tests.
