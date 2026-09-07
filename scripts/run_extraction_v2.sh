#!/usr/bin/env bash
# scripts/run_extraction_v2.sh
# Extracción de embeddings para los nuevos datasets (Exp 1).
# - KTH-TIPS2-b, VisTex: full extraction (Outex uses prepare_outex13_official.py)
# - GTOS-Mobile: subsample a 5K imágenes (160/clase) para velocidad
# DTD y FMD ya tienen embeddings, se reusan.
set -euo pipefail
cd "$(dirname "$0")/.."

EXTRACTORS_DEEP=(vit_b16 swin_t deit_s dinov2 dinov2_large resnet50 efficientnet_b0 convnext_v2_t)
EXTRACTORS_CLASSICAL=(lbp glcm gabor hog drlbp)
DATASETS_NEW=(KTH-TIPS2-b VisTex)

# Datasets nuevos sin GTOS (rápidos, todos los extractors)
for ds in "${DATASETS_NEW[@]}"; do
  for ext in "${EXTRACTORS_DEEP[@]}" "${EXTRACTORS_CLASSICAL[@]}"; do
    out="embeddings/${ds}/${ext}.npy"
    if [ -f "$out" ]; then
      echo "[SKIP] $ds / $ext"
      continue
    fi
    echo "=== $ds / $ext ==="
    bs=32
    [ "$ext" = "dinov2" ] && bs=8
    [ "$ext" = "dinov2_large" ] && bs=4
    python3 src/01_extract_features.py --dataset "$ds" --extractor "$ext" --batch-size $bs 2>&1 | tail -3
  done
done

# GTOS-Mobile subsample 5K (rápido para classical/CNN/ViT)
echo "=== GTOS-Mobile subsample 5K ==="
for ext in "${EXTRACTORS_DEEP[@]}" "${EXTRACTORS_CLASSICAL[@]}"; do
  out="embeddings/GTOS-Mobile/${ext}.npy"
  if [ -f "$out" ]; then
    echo "[SKIP] GTOS-Mobile / $ext"
    continue
  fi
  echo "=== GTOS-Mobile / $ext (5K subsample) ==="
  bs=32
  [ "$ext" = "dinov2" ] && bs=8
  [ "$ext" = "dinov2_large" ] && bs=4
  python3 src/01_extract_features.py --dataset GTOS-Mobile --extractor "$ext" --batch-size $bs --max-samples 5000 2>&1 | tail -3
done

echo "=== EXTRACCIÓN COMPLETADA ==="
