#!/usr/bin/env bash
# scripts/run_dinov2_large.sh
# Extracción: DINOv2-large (ViT-L/14, 1024 dim) en los 5 datasets.
# Tiempo estimado: ~70 min en RTX 4060.
set -euo pipefail
cd "$(dirname "$0")/.."

DATASETS=(DTD FMD KTH-TIPS2 HVD_glaucoma ocular_toxoplasmosis)

for ds in "${DATASETS[@]}"; do
  start=$(date +%s)
  echo ""
  echo "============================================="
  echo "=== dinov2_large on $ds ==="
  echo "============================================="
  python3 -u src/01_extract_features.py \
    --dataset "$ds" \
    --extractor dinov2_large \
    --batch-size 16 2>&1 | tail -8
  end=$(date +%s)
  echo ">>> dinov2_large on $ds: $((end - start))s"
done
echo ""
echo "=== Extracción DINOv2-large completa ==="
