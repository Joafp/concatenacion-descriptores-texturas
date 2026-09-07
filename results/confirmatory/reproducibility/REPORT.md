# Reproducibility checks

Date: 2026-07-20

Two isolated reruns were compared against their corresponding archived reference executions.

| Check | Scope | Result | Maximum relative metric difference |
|---|---|---|---:|
| Deterministic | DTD, SVM, seed 42, official split 1, smoke verification path | Exact match in macro-F1, accuracy, selected blocks, `k`, and dimensions | 0.0% |
| Stochastic | FMD, ResMLP, seed 42, outer fold 0, full path | Exact match in macro-F1, accuracy, selected blocks, `k`, and dimensions | 0.0% |

The deterministic check uses the smoke verification path to exercise data loading, nested selection, fitting, and external evaluation without repeating all 100 Monte Carlo controls. The stochastic check repeats the full condition. Both satisfy the preregistered tolerance of less than 5% relative metric variation; the observed variation was zero.

The first attempted deterministic full rerun was intentionally interrupted after confirming from the archived runtime that repeating its Monte Carlo controls would require roughly 90 minutes. Its earlier failed log is retained as provenance and is not part of the successful checks above.

Commands:

```bash
.venv-confirmatory/bin/python src/run_confirmatory_nested.py --dataset DTD --classifier svm --seed 42 --fold 0 --official-split 1 --smoke --n-jobs 2 --output results/confirmatory/reproducibility/deterministic
.venv-confirmatory/bin/python src/run_confirmatory_nested.py --dataset FMD --classifier resmlp --seed 42 --fold 0 --n-jobs 2 --output results/confirmatory/reproducibility/stochastic
```
