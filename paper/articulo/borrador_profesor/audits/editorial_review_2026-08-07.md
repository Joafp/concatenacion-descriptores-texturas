# Paquete de decisión editorial — Revisión full (2026-08-07)

Manuscrito: *Selección y concatenación de descriptores heterogéneos para la
clasificación de texturas* — Ayala y Delgado (UNA-FP).
Panel: 5 revisores (EIC, Metodología, Dominio, Perspectiva, Abogado del Diablo).
Modo: full. Estado del panel: 5/5 informes independientes, síntesis sin
fabricación (cada punto traza a un informe de Fase 1).

## Decisión editorial

**MAJOR REVISION** (unánime: EIC Major, R1 Major, R2 Major, R3 Major, DA con
3 problemas CRITICAL). Regla del panel: al existir problemas CRITICAL del
Abogado del Diablo, la decisión no puede ser Accept.

## Matriz de consenso

| # | Problema | EIC | R1 | R2 | R3 | DA | Naturaleza |
|---|----------|-----|----|----|----|----|------------|
| 1 | Sin calibración contra SOTA publicado de DTD/FMD/CUReT | M3 | — | M4 | — | M7 | Consenso amplio (3) |
| 2 | Mensaje central (abstract/conclusión) excede la evidencia ("8 de 8", complementariedad) | M4 | M1 | M5 | — | C1,C2,C3,M1 | Consenso + CRITICAL |
| 3 | Cobertura de literatura insuficiente (fusión clásico+profundo, CLBP, bilinear pooling, CLIP, ResMLP sin cita, group lasso) | M5 | — | M1 | M4 | — | Consenso 3 revisores |
| 4 | Reporte estadístico incompleto: sin dispersión en el cuerpo, sin tamaño de efecto, bootstrap no especificado, Holm del log ausente en el texto | — | M1,M2,M3 | — | M5 | — | Consenso R1+DA/EIC |
| 5 | Descriptores clásicos no reproducibles (Tabla 2) + asimetría gris vs. color sin discutir | — | m7 | M2,M3 | — | Alt.7 | Consenso R2+R1+DA |
| 6 | Costo medido en la variable equivocada (dimensión/ajuste), sin extracción, memoria ni hardware | — | m6 | — | M1,M2 | Mi1 | Consenso 3 |
| 7 | Tablas suplementarias citadas pero no provistas; URL del código pendiente | M1 | M3,m5 | — | — | M8 | Consenso 3 |
| 8 | Traza de revisión visible en el texto ("incorporado durante la revisión") | M6 | — | — | — | C2 | EIC+DA |
| 9 | CUReT n=2: medias/percentiles sobre 2 direcciones dependientes | — | M4 | Mi1 | — | M1 | R1+DA |
| 10 | Baseline "mejor individual" castigado por ruido de selección; falta el oráculo externo | — | — | — | — | C1 | Solo DA (a validar) |

## Consenso entre revisores (acuerdo 5/5)

1. **El protocolo anidado, la auditoría de integridad (hashes, manifiestos,
   duplicados byte-idénticos) y la honestidad del reporte son fortalezas de
   nivel publicable.** Todos los revisores las destacan y piden conservarlas.
2. **La decisión es Major Revision, no Reject:** la evidencia es sólida,
   trazable y reencuadrable; ninguna objeción exige re-ejecutar el protocolo.
3. **El hallazgo más robusto del paper no es "GFS supera al individual" sino:
   (a) el protocolo mide fusión sin fuga; (b) la mayor parte del beneficio de
   concatenar se obtiene reuniendo bloques individualmente fuertes (top-k
   empata 40/40/4), sin que la búsqueda secuencial añada algo medible.**
   Reencuadrar el titular en ese sentido haría el paper más fuerte (DA,
   EIC, R2, R3 convergen).

## Desacuerdos entre revisores

- **Valoración global:** R1 es el más favorable (rigor 88); DA el más severo;
  EIC/R2/R3 intermedios. El desacuerdo no es sobre hechos sino sobre el peso
  del encuadre (resumen) frente al cuerpo.
- **top-k:** EIC/R2/R3 lo ven como control bien diseñado (fortaleza); DA y R1
  lo ven como control conservador (hereda k de GFS) cuyo empate refuerza la
  conclusión débil. El panel coincide en que la limitación sexta ya lo declara;
  el desacuerdo es sobre el peso interpretativo.
- **Contaminación de preentrenamiento (DA M5):** solo DA la plantea. No es
  falsable con los datos actuales; se recomienda declararla como limitación,
  no re-ejecutar.
- **El "oráculo externo" (DA C1):** R2 pide anclaje a resultados publicados,
  EIC pide tabla SOTA; DA pide reportar la media externa de los 20 descriptores.
  Es una adición barata y de alta transparencia: incorporarla.

## Decisión y fundamento

MAJOR REVISION: el diseño respalda la contribución, pero el encuadre (resumen,
conclusión), la reproducibilidad de los bloques clásicos, el reporte
estadístico y el contexto SOTA requieren trabajo acotado. Ninguna objeción
requiere re-ejecutar el protocolo experimental.

---

# Revision Roadmap (priorizado)

## Bloque A — Requerido (CRITICAL, debe resolverse antes de la próxima ronda)

- **A1. Reencuadre del titular y el resumen** (DA C1–C3, EIC M4):
  - "GFS supera al mejor descriptor elegido por validación interna", no al
    mejor individual absoluto; reportar el oráculo externo (media externa de
    los 20 descriptores) como transparencia.
  - Aplicar el margen 0,01 de forma simétrica: 4 de 8 diferencias son empates
    prácticos; titular acorde ("4 superaciones sustantivas, 4 empates").
  - Liderar con el hallazgo real: el protocolo + que la fusión se explica por
    fortaleza individual (top-k) y no por complementariedad secuencial.
- **A2. Reporte estadístico completo:**
  - Dispersión (sd) y conteos por partición dentro del manuscrito (Tabla 3 o
    apéndice incluido); no remitir a "tablas suplementarias" ausentes.
  - Tamaños de efecto pareados (d_z) para los contrastes primarios.
  - Especificar bootstrap (percentil vs BCa, B=10.000, semilla) y declarar la
    decisión sobre comparaciones múltiples alineada con el REVISION_LOG
    (Holm no está en el texto; declararlo o eliminarlo explícitamente).
  - Especificar la partición de p_emp (Eq. 3): interna o test.
- **A3. Calibración SOTA:** tabla de contexto con resultados publicados
  (linear probing DTD/FMD/CUReT: DINOv2, DeepTEN, Deep Filter Banks, etc.) y
  situar los valores del estudio frente a ellos.

## Bloque B — Mayor (afecta la contribución)

- **B1. Literatura:** ampliar Sec. 2 (CLBP Guo et al. 2010; color+textura
  Mäenpää y Pietikäinen 2004; bilinear pooling Lin 2015 / Gao 2016; VZ-Joint
  2005; combinación multi-kernel Zhang et al. 2007; CLIP Radford 2021; group
  lasso Yuan-Lin 2006; mRMR Peng 2005); citar ResMLP (Touvron et al. 2021);
  reformular el "vacío experimental" como "escala (20 extractores) + protocolo".
- **B2. Descriptores clásicos reproducibles:** completar Tabla 2 (mapeo LBP
  u2/riu2, variante DRLBP exacta, parámetros Gabor σ/espaciado, niveles de gris
  de GLCM, normalización HOG, software y rutinas); justificar resoluciones.
- **B3. Asimetría gris vs. color:** declararla como limitación y, si es
  viable, análisis suplementario de LBP por canal/opponent en Outex color;
  discutir por qué ningún clásico entra en la Tabla 5.
- **B4. Familia homogénea:** identificar qué familia ganó en cada
  configuración y su composición; integrar valores a la Tabla 3.
- **B5. Explotar el hallazgo de dominio:** la complementariedad útil reside
  dentro de las familias profundas (DTD: DINOv2-L/SigLIP/EVA-02), no en la
  mezcla clásico-profundo; discutir EVA-02 (100% → 27%).
- **B6. CUReT:** presentar los dos valores por dirección (no solo medias);
  percentiles sobre n=2 justificados o removidos; considerar análisis de
  sensibilidad con biparticiones aleatorias marcado como no confirmatorio.
- **B7. Costo de despliegue:** reportar hardware; reformular "compactas" como
  "compactas en dimensión"; si es factible, bytes/latencia de extracción por
  bloque; nombrar el peor caso (0,021 es FMD–ResMLP).

## Bloque C — Menor (pulido)

- **C1.** Eliminar la traza de revisión ("control incorporado durante la
  revisión") — preespecificar top-k como comparador.
- **C2.** Coherencia de redondeo texto-tabla (CUReT −0,0004/−0,0003;
  −0,0007/−0,0008; Outex −0,0034/−0,0035).
- **C3.** Reducir la redundancia resumen/resultados/conclusión.
- **C4.** Limpiar hacks de plantilla (ORCID, \hfuzz, comentarios).
- **C5.** Nota al pie de la Tabla 5 con el denominador (n.º de condiciones);
  frecuencia completa de las 20 familias en suplemento.
- **C6.** Título orientado al resultado; 5-6 keywords (incluir GFS).
- **C7.** Justificar el margen 0,01 (o TOST de sensibilidad).
- **C8.** Especificar estratificación de Outex (shuffle vs bloques de 20) y
  balance de clases declarado.
- **C9.** B=100 → B≥999 con semilla; resolución 1/101 reportada.
- **C10.** Declarar la amenaza de contaminación de preentrenamiento
  (DA M5) como limitación.
- **C11.** Envases: URL archivada del código, tablas suplementarias incluidas,
  manifiesto de entorno GPU (determinismo cuDNN).
- **C12.** Figura 1: anotar valores GFS/top-k/homogénea por dataset.

## Puntuaciones del panel

| Revisor | Rigor/Diseño | Validez estadística | Reproducibilidad | Recomendación |
|---|---|---|---|---|
| R1 Metodología | 88 | 70 | 76 | Major |
| EIC | Relevancia 68 | Originalidad 50 | Claridad 72 | Major |
| R2 Dominio | Cobertura lit. 55 | Precisión técnica 65 | Contribución 58 | Major |
| R3 Perspectiva | Relevancia práctica 78 | Transferibilidad 68 | Impacto 62 | Major |
| DA | 3 CRITICAL, 8 MAJOR, 5 MINOR | — | — | Major |

Nota: las puntuaciones de EIC/R2/R3 usan dimensiones distintas (rubricas
propias del skill); no son comparables entre sí.
