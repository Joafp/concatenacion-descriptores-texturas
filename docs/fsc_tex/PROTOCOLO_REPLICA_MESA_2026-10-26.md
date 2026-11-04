# Réplica de desarrollo: protocolo fijado antes de las corridas

Fecha: 26 de octubre de 2026. Se continúa el plan autorizado por el autor. Esta especificación se guarda antes de iniciar las cinco condiciones nuevas; no es una preinscripción independiente ni convierte benchmarks previamente observados en datos ciegos.

## Cobertura y estimando

- FMD: semillas 42, 123 y 2026, partición externa SGKF de cinco pliegues, pliegue 0; únicamente sus 800 imágenes de entrenamiento se usan para desarrollo. No se evalúan las 200 de test de cada condición.
- Outex13Official1360: semillas 123 y 2026, entrenamiento oficial 1 de 680 imágenes. La condición de semilla 42 y su control presupuestado ya existen y se preservan, sin repetirlos ni sobrescribirlos.
- Se mantiene una evaluación productora de tres pliegues y tres internos. Cada imagen de desarrollo recibe una predicción OOF por política. Los índices y grupos deben ser disjuntos dentro de cada partición.
- La semilla afecta conjuntamente particiones, sorteos, SVM y SVD; en FMD también cambia el subconjunto externo de entrenamiento. No se interpreta como una ablación de inicialización aislada ni como tres nuevos datasets independientes.

## Método y controles congelados

Se conservan los 22 bloques, el perfil compartido de adquisición, SVM C=1, ajuste de escalas desde entrenamiento, N-gramas impl1 con 8.192 bins y SVD de 256 componentes ajustada dentro de cada partición. Solo se reutilizan conteos sin etiquetas y embeddings congelados; no se entrena una red ni se mide GPU en estas corridas.

Se mantienen presupuestos 15/30/60/120 ms, cuantiles 0,1/0,25/0,5, quince votos del ensamble de diversidad, subconjuntos de cuatro bloques y poda de hasta tres miembros únicos. Se conserva beta=8 y lambda=0,25 de la receta archivada. Las variantes completo, marginal y relevancia no se modifican según el resultado de la réplica.

Se ejecutan las implementaciones existentes en cuatro etapas: pool emparejado y controles de concatenación; ensambles de Carlos; híbrido completo/podado; control estático presupuestado. Este último enumera todos los ensambles de hasta tres miembros del pool de individuales y diversidad, con su selección interna propia. La adaptación de entrada al runner estático cambia únicamente el directorio del híbrido, no su selector. No se presenta como GFS sobre todas las concatenaciones.

## Registro y criterios de salida

El archivo `configs/fsc_tex/replication_mesa_20261026.json` fija las cinco condiciones, parámetros y rutas. Antes de ejecutar se guardan comandos, hashes del código y documento de protocolo en `frozen_protocol.json`. Las etapas comprueban que las fuentes no cambien; se conserva un log y un estado por etapa. Se permiten dos procesos de cómputo simultáneos y dos hilos por proceso. Una etapa fallida no se reintenta automáticamente ni se rellena con otra semilla. El límite de seguridad es 30 minutos por etapa, sin interpretar ausencia temporal de logs como fracaso científico.

El resultado se considera completo solo cuando las cuatro etapas terminan, los metadatos indican `complete` y la auditoría verifica cobertura, índices, rutas, predicciones, uniones de bloques y métricas desde archivos guardados. Se conservan todos los presupuestos, casos base, derrotas e incumplimientos de presupuesto. No se recomienda retrospectivamente el punto favorable ni se introduce margen de no inferioridad.

La comparación es descriptiva: macro-F1 OOF reunido, exactitud, adquisición media proyectada, llamadas y cumplimiento por pliegue. Primero se separan condiciones y semillas, después se resumen por dataset si la cobertura está completa. Dos datasets no justifican nuevos contrastes confirmatorios entre dominios. El perfil de costos común permite una comparación bajo el modelo fijado; no es un cronometraje de FMD u Outex.

El PDF y los resultados anteriores permanecen como corte histórico hasta incorporar únicamente resultados terminados y auditados. Esta réplica aborda estabilidad y cobertura; no cierra por sí sola medición física, reconciliación KTH, GFS ni entrega pública completa.
