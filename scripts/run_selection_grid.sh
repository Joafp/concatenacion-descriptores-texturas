#!/usr/bin/env bash
# Runs one of the k=4 follow-up experiments over the manuscript grid: six
# datasets, 47 external conditions per classifier (FMD and Soil with seeds 42,
# 123 and 2026; KTH-TIPS2-b with the RADAM protocol).  A condition whose JSON
# already exists is skipped, so an interrupted run resumes where it stopped.
#
#   MODE      control | size | capacity | cost
#   CLF       svm | resmlp (capacity is ResMLP only)
#   FILTER    optional regex over "DATASET|ARGS|..." to run a subset
#   FORCE_CPU set to run ResMLP on the CPU
#   THREADS   BLAS threads per process (default 2)
#   NJOBS     parallel SVM fits (default 3)
#   PY_SVM, PY_RESMLP  interpreters (defaults: .venv-confirmatory and ~/venvs/tesis-gpu)
#
# cost measures one condition per dataset and should run on an idle machine.
# The reported runs used the GPU for DTD, KTH-TIPS2-b, CUReT and Outex and the
# CPU for Soil and FMD, as the earlier lottery and diversity runs did; ResMLP
# results depend slightly on the device, so keep that split to reproduce them.
#
# Example: MODE=size CLF=resmlp FORCE_CPU=1 FILTER='^FMD\|' scripts/run_selection_grid.sh
set -u
cd "$(dirname "$0")/.."
T=${THREADS:-2}; export OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T
if [ "$CLF" = svm ]; then PY=${PY_SVM:-./.venv-confirmatory/bin/python}; JOBS="--n-jobs ${NJOBS:-3}"
else PY=${PY_RESMLP:-$HOME/venvs/tesis-gpu/bin/python}; JOBS=""
  [ -n "${FORCE_CPU:-}" ] && export CUDA_VISIBLE_DEVICES=""; fi
run() { echo "--- $(date +%H:%M) $* ---"; out=$(timeout 7200 "$@" 2>&1); rc=$?
        echo "$out" | tail -1; [ $rc -eq 0 ] || echo "!!! FALLO: $*"; }
case $MODE in
  control)  SCRIPT=src/run_ensemble_control.py; O=results/exploratory/ensemble_control/$CLF; CARG="--classifier $CLF $JOBS";;
  size)     SCRIPT=src/run_ensemble_size.py; O=results/exploratory/ensemble_size/$CLF; CARG="--classifier $CLF $JOBS";;
  capacity) SCRIPT=src/run_resmlp_capacity.py; O=results/exploratory/resmlp_capacity; CARG="";;
  cost)     SCRIPT=src/measure_selection_cost.py; O=results/exploratory/selection_cost/$CLF; CARG="--classifier $CLF";;
  *) echo "MODE must be control, size, capacity or cost"; exit 1;;
esac
EXT="--embedding-root embeddings_extensions"
RO="--audit-root results/extensions/outex13_official1360 --manifest-root results/extensions/outex13_official1360 $EXT"
RK="--audit-root results/extensions/kth_tips2b --manifest-root results/extensions/kth_tips2b $EXT --invert-official-split --inner-group-column sample --exclude-extractors beitv2_base_multilayer"
RS="--audit-root results/extensions/soil_original --manifest-root results/extensions/soil_original $EXT"
RC="--audit-root results/confirmatory --manifest-root results/confirmatory"
conds_all() {
  echo "Outex13Official1360|--official-split 1|$RO|outex13|42|official1"
  for SP in 1 2 3 4; do echo "KTHTIPS2b|--official-split $SP|$RK|kth_tips2b|42|official${SP}_inverted"; done
  echo "CUReT|--curet-direction a_to_b|$RC|curet|42|a_to_b"
  echo "CUReT|--curet-direction b_to_a|$RC|curet|42|b_to_a"
  for SEED in 42 123 2026; do for F in 0 1 2 3 4; do
    echo "SoilOriginal|--fold $F|$RS|soil_original|$SEED|f$F"
    echo "FMD|--fold $F|$RC|fmd|$SEED|f$F"
  done; done
  for SP in 1 2 3 4 5 6 7 8 9 10; do echo "DTD|--official-split $SP|$RC|dtd|42|official$SP"; done
}
conds() { if [ "$MODE" = cost ]; then conds_all | awk -F'|' '!seen[$1]++'; else conds_all; fi; }
conds | grep -E "${FILTER:-.}" | while IFS='|' read DS P R D SEED TAG; do
  [ -f "$O/$D/${DS}_${CLF}_s${SEED}_${TAG}_${MODE}.json" ] ||
    run $PY $SCRIPT --dataset $DS $CARG --seed $SEED $P $R --output $O/$D
done
echo "### $MODE $CLF ${FILTER:-all} done $(date) ###"
