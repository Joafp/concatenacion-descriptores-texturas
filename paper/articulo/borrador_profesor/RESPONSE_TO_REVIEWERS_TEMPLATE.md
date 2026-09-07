# Response to Reviewers — Template R->A->C (for journal Minor→Accept)
**Manuscript:** Selección y concatenación de descriptores heterogéneos...
**Version:** v6 32 págs (829 líneas) + overnight B1/C1 pending
**Decision:** Minor Revision (ARS v6 76.8/100)

Use this template for each Required Revision (R1-R5) from `Editorial Decision`:
**R#:** [Reviewer] — [Issue]
**Response:** [What was done, with line numbers]
**Change:** [Exact edit, e.g., `main.tex:491` Tabla `tab:tost` added]
**Evidence:** [Figure/Table/log]

---

## R1 — Top-k circularity (Methodology, Critical)
**Reviewer:** R1 (saga L1 61 classes) — "Top-k reuses k from GFS"
**Response:** Added Appendix A `app:topk-autonomo` `main.tex:709` with autonomous k (1..8 maximizing inner macro-F1) and Table `tab:topk-autonomo` (26-4-26 vs 27-3-26, Δ<0.002). Text `main.tex:286` now points to appendix.
**Change:** `main.tex:286` + `709-727`
**Evidence:** `results/confirmatory/...` 56/56 conditions

## R2 — Gray vs RGB asymmetry (Domain)
**Reviewer:** R2 — "Classics in gray, FMs in RGB"
**Response:** Added § `sec:ablacion-color` `main.tex:674` pilot 20 FMD images (LBP RGB 30-d vs gray, SigLIP still >0.12 above best classic) + full 15-fold design in progress (30 fits, `skimage`). Expected no reversal, consistent with RSA.
**Change:** `main.tex:674`
**Evidence:** `figures/ccm_heatmap.pdf` (LBP ρ≤0.08 FM)

## R3 — Cost is dimensional, not end-to-end (Perspective)
**Reviewer:** R3/DA — "70% dim ≠ 10× ms"
**Response:** Added Appendix B `sec:costo-busqueda` Table `tab:costo-busqueda` (640 vs 80 vs 40 fits, 8-16×) with GPU wall-clock RTX 4060 `main.tex:665` Fig `fig:pareto-flops` (DINOv2-L 167.5ms, total 393.9ms, GFS 267ms). Guide `tab:guia-practica` `main.tex:637` translates to decision rule.
**Change:** `main.tex:665,730` + `figures/pareto_flops_dtd.pdf`
**Evidence:** `measure_pareto_gpu.py` log (11 FM + 5 classics)

## R4 — Outex language (DA)
**Reviewer:** DA — "Elevó suggests effect"
**Response:** Uniformized to "incremento puntual de 4 aciertos, IC [-0.0088,0.0206], p=0.585, no distinguible de ruido" in Highlights `61`, Abstract `69`, Results `423,429`, Discussion `565`, Conclusion `704`.
**Change:** `main.tex:61,69,423,429,565,704`
**Evidence:** `paired_comparisons.csv`

## R5 — Group Lasso baseline (DA)
**Reviewer:** DA — "Why GFS if Group Lasso 1-fit exists?"
**Response:** Added § `sec:group-lasso-discusion` `main.tex:608` + Appendix C `app:group-lasso` `main.tex:751` Table `tab:group-lasso` (DTD/FMD 50/56 within ±0.01, 40 vs 640 fits, Jaccard 0.48 vs 0.43). Pilot binary DTD validated `group-lasso 1.5.0` (group_reg 0.0001→EVA02+DINOv2-L). CUReT/Outex 6 conds in overnight PID 6416.
**Change:** `main.tex:608,751` + `references.bib:494` `lui2026`
**Evidence:** `group_lasso` pilot log + `selected_subsets.jsonl`

---

## Minor — TOST, RSA, Stability (new in v6)
- **TOST** `tab:tost` `491` (8 rows, 0.01 margin, power Outex 14731)
- **RSA** `fig:rsa-heatmap` `660` (Spearman RDM 150, FM-FM 0.59, FM-LBP 0.08)
- **Stability** `tab:stability` `497` (bootstrap 1000 CI)

---

**Checklist for Accept:**
- [ ] B1 56/56 completes → update `tab:group-lasso` from 50/56 to 56/56 (2h, PID 6416)
- [ ] C1 15 folds RGB completes → create `tab:ablacion-color` (30 min)
- [ ] Final `bibtex+pdflatex x3` → 33 págs, 0 warnings → ARS v7 Accept ≥80
