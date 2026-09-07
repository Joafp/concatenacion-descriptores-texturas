# Auditoría del análisis no paramétrico del artículo

**Fecha:** 2026-08-21  
**Objeto:** reconstrucción desde tablas canónicas y comparación con
`paper/articulo/REPORTE_TESTS_NO_PARAMETRICOS.md`.

## Fuentes y ejecución

Las matrices se generan con `scripts/build_nonparametric_analysis.py` desde:

- `results/confirmatory/nested_summary.csv`;
- `results/confirmatory/topk_individual_control/nested_fold_results.csv`;
- `results/confirmatory/family_ablation.csv` (integrada en `nested_summary.csv`);
- `results/extensions/outex13_official1360/nested_summary.csv`;
- `results/extensions/outex13_official1360/topk_individual_control/nested_fold_results.csv`.

Se ejecutaron las copias oficiales de SCI2S descargadas el 2026-08-21. El sitio
tenía el certificado TLS vencido; la autenticidad se comprobó contra los hashes
que ya estaban declarados en el reporte previo:

```text
e99361a1504a54313efb0a276fbd619153fb6f4e4c1e1cfebe2a4e986ab929dd  controlTest.zip
d1c302b2ec4f39c23355bd8d60d1f5ca0e8d050778c809d9be2ac941cfa0ff98  multipleTest.zip
```

## Diseño vigente

Se comparan cinco estrategias: GFS, top-k, concatenación completa, mejor
descriptor individual y mejor selección homogénea.

1. **Análisis primario:** cuatro bloques independientes, uno por dataset. El
   valor de cada celda es la media de los dos clasificadores preespecificados.
2. **Sensibilidad:** ocho bloques dataset-clasificador. Este análisis duplica
   cada dataset y no satisface independencia entre bloques; se conserva solo
   para mostrar cuánto cambia el resultado bajo esa decisión.

## Resultados reproducidos

| Prueba | Primario (4 datasets) | Sensibilidad (8 dataset-clasificador) |
|---|---:|---:|
| Friedman | chi-cuadrado(4)=6,600; p=0,1586 | chi-cuadrado(4)=11,500; p=0,02148 |
| Iman-Davenport | F(4,12)=2,106; p=0,1429 | F(4,28)=3,927; p=0,01183 |
| Friedman Aligned Ranks | chi-cuadrado(4)=3,237; p=0,5190 | chi-cuadrado(4)=6,514; p=0,1639 |
| Quade | F(4,12)=2,233; p=0,1264 | F(4,28)=4,454; p=0,006535 |
| Kendall W (Friedman) | 0,4125 | 0,3594 |

En el análisis primario ninguna comparación por pares es significativa a
alpha=0,05. En MULTIPLETEST, los menores p sin ajustar corresponden a top-k
frente a individual (0,02535) y GFS frente a individual (0,04417); después de
Holm son 0,25347 y 0,39754, respectivamente. Bergmann-Hommel tampoco rechaza
ninguna hipótesis.

En la sensibilidad, el contraste 1xn con GFS como control frente al individual
da p ajustado de Holm 0,01065. En el análisis nxn, Holm conserva únicamente
GFS frente a individual (p ajustado 0,02663), mientras Bergmann-Hommel también
rechaza top-k frente a individual (0,04314) y completa frente a individual
(0,04565). Estos resultados no reciben autoridad confirmatoria por la
dependencia entre los dos bloques que comparten cada dataset.

## Diferencias frente al reporte previo

El reporte previo no reproduce exactamente las tablas canónicas actuales:

| Elemento | Reporte previo | Reconstrucción vigente |
|---|---:|---:|
| Friedman, sensibilidad | 11,325; p=0,0231 | 11,500; p=0,02148 |
| Iman-Davenport, sensibilidad | 3,834; p=0,0132 | 3,927; p=0,01183 |
| Quade, sensibilidad | 4,372; p=0,0072 | 4,454; p=0,006535 |
| Ranking top-k | 2,563 | 2,500 |
| Ranking homogénea | 2,938 | 3,000 |
| Bergmann-Hommel a 0,05 | solo GFS-individual | GFS, top-k y completa frente a individual |

La diferencia no proviene de redondeo del programa: las entradas anteriores no
están en el repositorio y los valores de ranking muestran que se usó una matriz
distinta. Por ello, `REPORTE_TESTS_NO_PARAMETRICOS.md` queda como documento
histórico y no debe citarse como resultado vigente.

## Conclusión metodológica

La conclusión confirmatoria es que, con cuatro datasets, no se detectan
diferencias globales ni por pares entre las cinco estrategias. El patrón
descriptivo sigue siendo informativo: las estrategias combinadas aventajan al
individual en varios dominios y GFS no muestra una ventaja estable sobre top-k
o la concatenación completa. La sensibilidad n=8 refuerza ese patrón, pero no
puede sustituir evidencia entre datasets independientes.
