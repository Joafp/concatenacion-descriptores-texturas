#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

for classifier in svm resmlp; do
  .venv-confirmatory/bin/python src/evaluate_beitv2_kth_individual.py \
    --classifier "$classifier" --mode full_plus_beitv2 --invert-official-split
done
