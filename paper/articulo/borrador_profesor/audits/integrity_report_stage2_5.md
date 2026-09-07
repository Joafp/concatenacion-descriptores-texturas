# Informe de integridad — actualización Outex oficial

Fecha: 2026-08-11  
Manuscrito: *Selección y concatenación de descriptores heterogéneos para la
clasificación de texturas*  
Estado: **PASS AFTER CORRECTION**

## Cobertura verificada

- DTD, FMD y CUReT: 54 condiciones externas, 216 evaluaciones principales,
  5.400 subconjuntos aleatorios y 54 controles top-k.
- Outex_TC_00013: 1.360 BMP RGB legibles, 68 clases con 20 imágenes cada una,
  IDs 000000--001359, sin duplicados y con partición oficial 680/680.
- Veinte matrices de descriptores de Outex con 1.360 filas, etiquetas y orden
  alineados al manifiesto oficial.
- Reproducción exacta de RGB Pixel N-grams: exactitudes 0,963235 y 0,952941.
- Concatenación n-grama + 20 bloques: exactitud 0,969118, macro-F1 0,968649;
  IC95 % pareado [-0,008824; 0,020588] y McNemar exacto p=0,584665.
- Veinticuatro pruebas automatizadas relevantes aprobadas.
- Flujo general Outex completo: dos condiciones, ocho evaluaciones principales,
  200 controles aleatorios y dos controles top-k.

## Controles metodológicos

- La selección de Outex usa cuatro folds internos construidos solo dentro de
  las 680 imágenes oficiales de entrenamiento.
- El test oficial no interviene en vocabulario, selección, parada ni ajuste.
- Una única partición no se trata como una muestra de splits: el analizador
  omite deliberadamente Wilcoxon e intervalos entre splits cuando n=1.
- La mejora de cuatro aciertos del n-grama concatenado se presenta como mejora
  puntual, no como superioridad estadística.
- El costo informado cubre ajuste sobre embeddings precalculados, no el costo
  de extracción de los backbones ni la búsqueda completa.

## Advertencias que deben conservarse

- Los splits repetidos de DTD y FMD no son réplicas científicas independientes.
- CUReT contiene dos direcciones complementarias dependientes.
- Top-k reutiliza el presupuesto k de GFS y es un control de composición.
- Los descriptores clásicos reciben gris y los aprendidos RGB; esta asimetría
  limita conclusiones causales sobre familias.
- Falta una URL pública archivada del código antes de la entrega definitiva.
