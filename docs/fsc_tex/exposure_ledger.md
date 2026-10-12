# Registro de Exposición al Test (Exposure Ledger) — FSC-Tex

**Fecha inicial:** 8 de octubre de 2026. **Actualización:** 10 de octubre de 2026.

**Propósito:** Documentar con absoluta transparencia la historia de exposición de cada dataset y partición canónica a lo largo del desarrollo del proyecto de tesis.  
**Principio metodológico:** Haber ejecutado pruebas previas sobre un benchmark conocido introduce riesgo de sesgo de diseño. Registrar esta exposición evita presentar como «generalización ciega» decisiones que fueron influenciadas por resultados históricos.

---

## 1. Historial de Exposición por Dataset Canónico

| Dataset | Particiones Archivadas | Fases Previas en que se Evaluó | Qué Información se Observó Históricamente | Medidas de Contención para FSC-Tex |
| :--- | :---: | :--- | :--- | :--- |
| **DTD** | 10 splits oficiales (1–10) | Confirmatory 20, N-gram 21, Primary 22, Pilotos de Cascada | Macro-F1 de 22 extractores individuales, selecciones GFS, Top-k, y latencias de inferencia. | El espacio de estados y la política se ajustan **exclusivamente con validación cruzada interna anidada sobre las particiones de entrenamiento**. No se ajustan hiperparámetros de política mirando el test de los 10 splits. |
| **FMD** | 5 folds agrupados (seed 42) | Confirmatory 20, Primary 22, Ablaciones de DynaTex | Macro-F1 saturando en ~0.97–0.98. Se conoce que DINOv2 y ViTs dominan el rendimiento. | ResNet fija se admite como control. La selección de una base adaptada al dataset debe validarse en entrenamiento; v2 todavía no hace selección conjunta base+política. |
| **CUReT** | 2 mitades complementarias (`a_to_b`, `b_to_a`) | Confirmatory 20, Primary 22, Piloto de Cascada | Macro-F1 extremadamente alto (~0.999). Prácticamente cualquier combinación profunda satura la métrica. | Se utiliza como prueba de **omisión de costo (parada temprana)**: si la predicción satura con el extractor inicial barato, la política debe emitir `STOP` y no incurrir en sobrecosto. |
| **Outex13Official1360** | 1 split oficial (1.360 imágenes) | Extensions, Primary 22, Benchmark de extracción online | Rendimiento comparativo SVM vs ResMLP, perfiles de tiempo por bloque en 20 imágenes. | Al existir un único split oficial, no admite inferencia estadística multifold. Se reporta como condición fija descriptiva. |
| **SoilOriginal** | 5 folds agrupados (seed 42) | Extensions, Primary 22, Pilotos de presupuesto PCA-LDA | Fuerte sensibilidad a la familia de descriptores; dominancia de Transformers y caída de clásicos. | Los grupos geológicos/familiares deben mantenerse estrictamente agrupados en la CV interna para evitar fuga intra-muestra. |
| **KTHTIPS2b** | 4 particiones RADAM (3 train, 1 test) | Extensions, Primary 22, Corrección de agrupamiento interno | Se demostró en el PR #1 que evaluar sin agrupar por muestra física producía saturación artificial (1.0). | **Regla estricta:** La validación interna para aprender la política debe usar obligatoriamente `--inner-group-column sample` (máximo 3 folds internos). |

---

## 2. Salvaguardas Metodológicas Contra la Filtración

Las siguientes son salvaguardas exigidas, no una certificación automática de que cada versión las cumple. Véase la auditoría v2 del 10 de octubre para el cumplimiento observado:

1. **Aislamiento de la Selección de Estados:**
   * El subgrafo de hasta 16 estados candidatos y las transiciones permitidas se construyen utilizando **únicamente** los folds de entrenamiento (`T_train`).
   * Ningún score, pérdida o margen obtenido sobre el conjunto de prueba (`T_test`) puede utilizarse para podar el grafo o elegir qué extractor considerar.

2. **Ajuste de Umbrales y Presupuestos ($\lambda$, $q$):**
   * El balance de costo-riesgo ($\lambda$) y los umbrales de margen se calibran mediante validación cruzada fuera de muestra (*Out-of-Fold* - OOF) dentro de `T_train`.
   * Si tras evaluar en `T_test` se observa que otro valor de $\lambda$ rendía mejor, **dicho hallazgo debe reportarse obligatoriamente como análisis de sensibilidad *post-hoc***, manteniendo el resultado congelado como el oficial.

3. **Inmutabilidad de los Embeddings y Manifiestos:**
   * La biblioteca de 22 bloques se toma tal como quedó auditada en `data_inventory.json` (hashes SHA-256 verificados). No se regeneran embeddings ni se alteran etiquetas para acomodar resultados.

4. **Transparencia en Reporte de Generalización:**
   * La tesis declarará explícitamente que los 6 datasets canónicos formaron parte del ecosistema de desarrollo de la cátedra.
   * La evidencia experimental se defenderá como **evaluación retrospectiva rigurosamente aislada por partición**, reconociendo los límites inherentes a la reutilización de benchmarks establecidos en visión por computadora.

## 3. Exposición adicional: v2 y auditoría del 10 de octubre

- Suite `phase3_v2_suite`: resultados externos de las 27 condiciones, ocho métodos, presupuesto estimado de 35 ms y base ResNet fija. Manifiestos entre 8 y 9 de octubre; inspección y recálculo el 10 de octubre.
- Información observada: H2 0,918317 frente a Completa-6 0,934073 en media equiponderada; H2 no mejora H1 globalmente; enriquecimiento de estado empeora. Todas las rutas H2 tienen como máximo una adquisición posterior a la base.
- Decisiones posteriores a esta exposición: revisar selección de base+política, factibilidad multietapa y contrato de presupuesto; propuestas de piloto a 35/45/75 ms modelados. No presentarlas como decisiones anteriores a v2 ni como validación ciega.
- Las referencias22 importadas por v2 tienen problemas de emparejamiento. Su corrección es una reparación de procedencia, no un nuevo experimento ni autorización para seleccionar modelos por sus resultados externos.
- No se generaron nuevas predicciones externas en esta auditoría. Una futura v3 debe registrar su protocolo antes de ejecutarse y mantener explícita la exposición histórica de estos seis datasets.

## 4. Exposición posterior: P0–P4 y cascada seleccionada

Esta entrada corresponde al corte `08c3ebb` del 10 de octubre, posterior al apartado3. Véase [auditoría actual](AUDITORIA_P0_P4_CASCADA_2026-10-10.md).

- P0 reparó procedencia sin entrenar: registro Completa/GFS 27/27 y Top-k 24/27. No reescribió referencias incorrectas ya guardadas en v2.
- P1–P3 observó resultados internos DTD oficial1 y Soil fold0 a 35/45/75 ms con ResNet/SigLIP. Estas variantes se decidieron después de observar v2; no son confirmación independiente. Hay reutilización interna de datos de sintonización documentada en la auditoría.
- P4 observó rutas/predicciones sobre 20 imágenes externas DTD oficial1, todas banded. Acuerdo90% de ruta final y95% de predicción. La muestra ya quedó expuesta para futuros cambios de extractor/paridad; no reutilizarla como validación ciega.
- La cascada seleccionada añadió evaluación de 27 condiciones: base/umbral elegidos en entrenamiento con el Top-k archivado fijo. Protocolo commit `a8de0dd`, resultados `cfb7605`, figuras `08c3ebb`. Su diseño sigue siendo posterior a resultados anteriores del proyecto, aunque se versionara antes de evaluar esta variante.
- Se observaron macro-F1 descriptivo medio0,934505 y reducción de costo proyectada 75,5%; cuatro datasets superan su Top-k de origen, dos no. No se identificó equivalencia ni ahorro físico pareado.
- KTH proviene de Top-k anterior (`ngram22_beitv2`), distinto del registro `innergrp_sample_v1`. La agrupación sample al calibrar la cascada no prueba que la selección original del Top-k siguiera la misma regla. La auditoría separó esta procedencia y limitó sus contrastes conjuntos a los otros cinco datasets.
- Las decisiones de priorizar validación física de la cascada, revisar la puerta, guardar predicciones y reconciliar KTH son **posteriores** a esta exposición. La presente actualización solo revisa/reporta artefactos; no genera nuevas predicciones externas.
