"""SCI2S sensitivity of the static benchmark with/without archived KTH.

Separate classifier analyses; original tables and predictions remain untouched.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, norm, rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_primary22_beitv2_paper import METHODS, LABELS, DATASETS, parse_java

BASE = ROOT / "results/primary22_beitv2/nonparametric/classifier_specific"
OUT = ROOT / "results/analysis/mesa_grado_20261025_r2/kth_sensitivity"
TEX = ROOT / "paper/generated_mesa_r2"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(x):
    return f"{x:.4f}".replace(".", "{,}")


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    TEX.mkdir(exist_ok=True)
    global_rows, pairs_rows, records, all_pairs = [], [], [], []
    inputs = [Path(__file__), ROOT / "scripts/build_primary22_beitv2_paper.py"]
    for clf, display in (("svm", "SVM"), ("resmlp", "ResMLP")):
        src = BASE / f"{clf}_by_dataset.csv"
        matrix = pd.read_csv(src).set_index("Data-set")
        assert matrix.shape == (6, 5)
        inputs += [src, BASE / f"{clf}_controltest.tex", BASE / f"{clf}_multipletest.tex"]
        archived = parse_java((BASE / f"{clf}_controltest.tex").read_text(),
                              (BASE / f"{clf}_multipletest.tex").read_text())
        for n in (6, 5):
            m = matrix if n == 6 else matrix.iloc[:5]
            assert ("KTH" in str(matrix.index[-1])) and all("KTH" not in x for x in m.index[:5])
            csv_path = OUT / f"{clf}_n{n}.csv"
            m.to_csv(csv_path, float_format="%.12f")
            outputs = {}
            for tool in ("controlTest", "multipleTest"):
                folder = ROOT / ".tools/nonparametric" / tool
                inputs += [folder / "Friedman.class"]
                result = subprocess.run(["/usr/bin/java", "Friedman", str(csv_path)], cwd=folder,
                                        capture_output=True, text=True, check=True)
                assert "\\end{document}" in result.stdout
                (OUT / f"{clf}_n{n}_{tool}.tex").write_text(result.stdout)
                outputs[tool] = result.stdout
            ranks, globals_, pairs = parse_java(outputs["controlTest"], outputs["multipleTest"])
            # Independent numerical checks of primary ranks and Holm family.
            scipy_test = friedmanchisquare(*[m[k].to_numpy() for k in m.columns])
            assert abs(scipy_test.pvalue - globals_["Friedman"]) < 1e-6
            means = np.array([rankdata(-row) for row in m.to_numpy()]).mean(axis=0)
            raw = []
            for i in range(5):
                for j in range(i + 1, 5):
                    p = 2 * norm.sf(abs(means[i] - means[j]) / np.sqrt(5 * 6 / (6 * n)))
                    raw.append((f"{m.columns[i]} vs. {m.columns[j]}", float(p)))
            raw.sort(key=lambda x: x[1])
            holm, current = {}, 0.
            for k, (comparison, p) in enumerate(raw):
                current = min(1., max(current, (10 - k) * p))
                holm[frozenset(comparison.split(" vs. "))] = (p, current)
            for comparison, p, adjusted in pairs:
                expected = holm[frozenset(comparison.split(" vs. "))]
                assert max(abs(p - expected[0]), abs(adjusted - expected[1])) < 1e-6
                all_pairs.append({"classifier": clf, "n_datasets": n, "comparison": comparison,
                                  "p": p, "p_holm": adjusted})
                if n == 5:
                    pairs_rows.append(" & ".join([display, comparison, "$" + number(p) + "$",
                                                  "$" + number(adjusted) + "$"]) + r"\\")
            if n == 6:
                assert all(abs(globals_[k] - archived[1][k]) < 1e-12 for k in globals_)
                assert pairs == archived[2]
            record = {"classifier": clf, "n_datasets": n, "datasets": list(m.index),
                      "global_p": globals_, "friedman_ranks": dict(zip(m.columns, means.tolist()))}
            records.append(record)
            global_rows.append(" & ".join([display, str(n)] +
                ["$" + number(globals_[k]) + "$" for k in
                 ("Friedman", "Iman--Davenport", "Aligned Friedman", "Quade")]) + r"\\")
    global_tex = [r"\begin{table}[!htbp]", r"\centering\fontsize{8}{10}\selectfont",
        r"\caption{Sensibilidad del benchmark estático a excluir KTH archivado: seis datasets originales frente a los cinco restantes. Valores $p$ SCI2S por clasificador; no son evaluaciones del híbrido.}",
        r"\label{tab:kth-sensibilidad-global}", r"\begin{tabular}{@{}llrrrr@{}}", r"\toprule",
        r"Clasif. & $N$ & Friedman & Iman--D. & F. alineado & Quade\\", r"\midrule",
        *global_rows, r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    pairs_tex = [r"\begin{table}[!htbp]", r"\centering\fontsize{8}{10}\selectfont",
        r"\caption{Sensibilidad sin KTH: post-hoc de rangos de Friedman sobre cinco datasets. Holm corrige diez pares por clasificador. Son contrastes exploratorios, no Wilcoxon exactos.}",
        r"\label{tab:kth-sensibilidad-holm}", r"\begin{tabular}{@{}llrr@{}}", r"\toprule",
        r"Clasif. & Comparación & $p$ & $p_{\mathrm{Holm}}$\\", r"\midrule",
        *pairs_rows, r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (TEX / "kth_sensibilidad_global.tex").write_text("\n".join(global_tex) + "\n")
    (TEX / "kth_sensibilidad_holm.tex").write_text("\n".join(pairs_tex) + "\n")
    pd.DataFrame(all_pairs).to_csv(OUT / "paired_results.csv", index=False)
    result = {"status": "ANALYZED", "scope": "Archived benchmark sensitivity, not KTH reconciliation or independent fitting",
              "records": records, "holm_family_size": 10,
              "n6_reproduces_archived_java": True, "python_primary_check": True,
              "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in set(inputs)}}
    (OUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    provenance = {"input_sha256": result["input_sha256"],
                  "output_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
                                     [TEX / "kth_sensibilidad_global.tex", TEX / "kth_sensibilidad_holm.tex"]}}
    (TEX / "statistics_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
