# Continuación después del panel local

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: continuación técnica y preparación, no nueva evaluación inferencial.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: ANALYZED para inventario y replay; ampliación externa pendiente.
- Version Label: post_panel_v1.

## Alcance vigente

El autor pidió actualizar el plan y continuar. Se conserva su delegación de
decisiones técnicas rutinarias. No se modifica manuscrito, protocolo congelado,
selección OOF, biblioteca, presupuesto, semillas ni particiones del panel cerrado.
Sin commits/push, VisTex, contactos a autores, descargas grandes o retries de
fallos científicos. Ningún protocolo retrospectivo se presenta como prerregistro.

## 1. Panel local: completo en cobertura, con reservas

Fuente: results/analysis/blocker_resolution_20261101/full_panel_online_v1/.
94 condiciones únicas,470 filas condición-método,60 resúmenes por dataset/head/
método;362640 llamadas primarias y9400 adicionales DTD por separado. F1 y ms
de las mismas llamadas. Sin benchmarks activos al revisar esta continuación.
No se repiten estas condiciones ni se reemplazan sus tablas por otra versión.

Persisten episodio extremo DTD/SVMofficial7, nueva representación autorizada
Outex/Soil, no equivalencia KTH con cascada histórica y hardware compartido con
una repetición por imagen. No inferencia estadística global ni victoria universal.

## 2. Comparadores externos: prioridad y estado

| Orden | Trabajo | Estado real | Próximo entregable / condición de salida |
| --- | --- | --- | --- |
| 1 | Neshov BEiTv2 multicapa + MLP | Adaptación de desarrollo FMD/42 completada; replay actualizado pasa | Especificación versionada de adaptación externa y adaptador de inferencia archivo-a-clase, con tests de capas, transformaciones, cabeza y cronómetro; sin medir hasta fijar cobertura y entrenamiento externo |
| 2 | Scabini | Inventario de arquitecturas, no réplica completa | Matriz de checkpoint, entrada, pooling, clasificador y particiones sustentada en fuente primaria; no asumir equivalencia por nombre del backbone |
| 3 | RGB Pixel N-grams | Bloque del proyecto disponible, método completo sin cerrar | Distinguir descriptor/SVD local de receta publicada; registrar componentes faltantes |
| 4 | AsTexNet / HyTexNet y demás inventario | Implementación completa no verificada | Mantener pendiente hasta obtener receta/checkpoint suficientes; no sustituir por componente aislado |

Neshov va primero por disponibilidad del modelo y cabeza implementados, no por
su F1 observado. No elegir capas, interpolación, épocas o checkpoint por test.
La adaptación al benchmark común no se rotula reproducción de porcentajes del paper.

## 3. Trabajo realizado en esta continuación

Reauditadas las salidas existentes del piloto, sin entrenamiento ni extracción:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 CUDA_VISIBLE_DEVICES= \
.venv-confirmatory/bin/python scripts/audit_neshov_fmd_development.py \
  --run results/exploratory/reference_papers/neshov_fmd_development_20261028 \
  --output results/analysis/neshov_fmd_readiness_20261102_v1
```

Exit0:800 predicciones y logits de3 cabezas reproducidos exactamente; fuentes,
protocolo, pesos y salidas verificados por hashes. No reextracción independiente
del backbone, test externo, latencia física ni porcentajes originales reproducidos.
Macro-F1 OOF de desarrollo0.945993, no emparejable con ms del panel externo94.
Artefactos nuevos: summary.json y matched_quality.csv en ese directorio.

Tests: PYTHONPATH=src y2hilos,12passed en test_neshov_beit_reference.py,
test_neshov_reference_training.py y test_matched_reference_quality.py.
La primera invocación de tests omitió PYTHONPATH y falló al recolectar imports;
se corrigió solo el entorno del comando, sin cambios de método ni experimentos.

Verificación web de las dos páginas MDPI referenciadas en el plan27-10:
HTTP429 en ambas; no se insistió ni se descargaron recursos. No se transforma
esta indisponibilidad en verificación nueva de sus recetas. Las decisiones
existentes proceden de las notas de lectura y protocolos locales identificados.

## 4. Secuencia de implementación siguiente

1. Preparar adaptador Neshov separado del benchmark local congelado: carga estricta
   offline, backbone en eval, cuatro capas2/5/8/11 desde1, GAP sin CLS, vector3072,
   resize224 bilineal/ImageNet y cabeza FC64/BN/ReLU/Dropout.2/FC(K).
2. Tests sintéticos y de replay sobre las cabezas ya guardadas; no volver a ejecutar
   entrenamiento, smoke fallido histórico ni extracción como parte de un test.
3. Redactar especificación de evaluación externa común: manifiesto/splits exactos,
   entrenamiento solo en fit, época final, seeds, número de condiciones, outputs,
   timeout y dispositivo. Marcar como propuesta hasta cerrar el alcance; el piloto
   de800 imágenes no autoriza silenciosamente entrenar o evaluar otro panel.
4. Preflight sin modelos: verificar hashes, disponibilidad offline, índices,
   dimensiones, recursos y espacio, directorios nuevos y exclusividad GPU.
5. Solo después de congelar el protocolo externo aplicable, entrenar/medir según
   ese protocolo: batch1 archivo-a-clase, calidad y tiempo de mismas llamadas,
   calentamiento excluido, sin caché de features compartida entre competidores.
   Un solo benchmarkGPU; CPU2hilos; proceso/timeout/logs y fallo→requires_review.
6. Auditar cobertura completa antes de medias. Estadística y comparaciones entre
   datasets requieren familia/estimando explícitos; no reciclar p-valores previos.
7. Escritura/figuras del manuscrito y paquete final permanecen fuera de esta
   autorización operativa. El análisis descriptivo puede vivir en results/analysis.

## 5. Monitoreo y criterio de avance

Este archivo sustituye el siguiente paso operativo antiguo, no los protocolos
ni resultados históricos. El heartbeat debe consultar este plan además del
registro nocturno; no repetir comprobaciones de94 celdas como si fueran trabajo
experimental pendiente. Avanzar preparación/adaptadores/tests dentro del alcance,
registrar cambios materiales y permanecer silencioso si no hay novedad accionable.
No hay corridas externas despachadas por esta actualización. No prometer ETA
global antes de un piloto físico y de fijar el tamaño del panel de papers.

## 6. Adaptador online preparado, seguimiento 02-11

Implementados src/neshov_online_adapter.py y tests/test_neshov_online_adapter.py.
Pasos1–2 avanzados: interfaz archivo-a-clase batch1, carga offline estricta de
backbone y cabeza con SHA256 exigidos, extractor FP32 en dispositivo declarado,
MLP en CPU, eval y sin gradientes. Usa capas/preprocesamiento del prototipo sin
alterarlo. Cronómetro incluye lectura/decodificaciónRGB, transformación, envío,
extracción, transferencia a CPU y clasificación; carga/warmup/serialización fuera.
No caché de features, retries, entrenamiento ni fallback de pesos. Devuelve
predicción y logits de la misma llamada; no acepta F1 histórico.

19tests pasan (7casos nuevos más12existentes), PYTHONPATH=src y2hilos/CPU.
Cubren orden del cronómetro respecto a decode y sync, mapeo de clases explícito,
dimensión3072, archivo ausente, checksum antes de carga y ausencia de reutilización
de features. Son tests sintéticos: no acreditan todavía fidelidad real online,
calidad externa ni latencia del método. Replay real del piloto sigue siendo la
reauditoría de800 logits anterior, no una prueba del extractor online nuevo.

SHA256 adaptador:354d7ffe94348e5f3cc6a21c78a9506aaa70949728c981d7439294d00bc9bd06.
SHA256 tests:02383b1ebc74ca8fc4c9bf5340e5d13a9095b56ef4ba1abf42df0e868856cefb.
Siguiente: especificación externa versionada y preflight de recursos/particiones.
No ejecutar el adaptador en imágenes del test ni entrenar cabezas externas antes
de fijar el protocolo aplicable. Este seguimiento no modifica el panel94 cerrado.

## 7. Ampliación explícita autorizada por el autor

Nueva petición: replicar todos los papers reproducibles y medir F1/latencia
para comparar con nuestro método, incluidos resultados adversos. Siguiente plan:
PLAN_REPLICAS_PAPERS_2026-11-02.md. Protocolo específico inicial:
PROTOCOLO_NESHOV_PANEL_COMUN_2026-11-02.md. Esta autorización supera la limitación
anterior a preparación/piloto800, pero no permite ejecutar sin runner probado y
manifiesto congelado. Objetivo47condiciones externas por sistema completo con
cabeza propia, no94copias bajo nombres de nuestros dos clasificadores.
Siguiente entregable implementable: runner y preflight Neshov, primer casoFMD42/f0
por orden fijo, sin modificar corridas locales cerradas ni manuscrito.

Seguimiento: preflight FMD externo completado,15condiciones/1000imágenes únicas
verificadas y3000llamadas planificadas, sin ejecutar modelos. Registro en
results/analysis/neshov_fmd_external_preflight_20261102_v1/manifest.json.
14tests pasan de preparación y adaptador; runner sigue pendiente. Prioridad
temática confirmada: sistemas de concatenación/fusión del directorio de referencias.

Siguiente estado operativo vigente: HyTexNetADAPTADO en cola nueva
results/analysis/hytex_fmd_external_queue_20261102_v1/, worker56637/sesión18682,
iniciado11:21UTC, primerextractor56645.35tests pasan. Revisar PLAN_REPLICAS_PAPERS
y DESPACHO_HYTEX_ADAPTADO_2026-11-02.md, no duplicarGPU/fit. Neshov queda fallido
sinretry. No contar15condiciones en cola como completas; auditorías requeridas.
