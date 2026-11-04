# Auditoría de comparabilidad y errores de la cascada

**Fecha:** 2026-10-21  
**Alcance:** auditoría reproducible de los cuatro pilotos de integración ya ejecutados y disponibilidad de bloques en los seis datasets principales. No se ajustaron modelos nuevos.

**Actualización de alcance:** la [reauditoría del 21-10](REAUDITORIA_INTEGRACION_2026-10-21.md) recalculó las 147 métricas y corrige la interpretación del costo, el protocolo de DTD y la disponibilidad de N-grams. Los costos de la tabla OOF siguiente están actualizados con ponderación por imagen; los CSV originales quedan conservados. La lista de próximos pasos vigente está en integración v3, sección 12 del plan.

## Resultado de la auditoría de biblioteca

Los seis caches se cargaron usando el cargador del proyecto. Las etiquetas de cada bloque coinciden en orden y contenido dentro de cada dataset. Para el inventario se registró una partición representativa seed 42/fold 0; CUReT usa a→b, Outex split oficial 1 y KTH split oficial 1 invertido (tres muestras para entrenamiento y una para prueba por clase). Cada fila incluye dimensiones, hashes de embeddings, etiquetas, manifiesto e índices de partición.

| Dataset | Imágenes | Clases | Bloques disponibles | Dimensiones concatenadas disponibles | Train/test de la partición auditada |
|---|---:|---:|---:|---:|---:|
| DTD | 5.640 | 47 | 21 | 20.396 | 4.512 / 1.128 |
| FMD | 1.000 | 10 | 21 | 20.396 | 800 / 200 |
| CUReT | 5.612 | 61 | 21 | 20.396 | 2.806 / 2.806 |
| Outex13Official1360 | 1.360 | 68 | 21 | 20.396 | 680 / 680 |
| SoilOriginal | 1.140 | 7 | 21 | 20.396 | 912 / 228 |
| KTHTIPS2b | 4.752 | 11 | 22 | 23.468 | 3.564 / 1.188 |

Los primeros cinco caches comparten exactamente los mismos 21 bloques y dimensiones. KTH contiene esos 21 más `beitv2_base_multilayer` (3.072 dimensiones); esa variante se excluye del panel común de 21. No hay `rgb_ngram_svd.npy` en esos caches estáticos, pero sí existe el bloque dinámico `RGBNgramSVDBlock` y conteos para los seis datasets. La ausencia de una SVD global no es un problema de disponibilidad: falta integrar su ajuste por fold en el evaluador nuevo. Los cuatro pilotos de cascada omiten N-grams y KTH incluye además el bloque multilayer.

DTD-SGKF 4.512/1.128 es una condición de desarrollo distinta de las diez oficiales. No emparejarla con tablas del protocolo oficial ni denominar sus métricas validación del panel canónico.

La auditoría comprueba que las predicciones guardadas corresponden a los índices de test recalculados desde los manifiestos. También guarda hashes de entrada, caché de ranking, parámetros de selección y código del ejecutor. Esto identifica las cuatro condiciones piloto; todavía falta expandir el registro a todas las semillas y pliegues del estudio antes de iniciar el barrido completo.

## Qué revelan las transiciones de error

Cada comparación usa las mismas imágenes de prueba dentro de su dataset. “Corregido” significa que la base se equivocó y la ruta adaptativa predijo la clase correcta; “introducido” significa que la base acertó y la ruta adaptativa cambió a una clase incorrecta. La columna neta es la resta entre ambas cantidades, no una prueba estadística.

| Dataset | Ruta adaptativa | Escaladas | Errores de base | Corregidos | Introducidos | Dejados sin escalar aunque el rescate estático acertaba | Reducción neta de errores |
|---|---|---:|---:|---:|---:|---:|---:|
| FMD | Ensamble de rescate | 64/200 | 11 | 5 | 3 | 0 | 2 |
| FMD | Rescate Top-4 | 64/200 | 11 | 5 | 2 | 0 | 3 |
| Outex | Ensamble de rescate | 148/680 | 73 | 36 | 4 | 2 | 32 |
| Outex | Rescate Top-4 | 148/680 | 73 | 29 | 5 | 2 | 24 |
| SoilOriginal | Ensamble de rescate | 47/228 | 15 | 5 | 3 | 0 | 2 |
| SoilOriginal | Rescate Top-4 | 47/228 | 15 | 5 | 3 | 0 | 2 |
| KTHTIPS2b | Ensamble de rescate | 172/1.188 | 39 | 23 | 5 | 0 | 18 |
| KTHTIPS2b | Rescate Top-4 | 172/1.188 | 39 | 31 | 2 | 0 | 29 |

Las rutas de rescate no corrigen todos los errores que la ruta estática podría corregir: las predicciones estáticas de los rescates aparecen por imagen en el CSV, junto a la compuerta, para localizar los errores que esta deja pasar. En KTH el rescate Top-4 corrige más errores e introduce menos que el ensamble; en Outex ocurre lo contrario en este split. Soil ofrece la misma transición neta para ambas rutas. Esto respalda mantener Top-4 como control y evaluar selección de rescate dentro de entrenamiento; no respalda elegir una política por dataset mirando estos resultados externos.

## Fronteras anidadas dentro del entrenamiento

Se implementó un evaluador de controles dentro del outer-train: base por ranking individual, rescates Top-3/4/5, ensambles de 3/5 y cuantiles 0,10/0,25/0,50. Cada fold productor recalcula ranking, base y márgenes de calibración con sus grupos de entrenamiento. Los ensambles sortean subconjuntos de cuatro bloques con β=8. El costo se calcula después; no selecciona los bloques. Esta ejecución no produce métricas de test externo, pero los tests/datasets ya fueron observados previamente en el proyecto.

La siguiente tabla muestra los dos extremos entre las políticas no dominadas para cada condición: el punto de menor costo estimado y el de mayor macro-F1 OOF. Son extremos descriptivos, no una recomendación de política. Costos en milisegundos: extracción más compuerta, con el perfil teórico del proyecto; excluyen latencia de clasificación y no son mediciones físicas.

| Condición | Menor costo no dominado | Mayor F1 no dominado |
|---|---|---|
| DTD-SGKF fold 0 | Base: 0,8393 / 53,09 ms | Top-5 estático: 0,8696 / 290,55 ms; Top-5 adaptativo q=0,50: 0,8696 / 172,53 ms |
| FMD fold 0 | Base: 0,9750 / 11,68 ms | Top-3 adaptativo q=0,10: 0,9825 / 21,95 ms |
| CUReT a→b | Base: 0,9911 / 148,69 ms | Top-5 adaptativo q=0,10: 0,9996 / 162,80 ms |
| CUReT b→a | Base: 0,9929 / 177,30 ms | Ensamble-3 adaptativo q=0,10: 0,9975 / 188,46 ms |
| Outex split 1 | Base: 0,8682 / 147,39 ms | Top-5 adaptativo q=0,50: 0,9105 / 214,05 ms |
| SoilOriginal fold 0 | Base: 0,8355 / 15,50 ms | Top-4 adaptativo q=0,25: 0,8627 / 27,85 ms |
| KTH split 1 invertido | Base: 0,8967 / 122,27 ms | Top-5 adaptativo q=0,50: 0,9244 / 188,29 ms |

KTH usa tres folds internos porque el train oficial invertido contiene solo tres muestras físicas; las demás condiciones usan cuatro. Los cuantiles son objetivos de calibración del entrenamiento y la fracción observada puede diferir de ellos. Las cifras cambian entre direcciones de CUReT, como corresponde a los dos protocolos.

Las rutas adaptativas ofrecen puntos internos de menor costo proyectado para F1 descriptivamente parecidos a sus rescates estáticos. El tamaño de rescate y la curva varían por condición. Las 147 métricas coinciden con las predicciones, y reponderar los costos por tamaño de fold conserva los puntos no dominados. La evaluación externa posterior debe tener protocolo emparejado y carácter exploratorio por la exposición histórica; estas cifras no acreditan superioridad frente a Complete-22 ni ahorro físico. Se conserva la frontera completa.

## Archivos reproducibles

- `results/analysis/integration_v2/audit_summary.json`: resumen del chequeo de conjuntos de bloques.
- `results/analysis/integration_v2/six_dataset_library_inventory.csv`: inventario por dataset y bloque, con dimensiones y hashes.
- `results/analysis/integration_v2/condition_registry.csv`: procedencia de los cuatro pilotos, particiones y configuración.
- `results/analysis/integration_v2/pilot_comparability_summary.csv`: comparación de bibliotecas y métricas resumidas.
- `results/analysis/integration_v2/rescue_error_transitions.csv`: transición por imagen, incluyendo etiqueta, grupo, escalado y predicciones.
- `results/analysis/integration_v2/rescue_error_transitions_by_class.csv`: resumen por clase codificada.
- `results/analysis/integration_v2/nested_selection_registry.csv` y `nested_frontier_summary.csv`: siete condiciones internas y las 21 políticas por condición, con cobertura OOF y hashes.
- `results/exploratory/integration_v2/nested_frontier21/`: predicciones OOF, fronteras y configuración de cada condición.
- `src/audit_integration_v2.py`: generador del inventario y diagnósticos.
- `src/run_rescue_nested_selection.py` y `src/register_nested_frontiers.py`: evaluador interno y registro de procedencia.
- `src/reaudit_integration_v2.py` y `results/analysis/integration_v2/reaudit_20261021/`: recálculo independiente de métricas guardadas, diagnóstico de costos y disponibilidad de conteos N-gram.

## Decisión y siguientes acciones

1. Corregir costo por imagen y guardar procedencia al lanzamiento; completar el registro canónico y alinear DTD oficial.
2. Reutilizar los conteos N-gram existentes con digest coincidente e integrar SVD por fold productor, conservando hashing fijo.
3. Implementar selección que use presupuesto/costo marginal; contrastar con los controles de ranking ya producidos y con Carlos.
4. Evaluar reglas congeladas en condiciones externas emparejadas y medir físicamente las rutas completas.
5. Recalcular estadística y actualizar el manuscrito después de esas evaluaciones; seguir integración v3, sección 12.

Los cuatro pilotos continúan siendo exploratorios, de una partición por dataset. Sus diferencias de F1 no se deben combinar entre datasets como si fueran una prueba inferencial ni presentar como resultado final de tesis.
