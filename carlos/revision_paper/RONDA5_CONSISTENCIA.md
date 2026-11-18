# Revisión simulada, ronda 5 (consistencia interna) — `carlos/main.tex`

Fecha: 2026-11-18. Skill: `academic-paper-reviewer`. Se usó el mismo panel de las
rondas 1 a 4: editor, metodología, dominio, perspectiva práctica y abogado del
diablo. El trabajo se hizo inline, sin subagentes.

**Qué se revisó.** Lo agregado el 18-11 y su coherencia con el resto del paper y
con los archivos del repositorio:
- §4.4: McNemar y kappa.
- §4.8: análisis por imagen, con la Tabla 10 y las Figuras 4 y 5.
- §4.12: síntesis de ablación, con la Tabla 14.
- El resumen recortado.
- Los agregados en discusión, conclusión y Apéndice A.

La revisión es de solo lectura. Las correcciones se aplicaron después, en un
paso separado (ver «Aplicación»).

## Hallazgos

| ID | Gravedad | Dónde | Inconsistencia | Corrección propuesta |
|---|---|---|---|---|
| C1 | Mayor | §4.8, párrafo 3 (y §4.7) | Dice que la proporción escalada es «21,1 % en promedio por condición». Pero 21,1 % es la media de las seis medias por dataset, la convención de las Tablas 7, 8 y 14. La media sobre las 27 condiciones es 21,8 % (0,2178), igual que la proporción sobre todas las predicciones (0,2177). §4.7 dice «en promedio el 21,1 %» sin aclarar la unidad | Decir «21,1 % como media de los seis datasets» en §4.8 y en §4.7 |
| C2 | Mayor | §4.8, párrafo sobre la Figura 4 | Dice que FMD y KTH-TIPS2-b son «los dos datasets en los que cada imagen aparece en el test de una sola condición». Es falso: lo mismo pasa en CUReT (mitades complementarias), Outex (una partición) y Soil (cinco folds con la semilla 42). Solo DTD repite imágenes de test entre sus diez particiones oficiales | Dar la razón real de la elección: 10 y 11 clases legibles en una figura, frente a 47, 61 y 68. Mantener que en ambos cada imagen aparece una vez |
| C3 | Moderada | §4.4 | Dice que «cada prueba usa seis bloques emparejados», pero McNemar compara imágenes dentro de cada condición. Además, McNemar supone imágenes independientes, y las de una misma muestra física o clase están correlacionadas (en KTH-TIPS2-b, 108 por muestra y clase), así que sus valores *p* pueden ser demasiado pequeños | Declarar McNemar como excepción a la unidad por dataset y decir que esa aproximación juega en contra de la conclusión de no diferencia, no a favor |
| C4 | Moderada | Tabla 14 | Muestra «1 bloque» (0,9272) e «Individual» (0,9281) como configuraciones distintas sin explicar por qué difieren, si Individual es el descriptor con mayor macro-F1 interno. Coinciden exactamente en cinco datasets y difieren solo en KTH-TIPS2-b (0,9360 frente a 0,9415). Ahí Individual viene del archivo de 22 bloques y el ranking, de la validación agrupada por muestra física (`results/exploratory/k_sweep/README.md`, `--inner-group-column sample`). Es la reserva de KTH de §4.3 | Explicarlo en la leyenda o el texto de §4.12 y avisarle a Joaquín (punto 4 de sus pendientes) |
| C5 | Moderada | §4.12, párrafo 1 | «Las dos métricas ordenan igual las configuraciones… Ninguna conclusión depende de informar accuracy en lugar de macro-F1» generaliza de más. §4.6 informa que, con SVM, los rangos medios de Top-4 y Completa-22 se invierten entre métricas | Limitar la afirmación a las medias de la Tabla 14 y remitir a la inversión de rangos de §4.6 |
| C6 | Menor | Tabla 14 | El grupo «Uso de Top-4 (SVM, E1)» usa la etiqueta interna «E1», que el paper no define | Cambiar por «27 cond.» |
| C7 | Menor | §4.8, párrafo 3; discusión, párrafo 2 | Usan «llamadas» para las predicciones almacenadas de la activación por margen. En el paper, «llamadas» designa las inferencias online del panel | Decir «predicciones de test» o «imágenes de test» |
| C8 | Menor | §4.8, párrafo 2 | «31.665 de las 31.984 imágenes»: son predicciones (pares imagen–condición). En DTD, una imagen de test puede aparecer en varias particiones oficiales | Decir «predicciones» y aclarar la repetición en DTD |
| C9 | Menor | §4.8, párrafo 3; discusión; conclusión | Los porcentajes conjuntos (96,2 % y 72,9 %) ponderan por tamaño de test, y DTD aporta el 59 % de las predicciones. Como DTD tiene la menor tasa de detección (69,6 %), el valor conjunto queda por debajo del de los demás datasets, pero el lector no puede saberlo | Indicar el peso de DTD en §4.8 |
| C10 | Menor | §4.8, párrafo sobre la Figura 5 | «La Figura 5 muestra por qué» atribuye una causa a partir de ocho imágenes de ejemplo | «sugiere por qué» |
| C11 | Menor | Figura 5 | Reproduce imágenes de KTH-TIPS2-b sin citar el dataset en la leyenda | Agregar `\citep{mallikarjuna2005kth}` |
| C12 | Menor | Apéndice A | No da las fuentes de la Tabla 14 ni de la selección de imágenes de la Figura 5 | Agregar `e1_ablacion.ps1`/`.csv`, `e2_complete_dataset_means.csv`, `selection_stats/*_metodos.csv`, `curves.csv` y el manifiesto de KTH |
| C13 | Menor | Conclusión, párrafo 1 | Todavía dice «con un margen de 0,01», contra la convención de la ronda 4 (C4: «margen de no inferioridad») | «con un margen de no inferioridad de 0,01» |
| C14 | Menor | Introducción, párrafo 5 | La contribución 2 no menciona el análisis por imagen, agregado justamente para responder que una sola métrica no alcanza | Agregar «y la examina imagen por imagen» |

## Lectura por perspectiva

- **Editor:** C2 y C1 son afirmaciones verificables que un revisor detecta
  enseguida con los archivos del repositorio. C14 importa porque la
  introducción tiene que anunciar la respuesta al pedido de más métricas.
- **Metodología:** C3 es el punto más técnico. Que las imágenes de una misma
  muestra física no sean independientes vuelve optimista a McNemar, y como
  ninguna condición es significativa, declararlo refuerza la conclusión. C9 y
  C8 tocan cómo se agregan las predicciones.
- **Dominio:** C4 es un detalle que un especialista en KTH-TIPS2-b notaría:
  Individual debería ser el primer bloque del ranking, y solo en KTH no lo es.
  Explicarlo conecta la tabla con la reserva de procedencia ya declarada. C11
  es práctica estándar al reproducir imágenes de un dataset.
- **Perspectiva práctica:** la Tabla 14 es útil para quien quiera adoptar el
  método: muestra en una sola vista que escalar más imágenes no mejora nada y
  solo cuesta más. C6 y C7 son de legibilidad.
- **Abogado del diablo:** el argumento contrario más fuerte es este: «McNemar
  con pocas discordancias tiene poca potencia; no encontrar diferencias era
  esperable y no prueba nada». El paper ya lo contesta en parte: dice que la
  ausencia de significancia no demuestra equivalencia y presenta la no
  inferioridad. C3 completa la respuesta: el sesgo de McNemar por dependencia
  iría a favor de encontrar diferencias, y aun así no aparecen. La lectura
  causal de la Figura 5 (C10) es la otra exageración posible. Ningún hallazgo
  se clasificó como CRITICAL: no hay cifras de resultados mal calculadas, y C1
  es una etiqueta mal puesta sobre un número correcto.

## Cifras verificadas contra el repositorio

| Afirmación | Fuente | Resultado |
|---|---|---|
| Tabla 10, columnas de accuracy, kappa, discordancias y compuerta | `carlos/analisis_paper/e1_resumen_por_dataset.csv` y `e1_mcnemar_compuerta.csv` | Coinciden |
| Accuracies por imagen frente a las almacenadas | `e1_por_imagen.csv` frente a `e1_conditions.csv` | Diferencia máxima 0 en 27 condiciones |
| Regla de la cascada (escalada → Top-4; no escalada → etapa barata) | `e1_por_imagen.csv` | Se cumple en las 31.984 filas |
| Proporción escalada: 21,1 % (media de datasets), 21,8 % (media por condición), 21,8 % (conjunta) | `e1_conditions.csv`, `e1_mcnemar_compuerta.csv` | 0,2106; 0,2178; 0,2177 |
| Tabla 14, accuracies | Figura 3, §4.5 y Tablas 5, 7, 8 y 9 del propio paper | Coinciden |
| Causa de C4: Individual y el primer bloque en KTH-TIPS2-b | `results/extensions/kth_tips2b/ngram22_beitv2/` y `inner_group_sample/` (`nested_fold_results.csv`, `best_individual`) | Archivo: 0,9941; 0,9108; 0,9865; 0,8746 (media 0,9415). Agrupada por muestra: media 0,9360, igual al primer bloque del ranking. Ninguna partición eligió N-gramas |
| Tabla 14, macro-F1 | `e1_ablacion.csv`, `e2_complete_dataset_means.csv`, `selection_stats/svm_metodos.csv`, `resmlp_metodos.csv`, `curves.csv` | Calculadas; la macro-F1 de Top-4 directo y de la cascada (0,9367 y 0,9368) coincide con §4.7 |
| Orden de los cuantiles en macro-F1 | `e2_complete_dataset_means.csv` | 0,936846 > 0,936740 > 0,936692: mismo orden que en accuracy |
| Algodón → lino por muestra física (cascada) | `e1_por_imagen.csv` y el manifiesto de KTH | b: 81, d: 17, a: 2; total 100 |
| Índices de test de KTH frente a las etiquetas del manifiesto | `hytex_kth_external_queue_20261102_v1/canonical_manifest.csv` | 4.752 de 4.752 coinciden |
| Palabras del resumen | `main.tex` | 249 |

## Aplicación

Se aplicaron los 14 hallazgos en `carlos/main.tex`.

| ID | Cambio aplicado |
|---|---|
| C1 | En §4.8, «21,8 % de las predicciones… (21,1 % como media de los seis datasets, la convención de las Tablas 7 y 8)». En §4.7, «el 21,1 % de las imágenes como media de los seis datasets» |
| C2 | La elección de FMD y KTH-TIPS2-b se justifica por la cantidad de clases (10 y 11 frente a 47, 61 y 68) y por su papel: benchmark de materiales y dataset que analiza HyTexNet. Se mantiene que en ambos cada imagen aparece una vez |
| C3 | En §4.4, «salvo la comparación imagen por imagen» en la frase sobre la unidad de prueba. Se agrega el supuesto de independencia de McNemar y la dirección de su sesgo |
| C4 | En §4.12, se explica que «1 bloque» e «Individual» coinciden en cinco datasets y difieren en KTH-TIPS2-b por la procedencia (archivo frente a validación agrupada). Se agregó `\label{sec:protocolo}` en §4.3 para la referencia |
| C5 | La afirmación se limita a las medias de la Tabla 14 y remite a la inversión de rangos de §4.6 |
| C6 | «(SVM, E1)» → «(SVM, 27 cond.)» |
| C7 | «llamadas» → «predicciones» o «predicciones de test» en §4.8 y en la discusión |
| C8 | «31.665 de las 31.984 predicciones», con la aclaración sobre DTD |
| C9 | En §4.8, el peso de DTD (59 %) y su efecto sobre los dos valores conjuntos |
| C10 | «sugiere por qué» |
| C11 | Cita del dataset en la leyenda de la Figura 5 |
| C12 | Apéndice A: fuentes de la Tabla 14 y de la selección de la Figura 5 |
| C13 | Conclusión: «la no inferioridad con $\delta=0{,}01$» |
| C14 | Introducción: «y examina la diferencia imagen por imagen con McNemar, matrices de confusión y la calidad de la compuerta» |

**Verificación:**
- El PDF compila sin errores, sin referencias indefinidas y sin cajas desbordadas: 28 páginas, más los aspectos destacados.
- El resumen tiene 249 palabras.
- Las cifras nuevas del texto (59 %, 0,9360 y 0,9415, 21,8 % frente a 21,1 %) salen de los archivos de la tabla anterior.
