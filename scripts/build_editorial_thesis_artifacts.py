"""Render tables/plot from archived results without fitting or changing sources."""
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_primary22_beitv2_paper import load_sources, SOURCES_22, METHODS

OUT = ROOT / "paper/generated_editorial"
HYBRID = ROOT / "results/exploratory/integration_v8/carlos_hybrid_outex22_20261021"
PAIRED = ROOT / "results/exploratory/integration_v7/outex_paired22_20261021"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def number(x, digits=6):
    return f"{x:.{digits}f}".replace(".", ",")


def main():
    OUT.mkdir(exist_ok=False)
    h, p = [pd.read_csv(root / "results.csv").set_index("policy")
            for root in (HYBRID, PAIRED)]
    labels = [("Individual interno", p.loc["best_individual"]),
              ("Top-3", p.loc["top3"]), ("Top-4", p.loc["top4"]),
              ("Top-5", p.loc["top5"]), ("Completa-22", p.loc["full_library"]),
              ("Diversidad15 permanente", h.loc["carlos_diversity15_always"])]
    lines = [r"\begin{table}[!htbp]", r"\centering\small",
             r"\caption{Controles del mismo piloto Outex: macro-F1 OOF sobre 680 imágenes de entrenamiento oficial y costo medio proyectado, no latencia física.}",
             r"\label{tab:controles-hibrido}", r"\begin{tabular}{@{}lrr@{}}",
             r"\toprule", r"Control & Macro-F1 & Costo proyectado ms\\", r"\midrule"]
    for label, row in labels:
        lines.append(f"{label} & {number(row.macro_f1_oof)} & {number(row.projected_ms,3)}" + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (OUT / "controles_hibrido.tex").write_text("\n".join(lines) + "\n")

    meta = json.loads((HYBRID / "metadata.json").read_text())
    profile = meta["provenance"]["cost_profile"]
    lines = [r"\begin{longtable}{@{}lr@{}}",
             r"\caption{Constantes del perfil del piloto, en ms por imagen. Son parámetros archivados del modelo de costos, no tiempos medidos del híbrido.}\label{tab:perfil-costos}\\",
             r"\toprule Bloque & $c_j$ ms\\ \midrule \endfirsthead",
             r"\toprule Bloque & $c_j$ ms\\ \midrule \endhead"]
    for name, cost in sorted(profile["per_descriptor_latency_ms"].items()):
        lines.append(r"\texttt{" + name.replace("_", r"\_") + "} & " + number(cost,2) + r"\\")
    lines += [r"\midrule Sobrecosto de política & " + number(profile["policy_overhead_ms"],2) + r"\\",
              r"\bottomrule", r"\end{longtable}"]
    (OUT / "perfil_costos.tex").write_text("\n".join(lines) + "\n")

    static = load_sources(SOURCES_22, 22)
    sd = static.groupby(["dataset", "classifier", "method"]).macro_f1.std()
    names = {"DTD":"DTD", "FMD":"FMD", "CUReT":"CUReT",
             "Outex13Official1360":"Outex", "SoilOriginal":"Soil", "KTHTIPS2b":"KTH-TIPS2-b"}
    lines = [r"\begin{table}[!htbp]", r"\centering\fontsize{8}{10}\selectfont",
             r"\caption{Desviación estándar descriptiva del macro-F1 entre condiciones externas del benchmark estático. No es error estándar ni intervalo de confianza; las condiciones comparten imágenes. El guion indica un único split.}",
             r"\label{tab:variabilidad-estatica}", r"\begin{tabular}{@{}llrrrrr@{}}",
             r"\toprule Dataset & Clasif. & Individual & Completa & Top-$k$ & GFS & Homogénea\\ \midrule"]
    order = ["best_individual", "full_concat", "topk_individual", "gfs", "homogeneous"]
    for dataset in names:
        for clf in ("svm", "resmlp"):
            values = [sd.loc[dataset,clf,m] for m in order]
            lines.append(" & ".join([names[dataset], "SVM" if clf=="svm" else "ResMLP"] +
                         ["--" if pd.isna(x) else number(x,4) for x in values]) + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (OUT / "variabilidad_estatica.tex").write_text("\n".join(lines) + "\n")

    plt.rcParams.update({"font.size":9, "pdf.fonttype":42})
    fig, ax = plt.subplots(figsize=(7.4,4.5), layout="constrained")
    for prefix,label,color,marker in [
        ("full","Rescate completo","#0072B2","o"),
        ("pruned_marginal","Poda marginal","#D55E00","s"),
        ("pruned_relevance","Poda por relevancia","#009E73","^")]:
        rows = h.loc[[f"{prefix}_B{b}" for b in (15,30,60,120)]]
        ax.plot(rows.projected_ms, rows.macro_f1_oof, marker=marker,
                color=color, label=label, linewidth=1.4)
    controls = [(p.loc["best_individual"],"Individual","P"),
                (p.loc["top3"],"Top-3","x"), (p.loc["top4"],"Top-4","+"),
                (p.loc["top5"],"Top-5","D"),
                (h.loc["carlos_diversity15_always"],"Diversidad15 permanente","*"),
                (p.loc["full_library"],"Completa-22","X")]
    for row,label,marker in controls:
        ax.scatter(row.projected_ms, row.macro_f1_oof, marker=marker,
                   s=65, color="#444444", label=label, zorder=5)
    ax.set(xscale="log", xlabel="Costo medio proyectado (ms/imagen; escala logarítmica)",
           ylabel="Macro-F1 OOF de desarrollo", ylim=(.845,.924))
    ax.grid(alpha=.22, which="both")
    ax.legend(loc="lower right", fontsize=8, ncol=2, framealpha=.95)
    figure = ROOT / "paper/figures/hibrido_calidad_costo.pdf"
    fig.savefig(figure)
    plt.close(fig)
    sources = [HYBRID/"results.csv", HYBRID/"metadata.json", PAIRED/"results.csv"]
    sources += [r/"nested_fold_results.csv" for r in SOURCES_22]
    sources += [r/"topk_individual_control/nested_fold_results.csv" for r in SOURCES_22]
    outputs = list(OUT.glob("*.tex")) + [figure]
    provenance = {"scope":"Rendering of saved development/static results; no model fitting",
                  "input_sha256":{str(x.relative_to(ROOT)):digest(x) for x in sources},
                  "output_sha256":{str(x.relative_to(ROOT)):digest(x) for x in outputs},
                  "script_sha256":digest(Path(__file__))}
    (OUT/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print({"static_rows":len(static), "hybrid_rows":len(h),
           "control_rows":len(labels), "outputs":len(outputs)})


if __name__ == "__main__":
    main()
