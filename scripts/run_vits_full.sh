#!/usr/bin/env bash
# scripts/run_vits_full.sh
# Extracción completa: 3 ViTs (vit_b16, swin_t, deit_s) en los 5 datasets.
# Tiempo estimado: ~7-8 min totales con RTX 4060.
set -euo pipefail
cd "$(dirname "$0")/.."

DATASETS=(FMD KTH-TIPS2 HVD_glaucoma ocular_toxoplasmosis)
EXTRACTORS=(vit_b16 swin_t deit_s)

total_start=$(date +%s)
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
      --batch-size 32 2>&1 | grep -v "^Loading weights:" | tail -10
    end=$(date +%s)
    echo ">>> $ext on $ds: $((end - start))s"
  done
done
total_end=$(date +%s)
echo ""
echo "============================================="
echo "=== Extracción completa en $((total_end - total_start))s ==="
echo "============================================="
