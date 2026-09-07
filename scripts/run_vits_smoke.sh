#!/usr/bin/env bash
# scripts/run_vits_smoke.sh
# Smoke test: 3 ViTs (vit_b16, swin_t, deit_s) sobre DTD (50 imgs).
# Valida que todos los modelos cargan y producen shapes correctos.
set -euo pipefail
cd "$(dirname "$0")/.."

for extractor in vit_b16 swin_t deit_s; do
  echo ""
  echo "============================================="
  echo "=== $extractor on DTD (50 imgs) ==="
  echo "============================================="
  python3 src/01_extract_features.py \
    --dataset DTD \
    --extractor "$extractor" \
    --max-samples 50 \
    --batch-size 16 \
    --suffix _smoke 2>&1 | grep -v "^Loading weights:" | grep -v "^$" | tail -15
done

echo ""
echo "=== Verificación de los 3 archivos ==="
python3 -c "
import numpy as np
import json

EXPECTED_DIMS = {'vit_b16': 768, 'swin_t': 768, 'deit_s': 384}
for ext, dim in EXPECTED_DIMS.items():
    base = f'embeddings/DTD/{ext}_smoke'
    emb = np.load(f'{base}.npy')
    lab = np.load(f'{base}_labels.npy')
    print(f'{ext}: shape={emb.shape}, NaN={np.isnan(emb).sum()}, Inf={np.isinf(emb).sum()}, L2_mean={np.linalg.norm(emb, axis=1).mean():.3f}')
    assert emb.shape[1] == dim, f'Expected dim {dim}, got {emb.shape[1]}'
    assert not np.isnan(emb).any() and not np.isinf(emb).any(), 'NaN/Inf detectado'
print('OK: los 3 ViTs producen embeddings válidos con shapes correctos')
"
