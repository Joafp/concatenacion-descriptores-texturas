# FSC-Tex Fase 1: Informe de Factibilidad Dentro del Entrenamiento

**Fecha:** 8 de octubre de 2026  
**Documento base:** `docs/PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md`  
**Artefacto generado:** `results/exploratory/fsc_tex/phase1_feasibility_report.json`  
**Salvaguarda metodológica:** Todo el análisis se ejecutó estrictamente *Out-of-Fold* (OOF) dentro de las particiones de entrenamiento ($T_{\text{train}}$). Ningún dato de $T_{\text{test}}$ fue consultado.

---

## 1. Resumen Ejecutivo del Experimento de Fase 1

La Fase 1 evaluó empíricamente en tres dominios canónicos muy diversos (**DTD** con 47 clases, **SoilOriginal** con 7 clases y grupos geológicos, y **KTHTIPS2b** con 11 clases y 3 muestras físicas en entrenamiento con agrupamiento estricto por `sample`):

1. **¿Existe margen real entre el clasificador base y un oráculo de selección adaptativa?**  
   **Sí, masivo.** El oráculo con parada (`STOP`) eleva la exactitud entre **+10,86% y +19,34%** respecto a la base `resnet50`.
2. **¿Existe perjuicio / daño predictivo al incorporar bloques adicionales a ciegas?**  
   **Sí.** Entre el **8,4% y el 12,4%** de las muestras se corrompen (una predicción correcta de la base se vuelve errónea al añadir un extractor). Descriptores clásicos como `hog` presentan ganancias netas negativas. Esto refuta la monotonía y justifica la modelación bipolar de utilidad con acción de parada.
3. **¿Puede un selector simple anticipar si se necesita adquirir un bloque usando solo el estado observable?**  
   **Sí.** Un selector entrenado únicamente sobre el margen de certeza de la base y sus scores top-5 alcanza un **AUROC de 0,8404 en DTD, 0,9046 en Soil y 0,8735 en KTH**.

---

## 2. Métricas Consolidadas por Dataset

| Dimensión Diagnóstica | DTD (Split 1) | SoilOriginal (Fold 0) | KTHTIPS2b (Split 1 Invertido) |
| :--- | :---: | :---: | :---: |
| **Muestras en Entrenamiento ($T_{\text{train}}$)** | 3.753 | 912 | 3.564 (3 muestras físicas) |
| **Número de Clases** | 47 | 7 | 11 |
| **Folds de Validación Interna (OOF)** | 3 folds | 4 folds agrupados | 3 folds (Leave-One-Sample-Out) |
| **Exactitud Base OOF (`resnet50`)** | $71{,}86\%$ | $85{,}09\%$ | $79{,}63\%$ |
| **Macro-F1 Base OOF (`resnet50`)** | $0{,}7157$ | $0{,}7891$ | $0{,}7892$ |
| **Exactitud Oráculo con `STOP`** | **$91{,}21\%$** | **$95{,}94\%$** | **$97{,}00\%$** |
| **Margen de Mejora Teórico (*Headroom*)** | **$+19{,}34\%$** | **$+10{,}86\%$** | **$+17{,}37\%$** |
| **Fracción de Errores Reparables** | **$68{,}8\%$** | **$72{,}8\%$** | **$85{,}3\%$** |
| **Muestras con Daño por al Menos un Bloque** | **$12{,}4\%$** | **$8{,}4\%$** | **$10{,}0\%$** |
| **AUROC del Selector Observable** | **$0{,}8404$** | **$0{,}9046$** | **$0{,}8735$** |

---

## 3. Comportamiento Específico por Bloque Descriptor

### A. DTD (Texturas Describibles en Contexto Abierto)
* **Mejores extractores complementarios:** `dinov2` (+11,5% ganancia neta, repara el 13,9% y solo daña el 2,4%) y `siglip_base` (+10,8% neto).
* **Bloques con balance neutro o negativo:** `hog` (repara 2,05% pero daña 2,66%, ganancia neta **$-0,61\%$**). `lbp` y `gabor` aportan menos del $+0,27\%$ neto.

### B. SoilOriginal (Suelos Agrícolas con Estructura Fina)
* **Mejores extractores complementarios:** `siglip_base` (+4,61% neto), `beitv2_base_final` (+3,95% neto) y `vit_b16` (+3,95% neto).
* **Bloques clásicos:** Aunque `gabor` y `lbp` dañan muy poco (<0,3%), su capacidad de reparación es modesta (~0,8%).

### C. KTH-TIPS2-b (Generalización entre Muestras Físicas)
* **Mejores extractores complementarios:** `beitv2_base_final` (+11,4% neto) y `dinov2` (+10,9% neto).
* **Bloques clásicos:** `hog` tiene ganancia neta **negativa ($-0,48\%$)** y `lbp` **negativa ($-0,06\%$)**; la variación de iluminación y escala entre muestras físicas hace que los clásicos introduzcan ruido si se aplican indiscriminadamente.

---

## 4. Conclusión de la Puerta de Continuidad (Gate hacia Fase 2)

El protocolo de la propuesta establece:
> *«Avanzar a Fase 2 si: hay margen predictivo y de costo en más de un dominio y la ventaja no depende de información no disponible. Si la referencia ya domina o el oráculo apenas puede mejorar, detener antes del barrido completo.»*

**Dictamen:** **APROBADO PARA AVANZAR A FASE 2.**
1. El techo de mejora potencial es amplio (+11% a +19%) en los 3 dominios evaluados.
2. La hipótesis de perjuicio se verifica empíricamente: entre 8% y 12% de las muestras empeoran si se añade un extractor ciegamente, validando la necesidad de la acción `STOP`.
3. La capacidad predictiva de un selector simple sobre el estado observable es alta y consistente (AUC > 0,84 en todos los casos).
