# Qué probamos exactamente — traza paso a paso

**Para:** Joaquín Delgado
**Fecha de ejecución:** 2026-08-20
**Objetivo:** dejar registrado qué entró al software estadístico, qué hizo, y qué salió, sin cajas negras.

---

## PASO 0 — Qué software y de dónde salió

Dos paquetes desarrollados por el grupo SCI2S de la Universidad de Granada, que acompañan al tutorial de Derrac, García, Molina y Herrera (2011) en *Swarm and Evolutionary Computation*.

| Paquete | Archivo | Qué hace |
|---|---|---|
| CONTROLTEST | `controlTest.zip` | Comparaciones **1×n**: un método de control contra el resto |
| MULTIPLETEST | `multipleTest.zip` | Comparaciones **n×n**: todas las parejas |

Descargados de <https://sci2s.ugr.es/sicidm>. Quedaron en `.tools/nonparametric/` del repo.

**Dos aclaraciones:**

1. **No son archivos `.jar`.** Adentro traen clases Java compiladas (`.class`) junto con el código fuente (`.java`), un `instructions.pdf` y un CSV de ejemplo. Se ejecutan invocando la clase.
2. **El sitio tiene el certificado TLS vencido**, así que la descarga se hizo con la verificación desactivada. Hashes SHA-256 de lo que se bajó, para que quede constancia:

```
e99361a1504a54313efb0a276fbd619153fb6f4e4c1e1cfebe2a4e986ab929dd  controlTest.zip
d1c302b2ec4f39c23355bd8d60d1f5ca0e8d050778c809d9be2ac941cfa0ff98  multipleTest.zip
```

**Requisito:** una JVM. Verificado con **Java 17.0.12**.

---

## PASO 1 — De dónde salieron los números

**No se recalculó nada.** Los 40 valores se transcribieron de lo que ya reporta `tesis.tex`:

| Columna | Origen dentro de `tesis.tex` |
|---|---|
| GFS, Top-$k$, Completa, Individual | Panel A de la Tabla `tab:resultados-confirmatorios` |
| Homogénea | Subsección "Heterogeneidad frente a selección homogénea" |

Se hizo así a propósito: garantiza que **los tests describan exactamente las mismas cifras que el texto**, sin riesgo de que la tabla diga una cosa y el análisis estadístico otra.

> ⚠️ **Punto a revisar:** los valores de CUReT en `tesis.tex` son los del protocolo de **dos direcciones fijas** (0,9948 / 0,9991 / 0,9988). En `results/confirmatory/` están los de las **ocho biparticiones aleatorias** que corrimos en julio (0,9942 / 0,9989 / 0,9982). Si alguna vez incorporamos las ocho a la tesis, **hay que recalcular estos tests**.

---

## PASO 2 — El archivo de entrada

El software exige un CSV con la primera columna = nombre del problema, y una columna por algoritmo.

Archivo: `macro_f1_tesis_5estrategias.csv`

```
Problema,GFS,Topk,Completa,Individual,Homogenea
DTD-SVM,0.8694,0.8684,0.8648,0.8426,0.8606
DTD-ResMLP,0.8668,0.8662,0.8602,0.8373,0.8611
FMD-SVM,0.9766,0.9820,0.9644,0.9726,0.9789
FMD-ResMLP,0.9783,0.9770,0.9575,0.9690,0.9773
CUReT-SVM,0.9988,0.9989,0.9991,0.9948,0.9989
CUReT-ResMLP,0.9980,0.9970,0.9988,0.9971,0.9982
Outex-SVM,0.9426,0.9503,0.9572,0.9066,0.9308
Outex-ResMLP,0.9423,0.9419,0.9542,0.9178,0.9306
```

- **k = 5** algoritmos (las 5 estrategias)
- **N = 8** problemas (4 datasets × 2 clasificadores)
- Métrica: macro-F1 en el test externo

### Por qué 8 problemas y no 56

Se podría haber usado cada split como un problema (10 de DTD + 15 de FMD + 2 de CUReT + 1 de Outex, por dos clasificadores = 56). **Se descartó a propósito.**

Los splits de un mismo dataset reutilizan las mismas imágenes: no son observaciones independientes. Demšar (2006) y el propio Derrac desaconsejan explícitamente tratar folds de validación cruzada como problemas separados. Usar 56 habría inflado N artificialmente y producido significación falsa.

---

## PASO 3 — Los comandos

**No hay parámetros que configurar.** El software no tiene flags, ni semillas, ni opciones: se le pasa el CSV y listo. Eso lo hace 100% reproducible.

```bash
cd .tools/nonparametric/controlTest
java Friedman tesis.csv > tesis_controltest.tex

cd ../multipleTest
java Friedman tesis.csv > tesis_multipletest.tex
```

La clase se llama `Friedman` en los dos paquetes. **La salida se emite por pantalla directamente en LaTeX**, por eso se redirige a un archivo — es lo que indica el manual incluido.

---

## PASO 4 — Qué hace el software por dentro (paso intermedio)

Antes de cualquier test, convierte los valores en **rankings**: en cada problema ordena las 5 estrategias del 1° al 5°.

Lo verificamos a mano y coincide exactamente con lo que reporta el software:

| Problema | GFS | Top-$k$ | Completa | Individual | Homogénea |
|---|---|---|---|---|---|
| DTD-SVM | **1** | 2 | 3 | 5 | 4 |
| DTD-ResMLP | **1** | 2 | 4 | 5 | 3 |
| FMD-SVM | 3 | **1** | 5 | 4 | 2 |
| FMD-ResMLP | **1** | 3 | 5 | 4 | 2 |
| CUReT-SVM | 4 | 2,5 | **1** | 5 | 2,5 |
| CUReT-ResMLP | 3 | 5 | **1** | 4 | 2 |
| Outex-SVM | 3 | 2 | **1** | 5 | 4 |
| Outex-ResMLP | 2 | 3 | **1** | 5 | 4 |
| **PROMEDIO** | **2,2500** | 2,5625 | 2,6250 | 4,6250 | 2,9375 |

*En CUReT-SVM, Top-$k$ y Homogénea empatan en 0,9989, así que se reparten los puestos 2 y 3: 2,5 cada una.*

**Dos controles de sanidad que pasan:**
- Los promedios coinciden con la salida del software al cuarto decimal.
- La suma de los promedios da **15,0**, que es exactamente $k(k+1)/2 = 5 \cdot 6/2$. Si no diera 15, habría un error de cálculo.

**Lo que ya se ve acá:** Individual sale 5° en seis de los ocho problemas y **nunca gana ninguno**. Completa gana cuatro, GFS tres, Top-$k$ uno.

---

## PASO 5 — Salida, primera parte: los tests omnibus

Pregunta: *¿las 5 estrategias son todas iguales, o al menos una se diferencia?*

| Test | Estadístico | p-valor | ¿Rechaza a α=0,05? |
|---|---|---|---|
| Friedman | χ²(4) = 11,325 | **0,0231** | Sí |
| Iman–Davenport | F(4,28) = 3,834 | **0,0132** | Sí |
| Friedman Aligned Ranks | χ²(4) = 6,515 | 0,1639 | No |
| Quade | F(4,28) = 4,372 | **0,0072** | Sí |

**Tres de cuatro rechazan.** Los cuatro se reportan sin maquillar; no se eligió el más favorable.

Los tres primeros rankean distinto (Friedman por puesto dentro de cada problema, Quade ponderando los problemas donde más se nota la diferencia, Aligned comparando entre problemas), y por eso pueden no coincidir. Iman–Davenport no es un ranking nuevo: es Friedman corregido, porque se sabe que Friedman es conservador de más.

Como la mayoría rechaza, se habilita el segundo paso.

---

## PASO 6 — Salida, segunda parte: post-hoc

### 6a) CONTROLTEST — GFS contra cada una (4 comparaciones)

El software elige el control automáticamente: el mejor rankeado, o sea GFS.

| Comparación | p crudo | p ajustado (Holm/Hochberg/Hommel/Bonferroni) |
|---|---|---|
| **GFS vs Individual** | 0,0027 | **0,011** ✅ |
| GFS vs Homogénea | 0,3845 | 0,693 |
| GFS vs Completa | 0,6353 | 0,693 |
| GFS vs Top-$k$ | 0,6926 | 0,693 |

### 6b) MULTIPLETEST — todas las parejas (10 comparaciones)

| Comparación | p crudo | p ajustado (Bergmann–Hommel) |
|---|---|---|
| **GFS vs Individual** | 0,0027 | **0,027** ✅ |
| Top-$k$ vs Individual | 0,0091 | 0,055 |
| Completa vs Individual | 0,0114 | 0,055 |
| Individual vs Homogénea | 0,0328 | 0,131 |
| GFS vs Homogénea | 0,3845 | >1 |
| GFS vs Completa | 0,6353 | >1 |
| Top-$k$ vs Homogénea | 0,6353 | >1 |
| GFS vs Top-$k$ | 0,6926 | >1 |
| Completa vs Homogénea | 0,6926 | >1 |
| Top-$k$ vs Completa | 0,9370 | >1 |

### Por qué el mismo par da 0,011 y 0,027

Es la misma comparación con el **mismo p crudo (0,0027)**. La diferencia es cuántas comparaciones se hacen en total: CONTROLTEST hace 4, MULTIPLETEST hace 10. Cuantas más preguntas hacés, más chance de un falso positivo, así que el ajuste es más severo.

---

## PASO 7 — Cómo se leyó todo esto

**El patrón salta a la vista en la tabla 6b:** las cuatro comparaciones de arriba son todas *"alguien vs Individual"*, y son las únicas que se acercan a significativas. Las seis de abajo son *"combinada vs combinada"*, y ninguna da nada.

Es decir, las estrategias se parten en dos grupos:

- **Las que combinan** (GFS, Top-$k$, Completa, Homogénea) → indistinguibles entre sí
- **Usar un descriptor solo** (Individual) → claramente por debajo

### Lo que se puede afirmar

> **Combinar descriptores mejora significativamente sobre usar el mejor descriptor individual.**

### Lo que NO se puede afirmar

> ~~GFS es mejor que Top-$k$, que Completa o que Homogénea.~~

No hay evidencia. El contraste GFS − Top-$k$ es de **+0,0002 de macro-F1** — dos diezmilésimas.

**Esto concuerda con lo que la tesis ya sostiene:** *"una parte sustancial de la mejora se recupera reuniendo pocos bloques individualmente fuertes"*, y con el reparto de 26 victorias por estrategia. El test no contradijo nada: dio el respaldo formal a una lectura que ya era prudente.

---

## PASO 8 — Dos advertencias honestas

**1. "No significativo" ≠ "son iguales".** Con N=8 la potencia es baja. Que no se detecte diferencia entre GFS y Completa no prueba que sean equivalentes; prueba que este estudio no alcanza para distinguirlas. Por eso la interpretación de las diferencias chicas sigue apoyándose en el **margen práctico de 0,01**, no en los p-valores.

**2. El 0,055 es elocuente.** Top-$k$ y Completa contra Individual quedan apenas afuera del corte. Con 10 o 12 datasets probablemente habrían entrado. No es que esas estrategias no funcionen: es que **cuatro datasets no alcanzan** para demostrarlo. Conviene decirlo antes de que lo pregunten.

El propio tutorial fija como regla práctica $n = a \cdot k$ con $a \geq 2$, o sea $n \geq 10$ para nuestros 5 algoritmos. Tenemos 8. En cambio **sí cumplimos el requisito duro** que ellos marcan como obligatorio: *"the number of algorithms must be lower than the number of case problems"* (5 < 8).

---

## Archivos para revisar

| Archivo | Contenido |
|---|---|
| `macro_f1_tesis_5estrategias.csv` | La entrada exacta |
| `tesis_controltest.tex` | Salida cruda de CONTROLTEST, sin editar |
| `tesis_multipletest.tex` | Salida cruda de MULTIPLETEST, sin editar |
| `INFORME_ENTRADA_SALIDA_SOFTWARE.md` | Todas las tablas de salida transcritas |
| `REPORTE_TESTS_NO_PARAMETRICOS.md` | La interpretación y qué respalda del manuscrito |

En `tesis.tex` esto quedó como la subsección **"Comparación múltiple entre estrategias"**, dentro del análisis estadístico.

**Falta hacer en Overleaf:** agregar al `references.bib` las claves `derrac2011nonparametric`, `demsar2006statistical` y `garcia2008extension`, que la sección nueva cita.
