#!/usr/bin/env bash
set -euo pipefail

cd "$(cd -- "$(dirname -- "$0")/.." && pwd)"

classifier="${1:?classifier required: svm or resmlp}"
dataset="${2:?dataset required: DTD, FMD, CUReT, Outex13Official1360 or KTHTIPS2b}"

case "$classifier" in
  svm) jobs=4 ;;
  resmlp) jobs=1 ;;
  *) echo "unsupported classifier: $classifier" >&2; exit 2 ;;
esac

common=(
  --classifier "$classifier"
  --max-k 8
  --random-b 100
  --n-jobs "$jobs"
  --include-rgb-ngram
  --ngram-components 256
  --ngram-hash-bins 8192
)

case "$dataset" in
  DTD)
    for split in $(seq 1 10); do
      .venv-confirmatory/bin/python -u src/run_confirmatory_nested.py \
        --dataset DTD --seed 42 --fold 0 --official-split "$split" \
        "${common[@]}"
    done
    ;;
  FMD)
    for seed in 42 123 2026; do
      for fold in 0 1 2 3 4; do
        .venv-confirmatory/bin/python -u src/run_confirmatory_nested.py \
          --dataset FMD --seed "$seed" --fold "$fold" \
          "${common[@]}"
      done
    done
    ;;
  CUReT)
    for direction in a_to_b b_to_a; do
      .venv-confirmatory/bin/python -u src/run_confirmatory_nested.py \
        --dataset CUReT --seed 42 --fold 0 --curet-direction "$direction" \
        "${common[@]}"
    done
    ;;
  Outex13Official1360)
    .venv-confirmatory/bin/python -u src/run_confirmatory_nested.py \
      --dataset Outex13Official1360 --seed 42 --fold 0 --official-split 1 \
      --embedding-root embeddings_extensions \
      --output results/extensions/outex13_official1360 \
      "${common[@]}"
    ;;
  KTHTIPS2b)
    # Official 4-fold protocol (Caputo et al. 2005): one physical sample trains,
    # the other three test, rotating -- split_1..split_4 in the manifest.
    for split in 1 2 3 4; do
      .venv-confirmatory/bin/python -u src/run_confirmatory_nested.py \
        --dataset KTHTIPS2b --seed 42 --fold 0 --official-split "$split" \
        --embedding-root embeddings_extensions \
        --output results/extensions/kth_tips2b \
        "${common[@]}"
    done
    ;;
  *)
    echo "unsupported dataset: $dataset" >&2
    exit 2
    ;;
esac

echo "RGB_NGRAM_MULTIBASE_COMPLETE classifier=$classifier dataset=$dataset"
