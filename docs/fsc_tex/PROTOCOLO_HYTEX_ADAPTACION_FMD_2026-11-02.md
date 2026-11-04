# HyTexNet adaptado al benchmark común: especificación prospectiva v1

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: implementación y experimento nuevo autorizado de comparadores externos.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: receta adaptada fijada; ejecución pendiente de runner/preflight.
- Version Label: hytex_common_fmd_adaptation_v1.

## Identidad y alcance

Autor autorizó réplicas viables y decisiones técnicas autónomas durante ausencia.
La fuente es DOI10.1016/j.knosys.2026.115482, PDF local hash
28169c0ec5d14654fffd347282c18caee99026bdf856149ffb3a46ae3f845e53.
Se conserva la arquitectura descrita, pero no están todos los parámetros de
entrenamiento/preprocesamiento ni código oficial verificados. Por tanto nombre
obligatorio: **HyTexNet adaptado, configuración local fijada**, no réplica fiel,
no reproducción de porcentajes publicados. Esta diferencia debe figurar en toda
tabla, no ocultarse en un anexo. No copiar F1 ni tiempos del artículo.

Primera etapa15condiciones FMD comunes (3semillas×5folds),3000llamadas externas;
es una ampliación a un dataset común, no un protocolo FMD del paper. No escoger
condiciones por desempeño. Índices exactos del preflightFMD compartido ya verificado,
sin usar heads/predicciones deNeshov para entrenar o elegir nada.

## Receta descrita y elecciones locales explícitas

EntradaRGB128×128. Elección local: PILresizebilineal, luminancia flotante
0.299R+0.587G+0.114B de la misma imagen redimensionada, sin redondeo a entero.
ParaCNN, ToTensor/ImageNetmeanstd. No augmentations/traincrop/flip añadidos.

Descriptor src/hytex_reference.py:8vecinos3×3 horario desde superiorizquierda,
se descarta borde1pixel (elecciones locales). Signo Ip≥Ic; magnitudabs(Ip−Ic),
umbralCDFempírica75% (sexta estadísticaordenada de8, sin interpolación), bits
mp≥T75. CentroIc≥mediaGLOBAL de imagen segúntexto/eq7–8; figura de ejemplo de
media local no se usa para cambiar esta decisión. HistS/M256 yC2, cada unoL1,
concat514; sin uniform/rotationmapping ni Hellinger adicionales.

DenseNet121tv_in1k, solo checkpointlocal existente, hash
c894c6d9caa317a8ca1942986dee7a16a86c77734a4d691d2abe05389cfef358,
snapshot f0d0f2698a02cb133b09d48396db6e1e46fe9f3b,32334434bytes. Cargaestricta,
sin headpreentrenada en extracción; ejecutar pipeline de features/pooling de
timm para embedding1024, eval/congeladoFP32. Elección explícita de implementación
timm y pesoImageNet, no garantía de mismocheckpoint de autores.
El artículo dice sin fine-tuning en descripción y end-to-end en entrenamiento:
esta adaptación fija backbonecongelado; no alternar interpretaciones porF1.

CNN1024 primero+HyTex514→1538→FC256/ReLU/Dropout.5/FC(K), logitsCE y
argmax para clase, sinBatchNorm ni softmax antes deCE. Se conservan dimensiones
y dropout deeq15–18. Entrenar SOLO cabeza con fit externo, semilla42 por cabeza.
Parámetros no verificados de la fuente se fijan localmente ANTES de nuevas
predicciones: Adam.001, betas(.9,.999), wd.0001,100épocas, batch32 yshuffle42,
épocaFINAL, sin earlystopping ni selección por test. No se atribuyen estos
valores al paper. No gridsearch ni ajuste por nuevas métricas; mapeo clases
explícito, inmutable y comprobado. Conservar historial y logits de entrenamiento.

## Régimen físico y controles

Extraerfeatures de fit en batch1FP32, misma ruta que online, no cachés DenseNet
históricas. Esto fija el régimen de esta adaptación nueva, no repite ni declara
resuelto el fallo de paridadhistoricalDenseNet ni el deNeshov. Ninguna comparación
con embeddings archivados se presenta como condición pasada de este método.
Antes de entrenar, reextraer primera/última filafit fijadas para comprobar
consistencia de vector1538 batch1→batch1 maxabs≤1e-4; guardar vectores y errores.
Si falla: requires_review, conservar todo, sin retry/relajar umbral/cambiarbatch.

CNNGPUresidente, descriptor y MLPCPU2hilos, D2H/concatenación incluidos en
cronómetro. Entradaarchivo→decodeRGB→resize→descriptorHyTex/CNN→MLP→clase,
sincronizaciónCUDA. Una llamada por imagenexterna;5warmups sobre primerfit
excluidas. Cada predicción/logits/ns/verdad/rowproviene de la misma llamada.
Sin features compartidas entre competidores, sin nuevoF1cached con tiempoonline.

Timeouts extracción7200s,train1800s,online14400s,auditoría300s por condición.
Solo un lockGPU global, no entrenamiento ni extracción concurrente al benchmark,
CPU2hilos, paquetes/versiones sellados, HFoffline, sin descargas. Hardware
compartido/noaislado y diferencia temporal con panel local expresamente declarados.

Runner/adaptador y tests deben completarse y manifiesto nuevo debe sellar
protocolo/código/peso/mapeos/índices/imagen antes de cualquierdespacho. Esta
especificación no cuenta como experimento iniciado. PrimerFMD42/f0 auditado
desbloquea resto; fallo bloquea dependientes, no se reutiliza colaNeshov fallida.
Registrar latencias/predicciones/error/ambiente/estados y hashes. Auditar todas
las llamadas antes de resúmenes; no inferenciaestadística ni margen de pérdida
aceptable elegido tras observar datos. Reportar victorias y derrotas.
