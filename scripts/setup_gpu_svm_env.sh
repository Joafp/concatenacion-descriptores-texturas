#!/usr/bin/env bash
set -euo pipefail

cd "$(cd -- "$(dirname -- "$0")/.." && pwd)"

# Instalación aislada: no modifica .venv-confirmatory ni resultados históricos.
# Se clona el entorno reproducible y se habilita pip solamente dentro de la copia.
ENV=.venv-gpu-svm-rapids
if [[ ! -x "$ENV/bin/python" ]]; then
  cp -a .venv-confirmatory "$ENV"
fi
"$ENV/bin/python" -m ensurepip --upgrade
"$ENV/bin/python" -m pip install --upgrade \
  --extra-index-url=https://pypi.nvidia.com \
  "cuml-cu13" "numpy>=2,<3" "scikit-learn>=1.6" pandas
"$ENV/bin/python" - <<'PY'
import cuml
from cuml.svm import LinearSVC
import cupy as cp

print("cuML", cuml.__version__)
print("GPU", cp.cuda.runtime.getDeviceProperties(0)["name"].decode())
print("LinearSVC", LinearSVC)
PY
