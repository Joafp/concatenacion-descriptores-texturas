#!/usr/bin/env bash
# scripts/run_classical_full.sh
# Extracción: 5 descriptores clásicos (lbp, glcm, gabor, hog, drlbp) en los 5 datasets.
# NOTA: estos son single-threaded por imagen. Tiempo estimado: 30-60 min totales.
set -euo pipefail
cd "$(dirname "$0")/.."

DATASETS=(DTD FMD KTH-TIPS2 HVD_glaucoma ocular_toxoplasmosis)
EXTRACTORS=(lbp glcm gabor hog drlbp)

total_start=$(date +%s)
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
      --batch-size 8 2>&1 | tail -6
    end=$(date +%s)
    echo ">>> $ext on $ds: $((end - start))s"
  done
done
total_end=$(date +%s)
echo ""
echo "============================================="
echo "=== Extracción clásicos completa en $((total_end - total_start))s ==="
echo "============================================="
