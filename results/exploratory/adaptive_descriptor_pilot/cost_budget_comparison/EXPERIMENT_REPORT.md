# Adaptive acquisition: accuracy and measured-cost pilot

Status: exploratory, descriptive. No manuscript/confirmatory outputs were changed.
All newly generated metrics and timings are stored in this directory.

## Design and comparability

The route was held fixed as ResNet-50 first, BEiTv2-final second, linear SVM,
seed 42. For each outer split, the 25%, 50%, and 75% thresholds are the
corresponding quantiles of four-fold `StratifiedGroupKFold` OOF margins from
outer-training rows only. A random-request control uses the same requested
count (100 draws per split). Embedding simulation is not itself latency.
Outex uses official split 1; DTD uses official splits 1–10 with the audited
duplicate-purged manifest; CUReT uses both audited deterministic
`curet_half_indices` directions. Every JSON records input and labels hashes
(Outex first run is retained separately; see version note below), runner hash,
outer group checks, and duration. DTD's four inner folds retained all 47
classes in every split. CUReT's four inner folds retained all 61 classes in
both directions.

Baselines are joined from the archived SVM/seed-42 CSV rows on the same
dataset split, outer test rows, and macro-F1 metric: Top-k22 (`topk_individual`),
GFS (`gfs`), and all 22 (`full_concat`). Outex's baseline CSV hashes are
`fa89a052d31931ebf2030c2fdaa52d4acb0b16dfb35a8d3a4633901aefcc3918`
(Top-k) and `73114486931e506a343ee520199f4358bf16bafd72c49531b09a4e95fc4eb545`
(GFS/full22). DTD uses `473dd378038fdecc6f98faf5e06a7d3039f56a9a56d69b13ed048f385e4408a8`
and `9d5188758cadc882aa02495cc135f124dee2f29a67d5000d95d82be6882dfc6a`.
CUReT baseline files and hashes are inventoried in the preceding
`official_protocol_50pct/EXPERIMENT_REPORT.md`; only matching directions are
paired here. Comparisons are descriptive, not inferential.

## Matched-split macro-F1

| Dataset / split(s) | ResNet only | Adaptive 25% | Adaptive 50% | Adaptive 75% | ResNet+BEiT always | Top-k22 | GFS | Full22 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Outex13 official1 | 0.8809 | 0.9074 | 0.9101 | 0.9101 | 0.9101 | 0.9426 | 0.9589 | 0.9656 |
| DTD official1–10 mean | 0.7303 | 0.7858 | 0.8115 | 0.8150 | 0.8151 | 0.8700 | 0.8703 | 0.8639 |
| CUReT a→b | 0.9572 | 0.9907 | 0.9915 | 0.9915 | 0.9915 | 0.9982 | 0.9982 | 0.9979 |
| CUReT b→a | 0.9678 | 0.9958 | 0.9961 | 0.9961 | 0.9961 | 0.9996 | 0.9993 | 1.0000 |

The observed BEiTv2 request fractions at target budgets 25/50/75 were:

| Dataset / split(s) | 25% target | 50% target | 75% target |
|---|---:|---:|---:|
| Outex official1 | 19.56% | 43.97% | 63.09% |
| DTD official1–10 mean | 22.84% | 47.16% | 71.73% |
| CUReT a→b | 22.45% | 45.87% | 71.17% |
| CUReT b→a | 18.03% | 41.02% | 68.18% |

DTD split means/ranges remain descriptive because official partitions overlap;
no fold-level significance test or independence claim is made. Thresholding
gives approximate request rates rather than exact quotas. The archived
per-split JSONs also contain the random same-count control, accuracy, actual
threshold, full/base results, group checks, and provenance.

## Image-to-prediction timing

The timing device was the RTX 4060. The adaptive online runner keeps ResNet,
BEiT, and trained SVMs resident; each per-image measurement includes image
read/decode, preprocessing, synchronized inference, routing, and prediction;
model load and SVM fit are excluded. Fifty equally spaced official-test rows
were timed, with five warmups per policy. Timing-subset classification scores
are not external estimates.

The original per-invocation online timings were not stable enough to pool:
Outex's first budget-25 run averaged 65.02/112.16 ms (adaptive/full), while
the later budget-50 control averaged 20.20/29.50 ms. The historical 50% pilot
reported 25.40/33.63 ms. To diagnose this, a same-process paired benchmark
timed the same 50 Outex rows three times at each budget, alternating policy
order image-by-image. The per-image latencies, row IDs, GPU clocks/temperature
by round, and aggregate JSON are in `paired_online_repeats/`. The task auditor
independently checked all 50 source SHA-256s and all 450 adaptive
prediction/request decisions against the offline CSV (zero mismatches).

| Target | Observed request | Round adaptive mean (ms) | Round full mean (ms) | Median paired difference, mean of rounds (ms) |
|---:|---:|---|---|---:|
| 25% | 16% | 15.64 / 15.35 / 15.78 | 28.80 / 27.13 / 25.85 | −11.90 |
| 50% | 46% | 20.15 / 19.44 / 19.54 | 25.97 / 26.26 / 27.01 | −9.60 |
| 75% | 68% | 23.09 / 24.00 / 25.18 | 27.41 / 30.09 / 28.69 | −3.33 |

This repeated paired control is the defensible Outex two-block timing estimate
for these rows and this loaded-model regime. It suggests declining savings as
the request rate rises; it is a small timing subset, not a population result.
The earlier one-off timings are retained as provenance but are not combined
with this paired session.

Additional 50-image route checks were recorded in `online_latency_*.json`:
Outex targets 25 and 75, DTD official1 targets 25 and 75. Online predictions
and request decisions agreed 100% with their offline simulation. DTD adaptive
mean time was 45.15 vs 78.21 ms at 25% target (18% actually requested), and
28.08 vs 33.25 ms at 75% target (70% requested). These one-off runs are
dataset/split/subset-specific and are not pooled with Outex.

## Measured primary-library route cost and limitations

`primary22_e2e/Outex_official1_primary22_online_components.json` measures
real source-image extraction for the archived Top-k22 descriptor subset on
the same deterministic 50-image subset. Each selected extractor was loaded
separately, model loading excluded, and its image decode/preprocessing/
inference timed at batch 1; the per-image extractor times were summed and the
SVM prediction component measured. The route's minimum per-block cosine to
the stored embeddings was at least 0.99993 and predictions matched the
archived Top-k baseline on all 50 rows. Its serial sum was 345.59 ms mean,
341.20 ms median, and 374.28 ms p95. This is a **serial cost-component / lower
bound**, not the wall time of a deployed service with eight models resident;
load, setup, concurrency, and memory pressure are excluded. It is markedly
more expensive than the two-block route in this timing regime, but the two
figures do not constitute a complete Pareto frontier.

A v2 attempt to complete GFS/full22 by using raw `count_image` plus an
outer-train-only SVD failed before writing a result: the reconstructed route
had 6,528 input dimensions while the archived SVM expected 6,784 (a 256-D
block was absent). No GFS or full22 latency is reported from that attempt.
The earlier v1 route report records GFS/full22 as incomplete because N-gram
was absent. Moreover, the v1 full22 extractor reproduction had minimum
cosines −0.1155 for DeiT-S and −0.0802 for ViT-B/16, so even a timing sum would
not be an accuracy-matched implementation of the archived 22-feature model.
Do not infer full22 cost or quality from those timings. Top-k22 is the only
complete baseline route in the measured extractor pilot.

## Artifacts and commands

New runner scripts:

- `scripts/run_adaptive_cost_budget_comparison.py` — offline quantile budgets,
  100 random same-count draws, JSON/CSV, input/labels/runner hashes.
- `scripts/run_online_adaptive_validation.py` — minimally extended to accept
  `--prior-json`/CUReT direction and this runner's JSON/CSV field names.
- `scripts/run_adaptive_online_budget_repeats.py` — same-session three-round
  paired Outex timing and GPU state.
- `scripts/benchmark_primary22_extraction_routes.py` — sequential primary
  extractor timing and embedding-cosine/prediction checks.

Offline execution commands (all results wrote only to this exploratory
directory):

```bash
python3 scripts/run_adaptive_cost_budget_comparison.py --dataset Outex13Official1360 --split 1 --audit-root results/extensions/outex13_official1360 --manifest-root results/extensions/outex13_official1360 --embedding-root embeddings_extensions --output results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison
python3 scripts/run_adaptive_cost_budget_comparison.py --dataset DTD --split N --audit-root results/confirmatory --manifest-root results/confirmatory --embedding-root embeddings --output results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison
python3 scripts/run_adaptive_cost_budget_comparison.py --dataset CUReT --direction a_to_b|b_to_a --audit-root results/confirmatory --manifest-root results/confirmatory --embedding-root embeddings_extensions/adaptive_descriptor_pilot --output results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison
```

DTD `N=1..10`; CUReT ran once for each direction. Outex was rerun in
`Outex_rerun_v2/` after the audit requested label and runner hashes; its
metrics match the retained first output exactly. The initial DTD shell-loop
wrapper had a quoting error and launched no valid split; it is not a result.
DTD official1–10 and CUReT outputs were subsequently run and completed.

Online validation used the same runner with explicit `--prior-json`,
`--official-split 1`, `--n 50`, `--warmup 5`, and budgets 0.25/0.75; the
paired Outex repeat command was:

```bash
python3 scripts/run_adaptive_online_budget_repeats.py --dataset Outex13Official1360 --split 1 --audit-root results/extensions/outex13_official1360 --manifest-root results/extensions/outex13_official1360 --embedding-root embeddings_extensions --pilot results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison/Outex_rerun_v2/Outex13Official1360_official1_budgets.json --output results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison/paired_online_repeats --n 50 --warmup 5 --rounds 3
```

The primary-library extractor pilot used the confirmatory Python runtime
(`.venv-confirmatory/bin/python`) because the system `python3` lacks
Transformers. One v2 extractor-route process completed with the dimension
failure above and left no JSON; the observed 256-D deficit is consistent with
the N-gram block being absent, but the internal per-descriptor exception was
not persisted, so that diagnosis is not asserted as proven. V1 JSON and all
source artifacts were retained.

No data were changed, and no paper/thesis, confirmatory outputs, or Git state
were edited.
