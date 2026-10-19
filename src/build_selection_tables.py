#!/usr/bin/env python3
"""Every number of the selection report, for both classifiers, from saved runs.

Reads the size sweeps, their inner-criterion twins, the rank-lottery and
diversity runs at k=4, and the manuscript's source rows, and writes one JSON per
classifier with the figures each report table needs.

All means are taken per dataset first and then across the six datasets, so that
DTD's ten partitions and the fifteen of FMD and Soil weigh the same as Outex's
single one.  Conditions are matched on (dataset, seed, outer fold) between the
exploratory runs and the manuscript's rows.  The ensemble configurations are
fixed in advance for both classifiers (rank lottery beta=8, diversity
lambda=0.25 beta=8, soft vote), so the ResMLP figures involve no selection on its
own test results.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[1]
KEYS = ["dataset", "seed", "outer_fold"]
ROOTS = {"svm": REPO / "results/exploratory",
         "resmlp": REPO / "results/exploratory/resmlp"}
SOURCE = REPO / "paper/articulo/borrador_profesor/generated/primary22_beitv2_source_rows.csv"
LITERATURE = {"DTD": {"Neshov 2025": 0.8200, "Scabini 2025": 0.7910, "HyTexNet 2026": 0.7320},
              "FMD": {"Neshov 2025": 0.9670, "Scabini 2025": 0.9090},
              "KTHTIPS2b": {"Neshov 2025": 0.9680, "Scabini 2025": 0.9370},
              "Outex13Official1360": {"Scabini 2025": 0.9160}}
LOTTERY_BETA, DIV_LAMBDA, DIV_BETA = 8.0, 0.25, 8.0


def read_all(pattern: str) -> pd.DataFrame:
    paths = glob.glob(str(pattern))
    if not paths:
        raise FileNotFoundError(pattern)
    return pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)


def by_dataset(s: pd.Series) -> float:
    """Mean per dataset first, then across datasets."""
    return float(s.groupby(level="dataset").mean().mean())


def series(frame: pd.DataFrame, value: str) -> pd.Series:
    out = frame.drop_duplicates(KEYS).set_index(KEYS)[value]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/selection_tables")
    args = parser.parse_args()
    src = pd.read_csv(SOURCE)
    src = src[src.run_mode.eq("full")].copy()
    src["method"] = src["method"].str.replace("best_homogeneous_.*", "homogeneous", regex=True)
    args.output.mkdir(parents=True, exist_ok=True)

    for clf, root in ROOTS.items():
        sweep = read_all(root / "k_sweep/*/k_sweep.csv")
        sweep = sweep[sweep.classifier.eq(clf)]
        inner = read_all(root / "k_sweep/*/k_sweep_inner.csv")
        inner = inner[inner.classifier.eq(clf)]
        lot = read_all(root / "k4/lottery/*/lottery_rows.csv")
        lot = lot[lot.classifier.eq(clf) & lot.k.eq(4)]
        div = read_all(root / "k4/diversity/*/diversity_rows.csv")
        div = div[div.classifier.eq(clf) & div.k.eq(4)]
        man = src[src.classifier.eq(clf)]

        index = sweep[sweep.k.eq(1)].drop_duplicates(KEYS).set_index(KEYS).index
        n_by_ds = index.to_frame(index=False).groupby("dataset").size().to_dict()

        def mval(method, value="macro_f1"):
            return series(man[man.method.eq(method)], value).reindex(index)

        full22 = {v: mval("full_concat", v) for v in ("macro_f1", "accuracy")}
        at = {k: sweep[sweep.k.eq(k)].drop_duplicates(KEYS).set_index(KEYS).reindex(index)
              for k in sorted(sweep.k.unique())}
        kmax = max(at)
        top4 = at[4]

        # Curve of k.
        curve = [{"k": int(k), "macro_f1": by_dataset(at[k].macro_f1),
                  "pct_dims": by_dataset(at[k].pct_dimensions)} for k in sorted(at)]
        peak = max(c["macro_f1"] for c in curve)
        for c in curve:
            c["pct_of_max"] = 100 * c["macro_f1"] / peak

        # Per-dataset figures.
        per_ds = {}
        for ds in sorted(index.get_level_values("dataset").unique()):
            sel = index.get_level_values("dataset") == ds
            row = {"conditions": int(n_by_ds[ds])}
            for v in ("macro_f1", "accuracy"):
                row[f"top4_{v}"] = float(top4[v][sel].mean())
                row[f"full21_{v}"] = float(at[kmax][v][sel].mean())
                row[f"full22_{v}"] = float(full22[v][sel].mean())
            row["top4_pct_dims"] = float(top4.pct_dimensions[sel].mean())
            row["literature"] = LITERATURE.get(ds, {})
            per_ds[ds] = row

        # Methods on the same base.
        lot_soft = series(lot[lot.variant.eq("ensemble_soft") & lot.beta.astype(float).eq(LOTTERY_BETA)], "macro_f1").reindex(index)
        lot_single = series(lot[lot.variant.eq("single_mean") & lot.beta.astype(float).eq(LOTTERY_BETA)], "macro_f1").reindex(index)
        dnum = div.assign(lam=pd.to_numeric(div["lambda"], errors="coerce"),
                          bet=pd.to_numeric(div["beta"], errors="coerce"))
        div_soft = series(dnum[dnum.variant.eq("ensemble_soft") & dnum.lam.eq(DIV_LAMBDA) & dnum.bet.eq(DIV_BETA)], "macro_f1").reindex(index)
        div_greedy = series(dnum[dnum.variant.eq("greedy") & dnum.lam.eq(DIV_LAMBDA)], "macro_f1").reindex(index)
        methods = {
            "Completa-22": (full22["macro_f1"], mval("full_concat", "dimensions")),
            "Ensamble con diversidad": (div_soft, None),
            "Ensamble tómbola": (lot_soft, None),
            "Top-4 fijo": (top4.macro_f1, top4.dimensions),
            "Top-k (k del GFS)": (mval("topk_individual"), mval("topk_individual", "dimensions")),
            "GFS": (mval("gfs"), mval("gfs", "dimensions")),
            "Homogénea": (mval("homogeneous"), mval("homogeneous", "dimensions")),
            "Mejor individual": (mval("best_individual"), mval("best_individual", "dimensions")),
        }
        base_full = by_dataset(full22["macro_f1"])
        method_rows = []
        for name, (s, dims) in methods.items():
            if s.isna().all():
                continue
            method_rows.append({"method": name, "macro_f1": by_dataset(s),
                                "vs_full22": by_dataset(s) - base_full,
                                "dims": by_dataset(dims) if dims is not None else None,
                                "missing": int(s.isna().sum())})

        variants = []
        for name, s in (("Top-4 determinista", top4.macro_f1),
                        (f"Tómbola: un sorteo (beta={LOTTERY_BETA:g})", lot_single),
                        (f"Tómbola: ensamble de 15 (beta={LOTTERY_BETA:g})", lot_soft),
                        (f"Diversidad: un subconjunto (lambda={DIV_LAMBDA:g})", div_greedy),
                        (f"Diversidad: ensamble de 15 (lambda={DIV_LAMBDA:g}, beta={DIV_BETA:g})", div_soft)):
            variants.append({"variant": name, "macro_f1": by_dataset(s),
                             "vs_top4": by_dataset(s) - by_dataset(top4.macro_f1),
                             "vs_full22": by_dataset(s) - base_full,
                             "wins_full22": int((s > full22["macro_f1"]).sum()),
                             "n": int(s.notna().sum()),
                             "per_dataset": s.groupby(level="dataset").mean().to_dict()})

        # Union of blocks touched by each ensemble.
        unions = {}
        for label, pattern, pick in (
                ("Tómbola", root / "k4/lottery/*/*_lottery.json",
                 lambda d: [b for b in d["betas"] if b["beta"] == LOTTERY_BETA]),
                ("Diversidad", root / "k4/diversity/*/*_diversity.json",
                 lambda d: [c for c in d["cells"] if c["lambda"] == DIV_LAMBDA and c["beta"] == DIV_BETA])):
            vals = {}
            for p in glob.glob(str(pattern)):
                d = json.loads(Path(p).read_text(encoding="utf-8"))
                if d["classifier"] != clf or d["k"] != 4:
                    continue
                for cell in pick(d):
                    subs = [dr["subset"] for dr in cell["draws"]] if "draws" in cell else cell["subsets"]
                    vals.setdefault(d["dataset"], []).append(len({b for s in subs for b in s}))
            unions[label] = float(np.mean([np.mean(v) for v in vals.values()])) if vals else None

        # Inner versus external curves, and rules for k.
        merged = sweep.merge(inner[KEYS + ["k", "inner_f1"]], on=KEYS + ["k"], how="inner")
        rhos, picks = [], {}
        rules = {"argmax interno": lambda b: int(b.loc[b.inner_f1.idxmax(), "k"])}
        for tau in (0.01, 0.005, 0.001):
            def elbow(b, t=tau):
                b = b.sort_values("k"); g = b.inner_f1.diff()
                for kk, gg in zip(b.k.iloc[1:], g.iloc[1:]):
                    if gg < t:
                        return int(kk - 1)
                return int(b.k.max())
            rules[f"codo tau={tau:g}"] = elbow
        for c in (3, 4, 6):
            rules[f"fijo k={c}"] = (lambda b, c=c: c)
        for key, b in merged.groupby(KEYS):
            rhos.append({"dataset": key[0], "rho": float(spearmanr(b.inner_f1, b.macro_f1).statistic)})
            for name, rule in rules.items():
                kk = rule(b)
                picks.setdefault(name, []).append(
                    {"dataset": key[0], "k": kk,
                     "macro_f1": float(b.loc[b.k.eq(kk), "macro_f1"].iloc[0])})
        rho_frame = pd.DataFrame(rhos)
        rule_rows = []
        for name, rows in picks.items():
            f = pd.DataFrame(rows)
            rule_rows.append({"rule": name, "mean_k": float(f.groupby("dataset").k.mean().mean()),
                              "macro_f1": float(f.groupby("dataset").macro_f1.mean().mean())})

        out = {
            "classifier": clf,
            "conditions": int(len(index)), "conditions_by_dataset": n_by_ds,
            "inner_conditions": int(merged.drop_duplicates(KEYS).shape[0]),
            "ensemble_configuration": {"lottery_beta": LOTTERY_BETA,
                                       "diversity_lambda": DIV_LAMBDA, "diversity_beta": DIV_BETA},
            "curve": curve, "full22_macro_f1": base_full,
            "full22_accuracy": by_dataset(full22["accuracy"]),
            "top4_accuracy": by_dataset(top4.accuracy),
            "full21_accuracy": by_dataset(at[kmax].accuracy),
            "per_dataset": per_ds, "methods": method_rows, "variants": variants,
            "ensemble_union_blocks": unions,
            "spearman_mean": float(rho_frame.rho.mean()),
            "spearman_by_dataset": rho_frame.groupby("dataset").rho.mean().to_dict(),
            "spearman_positive": int((rho_frame.rho > 0).sum()), "spearman_n": int(len(rho_frame)),
            "rules": rule_rows,
        }
        (args.output / f"{clf}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False)
                                                 + "\n", encoding="utf-8")

        print(f"\n################ {clf.upper()} — {out['conditions']} condiciones "
              f"{n_by_ds} ################")
        print("curva:", ", ".join(f"k={c['k']}:{c['macro_f1']:.4f}" for c in curve
                                   if c["k"] in (1, 2, 3, 4, 6, 10, kmax)))
        print(f"Completa-22 {base_full:.4f} | Top-4 {by_dataset(top4.macro_f1):.4f} | "
              f"21 bloques {by_dataset(at[kmax].macro_f1):.4f}")
        for m in method_rows:
            print(f"  {m['method']:<26}{m['macro_f1']:.4f}  {m['vs_full22']:+.4f}  faltan {m['missing']}")
        for v in variants:
            print(f"  {v['variant']:<52}{v['macro_f1']:.4f} {v['vs_top4']:+.4f} {v['vs_full22']:+.4f} "
                  f"{v['wins_full22']}/{v['n']}")
        print(f"  Spearman medio {out['spearman_mean']:+.3f} ({out['spearman_positive']}/{out['spearman_n']})")
        for r in rule_rows:
            print(f"  regla {r['rule']:<18} k={r['mean_k']:.1f}  {r['macro_f1']:.4f}")
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
