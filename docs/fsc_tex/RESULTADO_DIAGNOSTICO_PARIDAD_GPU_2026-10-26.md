# Resultado del diagnóstico de DINOv2-small en GPU

## Material Passport

- Origin Skill: ARS experiment-agent, ejecución local guiada.
- Origin Mode: run.
- Origin Date: 2026-10-26.
- Verification Status: ANALYZED; cuatro vectores comparados, sin validación de ruta completa ni latencia.
- Version Label: dinov2_small_gpu_diagnostic_result_v1.

El [protocolo congelado](DIAGNOSTICO_PARIDAD_GPU_2026-10-26.md) se conserva sin cambios. Este resultado se registra aparte para mantener intacta su huella previa a la ejecución.

+## Resultado observado

Las cuatro filas pasaron el criterio original, sin modificar la tolerancia:

| Condición | Fila del manifiesto | Error absoluto máximo GPU | Criterio ≤ 0,0001 |
| --- | ---: | ---: | --- |
| FMD/42 | 7 | 0,000000488013 | Pasa |
| FMD/42 | 193 | 0,000000406057 | Pasa |
| Outex/123 | 6 | 0,000000461936 | Pasa |
| Outex/123 | 266 | 0,000000301749 | Pasa |

Las filas 193 y 266 fueron las que detuvieron los pilotos CPU, con errores 0,00018891 y 0,00010315, respectivamente. En estas cuatro filas DINOv2-small reconstruido en la RTX 4060 concuerda con los vectores archivados dentro del criterio fijado. Es evidencia compatible con variación numérica de la ejecución CPU/GPU; no identifica de forma aislada la contribución de kernel, precisión o tamaño de lote ni prueba fidelidad de todos los demás extractores.

El registro conserva `matmul_allow_tf32=false`, `cudnn_allow_tf32=true` y precisión matmul `highest`, tal como se observaron. No se cambiaron esas opciones para forzar la paridad. Los pilotos CPU y sus fallos se preservan intactos.

Fuentes nuevas: `results/analysis/dinov2_small_gpu_parity_20261026/diagnostic.json` y `diagnostic_vectors.npz`. Se verificaron las huellas de entradas y vectores después de ejecutar. Las dos pruebas focalizadas de este diagnóstico pasaron; no se repitió la suite completa de 114 pruebas en este corte ni se la presenta como una prueba de rendimiento físico.

**Estado siguiente:** se resolvió esta comprobación de DINOv2-small en GPU, pero sigue pendiente verificar los demás bloques y las predicciones/compuertas de la ruta online completa y medirla con recursos documentados. No se ejecutaron nuevos ajustes SVM, pruebas de calidad, inferencia estadística ni mediciones de velocidad. No hay ahorro físico nuevo que añadir a la presentación.
