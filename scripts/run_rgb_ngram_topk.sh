#!/usr/bin/env bash
set -euo pipefail

cd "$(cd -- "$(dirname -- "$0")/.." && pwd)"
classifier="${1:?classifier required: svm or resmlp}"
dataset="${2:?dataset required: DTD, FMD, CUReT or Outex13Official1360}"

case "$classifier" in
  svm) jobs=4 ;;
  resmlp) jobs=1 ;;
  *) echo "unsupported classifier: $classifier" >&2; exit 2 ;;
esac

common=(
  --classifier "$classifier"
  --n-jobs "$jobs"
  --include-rgb-ngram
  --ngram-components 256
  --ngram-hash-bins 8192
)

case "$dataset" in
  DTD)
    for split in $(seq 1 10); do
      .venv-confirmatory/bin/python -u src/run_topk_individual_control.py \
        --dataset DTD --seed 42 --fold 0 --official-split "$split" \
        --output results/confirmatory "${common[@]}"
    done
    ;;
  FMD)
    for seed in 42 123 2026; do
      for fold in 0 1 2 3 4; do
        .venv-confirmatory/bin/python -u src/run_topk_individual_control.py \
          --dataset FMD --seed "$seed" --fold "$fold" \
          --output results/confirmatory "${common[@]}"
      done
    done
    ;;
  CUReT)
    for direction in a_to_b b_to_a; do
      .venv-confirmatory/bin/python -u src/run_topk_individual_control.py \
        --dataset CUReT --seed 42 --fold 0 --curet-direction "$direction" \
        --output results/confirmatory "${common[@]}"
    done
    ;;
  Outex13Official1360)
    .venv-confirmatory/bin/python -u src/run_topk_individual_control.py \
      --dataset Outex13Official1360 --seed 42 --fold 0 --official-split 1 \
      --embedding-root embeddings_extensions \
      --output results/extensions/outex13_official1360 \
      "${common[@]}"
    ;;
  *) echo "unsupported dataset: $dataset" >&2; exit 2 ;;
esac

echo "RGB_NGRAM_TOPK_COMPLETE classifier=$classifier dataset=$dataset"
