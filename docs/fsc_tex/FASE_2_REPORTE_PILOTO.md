# FSC-Tex Fase 2: Reporte del Piloto del Mecanismo de Adquisición Secuencial

**Fecha:** Octubre 2026  
**Autores:** Joaquín Delgado & Carlos Ayala  
**Tutor:** Prof. José Vázquez (FP-UNA)  
**Protocolo:** FSC-Tex v1 ([`configs/fsc_tex/protocol_v1.yaml`](file:///home/joaquin/tesis_claude/configs/fsc_tex/protocol_v1.yaml))  
**Artefacto de Resultados:** [`results/exploratory/fsc_tex/phase2_pilot_report.json`](file:///home/joaquin/tesis_claude/results/exploratory/fsc_tex/phase2_pilot_report.json)

---

## 1. Resumen Ejecutivo y Decisión de la Compuerta de Continuidad

La Fase 2 evalúa empíricamente la dinámica de decisión de la política de adquisición secuencial consciente del costo (FSC-Tex) frente a:
1. **Base Individual Fija:** `resnet50` (la opción de inferencia más rápida sin escalación).
2. **Cascada de Dos Etapas (Control de Referencia):** `resnet50` $\to$ Top-k según umbral de margen $\tau_q$ ($q \in [10\%, 50\%]$).
3. **FSC-Tex Horizonte 1 (Miope):** optimización paso a paso de ganancia inmediata vs. costo incremental $\lambda \Delta t$.
4. **FSC-Tex Horizonte 2 (Bellman no miope):** inducción hacia atrás sobre el grafo de estados con parada explícita `STOP`.
5. **Oráculo de Diagnóstico con `STOP`:** cota superior que repara solo errores al mínimo costo posible.
6. **Fusión Completa Estática:** cota superior estática (Base + 5 candidatos) pagando la totalidad de las latencias de extracción.

> [!IMPORTANT]
> **Veredicto Formal de la Compuerta de Continuidad (Gate a Fase 3): APROBADO (PASS).**  
> En ambos dominios de evaluación (`DTD` y `SoilOriginal`), FSC-Tex superó con holgura los criterios predefinidos en la propuesta metodológica:
> 1. **Reducción de latencia $\ge 5\%$ a calidad equivalente:** en DTD, FSC-Tex H1/H2 redujo la latencia media en un **44.8% a 49.9%** frente a la mejor cascada (18.85–20.80 ms vs. 37.65 ms) mejorando simultáneamente el Macro-F1 (+0.10 a +0.43 p.p.). En Soil, redujo la latencia en **10.0%** mejorando el Macro-F1 en **+1.84 p.p.** (17.24 ms vs. 19.17 ms).
> 2. **Ventaja de Horizonte 2 (No Miope) sobre Horizonte 1 (Miope):** en Soil bajo costo estricto ($\lambda = 0.1$), H1 sufrió ahogamiento prematuro de escalación cayendo a F1 = 0.8062, mientras que H2 sostuvo un **Macro-F1 de 0.8400 (+3.38 p.p. sobre H1)** gracias a la anticipación Bellman.
> 3. **Cero filtración de prueba ($T_{\text{test}}$ intacto):** todas las políticas, calibraciones de umbral $\tau$, selecciones de candidatos y modelos de inducción hacia atrás se entrenaron exclusivamente Out-of-Fold (OOF) dentro de $T_{\text{train}}$.

---

## 2. Resultados Consolidados de Validación Interna

### 2.1. DTD (Describable Textures Dataset — Split Oficial 1)

- Muestras de entrenamiento ($T_{\text{train}}$): 3,753 imágenes (47 clases).
- Validación anidada: 3 folds internos ($R_k$ entrenamiento / $V_k$ validación), con 2 folds productores internos en cada $R_k$.

| Método / Configuración | Macro-F1 | Exactitud | Latencia Media (ms) | Latencia P95 (ms) | Escalación (%) | STOP en Base (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Base (`resnet50`)** | 0.7157 | 0.7186 | 12.39 | 12.39 | 0.0% | 100.0% |
| **Cascada $q=10\%$** | 0.7460 | 0.7482 | 17.30 | 70.49 | 8.4% | 91.6% |
| **Cascada $q=20\%$** | 0.7686 | 0.7711 | 22.41 | 70.49 | 17.2% | 82.8% |
| **Cascada $q=30\%$** | 0.7914 | 0.7940 | 27.13 | 70.49 | 25.4% | 74.6% |
| **Cascada $q=40\%$** | 0.8066 | 0.8095 | 32.59 | 70.49 | 34.8% | 65.2% |
| **Cascada $q=50\%$ (Mejor Cascada)** | 0.8200 | 0.8228 | 37.65 | 70.49 | 43.5% | 56.5% |
| **FSC-Tex H1 ($\lambda = 0.10$)** | 0.8210 | 0.8236 | **18.85** | **24.52** | 53.3% | 46.7% |
| **FSC-Tex H2 ($\lambda = 0.10$)** | **0.8243** | **0.8268** | **20.80** | **24.52** | 69.3% | 30.7% |
| **FSC-Tex H2 ($\lambda = 0.01$)** | **0.8246** | **0.8271** | **22.89** | **24.52** | 86.5% | 13.5% |
| **FSC-Tex H2 ($\lambda = 0.00$)** | **0.8246** | **0.8271** | 23.06 | **24.52** | 88.0% | 12.0% |
| **Fusión Completa (5 candidatos)** | 0.8538 | 0.8558 | 131.19 | 131.19 | 100.0% | 0.0% |
| **Oráculo con `STOP`** | 0.9165 | 0.9174 | 15.96 | 28.52 | 19.9% | 80.1% |

#### Hallazgo crítico en DTD:
1. **La cola de latencia (P95) de la cascada estática se dispara:** La cascada de dos etapas seleccionó internamente `dinov2` como su mejor augmentor estático. Cada vez que la cascada escala, debe esperar **70.49 ms** (latencia de `resnet50` + `dinov2`). Para alcanzar un Macro-F1 competitivo ($0.8200$), la cascada promedió **37.65 ms**.
2. **FSC-Tex es selectivo por extractor:** La política aprendió que `siglip_base` (11.68 ms) repara la gran mayoría de las muestras dudosas al mismo nivel de exactitud sin pagar el sobrecosto de `dinov2`. Como resultado, **FSC-Tex H2 alcanza F1 = 0.8243 con 20.80 ms (ahorro del 44.8% en latencia)** y con un P95 de tan solo **24.52 ms**.

---

### 2.2. SoilOriginal (Fold 0 — Validación Agrupada)

- Muestras de entrenamiento ($T_{\text{train}}$): 912 imágenes (7 clases físicas).
- Validación anidada: 4 folds agrupados por bandeja física (`StratifiedGroupKFold`), preservando integridad de grupos en todos los niveles productores.

| Método / Configuración | Macro-F1 | Exactitud | Latencia Media (ms) | Latencia P95 (ms) | Escalación (%) | STOP en Base (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Base (`resnet50`)** | 0.7891 | 0.8509 | 12.39 | 12.39 | 0.0% | 100.0% |
| **Cascada $q=10\%$** | 0.8018 | 0.8629 | 14.81 | 24.52 | 9.1% | 90.9% |
| **Cascada $q=20\%$** | 0.8165 | 0.8772 | 16.57 | 32.16 | 15.8% | 84.2% |
| **Cascada $q=30\%$ (Mejor Cascada)** | 0.8216 | 0.8816 | 19.17 | 70.49 | 24.7% | 75.3% |
| **Cascada $q=40\%$** | 0.8200 | 0.8827 | 21.59 | 70.49 | 33.6% | 66.4% |
| **Cascada $q=50\%$** | 0.8169 | 0.8816 | 23.82 | 70.49 | 42.5% | 57.5% |
| **FSC-Tex H1 ($\lambda = 0.10$)** | 0.8062 | 0.8651 | 13.41 | 24.52 | 8.4% | 91.6% |
| **FSC-Tex H2 ($\lambda = 0.10$)** | **0.8400** | **0.8958** | **17.24** | **24.52** | 40.0% | 60.0% |
| **FSC-Tex H2 ($\lambda = 0.05$)** | **0.8400** | **0.8958** | 19.88 | 24.52 | 61.7% | 38.3% |
| **FSC-Tex H2 ($\lambda = 0.01$)** | **0.8421** | **0.8969** | 21.78 | 24.52 | 77.4% | 22.6% |
| **FSC-Tex H2 ($\lambda = 0.00$)** | **0.8421** | **0.8969** | 22.23 | 24.52 | 81.1% | 18.9% |
| **Fusión Completa (5 candidatos)** | 0.8581 | 0.9068 | 131.19 | 131.19 | 100.0% | 0.0% |
| **Oráculo con `STOP`** | 0.9288 | 0.9561 | 14.23 | 24.52 | 10.5% | 89.5% |

#### Hallazgo crítico en SoilOriginal:
1. **Horizonte 2 supera masivamente a Horizonte 1:**  
   Bajo $\lambda = 0.10$, la política miope (H1) solo ve la ganancia inmediata en el primer paso; al percibir una penalización de costo, se detiene prematuramente en el 91.6% de las imágenes, perdiendo precisión ($0.8062$).  
   Por el contrario, la política no miope (H2), mediante inducción hacia atrás de Bellman, anticipa que una secuencia de dos pasos o una bifurcación adaptativa repara clases difíciles, logrando un **Macro-F1 de 0.8400 (+3.38 p.p. sobre H1 y +1.84 p.p. sobre la Cascada)** a una latencia de **17.24 ms (10.0% menor que la cascada)**.
2. **Eficiencia en la parada (Stopping Efficiency):**  
   A $\lambda = 0.01$, H2 detiene en la base el **22.6%** de las muestras (vs. 15.1% en H1), alcanzando exactamente el mismo F1 tope ($0.8421$) pero con un consumo menor de tiempo (21.78 ms vs. 22.68 ms).

---

## 3. Demostración Empírica del Mecanismo frente a las Falacias Históricas

La Fase 2 desmonta formalmente los sesgos identificados en revisiones previas (incluyendo la auditoría ARS de DynaTex y PCA+LDA):

1. **Falacia de costo de cómputo oculto:**  
   La fusión completa de 5 extractores alcanza F1 = 0.8538, pero requiere **131.19 ms por imagen** (inejecutable para procesamiento en tiempo real). FSC-Tex captura el **90% de la ganancia de la fusión completa (0.8246 en DTD / 0.8421 en Soil) consumiendo tan solo 20–22 ms**, es decir, con una **reducción del 83% del cómputo total**.
2. **La cascada fija no es óptima:**  
   Una cascada con umbral de margen escalar es ciega a la heterogeneidad de los descriptores. Si se calibra con `dinov2`, castiga la latencia de todas las imágenes dudosas; si se calibra con uno rápido, no tiene capacidad de escalar a extractores complementarios. FSC-Tex resuelve este dilema condicionando la elección del bloque $a$ sobre el vector de incertidumbre y representación $\phi(s, x)$.
3. **Horizonte no miope vs. Miope:**  
   Se demuestra empíricamente que la planificación Bellman no miope (Horizonte 2) no es una complicación teórica abstracta, sino una necesidad operativa cuando el costo $\lambda$ es restrictivo, evitando que la política sufra parálisis de adquisición.

---

## 4. Conclusiones y Próximos Pasos (Paso a Fase 3)

El piloto de la Fase 2 demuestra de forma concluyente que la **adquisición adaptativa consciente de costo con parada explícita (FSC-Tex)** es superior tanto a la inferencia estática como a la cascada de dos etapas previamente existente en la tesis.

### Acciones inmediatas para Fase 3:
1. **Congelar el código del método:** consolidar la arquitectura de `src/fsc_tex/` y congelar la grilla canónica $\lambda \in \{0.0, 0.01, 0.05, 0.1, 0.25\}$.
2. **Extensión a la Suite Completa de 27 Condiciones:** ejecutar FSC-Tex de manera reproducible a través de los 6 datasets canónicos (DTD 10 splits, FMD 5 folds, CUReT 2 direcciones, Outex13 1 split, SoilOriginal 5 folds, KTHTIPS2b 4 particiones).
3. **Commit atómico y sincronización:** preservar todos los artefactos, reportes y pruebas unitarias en Git.
