#!/usr/bin/env bash
set -euo pipefail

PY=.venv-confirmatory/bin/python
RUN=src/run_topk_individual_control.py
CLF="${1:-svm}"

for split in $(seq 1 10); do
  "$PY" "$RUN" --dataset DTD --classifier "$CLF" --seed 42 --fold 0 \
    --official-split "$split" --output results/confirmatory --n-jobs 3
done

for seed in 42 123 2026; do
  for fold in 0 1 2 3 4; do
    "$PY" "$RUN" --dataset FMD --classifier "$CLF" --seed "$seed" --fold "$fold" \
      --output results/confirmatory --n-jobs 3
  done
done

for direction in a_to_b b_to_a; do
  "$PY" "$RUN" --dataset CUReT --classifier "$CLF" --seed 42 --fold 0 \
    --curet-direction "$direction" --output results/confirmatory --n-jobs 3
done

"$PY" "$RUN" --dataset Outex13Official1360 --classifier "$CLF" \
  --seed 42 --fold 0 --official-split 1 \
  --embedding-root embeddings_extensions \
  --output results/extensions/outex13_official1360 --n-jobs 3
