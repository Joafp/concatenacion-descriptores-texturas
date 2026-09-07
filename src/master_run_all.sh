#!/bin/bash
# master_run_all.sh — Orquesta Exp 3, Exp 4, diff sig cuando termine Exp 1.
set -e
cd /home/joa/data/tesis_claude

echo "=== Esperando que termine Exp 1 (PID 108006) ==="
while ps -p 108006 > /dev/null 2>&1; do
    sleep 30
done
echo "=== Exp 1 terminó ==="

# Verificar Exp 1 completo
python3 -c "
import json
from pathlib import Path
T = Path('results/tables')
for ds in ['DTD','FMD','CUReT','Soil','VisTex']:
    p = T / f'perfold_{ds}.jsonl'
    if not p.exists():
        print(f'  {ds}: FALTA perfold'); continue
    rows = [json.loads(l) for l in open(p) if l.strip()]
    clfs = sorted(set(r['clf'] for r in rows))
    n_ext = len(set(r['extractor'] for r in rows))
    print(f'  {ds:10s} extractors={n_ext}/17  clfs={clfs}  rows={len(rows)}')
"

echo ""
echo "=== Lanzando Exp 3 (prefix concat, 4 clfs, 6 datasets) ==="
nohup python3 -u src/run_exp3_prefix_concat.py > logs/exp3_concat.log 2>&1 &
EXP3_PID=$!
echo "Exp 3 PID: $EXP3_PID"

echo "=== Esperando Exp 3 ==="
while ps -p $EXP3_PID > /dev/null 2>&1; do
    sleep 60
done
echo "=== Exp 3 terminó ==="

echo ""
echo "=== Lanzando Exp 4 (diff sig sobre Exp 1) ==="
python3 -u src/exp4_significance_within_exp1.py 2>&1 | tee logs/exp4.log

echo ""
echo "=== Lanzando diff sig vs individual (Exp 3 vs Exp 1) ==="
python3 -u src/14_diff_sig_vs_individual.py 2>&1 | tee logs/diff_sig_vs_individual.log

echo ""
echo "=== RESUMEN FINAL ==="
python3 -c "
import pandas as pd
from pathlib import Path
T = Path('results/tables')

print('--- Exp 1: best per (dataset, clf) ---')
df = pd.read_csv(T / 'exp4_best_per_dataset_clf.csv')
print(df.to_string(index=False))

print()
print('--- Exp 3 (prefix concat): diff sig vs individual ---')
df2 = pd.read_csv(T / 'diff_sig_vs_individual.csv')
print(f'  Total comparaciones: {len(df2)}')
print(f'  Significativas (p<0.05 Holm): {df2.significant_05.sum()}')
print(f'  Significativas (p<0.01 Holm): {df2.significant_01.sum()}')
print(f'  Significativas (p<0.001 Holm): {df2.significant_001.sum()}')
"
