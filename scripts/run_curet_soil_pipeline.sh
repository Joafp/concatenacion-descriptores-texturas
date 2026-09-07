#!/bin/bash
# ============================================================
# run_curet_soil_pipeline.sh
# Pipeline completo para los 2 datasets nuevos: CUReT y Soil
# Ejecuta los 3 experimentos en orden secuencial.
# ============================================================
# Uso:
#   1. Descargar CUReT y Soil y ponerlos en data/CUReT/ y data/Soil/
#   2. chmod +x scripts/run_curet_soil_pipeline.sh
#   3. ./scripts/run_curet_soil_pipeline.sh
# ============================================================

set -e  # salir si hay error

cd "$(dirname "$0")/.."  # ir al root del proyecto

echo "============================================================"
echo "PIPELINE CUReT + Soil"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# Paso 1: Verificar datasets
# ------------------------------------------------------------
echo "[Paso 1/5] Verificando datasets..."
if [ ! -d "data/CUReT" ]; then
    echo "ERROR: data/CUReT no existe."
    echo "Descargar CUReT de: https://www.robots.ox.ac.uk/~vgg/data/datasheets/curet.html"
    echo "Y extraer en data/CUReT/<clase>/<imagen>.png"
    exit 1
fi
if [ ! -d "data/Soil" ]; then
    echo "ERROR: data/Soil no existe."
    echo "Descargar Soil dataset y extraer en data/Soil/<clase>/<imagen>.jpg"
    exit 1
fi
echo "  ✓ CUReT y Soil encontrados"
echo ""

# ------------------------------------------------------------
# Paso 2: Extracción de embeddings (17 extractores × 2 datasets)
# ------------------------------------------------------------
echo "[Paso 2/5] Extrayendo embeddings con 17 extractores..."
echo "Tiempo estimado: ~2-3 horas"
echo ""

for dataset in CUReT Soil; do
    for extractor in vit_b16 swin_t deit_s dinov2_small dinov2 dinov2_large vgg16 resnet50 resnet101 densenet121 efficientnet_b0 convnext_v2_t lbp glcm gabor hog drlbp; do
        echo "  → $dataset / $extractor"
        python src/01_extract_features.py --dataset "$dataset" --extractor "$extractor" 2>&1 | tail -3
    done
done
echo "  ✓ Embeddings extraídos"
echo ""

# ------------------------------------------------------------
# Paso 3: Linear probing (baseline individual)
# ------------------------------------------------------------
echo "[Paso 3/5] Linear probing (SVM, KNN, RF, MLP)..."
echo "Tiempo estimado: ~30 min"
echo ""

for dataset in CUReT Soil; do
    echo "  → $dataset"
    python src/02_baseline_individual.py --dataset "$dataset" 2>&1 | tail -3
done
echo "  ✓ Linear probing completo"
echo ""

# ------------------------------------------------------------
# Paso 4: Fine-tuning (LoRA + Last-block sobre DINOv2)
# ------------------------------------------------------------
echo "[Paso 4/5] Fine-tuning (LoRA + Last-block)..."
echo "Tiempo estimado: ~3-4 horas"
echo ""

for dataset in CUReT Soil; do
    echo "  → $dataset (LoRA)"
    python src/07_finetune_dinov2.py --dataset "$dataset" --method lora 2>&1 | tail -3
    echo "  → $dataset (Last-block)"
    python src/07_finetune_dinov2.py --dataset "$dataset" --method last 2>&1 | tail -3
done
echo "  ✓ Fine-tuning completo"
echo ""

# ------------------------------------------------------------
# Paso 5: Concatenación (prefix concat + GFS)
# ------------------------------------------------------------
echo "[Paso 5/5] Concatenación (Prefix + GFS)..."
echo "Tiempo estimado: ~1-2 horas"
echo ""

for dataset in CUReT Soil; do
    echo "  → $dataset (prefix concat)"
    python src/03_concat_progressive.py --dataset "$dataset" 2>&1 | tail -3
    echo "  → $dataset (GFS)"
    python src/05_greedy_subset_search.py --dataset "$dataset" 2>&1 | tail -3
done
echo "  ✓ Concatenación completa"
echo ""

# ------------------------------------------------------------
# Resumen
# ------------------------------------------------------------
echo "============================================================"
echo "PIPELINE COMPLETO"
echo "============================================================"
echo ""
echo "Resultados guardados en results/tables/:"
echo "  - baseline_CUReT.csv, baseline_Soil.csv"
echo "  - finetune_CUReT.csv, finetune_Soil.csv"
echo "  - concat_CUReT.csv, concat_Soil.csv"
echo "  - greedy_CUReT.csv, greedy_Soil.csv"
echo ""
echo "Embeddings guardados en embeddings/CUReT/ y embeddings/Soil/"
echo ""
echo "Próximo paso: regenerar manuscript con los 6 datasets nuevos"
echo ""
