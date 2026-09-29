# Corrección: el agrupamiento de la validación interna en KTH-TIPS2-b

**Para:** Joaquín Delgado
**De:** Carlos Ayala
**Fecha:** 26 de septiembre de 2026
**Estado:** propuesta, pendiente de re-corrida sobre la biblioteca del manuscrito

---

## Resumen

En KTH-TIPS2-b la validación interna que usa GFS **no replica la estructura de
dependencia del protocolo externo**. El externo deja afuera una muestra física
completa; el interno reparte imágenes al azar dentro de las muestras de
entrenamiento. La tarea interna resulta mucho más fácil, el criterio satura
cerca de 1,0 y pierde capacidad de discriminar entre candidatos.

Medido: **12 de 16 pasos de GFS tienen mejora exactamente 0,0** y entre 14 y 16
de los 22 bloques quedan dentro de una centésima del máximo interno. GFS está
eligiendo con muy poca información y por eso se detiene en `k`=1 o 2.

Verifiqué los seis datasets: **KTH-TIPS2-b es el único afectado.** El error
viene de cómo construí ese manifiesto.

Implementé la corrección como un parámetro opcional y la probé localmente:
la saturación desaparece por completo (**0 pasos ciegos de 41**) y la selección
mejora. **El contraste GFS vs Individual —nuestro único resultado
significativo— se refuerza.**

Necesito que la re-corras sobre la biblioteca real del manuscrito, porque la
mía no es la misma.

---

## 1. El problema

El protocolo externo de KTH-TIPS2-b (RADAM, tres muestras entrenan y una
testea) evalúa **generalización entre muestras físicas**.

Pero `inner_score` agrupa los folds internos con la columna `group` del
manifiesto, y en `KTHTIPS2b.csv` esa columna es el **SHA-256 de cada imagen**:
4.752 filas, 4.752 grupos. Con grupos unitarios la restricción de
`StratifiedGroupKFold` es vacua y el corte interno queda aleatorio
estratificado *dentro* de las muestras de entrenamiento.

Consecuencia: imágenes de la misma muestra física caen a ambos lados del corte
interno. **La tarea interna es intra-muestra; la externa es entre-muestras.**

### Evidencia

Criterio interno del mejor bloque individual y comportamiento de GFS:

| Clasificador | F1 interno medio | k medio | Pasos con mejora 0,0 |
|---|---:|---:|---:|
| SVM | 0,9998 | 1,25 | **7 de 8** |
| ResMLP | 0,9997 | 1,75 | **5 de 8** |

Bloques dentro de una tolerancia del máximo interno (SVM, por partición):

| Partición | ≤0,001 | ≤0,01 |
|---|---:|---:|
| 1 | 6 | **15 de 22** |
| 2 | 5 | **15 de 22** |
| 3 | 4 | **14 de 22** |
| 4 | 7 | **16 de 22** |

A esa escala, una diferencia de 1e-4 equivale a una sola muestra cambiando de
lado: es ruido. Y el orden que produce el criterio **no coincide con el
externo**. Ejemplo de la partición 4:

```
vit_b16     inner 1,000000    externo 0,8674   <- elegido (máximo interno)
dinov2      inner 0,999439    externo 0,9372
```

El criterio los ordena al revés de como se comportan afuera.

## 2. Alcance: solo KTH

| Dataset | Grupo interno | Partición externa | ¿Coinciden? |
|---|---|---|---|
| CUReT | condición (92) | mitades de condiciones | sí |
| Soil | familia de nombre (962) | folds agrupados | sí |
| FMD, VisTex | por imagen | folds por imagen | sí |
| DTD, Outex | por imagen | split oficial por imagen | sí |
| **KTH-TIPS2-b** | **por imagen (4.752)** | **por muestra física** | **no** |

En los otros cinco el agrupamiento interno replica al externo. No hay que
tocarlos.

## 3. La corrección

`src/run_confirmatory_nested.py` acepta ahora `--inner-group-column`, que
desacopla:

- el grupo del **chequeo de fuga externo** → sigue siendo `group` (SHA por imagen)
- el grupo de la **CV interna** → pasa a ser la columna indicada

El manifiesto ya trae la columna `sample` (letra a/b/c/d de la muestra
física), así que no hay que regenerarlo.

**Es retrocompatible.** Sin la bandera el comportamiento es idéntico al
actual; las claves de checkpoint solo cambian cuando se usa. Los 35 tests de
`experiments/` siguen pasando (los 2 que fallan son los de VisTex por imágenes
ausentes, preexistente).

Cambio adicional: `inner_score` ahora limita `n_splits` al número de grupos
disponibles. Bajo RADAM el entrenamiento externo tiene 3 muestras, así que el
diseño interno natural es dejar-una-muestra-afuera (3 folds). Con
agrupamientos por fila el tope nunca se activa.

## 4. Resultados locales

### Diagnóstico

| Clasificador | Agrupamiento | F1 interno | k medio | Pasos ciegos |
|---|---|---:|---:|---:|
| SVM | imagen | 0,9998 | 1,25 | 7 de 8 |
| SVM | **muestra** | 0,9272 | 5,75 | **0 de 22** |
| ResMLP | imagen | 0,9997 | 1,75 | 5 de 8 |
| ResMLP | **muestra** | 0,9296 | 4,25 | **0 de 19** |

### Efecto externo (macro-F1 medio sobre 4 particiones)

| Clasificador | Estrategia | Original | Corregido | Δ |
|---|---|---:|---:|---:|
| SVM | Individual | 0,9177 | 0,9303 | +0,0126 |
| SVM | **GFS** | 0,9213 | **0,9425** | **+0,0212** |
| SVM | Homogénea | 0,9213 | 0,9223 | +0,0010 |
| SVM | Completa | 0,9473 | 0,9473 | **0,0000** |
| ResMLP | Individual | 0,9082 | 0,9188 | +0,0106 |
| ResMLP | **GFS** | 0,9190 | **0,9335** | **+0,0146** |
| ResMLP | Homogénea | 0,9359 | 0,9177 | −0,0181 |
| ResMLP | Completa | 0,9446 | 0,9446 | **0,0000** |

Completa no se mueve en ninguno de los dos, que es el control esperado: no usa
selección.

### Contrastes clave

| Contraste | | Original | Corregido |
|---|---|---|---|
| **GFS vs Individual** | SVM | +0,0036 (1/4) | **+0,0122 (3/4)** |
| | ResMLP | +0,0108 (1/4) | **+0,0148 (3/4)** |
| GFS vs Completa | SVM | −0,0260 (1/4) | −0,0048 (1/4) |
| | ResMLP | −0,0256 (0/4) | −0,0111 (1/4) |
| Completa vs Individual | SVM | +0,0296 (3/4) | +0,0170 (4/4) |
| | ResMLP | +0,0364 (4/4) | +0,0258 (4/4) |

Lo que hoy afirma el manuscrito sobre KTH (Completa supera a GFS) **se
mantiene pero mucho más débil**: la brecha cae 80% con SVM y 57% con ResMLP.

---

## 5. Qué hay que correr

> **Nota:** los resultados de arriba salieron de mi biblioteca local, que tiene
> `beitv2_base` + `swinv2_base`. El manuscrito usa `rgb_ngram_svd` +
> `beitv2_base_final`. **Los números exactos no son transferibles**; hay que
> re-correr sobre la biblioteca real.

### Paso 1 — Re-correr KTH con el agrupamiento corregido

Mismo comando que la corrida del manuscrito, agregando `--inner-group-column
sample` y escribiendo a una carpeta separada para no pisar lo existente:

```bash
OUT=results/extensions/kth_tips2b/inner_group_sample_paper
mkdir -p "$OUT/sample_manifests"
cp results/extensions/kth_tips2b/data_audit.csv "$OUT/data_audit.csv"
cp results/extensions/kth_tips2b/sample_manifests/KTHTIPS2b.csv \
   "$OUT/sample_manifests/KTHTIPS2b.csv"

for clf in svm resmlp; do
  for split in 1 2 3 4; do
    .venv-confirmatory/bin/python src/run_confirmatory_nested.py \
      --dataset KTHTIPS2b --classifier "$clf" --seed 42 --fold 0 \
      --official-split "$split" --invert-official-split \
      --inner-group-column sample \
      --include-rgb-ngram \
      --exclude-extractors beitv2_base swinv2_base \
      --embedding-root embeddings_extensions \
      --output "$OUT" --max-k 8 --random-b 100 --n-jobs 3
  done
done
```

Ajustá `--exclude-extractors` según qué bloques tenga tu
`embeddings_extensions/KTH-TIPS2-b/`: la idea es reproducir exactamente la
biblioteca de 22 del manuscrito.

### Paso 2 — Comparar contra la corrida actual

```bash
.venv-confirmatory/bin/python src/report_inner_grouping_fix.py \
  --original  results/extensions/kth_tips2b/ngram22_beitv2 \
  --corrected results/extensions/kth_tips2b/inner_group_sample_paper
```

Imprime el diagnóstico (F1 interno, k, pasos ciegos), el efecto por estrategia
y los contrastes clave, y deja el JSON/CSV en
`results/analysis/inner_grouping/`.

### Paso 3 — Verificar que el diagnóstico se reproduce

```bash
.venv-confirmatory/bin/python src/check_tie_breaking.py \
  --dataset KTHTIPS2b --classifier svm \
  --official-splits 1 2 3 4 --invert-official-split \
  --embedding-dir embeddings_extensions/KTH-TIPS2-b \
  --results-root results/extensions/kth_tips2b
```

Debería mostrar 14-16 bloques de 22 dentro de 0,01 del máximo interno con el
agrupamiento actual.

### Qué esperar

1. F1 interno baja de ~0,9998 a ~0,93
2. Los pasos con mejora 0,0 desaparecen
3. `k` sube de 1-2 a 4-8
4. Completa **no cambia** (control de sanidad: si cambia, algo está mal)
5. GFS e Individual mejoran

---

## 6. La decisión que queda

Si el efecto se reproduce sobre la biblioteca del manuscrito, hay que definir:

**(a) Corregir.** Regenerar los resultados de KTH y rehacer el análisis
estadístico (KTH es 1 de 6 bloques en Friedman). Es lo mínimo honesto: los
números actuales salen de una validación interna que mide otra tarea.

**(b) Corregir y reportarlo.** Además, documentar la lección general —*el
agrupamiento de la validación interna debe replicar la estructura de
dependencia del protocolo externo*— con KTH como caso de estudio y el tamaño
del conjunto efectivamente empatado como diagnóstico reutilizable.

Mi voto es (b): ya verificamos que en los otros cinco datasets el agrupamiento
coincide, así que el hallazgo es verificable y acotado, no un descuido aislado.
Y ninguno de los trabajos relacionados que revisamos (Puig 2010, Khan 2015,
Ataky 2023, Chang 2024, Neshov 2025, HyTexNet 2026) verifica si su criterio de
selección conserva poder de discriminación.

---

## 7. Salvedades

- 4 particiones por clasificador: **ningún contraste estadístico es
  interpretable** a este tamaño. Los números son descriptivos.
- La corrección **no beneficia a todo por igual**: Homogénea empeora con
  ResMLP (−0,0181).
- No da vuelta la conclusión del manuscrito sobre KTH, solo la debilita.
- Biblioteca local ≠ biblioteca del manuscrito (ver nota del punto 5).

## 8. Archivos

**Código**
- `src/run_confirmatory_nested.py` — parámetro `--inner-group-column`,
  `manifest_groups()`, tope de `n_splits` en `inner_score`
- `src/report_inner_grouping_fix.py` — comparación original vs corregido
- `src/check_tie_breaking.py` — tamaño del conjunto empatado
- `src/analyze_selection_saturation.py` — relación margen interno ↔ k elegido
- `src/analyze_oracle_gap.py` / `src/report_oracle_gap.py` — enumeración
  exhaustiva para k pequeño y brecha contra el óptimo (**cota superior
  calculada sobre el test externo: no es un resultado alcanzable**)

**Resultados**
- `results/extensions/kth_tips2b/oracle_matched/` — GFS, agrupamiento original
- `results/extensions/kth_tips2b/inner_group_sample/` — GFS, corregido
- `results/analysis/inner_grouping/` — efecto de la corrección
- `results/analysis/oracle_gap/` — 1.012 subconjuntos enumerados (k=1,2)
- `results/analysis/tie_breaking/` — puntajes internos por bloque
- `results/analysis/selection_saturation/` — margen interno por condición
