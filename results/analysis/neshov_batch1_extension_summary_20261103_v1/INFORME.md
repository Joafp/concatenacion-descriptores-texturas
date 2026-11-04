# Extensión Neshov a cinco datasets: auditoría cerrada

Fecha de cierre: 2026-11-03. Cola congelada: `results/analysis/neshov_batch1_extension_queue_20261102_v1`; SHA256 de `manifest.json`: `d76b39cb95a8bda7c740624407bd3584a0c2e3b4ee9a96f6ce9eac515e9257a4`.

La cola terminó 32/32 condiciones y se auditó cada dataset por separado. Se comprobaron las cuatro etapas, recibos y hashes de salidas, identidad de partición, la comprobación de paridad de extracción (tolerancia 1e-4), predicciones y latencias individuales de las mismas llamadas. Las comparaciones con el panel local usan los mismos casos de prueba; el promedio de F1 local agrega por condición y método. Las mediciones se hicieron en fechas/estados de hardware distintos, así que las diferencias de latencia son descriptivas.

| Dataset | Condiciones | Llamadas Neshov | Macro-F1 medio por condición | Accuracy media | Latencia media por llamada (ms) | F1 local medio sobre 10 métodos/cabezas | Rango de (F1 local − F1 Neshov) |
|---|---:|---:|---:|---:|---:|---:|---:|
| CUReT | 2 | 5.612 | 0,99396 | 0,99394 | 14,273 | 0,99881 | +0,00443 a +0,00515 |
| DTD | 10 | 18.800 | 0,80203 | 0,80266 | 16,791 | 0,86855 | +0,05924 a +0,07505 |
| Outex-13 | 1 | 680 | 0,91930 | 0,92206 | 14,612 | 0,94417 | +0,00819 a +0,04156 |
| Soil | 15 | 3.420 | 0,86310 | 0,90819 | 19,168 | 0,87019 | −0,00370 a +0,01609 |
| KTH-TIPS2b | 4 | 4.752 | 0,92448 | 0,92824 | 16,479 | 0,95091 | +0,01452 a +0,03545 |

Estas cinco ejecuciones son adaptaciones del sistema Neshov BEiTv2+MLP al panel común con extracción de fit y evaluación online batch-1; no son reproducción de las métricas publicadas de esos datasets. Soil muestra una pérdida pequeña en al menos una estrategia local; no se oculta ni se selecciona por resultado. Se conservan las reservas de muestras físicas de DTD y KTH y las diferencias de representación de Outex/Soil. El registro completo, incluidos F1 por partición, accuracy, latencia y comparaciones por cada estrategia, está en los cinco subdirectorios de este informe: `condition_metrics.csv`, `comparison_by_condition.csv`, `comparison_dataset.csv`, `summary.json` y `provenance.json`.

| Dataset | Cobertura | SHA256 de `summary.json` |
|---|---:|---|
| CUReT | 2/2; 5.612 llamadas | `872db8ab2242059b5c7f7a5d27a922e2c9360ec98c10b01b5742056e8132caf4` |
| DTD | 10/10; 18.800 llamadas | `43c52337db00dac5537b522f5782000c97765336e2df2e1875aab09d2e76cc04` |
| Outex-13 | 1/1; 680 llamadas | `9056af1fd4b2ff574e3d54212399fed767f8d7d7fba8fb19b22f77788b2b596f` |
| Soil | 15/15; 3.420 llamadas | `3f63df1b77fc9c903f6f736e822fd197c1e043284f3fd0d975095a14eef2b4` |
| KTH-TIPS2b | 4/4; 4.752 llamadas | `a1d44398bf42497968f9a496fdf61cbe0ae91728c466eca25542d388e6d0106d` |

En total: 32 condiciones y 33.264 llamadas. No se alteró el panel local ni se lanzaron ajustes después de observar los resultados. El primer auditor auxiliar detectó que los recibos Neshov no incluyen el campo `method` en cada estado de etapa; se corrigió únicamente el auditor para verificar la receta congelada por manifiesto y el hash de cada etapa. La auditoría completa pasó sin volver a ejecutar experimentos.
