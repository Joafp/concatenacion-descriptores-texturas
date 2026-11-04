# Protocolo DeepLumina en FMD — adaptación auditable, 03-11-2026

## Estado y alcance

**Estado: receta congelada para una adaptación; ejecución no iniciada.** Esta
ficha no atribuye al código propuesto una reproducción del 90,15 % del artículo.
El artículo no enlaza una implementación y deja sin especificar semilla/índices
del split, archivo exacto de pesos/preprocesamiento de ResNet101 y varios
parámetros del ECOC/SVM. No se solicitaron materiales a los autores.

Objetivo de la futura prueba: incorporar un competidor **DeepLumina-adaptado**
al panel FMD común en las mismas imágenes de prueba que las mediciones locales
ya cerradas; obtener F1 macro, accuracy y latencia por llamada de las mismas
predicciones nuevas. No reejecutar ninguno de los cinco métodos locales.

## Evidencia del método original

Fuente primaria: Simon y Uma, *DeepLumina: A Method Based on Deep Features and
Luminance Information for Color Texture Classification*, 2022,
[DOI 10.1155/2022/9510987](https://doi.org/10.1155/2022/9510987), [texto del
artículo](https://pmc.ncbi.nlm.nih.gov/articles/PMC9023203/).

El artículo describe conversión RGB→YIQ, uso del canal Y junto con RGB,
extracción con ResNet101 preentrenada, capa `fc1000`, concatenación de rasgos y
clasificación SVM multiclase por ECOC con codificación `sparse random`. Declara
224×224×3 y un split aleatorio 80/20. Para FMD reporta **accuracy**
90,15 % ± 1,2; no reporta F1 macro ni identifica una semilla/índices públicos.
La tabla de arquitectura y la tabla de resultados indican `fc1000`; por eso no
se tratará el vector GAP de 2048 dimensiones como si fuese el rasgo del método.

La documentación oficial de MathWorks describe `sparserandom` como una matriz
ternaria aleatoria, aproximadamente `ceil(15 log2(K))` columnas, con
probabilidades 0,25/+1, 0,25/−1 y 0,5/0; descarta columnas vacías/no
separadoras y duplicadas o negadas, y conserva la matriz de mayor distancia
mínima entre filas entre 10.000 candidatas. También documenta decodificación
ECOC por pérdida ponderada (`lossweighted`) y pérdida hinge por defecto para
learners SVM ([`fitcecoc`](https://www.mathworks.com/help/stats/fitcecoc.html),
[`ClassificationECOC`](https://www.mathworks.com/help/stats/classificationecoc.html)).
El paper no identifica versión MATLAB, invocación/API, estado RNG ni parámetros
completos del learner. La receta de abajo fija estos elementos para que la
adaptación sea repetible, no para afirmar identidad con MATLAB.

## Recursos locales auditados (solo lectura)

| Recurso | Evidencia fijada | Evaluación |
|---|---|---|
| FMD original | `data/confirmatory_sources/FMD/original/FMD.zip`; SHA256 `254475ddb37bf0fe1383ff9ea61eb71042db33af1f9a9aa8747391a72135b8f8`; ZIP enumera 1000 imágenes RGB y 1000 máscaras; existen 1000 JPG en `data/confirmatory_sources/FMD/extracted/image` | Disponible localmente; no se descargó ni extrajo durante este preflight |
| Manifiesto de imágenes/clases | `results/confirmatory/sample_manifests/FMD.csv` (igual a `FMD_reextract.csv`); SHA256 `43f5d02a493763bff351e842d0ec29ac4fdcc9facccfa1364a028ed81d793984`; orden de clases: fabric, foliage, glass, leather, metal, paper, plastic, stone, water, wood | Verificados 1000 registros, 100 imágenes/clase, existencia y SHA256 de cada JPG |
| ResNet101 compatible por arquitectura/uso, no peso original | Cache local `timm/resnet101.a1_in1k`, revision `d90ce63ac1b05b22614f11dcea68fcedfc2c4dee`; `model.safetensors` SHA256 `1ba5b660e7c175b3c27c557fc7dc8b2815be830c516815b0155f61b403f27380` | Disponible offline; variante ImageNet de timm, **no** se ha demostrado que sean los pesos MATLAB del artículo |
| Embedding existente | `embeddings_confirmatory/FMD/resnet101.npy`, dimensión declarada 2048 (GAP); metadatos: Torch 2.12.1+cu126, RTX 4060 | No usar para este método: no es la capa `fc1000` y omite la ruta YIQ |
| Implementación original / MATLAB | No localizada en el barrido registrado; MATLAB no está disponible en el runtime WSL inspeccionado | Bloquea reproducción fiel; no bloquea una adaptación explícita |

Runtime WSL observado para la adaptación: Python 3.14.4; torch 2.13.0+cu130;
torchvision 0.28.0+cu130; CUDA runtime 13.0; timm 1.0.28; safetensors 0.8.0;
scikit-learn 1.9.0; NumPy 2.5.1; Pillow 12.3.0; SciPy 1.18.0. GPU visible:
NVIDIA GeForce RTX 4060 (1 dispositivo, consulta de estado solamente). El
manifiesto de corrida deberá confirmar estos valores al ejecutar y fallar
cerrado si difieren; no instalar, actualizar ni descargar dependencias/pesos
automáticamente.

## Receta congelada de la adaptación

1. **Datos y partición.** Usar exactamente las imágenes/labels/orden de
   `FMD.csv`. Para comparación en el panel común, cinco folds externos por cada
   semilla 42, 123 y 2026: 15 condiciones, 800 filas de fit y 200 de prueba por
   condición. Recuperar los row IDs de prueba del registro por-muestra ya
   cerrado (`results/analysis/overnight_f1_latency_20261028/summary_FMD_svm_s{42,123,2026}_online_v1/online_calls.csv`), deduplicando por `outer_fold,row_index`; fit es el complemento. Hashes de esos tres registros: 42=`4dec2fb2af1eda67da908a3e3f422f6658826a6fa4e7daeb5c46e8a7257b0c67`, 123=`ec86ba4bda4f0116bf3371787de15645642aa1fa1e76943dd55070fa94989b89`, 2026=`390eb98846c2c8854d8cb4c9c2654d3cd438657121fc57b151dab78b81ea2c0f`. Auditoría de solo lectura ya comprobó 15 folds con 200 IDs únicos, 20 imágenes/clase por test, folds disjuntos que cubren las 1000 filas por seed y hashes válidos de todas las imágenes. El preflight de cola todavía debe materializar los arrays exactos de fit/test en un manifiesto nuevo, verificar 800 complementarios y sellar sus hashes. Cualquier discrepancia → `requires_review`; no regenerar una partición alternativa.
2. **Backbone y rasgos.** Cargar offline y estrictamente el checkpoint timm fijado arriba; sin fallback ni pesos aleatorios. ResNet101 eval/FP32, dos pasadas independientes con los mismos pesos: RGB y YIQ-Y. Redimensionar cada imagen directamente a 224×224 con bicúbica (sin crop); RGB se convierte a float `[0,1]`. Calcular `Y=0.299R+0.587G+0.114B` según la ecuación impresa por el paper; replicar Y en tres canales para satisfacer la entrada RGB del backbone. Normalizar ambas entradas con media `(0.485,0.456,0.406)` y desviación `(0.229,0.224,0.225)`. Tomar los 1000 valores de la capa lineal final `fc` antes de softmax (equivalente funcional a `fc1000`): vector RGB 1000 + vector Y 1000 = 2000 dimensiones concatenadas, sin normalización extra. Interpolación bicúbica, pesos timm, replicación de Y y normalización ImageNet son decisiones explícitas de adaptación donde el artículo no permite identificar implementación idéntica.
3. **Clasificador ECOC-SVM.** Un único diseño sparse-random compartido entre condiciones, generado determinísticamente con semilla 42: K=10, L=`ceil(15 log2(10))`=50 columnas antes de filtrar; 10.000 candidatos ternarios con probabilidades −1/0/+1=`0.25/0.5/0.25`; descartar columnas sin ambos signos y duplicados/negaciones; retener el candidato con mayor distancia mínima `Δ(i,j)=0.5 Σ_l |m_il||m_jl||m_il−m_jl|` entre pares de filas (empate: primero generado). Guardar matriz exacta y SHA256. Ajustar un `sklearn.svm.LinearSVC` por columna, solo con clases ±1 (0 se ignora), `C=1`, `penalty=l2`, `loss=squared_hinge`, `dual=True`, `fit_intercept=True`, `class_weight=None`, `tol=1e-4`, `max_iter=10000`, `random_state=42`; sin escalado de rasgos ni búsqueda de hiperparámetros. Decodificar la clase por mínima pérdida media hinge ponderada sobre las columnas activas; empate al menor índice de clase. Guardar las 50 márgenes binarios y las 10 pérdidas ECOC de cada llamada. Solver, C, RNG y reglas de empate quedan fijados como elecciones de adaptación, no son recuperables de la publicación.
4. **Ajuste/aislamiento.** Extraer rasgos de fit y entrenar 15 cabezas (una por condición) en CPU con dos hilos. El backbone queda congelado. No extraer ni ajustar durante la medición online. No reutilizar embeddings 2048 existentes ni cachear rasgos de prueba. Un solo benchmark GPU, lock global existente y nada de extracción/fit concurrente a benchmark; cola/worker solo se crea después de tests, preflight y manifest congelado.
5. **Llamada online y métricas.** Un warm-up de cinco llamadas sobre la primera fila de fit, fuera de resultados. Cada evaluación mide una vez el archivo de prueba: lectura/decode RGB → resize y construcción Y → preprocesamiento → dos inferencias ResNet101 → extracción `fc1000` → concatenación → ECOC-SVM → puntuaciones/clase; CUDA sincronizada antes/después y `perf_counter_ns`. Carga del modelo, ajuste SVM, warm-up y serialización fuera del cronómetro. La misma llamada produce predicción, puntuaciones y duración. Reportar por condición accuracy, macro-F1, latencia media/mediana/p95 y todas las filas (row ID, truth, pred, puntuaciones, ns); no promediar si falta una condición.

## Comparación, interpretación y límites

Se comparará por condición y fila contra los resultados locales ya cerrados,
usando los mismos row IDs de prueba. No recalcular nuevos tiempos para enlazarlos
con F1 históricos, ni presentar las latencias de fechas/condiciones de hardware
distintas como un ensayo temporal controlado. El artículo reporta accuracy, no
macro-F1: informar ambas columnas como métricas distintas. El 90,15 % ± 1,2 se
mostrará únicamente como referencia publicada (accuracy); no se espera ni se
fuerza coincidencia porque el paper no publica la partición exacta ni el seed.
No interpretar la desviación entre estas 15 condiciones como el ±1,2 del paper.

Antes de crear la cola/medir, un runner nuevo deberá tener tests sintéticos para
la ecuación YIQ, orden de concatenación/dimensión 2000, matriz ECOC reproducible,
exclusión de filas 0, decoder/ties y contrato online; el preflight deberá fijar
SHA256 de código/config/modelo/datos/índices, GPU y presupuesto. No se inicia
benchmark ni se ejecuta inferencia científica hasta pasar esas comprobaciones.
Fallo científico → `requires_review` con evidencia, sin retry ni cambio de
tolerancias/método. Esta ficha no autoriza descargas, contacto a autores, cambios
al manuscrito ni modificaciones de fuentes selladas.
