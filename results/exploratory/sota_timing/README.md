# Tiempo de ejecución de los métodos de la literatura

Réplica de los métodos publicados con los que se compara la tesis, medidos en la
misma máquina que nuestros métodos (RTX 5060 Ti, WSL2, 8 hilos de CPU), para
poder comparar exactitud y costo bajo las mismas condiciones.

## Qué se mide

- **Lectura y decodificación** de las imágenes: una sola vez, por separado,
  porque la lectura desde `/mnt/d` en WSL es lenta y taparía el costo de las redes.
- **Extracción** de cada descriptor desde las imágenes ya en memoria: lotes de
  32, 4 *workers*, un lote de calentamiento que no se cuenta y
  `torch.cuda.synchronize` antes de parar el reloj. Los descriptores clásicos
  usan 8 procesos. Cada extracción se verifica contra los embeddings guardados
  (coseno mínimo); `mae_base` no coincide porque enmascara al azar en inferencia.
- **Clasificadores** de scikit-learn en un hilo de CPU; los MLP en la GPU.
- **Entrenar** = leer y decodificar + extraer todo lo que el método necesita
  para entrenarse + seleccionar + ajustar. **Predecir** = milisegundos para una
  imagen nueva: leerla, extraer solo los descriptores que usa el modelo final y
  clasificarla.

## KTH-TIPS2-b (protocolo RADAM: 3 muestras físicas entrenan, 1 prueba)

Media de las cuatro particiones.

| Método | Clasificador | Exactitud | Publicada | Entrenar | Predecir |
|---|---|---:|---:|---:|---:|
| Scabini 2025 | KNN | 0,9217 | | 42 s | 9,0 ms |
| Scabini 2025 | LDA | 0,9432 | | 42 s | 8,9 ms |
| Scabini 2025 | SVM | 0,9444 | | 42 s | 8,9 ms |
| Scabini 2025 | media de los tres | 0,9364 | 0,937 | 43 s | 9,1 ms |
| Neshov 2025 | MLP | 0,9303 | 0,968 | 63 s | 8,9 ms |
| Top-4 | SVM | 0,9575 | | 1956 s | 154 ms |
| Top-4 | ResMLP | 0,9596 | | 2045 s | 151 ms |
| Ens. diversidad | SVM | 0,9573 | | 2084 s | 178 ms |
| Ens. diversidad | ResMLP | 0,9585 | | 2154 s | 172 ms |
| Completa-22 | SVM | 0,9609 | | 1939 s | 404 ms |
| Completa-22 | ResMLP | 0,9487 | | 1928 s | 404 ms |

- Scabini reproduce el valor publicado. Neshov no: con su receta transcrita
  queda 3,8 puntos abajo (0,939 en CPU).
- Extraer los 21 bloques de la biblioteca cuesta 1891 s; Gabor (788 s),
  DINOv2-L (503 s) y DINOv2 (159 s) son el 77 %. Top-4 siempre usa
  `beitv2_base_final`, `dinov2` y `dinov2_large`, por eso predice en 150 ms.

## Scripts

```bash
# en WSL, con el entorno de GPU
python src/time_kth_extraction.py        # extraction_times.json
python src/benchmark_kth_methods.py      # method_runs.csv, method_summary.csv
python src/summarize_kth_timing.py       # timing_table.csv
```
