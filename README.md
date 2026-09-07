# Selección y concatenación de descriptores heterogéneos para la clasificación de texturas

Tesis de grado de Carlos Ayala y Joaquín Delgado, Facultad Politécnica de la
Universidad Nacional de Asunción. Tutor: Prof. José Vázquez.

## Pregunta de investigación

¿En qué condiciones la concatenación de descriptores heterogéneos mejora la
clasificación de texturas y qué balance ofrece la selección de subconjuntos
entre desempeño y dimensionalidad?

El trabajo trata cada extractor como un bloque completo. Compara, sin consultar
el test durante la selección:

1. el mejor descriptor individual;
2. la concatenación completa de los 20 descriptores;
3. Greedy Forward Selection (GFS);
4. la mejor selección restringida a una familia representacional;
5. la concatenación de los `k` descriptores individualmente más fuertes,
   usando el mismo `k` de GFS.

La métrica primaria es macro-F1 externo.

## Inicio rápido (clonar y verificar)

```bash
git clone <URL_DEL_REPO>
cd tesis_claude
bash scripts/setup_env.sh          # o: bash scripts/setup_env.sh --cpu
.venv-confirmatory/bin/python -m pytest experiments/ -q
```

Debe reportar **32 passed**. Eso valida el protocolo y el análisis sin
necesidad de datasets ni GPU.

Para reejecutar el protocolo experimental completo (datos + embeddings +
condiciones), seguí [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) y
[`docs/DATASETS.md`](docs/DATASETS.md).

## Alcance experimental vigente

| Bloque | Dataset | Muestras | Clases | Protocolo externo |
|---|---|---:|---:|---|
| Principal | DTD | 5.640 | 47 | 10 splits oficiales |
| Principal | FMD | 1.000 | 10 | 3 semillas × 5 folds agrupados |
| Principal | CUReT | 5.612 | 61 | dos mitades complementarias de 46 condiciones |
| Extensión oficial | Outex_TC_00013 color | 1.360 | 68 | 680 entrenamiento / 680 test oficiales |
| Suplementario | Soil Original | 1.140 | 7 | 3 semillas × 5 folds agrupados |
| Suplementario | VisTex Reference-12 | 140 | 12 | 3 semillas × 5 folds agrupados |

## Descriptores

- Clásicos: LBP, DRLBP, Gabor, GLCM y HOG.
- CNN: VGG16, ResNet-50, ResNet-101, DenseNet-121, EfficientNet-B0 y ConvNeXt V2-T.
- Transformers: ViT-B/16, DeiT-S, Swin-T y EVA-02 base.
- Autosupervisados o multimodales: DINOv2 small, base y large, MAE base y SigLIP base.

La concatenación completa suma 19.628 dimensiones. Los backbones permanecen
congelados y cada bloque se normaliza por muestra antes de concatenarse.

## Protocolo confirmatorio (resumen)

- Clasificadores: SVM lineal y ResMLP.
- Selección interna: cuatro folds estratificados y agrupados.
- Evaluación: test externo una sola vez por condición y método.
- GFS: máximo ocho bloques; tolerancia 0,001 durante dos pasos.
- Control: 100 subconjuntos aleatorios del mismo `k`; control top-k.

Ejemplo de una condición:

```bash
.venv-confirmatory/bin/python src/run_confirmatory_nested.py \
  --dataset DTD --classifier svm --seed 42 --fold 0 \
  --official-split 1 --n-jobs 2
```

Outex oficial:

```bash
bash scripts/run_extension_protocol.sh Outex13Official1360
```

Análisis:

```bash
.venv-confirmatory/bin/python src/analyze_confirmatory_results.py \
  --output results/confirmatory
```

## Organización del repositorio

```text
src/                 código experimental (extracción, GFS, análisis, n-gramas)
scripts/             orquestación (setup_env, protocolos, tablas)
experiments/         tests automatizados del protocolo
results/confirmatory/  resúmenes, manifiestos y evidencia principal
results/extensions/  Outex, Soil, VisTex
paper/articulo/      manuscrito LaTeX canónico
docs/                datasets, reproducibilidad, traza SCI2S
.tools/nonparametric/  CONTROLTEST y MULTIPLETEST (Java)
archive/             nota sobre artefactos locales (no versionados)
```

No se versionan: `data/`, `embeddings*/`, entornos `.venv*`, logs/checkpoints
y respaldos en `archive/local/`. Detalle en `.gitignore`.

## Resultados principales (lectura)

En DTD, FMD y CUReT, GFS superó al mejor descriptor individual en las seis
combinaciones con SVM y ResMLP. Frente a la concatenación completa fue superior
en DTD y FMD, y quedó apenas por debajo en CUReT. Los subconjuntos redujeron la
dimensionalidad entre ~70 % y ~85 %. El detalle, tablas y auditoría están en
`results/confirmatory/` y en el manuscrito.

## Entorno

- Python **3.12** + `requirements.txt` fijado a las versiones del entorno de desarrollo.
- PyTorch se instala desde el índice CUDA 12.6 (o CPU con `--cpu`).
- Tests no paramétricos: Java 17+ y `.tools/nonparametric/` — ver
  [`docs/PASO_A_PASO_SOFTWARE.md`](docs/PASO_A_PASO_SOFTWARE.md).

## Estado

Bloque experimental principal y Outex oficial cerrados. El manuscrito está en
revisión; este repositorio concentra el código y la evidencia necesaria para
reproducir las pruebas automatizadas y el protocolo confirmatorio.
