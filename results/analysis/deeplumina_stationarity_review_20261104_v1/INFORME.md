# Diagnóstico de optimización DeepLumina — 04-11-2026

Se inspeccionaron **46 modelos ECOC guardados**, sus **2.441 clasificadores
binarios** y los rasgos de entrenamiento ya extraídos. Se verificaron recibos,
hashes de los modelos, rasgos, código, particiones y manifiestos. No se ajustó
ningún clasificador, no se extrajeron rasgos, no se evaluó test y no se repitió
ninguna corrida. DTD `s42_f3` conserva su estado `requires_review`: agotó el
tiempo de entrenamiento y no dejó un modelo terminado que inspeccionar.

Para cada clasificador se calculó la norma del gradiente del objetivo primal
L2 con pérdida squared-hinge y sesgo regularizado, dividida por la norma del
gradiente en el origen. La formulación corresponde a la documentación primaria
de [LIBLINEAR](https://github.com/cjlin1/liblinear/blob/master/README) y a su
[tratamiento del sesgo](https://www.csie.ntu.edu.tw/~cjlin/liblinear/FAQ_src.html).
El código exige la configuración guardada `C=1`, `penalty=l2`,
`loss=squared_hinge`, `dual=True`, `intercept_scaling=1` y sin pesos de clase.
Las derivadas se verificaron con diferencias finitas en datos sintéticos
incluyendo filas ECOC ignoradas y sesgo: **2/2 pruebas aprobadas**.

| Dataset | Binarios con `max_iter` | Binarios sin llegar al límite | Mediana de razón de gradiente con límite | Mediana sin límite |
|---|---:|---:|---:|---:|
| FMD | 41 | 649 | 4,59e−5 | 5,32e−6 |
| CUReT | 178 | 0 | 7,15e−2 | — |
| Outex-13 | 92 | 0 | 2,56e−2 | — |
| Soil | 423 | 102 | 1,87e−3 | 9,59e−6 |
| KTH-TIPS2b | 166 | 34 | 2,66e−4 | 6,31e−7 |
| DTD (9/10) | 753 | 3 | 5,89e−3 | 4,11e−7 |

Las medianas describen los clasificadores guardados, no muestras independientes
para una prueba estadística. La razón **no es el criterio dual de parada de
Liblinear**, no se compara con `tol` como si fuera equivalente y no estima el
cambio que produciría otra solución en las predicciones o en el F1. En DTD hay
solo tres clasificadores en la columna sin límite. La evidencia refuerza la
necesidad de revisión; no autoriza automáticamente un reintento, aumentar
iteraciones, relajar tolerancias, cambiar el solver o elegir resultados.

Los 1.653 clasificadores que alcanzaron 10.000 iteraciones concuerdan por
condición con los avisos de no convergencia registrados en los logs. En CUReT y
Outex todos los clasificadores inspeccionados llegaron al límite. El estado
científico de las adaptaciones DeepLumina sigue siendo **requiere revisión**;
las llamadas existentes se conservan con sus métricas observadas y reservas.

Artefactos: `summary.json`, `conditions.csv`, `learners.csv` (una fila por
clasificador) y `provenance.json`. Los CSV no contienen predicciones nuevas.
