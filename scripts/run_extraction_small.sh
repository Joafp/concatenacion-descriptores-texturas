#!/usr/bin/env bash
# scripts/run_extraction_small.sh
# Extrae embeddings para los 5 datasets "chicos" (sin GTOS-Mobile que es 100K).
# 13 extractores × 5 datasets = 65 extracciones.
set -euo pipefail
cd "$(dirname "$0")/.."

EXTRACTORS=(
  vit_b16 swin_t deit_s
  dinov2 dinov2_large
  resnet50 efficientnet_b0 convnext_v2_t
  lbp glcm gabor hog drlbp
)
DATASETS_SMALL=(DTD FMD KTH-TIPS2-b VisTex)

for ds in "${DATASETS_SMALL[@]}"; do
  for ext in "${EXTRACTORS[@]}"; do
    out="embeddings/${ds}/${ext}.npy"
    if [ -f "$out" ]; then
      echo "[SKIP] $ds / $ext (ya existe)"
      continue
    fi
    echo "=== $ds / $ext ==="
    bs=32
    [ "$ext" = "dinov2" ] && bs=8
    [ "$ext" = "dinov2_large" ] && bs=4
    python3 src/01_extract_features.py --dataset "$ds" --extractor "$ext" --batch-size $bs 2>&1 | tail -3
  done
done
echo "=== EXTRACCIÓN SMALL COMPLETADA ==="
