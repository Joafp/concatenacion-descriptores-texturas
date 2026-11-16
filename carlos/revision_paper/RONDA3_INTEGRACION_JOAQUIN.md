# Ronda 3: integración de lo que subió Joaquín el 15-11 (noche)

Fecha: 2026-11-16. Commits integrados: `1fdf0a8`, `20aa4cb` y `7372759`.

Joaquín hizo una revisión ARS de la tesis y aplicó sus 15 correcciones, todas Minor. No corrió experimentos nuevos: solo análisis sobre resultados guardados. Este documento registra qué de eso pasó al paper (`carlos/main.tex`) y qué no.

## Qué se incorporó al paper

| Punto de Joaquín | Cambio en el paper | Dónde |
|---|---|---|
| REV-05: variación por condición y sensibilidad dejando un dataset fuera | Diferencia cascada − Top-4 directo por condición: de −0,0032 a +0,0050. Dejando un dataset fuera, la media queda entre −0,0002 (sin Soil) y +0,0007 (sin Outex), sin significancia. Se aclara que el IC de no inferioridad toma como unidad la media por dataset | §4.7, discusión, limitaciones, conclusión |
| REV-06: sensibilidad estática sin KTH | Friedman exacto sin KTH: p = 0,1242 (SVM) y 0,5216 (ResMLP). Sin Outex: 0,1242 con ambos. Ningún par es significativo tras Holm. Sin Outex, Top-4 queda 0,0036 por encima de Completa-22 con SVM | §4.6 |
| Reserva de KTH estática (Anexo B de la tesis) | La evaluación estática de KTH usa el archivo de 22 bloques; no está certificado que todos sus controles correspondan a la variante con agrupación interna corregida | §4.3, limitaciones |
| REV-08/09: reserva de Outex | Se eliminó la frase «Todos los bloques respetan el orden de las 1.360 muestras», que contradecía la reserva. Ahora se dice que el DeiT-S histórico no coincide con el registro del panel, que Top-4 no usa ViT-B/16 ni DeiT-S en Outex y que Completa-22 sí los usa | §4.1, discusión, limitaciones |
| REV-07/15: OOF condicionado | Se explica en el método que el ranking de Top-4 no se reaprende dentro de cada pliegue OOF | §3.4, limitaciones |
| REV-10/11: antecedentes | Puig et al. (2010) y Khan et al. (2015), verificados contra los PDFs de `carlos/` (título, autores, revista, páginas y DOI). Se aclara que el aporte no es la idea de concatenar o seleccionar | §2.1, `references.bib` |
| REV-12: recetas de comparadores | Dimensión y cabeza de cada adaptación (Neshov 3.072, HyTexNet 1.538, 6LBP+dCellNN 768, DeepLumina 2.000) y aclaración de que no reproducen las cifras publicadas | §4.10 |
| REV-13: siglas | Se definen CNN, MLP y GFS | §2.3, §3.2, §4.4 |
| REV-14: coseno | Fórmula, rango, invariancia de escala y alcance del umbral 0,999 (33 imágenes, tres por clase) | §4.3 |

Fuente de los números nuevos: `results/analysis/ars_revision_existing_analyses_20261115_v1/` (`e1_condition_differences.csv`, `e1_dataset_observed_ranges.csv`, `e1_leave_one_dataset_out.csv`, `static_accuracy_sensitivity_friedman.csv`, `static_accuracy_sensitivity_pairs.csv`). Las diferencias en puntos porcentuales se convirtieron a fracción, que es la unidad del paper.

## Qué no se incorporó y por qué

- REV-01 a REV-04 (cifra ResMLP k4→5, referencias cruzadas, pie de latencias, bitácora KTH): son problemas propios del texto de la tesis. En el paper la cifra ResMLP ya era coherente (0,9443 frente a 0,9420), y la bitácora KTH nunca estuvo en el cuerpo.
- Tablas completas de sensibilidad y de recetas: el paper las resume en una o dos oraciones para no alargarlo; las tablas quedan en la tesis y en la carpeta de análisis.
- Protocolo de latencia online de Top-4: está preparado, pero no se ejecutó. CUReT fold 0 y Soil folds 1 y 4 están bloqueados por ViT-B/16. El paper ya dice que la cascada con Top-4 no se midió en línea.

## Diferencia de enfoque con la tesis para conversar

La tesis dice que p = 0,5625 «no demuestra equivalencia ni no inferioridad» y muestra rangos en lugar de intervalos. El paper mantiene el análisis de no inferioridad (δ = 0,01, declarado posterior), que toma como unidad la media por dataset. No hay contradicción técnica: el no rechazo de Wilcoxon no prueba nada, y la no inferioridad es otra prueba. Igual conviene que Carlos, Joaquín y el tutor decidan si ambos documentos lo presentan igual.

## Compilación

pdfLaTeX + BibTeX sin errores, sin citas ni referencias indefinidas y sin cajas desbordadas. El PDF tiene 23 páginas: aspectos destacados + 22 numeradas. Se revisaron visualmente las páginas 10 (coseno y reserva KTH) y 14 (no inferioridad y variación).
