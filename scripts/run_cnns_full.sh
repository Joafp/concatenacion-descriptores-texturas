#!/usr/bin/env bash
# scripts/run_cnns_full.sh
# Extracción: 2 CNNs (efficientnet_b0, convnext_v2_t) en los 5 datasets.
set -euo pipefail
cd "$(dirname "$0")/.."

DATASETS=(DTD FMD KTH-TIPS2 HVD_glaucoma ocular_toxoplasmosis)
EXTRACTORS=(efficientnet_b0 convnext_v2_t)

for ds in "${DATASETS[@]}"; do
  for ext in "${EXTRACTORS[@]}"; do
    start=$(date +%s)
    echo ""
    echo "============================================="
    echo "=== $ext on $ds ==="
    echo "============================================="
    python3 src/01_extract_features.py \
      --dataset "$ds" \
      --extractor "$ext" \
      --batch-size 32 2>&1 | grep -v "^Loading weights:" | tail -8
    end=$(date +%s)
    echo ">>> $ext on $ds: $((end - start))s"
  done
done
echo ""
echo "=== Extracción CNNs completa ==="
