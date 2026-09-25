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
git clone https://github.com/Joafp/concatenacion-descriptores-texturas.git
cd concatenacion-descriptores-texturas
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

El número de tests puede cambiar con el repositorio. Dos pruebas de
`test_vistex_reference12_extension.py` requieren las imágenes originales de
VisTex Reference12 en `results/confirmatory/recovery/vistex/staging/`; no son
pruebas independientes de datasets. Sin ese corpus, las restantes se ejecutan
con `-k 'not test_manifest_discovery_is_canonical and not test_manifest_gate_counts_hashes_and_groups'`.

## 4. Datos y embeddings

1. Seguí [`DATASETS.md`](DATASETS.md).
2. Congelá el orden con los manifiestos de `results/confirmatory/sample_manifests/`.
3. Extraé o reextraé embeddings hacia `embeddings_confirmatory/` y
   `embeddings_extensions/`.

## 5. Protocolo confirmatorio

La matriz del manuscrito utiliza 22 bloques, seis datasets, SVM y ResMLP.
Cada clasificador tiene 47 condiciones externas (DTD 10, FMD 15, CUReT 2,
Outex 1, Soil 15 y KTH-TIPS2-b 4), con cinco estrategias por condición.
Los CSV de 21 bloques se requieren únicamente para la comparación incremental
de BEiTv2.

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

## 6. Reconstrucción de tablas y pruebas del manuscrito

Con las salidas CSV de 21 y 22 bloques en las rutas indicadas por
`scripts/build_primary22_beitv2_paper.py`, ejecutá:

```bash
.venv-confirmatory/bin/python scripts/build_primary22_beitv2_paper.py
```

El script valida 94 condiciones externas, 470 filas de resultados y ausencia
de claves duplicadas o métricas no finitas. Comprueba también que las claves
externas de Completa-21 y Completa-22 coincidan. Luego genera las tablas LaTeX
en `paper/articulo/borrador_profesor/generated/` y las entradas/salidas SCI2S
por clasificador en `results/primary22_beitv2/nonparametric/`.

El archivo `results/primary22_beitv2/nonparametric/validation.json` guarda
hashes SHA-256 de los CSV fuente y del CSV canónico de 470 filas. La tabla
bibliográfica usa el mayor **promedio externo por configuración**; ese máximo
se elige después de observar los tests y sirve únicamente como contexto.
Soil Original no es el mismo corpus/protocolo que el Soil aumentado del paper
de Neshov et al.

## 7. Tests no paramétricos (SCI2S)

Herramientas en `.tools/nonparametric/` (CONTROLTEST y MULTIPLETEST).
Procedimiento detallado: [`PASO_A_PASO_SOFTWARE.md`](PASO_A_PASO_SOFTWARE.md).

```bash
cd .tools/nonparametric/controlTest
java Friedman <entrada.csv> > salida_controltest.tex
```

## 8. Evidencia y estado de publicación

El material necesario para auditar las tablas, una vez versionado en un commit
y comprobado contra una versión pública, incluye:

- Los CSV `nested_fold_results.csv` y `topk_individual_control/nested_fold_results.csv`
  de las ocho raíces de 21 y 22 bloques enumeradas en el script.
- El CSV canónico `paper/articulo/borrador_profesor/generated/primary22_beitv2_source_rows.csv`.
- Las entradas y salidas SCI2S de SVM y ResMLP y `validation.json` en
  `results/primary22_beitv2/nonparametric/`.
- El manuscrito y las tablas derivadas en `paper/articulo/borrador_profesor/`.

Un archivo local sin commit no constituye evidencia disponible públicamente.
Antes del envío, verificar que estos archivos figuren en el commit público,
anotar su SHA y depositar una versión inmutable. Los datasets y embeddings
originales se distribuyen o regeneran según las condiciones de sus fuentes.

## 9. Qué no se clona

| Ruta | Motivo |
|---|---|
| `data/` | Datasets de terceros |
| `embeddings*/` | Arrays regenerables / pesados |
| `archive/local/` | Respaldos Overleaf, ZIPs locales |
| `.venv-*/` | Entornos |
| `results/**/logs|checkpoints` | Runtime regenerable |
