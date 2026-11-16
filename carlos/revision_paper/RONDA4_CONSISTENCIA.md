# Revisión simulada, ronda 4 (consistencia interna) — `carlos/main.tex`

Fecha: 2026-11-16. Skill: `academic-paper-reviewer`. Se usó el mismo panel de las rondas 1 y 2: editor, metodología, dominio, perspectiva práctica y abogado del diablo. El trabajo se hizo inline, sin subagentes.

Esta ronda no evalúa la contribución. Busca contradicciones dentro del paper:
- cifras repetidas entre resumen, aspectos destacados, texto, tablas y conclusión;
- terminología;
- afirmaciones frente a las tablas;
- afirmaciones frente a los archivos del repositorio.

La revisión es de solo lectura. Las correcciones se aplicaron después, en un paso separado (ver «Aplicación»).

## Hallazgos

| ID | Gravedad | Dónde | Inconsistencia | Corrección propuesta |
|---|---|---|---|---|
| C1 | Mayor | Introducción, párrafos 4 y 5 | Dice que se miden latencias en un piloto físico y en un panel online, y que el trabajo «contrasta esas políticas» con mediciones. Así sugiere que se midió en línea la comparación Top-4 directo / activación por margen, pero §4.8 y §4.9 aclaran que no. El piloto midió la cascada anterior, y el panel, una variante con rescate por ensamble | Nombrar qué mide cada evaluación y decir que la cascada con Top-4 no se midió en línea |
| C2 | Mayor | §4.8 frente a la discusión | §4.8 dice «La única medición física de una cascada por margen» y describe una condición por dataset. La discusión cita otra medición física: KTH-TIPS2-b, cuatro particiones, 30 imágenes, 49,45 frente a 42,61 ms. Esa medición no aparece en Resultados (fuente: `results/exploratory/topk_cascade/README.md`, `kth_tips2b/online_fair_topk/`) | Presentar la medición de KTH en §4.8 y quitar «única» |
| C3 | Mayor | §4.3, §4.9, §4.10 | El panel tiene 470 filas condición–método (94 × 5) y 230 comparaciones con métodos externos (10 estrategias × 23 resultados externos), pero la Tabla 11 muestra 3 de las 5 estrategias. Faltan dos ensambles de 15 subconjuntos de cuatro bloques (`Ens-diversidad`, `Ens-tombola` en `online_means.csv`). Esos ensambles obtienen accuracy media de 0,9452 a 0,9487, más que Top-4 y que la política por margen. Entonces §4.9 es falsa en el panel completo cuando dice «Completa-22 obtiene la mayor media con SVM, 0,9457», porque Ens-diversidad obtiene 0,9468. Además, «estrategias propias» no está definido | Nombrar las cinco estrategias, informar las medias de los ensambles con su latencia (328–352 ms de media) y limitar «la mayor media» a las tres de la tabla. Además, aclarar que la política por margen rescata con subconjuntos del ensamble por diversidad |
| C4 | Moderada | Aspecto destacado 5, resumen, §4.4, §4.7, conclusión | «Margen» nombra dos cosas: la diferencia de puntuaciones de la compuerta y el margen δ de no inferioridad. «Con un margen de 0,01, la activación por margen es no inferior» es ambiguo | Decir «margen de no inferioridad» siempre que se trate de δ |
| C5 | Moderada | Aspectos destacados 3 y 4 | Usan términos que los aspectos destacados no definen: «la misma base» y «la política por margen». El 4 puede leerse como Top-4 activada por margen, que el paper distingue explícitamente | Reformular con «etapa barata» y «variante por margen con rescate por ensamble» |
| C6 | Moderada | §4.3 | Dice que hay «tres evaluaciones que no se mezclan entre sí», pero §4.8 agrega un piloto físico | Decir «tres evaluaciones principales» y remitir al piloto |
| C7 | Moderada | §3.4 frente a §4.3 | §3.4 dice que el perfil de costos se congeló antes de la evaluación. En KTH-TIPS2-b, las constantes de EVA-02 y SigLIP-B se agregaron después de completar 25 de las 27 condiciones, antes de ajustar las dos restantes (`docs/fsc_tex/CIERRE_FIDELIDAD_KTH_E1_E2_2026-11-15.md`) | Aclararlo en §4.3 |
| C8 | Menor | §4.9 | Solo explica la diferencia panel–estático de SVM en Soil. Con ResMLP también difieren Outex (0,9294 frente a 0,9368) y KTH-TIPS2-b (0,9558 frente a 0,9596), y en Outex Top-4 no usa ViT-B/16 | Informarlas y decir que su causa no se diagnosticó |
| C9 | Menor | Tablas 7 y 8 | Las cabeceras dicen «base elegida» y «Base sola»; el texto dice «etapa barata» | Definir «base» en los títulos de las tablas |
| C10 | Menor | §3.4 | «Escalar» se usa antes de definirse; solo lo define el título de la Tabla 8 | Definirlo en el primer uso |
| C11 | Menor | Apéndice A | Da dos fuentes para las reglas de $k$ (`results/analysis/k_selection_rules/` y `carlos/analisis_paper/`) sin decir cuál corresponde a cada métrica | Aclarar: macro-F1 en la primera y accuracy (Tabla 4) en la segunda |
| C12 | Menor | Varias | «split» (3 veces) frente a «partición»; «fold» frente a «pliegue», mezcla introducida en la ronda 3; «sólo» frente a «solo» | Unificar en partición, fold y solo, y conservar «fuera de pliegue» como expansión de OOF |
| C13 | Menor | Conclusión, párrafo 1 | «La no inferioridad con margen 0,01 solo se establece con ResMLP» no dice frente a qué; el párrafo siguiente habla de otra no inferioridad | «frente a la concatenación completa» |
| C14 | Menor | Tabla 3 | «Puntaje máximo y entropía del softmax» puede leerse como el máximo del softmax, pero el texto usa el puntaje crudo de la SVM | «Puntaje máximo $s_{(1)}$ y entropía del softmax de las puntuaciones» |

## Lectura por perspectiva

- **Editor:** C1, C3 y C5 afectan lo que un lector entiende en los primeros minutos (introducción, aspectos destacados, panel). Ninguno cambia los resultados, pero C3 puede leerse como reporte selectivo si un revisor externo abre `online_means.csv`.
- **Metodología:** C2, C6 y C7 tocan la trazabilidad de las mediciones. C3 cambia una afirmación comparativa («la mayor media»).
- **Dominio:** C4 es el problema terminológico más visible para un lector del área, porque «margen» es el concepto central del título.
- **Perspectiva práctica:** C3 importa para quien quiera usar el método. Los ensambles son más precisos, pero tardan entre 1,4 y 1,5 veces lo que Top-4 en promedio, y unas nueve veces lo que la política por margen.
- **Abogado del diablo:** el argumento contrario más fuerte que sale de esta ronda es este: «el paper muestra en el panel solo las estrategias que lo favorecen; los ensambles, que la tesis sí evalúa, superan a Top-4 y a Completa-22». Se responde informándolos (C3). El trabajo no los estudia porque no son concatenaciones de un único vector y cuestan más que Top-4. Ningún hallazgo se clasificó como CRITICAL: no hay cifras de resultados mal calculadas.

## Cifras verificadas contra el repositorio (sin discrepancias)

| Afirmación | Fuente | Resultado |
|---|---|---|
| Medias de la Tabla 7 (0,9444; 468,3; 0,9426; 249,5; 0,9446; 117,1; 0,9483) | Filas de la propia tabla, medias equiponderadas | Coinciden |
| Ruta ResNet-50: 48,5 % escalado | `carlos/analisis_paper/e1_condiciones.csv` | 0,4853 |
| Escalado 9,9–30,1 %; 10/10/7 condiciones | `e1_condition_differences.csv` | Coinciden |
| Curva interna SVM: +0,0014 (3→4) y +0,0009 (4→5) | `results/exploratory/k_sweep/*/k_sweep_inner.csv` | 0,00137 y 0,00087 |
| SigLIP-B y EVA-02 en 41/47 Top-4; DINOv2-B y DINOv2-L en 32; BEiTv2-B en 19 | `k_sweep_inner.csv`, $k=4$ | Coinciden |
| Completa-22 supera a los 21 bloques en 0,0058 (Soil) y 0,0093 (KTH) | `thesis_accuracy_primary_20261115_v3/top4.csv` | Coinciden |
| Macro-F1 de Top-4: 0,9366 (SVM) y 0,9331 (ResMLP) | `top4.csv` | Coinciden |
| DINOv2-L 476 ms frente a ResNet-50 37 ms | `kth_tips2b/timing/latency_KTHTIPS2b_s42_official1_n30.json` | 476,04 y 37,08 |
| Cascada anterior: 143,1 frente a 580,3 ms; 0,9427 frente a 0,9432 | `historical_cascade.csv`, sin KTH | 143,050 y 580,33; 0,9427 y 0,9432 |
| 362.640 inferencias; 470 filas; 230 comparaciones | Recuento de imágenes de test × 5 estrategias × 2 clasificadores; 23 resultados externos × 10 | Coinciden |
| Latencias del panel, razones 1,6–12,2, «41 veces», diferencias −0,0027 / +0,0037 | `online_means.csv` | Coinciden |
| Ventajas frente a Neshov et al. (0,0045–0,0659) | Tabla 12 | Coinciden |
| Rangos y conteos de la Tabla 5 («seis con SVM, cinco con ResMLP», «once de doce») | Tabla 5 | Coinciden |

## Decisión

**Revisión menor.** No hay errores de cálculo. C1–C3 son inconsistencias de presentación que conviene corregir antes de mostrar el paper. C3 además evita que parezca un reporte selectivo.

## Aplicación

Las correcciones C1–C14 se aplicaron a `main.tex` y se verificaron compilando el PDF. Detalle:

| ID | Qué cambió |
|---|---|
| C1 | La introducción dice qué mide cada evaluación: costos proyectados para la cascada con Top-4, piloto de una cascada anterior y panel con la variante con rescate. El tercer aporte ahora es «mide en línea la latencia de Top-4 y de esa variante» |
| C2 | §4.8 dice «las mediciones físicas», llama «principal» al piloto y agrega un párrafo con la medición de KTH-TIPS2-b: ahorro de 56 y 46 % con DINOv2-L, y cascada más lenta con una Top-$k$ de un solo bloque. La discusión remite a ese párrafo |
| C3 | §4.3 nombra las cinco estrategias del panel. §4.9 limita «la mayor media» a las tres de la tabla e informa los ensambles: 0,9468 / 0,9452 (SVM) y 0,9484 / 0,9487 (ResMLP), con 328–352 ms. §4.10 explica que 230 = 10 × 23 |
| C3, hallazgo adicional | La ventaja mínima frente a Neshov et al. (0,0045 en CUReT) la comparten la política por margen con SVM y Top-4 con ResMLP, que tienen la misma accuracy (0,998396). El texto atribuía esa ventaja solo a la primera |
| C4 | «Margen de no inferioridad» en §4.4 (con aviso explícito de que no es el margen de la compuerta), el título de la Tabla 6, §4.7, limitaciones, el resumen y la conclusión. El aspecto destacado 5 dice «pérdida máxima 0,01» |
| C5 | Aspectos destacados 3 y 4 reformulados («igual etapa barata», «una variante por margen con rescate») |
| C6 | §4.3 habla de «tres evaluaciones principales … más un piloto físico» |
| C7 | §4.3: las constantes de EVA-02 y SigLIP-B se agregaron después de 25 condiciones, que no las necesitaban (las Top-4 de las particiones 1 y 3 de KTH no incluyen esos bloques), y antes de ajustar las dos restantes |
| C8 | §4.9 informa las diferencias de ResMLP en Outex y KTH-TIPS2-b. Allí Top-4 no incluye ViT-B/16 (comprobado en `results/exploratory/resmlp/k_sweep/`); la causa no se diagnosticó |
| C9 | Los títulos de las Tablas 7 y 8 definen «base» |
| C10 | §3.4 define «escalar» |
| C11 | El apéndice separa las fuentes en macro-F1 y en accuracy |
| C12 | «split» pasa a «partición»; «pliegue» a «fold» (salvo «fuera de pliegue», que expande OOF); «sólo» a «solo» |
| C13 | Conclusión: «Frente a la concatenación completa, la no inferioridad…» |
| C14 | Tabla 3: «Puntaje máximo $s_{(1)}$ y entropía del softmax de las puntuaciones» |
| Extra | Concordancia en la introducción: «las compara» |

Comprobaciones finales:
- pdfLaTeX + BibTeX sin errores, sin referencias o citas indefinidas y sin cajas desbordadas.
- 24 páginas: aspectos destacados + 23 numeradas.
- Aspectos destacados de 77 a 84 caracteres.
- Resumen de 255 unidades en la fuente; antes eran 252 y equivalían a ≈ 240 palabras en el PDF.
- Se revisaron visualmente las páginas 1, 15 y 16.
