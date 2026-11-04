# Neshov/BEiTv2: adaptación al panel externo común, v1

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: protocolo prospectivo de nuevas llamadas, posterior a observar panel local.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: especificación fijada; runner y manifiesto aún pendientes.
- Version Label: neshov_common_external_v1.

## Sistema y cobertura

Autoridad: nueva petición de replicar papers y medir F1/latencia, registrada en
PLAN_REPLICAS_PAPERS_2026-11-02.md. No cambia el piloto28-10 ni sus archivos.
Etiqueta: reimplementación adaptada al benchmark común, no código oficial ni
reproducción de porcentajes publicados. Decisiones de interpretación heredadas
de REPRODUCCION_NESHOV_BEITV2_2026-10-27.md y piloto28-10, sin optimizarlas por test.

47condiciones únicas:15FMD,2CUReT,10DTD,1Outex,15Soil,4KTH. Comenzar FMD/42/f0
como primer caso operativo por orden fijo, luego FMD completo, después CUReT,
DTD, Outex, Soil, KTH. No elegir ampliaciones según desempeño. Cada método usa
su MLP propia; no crear dos resultados idénticos bajo nombres SVM y ResMLP.
Mismos índices externos/fit y mapeos de etiquetas del panel común. Manifiesto
debe verificar identidades equivalentes entre ambos heads locales y fijar hashes
de configs, índices e imágenes antes de extracción. No tomar índices por resumen.

## Receta fijada

Checkpoint timm beitv2_base_patch16_224.in1k_ft_in22k_in1k, offline y carga
estricta con puente de índices posicionales idénticos ya documentado. Congelar
SHA256 del peso local en el manifiesto. Software local congelado, diferencias
con versiones de fuente declaradas, sin actualizar bibliotecas para esta corrida.
Backbone completo congelado/eval FP32, capas2/5/8/11 desde1, GAP sin CLS,
concatenación3072, sin L2/normalización adicional. RGB, resize224×224 bilineal,
ToTensor y media/desviaciónImageNet. No truncar backbone después de capa11.

MLP FC3072→64/BN/ReLU/Dropout.2/FC→K, CrossEntropyLoss/logits, Adam .001,
weight_decay .0001, betas(.9,.999),100épocas, batch32, shuffle y semilla42
de entrenamiento para cada cabeza. Esta semilla es distinta de las semillas
de partición42/123/2026. Época final, sin early stopping/gridsearch/selección por
test. Ajustar exclusivamente fit externo, no ajustar con validación/test.
Clase→índice explícito, reversible, fijado antes del fit y guardado con la cabeza.
No eliminar una fila para resolver BatchNorm: preflight rechaza lote final
singleton si apareciera; requiere revisión antes de cualquier cambio de receta.

Features de entrenamiento pueden cachearse porque backbone no se ajusta;
extracción en lotes8, GPU exclusiva mediante lockglobal. Cabeza entrenadaCPU2hilos.
No caché para evaluación física: cada llamada extrae desde archivo original.

## Comprobaciones y cronómetro

Primera/última fila de fit de cada dataset según orden de manifiesto, sin usar
sus resultados para elegirlas. Comparar extracciónFP32 batch1/batch8 en mismo
dispositivo con maxerror absoluto≤1e-4 en vector3072; registrar tensores/hashes.
No exige igualdad con bloqueBEiT768 ni con salidas del autor no disponibles.
Si falla, conservar evidencia/requires_review, no aflojar umbral ni retry automático.

Warmup5llamadas sobre primera fila de fit, excluidas del panel y de la distribución.
Evaluación una llamada por imagen externa, orden de filas del manifiesto; repetir
imágenes entre semillas no las convierte en observaciones independientes.
ExtractorGPU FP32 residente y MLPCPU2hilos: usar src/neshov_online_adapter.py,
sincronizaciónCUDA, perf_counter_ns, archivo/decodeRGB→preprocesamiento→GPU→
extracción→D2H→MLP→clase. Carga y serialización fuera del cronómetro; registrar
esta definición. Usar logits de esa llamada para clase/F1, no F1cached del piloto.
No comparación de aislamiento temporal con panel histórico: entorno compartido
y fechas distintas; registrar observabilidad nueva y mantener reservas originales.

## Ejecución y éxito

Timeouts operativos por condición: extracción7200s, cabeza1800s, online14400s.
No timeout inferido por calidad; proceso y progreso con logs30s. Hardtimeout
conserva parcial/error y termina solo proceso propio según infraestructura aprobada.
No reintentos científicos. Un benchmarkGPU a la vez; sin extracción/fit concurrente
durante benchmark; CPU2hilos, HFoffline y sin descargas de checkpoint.

Antes de despachar falta implementar y probar runner/preflight y congelar
manifiesto con comandos exactos, fuentes/versiones, directorios nuevos, pesos,
filas/mapeos y estado esperado por etapa. Este documento no dice que ya se ejecutó.
No ejecutar comandos del piloto28-10 con nuevas filas como sustituto de runner.

Guardar: status/error, receta/config, hashes, índices fit/test, imágenes,
featuresfit/orden, entrenamiento100épocas, head, mapeo, llamadas online con
row/truth/pred/logits/ns, observador/ambiente y auditoría. Resumen por dataset solo
con todas sus condiciones; total47solo al cerrar todas. Comparar F1macro por
condición y latencia por llamadas, sin integrar piloto800 ni DTDadicional.
No hipótesis de superioridad impuesta ni estadísticas inferenciales en este v1.
