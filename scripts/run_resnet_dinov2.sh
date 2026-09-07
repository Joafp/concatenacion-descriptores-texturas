#!/usr/bin/env bash
# scripts/run_resnet_dinov2.sh
# Extracción: ResNet-50 y DINOv2 en los 5 datasets.
set -euo pipefail
cd "$(dirname "$0")/.."

DATASETS=(DTD FMD KTH-TIPS2 HVD_glaucoma ocular_toxoplasmosis)
EXTRACTORS=(resnet50 dinov2)

for ds in "${DATASETS[@]}"; do
  for ext in "${EXTRACTORS[@]}"; do
    start=$(date +%s)
    echo ""
    echo "============================================="
    echo "=== $ext on $ds ==="
    echo "============================================="
    python3 -u src/01_extract_features.py \
      --dataset "$ds" \
      --extractor "$ext" \
      --batch-size 32 2>&1 | tail -8
    end=$(date +%s)
    echo ">>> $ext on $ds: $((end - start))s"
  done
done
echo ""
echo "=== Extracción ResNet-50 + DINOv2 completa ==="
