# Registro de Exposición al Test (Exposure Ledger) — FSC-Tex

**Fecha:** 8 de octubre de 2026  
**Propósito:** Documentar con absoluta transparencia la historia de exposición de cada dataset y partición canónica a lo largo del desarrollo del proyecto de tesis.  
**Principio metodológico:** Haber ejecutado pruebas previas sobre un benchmark conocido introduce riesgo de sesgo de diseño. Registrar esta exposición evita presentar como «generalización ciega» decisiones que fueron influenciadas por resultados históricos.

---

## 1. Historial de Exposición por Dataset Canónico

| Dataset | Particiones Archivadas | Fases Previas en que se Evaluó | Qué Información se Observó Históricamente | Medidas de Contención para FSC-Tex |
| :--- | :---: | :--- | :--- | :--- |
| **DTD** | 10 splits oficiales (1–10) | Confirmatory 20, N-gram 21, Primary 22, Pilotos de Cascada | Macro-F1 de 22 extractores individuales, selecciones GFS, Top-k, y latencias de inferencia. | El espacio de estados y la política se ajustan **exclusivamente con validación cruzada interna anidada sobre las particiones de entrenamiento**. No se ajustan hiperparámetros de política mirando el test de los 10 splits. |
| **FMD** | 5 folds agrupados (seed 42) | Confirmatory 20, Primary 22, Ablaciones de DynaTex | Macro-F1 saturando en ~0.97–0.98. Se conoce que DINOv2 y ViTs dominan el rendimiento. | Se prohíbe fijar la ruta base a priori mirando el desempeño del test. La elección de la base (`resnet50` u otra) se valida contra el entrenamiento. |
| **CUReT** | 2 mitades complementarias (`a_to_b`, `b_to_a`) | Confirmatory 20, Primary 22, Piloto de Cascada | Macro-F1 extremadamente alto (~0.999). Prácticamente cualquier combinación profunda satura la métrica. | Se utiliza como prueba de **omisión de costo (parada temprana)**: si la predicción satura con el extractor inicial barato, la política debe emitir `STOP` y no incurrir en sobrecosto. |
| **Outex13Official1360** | 1 split oficial (1.360 imágenes) | Extensions, Primary 22, Benchmark de extracción online | Rendimiento comparativo SVM vs ResMLP, perfiles de tiempo por bloque en 20 imágenes. | Al existir un único split oficial, no admite inferencia estadística multifold. Se reporta como condición fija descriptiva. |
| **SoilOriginal** | 5 folds agrupados (seed 42) | Extensions, Primary 22, Pilotos de presupuesto PCA-LDA | Fuerte sensibilidad a la familia de descriptores; dominancia de Transformers y caída de clásicos. | Los grupos geológicos/familiares deben mantenerse estrictamente agrupados en la CV interna para evitar fuga intra-muestra. |
| **KTHTIPS2b** | 4 particiones RADAM (3 train, 1 test) | Extensions, Primary 22, Corrección de agrupamiento interno | Se demostró en el PR #1 que evaluar sin agrupar por muestra física producía saturación artificial (1.0). | **Regla estricta:** La validación interna para aprender la política debe usar obligatoriamente `--inner-group-column sample` (máximo 3 folds internos). |

---

## 2. Salvaguardas Metodológicas Contra la Filtración

Para que las conclusiones de FSC-Tex sean científicamente defendibles:

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
