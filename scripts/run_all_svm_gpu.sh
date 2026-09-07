#!/usr/bin/env bash
set -euo pipefail
cd "$(cd -- "$(dirname -- "$0")/.." && pwd)"
PY=.venv-gpu-svm-rapids/bin/python
run_main() {
  local dataset="$1" seed="$2" fold="$3" split="$4" output="$5" embed="${6:-}"
  local args=(--dataset "$dataset" --classifier svm --svm-backend cuml --seed "$seed" --fold "$fold" --max-k 8 --random-b 100 --n-jobs 1 --output "$output")
  [[ -n "$split" ]] && args+=(--official-split "$split")
  [[ -n "$embed" ]] && args+=(--embedding-root "$embed")
  "$PY" src/run_confirmatory_nested.py "${args[@]}"
}
run_topk() {
  local dataset="$1" seed="$2" fold="$3" split="$4" output="$5" embed="${6:-}"
  local args=(--dataset "$dataset" --classifier svm --svm-backend cuml --seed "$seed" --fold "$fold" --output "$output" --n-jobs 1)
  [[ -n "$split" ]] && args+=(--official-split "$split")
  [[ -n "$embed" ]] && args+=(--embedding-root "$embed")
  "$PY" src/run_topk_individual_control.py "${args[@]}"
}
for split in $(seq 1 10); do run_main DTD 42 0 "$split" results/confirmatory; done
for seed in 42 123 2026; do for fold in 0 1 2 3 4; do run_main FMD "$seed" "$fold" "" results/confirmatory; done; done
for direction in a_to_b b_to_a; do
  "$PY" src/run_confirmatory_nested.py --dataset CUReT --classifier svm --svm-backend cuml --seed 42 --fold 0 --curet-direction "$direction" --max-k 8 --random-b 100 --n-jobs 1 --output results/confirmatory
done
run_main Outex13Official1360 42 0 1 results/extensions/outex13_official1360 embeddings_extensions
for split in $(seq 1 10); do run_topk DTD 42 0 "$split" results/confirmatory; done
for seed in 42 123 2026; do for fold in 0 1 2 3 4; do run_topk FMD "$seed" "$fold" "" results/confirmatory; done; done
for direction in a_to_b b_to_a; do
  "$PY" src/run_topk_individual_control.py --dataset CUReT --classifier svm --svm-backend cuml --seed 42 --fold 0 --curet-direction "$direction" --output results/confirmatory --n-jobs 1
done
run_topk Outex13Official1360 42 0 1 results/extensions/outex13_official1360 embeddings_extensions
bash scripts/run_diverse_topk_control.sh svm cuml
for dataset in SoilOriginal VisTexReference12; do
  if [[ "$dataset" == SoilOriginal ]]; then output=results/extensions/soil_original; else output=results/extensions/vistex_reference12; fi
  for seed in 42 123 2026; do for fold in 0 1 2 3 4; do run_main "$dataset" "$seed" "$fold" "" "$output" embeddings_extensions; done; done
done
bash scripts/run_diverse_topk_extensions.sh svm cuml
echo "ALL_SVM_GPU_COMPLETE"
