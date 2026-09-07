# Plan de Cierre Final — De Minor a Accept (mientras overnight corre)
**Paper v5:** `main.tex` 829 líneas, 32 págs, 4 figuras nuevas, 4 tablas nuevas, 1 apéndice nuevo, GPU RTX 4060 medido
**Overnight PID 6416:** B1 Group Lasso 56/56 (12:xx elapsed, ETA 13:30)
**Objetivo:** Cerrar 100% sin "preliminar/en curso" al terminar overnight, pasar ARS v6 Minor (76) → Accept (≥80)

---

## Checklist de cierre (todo medible, nada estimado al final)

| # | Item | Estado v5 | Acción cierre en esta sesión | Artefacto | Criterio Accept |
|---|------|-----------|------------------------------|-----------|-----------------|
| 1 | **TOST + potencia** | Hecho texto | **Hecho tabla** `tab:tost` `main.tex:491` con 8 filas DTD/FMD + Outex n=14731 | `tab:tost` | R1: p_TOST visible, potencia declarada |
| 2 | **RSA heatmap** | Hecho fig | **Hecho** `figures/ccm_heatmap.pdf` `main.tex:660` (Spearman RDM 150, 6 bloques, ρ 0.59 FM-FM vs 0.08 FM-LBP) | `fig:rsa-heatmap` | R2: explica paridad top-k |
| 3 | **Stability Jaccard** | Mencionado | **Hecho tabla** `tab:stability` `main.tex:497` bootstrap 1000, CI [0.405,0.463] etc. | `tab:stability` | R1: Jaccard con IC, no solo media |
| 4 | **Pareto GPU real** | Estimado | **Hecho medición** RTX 4060 11 FM + 5 clásicos `main.tex:665` Fig `fig:pareto-flops` + Tabla `tab:costo-busqueda` con ms reales (DINOv2-L 167.5ms etc., total 389ms) | `fig:pareto-flops` | R3: ms medidos, no literatura |
| 5 | **Group Lasso 50/56 → 56/56** | Preliminar 50/56 | **En curso B1** (6 conds CUReT+Outex, 180 fits L1 saga, 45-90 min). Al terminar, actualizar `tab:group-lasso` `main.tex:754` de "50/56 (n=10/15)" a "56/56 (n=10/15/2/1)" y recalcular Δ Lasso-GFS y Jaccard 0.48 | `tab:group-lasso` | R1: 56/56 sin "en curso" |
| 6 | **Color ablation FMD** | Piloto 20 imgs | **En curso C1** (15 folds, 30 fits, 30 min). Al terminar, actualizar `sec:ablacion-color` `main.tex:672` con `tab:ablacion-color` (Δ 15 folds, p pareado). Si C1 no termina hoy, dejar piloto + metodología como "Minor" (no bloquea tesis) | `tab:ablacion-color` | R2: Δ RGB-gris con p |
| 7 | **Guía práctica** | Hecho | Verificar que `tab:guia-practica` cite Pareto ms reales (ya lo hace) | `tab:guia-practica` | EIC: citable |
| 8 | **Overfulls** | 6→3 | **Hecho** `resizebox` en 3 tablas anchas `main.tex:491,735,759` (99pt→9pt max) | `main.pdf` | QA |
| 9 | **Referencias** | 29 citas | Verificar 0 undefined (ya 0) | `main.bbl` | QA |

**Cierre total = 9/9 sin "preliminar".** Si B1/C1 no terminan en esta sesión, el paper queda en **Minor sólido (76) defendible** con 4/9 en "preliminar" correctamente etiquetado; con B1+C1 termina en **Accept (≥80)**.

---

## Plan de ejecución mientras overnight corre (no bloqueante)

**Ahora (0-15 min, sin cómputo):**
- [x] TOST, RSA, stability, Pareto real, guía, overfulls → **ya hechos, 32 págs compila limpio**
- [ ] Re-ejecutar ARS v6 sobre 829 líneas (5 revisores) → obtener feedback residual
- [ ] Si ARS v6 pide pulido menor (ej. acortar `tab:roadmap` o mover 4 direcciones de Conclusión), ejecutarlo inmediato (2 min/edición)

**En paralelo (overnight 45-90 min, background):**
- [ ] B1: termina CUReT/Outex → actualizar `tab:group-lasso` 56/56
- [ ] C1: termina FMD RGB → crear `tab:ablacion-color`
- [ ] Al terminar cada uno: `bibtex+pdflatex x3` → verificar 0 warnings → re-ejecutar ARS v6 → si da Accept, entregar

**Dependencias:** A1-A3 y B2 ya no bloquean; B1 y C1 son independientes y se integran al final sin reescribir texto principal.

---

## Re-ejecución ARS v6 (ahora)

Se lanza ARS full sobre `main.tex:829` 32 págs (mismo panel 5). Se espera que EIC pase a Accept (78), R1/R3/R2 queden en Minor por B1/C1 "preliminar" — feedback esperado será exactamente "completar 56/56 y ms reales" que ya están en curso. Si ARS pide algo extra no previsto (ej. acortar `tab:roadmap` o clarificar `lui2026` preprint), se ejecuta en <5 min.

---

*Generado 2026-08-20 12:25, mientras PID 6416 lleva 14 min. Próximo checkpoint: 13:30.*
