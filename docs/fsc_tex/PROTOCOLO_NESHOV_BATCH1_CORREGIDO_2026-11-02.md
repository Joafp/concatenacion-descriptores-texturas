# Neshov adaptado: nueva extracción individual coherente

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent.
- Origin Mode: corrección autorizada y nueva evaluación prospectiva.
- Origin Date: 2026-11-02, America/Asuncion.
- Verification Status: protocolo prospectivo, sin resultados al redactarse.

El diagnóstico `results/analysis/neshov_batch_parity_diagnostic_20261102_v1`
reprodujo el error original, 0,0039382 y 0,0055108 entre lote 8 y lote 1.
Ambos regímenes fueron exactamente repetibles entre dos llamadas de su mismo
tamaño. Esto identifica una dependencia de la forma del lote en ese entorno;
no identifica todavía el kernel ni demuestra equivalencia con el código original.

La evaluación nueva extrae **una imagen de entrenamiento por llamada**, como
la ruta de inferencia ya fijada. No se reemplazan pesos, capas, cabeza, semillas,
particiones, presupuesto de 100 épocas, precisión ni cronómetro. Es una nueva
versión de la adaptación, no una continuación de la corrida fallida y no una
reproducción del porcentaje publicado. Las características entrenadas con lote 8
del intento fallido no se reutilizan. Antes de entrenar, guardar y comparar
primera y última imagen fit reextraídas con la misma ruta lote 1; mantener el
umbral absoluto 1e-4 y guardar ambos vectores, errores e índices. El gate previo
de lote 8 frente a lote 1 falló y permanece como evidencia, no se declara pasado.

Conservar las 15 particiones FMD del manifiesto anterior, mismas imágenes, pesos,
versiones, semillas y cuatro etapas. La primera condición completa habilita las
demás; un fallo nuevo detiene sus dependientes y requiere revisión. No usar test
para seleccionar implementación, características o umbral. Lock GPU global,
CPU dos hilos, sin otros fits o benchmarks concurrentes. Archivos nuevos con
hashes, predicciones y tiempos de las mismas llamadas, más auditoría completa.

Para reproducir las cifras originales del paper hace falta otro protocolo: FMD
allí usa diez repeticiones de validación cruzada de diez pliegues, no nuestras
3 semillas × 5 pliegues; sus cifras son accuracy, no automáticamente macro-F1.
Código de autores, índices exactos y algunas elecciones siguen sin verificarse.
No reclamar equivalencia ni ajustar para alcanzar el número publicado.
