# Despacho HyTexNet adaptado, 02-11

Especificación científica inmutable: PROTOCOLO_HYTEX_ADAPTACION_FMD_2026-11-02.md.
Autorización: continuar comparadores reproducibles autónomamente, con elecciones
locales y adaptaciones declaradas, sin cambiar el panel94 cerrado ni repetir fallos.
No es reintento deNeshov ni de paridadDenseNet histórica.

Implementación: src/hytex_online_adapter.py, src/hytex_reference.py y
src/hytex_fixed_training.py. Pipeline propio completo, FP32, DenseNetoffline
estricto num_classes0/globalpooltimm, descriptor514CPU, concatenación1538 y
cabeza256CPU. Fuente/render permiten revisar ecuaciones; tests no acreditan
igualdad numérica con autores sin salidas de referencia.35tests pasan de
descriptor/adaptador/training/runner/auditoría/dispatcher. No se inspeccionó F1
nuevo para fijar entrenamiento. Lectura/versiones de códigoTimmlocal verificados.

Preparador scripts/prepare_hytex_fmd_queue.py verifica1000imágenes,15particiones
FMD de preflight previo, clases y pesosDenseNet locales. Guarda preflight.json
y manifest.json en results/analysis/hytex_fmd_external_queue_20261102_v1/.
Manifiesto sella hashes de protocolo/código/pesos/índices/entorno; no editar
fuentes selladas tras despacho. Toda etapa usa laneGPU/lockglobal para excluir
competencia propia durante fitCPU y benchmark. CPU2hilos, ventana12h, timeouts
7200/1800/14400/300s por etapa; procesos propios monitorizados por dispatcher.

Cada condición: extracción800fit batch1→consistencia primeros/últimosfit y
vectoresguardados→head100épocas→200llamadas externas→auditoría. Misma ruta
features física/entrenamiento, sin comparación con embeddings archivados. Primera
condición auditada habilita14restantes. Un fallo requires_review bloquea sus
dependientes; no retry/relajación ni omitir casos. Guardar los vectores antes de
decidir fidelidad, con umbral1e-4. No descargas de checkpoint.

Auditoría reutiliza exclusivamente funciones genéricas de recibos y llamadas
del runnerNeshov, sin ejecutar modeloNeshov ni tocar su cola fallida. Predicción,
F1 y tiempo derivados de las mismas llamadas. Método debe rotularse
HyTexNet adapted; local fixed configuration en todos los resúmenes.

Al terminar15condiciones auditar3000llamadas, comparar cada una con ambos heads
locales de la misma semilla/fold, mantener reservas y mostrar deltas adversos.
No medias completas deFMD mientras falte una condición. Ampliación de otros
datasets solo con preflight/manifiestos propios; no presentar esteFMD como seis
datasets ni como reproducción de porcentajes publicados deHyTexNet.
