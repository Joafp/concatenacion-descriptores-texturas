#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=".venv-confirmatory/bin/python"
PARTS_SUBDIR="ngram22_beitv2_parts"
RUN_ROOT="results/confirmatory/ngram22_beitv2_runner"
mkdir -p "$RUN_ROOT"

run_one() {
  local dataset="$1" classifier="$2" seed="$3" fold="$4" output="$5" part="$6"
  shift 6
  local extra=("$@")
  local subdir="$PARTS_SUBDIR/$part"

  "$PYTHON" src/run_confirmatory_nested.py \
    --dataset "$dataset" --classifier "$classifier" --seed "$seed" --fold "$fold" \
    --output "$output" --include-rgb-ngram --result-subdir "$subdir" \
    --max-k 8 --random-b 100 --n-jobs 3 "${extra[@]}"

  "$PYTHON" src/run_topk_individual_control.py \
    --dataset "$dataset" --classifier "$classifier" --seed "$seed" --fold "$fold" \
    --output "$output" --include-rgb-ngram --ngram-result-subdir "$subdir" \
    --n-jobs 3 "${extra[@]}"

  flock "$RUN_ROOT/merge.lock" "$PYTHON" scripts/merge_primary22_beitv2_parts.py \
    --root "$output"
}
export -f run_one
export PYTHON PARTS_SUBDIR RUN_ROOT

emit_queue() {
  local classifier="$1"
  local split seed fold direction
  for split in {1..10}; do
    if [[ "$classifier" == "svm" && "$split" == "1" ]]; then
      continue
    fi
    printf 'DTD\t%s\t42\t0\tresults/confirmatory\tDTD_%s_s%02d\t--official-split\t%s\n' \
      "$classifier" "$classifier" "$split" "$split"
  done
  for seed in 42 123 2026; do
    for fold in {0..4}; do
      printf 'FMD\t%s\t%s\t%s\tresults/confirmatory\tFMD_%s_%s_f%s\n' \
        "$classifier" "$seed" "$fold" "$classifier" "$seed" "$fold"
    done
  done
  for direction in a_to_b b_to_a; do
    printf 'CUReT\t%s\t42\t0\tresults/confirmatory\tCUReT_%s_%s\t--curet-direction\t%s\n' \
      "$classifier" "$classifier" "$direction" "$direction"
  done
  for seed in 42 123 2026; do
    for fold in {0..4}; do
      printf 'SoilOriginal\t%s\t%s\t%s\tresults/extensions/soil_original\tSoil_%s_%s_f%s\t--embedding-root\tembeddings_extensions\n' \
        "$classifier" "$seed" "$fold" "$classifier" "$seed" "$fold"
    done
  done
  for split in {1..4}; do
    printf 'KTHTIPS2b\t%s\t42\t0\tresults/extensions/kth_tips2b\tKTH_%s_s%s\t--official-split\t%s\t--invert-official-split\t--embedding-root\tembeddings_extensions\t--exclude-extractors\tbeitv2_base_multilayer\n' \
      "$classifier" "$classifier" "$split" "$split"
  done
}

run_svm_queue() {
  emit_queue svm | xargs -P 3 -L 1 bash -c 'run_one "$@"' _
}

run_resmlp_queue() {
  while IFS=$'\t' read -r -a fields; do
    run_one "${fields[@]}"
  done < <(emit_queue resmlp)
}

run_svm_queue >"$RUN_ROOT/svm.log" 2>"$RUN_ROOT/svm.err" &
svm_pid=$!
run_resmlp_queue >"$RUN_ROOT/resmlp.log" 2>"$RUN_ROOT/resmlp.err" &
resmlp_pid=$!
printf '%s\n' "$svm_pid" >"$RUN_ROOT/svm.pid"
printf '%s\n' "$resmlp_pid" >"$RUN_ROOT/resmlp.pid"

status=0
wait "$svm_pid" || status=1
wait "$resmlp_pid" || status=1

"$PYTHON" scripts/merge_primary22_beitv2_parts.py --root results/confirmatory
"$PYTHON" scripts/merge_primary22_beitv2_parts.py --root results/extensions/soil_original
"$PYTHON" scripts/merge_primary22_beitv2_parts.py --root results/extensions/kth_tips2b
date --iso-8601=seconds >"$RUN_ROOT/finished_at.txt"
exit "$status"
