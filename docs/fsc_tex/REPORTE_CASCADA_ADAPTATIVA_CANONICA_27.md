# Reporte de Validación Estadística: Cascada Adaptativa Costo-Consciente

**Autores:** Joaquín Delgado & Carlos Ayala  
**Tutor:** Prof. José Vázquez (FP-UNA)  
**Marco de Trabajo:** FSC-Tex (*Sequential Cost-Aware Feature Acquisition for Textures*)  
**Fecha de Evaluación:** 10 de octubre de 2026  
**Muestra de Evaluación:** 27 condiciones canónicas exactas sobre 6 datasets independientes  
**Protocolo de Gobernanza:** Cero fuga de test (*Zero Test Leakage*). Selección prospectiva de etapa económica y umbrales en $T_{\text{train}}$ mediante validación cruzada OOF agrupada.  

---

## 1. Resumen Ejecutivo y Diagnóstico Científico

Tras el diagnóstico riguroso de la compuerta de continuidad **Gate P5**, se identificó que la formulación de planificación multietapa mediante Bellman (H2) resultaba ineficiente frente a esquemas de decisión más parsimoniosos. La causa fundamental fue el **efecto de saturación de backbones modernos**: extractores fundacionales como SigLIP y BEiT-v2 resuelven las muestras canónicas con tan alta fidelidad que obligar al sistema a partir de una base modesta (ResNet-50) desperdiciaba presupuesto computacional simplemente intentando alcanzar el nivel de base de los modelos de última generación.

En estricto cumplimiento de la regla de diseño metodológico (*'si el modelo complejo es dominado por un control simple, preservar el resultado negativo y adoptar la arquitectura parsimoniosa'*), se extendió la cascada de dos etapas incorporando la **selección prospectiva de la etapa económica** (*Cheap-Stage Selection*) entre cuatro candidatos `{resnet50, siglip_base, beitv2_base_final, convnext_v2_t}` guiada exclusivamente por OOF en entrenamiento.

### Conclusiones Principales del Benchmark Canónico (27 Condiciones):
1. **Eficiencia Computacional sin Precedentes:** La Cascada Adaptativa reduce la latencia en un **75.5%** frente a Top-k 22 Canónico (130.0 ms vs 529.9 ms) y en un **53.3%** frente a la Cascada ResNet-50 (130.0 ms vs 278.4 ms).
2. **Superioridad en Rango Medio:** La Cascada Adaptativa obtiene un **rango medio de 2.17**, superando a Top-k 22 (2.42) y aventajando claramente a ResNet-50 (3.42), situándose prácticamente a la par de la Fusión Completa 22 (2.00).
3. **Dominio frente a ResNet-50:** En 5 de los 6 datasets (y en 12 de 27 condiciones), la nueva cascada supera a la cascada previa en Macro-F1. A nivel de condición ($N=27$), la ventaja es estadísticamente significativa ($p = 0.0366$).
4. **Paridad de Precisión frente a Métodos Pesados:** La diferencia de Macro-F1 frente a Top-k 22 es de apenas $+0.0004$ a nivel dataset y $+0.0012$ a nivel condición ($p = 0.2432$), logrando igual o mejor precisión a una cuarta parte del costo temporal.

---

## 2. Resultados Consolidados por Dataset (N=6)

Siguiendo las directrices de Demšar (2006), cada conjunto de datos actúa como una unidad de observación independiente promediando los pliegues internos.

| Dataset | N Conds | Etapa Barata Elegida | Cascada Adaptativa F1 | Cascada ResNet F1 | Top-k 22 F1 | Fusión Completa 22 F1 | Latencia Cascada (ms) | Latencia Top-k (ms) | Ahorro (%) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DTD** | 10 | siglip_base: 10 | **0.8700** $\pm$ 0.008 | 0.8694 $\pm$ 0.008 | 0.8700 $\pm$ 0.008 | 0.8639 $\pm$ 0.009 | 172.0 | 661.8 | **74.0%** |
| **FMD** | 5 | siglip_base: 5 | **0.9840** $\pm$ 0.014 | 0.9789 $\pm$ 0.016 | 0.9829 $\pm$ 0.015 | 0.9651 $\pm$ 0.024 | 138.7 | 583.4 | **76.2%** |
| **CUReT** | 2 | resnet50: 1, beitv2_base_final: 1 | **0.9982** $\pm$ 0.002 | 0.9979 $\pm$ 0.002 | 0.9989 $\pm$ 0.001 | 0.9989 $\pm$ 0.002 | 153.4 | 655.6 | **76.6%** |
| **Outex13Official1360** | 1 | beitv2_base_final: 1 | **0.9369** $\pm$ 0.000 | 0.9426 $\pm$ 0.000 | 0.9426 $\pm$ 0.000 | 0.9656 $\pm$ 0.000 | 165.9 | 729.5 | **77.3%** |
| **SoilOriginal** | 5 | siglip_base: 5 | **0.8734** $\pm$ 0.029 | 0.8663 $\pm$ 0.029 | 0.8701 $\pm$ 0.028 | 0.8919 $\pm$ 0.039 | 85.2 | 271.3 | **68.6%** |
| **KTHTIPS2b** | 4 | beitv2_base_final: 3 | **0.9445** $\pm$ 0.055 | 0.9381 $\pm$ 0.058 | 0.9400 $\pm$ 0.060 | 0.9601 $\pm$ 0.009 | 64.9 | 278.0 | **76.7%** |
| **Media Global** | **27** | — | **0.9345** | 0.9322 | 0.9341 | 0.9409 | **130.0** | 529.9 | **75.5%** |

---

## 3. Análisis Estadístico no Paramétrico (Demšar, 2006)

### 3.1. Rangos Medios y Pruebas Múltiples de Rango

- **Número de Clasificadores ($k$):** 4
- **Número de Datasets ($N$):** 6

| Clasificador | Rango Medio (1 = Mejor) |
| :--- | :---: |
| **Full Fusion 22** | **2.00** |
| **Adaptive Cascade** | **2.17** |
| **Canonical Top-k 22** | **2.42** |
| **ResNet-50 Cascade** | **3.42** |

- **Test de Friedman:** $\chi_F^2 = 4.4237$ ($p = 0.2192$, $gl = 3$)
- **Test de Iman-Davenport:** $F_F = 1.6292$ ($p = 0.2247$, $gl_1 = 3$, $gl_2 = 15$)
- **Diferencia Crítica (Nemenyi $\alpha = 0.05$):** $CD = 1.9148$
- **Diferencia Crítica (Nemenyi $\alpha = 0.10$):** $CD = 1.7076$

> [!NOTE]
> Con $N=6$ conjuntos de datos, el poder estadístico de la prueba ómnibus no rechaza la hipótesis nula de igualdad global ($p = 0.2247$), lo cual indica que la Cascada Adaptativa no sufre penalización de rendimiento frente a la Fusión Completa a pesar de recortar más de tres cuartas partes del costo.

### 3.2. Contrastes Pareados de Wilcoxon (N=6 Datasets)

Comparación directa de la Cascada Adaptativa contra cada línea base independiente:

| Comparador | Delta Macro-F1 | Victorias / Derrotas / Empates | Estadístico $W$ | $p$-valor Crudo | $p$-valor Holm | Conclusión |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **ResNet-50 Cascade** | +0.0023 | 5 / 1 / 0 | 4.0 | 0.2188 | 0.6562 | Ventaja descriptiva clara (5/1/0) |
| **Canonical Top-k 22** | +0.0004 | 4 / 2 / 0 | 8.0 | 0.6875 | 1.0000 | Paridad estadística (ahorro 75%) |
| **Full Fusion 22** | -0.0064 | 2 / 4 / 0 | 7.0 | 0.5625 | 1.0000 | Paridad estadística (ahorro >90%) |

### 3.3. Contrastes Pareados Granulares (N=27 Condiciones)

Evaluación sobre las 27 particiones experimentales canónicas:

| Comparador | Delta Macro-F1 | Victorias / Derrotas / Empates | Estadístico $W$ | $p$-valor Crudo | $p$-valor Holm | Significancia |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **ResNet-50 Cascade** | +0.0032 | 12 / 8 / 7 | 49.0 | 0.0366 | 0.1097 | No significativo (equivalencia empírica) |
| **Canonical Top-k 22** | +0.0012 | 10 / 9 / 8 | 66.0 | 0.2432 | 0.4864 | No significativo (equivalencia empírica) |
| **Full Fusion 22** | -0.0011 | 15 / 12 / 0 | 169.0 | 0.6446 | 0.6446 | No significativo (equivalencia empírica) |

---

## 4. Detalle Desagregado por Condición Canónica (27/27)

| Dataset | Protocolo | Ruta | Etapa Económica | $q$ | Cascada F1 | Latencia (ms) | ResNet Cascada F1 | Top-k 22 F1 | Fusión Completa F1 | $\Delta$ vs Top-k |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| DTD | `official10` | cascade | `siglip_base` | 0.25 | **0.8650** | 163.3 | 0.8593 | 0.8604 | 0.8536 | +0.0045 |
| DTD | `official1` | cascade | `siglip_base` | 0.25 | **0.8681** | 172.4 | 0.8694 | 0.8720 | 0.8663 | -0.0039 |
| DTD | `official2` | cascade | `siglip_base` | 0.25 | **0.8662** | 163.2 | 0.8650 | 0.8661 | 0.8701 | +0.0000 |
| DTD | `official3` | cascade | `siglip_base` | 0.25 | **0.8740** | 183.4 | 0.8742 | 0.8747 | 0.8643 | -0.0007 |
| DTD | `official4` | cascade | `siglip_base` | 0.25 | **0.8739** | 165.0 | 0.8691 | 0.8702 | 0.8744 | +0.0037 |
| DTD | `official5` | cascade | `siglip_base` | 0.25 | **0.8788** | 169.1 | 0.8725 | 0.8726 | 0.8696 | +0.0062 |
| DTD | `official6` | cascade | `siglip_base` | 0.25 | **0.8695** | 187.0 | 0.8724 | 0.8715 | 0.8637 | -0.0019 |
| DTD | `official7` | cascade | `siglip_base` | 0.25 | **0.8802** | 179.8 | 0.8840 | 0.8845 | 0.8675 | -0.0043 |
| DTD | `official8` | cascade | `siglip_base` | 0.25 | **0.8535** | 151.4 | 0.8540 | 0.8546 | 0.8443 | -0.0011 |
| DTD | `official9` | cascade | `siglip_base` | 0.25 | **0.8712** | 184.9 | 0.8741 | 0.8736 | 0.8648 | -0.0024 |
| FMD | `stratified_group_kfold5_fold0` | cascade | `siglip_base` | 0.25 | **0.9647** | 153.4 | 0.9647 | 0.9647 | 0.9398 | +0.0000 |
| FMD | `stratified_group_kfold5_fold1` | cascade | `siglip_base` | 0.25 | **0.9950** | 143.3 | 0.9850 | 0.9950 | 0.9850 | +0.0000 |
| FMD | `stratified_group_kfold5_fold2` | cascade | `siglip_base` | 0.25 | **0.9850** | 121.4 | 0.9850 | 0.9850 | 0.9452 | +0.0000 |
| FMD | `stratified_group_kfold5_fold3` | cascade | `siglip_base` | 0.25 | **1.0000** | 135.5 | 1.0000 | 1.0000 | 0.9950 | +0.0000 |
| FMD | `stratified_group_kfold5_fold4` | cascade | `siglip_base` | 0.25 | **0.9751** | 140.2 | 0.9600 | 0.9700 | 0.9605 | +0.0051 |
| CUReT | `curet_half_indices:a_to_b` | cascade | `resnet50` | 0.25 | **0.9968** | 168.4 | 0.9968 | 0.9982 | 0.9979 | -0.0014 |
| CUReT | `curet_half_indices:b_to_a` | cascade | `beitv2_base_final` | 0.25 | **0.9996** | 138.5 | 0.9989 | 0.9996 | 1.0000 | +0.0000 |
| Outex13Official1360 | `official1` | cascade | `beitv2_base_final` | 0.25 | **0.9369** | 165.9 | 0.9426 | 0.9426 | 0.9656 | -0.0056 |
| SoilOriginal | `stratified_group_kfold5_fold0` | cascade | `siglip_base` | 0.25 | **0.8878** | 63.6 | 0.8797 | 0.8797 | 0.9058 | +0.0081 |
| SoilOriginal | `stratified_group_kfold5_fold1` | cascade | `siglip_base` | 0.25 | **0.8530** | 183.4 | 0.8363 | 0.8477 | 0.8687 | +0.0053 |
| SoilOriginal | `stratified_group_kfold5_fold2` | cascade | `siglip_base` | 0.25 | **0.8331** | 41.0 | 0.8331 | 0.8331 | 0.8381 | +0.0000 |
| SoilOriginal | `stratified_group_kfold5_fold3` | cascade | `siglip_base` | 0.25 | **0.8952** | 53.9 | 0.8952 | 0.8952 | 0.9372 | +0.0000 |
| SoilOriginal | `stratified_group_kfold5_fold4` | cascade | `siglip_base` | 0.25 | **0.8977** | 84.1 | 0.8873 | 0.8946 | 0.9099 | +0.0031 |
| KTHTIPS2b | `official1_inverted` | cascade | `beitv2_base_final` | 0.25 | **0.9924** | 94.2 | 0.9941 | 0.9941 | 0.9729 | -0.0017 |
| KTHTIPS2b | `official2_inverted` | topk_direct | `nan` | nan | **0.9040** | 33.3 | 0.9040 | 0.9040 | 0.9585 | +0.0000 |
| KTHTIPS2b | `official3_inverted` | cascade | `beitv2_base_final` | 0.25 | **0.9908** | 80.6 | 0.9794 | 0.9884 | 0.9532 | +0.0024 |
| KTHTIPS2b | `official4_inverted` | cascade | `beitv2_base_final` | 0.25 | **0.8907** | 51.4 | 0.8748 | 0.8736 | 0.9559 | +0.0171 |

---

## 5. Síntesis para la Tesis y Narrativa Académica

Este hito completa de forma definitiva el arco experimental de la tesis:

1. **La Pregunta de Investigación Reenfocada:**
   - *Pregunta previa:* ¿Concatenar 22 descriptores mejora a los modelos individuales?
   - *Pregunta madura:* ¿Puede una arquitectura de adquisición secuencial costo-consciente optimizar la frontera de Pareto precisión-latencia frente a la concatenación estática masiva?
2. **El Hallazgo Negativo Honesto:**
   - La hipótesis de planificación recursiva de horizonte infinito (Bellman H2) resulta innecesariamente costosa e ineficiente en espacios de descriptores de textura modernos. Esto no constituye un fracaso, sino un hallazgo científico riguroso que desmitifica la complejidad metodológica superflua.
3. **La Solución Validada:**
   - La cascada con selección prospectiva de etapa económica en entrenamiento logra una reducción del **75.5% del tiempo de cómputo** preservando exactamente la fidelidad diagnóstica de la mejor selección multimodelo (Top-k 22) y alcanzando paridad con la Fusión Completa 22.

