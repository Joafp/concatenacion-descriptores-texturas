#!/usr/bin/env bash
# scripts/run_smoke_test.sh
# Verifica que el pipeline de extracción funciona con un subset pequeño.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Smoke test: ViT-B/16 sobre DTD (50 imgs) ==="
python3 src/01_extract_features.py \
  --dataset DTD \
  --extractor vit_b16 \
  --max-samples 50 \
  --batch-size 16 \
  --suffix _smoke

echo ""
echo "=== Verificación de archivo guardado ==="
python3 -c "
import numpy as np
import json

base = 'embeddings/DTD'
emb = np.load(f'{base}/vit_b16_smoke.npy')
lab = np.load(f'{base}/vit_b16_smoke_labels.npy')
with open(f'{base}/vit_b16_smoke_classes.json') as f:
    classes = json.load(f)

print(f'Embeddings shape:  {emb.shape}')
print(f'Labels shape:      {lab.shape}')
print(f'Unique classes:    {len(np.unique(lab))} de {len(classes)} totales')
print(f'Class range:       [{lab.min()}, {lab.max()}]')
print(f'NaN count:         {np.isnan(emb).sum()}')
print(f'Inf count:         {np.isinf(emb).sum()}')
print(f'Embedding stats:   mean={emb.mean():.4f}, std={emb.std():.4f}, min={emb.min():.4f}, max={emb.max():.4f}')
print(f'L2 norms (mean):   {np.linalg.norm(emb, axis=1).mean():.4f}')

assert emb.shape[0] == 47, f'Expected 47 imgs (1 per class en DTD), got {emb.shape[0]}'
assert emb.shape[1] == 768, f'Expected dim 768, got {emb.shape[1]}'
assert not np.isnan(emb).any(), 'NaN detectado'
assert not np.isinf(emb).any(), 'Inf detectado'
print('OK: todas las verificaciones pasaron')
"
