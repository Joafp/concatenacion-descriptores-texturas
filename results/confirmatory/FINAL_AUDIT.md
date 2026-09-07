# Auditoría experimental vigente

Fecha: 2026-08-11

## Bloque principal cerrado

- Datasets: DTD, FMD y CUReT.
- Clasificadores: SVM lineal y ResMLP.
- 54 condiciones externas y 216 evaluaciones principales.
- 5.400 subconjuntos aleatorios y 54 controles top-k.
- Sin claves duplicadas ni métricas obligatorias no finitas.

## Outex oficial

- Única fuente admisible: `Outex_TC_00013-20260120T014101Z-3-001.zip`.
- 1.360 imágenes RGB, 68 clases balanceadas, partición oficial 680/680.
- Veinte bloques completos y alineados al manifiesto canónico.
- RGB Pixel N-grams reproducido exactamente; concatenación de 21 bloques
  validada con predicciones persistidas.
- Integración al flujo general: una condición oficial por clasificador,
  selección interna restringida al entrenamiento y test consultado una vez.
- Resultado general completo: ocho evaluaciones principales, 200 controles
  aleatorios y dos controles top-k.
- No se calcula inferencia entre splits para Outex porque existe un único split
  oficial.

## Frontera interpretativa

La evidencia permite estudiar cuándo concatenar aumenta el desempeño y cuándo
seleccionar reduce dimensión. No demuestra que GFS, la heterogeneidad o la
concatenación completa sean universalmente superiores. La mejora puntual del
n-grama concatenado en Outex tiene incertidumbre compatible con cero.
