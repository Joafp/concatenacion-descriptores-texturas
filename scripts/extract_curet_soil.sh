#!/bin/bash
# Extrae embeddings para CUReT y Soil con los 17 extractores
# Uso: ./scripts/extract_curet_soil.sh
set -e
cd "$(dirname "$0")/.."

mkdir -p logs

DATASETS="CUReT Soil"
EXTRACTORS="vit_b16 swin_t deit_s dinov2_small dinov2 dinov2_large vgg16 resnet50 resnet101 densenet121 efficientnet_b0 convnext_v2_t lbp glcm gabor hog drlbp"

echo "============================================================"
echo "Extracción embeddings: CUReT + Soil"
echo "Inicio: $(date)"
echo "============================================================"

for dataset in $DATASETS; do
    echo ""
    echo ">>> Dataset: $dataset <<<"
    for extractor in $EXTRACTORS; do
        log="logs/extract_${dataset}_${extractor}.log"
        echo "  → $extractor (log: $log)"
        if python src/01_extract_features.py --dataset "$dataset" --extractor "$extractor" > "$log" 2>&1; then
            tail -1 "$log"
        else
            echo "    ERROR en $extractor (ver $log)"
        fi
    done
done

echo ""
echo "============================================================"
echo "Extracción completa: $(date)"
echo "Embeddings en embeddings/CUReT/ y embeddings/Soil/"
echo "============================================================"
ls embeddings/CUReT/*.npy 2>/dev/null | grep -v _labels | wc -l
ls embeddings/Soil/*.npy 2>/dev/null | grep -v _labels | wc -l