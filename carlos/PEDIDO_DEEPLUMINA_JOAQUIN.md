# Pedido a Joaquín: volver a correr DeepLumina

Fecha: 2026-11-18 · De: Carlos · Para: Joaquín

> **Estado (23-11): resuelto.** Joaquín corrió la variante B: rasgos escalados
> y hasta 100.000 iteraciones, en 47 de 47 condiciones, sin ningún SVM en el
> tope (`docs/fsc_tex/REPORTE_DEEPLUMINA_CARLOS_2026-11-19.md`). La accuracy
> cambia entre −0,29 y +0,30 puntos frente a la versión original, y DTD queda
> completo con 70,55 %. La corrida A de `f3` sin límite de tiempo dejó 83 de
> 84 SVM en el tope, lo que confirma que la causa era la falta de escalado. Ya
> está integrado en `carlos/main.tex` (§4.11 y Tabla 13).

Joaco, en la reunión el profesor preguntó por qué DeepLumina «no convergió en
DTD» si en los otros datasets sí, y si no será un problema de implementación.
Revisé los registros que ya están en el repo. Te dejo lo que encontré y lo que
te pido correr. Si estás de acuerdo, decidilo vos con el profesor: yo no corrí
nada.

## 1. Lo que ya está en el repo

La no convergencia aparece en los seis datasets, no solo en DTD. Lo que es
propio de DTD es que la condición `s42_f3` superó el límite de 3.600 s de
entrenamiento y quedó en `requires_review`, sin modelo.

| Dataset | Condiciones | SVM binarios con `max_iter` | Entrenamiento por condición |
|---|---:|---:|---:|
| FMD | 15 | 41 de 690 | ≈ 3,3 min |
| Soil | 15 | 423 de 525 | ≈ 2,9 min |
| KTH-TIPS2-b | 4 | 166 de 200 | ≈ 3,8 min |
| Outex-13 | 1 | 92 de 92 | ≈ 10,4 min |
| CUReT | 2 | 178 de 178 | ≈ 21 min |
| DTD | 9 de 10 | 753 de 756 | 32 a 53 min; f3 > 60 min (cortada) |

- En DTD, `f2` ya tardó 53 min. La partición de `f3` no tiene nada raro:
  3.754 imágenes de entrenamiento, igual que las demás (3.749 a 3.757).
- Con 9 de 10 condiciones, DTD da 70,40 % de accuracy; el paper de DeepLumina
  informa 73,63 %.
- Tu diagnóstico de gradiente primal no deja a DTD como el peor caso. La
  mediana entre los clasificadores que llegaron al tope es 5,9e−3 en DTD y
  7,2e−2 en CUReT. Sin embargo, CUReT da 98,81 %, más que el 97,53 %
  publicado.

Fuentes:
- [Revisión de iteraciones](../results/analysis/deeplumina_niter_review_20261104_v1/summary.json)
- [Diagnóstico de estacionariedad](../results/analysis/deeplumina_stationarity_review_20261104_v1/INFORME.md)
- [Resumen DTD](../results/analysis/deeplumina_dtd_external_summary_20261103_v1/summary.json)
- Duraciones calculadas a partir de `started_utc` y `finished_utc` en
  `results/analysis/deeplumina_*_external_queue_20261103_v1/jobs/*/train/status.json`.

## 2. Hipótesis

No parece un bug que afecte solo a DTD:
- es el mismo código en todos los datasets;
- la cantidad de clasificadores con `max_iter` coincide exactamente con los
  avisos de los logs;
- ese mismo código reproduce CUReT.

Sospecho más bien de la configuración del clasificador que fijamos en el
[protocolo de adaptación](../docs/fsc_tex/PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md):

1. **Rasgos sin escalar.** Los 2.000 valores `fc` crudos entran directo al SVM.
   liblinear y scikit-learn recomiendan escalar, porque el descenso por
   coordenadas dual converge muy lento con rasgos de norma grande.
2. **Solver distinto del original.** Usamos `LinearSVC` (liblinear, pérdida
   squared hinge, `dual=True`, `C=1`, `max_iter=10_000`). El paper usó
   MATLAB `fitcecoc`, cuyo learner SVM usa SMO por defecto con pérdida hinge.
   Según MATLAB Answers, los otros valores por defecto serían un límite de
   10⁶ iteraciones, sin estandarizar y con `BoxConstraint` 1. La página
   oficial no los mostró; confirmalos en
   [templateSVM](https://www.mathworks.com/help/stats/templatesvm.html).
3. **DTD es el problema más grande.** Tiene 47 clases, 84 columnas ECOC por
   condición (FMD tiene 46) y clases que se solapan mucho. Por eso el límite de
   tiempo se nota solo ahí.

## 3. Qué te pido correr

Para que nadie diga que elegimos resultados, fijá la configuración en un
protocolo antes de correr y aplicala a **todas** las condiciones, no solo a
DTD `f3`.

**A. Completar DTD `f3` con la configuración original.** Mismo código, semilla,
partición y parámetros, pero sin el límite de 3.600 s. Sirve para tener DTD
10/10 con la adaptación tal como está y una media DTD comparable con los otros
métodos.

**B. Versión con convergencia corregida, en las 47 condiciones** (propuesta
principal):
- `StandardScaler` ajustado solo con las filas de entrenamiento de cada
  condición y aplicado a entrenamiento y prueba;
- `LinearSVC` con los mismos parámetros, salvo `max_iter=100_000`;
- sin límite de tiempo, o con un límite amplio (por ejemplo 6 h) fijado antes
  de correr;
- el mismo código ECOC, la misma decodificación y las mismas llamadas de
  prueba que la versión original.

Si preferís normalizar con L2 cada rama (RGB y Y) para seguir la línea del
resto de la tesis, está bien. Elegí una sola opción antes de correr.

**C. Opcional, más cercana a MATLAB:** `SVC(kernel="linear", C=1.0)` (libsvm,
SMO, pérdida hinge), `max_iter=-1` y sin escalar. Solo si los valores por
defecto de MATLAB se confirman y el tiempo alcanza.

**Costo aproximado.** El entrenamiento original sumó ≈ 9 h de CPU, de las
cuales ≈ 6,5 h fueron de DTD. Si los rasgos extraídos siguen en caché, solo
hace falta reentrenar las cabezas ECOC y predecir; no hay que volver a pasar
las imágenes por la ResNet-101.

## 4. Qué guardar y cómo informarlo

- Por cada SVM binario: `n_iter_`, si llegó al tope y el tiempo de ajuste.
- Por cada condición: accuracy, macro-F1, predicciones por llamada, cantidad de
  avisos y tiempo total de entrenamiento.
- Tu razón de gradiente primal para la versión B, para compararla con la
  original.
- Una tabla con la versión original y la B lado a lado en los seis datasets,
  salga como salga. No se elige la mejor variante por dataset.
- La corrida original queda intacta, con sus artefactos y hashes.
- Latencia: el escalado agrega una operación despreciable frente a las dos
  pasadas de la ResNet-101. Si no volvés a medir tiempos, avisame y en el paper
  aclaro que el tiempo es el de la corrida original.

Para decir que la versión B convergió, propongo dos condiciones: ningún SVM con
`max_iter` y ninguna condición cortada por tiempo.

## 5. Qué cambio yo en el paper cuando esté

En `carlos/main.tex`:
- la fila de DeepLumina y la columna de DTD de la tabla de comparación externa;
- la nota ‡ sobre la no convergencia;
- la sección de comparación con métodos recientes (§4.11 desde el 18-11).

Si B converge, DeepLumina deja de figurar como «sujeta a revisión» por
convergencia. Si no converge, se mantiene la reserva, pero con la causa
investigada.

## 6. Preguntas para vos

1. ¿Los rasgos de las 47 condiciones siguen en caché en tu máquina?
2. ¿Te parece bien `StandardScaler` como opción principal, o preferís L2 por
   rama?
3. ¿Corremos A y B juntos, o primero A para cerrar DTD 10/10?
