#!/usr/bin/env python3
"""The two sampling ideas at a fixed size of four blocks.

The rank lottery and the diversity-discounted sampling were first evaluated at
the subset size each condition inherits from GFS.  The size sweep later showed
that a fixed k=4 is the strongest simple choice, so both ideas are re-run at
k=4 and compared, on the same 27 external conditions, with deterministic Top-4
and with the manuscript's 22-block full concatenation.

Means are reported per dataset first, so that DTD's ten partitions do not
outweigh Outex's single one; condition-level win counts are given alongside.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEYS = ["dataset", "outer_fold"]


def series(frame: pd.DataFrame, metric: str) -> pd.Series:
    return frame.drop_duplicates(KEYS).set_index(KEYS)[metric]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=REPO / "results/exploratory/k4")
    parser.add_argument("--source-rows", type=Path, default=REPO /
                        "paper/articulo/borrador_profesor/generated/primary22_beitv2_source_rows.csv")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/k4_professor")
    args = parser.parse_args()

    lot = pd.concat([pd.read_csv(p) for p in
                     glob.glob(str(args.root / "lottery/*/lottery_rows.csv"))])
    div = pd.concat([pd.read_csv(p) for p in
                     glob.glob(str(args.root / "diversity/*/diversity_rows.csv"))])
    src = pd.read_csv(args.source_rows)
    src = src[src.run_mode.eq("full") & src.classifier.eq("svm") & src.seed.eq(42)]

    metric = "macro_f1"
    methods: dict[str, pd.Series] = {}
    methods["Completa-22"] = series(src[src.method.eq("full_concat")], metric)
    methods["Top-4 determinista"] = series(lot[lot.variant.eq("topk_deterministic")], metric)
    lot_beta = lot.assign(beta=pd.to_numeric(lot["beta"], errors="coerce"))
    for b in (0.0, 2.0, 8.0):
        for v, lab in (("single_mean", "sorteo"), ("ensemble_soft", "ensamble suave"),
                       ("ensemble_hard", "ensamble voto")):
            sel = lot_beta[lot_beta.variant.eq(v) & lot_beta.beta.eq(b)]
            methods[f"Tombola b={b:g} {lab}"] = series(sel, metric)
    div_num = div.assign(lam=pd.to_numeric(div["lambda"], errors="coerce"),
                         beta=pd.to_numeric(div["beta"], errors="coerce"))
    for lam in (0.0, 0.25, 0.5, 1.0):
        g = div_num[div_num.variant.eq("greedy") & div_num.lam.eq(lam)]
        methods[f"Diversidad lam={lam:g} determinista"] = series(g, metric)
        for b in (2.0, 8.0):
            e = div_num[div_num.variant.eq("ensemble_soft") & div_num.lam.eq(lam)
                        & div_num.beta.eq(b)]
            methods[f"Diversidad lam={lam:g} b={b:g} ensamble"] = series(e, metric)

    index = methods["Top-4 determinista"].index
    full, top4 = methods["Completa-22"].reindex(index), methods["Top-4 determinista"]
    rows = []
    for name, s in methods.items():
        s = s.reindex(index)
        if s.isna().all():
            continue
        by_ds = s.groupby(level=0).mean()
        rows.append({
            "metodo": name,
            "macro_f1_por_dataset": float(by_ds.mean()),
            "vs_top4": float(by_ds.mean() - top4.groupby(level=0).mean().mean()),
            "vs_completa22": float(by_ds.mean() - full.groupby(level=0).mean().mean()),
            "gana_top4": int((s > top4).sum()),
            "gana_completa22": int((s > full).sum()),
            "n": int(s.notna().sum()),
            **{f"ds_{d}": float(v) for d, v in by_ds.items()},
        })
    table = pd.DataFrame(rows).sort_values("macro_f1_por_dataset", ascending=False)

    print(f"condiciones: {len(index)}   datasets: {index.get_level_values(0).nunique()}\n")
    print(f"{'metodo':<36}{'F1':>8}{'vs Top-4':>10}{'vs C-22':>10}"
          f"{'gana T4':>9}{'gana C22':>10}")
    for _, r in table.iterrows():
        print(f"{r['metodo']:<36}{r['macro_f1_por_dataset']:>8.4f}{r['vs_top4']:>+10.4f}"
              f"{r['vs_completa22']:>+10.4f}{r['gana_top4']:>6}/{r['n']:<3}"
              f"{r['gana_completa22']:>6}/{r['n']}")

    ds_cols = [c for c in table.columns if c.startswith("ds_")]
    print("\nPOR DATASET (los mejores de cada familia)")
    keep = ["Completa-22", "Top-4 determinista"]
    for prefix in ("Tombola", "Diversidad"):
        fam = table[table.metodo.str.startswith(prefix)]
        if len(fam):
            keep.append(fam.iloc[0]["metodo"])
    sub = table.set_index("metodo").loc[keep, ds_cols]
    sub.columns = [c[3:] for c in ds_cols]
    print(sub.T.round(4).to_string())

    # Which blocks the diversity rule actually picks on Outex13.
    print("\nOUTEX13: subconjunto de 4 bloques segun lambda")
    for p in glob.glob(str(args.root / "diversity/outex13/*_diversity.json")):
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        print(f"  Top-4: {'+'.join(d['topk']['subset'])}  "
              f"(CKA {d['topk']['mean_cka']:.3f}, F1 {d['topk']['macro_f1']:.4f})")
        seen = set()
        for c in d["cells"]:
            lam = c["lambda"]
            if lam in seen:
                continue
            seen.add(lam)
            g = c["greedy"]
            print(f"  lam={lam:<5}{'+'.join(g['subset'])}  "
                  f"(CKA {g['mean_cka']:.3f}, F1 {g['macro_f1']:.4f})")

    args.output.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output / "k4_professor.csv", index=False)
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
