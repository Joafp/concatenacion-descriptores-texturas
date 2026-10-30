# Tiempo de ejecución de los métodos de la literatura

Réplica de los métodos publicados con los que se compara la tesis, medidos en la
misma máquina que nuestros métodos (RTX 5060 Ti, WSL2, 12 hilos de CPU), para
comparar exactitud y costo en las mismas condiciones.

| Método | Qué es | Datasets medidos |
|---|---|---|
| Scabini 2025 (*J. Imaging*) | BEiTv2-B/16 IN-21k congelado; KNN, LDA y SVM lineal sin ajustar; reporta la media de los tres | KTH-TIPS2-b, DTD, FMD |
| Neshov 2025 (*Electronics*) | BEiTv2 capas 2, 5, 8 y 11 congelado; MLP 64-BN-ReLU-Dropout(0,2), 100 épocas | KTH-TIPS2-b, DTD, FMD |
| HyTexNet 2026 (*Knowl.-Based Syst.*) | Histogramas HyTex (514-D) + DenseNet-121 con el último bloque ajustado, a 128×128 | DTD, KTH-TIPS2-b |

Nuestros métodos (Top-4, ensamble por diversidad y Completa-22) se midieron en
los mismos tres datasets, con el protocolo de la tesis. Outex13 (Scabini y los
nuestros) está pendiente: el sitio oficial de Outex no responde y hacen falta
las imágenes del ZIP de la tesis (ver al final).

## Qué se mide

- **Lectura y decodificación** de las imágenes: una sola vez y por separado. Se
  verifica cada archivo contra el SHA-256 del manifiesto. Leer desde `/mnt/d` en
  WSL es lento (5 a 12 ms por imagen) y taparía el costo de los métodos livianos.
- **Extracción** de cada descriptor desde las imágenes ya en memoria: lotes de
  32, 4 *workers*, un lote de calentamiento que no se cuenta y
  `torch.cuda.synchronize` antes de parar el reloj. Cada extracción se verifica
  contra los embeddings guardados; en DTD y FMD, `beitv2_base_final` (mismo
  checkpoint que Neshov) coincide con coseno 1,0, lo que confirma el orden de las
  imágenes y el preprocesamiento. De los 21 bloques coinciden todos salvo MAE,
  que enmascara parches al azar (coseno mínimo 0,975 a 0,980), y DINOv2-L en
  DTD (coseno medio 0,99999, mínimo 0,9975: redondeo de la GPU en pocas
  imágenes).
- **Clasificadores** de scikit-learn en un hilo de CPU; MLP y HyTexNet en la GPU.
- **Entrenar** = leer y decodificar todas las imágenes + extraer lo que el método
  necesita + seleccionar + ajustar, en segundos, para una partición.
  **Predecir** = milisegundos por imagen nueva: leerla, extraer solo lo que usa
  el modelo final y clasificarla. *Sin lectura* descuenta leer y decodificar.

## Protocolos

| Dataset | Protocolo (el de los papers) | Evaluaciones |
|---|---|---|
| KTH-TIPS2-b | RADAM: 3 muestras físicas entrenan, 1 prueba | 4 |
| DTD | 10 particiones oficiales; se ajusta con train + validación (como la tesis), sin las copias idénticas de imágenes de test | 10 |
| FMD | 10 repeticiones de validación cruzada estratificada de 10 folds, semilla 42·r (Neshov) | 100 |

Nuestros métodos usan las condiciones externas del estudio k=4 de la tesis: las
mismas particiones en KTH y DTD, y en FMD los 5 folds de `StratifiedGroupKFold`
con semilla 42 (800 imágenes de entrenamiento y 200 de prueba, contra 900 y 100
de los papers). Sus exactitudes reproducen las de `../k4/README.md`.

Neshov no dice para qué usa la validación de DTD, así que su MLP también se
ajustó solo con train (*solo train*). HyTexNet usa la validación de DTD para
parar el entrenamiento; en KTH aparta una de las tres muestras de entrenamiento
para elegir las épocas y después reentrena con las tres.

## Resultados

Exactitud media; desvío entre evaluaciones.

### KTH-TIPS2-b

| Método | Clasif. | Exactitud | Publicada | Entrenar | Predecir | Sin lectura |
|---|---|---:|---:|---:|---:|---:|
| Scabini 2025 | media de 3 | 0,9364 ± 0,034 | 0,937 | 43 s | 9,1 ms | 4,0 ms |
| Scabini 2025 | SVM | 0,9444 | | 42 s | 8,9 ms | 3,8 ms |
| Neshov 2025 | MLP | 0,9303 ± 0,038 | 0,968 | 63 s | 8,9 ms | 3,8 ms |
| HyTexNet 2026 | MLP | 0,8500 ± 0,030 | n. c. | 89 s | 7,6 ms | 2,5 ms |
| Top-4 | SVM | 0,9575 ± 0,034 | | 1956 s | 154 ms | 149 ms |
| Top-4 | ResMLP | 0,9596 ± 0,029 | | 2045 s | 151 ms | 146 ms |
| Ens. diversidad | SVM | 0,9573 | | 2084 s | 178 ms | 173 ms |
| Ens. diversidad | ResMLP | 0,9585 | | 2154 s | 172 ms | 167 ms |
| Completa-22 | SVM | 0,9609 ± 0,008 | | 1939 s | 404 ms | 399 ms |
| Completa-22 | ResMLP | 0,9487 | | 1928 s | 404 ms | 399 ms |

### DTD

| Método | Clasif. | Exactitud | Publicada | Entrenar | Predecir | Sin lectura |
|---|---|---:|---:|---:|---:|---:|
| Scabini 2025 | media de 3 | 0,7883 ± 0,009 | 0,791 | 90 s | 16,3 ms | 4,4 ms |
| Scabini 2025 | SVM | 0,8178 | | 89 s | 16,1 ms | 4,3 ms |
| Neshov 2025 | MLP | 0,7993 ± 0,007 | 0,820 | 109 s | 15,6 ms | 3,8 ms |
| Neshov 2025 | MLP, solo train | 0,7701 ± 0,009 | 0,820 | 98 s | 15,6 ms | 3,8 ms |
| HyTexNet 2026 | MLP | 0,6141 ± 0,008 | 0,732 | 166 s | 15,1 ms | 3,2 ms |
| Top-4 | SVM | 0,8703 ± 0,008 | | 2761 s | 160 ms | 149 ms |
| Top-4 | ResMLP | 0,8624 ± 0,005 | | 2703 s | 163 ms | 151 ms |
| Ens. diversidad | SVM | 0,8748 | | 3019 s | 183 ms | 171 ms |
| Ens. diversidad | ResMLP | 0,8768 | | 2828 s | 183 ms | 171 ms |
| Completa-22 | SVM | 0,8654 ± 0,008 | | 2568 s | 441 ms | 429 ms |
| Completa-22 | ResMLP | 0,8637 | | 2505 s | 441 ms | 429 ms |

### FMD

| Método | Clasif. | Exactitud | Publicada | Entrenar | Predecir | Sin lectura |
|---|---|---:|---:|---:|---:|---:|
| Scabini 2025 | media de 3 | 0,9130 ± 0,020 | 0,909 | 14,6 s | 14,5 ms | 4,0 ms |
| Scabini 2025 | SVM | 0,9524 | | 14,4 s | 14,4 ms | 4,0 ms |
| Neshov 2025 | MLP | 0,9426 ± 0,021 | 0,967 | 19,4 s | 14,4 ms | 3,9 ms |
| Top-4 | SVM | 0,9820 ± 0,017 | | 439 s | 160 ms | 150 ms |
| Top-4 | ResMLP | 0,9750 ± 0,017 | | 507 s | 160 ms | 150 ms |
| Ens. diversidad | SVM | 0,9790 | | 467 s | 187 ms | 177 ms |
| Ens. diversidad | ResMLP | 0,9770 | | 539 s | 187 ms | 176 ms |
| Completa-22 | SVM | 0,9650 ± 0,024 | | 434 s | 428 ms | 417 ms |
| Completa-22 | ResMLP | 0,9560 | | 432 s | 428 ms | 417 ms |

Los métodos de la literatura se evalúan en 100 folds de 10×10 y los nuestros en
5 folds con menos imágenes de entrenamiento, así que las exactitudes de FMD no
son de las mismas particiones.

La lectura de las imágenes es 67 s del tiempo de entrenar en DTD, 24 s en KTH y
10 s en FMD.

## Lectura

- **Scabini se reproduce** en los tres datasets (diferencias de 0,1 a 0,4
  puntos). **Neshov no**: con su receta transcrita queda 2 a 4 puntos debajo en
  los tres, siempre en la misma dirección.
- **HyTexNet**: con el protocolo de su paper la réplica da 0,987 ± 0,006 en KTH
  (cinco sorteos de 2 poses, 3 iluminaciones y 6 escalas de las cuatro
  muestras; publican 0,998 en una corrida y 0,991 ± 0,001 en cinco), así que el
  método está bien transcrito. Con el protocolo RADAM, que deja una muestra
  física fuera, baja a 0,850: su 0,998 mide reconocer la misma muestra física
  vista en entrenamiento. En DTD queda 12 puntos debajo de lo publicado; parte
  es la entrada de 128×128, que el paper fija para todo: a 224×224 sube a
  0,6828 ± 0,010 (entrenar 262 s, predecir 8,1 ms sin lectura), todavía 5
  puntos abajo.
- **Exactitud**: nuestros métodos superan a los de la literatura en los tres
  datasets. En DTD, con las mismas particiones, Top-4 con SVM da 0,870
  contra 0,788 de Scabini y 0,799 de Neshov; en KTH, 0,958 contra 0,936 y
  0,930. En FMD la ventaja es parecida (0,982 contra 0,913 y 0,943), pero los
  protocolos difieren.
- **Costo**: los tres métodos de la literatura usan una sola red y predicen en
  2,5 a 4,4 ms por imagen sin contar la lectura. Nuestros métodos extraen 4 a 22
  bloques: Top-4 predice en ~150 ms (lo dominan DINOv2 y DINOv2-L) y Completa-22
  en 400 a 430 ms. Entrenarlos cuesta ~2000 s en KTH, ~2700 s en DTD y ~450 s
  en FMD, porque hay que extraer los 21 bloques para el ranking; Gabor, DINOv2-L
  y DINOv2 son más del 70 % de esa extracción. Predecir con Top-4 cuesta unas
  35 a 40 veces lo que cuesta con un método de una sola red.

## Decisiones de la réplica de HyTexNet

El paper no publica código ni da tasa de aprendizaje, lote, épocas ni
aumentación. Se usó lote 32, sin aumentación, inicialización de Keras en la
cabeza, BatchNorm congelado fuera del bloque ajustado y Adam con la tasa que
mejor valida en la primera partición entre 1e-3 y 1e-4 (DTD: 1e-4, 110 s; KTH:
1e-3), con parada temprana de paciencia 8 sobre un máximo de 50 épocas. La
elección de la tasa se hace una vez y no está sumada en *Entrenar*. El
descriptor HyTex se verificó contra la Tabla 1 del paper (umbral T75).

## Pendiente: Outex13

Los embeddings guardados de Outex13 ya están en el repo (para verificar la
extracción). Con las imágenes del ZIP `Outex_TC_00013-20260120T014101Z-3-001.zip`
descomprimidas en `data/confirmatory_sources/Outex13/` (debe quedar
`Outex_TC_00013/images/000000.bmp`):

```bash
python src/time_extraction.py --dataset Outex13Official1360 \
  --image-root data/confirmatory_sources/Outex13
python src/benchmark_sota_methods.py --dataset Outex13Official1360
python src/benchmark_our_methods.py --dataset Outex13Official1360
python src/summarize_timing.py --dataset all
```

## Scripts

En WSL, con el entorno de GPU. Las imágenes van en `data/` según
`docs/DATASETS.md`; los rasgos que no están guardados se escriben en
`<carpeta de embeddings>_sota/`.

```bash
python src/time_extraction.py --dataset DTD --descriptors \
  beitv2_base_final beitv2_base_multilayer beitv2_scabini   # extraction_times.json
python src/benchmark_sota_methods.py --dataset DTD          # sota_runs.csv: Scabini y Neshov
python src/replicate_hytexnet.py --dataset DTD              # hytexnet_runs.csv
python src/replicate_hytexnet.py --dataset KTHTIPS2b --kth-protocol paper  # control de la réplica
python src/benchmark_kth_methods.py                         # KTH: también Top-4, ensamble y Completa-22
python src/time_extraction.py --dataset DTD                 # los 21 bloques y los conteos de color
python src/benchmark_our_methods.py --dataset DTD           # our_runs.csv: Top-4, ensamble y Completa-22
python src/summarize_timing.py --dataset all                # timing_table.csv y timing_all.csv
```
