# Trazabilidad Outex13: filas señaladas y métodos — 8 de noviembre de 2026

Análisis de solo lectura: no hubo extracción, entrenamiento, inferencia ni
modificación de resultados. La hipótesis sobre cinco embeddings sigue pendiente
de verificación independiente; este documento no estima efecto contrafactual.

## Corridas de Carlos

La columna `blocks` de `results/exploratory/sota_timing/outex13/our_runs.csv`
identifica los bloques declarados para cada resultado:

| Método | ViT-B/16 | DeiT-S |
|---|---|---|
| Top-4, SVM y ResMLP | No | No |
| Ensamble diversidad, SVM | Sí | No |
| Ensamble diversidad, ResMLP | No | No |
| Completa-22, SVM y ResMLP | Sí | Sí |
| Scabini, KNN/LDA/SVM | No | No |

Scabini declara BEiTv2 en `sota_runs.csv`. Estas dependencias no demuestran que
el resultado haya cambiado: incluso un método sin esos bloques finales podría
depender de otras etapas de selección o entrenamiento.

## Llamadas online del panel local

Se filtraron las filas 991, 1137 y 1329, marcadas test en el manifiesto, en
los archivos `online_calls.csv` de ambas condiciones Outex, repetición primaria
`repeat=0`. Hay 5 políticas × 3 filas × 2 clasificadores = 30 llamadas; las 30
predicciones guardadas coinciden con su etiqueta. Esto no estima qué habría
ocurrido con otros embeddings, ni descarta impacto de las dos filas train
1034 y 1302 sobre ajuste o selección.

| Política | SVM, bloques de cada una de las 3 llamadas | ResMLP |
|---|---|---|
| Completa-22 | `vit_b16` y `deit_s` | ambos |
| Ens-diversidad | `vit_b16`, no `deit_s` | ninguno |
| Top-4 | ninguno | ninguno |
| Ens-tombola | ninguno | ninguno |
| Adaptive-selection-margin | ninguno | ninguno |

`blocks` describe cada llamada online, no prueba que el embedding histórico
señalado por Carlos se haya usado en esa inferencia. La dependencia del ajuste
respecto de datos precalculados y el efecto de sus filas train requieren más
auditoría. El acierto en tres muestras no descarta efectos en otras muestras.

## Evidencia disponible de Carlos

La carpeta `results/exploratory/sota_timing/outex13/` contiene `our_runs.csv`,
`sota_runs.csv`, `timing_table.csv` y `extraction_times.json`. Los CSV de
corridas guardan métricas agregadas y bloques, no predicciones ni IDs por imagen.
Los scripts `src/benchmark_our_methods.py` y `src/benchmark_sota_methods.py`
calculan métricas desde `pred` y escriben filas agregadas; no se observó
escritura de predicciones individuales en esos scripts. Esos archivos por sí
solos no permiten reconstruir F1, verificar las tres predicciones ni emparejar
llamadas con el panel local. Esto no demuestra que no existan predicciones en
otra ubicación o máquina.

## Fuentes y huellas SHA-256

- Manifiesto `Outex13Official1360.csv`: `6499321a05630111dda4e3a7421995555553deea4807f23a5b4673a011856447`.
- Carlos `outex13/our_runs.csv`: `fe54e48a0ef79c9590c5567ad013da3ffdf358c1195defe03530c7c9bc785086`.
- Carlos `outex13/sota_runs.csv`: `1073fb52e74ab56ee102232b4bd619c49d7507ca51271150148b5ef17472211a`.
- Panel SVM `online_calls.csv`: `484720bb6b2fb4d194079bd2aebfd8234958019bb4d550d32d2074a7e4646f2e`.
- Panel ResMLP `online_calls.csv`: `3535989e931bc853b17886261d4d5735b00e994b81a7b4e639cd84c1ad9576db`.

Los hashes online constan en `results/analysis/reconciliation_outex_calls_20261104_v1/provenance.json`.
Los identificadores y hashes de las imágenes están en la
[conciliación inicial](CONCILIACION_CARLOS_SOTA_TIMING_2026-11-08.md).

## Pendiente

Localizar recibos y predicciones individuales si existen, comprobar hashes de
embeddings y decisiones de entrenamiento/selección, y diseñar por separado una
validación de la hipótesis antes de nuevas extracciones. Conservar la reserva en
conclusiones y no cambiar los resultados observados.
