# Ronda 1 — Cambios aplicados a `carlos/main.tex`

Fecha: 2026-11-15. Hoja de ruta: [RONDA1_REVISION.md](RONDA1_REVISION.md). Skill: `academic-paper`, modo `revision`.

Los cambios se aplicaron con ediciones puntuales; cada una exige que el texto original coincida exactamente. No hubo experimentos nuevos. El único cálculo nuevo es la no inferioridad de la cascada, hecho sobre `carlos/analisis_paper/e1_medias_por_dataset.csv` con `no_inferioridad.awk`.

| ID | Estado | Qué se hizo | Dónde |
|---|---|---|---|
| R1 | Hecho | No inferioridad de la cascada frente a Top-4 directo con δ = 0,01: diferencia media +0,0001, IC 95 % [−0,0017; 0,0019], cota unilateral −0,0013, p(t) < 0,0001, Wilcoxon exacto unilateral p = 0,0156. Con δ = 0,005, p(t) = 0,0004. Se declara que el análisis se definió después de observar E1 | §4.4 (método), §4.7, resumen, aspecto destacado 5, discusión, limitaciones, conclusión |
| R2 | Hecho | En 26/27 condiciones la etapa barata es un bloque de Top-4; la excepción es CUReT A→B (ResNet-50) | §4.7, discusión |
| R3 | Hecho | Cita de RADAM (Scabini et al., 2023, *Pattern Recognition* 143, 109802) | §4.1, `references.bib` |
| R4 | Hecho | Resumen reducido de 285 a menos de 250 palabras | Resumen |
| R5 | Hecho | El cambio de métrica no favorece las conclusiones: en macro-F1, Top-4 tenía el mejor rango medio con SVM, y en E1 las dos métricas dan diferencias menores que 0,0002 | §4.6, limitaciones |
| R6 | Hecho | «Similar» reemplazado por las diferencias: −0,0027 con SVM y +0,0037 con ResMLP | Resumen, discusión, conclusión |
| R7 | Hecho | Antecedentes de las compuertas: IDK cascades (Wang et al., UAI 2018), clasificación selectiva (Geifman y El-Yaniv, NeurIPS 2017) y puntaje máximo del softmax (Hendrycks y Gimpel, ICLR 2017). Las cuatro referencias se verificaron en la web antes de agregarlas | §2.2, §3.4, `references.bib` |
| R8 | Hecho | Rótulos de la plantilla en español («Información», «Palabras clave», «Resumen», «Página x de y», «Contribución de los autores (CRediT)»), babel en español y separación silábica española | Preámbulo |
| R9 | Hecho | Secciones de conflicto de intereses, financiamiento y uso de IA generativa, marcadas «Pendiente de confirmación por los autores» | Final del documento |
| R10 | Hecho | Se nombra la suite Outex_TC_00013 | §4.1 |
| R11 | Hecho | La entropía se calcula sobre los valores crudos de la función de decisión, sin calibración ni temperatura | §3.4 |
| R12 | Hecho | Frase sobre inferencia por lotes | Discusión |
| — | Extra | Título de §4.8: «Medición física de una cascada anterior» | §4.8 |

## Referencias verificadas

- [RADAM, Pattern Recognition 143 (2023)](https://repositorio.unesp.br/entities/publication/013ff898-e6d5-46fe-85d0-5833c0c0cc26/full), DOI 10.1016/j.patcog.2023.109802
- [Hendrycks y Gimpel, ICLR 2017](https://arxiv.org/abs/1610.02136)
- [Geifman y El-Yaniv, NeurIPS 2017, pp. 4878–4887](https://mlanthology.org/neurips/2017/geifman2017neurips-selective)
- [Wang et al., IDK Cascades, UAI 2018, pp. 580–590](https://mlanthology.org/uai/2018/wang2018uai-idk/)
