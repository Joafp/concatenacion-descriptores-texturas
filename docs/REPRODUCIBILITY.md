# Reproducibilidad

Guía para clonar este repositorio y obtener las mismas pruebas unitarias y el
mismo protocolo experimental que el estudio confirmatorio.

## 1. Requisitos

- Python **3.12** (verificado con 3.12.13)
- Linux x86_64 (desarrollo en WSL2)
- GPU NVIDIA opcional (CUDA 12.6) para extracción y SVM/ResMLP a escala completa
- Java 17+ solo si vas a reejecutar CONTROLTEST / MULTIPLETEST (SCI2S)

## 2. Entorno

```bash
git clone <URL_DEL_REPO>
cd tesis_claude   # o el nombre del clone
bash scripts/setup_env.sh          # GPU: ruedas cu126
# bash scripts/setup_env.sh --cpu  # solo CPU (tests y análisis livianos)
```

El entorno queda en `.venv-confirmatory/`.

## 3. Tests automatizados (sin datasets)

Estos tests no necesitan `data/` ni embeddings. Validan el protocolo, el
análisis y descriptores sintéticos:

```bash
.venv-confirmatory/bin/python -m pytest experiments/ -q
```

Expectativa: **32 passed**.

## 4. Datos y embeddings

1. Seguí [`DATASETS.md`](DATASETS.md).
2. Congelá el orden con los manifiestos de `results/confirmatory/sample_manifests/`.
3. Extraé o reextraé embeddings hacia `embeddings_confirmatory/` y
   `embeddings_extensions/`.

## 5. Protocolo confirmatorio

Una condición DTD (ejemplo del manuscrito):

```bash
.venv-confirmatory/bin/python src/run_confirmatory_nested.py \
  --dataset DTD --classifier svm --seed 42 --fold 0 \
  --official-split 1 --n-jobs 2
```

Smoke de reproducibilidad (sin los 100 controles Monte Carlo):

```bash
.venv-confirmatory/bin/python src/run_confirmatory_nested.py \
  --dataset DTD --classifier svm --seed 42 --fold 0 \
  --official-split 1 --smoke --n-jobs 2 \
  --output results/confirmatory/reproducibility/deterministic
```

Outex oficial (una condición por clasificador):

```bash
bash scripts/run_extension_protocol.sh Outex13Official1360
```

RGB Pixel N-grams + concatenación:

```bash
.venv-confirmatory/bin/python src/run_rgb_ngram_outex13_official.py
```

Análisis consolidado:

```bash
.venv-confirmatory/bin/python src/analyze_confirmatory_results.py \
  --output results/confirmatory
```

## 6. Tests no paramétricos (SCI2S)

Herramientas en `.tools/nonparametric/` (CONTROLTEST y MULTIPLETEST).
Procedimiento detallado: [`PASO_A_PASO_SOFTWARE.md`](PASO_A_PASO_SOFTWARE.md).

```bash
cd .tools/nonparametric/controlTest
java Friedman <entrada.csv> > salida_controltest.tex
```

## 7. Evidencia archivada en el repo

Sin reejecutar GPU, ya están versionados (cuando no caen bajo `.gitignore`):

- Resúmenes CSV/JSON en `results/confirmatory/`
- Manifiestos y `ORDER_AND_SPLIT_PROTOCOL.md`
- Salidas SCI2S en `results/confirmatory/nonparametric/`
- Manuscrito en `paper/articulo/borrador_profesor/`

## 8. Qué no se clona

| Ruta | Motivo |
|---|---|
| `data/` | Datasets de terceros |
| `embeddings*/` | Arrays regenerables / pesados |
| `archive/local/` | Respaldos Overleaf, ZIPs locales |
| `.venv-*/` | Entornos |
| `results/**/logs|checkpoints` | Runtime regenerable |
