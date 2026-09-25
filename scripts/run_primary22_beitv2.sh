#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

RESULT_SUBDIR="ngram22_beitv2"

run_pair() {
  local dataset="$1" classifier="$2" seed="$3" fold="$4" output="$5"
  shift 5
  local extra=("$@")

  .venv-confirmatory/bin/python src/run_confirmatory_nested.py \
    --dataset "$dataset" --classifier "$classifier" --seed "$seed" --fold "$fold" \
    --output "$output" --include-rgb-ngram --result-subdir "$RESULT_SUBDIR" \
    --max-k 8 --random-b 100 --n-jobs 3 "${extra[@]}"

  .venv-confirmatory/bin/python src/run_topk_individual_control.py \
    --dataset "$dataset" --classifier "$classifier" --seed "$seed" --fold "$fold" \
    --output "$output" --include-rgb-ngram --ngram-result-subdir "$RESULT_SUBDIR" \
    --n-jobs 3 "${extra[@]}"
}

for classifier in svm resmlp; do
  for split in {1..10}; do
    run_pair DTD "$classifier" 42 0 results/confirmatory --official-split "$split"
  done

  for seed in 42 123 2026; do
    for fold in {0..4}; do
      run_pair FMD "$classifier" "$seed" "$fold" results/confirmatory
    done
  done

  for direction in a_to_b b_to_a; do
    run_pair CUReT "$classifier" 42 0 results/confirmatory --curet-direction "$direction"
  done

  if [[ -f embeddings_extensions/Outex13Official1360/beitv2_base_final.npy ]]; then
    run_pair Outex13Official1360 "$classifier" 42 0 \
      results/extensions/outex13_official1360 \
      --official-split 1 --embedding-root embeddings_extensions
  else
    echo "PENDING Outex13Official1360: audited RGB source archive unavailable"
  fi

  for seed in 42 123 2026; do
    for fold in {0..4}; do
      run_pair SoilOriginal "$classifier" "$seed" "$fold" \
        results/extensions/soil_original --embedding-root embeddings_extensions
    done
  done

  for split in {1..4}; do
    run_pair KTHTIPS2b "$classifier" 42 0 results/extensions/kth_tips2b \
      --official-split "$split" --invert-official-split \
      --embedding-root embeddings_extensions \
      --exclude-extractors beitv2_base_multilayer
  done
done
