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
2. la concatenación completa de los 22 descriptores;
3. Greedy Forward Selection (GFS);
4. la mejor selección restringida a una familia representacional;
5. la concatenación de los `k` descriptores individualmente más fuertes,
   usando el mismo `k` de GFS.

La métrica primaria es macro-F1 externo.

## Inicio rápido (clonar y verificar)

```bash
git clone https://github.com/Joafp/concatenacion-descriptores-texturas.git
cd concatenacion-descriptores-texturas
bash scripts/setup_env.sh          # o: bash scripts/setup_env.sh --cpu
.venv-confirmatory/bin/python -m pytest experiments/ -q
```

Debe reportar **32 passed**. Eso valida el protocolo y el análisis sin
necesidad de datasets ni GPU.

Para reejecutar el protocolo experimental completo (datos + embeddings +
condiciones), seguí [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) y
[`docs/DATASETS.md`](docs/DATASETS.md).

## Alcance experimental vigente

| Dataset del análisis principal | Muestras | Clases | Protocolo externo |
|---|---:|---:|---|
| DTD | 5.640 | 47 | 10 splits oficiales |
| FMD | 1.000 | 10 | 3 semillas × 5 folds agrupados |
| CUReT | 5.612 | 61 | dos mitades complementarias de 46 condiciones |
| Outex_TC_00013 color | 1.360 | 68 | 680 entrenamiento / 680 test oficiales |
| Soil Original | 1.140 | 7 | 3 semillas × 5 folds agrupados |
| KTH-TIPS2-b | 4.752 | 11 | cuatro particiones por muestra física |

VisTex Reference-12 se conserva como análisis auxiliar; no entra en los contrastes principales.

## Descriptores

- Clásicos y conteos: LBP, LBP-rot, Gabor, GLCM, HOG y RGB N-gramas + SVD.
- CNN: VGG16, ResNet-50, ResNet-101, DenseNet-121, EfficientNet-B0 y ConvNeXt V2-T.
- Transformers: ViT-B/16, DeiT-S, Swin-T y EVA-02 base.
- Autosupervisados o multimodales: DINOv2 small, base y large, MAE base, SigLIP base y BEiTv2-B.

La concatenación completa suma 20.652 dimensiones. Los backbones permanecen
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

La matriz principal contiene 94 condiciones externas (47 por clasificador) y
470 resultados. Friedman, Iman--Davenport y Quade detectan diferencias globales
entre estrategias con SVM y ResMLP; Friedman alineado no rechaza. Tras Holm,
GFS supera a Individual con ResMLP; ningún par es significativo con SVM.
Completa no supera significativamente a Individual en la comparación bilateral
exacta por dataset. Las cifras, CSV de procedencia y salidas de SCI2S se generan
con `scripts/build_primary22_beitv2_paper.py`; ver
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## Entorno

- Python **3.12** + `requirements.txt` fijado a las versiones del entorno de desarrollo.
- PyTorch se instala desde el índice CUDA 12.6 (o CPU con `--cpu`).
- Tests no paramétricos: Java 17+ y `.tools/nonparametric/` — ver
  [`docs/PASO_A_PASO_SOFTWARE.md`](docs/PASO_A_PASO_SOFTWARE.md).

## Estado

Bloque experimental de seis datasets y Outex oficial cerrados. El manuscrito
está en revisión. Las salidas auditables de 22 descriptores ya están versionadas
en este repositorio; todavía falta depositar una versión archivada e inmutable.
