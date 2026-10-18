#!/usr/bin/env python3
"""Non-parametric tests for the selection methods, with the manuscript's tools.

The manuscript compares strategies with the SCI2S Java suite (Friedman,
Iman-Davenport, aligned Friedman and Quade, then Holm and Shaffer over all
pairs) on one value per dataset.  The same is done here for two families per
classifier:

``metodos``  the eight methods of the report's method table;
``control``  the two sampling ensembles against the two ensembles that keep the
             subset fixed at Top-4 (seed and bagging), and Top-4 itself.

Exact two-sided Wilcoxon tests on the six dataset means are added for the pairs
the report discusses, together with win counts over the external conditions,
which are descriptive only because conditions of one dataset share images.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from scipy.stats import wilcoxon

REPO = Path(__file__).resolve().parents[1]
KEYS = ["dataset", "seed", "outer_fold"]
SOURCE = REPO / "paper/articulo/borrador_profesor/generated/primary22_beitv2_source_rows.csv"
ROOTS = {"svm": REPO / "results/exploratory", "resmlp": REPO / "results/exploratory/resmlp"}
TOOLS = REPO / ".tools/nonparametric"
SHORT = {"Outex13Official1360": "Outex", "KTHTIPS2b": "KTH-TIPS2-b", "SoilOriginal": "Soil"}
PAIRS = [("Ens-diversidad", "Completa-22"), ("Ens-tombola", "Completa-22"),
         ("Top-4", "Completa-22"), ("Ens-diversidad", "Top-4"), ("Ens-tombola", "Top-4"),
         ("Ens-diversidad", "Ens-bagging"), ("Ens-tombola", "Ens-bagging"),
         ("Ens-diversidad", "Ens-semillas"), ("Ens-tombola", "Ens-semillas")]


def read_all(pattern) -> pd.DataFrame:
    paths = glob.glob(str(pattern))
    return pd.concat([pd.read_csv(p) for p in paths], ignore_index=True) if paths else pd.DataFrame()


def conditions(clf: str) -> dict[str, pd.Series]:
    """Macro-F1 of every method, one value per external condition."""
    root = ROOTS[clf]
    sweep = read_all(root / "k_sweep/*/k_sweep.csv")
    sweep = sweep[sweep.classifier.eq(clf)]
    index = sweep[sweep.k.eq(1)].drop_duplicates(KEYS).set_index(KEYS).index
    s = lambda f: f.drop_duplicates(KEYS).set_index(KEYS)["macro_f1"].reindex(index)
    src = pd.read_csv(SOURCE)
    src = src[src.run_mode.eq("full") & src.classifier.eq(clf)].copy()
    src["method"] = src["method"].str.replace("best_homogeneous_.*", "homogeneous", regex=True)
    lot = read_all(root / "k4/lottery/*/lottery_rows.csv")
    lot = lot[lot.classifier.eq(clf) & lot.k.eq(4)]
    div = read_all(root / "k4/diversity/*/diversity_rows.csv")
    div = div[div.classifier.eq(clf) & div.k.eq(4)]
    div = div.assign(lam=pd.to_numeric(div["lambda"], errors="coerce"),
                     bet=pd.to_numeric(div["beta"], errors="coerce"))
    out = {
        "Completa-22": s(src[src.method.eq("full_concat")]),
        "Ens-diversidad": s(div[div.variant.eq("ensemble_soft") & div.lam.eq(0.25) & div.bet.eq(8.0)]),
        "Ens-tombola": s(lot[lot.variant.eq("ensemble_soft") & lot.beta.astype(float).eq(8.0)]),
        "Top-4": s(sweep[sweep.k.eq(4)]),
        "Top-k": s(src[src.method.eq("topk_individual")]),
        "GFS": s(src[src.method.eq("gfs")]),
        "Homogenea": s(src[src.method.eq("homogeneous")]),
        "Individual": s(src[src.method.eq("best_individual")]),
    }
    ctl = read_all(REPO / f"results/exploratory/ensemble_control/{clf}/*/control_rows.csv")
    if len(ctl):
        out["Ens-semillas"] = s(ctl[ctl.variant.eq("seed_ensemble")])
        out["Ens-bagging"] = s(ctl[ctl.variant.eq("bagging_ensemble")])
    return out


def java_command() -> tuple[list[str], bool]:
    if shutil.which("java"):
        return ["java"], False
    win = Path("/mnt/c/Program Files/Java/jdk-17/bin/java.exe")
    if win.exists():
        return [str(win)], True
    raise FileNotFoundError("no Java runtime found")


def run_sci2s(matrix: pd.DataFrame, path: Path) -> dict:
    matrix.to_csv(path, float_format="%.12f", index_label="Data-set")
    java, windows = java_command()
    arg = (subprocess.run(["wslpath", "-w", str(path)], capture_output=True, text=True,
                          check=True).stdout.strip() if windows else str(path))
    texts = {}
    for tool in ("controlTest", "multipleTest"):
        res = subprocess.run(java + ["Friedman", arg], cwd=TOOLS / tool,
                             capture_output=True, text=True, check=True)
        texts[tool] = res.stdout
        path.with_name(f"{path.stem}_{tool}.tex").write_text(res.stdout, encoding="utf-8")
    ctrl, mult = texts["controlTest"], texts["multipleTest"]
    num = r"([0-9.Ee+-]+)"
    def pval(label):
        m = re.search(rf"P-value computed by {label}: {num}", ctrl)
        return float(m.group(1).rstrip(".")) if m else None
    def ranking(test):
        chunk = ctrl.split(f"Average Rankings of the algorithms ({test})")[1].split(r"\end{tabular}")[0]
        return {a.strip(): float(r) for a, r in re.findall(r"^([^&\n]+)&([0-9.]+)\\\\", chunk, re.M)}
    pairs = {}
    tables = mult.split("Adjusted $p$-values")
    body = tables[-1].split(r"\end{tabular}")[0]
    for line in body.splitlines():
        f = line.rstrip("\\").split("&")
        if len(f) >= 7 and f[0].strip().isdigit():
            a, b = [x.strip(" .") for x in f[1].split("vs")]
            # SCI2S prints adjusted values without capping them at one.
            pairs[f"{a} vs {b}"] = {"p": float(f[2]), "holm": min(1.0, float(f[4])),
                                    "shaffer": min(1.0, float(f[5]))}
    return {"ranks": ranking("Friedman"), "aligned_ranks": ranking("Aligned Friedman"),
            "quade_ranks": ranking("Quade"), "friedman_p": pval("Friedman Test"),
            "iman_davenport_p": pval("Iman and Daveport Test"),
            "aligned_friedman_p": pval("Aligned Friedman Test"),
            "quade_p": pval("Quade Test"), "pairs": pairs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=REPO / "results/analysis/selection_stats")
    parser.add_argument("--tables-only", action="store_true",
                        help="rewrite the LaTeX tables from the saved JSON without running the tests")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.tables_only:
        report = json.loads((args.output / "selection_stats.json").read_text(encoding="utf-8"))
        write_paper_tables(report, args.output)
        write_supplementary(args.output)
        return
    report = {}
    for clf in ("svm", "resmlp"):
        cond = conditions(clf)
        # A dataset mean only counts when every condition of that dataset is present.
        per_ds = pd.DataFrame({m: s.groupby(level="dataset").agg(
            lambda v: v.mean() if v.notna().all() else np.nan) for m, s in cond.items()})
        per_ds.index = [SHORT.get(d, d) for d in per_ds.index]
        families = {"metodos": ["Completa-22", "Ens-diversidad", "Ens-tombola", "Top-4",
                                "Top-k", "GFS", "Homogenea", "Individual"],
                    "control": ["Ens-diversidad", "Ens-tombola", "Ens-bagging",
                                "Ens-semillas", "Top-4"]}
        report[clf] = {"per_dataset": per_ds.round(6).to_dict(), "families": {}, "wilcoxon": []}
        print(f"\n################ {clf.upper()} ################")
        for fam, methods in families.items():
            if any(m not in per_ds or per_ds[m].isna().any() for m in methods):
                print(f"  familia {fam}: faltan datos, se omite")
                continue
            res = run_sci2s(per_ds[methods], args.output / f"{clf}_{fam}.csv")
            report[clf]["families"][fam] = res
            print(f"  familia {fam}: Friedman p={res['friedman_p']:.4f}  Iman-Davenport "
                  f"p={res['iman_davenport_p']:.4f}  Friedman alineado p={res['aligned_friedman_p']:.4f}  "
                  f"Quade p={res['quade_p']:.4f}")
            for m, r in sorted(res["ranks"].items(), key=lambda kv: kv[1]):
                print(f"     {m:<16} rango {r:.3f}")
            sig = {k: v for k, v in res["pairs"].items() if v["holm"] < 0.05}
            print(f"     pares con Holm < 0,05: {len(sig)} de {len(res['pairs'])}"
                  + "".join(f"\n        {k}: Holm {v['holm']:.4f}" for k, v in sig.items()))
        for a, b in PAIRS:
            if any(m not in per_ds or per_ds[m].isna().any() for m in (a, b)):
                continue
            d = per_ds[a] - per_ds[b]
            # Zero differences are dropped before ranking; W is the smaller rank sum.
            test = wilcoxon(d, alternative="two-sided", method="exact") if (d != 0).any() else None
            p = float(test.pvalue) if test else 1.0
            c = (cond[a] - cond[b]).dropna()
            row = {"pair": f"{a} vs {b}", "mean_diff": float(d.mean()),
                   "datasets_won": int((d > 0).sum()), "datasets_lost": int((d < 0).sum()),
                   "wilcoxon_w": float(test.statistic) if test else 0.0,
                   "wilcoxon_exact_p": p, "conditions_won": int((c > 0).sum()),
                   "conditions_lost": int((c < 0).sum()), "conditions": int(len(c))}
            report[clf]["wilcoxon"].append(row)
            print(f"  {row['pair']:<32} {row['mean_diff']:+.4f}  datasets {row['datasets_won']}-"
                  f"{row['datasets_lost']}  Wilcoxon p={p:.4f}  condiciones {row['conditions_won']}-"
                  f"{row['conditions_lost']} de {row['conditions']}")
    (args.output / "selection_stats.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_paper_tables(report, args.output)
    write_supplementary(args.output)
    print(f"\nescrito en {args.output}")


LATEX = {"Completa-22": "Completa-22", "Ens-diversidad": r"Ens.\ diversidad",
         "Ens-tombola": r"Ens.\ tómbola", "Ens-semillas": r"Ens.\ semillas",
         "Ens-bagging": r"Ens.\ bagging", "Top-4": "Top-4", "Top-k": r"Top-$k$", "GFS": "GFS",
         "Homogenea": "Homogénea", "Individual": "Individual"}
CLF = {"svm": "SVM", "resmlp": "ResMLP"}


def num(x: float, digits: int = 4) -> str:
    return f"${x:.{digits}f}$".replace(".", "{,}")


def table(caption: str, label: str, spec: str, header: str, rows: list[str]) -> str:
    return "\n".join([r"\begin{table}[H]", r"\centering\fontsize{8}{10}\selectfont"
                      r"\setlength{\tabcolsep}{3.0pt}", rf"\caption{{{caption}}}",
                      rf"\label{{{label}}}", rf"\begin{{tabular}}{{{spec}}}", r"\toprule",
                      header + r" \\", r"\midrule", *rows, r"\bottomrule", r"\end{tabular}",
                      r"\end{table}", ""])


def write_paper_tables(report: dict, out: Path) -> None:
    """The manuscript's four statistics tables, for the methods of this study."""
    for fam, what in (("metodos", "ocho métodos"), ("control", "cinco variantes del control")):
        if not all(fam in report[c]["families"] for c in CLF):
            continue
        rows = []
        for clf, name in CLF.items():
            res = report[clf]["families"][fam]
            for m in res["ranks"]:
                rows.append(f"{name} & {LATEX[m]} & {num(res['ranks'][m], 3)} & "
                            f"{num(res['aligned_ranks'][m], 3)} & {num(res['quade_ranks'][m], 3)} \\\\")
        rank_tex = table(f"Rankings medios de macro-F1 según Friedman, Friedman alineado y Quade: "
                         f"{what}. Seis datasets por clasificador; menor ranking indica mejor "
                         f"desempeño relativo dentro de cada prueba.", f"tab:sel-{fam}-rankings",
                         "@{}llrrr@{}", "Clasif. & Método & Friedman & F. alineado & Quade", rows)
        rows = []
        for clf, name in CLF.items():
            res = report[clf]["families"][fam]
            for label, key in (("Friedman", "friedman_p"), ("Iman--Davenport", "iman_davenport_p"),
                               ("Friedman alineado", "aligned_friedman_p"), ("Quade", "quade_p")):
                rows.append(f"{name} & {label} & {num(res[key])} & "
                            f"{'Rechazo' if res[key] < 0.05 else 'No rechazo'} \\\\")
        global_tex = table(f"Pruebas globales por clasificador: {what} y seis datasets. "
                           r"Nivel nominal $\alpha=0{,}05$.", f"tab:sel-{fam}-global",
                           "@{}llrl@{}", r"Clasif. & Prueba & $p$ & Decisión", rows)
        rows = []
        for clf, name in CLF.items():
            pairs = report[clf]["families"][fam]["pairs"]
            for pair, v in sorted(pairs.items(), key=lambda kv: (kv[1]["p"], kv[0])):
                a, b = pair.split(" vs ")
                rows.append(f"{name} & {LATEX[a]} vs.\\ {LATEX[b]} & {num(v['p'])} & "
                            f"{num(v['holm'])} \\\\")
        n_pairs = len(next(iter(report.values()))["families"][fam]["pairs"])
        holm_tex = table(f"Comparaciones por pares basadas en rangos de Friedman: {what}. Holm "
                         f"corrige los {n_pairs} pares dentro de cada clasificador.",
                         f"tab:sel-{fam}-holm", "@{}llrr@{}",
                         r"Clasif. & Comparación & $p$ sin ajustar & $p$ Holm", rows)
        (out / f"tabla_{fam}.tex").write_text(rank_tex + global_tex + holm_tex, encoding="utf-8")
    rows = []
    for clf, name in CLF.items():
        for r in report[clf]["wilcoxon"]:
            a, b = r["pair"].split(" vs ")
            n = r["datasets_won"] + r["datasets_lost"]
            rows.append(f"{name} & {LATEX[a]} menos {LATEX[b]} & {num(r['mean_diff'])} & "
                        f"{r['datasets_won']}/{n} & {num(r['wilcoxon_w'], 0)} & "
                        f"{num(r['wilcoxon_exact_p'])} & "
                        f"{r['conditions_won']}--{r['conditions_lost']} \\\\")
    sens_tex = table(r"Sensibilidad: Wilcoxon exacto bilateral sobre seis datasets. V indica "
                     r"datasets con diferencia positiva sobre los que no empatan y $W$ la menor "
                     r"suma de rangos. Cond.: condiciones externas ganadas y perdidas, "
                     r"descriptivo.", "tab:sel-sensitivity", "@{}llrrrrr@{}",
                     r"Clasif. & Diferencia & $\Delta$ medio & V & $W$ & $p$ & Cond.", rows)
    (out / "tabla_wilcoxon.tex").write_text(sens_tex, encoding="utf-8")


MARGIN = 0.01  # one macro-F1 point, fixed before looking at the non-inferiority tests


def per_dataset(series: pd.Series) -> pd.Series:
    return series.groupby(level="dataset").mean().rename(index=lambda d: SHORT.get(d, d))


def write_supplementary(out: Path) -> None:
    """Non-inferiority against Completa-22, spread across conditions and the
    sensitivity of the sampling ensembles to their configuration."""
    result = {"margin": MARGIN, "noninferiority": [], "spread": [], "sensitivity": []}
    for clf in CLF:
        cond = conditions(clf)
        base = per_dataset(cond["Completa-22"])
        for m in ("Top-4", "Ens-diversidad", "Ens-tombola"):
            d = per_dataset(cond[m]) - base
            n = len(d)
            se = float(d.std(ddof=1) / np.sqrt(n))
            lower = float(d.mean() - student_t.ppf(0.95, df=n - 1) * se)
            shifted = d + MARGIN
            result["noninferiority"].append({
                "classifier": clf, "method": m, "mean_diff": float(d.mean()),
                "lower_95": lower, "smallest_margin": max(0.0, -lower),
                "t_p": float(student_t.sf(shifted.mean() / se, df=n - 1)),
                "wilcoxon_p": float(wilcoxon(shifted, alternative="greater",
                                             method="exact").pvalue)})
        for ds, g in pd.DataFrame({m: cond[m] for m in ("Top-4", "Completa-22",
                                                         "Ens-diversidad")}).groupby(level="dataset"):
            result["spread"].append({"classifier": clf, "dataset": SHORT.get(ds, ds),
                                     "conditions": int(len(g)),
                                     **{f"{m}_mean": float(g[m].mean()) for m in g},
                                     **{f"{m}_sd": float(g[m].std(ddof=1)) if len(g) > 1
                                        else None for m in g}})
        root = ROOTS[clf]
        lot = read_all(root / "k4/lottery/*/lottery_rows.csv")
        lot = lot[lot.classifier.eq(clf) & lot.k.eq(4) & lot.variant.eq("ensemble_soft")]
        div = read_all(root / "k4/diversity/*/diversity_rows.csv")
        div = div[div.classifier.eq(clf) & div.k.eq(4) & div.variant.eq("ensemble_soft")]
        cells = [("tombola", float(b), None, g) for b, g in lot.groupby("beta")]
        cells += [("diversidad", float(b), float(lam), g)
                  for (lam, b), g in div.groupby(["lambda", "beta"])]
        for method, beta, lam, g in cells:
            g = g.drop_duplicates(KEYS).set_index(KEYS)["macro_f1"]
            result["sensitivity"].append({"classifier": clf, "method": method, "beta": beta,
                                          "lambda": lam, "conditions": int(len(g)),
                                          "macro_f1": float(per_dataset(g).mean())})
    (out / "supplementary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    rows = [f"{CLF[r['classifier']]} & {LATEX[r['method']]} & {num(r['mean_diff'])} & "
            f"{num(r['lower_95'])} & {num(r['smallest_margin'])} & {num(r['t_p'])} & "
            f"{num(r['wilcoxon_p'])} \\\\" for r in result["noninferiority"]]
    ni_tex = table(r"No inferioridad frente a Completa-22 sobre las medias de seis datasets. "
                   r"Cota: límite inferior unilateral al 95\,\% de la diferencia media ($t$ de "
                   r"Student). Margen mínimo: la mayor pérdida que la cota permite descartar. "
                   rf"$p$: hipótesis nula de pérdida mayor o igual a {num(MARGIN, 2)}.",
                   "tab:sel-noninferiority", "@{}llrrrrr@{}",
                   r"Clasif. & Método & $\Delta$ medio & Cota 95\,\% & Margen mín. & "
                   r"$p$ ($t$) & $p$ (Wilcoxon)", rows)
    fmt = lambda r, m: (f"{num(r[m + '_mean'])} $\\pm$ {num(r[m + '_sd'])}"
                        if r[m + "_sd"] is not None else num(r[m + "_mean"]))
    rows = [f"{CLF[r['classifier']]} & {r['dataset']} & {r['conditions']} & "
            f"{fmt(r, 'Top-4')} & {fmt(r, 'Completa-22')} & {fmt(r, 'Ens-diversidad')} \\\\"
            for r in result["spread"]]
    spread_tex = table(r"Macro-F1 por dataset: media $\pm$ desvío estándar entre condiciones "
                       r"externas. Outex13 tiene una sola partición.", "tab:sel-spread",
                       "@{}llrlll@{}", r"Clasif. & Dataset & Cond. & Top-4 & Completa-22 & "
                       r"Ens.\ diversidad", rows)
    rows = []
    for r in result["sensitivity"]:
        cfg = (f"$\\beta={r['beta']:g}$" if r["lambda"] is None
               else f"$\\lambda={r['lambda']:g}$, $\\beta={r['beta']:g}$").replace(".", "{,}")
        rows.append(f"{CLF[r['classifier']]} & {LATEX['Ens-' + r['method']]} & {cfg} & "
                    f"{num(r['macro_f1'])} \\\\")
    sens_tex = table(r"Sensibilidad de los ensambles a su configuración: macro-F1 medio sobre "
                     r"las 47 condiciones. $\beta=0$ es el sorteo uniforme, sin ranking.",
                     "tab:sel-config", "@{}lllr@{}",
                     r"Clasif. & Ensamble & Configuración & Macro-F1", rows)
    (out / "tabla_no_inferioridad.tex").write_text(ni_tex, encoding="utf-8")
    (out / "tabla_variabilidad.tex").write_text(spread_tex, encoding="utf-8")
    (out / "tabla_configuracion.tex").write_text(sens_tex, encoding="utf-8")
    for r in result["noninferiority"]:
        print(f"  no inferioridad {r['classifier']:<6} {r['method']:<15} dif {r['mean_diff']:+.4f} "
              f"cota95 {r['lower_95']:+.4f} margen_min {r['smallest_margin']:.4f} "
              f"p_t {r['t_p']:.4f} p_wilcoxon {r['wilcoxon_p']:.4f}")
    write_extensions(out)


def dataset_mean(frame: pd.DataFrame, by: list[str], value: str) -> pd.Series:
    """Mean within each dataset first, then across datasets."""
    return frame.groupby(by + ["dataset"])[value].mean().groupby(level=by).mean()


def write_extensions(out: Path) -> None:
    """Tables for the ensemble size, the ResMLP capacity diagnostic and the cost."""
    rows = []
    for clf, name in CLF.items():
        size = read_all(REPO / f"results/exploratory/ensemble_size/{clf}/*/size_rows.csv")
        if size.empty:
            continue
        curve = dataset_mean(size, ["method", "members"], "macro_f1").unstack("members")
        for method in ("tombola", "diversidad"):
            rows.append(f"{name} & {LATEX['Ens-' + method]} & "
                        + " & ".join(num(v) for v in curve.loc[method]) + r" \\")
    if rows:
        sizes = curve.columns.tolist()
        (out / "tabla_tamano.tex").write_text(table(
            r"Macro-F1 medio de los ensambles según la cantidad de modelos: prefijos de una "
            r"misma secuencia de 50 sorteos, cuyos primeros 15 son los de los ensambles "
            r"reportados. Con 15 sorteos hay en promedio entre 10,6 y 11,8 subconjuntos "
            r"distintos.",
            "tab:sel-size", "@{}ll" + "r" * len(sizes) + "@{}",
            "Clasif. & Ensamble & " + " & ".join(str(s) for s in sizes), rows), encoding="utf-8")

    cap = read_all(REPO / "results/exploratory/resmlp_capacity/*/capacity_rows.csv")
    if not cap.empty:
        order = ["all21", "all21_pca", "all21_regularized", "top4"]
        per = cap.groupby(["dataset", "variant"]).macro_f1.mean().unstack("variant")[order]
        per = per.rename(index=lambda d: SHORT.get(d, d)).sort_index()
        rows = [f"{ds} & " + " & ".join(num(v) for v in r) + r" \\" for ds, r in per.iterrows()]
        rows.append(r"\midrule")
        rows.append("Media & " + " & ".join(num(v) for v in per.mean()) + r" \\")
        wins = cap.pivot_table(index=KEYS, columns="variant", values="macro_f1")
        rows.append("Gana a 21 bloques & --- & " + " & ".join(
            f"{int((wins[v] > wins.all21).sum())}/{len(wins)}" for v in order[1:]) + r" \\")
        params = dataset_mean(cap, ["variant"], "parameters")[order]
        rows.append("Parámetros (miles) & " + " & ".join(
            f"{p / 1000:,.0f}".replace(",", ".") for p in params) + r" \\")
        train = dataset_mean(cap, ["variant"], "train_accuracy")[order]
        rows.append("Exactitud en entrenamiento & " + " & ".join(num(v, 3) for v in train) + r" \\")
        (out / "tabla_capacidad.tex").write_text(table(
            r"ResMLP con los 21 bloques: macro-F1 externo al reducir la entrada con PCA, "
            r"ajustado en el entrenamiento, a tantos componentes como dimensiones tiene el "
            r"Top-4 (o imágenes de entrenamiento menos una, si son menos), y al aumentar la "
            r"regularización (\emph{dropout} 0,3 y decaimiento de pesos 0,01).",
            "tab:sel-capacity", "@{}lrrrr@{}",
            r"Dataset & 21 bloques & 21 + PCA & 21 + regularización & Top-4", rows),
            encoding="utf-8")

    cost = pd.concat([read_all(REPO / f"results/exploratory/selection_cost/{c}/*/cost_rows.csv")
                      for c in CLF], ignore_index=True)
    # One condition per dataset, four methods, two classifiers.
    if len(cost.drop_duplicates(["dataset", "classifier", "method"])) == 48:
        order = ["top4", "all21", "tombola", "diversidad"]
        label = {"top4": "Top-4", "all21": "21 bloques", "tombola": r"Ens.\ tómbola",
                 "diversidad": r"Ens.\ diversidad"}
        total = cost.groupby(["classifier", "method"])[
            ["selection_seconds", "fit_seconds", "total_train_seconds", "predict_seconds",
             "parameters"]].sum()
        dims = cost.groupby("method").dimensions.mean()
        rows = []
        for m in order:
            cells = [label[m], f"{dims[m]:,.0f}".replace(",", ".")]
            for clf in CLF:
                r = total.loc[(clf, m)]
                cells += [f"{r.selection_seconds:,.0f}".replace(",", "."),
                          f"{r.fit_seconds:,.0f}".replace(",", "."),
                          f"{r.total_train_seconds:,.0f}".replace(",", "."),
                          num(r.predict_seconds, 2)]
            rows.append(" & ".join(cells) + r" \\")
        header = (r" & & \multicolumn{4}{c}{SVM} & \multicolumn{4}{c@{}}{ResMLP} \\"
                  "\n" r"\cmidrule(lr){3-6}\cmidrule(l){7-10}" "\n"
                  r"Método & Dims & Selección & Ajuste & Total & Predicción & Selección & "
                  r"Ajuste & Total & Predicción")
        (out / "tabla_costo.tex").write_text(table(
            r"Costo en segundos, sumado sobre una condición por dataset y ejecutado en serie. "
            r"Selección: ranking interno de los 21 bloques (y CKA para diversidad). Ajuste: "
            r"un modelo por subconjunto distinto. Predicción: imágenes de test. Dims: media "
            r"por modelo. 21 bloques: la concatenación completa sin el bloque de color. "
            r"SVM en CPU; ResMLP en GPU.", "tab:sel-cost", "@{}lrrrrrrrrr@{}", header, rows),
            encoding="utf-8")


if __name__ == "__main__":
    main()
