# Reproducción mínima y procedencia de datos

Fecha: 25 de octubre de 2026. Revisión de trabajo sobre el commit base `bf5e7f9970b1e4eac7aa4e3f8d70a296c95f38bc`, con cambios locales. El commit por sí solo no contiene necesariamente todos los materiales: las versiones efectivas se identifican por los hashes de los registros de esta revisión. No se afirma que los datos o resultados locales estén ya publicados.

## 1. Reconstruir las dos tablas P0 sin imágenes ni GPU

Se necesitan Python 3.12 y las versiones usadas en la revisión: NumPy 2.4.4, SciPy 1.18.0 y scikit-learn 1.9.0, junto con las dependencias transitivas de este último. No se requiere PyTorch para esta reconstrucción. La lista general del proyecto está en `requirements.txt`; instala también paquetes que no necesita este nivel mínimo.

En una copia del repositorio, conservar la siguiente estructura y diez archivos de entrada:

1. `scripts/build_p0_thesis_tables.py`.
2. En `results/analysis/integration_v9/p0_gate_ablation_outex22_20261025/`: `results.csv`, `fold_results.csv`, `prediction_views.csv`, `validation_summary.json`, `artifact_manifest.json`.
3. En `results/exploratory/integration_v8/carlos_hybrid_outex22_20261021/`: `results.csv`, `fold0.json`, `fold1.json`, `fold2.json`.

Ejecutar desde la raíz, usando el entorno del proyecto:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  .venv-confirmatory/bin/python scripts/build_p0_thesis_tables.py
```

Salidas: `paper/generated_p0/descomposicion_b60.tex`, `barrido_p0.tex` y `provenance.json`. El generador comprueba 156 campos numéricos y cobertura; no reentrena ni altera las predicciones. Solo regenera sus salidas de presentación, por lo que deben respaldarse si se editaron manualmente.

La prueba local copió únicamente esos diez archivos a una carpeta temporal aislada, manteniendo el entorno Python, y produjo tablas byte-idénticas a las del manuscrito. No fue una instalación independiente de dependencias ni una nueva extracción. Evidencia: `results/analysis/mesa_grado_20261025_r2/reproduction/summary.json`, que enumera los hashes completos. Los hashes de tabla obtenidos fueron:

- Barrido: `ec39b4910be2b61ad7bf33e266b6b6dc98fc19a19484ffc820abeeba4148c65e`.
- Descomposición: `20039e0a90f3b3cf963d633faec12c98d02928f9d67d33cabcb59fc76216dd94`.

## 2. Control estático y sensibilidad estadística

El control estático nuevo queda en `results/exploratory/integration_v10/static_budget_outex22_20261025/`. `metadata.json` registra entorno, doce decisiones congeladas, hashes, nueve modelos reutilizados y nueve reajustes productores; no contiene entrenamiento nuevo de redes. `decisions.json`, `validation_scores.npz` y `predictions.csv` permiten auditar selección y evaluación sin volver a entrenar.

El protocolo, fijado antes de obtener esas predicciones, está en `PROTOCOLO_CONTROL_ESTATICO_MESA_2026-10-25.md`. El comando usado fue:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONPATH=.:src \
  .venv-confirmatory/bin/python scripts/run_static_budget_control.py \
  --output results/exploratory/integration_v10/static_budget_outex22_20261025
```

Ese directorio ya existe: el programa lo rechazará para no sobrescribirlo. Una repetición debe usar otra salida vacía. Requiere los pools v6/v7/v8, embeddings y conteos N-gramas referenciados por sus metadatos. Las rutas absolutas históricas de esos metadatos corresponden al entorno original; trasladar la corrida completa exige resolverlas explícitamente, sin cambiar los archivos originales ni sus hashes. La prueba aislada del apartado 1 no acredita la portabilidad completa de este entrenamiento.

`scripts/audit_static_budget_control.py` reproduce las doce selecciones desde puntuaciones internas, contrasta las clases predichas con scores guardados y verifica los doce presupuestos por pliegue. `paper/generated_mesa_r2/static_control_provenance.json` identifica las tablas resultantes. Se conservan doce comparaciones, cuatro presupuestos por tres variantes híbridas, en el análisis de ronda 2.

La sensibilidad KTH utiliza las matrices archivadas por dataset y clasificador de `results/primary22_beitv2/nonparametric/classifier_specific/`. `scripts/build_kth_sensitivity_mesa.py` ejecutó los programas Java SCI2S locales, reprodujo primero N=6 y repitió N=5. Conserva entradas CSV, salidas Java y una comprobación Python de Friedman y las familias Holm en `results/analysis/mesa_grado_20261025_r2/kth_sensitivity/`. Los scripts de construcción y auditoría rechazan sus carpetas de resultados existentes: no deben repetirse sobre las salidas congeladas.

## 3. Identificar SoilOriginal sin confundirlo con el conjunto aumentado

Proveedor: [ai4a-lab, Comprehensive Soil Classification Datasets](https://www.kaggle.com/datasets/ai4a-lab/comprehensive-soil-classification-datasets), versión 1 según el archivo adquirido y el manifiesto congelado. Archivo local: `results/confirmatory/recovery/soil/source/comprehensive-soil-classification-datasets-v1.zip`.

SHA-256 completo del ZIP: `a4ae6ce5f918128104d79ccfbf12ec93e670fa6aa4617eb788df3e4dda08d97e`.

El árbol original del ZIP se denomina `Orignal-Dataset`; el aumentado, `CyAUG-Dataset`. El manifiesto `results/confirmatory/recovery/soil/Soil_Original_manifest.csv` conserva solo originales, deduplicados por hash de archivo, con 1.140 filas, siete clases y 962 grupos conservadores por familia de nombre dentro de clase. Cada fila identifica versión, ruta, etiqueta, grupo, hashes de archivo y píxeles. Su generador documenta el orden y los desempates. No define una partición oficial del proveedor.

Esta revisión volvió a comprobar el ZIP y los hashes de las 1.140 imágenes seleccionadas, sin regenerar el manifiesto. El verificador no necesita el árbol de placeholders antiguo de `data/Soil`; utiliza las rutas del manifiesto recuperado. El estado previo de esa carpeta no debe confundirse con las fuentes admitidas para SoilOriginal.

## 4. Lo que no reconstruye el nivel mínimo

Reproducir desde RGB exige imágenes legibles en el orden canónico, pesos exactos, versiones de librerías, preprocesamiento, capa, pooling y normalización. El Anexo A identifica los modelos y operadores; los metadatos por extractor y las implementaciones registran detalles adicionales. Los conteos N-gramas y cada SVD deben volver a ajustarse solo en su entrenamiento correspondiente, nunca en toda la colección antes de particionar.

No se ejecutó una reextracción independiente desde RGB en esta ronda, ni se verificó disponibilidad pública de cada checkpoint o licencia de redistribución. Las discrepancias físicas CUReT/Soil siguen abiertas. Para entregar un paquete público completo deben fijarse rutas portables, adjuntar los archivos permitidos, declarar los ausentes e identificar las revisiones/hashes de pesos que faltan. La reconstrucción local de tablas no resuelve por sí sola esos requisitos.
