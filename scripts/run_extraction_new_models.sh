#!/usr/bin/env bash
# scripts/run_extraction_new_models.sh
# Extracción para los 4 modelos NUEVOS sobre los 6 datasets.
# Modelos: vgg16, resnet101, densenet121, dinov2_small
# Datasets: DTD, FMD, KTH-TIPS2-b, GTOS-Mobile (5K), VisTex. Outex uses the official extension protocol.
set -euo pipefail
cd "$(dirname "$0")/.."

NEW_EXTRACTORS=(vgg16 resnet101 densenet121 dinov2_small)
DATASETS_ALL=(DTD FMD KTH-TIPS2-b VisTex)

# Datasets "full" (sin GTOS que requiere subsample)
for ds in "${DATASETS_ALL[@]}"; do
  for ext in "${NEW_EXTRACTORS[@]}"; do
    out="embeddings/${ds}/${ext}.npy"
    if [ -f "$out" ]; then
      echo "[SKIP] $ds / $ext"
      continue
    fi
    echo "=== $ds / $ext ==="
    bs=32
    python3 src/01_extract_features.py --dataset "$ds" --extractor "$ext" --batch-size $bs 2>&1 | tail -3
  done
done

# GTOS-Mobile subsample 5K
echo "=== GTOS-Mobile subsample 5K ==="
for ext in "${NEW_EXTRACTORS[@]}"; do
  out="embeddings/GTOS-Mobile/${ext}.npy"
  if [ -f "$out" ]; then
    echo "[SKIP] GTOS-Mobile / $ext"
    continue
  fi
  echo "=== GTOS-Mobile / $ext (5K) ==="
  bs=32
  python3 src/01_extract_features.py --dataset GTOS-Mobile --extractor "$ext" --batch-size $bs --max-samples 5000 2>&1 | tail -3
done

echo "=== NEW MODELS EXTRACTION COMPLETADA ==="
