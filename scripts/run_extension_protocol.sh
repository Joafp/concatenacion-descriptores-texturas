#!/usr/bin/env bash
set -euo pipefail

dataset="${1:?dataset required: VisTexReference12, SoilOriginal, Outex13Official1360 or KTHTIPS2b}"
case "$dataset" in
  VisTexReference12)
    output="results/extensions/vistex_reference12"
    ;;
  SoilOriginal)
    output="results/extensions/soil_original"
    ;;
  Outex13Official1360)
    output="results/extensions/outex13_official1360"
    ;;
  KTHTIPS2b)
    output="results/extensions/kth_tips2b"
    ;;
  *)
    echo "unsupported extension dataset: $dataset" >&2
    exit 2
    ;;
esac

for classifier in svm resmlp; do
  if [[ "$dataset" == "Outex13Official1360" ]]; then
    .venv-confirmatory/bin/python src/run_confirmatory_nested.py \
      --dataset "$dataset" \
      --classifier "$classifier" \
      --seed 42 \
      --fold 0 \
      --official-split 1 \
      --max-k 8 \
      --random-b 100 \
      --n-jobs 2 \
      --embedding-root embeddings_extensions \
      --output "$output"
    continue
  fi
  if [[ "$dataset" == "KTHTIPS2b" ]]; then
    # Official 4-fold protocol (Caputo et al. 2005): one physical sample trains,
    # the other three test, rotating -- split_1..split_4 in the manifest.
    for official_split in 1 2 3 4; do
      .venv-confirmatory/bin/python src/run_confirmatory_nested.py \
        --dataset "$dataset" \
        --classifier "$classifier" \
        --seed 42 \
        --fold 0 \
        --official-split "$official_split" \
        --max-k 8 \
        --random-b 100 \
        --n-jobs 2 \
        --embedding-root embeddings_extensions \
        --output "$output"
    done
    continue
  fi
  for seed in 42 123 2026; do
    for fold in 0 1 2 3 4; do
      .venv-confirmatory/bin/python src/run_confirmatory_nested.py \
        --dataset "$dataset" \
        --classifier "$classifier" \
        --seed "$seed" \
        --fold "$fold" \
        --max-k 8 \
        --random-b 100 \
        --n-jobs 2 \
        --embedding-root embeddings_extensions \
        --output "$output"
    done
  done
done
