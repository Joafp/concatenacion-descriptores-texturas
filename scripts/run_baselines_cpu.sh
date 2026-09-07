#!/bin/bash
# Run linear probing baselines para datasets que YA tienen embeddings
# Solo SVM/KNN/RF/MLP (CPU). ResMLP se corre después cuando GPU esté libre.
set -e
cd "$(dirname "$0")/.."

DATASETS="DTD FMD KTH-TIPS2-b GTOS-Mobile VisTex"
CLFS="svm knn rf mlp"

echo "============================================================"
echo "Baselines CPU-only: $DATASETS"
echo "Inicio: $(date)"
echo "============================================================"

for dataset in $DATASETS; do
    echo ""
    echo ">>> Dataset: $dataset <<<"
    log="logs/baseline_${dataset}.log"
    if python src/02_baseline_individual.py --datasets "$dataset" --clfs $CLFS > "$log" 2>&1; then
        tail -5 "$log"
    else
        echo "ERROR (ver $log)"
    fi
done

echo ""
echo "============================================================"
echo "Baselines CPU terminadas: $(date)"
echo "============================================================"
