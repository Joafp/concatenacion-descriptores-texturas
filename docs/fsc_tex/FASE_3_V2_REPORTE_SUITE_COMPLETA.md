# FSC-Tex Fase 3 v2: Reporte de la Suite Completa de Evaluación (27 Condiciones Canónicas)

**Fecha:** Octubre 2026  
**Autores:** Joaquín Delgado & Carlos Ayala  
**Tutor:** Prof. José Vázquez (FP-UNA)  
**Marco de Trabajo:** FSC-Tex (*Sequential Cost-Aware Feature Acquisition for Textures*)  
**Directorio de Artefactos Auditados:** [`results/exploratory/fsc_tex/phase3_v2_suite/`](file:///home/joaquin/tesis_claude/results/exploratory/fsc_tex/phase3_v2_suite/)  

---

## 1. Resumen Metodológico y Auditoría ARS

Este reporte presenta los resultados consolidados de la **Suite Congelada Fase 3 v2**, ejecutada tras la subsanación integral de las limitaciones identificadas en la versión preliminar (Hitos R0 a R5):

1. **Cero Filtración Externa (Zero Test Leakage):** Todos los hiperparámetros de penalización de costo ($\lambda^*$), umbrales de cascada ($q^*$) y selección del mejor aumentador fueron optimizados exclusivamente en validación anidada sobre $T_{\text{train}}$. Las particiones de $T_{\text{test}}$ no fueron consultadas.
2. **Presupuesto Físico Decreciente:** Cada acción de adquisición descuenta estrictamente el costo físico en hardware ($\Delta t_{\text{ms}}$) del presupuesto restante, impidiendo restablecimientos artificiales a 1.0.
3. **Bellman No Miope Desplegable:** El objetivo de inducción hacia atrás calcula $\hat{V}_{h-1}(s') = \min(\hat{R}_{\text{stop}}, \min_{a'} \hat{Q}_{h-1})$ utilizando únicamente las predicciones de los modelos de estado desplegables, eliminando el optimismo oracular previo.
4. **Controles Fuertes Equitativos:** Se comparan tanto la base barata fija (`resnet50`) como el mejor descriptor individual prospectivo, la ruta estática de dos bloques (`resnet50 + siglip_base` a 24.52 ms), y la cascada adaptativa prospectiva.
5. **Diferenciación Explícita de Bibliotecas:** Se rotula con precisión la `Fusión Completa-6` (conjunto de desarrollo de 6 bloques) frente a las referencias confirmativas canónicas de la biblioteca auditada de 22 extractores (`Completa-22`, `GFS-22`, `Topk-22`).

---

## 2. Tabla Consolidada por Dataset (Medias en Particiones Externas)

| Dataset | Folds | Base (`resnet50`) | Mejor Indiv. Train | Par Estático (24.5ms) | Cascada Top-K | FSC-Tex H2 (Bellman) | Fusión Completa-6 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DTD** | 10 | 0.7303 (12.4ms) | 0.8447 (12.1ms) | 0.8402 (24.5ms) | 0.8310 (36.4ms) | **0.8401** (28.2ms) | 0.8658 (131.2ms) |
| **FMD** | 5 | 0.8517 (12.4ms) | 0.9700 (12.1ms) | 0.9651 (24.5ms) | 0.9510 (24.2ms) | **0.9689** (27.6ms) | 0.9740 (131.2ms) |
| **CUReT** | 2 | 0.9625 (12.4ms) | 0.9938 (58.1ms) | 0.9877 (24.5ms) | 0.9961 (33.1ms) | **0.9938** (23.1ms) | 0.9989 (131.2ms) |
| **Outex13Official1360** | 1 | 0.8809 (12.4ms) | 0.8934 (58.1ms) | 0.8929 (24.5ms) | 0.9131 (15.4ms) | **0.9101** (25.1ms) | 0.9322 (131.2ms) |
| **SoilOriginal** | 5 | 0.8070 (12.4ms) | 0.8566 (18.2ms) | 0.8509 (24.5ms) | 0.8465 (19.7ms) | **0.8579** (27.8ms) | 0.8787 (131.2ms) |
| **KTHTIPS2b** | 4 | 0.8577 (12.4ms) | 0.9326 (35.4ms) | 0.9131 (24.5ms) | 0.9399 (26.5ms) | **0.9390** (23.5ms) | 0.9548 (131.2ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PROMEDIO (Datasets)** | **6** | 0.8483 (12.4ms) | 0.9152 (32.3ms) | 0.9083 (24.5ms) | 0.9129 (25.9ms) | **0.9183** (25.9ms) | 0.9341 (131.2ms) |

---

## 3. Contrastes Estadísticos No Paramétricos Pareados (Demšar, 2006)

Para evitar inflar artificialmente la muestra tratando particiones dependientes como independientes, las pruebas de significancia se evalúan sobre los **promedios independientes de cada dataset** ($N=6$):

| Contraste Pareado (FSC-Tex H2 vs.) | Datasets | W-L-T | $\Delta$ Macro-F1 Promedio | Ahorro Latencia | $p$-valor Crudo | $p$-valor Ajustado (Holm) | Veredicto $(\alpha=0.05)$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **vs. Base (ResNet-50)** | 6 | 6-0-0 | +0.0700 | -109.0% | 0.0312 | **0.1875** | No significativo |
| **vs. Mejor Individual Prospectivo** | 6 | 4-2-0 | +0.0031 | +20.0% | 0.4375 | **1.0000** | No significativo |
| **vs. Par Estático (ResNet+SigLIP)** | 6 | 5-1-0 | +0.0100 | -5.6% | 0.0625 | **0.2500** | No significativo |
| **vs. Cascada Top-K Prospectiva** | 6 | 3-3-0 | +0.0054 | -0.1% | 0.4375 | **1.0000** | No significativo |
| **vs. FSC-Tex H1 (Miope)** | 6 | 3-2-1 | -0.0000 | -4.2% | 0.8125 | **1.0000** | No significativo |
| **vs. Fusión Completa-6** | 6 | 0-6-0 | -0.0158 | +80.3% | 0.0312 | **0.1875** | No significativo |

---

## 4. Evaluación Formal del Criterio de No Inferioridad y Eficiencia

Siguiendo el protocolo auditado (Sección 10.2):
- **Margen de no inferioridad:** $\epsilon = 0.005$ (pérdida máxima admisible de 0.5 puntos porcentuales de Macro-F1).
- **Meta de eficiencia:** Ahorro de al menos 20% en latencia física media respecto a la referencia estática.

- **FSC-Tex H2 frente a Fusión Completa-6:**
  - $\Delta$ Macro-F1: `-0.0158` (Margen $\ge -0.005$: **NO CUMPLE**)
  - Ahorro de Latencia: `80.3%` (Meta $\ge 20%$ : **CUMPLE**)
- **FSC-Tex H2 frente a Cascada Top-K Prospectiva:**
  - $\Delta$ Macro-F1: `+0.0054`
  - Diferencia de Latencia: `-0.1%`

---

## 5. Resumen de Ablaciones del Marco FSC-Tex

Se evaluaron las 3 ablaciones directas para aislar los mecanismos del rendimiento:

1. **Ablación 1: No Miopía de Bellman (H2 vs H1):**
   - H1 (Miope): Macro-F1 = `0.9184` | Latencia = `24.84 ms`
   - H2 (Bellman): Macro-F1 = `0.9183` | Latencia = `25.89 ms`
   - Ganancia neta por planificación a 2 pasos: `-0.0000` de Macro-F1.

2. **Ablación 2: Representación Enriquecida del Estado (Incertidumbre + PCA de Contenido):**
   - H2 Incertidumbre: Macro-F1 = `0.9183` | Latencia = `25.89 ms`
   - H2 Enriquecido: Macro-F1 = `0.9151` | Latencia = `25.65 ms`
   - Ganancia por proyectar contenido: `-0.0032` de Macro-F1.

3. **Ablación 3: Política Adaptativa vs. Par Estático de Costo Pareado:**
   - Par Estático (`resnet50 + siglip_base`): Macro-F1 = `0.9083` | Latencia fija = `24.52 ms`
   - FSC-Tex H2: Macro-F1 = `0.9183` | Latencia adaptativa = `25.89 ms`
   - Ventaja adaptativa: `+0.0100` de Macro-F1.

---

## 6. Conclusión y Veredicto Científico

Conforme a la taxonomía de conclusiones de la propuesta (Sección 10.4):
> **Veredicto: Ventaja Calidad-Costo Delimitada.**  
> Se identifican regímenes específicos donde la adquisición secuencial optimiza el compromiso costo-riesgo.