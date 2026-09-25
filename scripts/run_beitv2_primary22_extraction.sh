#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

extract() {
  local dataset="$1" embedding_root="$2" manifest="$3"
  local output="$embedding_root/$dataset/beitv2_base_final.npy"
  if [[ -f "$output" ]]; then
    echo "SKIP existing $output"
    return
  fi
  .venv-confirmatory/bin/python src/extract_beitv2_extension.py \
    --dataset "$dataset" --embedding-root "$embedding_root" \
    --manifest "$manifest" --reference-extractor dinov2 \
    --final-only --batch-size 16 --num-workers 2
}

extract DTD embeddings results/confirmatory/sample_manifests/DTD.csv
extract FMD embeddings_confirmatory results/confirmatory/sample_manifests/FMD.csv
extract CUReT embeddings_confirmatory results/confirmatory/sample_manifests/CUReT.csv
extract Outex13Official1360 embeddings_extensions results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.csv
extract SoilOriginal embeddings_extensions results/extensions/soil_original/sample_manifests/SoilOriginal.csv
extract KTH-TIPS2-b embeddings_extensions results/extensions/kth_tips2b/sample_manifests/KTHTIPS2b.csv
