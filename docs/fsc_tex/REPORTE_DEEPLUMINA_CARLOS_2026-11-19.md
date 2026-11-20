# DeepLumina: ajuste escalado y evaluación online

**Cierre auditado:** variante B escalada, 47/47 condiciones, 36.264 llamadas individuales, seis datasets. Los resultados son una **adaptación local**, no una reproducción fiel del código o de los porcentajes del paper. Ver [auditoría online](../../results/analysis/deeplumina_carlos_online_audit_20261119_v1/summary.json), [condiciones y métricas](../../results/analysis/deeplumina_carlos_online_audit_20261119_v1/conditions.csv) y [agregados](../../results/analysis/deeplumina_carlos_online_audit_20261119_v1/datasets.csv).

Los 47 ajustes se auditaron: hashes, filas de entrenamiento, matrices ECOC y media y varianza del escalador verificados. Ninguno de sus 2.525 clasificadores binarios llegó al límite de 100.000 iteraciones ni produjo avisos registrados. La ausencia de avisos no demuestra equivalencia con el criterio de MATLAB ni garantiza por sí misma un óptimo. [Auditoría de entrenamiento](../../results/analysis/deeplumina_carlos_training_audit_20261119_v1/summary.json).

## Accuracy y macro-F1

Medias equiponderadas por condición dentro de cada dataset. Delta = B escalada menos adaptación original, en puntos porcentuales; usa las mismas filas de prueba en las condiciones disponibles.

| Dataset | Condiciones B | Accuracy B | Macro-F1 B | Accuracy original | Delta accuracy |
|---|---:|---:|---:|---:|---:|
| CUReT | 2/2 | 98,88 % | 98,88 % | 98,81 % | +0,07 pp |
| DTD | 10/10 | 70,55 % | 70,37 % | No disponible 10/10 | — |
| FMD | 15/15 | 85,63 % | 85,60 % | 85,53 % | +0,10 pp |
| KTH-TIPS2-b | 4/4 | 88,28 % | 87,69 % | 87,98 % | +0,29 pp |
| Outex13 | 1/1 | 90,74 % | 90,57 % | 91,03 % | −0,29 pp |
| SoilOriginal | 15/15 | 86,20 % | 80,61 % | 86,14 % | +0,06 pp |

DTD original no se agrega como si cubriera 10 condiciones: conserva 9/10. La ejecución A de `f3`, pedida expresamente tras el timeout, **terminó con 83 de 84 SVM en el límite**, no 84; queda `requires_review` y no se ejecutó online. Las predicciones B de `f3` no sustituyen la condición original.

El [CSV de datasets](../../results/analysis/deeplumina_carlos_online_audit_20261119_v1/datasets.csv) incluye también precisión y recall macro. Las métricas se recalcularon desde los mismos registros que produjeron los tiempos; los 46 pares disponibles se cotejaron por índice y etiqueta. No corresponde afirmar identidad total de preprocesamiento entre todas las comparaciones históricas por esa sola comprobación.

## Latencia B

Medias ponderadas por llamada en ms: CUReT 85,05; DTD 79,77; FMD 73,28; KTH 73,56; Outex 84,12; Soil 78,48. Cada llamada incluye lectura/decodificación, preprocesamiento RGB/Y, dos pasadas ResNet101, escalador y cabeza ECOC; se excluyen verificación previa de hash, carga, calentamiento y escritura. Media, mediana y p95 por condición se encuentran en el [CSV](../../results/analysis/deeplumina_carlos_online_audit_20261119_v1/conditions.csv).

La GPU estaba a 0 % en la comprobación inicial y Wallpaper Engine había sido cerrado por el usuario; el lock coordina los procesos del proyecto, pero no garantiza ausencia de toda actividad externa durante la sesión. Las latencias originales y B provienen de sesiones diferentes y cualquier comparación de tiempos entre ambas es descriptiva, no una medición controlada pareada.

## Interpretación y límites

- El escalado y el aumento de presupuesto forman una **nueva variante conjunta**; el experimento no separa el efecto individual de cada cambio. No se eligió una variante por dataset.
- La identidad de pesos, preprocesamiento y ECOC con el MATLAB de los autores no está demostrada. La configuración B, aunque no llegó al límite, no reproduce necesariamente el procedimiento publicado.
- Los folds pueden reutilizar imágenes, Outex tiene una sola condición y no todas las medias son independientes. No se realizó inferencia estadística en este cierre.
- Las 47 ejecuciones online terminaron y se auditaron; una condición parcial o fallida no se reintentó automáticamente. Las fuentes originales y el estado de A se conservan.
