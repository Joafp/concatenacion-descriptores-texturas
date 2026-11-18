# Tabla exploratoria: accuracy por dataset y método

Porcentaje medio entre condiciones completas. Cada columna representa una receta local; los métodos externos son adaptaciones y no cifras reportadas por sus autores.

| Dataset | Condiciones Top-4 | Top-4 SVM | Completa SVM | Margen + ensamble SVM | Neshov adaptado | CellNN adaptado | HyTex congelada | HyTex ajustada | DeepLumina adaptada |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FMD | 15 | 98.23 | 96.50 | 97.77 | 94.20 | 27.10 | 74.17 | 74.17 | 85.53 |
| CUReT | 2 | 99.86 | 99.89 | 99.84 | 99.39 | 70.99 | 98.31 | 99.11 | 98.81 |
| DTD | 10 | 87.03 | 86.51 | 86.86 | 80.27 | 22.47 | 62.60 | — | — |
| KTHTIPS2b | 4 | 95.75 | 96.06 | 94.15 | 92.82 | 60.73 | 83.92 | — | 87.98 |
| SoilOriginal | 15 | 91.58 | 92.75 | 92.22 | 90.82 | 46.84 | 85.09 | 86.75 | 86.14 |
| Outex13Official1360 | 1 | 92.94 | 95.74 | 92.94 | 92.21 | 64.71 | 89.56 | 85.59 | 91.03 |

— = no hay agregado completo para esa receta; no es cero.
La regla por margen incluye rescate por ensamble y no es la E1 estricta. DeepLumina presenta no convergencia y DTD 9/10. KTH/DTD/Outex mantienen las reservas de los informes originales. Las condiciones no son réplicas necesariamente independientes.
Tiempos del CSV corresponden a llamadas online propias y se obtuvieron en sesiones diferentes; comparaciones temporales son descriptivas. No combinar con curvas de k calculadas desde otro archivo.

