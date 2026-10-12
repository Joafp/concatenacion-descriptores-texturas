# FSC-Tex Fase 3: Reporte de Exploración Preliminar v1 (27 Condiciones Canónicas)

> Documento histórico de v1. Para el estado vigente y los avances posteriores, consultar la [auditoría v2 del 10 de octubre](AUDITORIA_FASE3_V2_2026-10-10.md) y el [plan de trabajo 1.2](../PROPUESTA_TESIS_FUSION_SECUENCIAL_COSTO_RIESGO.md). Los próximos pasos de este archivo corresponden a su fecha original.

**Fecha:** 8 de Octubre de 2026  
**Autores:** Joaquín Delgado & Carlos Ayala  
**Tutor:** Prof. José Vázquez (FP-UNA)  
**Marco de Trabajo:** FSC-Tex (*Sequential Cost-Aware Feature Acquisition for Textures*)  
**Estado Metodológico:** **EXPLORACIÓN PRELIMINAR (v1)** — Auditado bajo estándar ARS ([`docs/fsc_tex/AUDITORIA_FASE3_2026-10-08.md`](file:///home/joaquin/tesis_claude/docs/fsc_tex/AUDITORIA_FASE3_2026-10-08.md))  
**Artefacto Canónico v1:** [`results/exploratory/fsc_tex/phase3_full_suite/summary_27_conditions.json`](file:///home/joaquin/tesis_claude/results/exploratory/fsc_tex/phase3_full_suite/summary_27_conditions.json) (SHA-256: `d28972a33e9185e049054c579101e70bc1a5f00274d78f1dbf2c9f70d4bfbe19`)  
**Manifiesto de Archivo:** [`results/exploratory/fsc_tex/phase3_full_suite/ARCHIVE_MANIFEST_V1.json`](file:///home/joaquin/tesis_claude/results/exploratory/fsc_tex/phase3_full_suite/ARCHIVE_MANIFEST_V1.json)

---

## 1. Declaración de Alcance y Salvedades de Auditoría

> [!WARNING]
> **Salvedades Metodológicas Críticas Identificadas en la Auditoría del 8 de Octubre:**
> 1. **Defecto de Presupuesto en v1:** En la implementación inicial del script evaluador v1, las llamadas a la política no pasaron ni actualizaron un presupuesto decreciente (`remaining_budget = 1.0` por defecto). Al estar normalizados los costos por el extractor base (`resnet50`, ~12.39 ms), `siglip_base` tuvo costo 0.9790 ($\le 1.0$), mientras que `beitv2` (1.0226), `convnext` (1.3019), `eva02` (1.5956) y `dinov2` (4.6893) quedaron como infactibles. **En esta corrida v1, la política operó de facto como una decisión de un solo paso entre ResNet-50 y ResNet-50 + SigLIP.**
> 2. **Latencias Estimadas por Modelo Aditivo:** Las latencias reportadas son cálculos derivados del modelo aditivo precalibrado en GPU (`HardwareCostModel`), no mediciones cronometradas online de extremo a extremo en esta corrida.
> 3. **Biblioteca Evaluada (Completa-6):** El subconjunto evaluado consistió en 6 extractores (ResNet-50 base + 5 candidatos). No comprende la biblioteca canónica de 22 bloques ni compara contra Top-k22 o GFS.
> 4. **Comparación con Cascada:** La variante de cascada reportada seleccionó el umbral $q$ retrospectivamente en test (actuando como control de referencia optimista).
> 5. **Balance en DTD:** H2 superó a la cascada en **9 de 10 splits** (en el split 3 la cascada $q=50\%$ obtuvo 0.8426 vs. 0.8411 de FSC-Tex, una diferencia de −0.16 p.p.).
> 6. **Objetivos H2 en v1:** El objetivo de inducción hacia atrás en v1 empleó el mínimo muestral de pérdidas reales futuras, introduciendo optimismo oracular en lugar del valor esperado de la política desplegable $\hat{V}_{h-1}$.

Estos resultados se preservan formalmente como **evidencia de exploración preliminar (v1)** y fundamentan las correcciones del camino crítico R1–R6 establecido en la versión 1.1 del plan de trabajo.

---

## 2. Tabla Consolidada por Dataset (Medias en Test Oficial $T_{\text{test}}$)

*Nota:* Cascada elegida retrospectivamente en test como cota superior de referencia. H1 y H2 evaluados con $\lambda = 0.0$ y $\lambda = 0.1$.

| Dataset | Condiciones | Base (`resnet50`) | Mejor Cascada (Test) | FSC-Tex H2 ($\lambda=0.0$) | FSC-Tex H2 ($\lambda=0.1$) | Completa-6 | Oráculo `STOP` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **CUReT** | 2 | 0.9625 (12.4ms) | 0.9963 (30.3ms) | **0.9877** (21.9ms) | 0.9631 (12.4ms) | 0.9989 (131.2ms) | 0.9989 (12.9ms) |
| **DTD** | 10 | 0.7303 (12.4ms) | 0.8346 (37.6ms) | **0.8402** (23.1ms) | 0.8395 (20.7ms) | 0.8658 (131.2ms) | 0.9283 (15.9ms) |
| **FMD** | 5 | 0.8517 (12.4ms) | 0.9551 (18.0ms) | **0.9651** (22.9ms) | 0.9621 (19.1ms) | 0.9740 (131.2ms) | 0.9910 (14.3ms) |
| **KTHTIPS2b** | 4 | 0.8577 (12.4ms) | 0.9422 (24.9ms) | **0.9114** (20.7ms) | 0.9051 (17.0ms) | 0.9548 (131.2ms) | 0.9797 (14.3ms) |
| **Outex13** | 1 | 0.8809 (12.4ms) | 0.9117 (15.1ms) | **0.8929** (20.3ms) | 0.8929 (17.1ms) | 0.9322 (131.2ms) | 0.9836 (14.3ms) |
| **SoilOriginal** | 5 | 0.8070 (12.4ms) | 0.8615 (17.9ms) | **0.8509** (22.2ms) | 0.8489 (16.8ms) | 0.8787 (131.2ms) | 0.9388 (14.1ms) |
| **Media 27 cond.** | **27** | **0.8086** (12.4ms) | **0.8927** (27.1ms) | **0.8887** (22.4ms) | **0.8848** (18.4ms) | **0.9137** (131.2ms) | **0.9567** (14.7ms) |
| **Media 6 datasets** | **6** | **0.8483** (12.4ms) | **0.9169** (24.0ms) | **0.9080** (21.8ms) | **0.9019** (17.2ms) | **0.9341** (131.2ms) | **0.9701** (14.3ms) |

---

## 3. Análisis Estadístico y Diagnóstico ARS

### 3.1. Contrastes de Hipótesis Pareados

1. **FSC-Tex H2 vs. Base (`resnet50`):**
   - Incremento medio de +8.01 p.p. en las 27 condiciones ($p = 7.45 \times 10^{-9}$ por Wilcoxon pareado) y +5.97 p.p. equiponderado entre los 6 datasets ($p = 0.0156$).
   - Confirma que la adquisición adaptativa de al menos un extractor adicional supera a la base fija débil.
2. **FSC-Tex H2 vs. FSC-Tex H1 (Miope vs. Bellman):**
   - En 22 de las 27 condiciones (DTD, FMD, CUReT, Soil), H1 y H2 con $\lambda=0$ arrojaron predicciones idénticas debido al defecto de factibilidad de presupuesto que impidió transiciones de paso 2.
   - Las diferencias se concentraron en KTH y Outex, dando un $p = 0.0216$ en las 27 condiciones, pero $p = 0.25$ en el contraste agregado por dataset.
   - **Conclusión de auditoría:** No se puede certificar una ventaja multietapa general en v1 hasta resolver la factibilidad decreciente en R1.
3. **FSC-Tex H2 vs. Completa-6:**
   - H2 queda 2.50 p.p. por debajo de Completa-6 a cambio de reducir la latencia estimada de 131.2 ms a 22.4 ms (ahorro del 83.0%).
   - Esta brecha excede el margen práctico de no inferioridad ($\epsilon = 0.5$ p.p.), lo cual ilustra la necesidad de permitir la adquisición de candidatos de mayor capacidad (`beitv2`, `dinov2`) cuando el presupuesto físico lo permita.

---

## 4. Estado y Próximos Pasos (Transición a R1)

Conforme a la Sección 12.0 del plan de trabajo:
- **R0:** Completado. Resultados preservados como exploración preliminar v1 con todas sus limitaciones documentadas.
- **R1:** Implementar presupuesto físico explícito decreciente en milisegundos y redefinir los objetivos de valor de Bellman hacia la política desplegable $\hat{V}_{h-1}$, respaldado por pruebas unitarias de regresión.
- **R2–R6:** Ejecutar la selección anidada prospectiva y avanzar hacia el benchmark físico online antes del nuevo barrido de Fase 3 (`phase3_v2`).
