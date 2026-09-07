# Guía para entender y explicar las pruebas estadísticas

## Objetivo de esta guía

Esta guía está escrita para preparar la explicación oral al profesor. La idea
es entender primero cada concepto y después leer nuestros resultados, sin
memorizar p-valores aislados.

---

## 1. ¿Qué queremos demostrar?

Comparamos cinco estrategias para construir la representación de textura:

1. **Individual:** se conserva el mejor descriptor individual.
2. **Homogénea:** se seleccionan descriptores de una misma familia.
3. **GFS:** Greedy Forward Selection, selección progresiva de bloques.
4. **Top-k:** se toman los mejores descriptores individuales.
5. **Completa:** se concatenan los 20 descriptores.

La pregunta no es simplemente qué promedio es mayor. La pregunta estadística
es:

> ¿Las diferencias entre estrategias son suficientemente consistentes entre
> datasets como para no explicarse por variación aleatoria?

---

## 2. ¿Cómo se organiza la información?

La entrada al programa SCI2S es una tabla donde:

- cada fila es un dataset o problema;
- cada columna es una estrategia;
- cada celda es una métrica de rendimiento.

Ejemplo simplificado:

| Dataset | GFS | Top-k | Completa | Individual | Homogénea |
|---|---:|---:|---:|---:|---:|
| DTD | 0,87 | 0,87 | 0,86 | 0,84 | 0,86 |
| FMD | 0,98 | 0,98 | 0,96 | 0,97 | 0,98 |

Dentro de cada fila se ordenan las estrategias por rendimiento y se asignan
**rangos**. El programa trabaja principalmente con esos rangos, no con los
promedios directamente.

### ¿Por qué rangos?

Los rangos reducen la dependencia de la escala de cada dataset. Un dataset
puede tener F1 entre 0,80 y 0,90 y otro entre 0,99 y 1,00; ambos pueden
compararse preguntando qué estrategia queda mejor posicionada dentro de cada
dataset.

---

## 3. ¿De dónde salen las pruebas?

### García y Herrera (2008)

Este artículo estudia la comparación de muchos clasificadores sobre varios
datasets y se concentra en las comparaciones **todos contra todos**. Explica
cómo calcular p-valores comparables y cómo corregirlos cuando se realizan
muchas comparaciones. Presenta y discute procedimientos como Nemenyi, Holm,
Shaffer y Bergmann-Hommel.

Fuente: [García y Herrera, JMLR 2008](https://www.jmlr.org/papers/v9/garcia08a.html).

### Derrac et al. (2011)

Este tutorial organiza el flujo completo para comparar algoritmos mediante
pruebas no paramétricas. Distingue entre comparar contra un método de control y
comparar todos los pares. También presenta Friedman, Iman-Davenport, Friedman
Aligned Ranks y Quade.

Fuente: [Derrac et al., Swarm and Evolutionary Computation 2011](https://sci2s.ugr.es/sites/default/files/ficherosPublicaciones/1374_2011-Derrac-SWEVO.pdf).

---

## 4. ¿Qué significa un p-valor?

El p-valor responde:

> Si realmente no hubiera diferencias entre las estrategias, ¿qué tan raro
> sería observar una diferencia como la encontrada?

Con `alpha = 0,05`:

- `p < 0,05`: se rechaza la hipótesis nula según ese procedimiento;
- `p >= 0,05`: no se rechaza la hipótesis nula.

Esto no significa que `p >= 0,05` demuestre igualdad. Puede significar que hay
pocos datasets o poca potencia estadística.

Tampoco significa que `p < 0,05` pruebe que una estrategia sea universalmente
mejor. Solo indica evidencia de diferencia bajo el diseño y procedimiento
utilizados.

---

## 5. Pruebas globales

### Friedman

Pregunta:

> ¿Existe alguna diferencia global entre las cinco estrategias?

No indica todavía qué pares son diferentes.

### Iman-Davenport

Es una versión corregida de Friedman que usa una distribución F. Busca una
aproximación más adecuada cuando hay pocos datasets.

### Friedman Aligned Ranks

Primero alinea los resultados para reducir el efecto de la dificultad general
de cada dataset y después calcula los rangos. Puede dar una conclusión distinta
de Friedman porque pondera la información de otra forma.

### Quade

Da más peso a los datasets donde las estrategias presentan diferencias grandes.
Es útil como análisis complementario, pero puede ser sensible a qué datasets se
incluyen.

Regla práctica: si los cuatro procedimientos coinciden, la evidencia es más
convincente. Si discrepan, se debe informar la discrepancia.

---

## 6. ControlTest y MultipleTest

### ControlTest

Elige una estrategia como control, normalmente la de mejor ranking promedio, y
la compara contra las demás.

En nuestro caso puede producir comparaciones como:

- GFS vs. Individual;
- GFS vs. Top-k;
- GFS vs. Completa;
- GFS vs. Homogénea.

El control no siempre es GFS. En algunos análisis primarios Top-k tuvo mejor
ranking promedio, por lo que el programa lo trató como control.

### MultipleTest

Compara todos los pares. Con cinco estrategias hay diez comparaciones:

\[
\frac{5(5-1)}{2}=10.
\]

Por eso `MultipleTest` es el archivo más directo para estudiar simultáneamente
GFS/Top-k/Completa/Homogénea frente a Individual.

---

## 7. ¿Por qué corregimos los p-valores?

Si hacemos diez comparaciones, aumenta la probabilidad de que alguna parezca
significativa solo por azar. Esto se llama problema de comparaciones múltiples.

Por eso SCI2S calcula, entre otros:

- **Bonferroni:** muy conservador;
- **Holm:** controla el error familiar y suele ser una opción equilibrada;
- **Shaffer:** aprovecha las relaciones lógicas entre hipótesis;
- **Bergmann-Hommel:** puede ser más potente, pero debe reportarse junto con
  los otros ajustes.

La lectura correcta es priorizar el p ajustado, no el p sin ajustar.

---

## 8. ¿De dónde sale nuestro macro-F1?

Para cada condición, el modelo predice las etiquetas del **test externo**. El
F1 se calcula por clase y luego se promedia:

\[
F1_{macro}=\frac{1}{C}\sum_{c=1}^{C}F1_c.
\]

El cálculo del código es equivalente a:

```python
f1_score(y[test], pred, average="macro")
```

El `inner_f1` solo se usa para seleccionar descriptores dentro de GFS. El
resultado final que entra en el análisis estadístico es el `macro_f1` del test
externo.

---

## 9. Nuestros dos niveles de análisis

### Análisis primario

Usa cuatro bloques independientes:

- DTD;
- FMD;
- CUReT;
- Outex.

Los clasificadores se agregan dentro de cada dataset. Esta es la evidencia con
mayor autoridad confirmatoria.

### Análisis de sensibilidad

Se separan SVM y ResMLP, por lo que hay ocho bloques:

- DTD-SVM y DTD-ResMLP;
- FMD-SVM y FMD-ResMLP;
- CUReT-SVM y CUReT-ResMLP;
- Outex-SVM y Outex-ResMLP.

Estos bloques comparten los mismos datasets y, por tanto, no son ocho problemas
completamente independientes. Se presentan como sensibilidad, no como una
replicación confirmatoria de ocho datasets nuevos.

SoilOriginal y VisTexReference12 son extensiones suplementarias y no forman
parte de la inferencia principal.

---

## 10. Resultados primarios CPU

En la ejecución multmétrica directa de SCI2S, las comparaciones contra
Individual no fueron significativas después de Holm ni Bergmann-Hommel para
ninguna de las seis métricas:

- accuracy;
- balanced accuracy;
- precision macro;
- recall macro;
- macro-F1;
- AUC.

Esto significa que, con cuatro datasets, no podemos afirmar estadísticamente
que GFS, Top-k, Completa u Homogénea superen a Individual de manera general.

Los contrastes globales fueron mixtos. Por ejemplo, para macro-F1:

| Prueba | p |
|---|---:|
| Friedman | 0,0780 |
| Iman-Davenport | 0,0477 |
| Friedman Aligned Ranks | 0,5186 |
| Quade | 0,0160 |

La discrepancia muestra por qué no debemos elegir únicamente el resultado más
favorable.

---

## 11. Resultados de sensibilidad CPU

En la sensibilidad, las comparaciones por pares contra Individual dieron un
patrón más fuerte:

- **GFS vs. Individual:** significativo con Holm para las seis métricas;
- **Top-k vs. Individual:** significativo con Holm para las seis métricas;
- **Completa vs. Individual:** no robusto con Holm;
- **Homogénea vs. Individual:** no significativa con Holm.

Los p-valores omnibus también fueron bajos para Friedman, Iman-Davenport y
Quade en muchas métricas, mientras Friedman Aligned Ranks no rechazó la
igualdad. Esto se interpreta como apoyo secundario, no como confirmación
definitiva.

Para macro-F1, la salida histórica de `MultipleTest` mostró:

| Comparación | p sin ajustar | Holm | Bergmann-Hommel |
|---|---:|---:|---:|
| GFS vs. Individual | 0,00266 | 0,02663 | 0,02663 |
| Top-k vs. Individual | 0,00719 | 0,06471 | 0,04314 |
| Completa vs. Individual | 0,01141 | 0,09130 | 0,04565 |
| Homogénea vs. Individual | 0,03983 | 0,27883 | 0,15933 |

La lectura más conservadora es que GFS es la comparación más estable frente a
Individual; Top-k y Completa dependen del ajuste elegido.

---

## 12. Cómo leer el LaTeX generado

Las salidas están en:

`results/confirmatory/nonparametric/metrics_cpu/<métrica>/`

Cada carpeta contiene:

- `primary_controltest.tex`;
- `primary_multipletest.tex`;
- `sensitivity_controltest.tex`;
- `sensitivity_multipletest.tex`;
- las matrices CSV utilizadas.

En `MultipleTest`, una línea como:

```text
GFS vs. Individual ... 0.00266 ... 0.02663 ...
```

debe leerse como:

- primer valor: p sin ajustar;
- valor posterior: corrección Holm u otro ajuste, según el encabezado de la
  tabla;
- la decisión depende del ajuste y de `alpha = 0,05`.

Siempre hay que mirar el encabezado de la tabla para saber qué columna se está
leyendo.

---

## 13. Qué decirle al profesor en una explicación oral

Una explicación breve y correcta sería:

> “Usamos el protocolo de comparación de algoritmos sobre múltiples datasets
> descrito por García y Herrera y por Derrac et al. Cada estrategia es una
> columna y cada dataset un bloque. Aplicamos Friedman, Iman-Davenport,
> Friedman Aligned Ranks y Quade, y luego ControlTest y MultipleTest con
> correcciones por comparaciones múltiples. En el análisis primario de cuatro
> datasets, ninguna métrica mostró una diferencia robusta contra Individual
> después de corregir los p-valores. En la sensibilidad que separa SVM y
> ResMLP, GFS y Top-k sí mostraron diferencias frente a Individual en varias
> métricas, pero esa evidencia es secundaria porque reutiliza los mismos
> datasets.”

---

## 14. Qué no debemos decir

No conviene decir:

- “GFS es significativamente mejor en todos los casos”;
- “p > 0,05 demuestra que los métodos son iguales”;
- “Top-k es significativamente mejor” sin indicar el ajuste utilizado;
- “tenemos ocho datasets independientes”;
- “AUC/precision/recall fueron significativos en el análisis primario”;
- “los resultados CPU y GPU son idénticos”.

La ejecución SVM-GPU/cuML todavía está completándose. Después habrá que
reconstruir las matrices y repetir esta lectura con ese backend antes de
convertirla en la versión final del artículo.

---

## 15. Archivos de consulta rápida

- [Informe para el profesor](INFORME_RESULTADOS_PROFESOR.md)
- [Salidas LaTeX SCI2S](latex_sci2s/)
- [Salidas LaTeX por métrica](../../../../results/confirmatory/nonparametric/metrics_cpu/)
- [Resumen contra Individual](../../../../results/confirmatory/nonparametric/metrics_cpu/multipletest_summary_vs_individual.csv)
- [Historial del borrador](../REVISION_LOG.md)

## 16. Cómo leer cada tabla de `ControlTest`

### Tabla 1: Average Rankings of the algorithms (Friedman)

Esta tabla solo ordena las estrategias usando los rankings de Friedman.
Ranking 1 es mejor y ranking 5 peor. Después de la tabla aparece:

```text
Friedman statistic ...
P-value computed by Friedman Test: ...
```

Ese p-valor es global: si es menor que 0,05, hay evidencia de que alguna
estrategia difiere, pero todavía no sabemos cuál.

### Tablas de Aligned Friedman y Quade

Repiten la misma idea con otra forma de construir los rankings. Se mira el
ranking de cada estrategia y luego el p-valor global. No se deben mezclar los
p-valores: cada tabla responde con un procedimiento diferente.

### Tabla `Contrast Estimation`

Muestra la diferencia estimada entre cada par de estrategias. Sirve para saber
el tamaño y el sentido de la diferencia, pero no decide significación por sí
sola. La significación se decide con las tablas post-hoc y sus correcciones.

### Tabla `Holm / Hochberg / ... for alpha=0.05`

Esta es la comparación contra el control elegido por el programa. Las columnas
significan:

- `algorithm`: estrategia comparada contra el control;
- `z`: distancia estandarizada entre rankings;
- `p`: p-valor sin ajustar;
- `Holm`, `Hochberg`, etc.: umbrales ajustados para decidir en cada posición.

En estas tablas se compara el p de la fila con el umbral de la columna. Un p
menor que el umbral permite rechazar esa hipótesis. Estos números de Holm no
son p-valores ajustados; son niveles críticos.

### Tabla `Adjusted p-values`

Es la tabla más sencilla para informar. Aquí sí aparecen p-valores ajustados
directamente:

```text
unadjusted p | p_Bonf | p_Holm | p_Hoch | p_Homm
```

Se compara directamente cada columna con 0,05. Por ejemplo, `p_Holm=0,03`
significa significación bajo Holm; `p_Holm=0,20` no la significa.

### Tablas con alpha=0.10

Son un análisis menos estricto. No sustituyen la conclusión a alpha=0,05; se
pueden mencionar como sensibilidad.

## 17. Cómo leer cada tabla de `MultipleTest`

### Ranking y p global

La primera parte funciona igual que en `ControlTest`: rankings, Friedman e
Iman-Davenport. El p global solo dice si existe alguna diferencia entre las
cinco estrategias.

### `Holm / Shaffer Table`

Aquí `algorithms` contiene pares completos, por ejemplo `GFS vs. Individual`.
La columna `p` es sin ajustar. Las columnas `Holm` y `Shaffer` son umbrales
secuenciales, no p-valores ajustados.

### Lista de Bergmann

Cuando el programa escribe:

```text
Bergmann's procedure rejects these hypotheses:
```

las hipótesis que siguen son las comparaciones que Bergmann-Hommel considera
significativas al alpha indicado.

### Última tabla `Adjusted p-values`

Esta es la tabla final para leer comparaciones todos-contra-todos. Sus columnas
son p-valores ajustados:

- `p_Neme`: Nemenyi;
- `p_Holm`: Holm;
- `p_Shaf`: Shaffer;
- `p_Berg`: Bergmann-Hommel.

Para cada comparación contra Individual, se mira el valor ajustado y se lo
compara con 0,05. No se debe usar el p sin ajustar si ya se hicieron las diez
comparaciones posibles.

## 18. Qué tablas mostrar primero

Para una explicación oral no hace falta leer todo el `.tex`. Conviene mostrar,
en este orden:

1. ranking promedio;
2. p global de Friedman e Iman-Davenport;
3. p global de Aligned Ranks y Quade;
4. última tabla de p-valores ajustados de `MultipleTest`;
5. comparación GFS/Top-k/Completa/Homogénea contra Individual.

Las tablas intermedias de umbrales sirven para verificar el cálculo, pero la
última tabla de p ajustados es la más clara para comunicar la conclusión.
