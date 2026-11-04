# Estado original de DeiT recuperado con semilla 42

## Material Passport

- Fecha: 28-10-2026. Ejecución numérica guiada por ARS, inline.
- Autoridad: reconstruir el estado original; integrar solo con coincidencia.
- Estado: diagnóstico completado, ambas imágenes pasan; adaptador local integrado.
- Protocolo previo: `PROTOCOLO_DIAGNOSTICO_DEIT_SEED42_2026-10-28.md`.
- Embeddings, cabezas, predicciones y F1 preservados. Sin latencias publicadas.

## Resultado

La metadata de DeiT/FMD declara semilla 42 y su SHA-256 coincide con el archivo
de embeddings. Se reprodujo el orden original: `set_seed(42)`, construcción
del procesador/modelo y extracción mediante el método histórico, sin cambiar
el checkpoint o seleccionar otro tap.

| Fila FMD | Error absoluto máximo | Coseno | Pasa 1e-4 |
| --- | ---: | ---: | --- |
| 3 | 0,0000003054738045 | 0,9999999999986624 | Sí |
| 996 | 0,0000001713633537 | 0,9999999999996385 | Sí |

La ruta CLS anterior no coincidía. La carga histórica usa `pooler_output` de
un pooler inicialmente no entrenado y reproducible mediante el estado de carga
original. El adaptador sin fijar ese estado generaba otro pooler. La
reconstrucción pasa sobre estas dos imágenes con la tolerancia intacta.

Esto permite reproducir la **representación histórica**, no calificar ese
pooler como preentrenado, convertirlo en una cabeza entrenada ni demostrar
paridad universal. Es una limitación de la representación que debe conservarse
en la trazabilidad metodológica, no ocultarse reemplazándola por CLS.

## Corrección acotada

Se creó `src/local_deit_reconstruction.py`. Antes de cargar exige diagnóstico
completado, dos checks positivos con tolerancia 1e-4 y hash idéntico del estado
del pooler. Carga el backbone original y restaura **solo** los dos parámetros
validados del pooler, con carga estricta de ese submódulo. No depende del
orden de inicialización de otros extractores. Se preserva el RNG de CPU del
llamador durante la construcción. El adaptador histórico queda intacto.

El preflight local acepta la reconstrucción mediante argumento explícito y
comprueba además el hash del embedding al que está ligada. La nueva corrida se
guarda en carpeta distinta de ambos fallos previos. Sus resultados se deben
consultar separadamente: recuperar DeiT no implica que los otros 21 bloques
o las cinco rutas ya hayan pasado.

## Artefactos

- Diagnóstico y estado recuperado: `results/analysis/deit_seed42_diagnostic_20261028/`.
- Preflight nuevo: `results/analysis/local_online_parity_seed42_20261028/FMD_s42_f0_svm/`.
- Pruebas focalizadas del adaptador/registro: seis aprobadas, sin GPU.

No se realizó entrenamiento ni se publicó aceleración física.

## Resultado del preflight repetido

La nueva ejecución pasó BEiT-v2, ConvNeXt-v2 y **DeiT-small corregido** en
las dos imágenes originales. Se detuvo después en DenseNet121, fila 3:
error máximo 0,00011245906352996826 frente a 0,0001; coseno
0,9999998188337963. Este es un desacuerdo nuevo y mucho menor que el de DeiT,
no una recaída del pooler corregido. Su causa todavía no está diagnosticada.

Se conserva el fallo en `local_online_parity_seed42_20261028`, sin relajar la
tolerancia, modificar DenseNet o reintentar automáticamente. Pasaron tres
extractores, no los 22 ni las rutas completas. Latencia física pendiente.
