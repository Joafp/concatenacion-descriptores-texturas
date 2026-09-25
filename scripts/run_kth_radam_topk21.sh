#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

for classifier in svm resmlp; do
  for split in 1 2 3 4; do
    .venv-confirmatory/bin/python src/run_topk_individual_control.py \
      --dataset KTHTIPS2b --classifier "$classifier" --seed 42 --fold 0 \
      --official-split "$split" --invert-official-split \
      --embedding-root embeddings_extensions \
      --output results/extensions/kth_tips2b \
      --include-rgb-ngram --ngram-result-subdir ngram21_radam_3train \
      --exclude-extractors beitv2_base_final beitv2_base_multilayer \
      --n-jobs 3
  done
done
