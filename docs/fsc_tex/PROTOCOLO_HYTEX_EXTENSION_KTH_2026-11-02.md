# HyTexNet ADAPTADO: KTH-TIPS2-b en panel común

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: extensión autorizada del sistema adaptado completo.
- Origin Date: 2026-11-02.
- Verification Status: fijado antes de modelos/llamadas KTH HyTex.
- Version Label: hytex_kth_adaptation_v1.

Hereda PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md íntegro: RGB128,
descriptor514+DenseNet121GAP1024 congelado offlineFP32,head256/ReLU/dropout0.5,
Adam0.001/wd0.0001/betas0.9/0.999,100épocas/batch32/trainseed42,últimaépoca.
No ajuste por resultados de otros datasets. Adaptación, no cifraspublicadas.

4752filas,11clases,4muestras físicas a/b/c/d porclase. Cuatro condiciones
seed42/folds0–3,3564train/1188test cada una. Protocolo común usa tres muestras
para train y una para test (invierte las columnas históricas split_1..4 de
una muestra train). Exigir coincidencia exacta de índices en ambos heads,
config oficialfold+1,invert_official_split=True,inner_group_column=sample.
No mezclar la reserva histórica de cascadas ni afirmar equivalencia con
papers que usan una muestra para entrenamiento y tres para test.

Controlar cada muestra física disjunta, clases completas, hash/grupos, cobertura
test total una vez,4752imágenes. Etiquetas por primera aparición textual,
hash del array completo contra8estados y verdad de cada bloque policy de
predicciones archivadas; no usar predicciones como etiquetas. CSV nuevo con
path desde source_path ysha256 desde source_sha256 conserva orden/bytes/grupos.
Ruta explícita data/KTH-TIPS2-b, no alias KTHTIPS2b en ruta física.

Mismo runner sellado y cuatro etapas extract/train/online/audit. Gate batch1
first/lastfit→batch1≤1e-4, evidencia antes de aceptar; primera auditoría
habilita tres restantes. Cinco warmups fit excluidos; una llamada archivo-a-
clase por test, total4752, F1 ylatencia de esas mismas llamadas sin featurecache.
GlobalGPUlock,CPU2hilos,sin fits/extracciones/benchmarks concurrentes.
Timeouts7200/1800/14400/300s,ventana12h. Error requiere revisión sinretry,
relajar tolerancia ni cambiar método. No repetir otras colas cerradas/fallidas.

Consolidar solo4/4 con hashes yrecibos/cadenas completos; comparar diez pares
head×método con ganancias/pérdidas, manteniendo reservasKTH históricas y
hardware compartido/fechas distintas. No inferencia global ni reproducción
de porcentajes delpaper ni igualdad contemporánea aislada. No manuscrito,
commits,push,descargas,contactos ni serviciospagos.
