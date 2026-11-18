# Métricas disponibles con criterios comparables a HyTexNet

> **Estado posterior:** la cola HyTex ajustada cerró 33/33 condiciones en cuatro datasets y la robustez FMD cerró 15/15 con 6.000 llamadas auditadas. El perfil estructural ya fue calculado. Los párrafos iniciales conservan los cortes v1/v2 previos; el cierre está detallado más abajo y en el [estado de experimentos](ESTADO_EXPERIMENTOS.md). Top-4 no tiene todavía esa prueba de robustez.

Fecha 2026-11-16. Resultado de una agregación de archivos existentes; no se entrenaron modelos ni se ejecutó inferencia para este reporte. Código `scripts/report_hytex_paper_metrics.py`; salida exclusiva `results/analysis/hytex_paper_metrics_20261116_v1/`, que contiene CSV y hashes de fuentes. Verificación sintética de precisión/recall/F1 macro: 1 prueba aprobada.

**Actualización posterior:** `scripts/report_hytex_paper_metrics_v2.py` generó `results/analysis/hytex_paper_metrics_20261116_v2/` sin modificar v1. Incluye FMD (15/15) y CUReT (2/2) de HyTex fine-tuned, además de los 60 agregados del panel propio. En el corte de v2, Soil tenía 3/15 y Outex 0/1: no se agregaron. Los CSV por clase y las matrices acumuladas incluyen ahora nombres de clases y corresponden a observaciones repetidas, no a imágenes independientes. Dos pruebas validaron las métricas y la exclusión de datos incompletos.

CUReT: HyTex fine-tuned accuracy **99,1091 %**, precisión macro **99,1470 %**, recall macro **99,1091 %**, macro-F1 **99,1122 %**, latencia media **35,7175 ms** y p95 **88,1698 ms**, 2 condiciones y 5.612 llamadas. Top-4 SVM para ese dataset: accuracy **99,8574 %**, precisión macro **99,8605 %**, macro-F1 **99,8574 %** y latencia media **270,6926 ms**, p95 **286,5198 ms**. Son sesiones distintas y resultados descriptivos.

Se preparó y probó `scripts/profile_hytex_model_resources.py` para contar parámetros y MACs de convoluciones/capas lineales mediante tensores `meta` CPU, sin descargar pesos: documenta que cada MAC equivale a 2 FLOPs y excluye preprocesamiento, descriptor manual, BN, ReLU, pooling e I/O. El conteo estructural está **pendiente de ejecución con GPU libre**; no es una medición end-to-end ni latencia. La propuesta de ruido y brillo y sus pruebas sintéticas se documentan en `docs/fsc_tex/PROTOCOLO_ROBUSTEZ_HYTEX_COMPARACION_2026-11-16.md`; todavía no hay predicciones perturbadas.

**Cierre de cola y actualización v3:** las 33 condiciones nuevas de HyTex fine-tuned se completaron y auditaron: FMD 15/15, CUReT 2/2, Soil 15/15 y Outex 1/1. `results/analysis/hytex_paper_metrics_20261116_v3/` agrega esos cuatro datasets y los 60 casos completos del panel propio. Se preservan v1 y v2. DTD y KTH de esta nueva receta no se ejecutaron en el panel común; no rellenarlos con otras recetas. Outex tiene una sola condición y la reserva de procedencia correspondiente.

Las 23 combinaciones completas de cuatro adaptaciones externas y seis datasets, excluyendo DeepLumina/DTD con 9/10, se agregaron en `results/analysis/external_paper_metrics_20261116_v2/external_dataset_metrics.csv`. Se verificaron hashes y recibos y se reconstruyeron métricas desde las mismas llamadas. DeepLumina conserva reserva de no convergencia en todos los datasets. Las cifras son adaptaciones y los tiempos de sesiones distintas son descriptivos.

**Perfil estructural realizado tras liberarse la GPU:** el modelo HyTex fine-tuned de FMD con 10 clases tiene **7.350.410 parámetros**, de los cuales 2.556.682 son entrenables. Para entrada 128×128, solo convoluciones y capas lineales, contiene **925.502.464 MAC**, que equivalen a **1.851.004.928 FLOPs** bajo la convención explícita de 2 FLOPs por MAC. No cuenta bias, BatchNorm, ReLU, pooling, descriptor manual, preprocesamiento ni lectura: no son FLOPs end-to-end ni latencia. El paper informa 0,94 GFLOPs, cercano al número de GMAC de este conteo, pero no se ha verificado que ambos utilicen la misma convención o alcance; no afirmar identidad. El resultado y hashes están en `results/analysis/hytex_resource_profile_20261116_v1/profile.json`.

Una evaluación nueva de robustez FMD para HyTex sobre las 15 condiciones quedó preregistrada y comenzó después de la cola. Brillo RGB ×1,2 y ruido gaussiano con σ=0,1×255 son decisiones locales (no verificadas como equivalentes al paper). No se agregará hasta 6.000/6.000 llamadas y auditoría. La ruta Top-4 perturbada requiere validar pesos y adaptadores por separado; no se inventa comparación ni se atribuye robustez al método propio sin su medición.

## Inventario

| Medida en HyTexNet | Estado en este reporte |
|---|---|
| Accuracy y macro-F1 | Disponibles en `dataset_metrics.csv` para cinco políticas propias, seis datasets y dos clasificadores (60 combinaciones completas). Nueva HyTex con fine-tuning: FMD 15/15, CUReT 2/2, Soil 15/15 y Outex 1/1 auditados en la tabla v3. |
| Precisión y recall macro | Calculados de las mismas llamadas para los métodos propios y reconstruidos de las predicciones de la nueva HyTex FMD. Promedio de métricas por condición, división cero con valor 0; no intercambiar con accuracy. |
| Matriz de confusión y por clase | HyTex FMD: archivos `hytex_fmd_pooled_confusion.csv` y `hytex_fmd_pooled_per_class.csv`, 3.000 llamadas acumuladas. Son descriptivos: los folds y semillas reutilizan imágenes, por lo que sus filas no son 3.000 muestras físicas independientes. Etiquetas: 0 fabric, 1 foliage, 2 glass, 3 leather, 4 metal, 5 paper, 6 plastic, 7 stone, 8 water, 9 wood. |
| Desviación estándar | Desviación muestral de las accuracies de las condiciones; no equivale a cinco inicializaciones sobre un mismo split ni a un intervalo de confianza. No se calcula para Outex (una condición). |
| Tiempos medios, mediana y percentil 95 | Calculados sobre llamadas online completas; sesiones y condiciones de hardware diferentes, por tanto descriptivos. La política online por margen es variante con rescate por ensamble, no la cascada E1 estricta. |
| Dimensiones | Disponibles en tablas previas de Top-4 y Completa, pero no se incorporan a la tabla automática sin identificar por condición y modelo. HyTex final fusiona 1.538 valores. |
| Parámetros y GFLOPs | Perfil estructural de HyTex FMD calculado y documentado arriba; quedan pendientes los demás pipelines y operaciones de CPU, preprocesamiento y rutas condicionales. GFLOPs no son latencia ni deben copiarse del paper. |
| Perturbaciones, estabilidad por inicialización, curvas de validación y cross-domain | No están cubiertas de forma comparable para todos los métodos con fuentes aquí verificadas. No extrapolar ni inventar cifras; requieren protocolos y corridas explícitos o auditoría de archivos de entrenamiento. |

## Comparación ilustrativa: FMD, 15 condiciones por método

Accuracy, precisión macro, recall macro y F1 macro son medias de las métricas por condición. Los tiempos resumen las 3.000 llamadas individuales de cada método y están en milisegundos; los experimentos se ejecutaron en sesiones distintas. La variante por margen del panel usa rescate por ensamble.

| Método | Accuracy | Precisión macro | Recall macro | F1 macro | Media ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|
| Top-4 SVM | 98,23 % | 98,33 % | 98,23 % | 98,23 % | 268,96 | 296,25 |
| Política por margen SVM, rescate por ensamble | 97,77 % | 97,88 % | 97,77 % | 97,76 % | 38,63 | 270,77 |
| Completa-22 SVM | 96,50 % | 96,70 % | 96,50 % | 96,51 % | 1.759,50 | 1.850,41 |
| HyTexNet local, último bloque ajustado | 74,17 % | 75,35 % | 74,17 % | 74,07 % | 36,69 | 88,93 |

FMD tiene 20 imágenes por clase en cada una de estas condiciones; por eso aquí recall macro y accuracy coinciden numéricamente. No es identidad general para datasets desbalanceados. La comparación es local y descriptiva, no una réplica de los porcentajes originales ni una prueba causal de latencia; los tiempos se midieron en sesiones distintas. No confundir con HyTex congelada ni con la variante KTH paperlike compartiendo muestras físicas.

## Próximos pasos

La cola de fine-tuning cerró 33/33 y sus cuatro datasets están auditados en v3; conservar separadas las recetas. Extender el conteo a otros pipelines sin inferir el costo de descriptores manuales a partir de GFLOPs de la red. Cualquier robustez a ruido/luz, curvas o intervalos comparables requiere protocolo, fuentes y unidad estadística explícitos antes de medir.

## Robustez FMD: cierre auditado

Se auditaron las 15 condiciones y 6.000 llamadas perturbadas, emparejadas con los mismos modelos y muestras limpias. Accuracy medio limpio: **74,17 %**; con brillo RGB ×1,2: **72,70 %** (−1,47 puntos porcentuales); con ruido gaussiano σ=0,1×255: **71,90 %** (−2,27 puntos). F1 macro medio: 72,52 % y 71,65 %, respectivamente. El detalle, hashes y auditoría están en `results/analysis/hytex_fmd_robustness_20261116_audit_v1/`. Las transformaciones son supuestos locales y no se afirma equivalencia con las del artículo. Las imágenes reaparecen en diferentes particiones: las 6.000 llamadas no son imágenes físicas independientes. No hay comparación de robustez contra Top-4 aún.

Se extendió el perfil estructural a las cuatro configuraciones según el número de clases, verificando los 33 checkpoints, en `results/analysis/hytex_resource_profile_by_dataset_20261116_v1/`. El costo de convoluciones y capas lineales es aproximadamente 0,926 GMAC por inferencia en las cuatro arquitecturas, con exclusiones y convención detalladas arriba. Falta medir el pipeline completo de cada método y las otras condiciones de robustez; no confundir estos conteos con tiempos medidos.
