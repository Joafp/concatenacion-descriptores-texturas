# FSC-Tex Fase 3 v2: reporte exploratorio (27 condiciones)

**Revisión del reporte:** 10 de octubre de 2026. Resultados de las corridas originales conservados.

**Autores:** Joaquín Delgado & Carlos Ayala  
**Tutor:** Prof. José Vázquez (FP-UNA)  
**Marco de Trabajo:** FSC-Tex (*Sequential Cost-Aware Feature Acquisition for Textures*)  
**Artefactos:** `results/exploratory/fsc_tex/phase3_v2_suite/`. Métricas recalculadas desde predicciones; no se reentrenaron los modelos.

**Estado ARS: ANALYZED**, no reproducción integral ni revisión independiente. Véase [auditoría del 10 de octubre](AUDITORIA_FASE3_V2_2026-10-10.md).

---

## 1. Alcance y limitaciones

La v2 incorpora correcciones de presupuesto, objetivos de continuación y selección interna. Los hitos R0–R6 no están íntegramente cerrados: completar archivos no demuestra todas las hipótesis del plan.

1. **Selección interna:** el código ajusta lambda, q y aumentador dentro de entrenamiento. Los benchmarks ya se observaron durante el desarrollo; esto no es generalización ciega. Los booleanos de `audit.json` no certifican por sí solos ausencia de filtración de toda la tubería.
2. **Costos estimados:** todos los ms y ahorros de las tablas provienen de sumas de constantes de `HardwareCostModel`, incluido overhead supuesto de 0.45 ms por bloque. No son latencias end-to-end medidas de FSC-Tex; el p95 guardado también es de costos modelados.
3. **Presupuestos guardados:** [35.0] ms modelados. Con base ResNet y los cinco candidatos de esta suite, la ruta mínima con dos adquisiciones adicionales cuesta 37.19 ms. A 35 ms no es factible: H1/H2 no aísla planificación multietapa, aunque el objetivo H2 ya utiliza valores predichos en lugar del mínimo de pérdidas futuras reales.
4. **Controles:** mejor individual entre seis bloques, par fijo ResNet+SigLIP y cascada ResNet más un aumentador. El identificador histórico `Cascade_TopK_Prospective` no representa Top-k22. La cascada se calibra por costo medio y puede exceder 35 ms por imagen; H2 restringe cada ruta. No son presupuestos duros equiparables.
5. **Referencias históricas de v2 en cuarentena:** el importador usado para estos artefactos confundía `condition` con `outer_fold` y las direcciones CUReT. P0 corrigió después el código y generó un registro trazable (Completa/GFS 27/27; Top-k 24/27). Eso no reescribe las referencias antiguas guardadas en v2 ni las convierte en controles validados de esta tabla.
6. **Online:** después de v2 apareció P4 sobre 20 imágenes DTD, con límites de representatividad, paridad y temporización. No es un benchmark físico pareado de esta suite que respalde sus porcentajes. Véase [auditoría posterior P0–P4/cascada](AUDITORIA_P0_P4_CASCADA_2026-10-10.md).

---

## 2. Tabla Consolidada por Dataset (Medias en Particiones Externas)

Cada celda indica macro-F1 y costo **estimado** medio en ms. El promedio final da el mismo peso a cada dataset; las condiciones no son réplicas independientes. Un mayor F1 no implica significancia.

| Dataset | Condiciones | Base (`resnet50`) | Mejor individual (6) | Par estático | Cascada base + 1 | FSC-Tex H2 | Completa-6 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DTD** | 10 | 0.7303 (12.4ms) | 0.8447 (12.1ms) | 0.8402 (24.5ms) | 0.8310 (36.4ms) | 0.8401 (28.2ms) | 0.8658 (131.2ms) |
| **FMD** | 5 | 0.8517 (12.4ms) | 0.9700 (12.1ms) | 0.9651 (24.5ms) | 0.9510 (24.2ms) | 0.9689 (27.6ms) | 0.9740 (131.2ms) |
| **CUReT** | 2 | 0.9625 (12.4ms) | 0.9938 (58.1ms) | 0.9877 (24.5ms) | 0.9961 (33.1ms) | 0.9938 (23.1ms) | 0.9989 (131.2ms) |
| **Outex13Official1360** | 1 | 0.8809 (12.4ms) | 0.8934 (58.1ms) | 0.8929 (24.5ms) | 0.9131 (15.4ms) | 0.9101 (25.1ms) | 0.9322 (131.2ms) |
| **SoilOriginal** | 5 | 0.8070 (12.4ms) | 0.8566 (18.2ms) | 0.8509 (24.5ms) | 0.8465 (19.7ms) | 0.8579 (27.8ms) | 0.8787 (131.2ms) |
| **KTHTIPS2b** | 4 | 0.8577 (12.4ms) | 0.9326 (35.4ms) | 0.9131 (24.5ms) | 0.9399 (26.5ms) | 0.9390 (23.5ms) | 0.9548 (131.2ms) |
| **PROMEDIO (Datasets)** | **6** | 0.8483 (12.4ms) | 0.9152 (32.3ms) | 0.9083 (24.5ms) | 0.9129 (25.9ms) | 0.9183 (25.9ms) | 0.9341 (131.2ms) |

---

## 3. Contrastes Estadísticos No Paramétricos Pareados (Demšar, 2006)

Wilcoxon bilateral sobre una media por dataset (N=6), con Holm sobre los seis contrastes mostrados. No se tratan folds como datasets independientes. Análisis exploratorio de baja potencia; no significancia no implica equivalencia. La familia de contrastes es la del reporte v2, sin afirmar prerregistro.

| Contraste (H2 vs.) | Datasets | Victorias-Derrotas-Empates | Delta macro-F1 | Ahorro estimado | p crudo | p Holm | Decisión (0.05) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **vs. Base (ResNet-50)** | 6 | 6-0-0 | +0.0700 | -109.0% | 0.0312 | **0.1875** | No significativo |
| **vs. Mejor individual interno (6)** | 6 | 4-2-0 | +0.0031 | +20.0% | 0.4375 | **1.0000** | No significativo |
| **vs. Par Estático (ResNet+SigLIP)** | 6 | 5-1-0 | +0.0100 | -5.6% | 0.0625 | **0.2500** | No significativo |
| **vs. Cascada base + 1 aumentador** | 6 | 3-3-0 | +0.0054 | -0.1% | 0.4375 | **1.0000** | No significativo |
| **vs. FSC-Tex H1 (Miope)** | 6 | 3-2-1 | -0.0000 | -4.2% | 0.8125 | **1.0000** | No significativo |
| **vs. Fusión Completa-6** | 6 | 0-6-0 | -0.0158 | +80.3% | 0.0312 | **0.1875** | No significativo |

---

## 4. Diagnóstico descriptivo de calidad y costo

Se comprueba el margen práctico del plan sobre estimaciones puntuales. **No se ha ejecutado una prueba formal de no inferioridad ni calculado su intervalo de confianza.** La eficiencia física queda pendiente.

- **Margen de no inferioridad:** $\epsilon = 0.005$ (pérdida máxima admisible de 0.5 puntos porcentuales de Macro-F1).
- **Meta futura:** ahorro de al menos 20% en latencia real frente a una referencia equiparable. El cálculo actual solo es una proyección del modelo de costos.

- **FSC-Tex H2 frente a Fusión Completa-6:**
  - $\Delta$ Macro-F1: `-0.0158` (Margen $\ge -0.005$: **NO CUMPLE**)
  - Ahorro **estimado**: `80.3%`. No demuestra cumplimiento de la meta física.
- **FSC-Tex H2 frente a cascada base + 1 aumentador:**
  - $\Delta$ Macro-F1: `+0.0054`
  - Ahorro estimado relativo: `-0.1%`

---

## 5. Resumen de Ablaciones del Marco FSC-Tex

Comparaciones descriptivas: H1 y el estado enriquecido reutilizan lambda seleccionado para H2; no tienen ajuste independiente equivalente. Las cifras siguientes son costos estimados, no cronometraje físico.

1. **Comparación H2 vs H1 (no identifica no miopía con este presupuesto):**
   - H1 (Miope): Macro-F1 = `0.9184` | Latencia = `24.84 ms`
   - H2 (Bellman): Macro-F1 = `0.9183` | Latencia = `25.89 ms`
   - Diferencia H2–H1: `-0.000041` de macro-F1; no atribuirla a dos adquisiciones que aquí no son factibles.

2. **Ablación 2: Representación Enriquecida del Estado (Incertidumbre + PCA de Contenido):**
   - H2 Incertidumbre: Macro-F1 = `0.9183` | Latencia = `25.89 ms`
   - H2 Enriquecido: Macro-F1 = `0.9151` | Latencia = `25.65 ms`
   - Ganancia por proyectar contenido: `-0.0032` de Macro-F1.

3. **Política adaptativa vs. par estático (costos no exactamente igualados):**
   - Par Estático (`resnet50 + siglip_base`): Macro-F1 = `0.9083` | Latencia fija = `24.52 ms`
   - FSC-Tex H2: Macro-F1 = `0.9183` | Latencia adaptativa = `25.89 ms`
   - Ventaja adaptativa: `+0.0100` de Macro-F1.

---

## 6. Conclusión y trabajo pendiente

**Veredicto: evidencia insuficiente para declarar superioridad de la propuesta.** Los archivos permiten reproducir las métricas, pero no cerrar las afirmaciones multietapa, físicas o relativas a la biblioteca de 22 bloques.

H2 difiere de Completa-6 en -1.576 puntos porcentuales de macro-F1. El margen puntual de 0.5 p.p. no se satisface; ello no constituye una prueba formal. Contrastes con p Holm < 0.05: 0/6.

Conservar v2 como exploración, sin sobrescribir sus predicciones. P0 y los pilotos posteriores ya avanzaron respecto de este corte: el estado vigente y los pendientes de KTH, validación interna, puerta y tiempo físico están en la [auditoría P0–P4/cascada](AUDITORIA_P0_P4_CASCADA_2026-10-10.md) y en el plan v1.3.
