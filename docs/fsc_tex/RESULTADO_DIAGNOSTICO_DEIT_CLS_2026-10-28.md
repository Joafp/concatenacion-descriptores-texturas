# DeiT-small: CLS no reconcilia el embedding archivado

## Material Passport

- Fecha: 28-10-2026. Tipo: resultado diagnóstico parcial, ARS inline.
- Autoridad: diagnosticar CLS y corregir el adaptador solo si pasa 1e-4.
- Estado: condición de corrección no satisfecha; adaptador no modificado.
- No se modificaron embeddings, cabezas ni resultados de calidad.

## Observación obtenida

Se cargó el checkpoint local facebook/deit-small-patch16-224 sin crear pooler,
con el mismo procesador del preflight previo. La carga no indicó pesos de
backbone faltantes; descartó las dos claves de la cabeza clasificadora.
Sobre la primera imagen fija del preflight (fila FMD 3), CLS normalizado produjo:

| Control | Valor |
| --- | ---: |
| Dimensión idéntica | Sí |
| Valores finitos | Sí |
| Error absoluto máximo | 0,19253962486982346 |
| Error absoluto medio | 0,059067847860250045 |
| Error L2 | 1,4570781613921078 |
| Coseno | -0,06153836850011381 |
| Tolerancia original | 0,0001 |
| Pasa | No |

Por tanto, **eliminar el pooler y usar CLS no basta para reproducir este
embedding**. No se modificó el adaptador ni se repitió el preflight de los 22
bloques: ambos pasos estaban condicionados a la coincidencia numérica.
La carga previa de un pooler sin pesos entrenados era un problema real del
adaptador actual, pero no queda demostrado que sea la única diferencia.

## Incidente del registro

Después de imprimir la primera comprobación, la ejecución falló al serializar
`loading_info`, cuyos campos eran conjuntos Python en esta versión de
Transformers. El estado JSON en `results/analysis/deit_cls_diagnostic_20261028/`
conserva únicamente el preflight anterior a esa observación. **No debe leerse
como un diagnóstico completo ni como prueba de coincidencia.**

La salida de la sesión registró exactamente:

```json
{"row_index":3,"same_shape":true,"finite":true,"tolerance":0.0001,"pass":false,"max_abs_error":0.19253962486982346,"mean_abs_error":0.059067847860250045,"l2_error":1.4570781613921078,"cosine":-0.06153836850011381}
```

El error terminal fue `TypeError: Object of type set is not JSON serializable`.
Se corrigió exclusivamente la conversión de conjuntos en el registrador y se
añadió una prueba de regresión sin GPU. No se repitió la extracción fallida ni
se reconstruyeron retrospectivamente vectores que no llegaron a guardarse.
La segunda imagen no fue evaluada. Basta el primer fallo para descartar la
condición de aceptación, pero no para localizar toda la causa del desacuerdo.

## Siguiente decisión necesaria

La inspección de `embeddings_confirmatory/FMD/deit_s_metadata.json` identifica
semilla 42 y PyTorch 2.12.1+cu126. `src/reextract_confirmatory_embeddings.py`
ejecuta `legacy.set_seed(args.seed)` antes de construir el extractor; el
adaptador online no lo hace. Es una discrepancia verificable del procedimiento,
pero su capacidad de explicar el vector archivado **no se ha probado**.
Se consultó al usuario por un diagnóstico separado del estado original con
semilla 42. No se integró automáticamente como corrección tras fallar CLS.

Rastrear entorno, versión y checkpoint exactos usados para crear los embeddings
DeiT archivados y buscar pesos de la extracción original, incluido cualquier
pooler. No sustituir el embedding por CLS ni reentrenar silenciosamente los
controles. Si esa representación no se puede reconstruir, habrá que decidir
explícitamente entre reconstruir el entorno original o una biblioteca corregida
con una evaluación de calidad nueva. Mientras tanto, latencias de la biblioteca
completa no validadas y ninguna aceleración física publicada.
