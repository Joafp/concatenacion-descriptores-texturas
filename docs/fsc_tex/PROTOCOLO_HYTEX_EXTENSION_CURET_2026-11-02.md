# Extensión prospectiva de HyTexNet ADAPTADO a CUReT

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: extensión autorizada a los seis datasets comunes, sin ajuste por F1.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: protocolo fijado antes de nuevas predicciones CUReT.
- Version Label: hytex_curet_adaptation_v1.

Hereda íntegramente PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md: dimensiones,
preprocesamiento128RGB, descriptor, backbone offlineFP32 congelado, cabezaCPU,
Adam.001/wd.0001/betas.9/.999/100épocas/batch32/shuffle42 y época final. No
modificar hiperparámetros por FMD. Modelo se rotulaHyTexNetadaptado, nunca réplica
de porcentajes delpaper. CUReT no implica nuevo clasificadorSVM/ResMLP duplicado.

Doscondiciones de las mismas dos direcciones alternantes del panel local,
semilla42/folds0y1:2806fit y2806test cada una,61clases,5612imágenes en total.
5612llamadas externas planificadas por sistema, una por imagen y condición.
Direcciones exactas e índices se leen de configs/estados locales verificados;
no se regeneran splits ni se seleccionan por resultado. Concordancia entre
ambos heads locales obligatoria. Preflight comprueba filas, cobertura completa,
clases/grupos, hashes de5612imágenes y manifiesto, y verdad de predicciones
archivadas contra labels de manifiesto. Son dos direcciones de UNdataset,
no réplicas independientes. Primera auditoría completa habilita segunda.

Runner HyTex existente se usa sin alterar fuentes deFMD. Nuevos preflight/cola/
salidas en hytex_curet_external_queue_20261102_v1/, con fuentes/pesos/protocolos/
versiones yargv sellados antes de carga. No reutilizarfeatures ni headsFMD.
Extraerfit batch1, comprobar primeros/últimosfit batch1→batch1 maxabs≤1e-4,
guardando vectores antes de aceptar. Error→requires_review y dependientes
bloqueados, no retry/relajar umbral/método; Neshov sigue separado y fallido.

Medir archivo-a-clase,5warmups deprimerfit excluidas, mismo sentido de etiquetas,
sin caché de features paraonline. CNNGPUresidente/descriptor yMLPCPU2hilos,
lockGPUglobal durante todas las etapas, sin trabajos competidores propios.
Timeouts7200/1800/14400/300s; ventana12h no corta una etapa ya iniciada antes
de suhardtimeout. Estado/proceso/logs/timestamps/ambiente y errores preservados.
Sin descargas, modificaciones del manuscrito, commits ni push.

Solo consolidar tras2auditorías/5612llamadas; reagregar F1/tiempos desde las
mismas llamadas y verificar hashes/cadenas de etapas. Emparejar contra ambos
heads locales y cinco métodos de iguales filas/dirección; mostrar pérdidas y
ganancias. Tiempos medidos en momentos distintos/hardwarecompartido: descriptivos,
sin claim de emparejamiento temporal aislado. No inferenciaestadística ni media
de seis datasets cuando solo hayaFMD/CUReT. FMD15cerrado no se repite.
