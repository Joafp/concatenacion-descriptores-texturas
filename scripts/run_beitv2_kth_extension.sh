#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

.venv-confirmatory/bin/python src/extract_beitv2_extension.py \
  --dataset KTH-TIPS2-b \
  --embedding-root embeddings_extensions \
  --data-root results/confirmatory/recovery/kth/staging/KTH-TIPS2-b \
  --reference-extractor dinov2 \
  --layers 1 4 7 10 \
  --batch-size 16
