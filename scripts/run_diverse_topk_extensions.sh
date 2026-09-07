#!/usr/bin/env bash
set -euo pipefail

# Extensiones suplementarias: mismas 15 condiciones externas por clasificador
# que el protocolo confirmatorio de FMD, con embeddings ya auditados.
RUN=src/run_diverse_topk_control.py
CLF="${1:?classifier required: svm or resmlp}"
BACKEND="${2:-cpu}"
if [[ "$BACKEND" == "cuml" ]]; then
  PY=.venv-gpu-svm-rapids/bin/python
else
  PY=.venv-confirmatory/bin/python
fi

for dataset in SoilOriginal VisTexReference12; do
  case "$dataset" in
    SoilOriginal) output="results/extensions/soil_original" ;;
    VisTexReference12) output="results/extensions/vistex_reference12" ;;
  esac
  for seed in 42 123 2026; do
    for fold in 0 1 2 3 4; do
      "$PY" "$RUN" --dataset "$dataset" --classifier "$CLF" --seed "$seed" --fold "$fold" \
        --embedding-root embeddings_extensions --output "$output" --n-jobs 3 --svm-backend "$BACKEND"
    done
  done
done
