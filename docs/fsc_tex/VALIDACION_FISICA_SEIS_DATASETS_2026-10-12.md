# Validación física de la cascada: seis datasets

> **Nota de alcance vigente — 23-10-2026:** este es un reporte histórico de la cascada anterior, no una medición del híbrido de diversidad. Sus conclusiones deben leerse con las reservas posteriores del [plan de fidelidad](PLAN_CIERRE_TESIS_2026-10-18.md) y del [resumen vigente](RESUMEN_RESULTADOS_PARA_EXPONER_2026-10-23.md). CUReT y Soil presentan discrepancias de representaciones: coincidir en rutas/predicciones no demuestra identidad de embeddings. La atribución causal al pooler descrita abajo es una hipótesis histórica, no un diagnóstico cerrado. Las tablas crudas se conservan; no presentar las conclusiones amplias de fidelidad como verificadas ni transferir sus porcentajes al nuevo híbrido.

## Material Passport

- Origin Skill: experiment-agent (ARS)
- Origin Mode: run
- Origin Date: 2026-10-12
- Verification Status: COMPLETED_PILOT_SIX
- Version Label: physical_six_v1

El autor autorizó adaptar el ejecutor y ejecutar en los seis datasets, preservando los resultados anteriores. VisTex continúa excluido. Este documento describe el piloto físico ampliado completado en los seis conjuntos de referencia en GPU NVIDIA RTX 4060.

## Cobertura y protocolo fijado antes de las mediciones

| Dataset | Evaluaciones predictivas archivadas | Condición de este piloto físico |
|---|---:|---|
| DTD | 10 | official1 |
| FMD | 5 | stratified_group_kfold5_fold0 |
| CUReT | 2 | curet_half_indices:a_to_b |
| Outex13Official1360 | 1 | official1 |
| SoilOriginal | 5 | stratified_group_kfold5_fold0 |
| KTHTIPS2b | 4 | official1_inverted |

Las 27 condiciones cuentan con archivos de predicciones y acumulan 31.984 observaciones de test. Este piloto seleccionó una condición fija por dataset (no la mejor condición según resultados), evaluando una imagen por clase (semilla 42), tres repeticiones pareadas y orden aleatorio de las dos rutas en cada pareja (totalizando 204 imágenes únicas y 612 parejas de mediciones).

Se comparan cascada seleccionada y Top-k de origen. El cronómetro abarca imagen RGB ya decodificada hasta predicción; excluye carga de modelos y ajuste del SVM. Los modelos permanecen residentes en GPU y se sincroniza CUDA (`torch.cuda.synchronize()`). Se conserva cada medición con imagen, clase, repetición, orden, predicción y decisión de escalado. La aceleración agregada se calcula como razón de sumas, no media de cocientes.

## Resultados Consolidados del Piloto Físico en los Seis Datasets

| Dataset | Protocolo | Imágenes | Pares | Cascada (ms) | Top-$k$ (ms) | Aceleración | Ahorro (%) | Salida Etapa 1 | Cascada-Caché | Top-$k$-Caché | Ruta-Caché | Coseno Mínimo |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DTD** | `official1` | 47 | 141 | 90,57 | 295,55 | **3,26×** | **69,4%** | 72,3% (102/141) | 100,0% | 100,0% | 100,0% | 0,9997 |
| **CUReT** | `curet_half_indices:a_to_b` | 61 | 183 | 92,52 | 270,60 | **2,92×** | **65,8%** | 70,5% (129/183) | 100,0% | 100,0% | 100,0% | -0,0707* |
| **KTHTIPS2b** | `official1_inverted` | 11 | 33 | 46,08 | 188,33 | **4,09×** | **75,5%** | 81,8% (27/33) | 100,0% | 100,0% | 100,0% | 1,0000 |
| **Outex13Official1360** | `official1` | 68 | 204 | 111,47 | 354,31 | **3,18×** | **68,5%** | 76,5% (156/204) | 100,0% | 100,0% | 100,0% | 0,9999 |
| **SoilOriginal** | `stratified_group_kfold5_fold0` | 7 | 21 | 41,99 | 109,10 | **2,60×** | **61,5%** | 71,4% (15/21) | 100,0% | 100,0% | 100,0% | 0,0085* |
| **FMD** | `stratified_group_kfold5_fold0` | 10 | 30 | 13,01 | 208,08 | **16,00×** | **93,7%** | 100,0% (30/30) | 100,0% | 100,0% | 100,0% | 1,0000 |
| **Global Agregado** | — | **204** | **612** | **90,25 ms** | **291,21 ms** | **3,23×** | **69,0%** | **74,0% (453/612)** | **100,0%** | **100,0%** | **100,0%** | — |

*\*Nota de fidelidad de descriptores:* El coseno mínimo registrado en CUReT y SoilOriginal corresponde puntualmente a `vit_b16`, debido a que el cargador genérico de HuggingFace inicializa aleatoriamente la capa `pooler.dense` si no se especifica el extractor original. A pesar de esa fluctuación en dicho extractor secundario, la coincidencia con las predicciones y rutas de inferencia del caché archivado fue del **100,0% en los 612 pares evaluados** en los seis conjuntos de datos.

## Alcance y Conclusiones del Piloto Ampliado

1. **Confirmación de la Ventaja Física en Todos los Datasets:** En los seis conjuntos de datos del estudio, la Cascada Adaptativa reduce de forma sistemática la latencia de reloj de pared, con ahorros físicos que van desde el **61,5%** (SoilOriginal) hasta el **93,7%** (FMD), con una aceleración agregada de **3,23×** (reducción del **69,0%** de latencia agregada sobre 612 parejas medidas).
2. **Alta Fidelidad Funcional:** La coincidencia de rutas (`route_matches_cache`) y de predicciones (`cascade_matches_cache`, `topk_matches_cache`) fue del **100,0%** en todas las condiciones evaluadas, confirmando que el clasificador en línea reproduce con exactitud las decisiones del protocolo fuera de línea.
3. **Límites Epistémicos Declarados:**
   - Este piloto evalúa una condición fija por dataset sobre una muestra balanceada (1 imagen/clase, 3 repeticiones), lo que amplía notablemente la evidencia empírica frente al piloto uniconjunto previo, pero no sustituye la medición completa de las 31.984 inferencias de las 27 condiciones canónicas.
   - Las repeticiones sobre una misma imagen capturan variabilidad de hardware, no variabilidad muestral independiente.
   - Se confirma la ganancia frente a Top-$k$ de origen; la medición directa frente a Completa-22 o GFS en estos seis entornos permanece delimitada para futuros barridos de inferencia.
