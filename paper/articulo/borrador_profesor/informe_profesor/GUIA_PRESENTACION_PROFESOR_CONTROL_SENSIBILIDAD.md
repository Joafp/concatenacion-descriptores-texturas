# Guía para presentar los resultados al profesor

## Orden recomendado

### Paso 1: explicar el diseño

Decir:

> “Comparamos cinco estrategias: GFS, Top-k, concatenación completa,
> selección homogénea y mejor descriptor individual. Usamos DTD, FMD, CUReT y
> Outex como datasets.”

Luego aclarar que hay dos análisis:

- **Primary:** cuatro bloques, uno por dataset.
- **Sensitivity:** ocho bloques, separando SVM y ResMLP dentro de cada dataset.

`ControlTest` es el procedimiento; `primary` y `sensitivity` describen la
matriz de entrada.

---

## Paso 2: mostrar ControlTest primario

Archivo recomendado:

[`ControlTest/macro_f1/primary.tex`](latex_sci2s_organizado/ControlTest/macro_f1/primary.tex)

Explicar:

> “En ControlTest el programa identifica la estrategia con mejor ranking
> promedio y la compara contra las demás. El test global pregunta si existen
> diferencias entre las cinco estrategias; las tablas posteriores muestran las
> comparaciones contra el control.”

Conclusión del análisis primario:

> “Con cuatro datasets independientes, los resultados no permiten sostener
> una diferencia confirmatoria robusta entre las estrategias. Las conclusiones
> dependen del procedimiento: algunos tests globales producen señales, pero no
> hay una coincidencia completa entre Friedman, Iman-Davenport, Aligned Ranks y
> Quade.”

Para la comparación contra Individual, mostrar preferentemente la salida de
`MultipleTest` primary, porque contiene explícitamente todos los pares. En el
análisis primario, ninguna de las seis métricas mantiene una diferencia robusta
contra Individual después de Holm o Bergmann-Hommel.

---

## Paso 3: mostrar el análisis de sensibilidad

Archivo recomendado:

[`ControlTest/macro_f1/sensitivity.tex`](latex_sci2s_organizado/ControlTest/macro_f1/sensitivity.tex)

Y para todas las comparaciones por pares:

[`MultipleTest/macro_f1/sensitivity.tex`](latex_sci2s_organizado/MultipleTest/macro_f1/sensitivity.tex)

Explicar:

> “Aquí no promediamos SVM y ResMLP. Tratamos cada combinación
> dataset-clasificador como una fila. Esto aumenta de cuatro a ocho bloques y
> permite comprobar si el patrón cambia con el clasificador.”

Resultado de sensibilidad:

- GFS vs. Individual: significativo con Holm;
- Top-k vs. Individual: significativo con Holm en la ejecución multmétrica;
- Completa vs. Individual: no robusto con Holm;
- Homogénea vs. Individual: no significativa con Holm.

Este patrón se observó para accuracy, balanced accuracy, precision, recall,
macro-F1 y AUC en la ejecución CPU multmétrica.

---

## Paso 4: explicar por qué no elegimos solo el resultado favorable

Decir:

> “La sensibilidad muestra señales más fuertes, pero SVM y ResMLP reutilizan
> los mismos datasets. Por eso esos ocho bloques no equivalen a ocho datasets
> independientes. Lo presentamos como evidencia secundaria y no como
> sustituto del análisis primario.”

También aclarar que los p-valores sin ajustar no bastan: se priorizan Holm,
Shaffer y Bergmann-Hommel porque se hicieron muchas comparaciones.

---

## Conclusión para decirle al profesor

> “El análisis primario con cuatro datasets no demuestra una superioridad
> estadística general de GFS o Top-k frente a Individual. La sensibilidad por
> clasificador sí muestra diferencias favorables a GFS y Top-k en varias
> métricas, pero tiene menor autoridad confirmatoria porque reutiliza los mismos
> datasets. Por eso nuestra conclusión principal es que las estrategias
> combinadas mejoran descriptivamente, pero no podemos afirmar una superioridad
> universal con la evidencia primaria disponible.”

---

## Archivos para llevar

1. `latex_sci2s_organizado/ControlTest/macro_f1/primary.tex`
2. `latex_sci2s_organizado/MultipleTest/macro_f1/primary.tex`
3. `latex_sci2s_organizado/ControlTest/macro_f1/sensitivity.tex`
4. `latex_sci2s_organizado/MultipleTest/macro_f1/sensitivity.tex`
5. `latex_sci2s_organizado/MultipleTest/accuracy/sensitivity.tex`
6. `latex_sci2s_organizado/MultipleTest/auc_roc_ovr_macro/sensitivity.tex`

Los archivos 1 y 2 representan la conclusión principal; los archivos 3–6
permiten explicar la sensibilidad y mostrar que el patrón se revisó en más de
una métrica.
