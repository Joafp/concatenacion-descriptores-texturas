# Tests no paramétricos — comparación múltiple de las cinco estrategias

**Fecha:** 2026-08-20
**Software:** CONTROLTEST y MULTIPLETEST (SCI2S, Universidad de Granada)
**Metodología:** Derrac, García, Molina, Herrera (2011), *Swarm and Evolutionary Computation* 1(1):3–18
**Destino:** sección `\subsubsection{Comparación múltiple entre estrategias}` de `paper/tesis.tex`

---

## 1. Diseño del análisis

**k = 5 algoritmos** (las estrategias comparadas en `tesis.tex`):

| Etiqueta | Estrategia |
|---|---|
| `GFS` | Greedy Forward Selection |
| `Topk` | Control top-$k$ individual |
| `Completa` | Concatenación de los 20 extractores |
| `Individual` | Mejor descriptor individual |
| `Homogenea` | Mejor selección restringida a una familia |

**N = 8 problemas** (cada configuración dataset–clasificador):
DTD-SVM, DTD-ResMLP, FMD-SVM, FMD-ResMLP, CUReT-SVM, CUReT-ResMLP, Outex-SVM, Outex-ResMLP.

**Métrica:** macro-F1 en el test externo.

### Origen de los valores

Los 40 valores provienen de lo que la propia `tesis.tex` reporta: el Panel A de la Tabla 3 (`tab:resultados-confirmatorios`) para cuatro estrategias, y la subsección "Heterogeneidad frente a selección homogénea" para la quinta. Esto garantiza que los tests sean **consistentes con las tablas del mismo documento**.

> **Advertencia de consistencia.** Los valores de CUReT en `tesis.tex` corresponden al protocolo de dos direcciones fijas (0,9948 / 0,9991 / 0,9988). El directorio `results/confirmatory/` contiene, en cambio, los de las ocho biparticiones aleatorias corridas en julio (0,9942 / 0,9989 / 0,9982). Si en algún momento se incorporan esas ocho biparticiones a la tesis, **estos tests deben recalcularse**.

### Por qué N = 8 y no N = 56

Se consideró usar cada split externo como un problema separado (10 de DTD, 15 de FMD, 2 de CUReT, 1 de Outex, por dos clasificadores = 56). **Se descartó deliberadamente.** Los splits de un mismo dataset reutilizan las mismas imágenes y no son observaciones independientes; Demšar (2006) y Derrac et al. (2011) desaconsejan explícitamente tratar particiones de validación cruzada como problemas separados. Hacerlo inflaría artificialmente N y produciría significación espuria.

---

## 2. Rankings medios

Menor es mejor.

| Estrategia | Friedman | Friedman Aligned | Quade |
|---|---|---|---|
| **GFS** | **2,250** | 14,000 | **2,028** |
| Top-$k$ | 2,563 | **12,563** | 2,333 |
| Completa | 2,625 | 18,625 | 2,556 |
| Homogénea | 2,938 | 22,938 | 3,306 |
| Individual | 4,625 | 34,375 | 4,778 |

GFS encabeza Friedman y Quade; top-$k$ encabeza Aligned Ranks. Individual queda último en los tres, con amplio margen.

---

## 3. Tests omnibus (¿hay alguna diferencia entre las cinco?)

| Test | Estadístico | p-valor | ¿Rechaza H₀ a α=0,05? |
|---|---|---|---|
| Friedman | χ²(4) = 11,325 | **0,0231** | Sí |
| Iman–Davenport | F(4,28) = 3,834 | **0,0132** | Sí |
| Friedman Aligned Ranks | χ²(4) = 6,515 | 0,1639 | No |
| Quade | F(4,28) = 4,372 | **0,0072** | Sí |

### Los tests no coinciden: cómo leerlo honestamente

Tres de cuatro rechazan; Aligned Ranks no. Esta discrepancia hay que reportarla, no elegir el resultado que conviene.

- **Iman–Davenport** deriva del estadístico de Friedman corrigiendo su efecto conservador; es su acompañante estándar.
- **Aligned Ranks** y **Quade** son los que el tutorial *recomienda cuando el número de algoritmos es bajo*, y dan resultados opuestos entre sí.
- El tutorial advierte que **Quade "debe usarse con especial cautela"** porque es muy sensible a la elección de problemas: si se incluye un subgrupo donde la propuesta ya rendía bien, reporta diferencias significativas en exceso. Su p = 0,0072 no debe leerse aisladamente.
- El tutorial fija una regla práctica para la validez de la aproximación χ²: **n > 10 y k > 5**. Nuestro caso (n = 8, k = 5) queda por debajo en ambos ejes.

**Lectura conservadora:** hay evidencia de diferencias entre las estrategias, pero el poder es limitado por N = 8. Lo verdaderamente informativo es el post-hoc, que sí es consistente entre procedimientos.

---

## 4. Post-hoc 1×n — GFS como método de control

Control = GFS (mejor rankeado). El tutorial desaconseja Bonferroni–Dunn por conservador y recomienda Holm junto con Hochberg.

| Comparación | p sin ajustar | Bonferroni | Holm | Hochberg | Hommel | Finner | Li |
|---|---|---|---|---|---|---|---|
| **GFS vs Individual** | **0,00266** | **0,0107** | **0,0107** | **0,0107** | **0,0107** | **0,0106** | **0,0086** |
| GFS vs Homogénea | 0,3845 | 1,538 | 1,154 | 0,693 | 0,693 | 0,621 | 0,556 |
| GFS vs Completa | 0,6353 | 2,541 | 1,271 | 0,693 | 0,693 | 0,739 | 0,674 |
| GFS vs Top-$k$ | 0,6926 | 2,771 | 1,271 | 0,693 | 0,693 | 0,739 | 0,693 |

**GFS supera significativamente al mejor descriptor individual** (p ajustado ≈ 0,011 en todos los procedimientos, incluido el conservador Bonferroni). Las diferencias frente a top-$k$, concatenación completa y selección homogénea **no son significativas**.

### Estimación de contraste (diferencias medias de macro-F1)

| Comparación | Diferencia |
|---|---|
| GFS − Individual | +0,0161 |
| GFS − Homogénea | +0,0040 |
| GFS − Completa | +0,0026 |
| GFS − Top-$k$ | **+0,0002** |

La diferencia frente a top-$k$ es de dos diezmilésimas: numéricamente despreciable, y sin respaldo estadístico.

---

## 5. Post-hoc n×n — todas las comparaciones por pares

| Comparación | p sin ajustar | α=0,05 | α=0,10 |
|---|---|---|---|
| **GFS vs Individual** | **0,0027** | **Rechazada** | **Rechazada** |
| Top-$k$ vs Individual | 0,0091 | No | **Rechazada** |
| Completa vs Individual | 0,0114 | No | **Rechazada** |
| Individual vs Homogénea | 0,0328 | No | No |
| GFS vs Homogénea | 0,3845 | No | No |
| GFS vs Completa | 0,6353 | No | No |
| Top-$k$ vs Homogénea | 0,6353 | No | No |
| GFS vs Top-$k$ | 0,6926 | No | No |
| Completa vs Homogénea | 0,6926 | No | No |
| Top-$k$ vs Completa | 0,9370 | No | No |

A α=0,05, el procedimiento de **Bergmann–Hommel** (el más potente de los n×n) rechaza **una sola hipótesis: GFS vs Individual**.

A α=0,10 se suman top-$k$ y Completa frente a Individual. **Ninguna comparación entre estrategias combinadas alcanza significación en ningún nivel.**

---

## 6. Qué respalda y qué no respalda el manuscrito

### Respalda

1. **Combinar bloques mejora sobre el descriptor individual.** Es el resultado significativo, consistente en los dos análisis (1×n y n×n) y bajo todos los procedimientos de ajuste. A α=0,10 el efecto aparece con las tres estrategias combinadas, no solo con GFS: no depende del método de composición.
2. **GFS es la estrategia mejor rankeada** en Friedman y Quade.
3. **GFS no supera a top-$k$.** El contraste es de +0,0002 y p = 0,693. Esto respalda estadísticamente la afirmación más honesta de la tesis: *"una parte sustancial de la mejora se recupera reuniendo pocos bloques individualmente fuertes"*, y concuerda con el reparto de 26 victorias por estrategia.
4. **La heterogeneidad no es universalmente superior:** GFS frente a la mejor familia homogénea da p = 0,385.

### No respalda

- No permite afirmar que GFS **supere** a la concatenación completa, a top-$k$ ni a la selección homogénea. El manuscrito ya evita esas afirmaciones.
- Con N = 8 el poder es bajo: la ausencia de significación **no es evidencia de igualdad**. Por eso la interpretación de las diferencias pequeñas debe seguir apoyándose en el **margen práctico predefinido de 0,01**, no en la falta de significancia.

---

## 7. Limitación principal, dicha con claridad

**El estudio tiene cuatro datasets.** De ahí que N = 8 aun contando ambos clasificadores. El propio tutorial señala n > 10 como regla práctica. Ninguna elección de test arregla eso: es una limitación de diseño, no de análisis. Conviene declararlo antes de que lo señale un revisor.

---

## 8. Reproducir este análisis

```bash
# 1 x n (control = mejor rankeado)
cd .tools/nonparametric/controlTest
java Friedman tesis.csv > ../../../results/confirmatory/nonparametric/tesis_controltest.tex

# n x n (todas las comparaciones por pares)
cd ../multipleTest
java Friedman tesis.csv > ../../../results/confirmatory/nonparametric/tesis_multipletest.tex
```

Requiere una JVM instalada (verificado con Java 17). El software se descargó de
<https://sci2s.ugr.es/sicidm> — **nota:** ese sitio tiene el certificado TLS vencido, por lo que
la descarga se hizo con verificación desactivada. Hashes SHA-256 de lo descargado:

```
e99361a1504a54313efb0a276fbd619153fb6f4e4c1e1cfebe2a4e986ab929dd  controlTest.zip
d1c302b2ec4f39c23355bd8d60d1f5ca0e8d050778c809d9be2ac941cfa0ff98  multipleTest.zip
```

### Archivos

| Archivo | Contenido |
|---|---|
| `macro_f1_tesis_5estrategias.csv` | **Entrada del análisis vigente**: 5 estrategias × 8 problemas |
| `tesis_controltest.tex` | Salida cruda de CONTROLTEST |
| `tesis_multipletest.tex` | Salida cruda de MULTIPLETEST |
| `macro_f1_por_condicion.csv` | Entrada de un análisis previo (4 estrategias × 6 problemas, datos del artículo `borrador_profesor/main.tex`) |
| `controltest_salida.tex`, `multipletest_salida.tex` | Salidas de ese análisis previo |

> Los cuatro últimos archivos corresponden al artículo, que no incluye Outex ni top-$k$. Se conservan por trazabilidad; **el análisis que se reporta en `tesis.tex` es el de 5 estrategias × 8 problemas.**

---

## 9. Referencias a citar

Las tres primeras ya se agregaron a `paper/references/references.bib` con las claves indicadas:

- `derrac2011nonparametric` — Derrac, J., García, S., Molina, D., Herrera, F. (2011). A practical tutorial on the use of nonparametric statistical tests as a methodology for comparing evolutionary and swarm intelligence algorithms. *Swarm and Evolutionary Computation*, 1(1), 3–18.
- `demsar2006statistical` — Demšar, J. (2006). Statistical comparisons of classifiers over multiple data sets. *JMLR*, 7, 1–30.
- `garcia2008extension` — García, S., Herrera, F. (2008). An extension on "Statistical comparisons of classifiers over multiple data sets" for all pairwise comparisons. *JMLR*, 9, 2677–2694.
- García, S., Fernández, A., Luengo, J., Herrera, F. (2010). Advanced nonparametric tests for multiple comparisons in the design of experiments in computational intelligence and data mining. *Information Sciences*, 180, 2044–2064. *(No citada en el texto; es la referencia del paquete CONTROLTEST.)*
