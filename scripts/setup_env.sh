#!/usr/bin/env bash
# Crea .venv-confirmatory e instala dependencias reproducibles.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3.12}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python3
fi

PY_VER="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if [[ "$PY_VER" != "3.12" ]]; then
  echo "Advertencia: se recomienda Python 3.12 (encontrado $PY_VER)." >&2
  echo "Continuar puede cambiar resultados numéricos." >&2
fi

ENV_DIR="${ENV_DIR:-.venv-confirmatory}"
TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu126}"

if [[ "${1:-}" == "--cpu" ]]; then
  TORCH_INDEX="https://download.pytorch.org/whl/cpu"
fi

echo "==> Entorno: $ENV_DIR  (python=$PYTHON_BIN, torch index=$TORCH_INDEX)"
"$PYTHON_BIN" -m venv "$ENV_DIR"
# ensurepip can be missing in some distros; bootstrap if needed
"$ENV_DIR/bin/python" -m ensurepip --upgrade 2>/dev/null || true
"$ENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel

echo "==> PyTorch"
"$ENV_DIR/bin/python" -m pip install \
  torch==2.12.1 torchvision==0.27.1 \
  --index-url "$TORCH_INDEX"

echo "==> Resto de requirements.txt"
"$ENV_DIR/bin/python" -m pip install -r requirements.txt

echo "==> Verificación rápida"
"$ENV_DIR/bin/python" - <<'PY'
import importlib.metadata as m
for pkg in ("torch", "scikit-learn", "numpy", "pandas", "pytest"):
    print(f"  {pkg}=={m.version(pkg)}")
PY

echo
echo "Listo. Activá con:  source $ENV_DIR/bin/activate"
echo "Tests:              $ENV_DIR/bin/python -m pytest experiments/ -q"
echo "Docs:               docs/REPRODUCIBILITY.md"
