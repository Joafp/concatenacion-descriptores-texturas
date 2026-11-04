# Diagnóstico autorizado: paridad de DINOv2-small en GPU

## Material Passport

- Origin Skill: ARS experiment-agent, ejecución local guiada.
- Origin Mode: run.
- Origin Date: 2026-10-26.
- Verification Status: PENDING antes de la ejecución.
- Version Label: dinov2_small_gpu_diagnostic_v1.

El autor respondió «Sí, diagnosticar paridad en GPU» a una consulta que excluye cambiar la tolerancia, repetir los experimentos de calidad y publicar latencias con la GPU ocupada. Se mantiene el umbral absoluto máximo de **0,0001** sobre vectores normalizados.

## Alcance fijado

Una carga de DINOv2-small en GPU, utilizando el mismo adaptador y preprocesamiento del piloto CPU, checkpoints locales en modo offline y primeras dos filas de las listas ya fijadas de FMD/42 y Outex/123. Son cuatro comparaciones de vectores, incluidas las filas que detuvieron esos pilotos. No se ajustan SVM, no se seleccionan políticas, no se calculan nuevas métricas de calidad y no se mide ni publica tiempo de inferencia.

Se verifican hashes de las imágenes y se guardan huellas de fuentes, etiquetas, embeddings, metadatos y adaptadores antes de extraer. No se sobrescribe ningún resultado original. Las salidas se guardan en `results/analysis/dinov2_small_gpu_parity_20261026` y el ejecutor rechaza una carpeta ya existente.

La GPU conserva actividad ajena. El proceso no la interrumpe, carga un solo extractor y requiere al menos 512 MiB libres antes de cargarlo. Registra configuración numérica observada (TF32 y precisión matmul), sin cambiarla para forzar un resultado. Su techo operativo es diez minutos y no hay reintento automático.

## Interpretación

Si alguna fila excede el umbral, el diagnóstico completa con paridad fallida, sin suavizar el criterio. Si las cuatro pasan, solo se resuelve esta comprobación parcial de un extractor en estas filas: no valida el ensamble completo ni habilita por sí sola un reclamo de velocidad. El contraste CPU/GPU orienta el diagnóstico, pero no prueba por sí solo que el dispositivo sea la única causa, dado que el entorno histórico y el tamaño de lote también pueden influir.

Una medición física posterior exige fidelidad de todos los bloques y predicciones y una sesión de recursos documentada; no queda sustituida por este diagnóstico.
