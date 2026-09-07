#!/usr/bin/env bash
# Resume the existing, fixed ngram21 experiment without overwriting checkpoints.
set -euo pipefail
cd "$(cd -- "$(dirname -- "$0")/.." && pwd)"
classifier="${1:?classifier required: svm or resmlp}"
case "$classifier" in
  svm|resmlp) ;;
  *) echo "Unsupported classifier: $classifier" >&2; exit 2 ;;
esac
mkdir -p results/confirmatory/ngram21/queue
exec 9>"results/confirmatory/ngram21/queue/${classifier}.lock"
flock -n 9 || { echo "Queue already active: $classifier" >&2; exit 3; }
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONUNBUFFERED=1
trap 'echo "QUEUE_FAILED classifier=$classifier exit=$? time=$(date -Is)" >&2' ERR
echo "QUEUE_START classifier=$classifier time=$(date -Is)"
for dataset in DTD FMD CUReT Outex13Official1360; do
  echo "QUEUE_STAGE main classifier=$classifier dataset=$dataset time=$(date -Is)"
  bash scripts/run_rgb_ngram_multibase.sh "$classifier" "$dataset"
done
for dataset in DTD FMD CUReT Outex13Official1360; do
  echo "QUEUE_STAGE topk classifier=$classifier dataset=$dataset time=$(date -Is)"
  bash scripts/run_rgb_ngram_topk.sh "$classifier" "$dataset"
done
echo "QUEUE_COMPLETE classifier=$classifier time=$(date -Is)"
