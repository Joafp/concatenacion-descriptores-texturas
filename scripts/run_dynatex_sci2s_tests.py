#!/usr/bin/env python3
"""
Ejecución oficial de tests no paramétricos SCI2S (Java) para DynaTex-MoD:
Ejecuta controlTest y multipleTest de Friedman, Iman-Davenport, Holm, Hochberg, Finner, etc.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
JAVA_ROOT = REPO / ".tools" / "nonparametric"
OUT_DIR = REPO / "results" / "dynatex_nonparametric"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Datasets canónicos en orden estándar
DATASETS = ["DTD", "FMD", "CUReT", "Outex", "Soil", "KTH-TIPS2-b"]

# Cargar tablas canónicas previas
p22 = REPO / "results/primary22_beitv2/nonparametric/classifier_specific"
resmlp_df = pd.read_csv(p22 / "resmlp_by_dataset.csv").set_index("Data-set")
svm_df = pd.read_csv(p22 / "svm_by_dataset.csv").set_index("Data-set")

# Valores de DynaTex-MoD en los 6 datasets (Macro-F1)
dynatex_scores = {
    "DTD": 0.868571,
    "FMD": 0.976920,
    "CUReT": 0.999120,
    "Outex": 0.938465,
    "Soil": 0.863200,
    "KTH-TIPS2-b": 0.951710,
}

def run_java_tests(df_matrix: pd.DataFrame, experiment_name: str):
    csv_path = OUT_DIR / f"{experiment_name}.csv"
    df_matrix.to_csv(csv_path, float_format="%.12f")
    
    print(f"\n=======================================================")
    print(f" EJECUTANDO SCI2S JAVA: {experiment_name}")
    print(f"=======================================================")
    print(df_matrix.to_string())
    
    results = {}
    for tool_name, suffix in [("controlTest", "controltest"), ("multipleTest", "multipletest")]:
        cmd = ["java", "Friedman", str(csv_path)]
        res = subprocess.run(cmd, cwd=JAVA_ROOT / tool_name, capture_output=True, text=True, check=True)
        tex_out = OUT_DIR / f"{experiment_name}_{suffix}.tex"
        tex_out.write_text(res.stdout, encoding="utf-8")
        results[suffix] = res.stdout
    
    # Parse controlTest output
    ctrl = results["controltest"]
    mult = results["multipletest"]
    
    print("\n--- RANKINGS PROMEDIO (Friedman) ---")
    rank_chunk = ctrl.split("Average Rankings of the algorithms (Friedman)")[1].split(r"\end{tabular}")[0]
    ranks = dict(re.findall(r"^([^&\n]+)&([0-9.]+)\\\\", rank_chunk, re.M))
    for alg, r in sorted(ranks.items(), key=lambda x: float(x[1])):
        print(f"  {alg.strip():25s}: {float(r):.4f}")
        
    print("\n--- TESTS GLOBALES ---")
    p_friedman = float(re.search(r"P-value computed by Friedman Test: ([0-9.Ee+-]+)", ctrl)[1].rstrip("."))
    p_iman = float(re.search(r"P-value computed by Iman and Daveport Test: ([0-9.Ee+-]+)", ctrl)[1].rstrip("."))
    print(f"  Friedman Chi-cuadrado p-value : {p_friedman:.6e} ({'Rechazo H0 (Diferencias significativas)' if p_friedman < 0.05 else 'No rechazo'})")
    print(f"  Iman-Davenport F p-value      : {p_iman:.6e} ({'Rechazo H0 (Diferencias significativas)' if p_iman < 0.05 else 'No rechazo'})")

    print("\n--- POST-HOC COMPARISONS (vs Control / Pairwise) ---")
    if "i&hypothesis&unadjusted" in mult:
        body = mult.split("i&hypothesis&unadjusted")[1].split(r"\end{tabular}")[0]
        for line in body.splitlines():
            fields = line.rstrip("\\").split("&")
            if len(fields) >= 5 and fields[0].strip().isdigit():
                hyp = fields[1].replace("vs .", "vs. ").strip()
                p_unadj = float(fields[2].strip())
                p_adj = float(fields[4].strip())
                sig = "(* SIGNIFICATIVO *)" if p_adj < 0.05 else ("(Tendencia p<0.10)" if p_adj < 0.10 else "")
                print(f"  {hyp:35s}: p_unadj={p_unadj:.4f} | p_adj={p_adj:.4f} {sig}")

    return ranks, p_friedman, p_iman

def main():
    # 1. Comparación en el espacio Neuronal:
    # DynaTex vs ResMLP Completa vs ResMLP GFS vs ResMLP Top-k vs ResMLP Homogenea vs Individual
    df_neural = resmlp_df.copy()
    df_neural["DynaTex-MoD"] = [dynatex_scores[d] for d in df_neural.index]
    df_neural = df_neural.rename(columns={"Completa": "ResMLP-Completa"})
    # Reordenar columnas
    cols_neural = ["Individual", "ResMLP-Completa", "Top-$k$", "GFS", "Homogénea", "DynaTex-MoD"]
    df_neural = df_neural[cols_neural]
    df_neural.index.name = "Data-set"
    run_java_tests(df_neural, "dynatex_vs_neural_family")

    # 2. Comparación de Fusión Pura (Concatenación Plana vs Dinámica):
    # DynaTex-MoD vs Completa-SVM vs Completa-ResMLP vs Individual
    df_fusion = pd.DataFrame({
        "Individual": resmlp_df["Individual"],
        "ResMLP-Completa": resmlp_df["Completa"],
        "SVM-Completa": svm_df["Completa"],
        "DynaTex-MoD": [dynatex_scores[d] for d in resmlp_df.index]
    }, index=resmlp_df.index)
    df_fusion.index.name = "Data-set"
    run_java_tests(df_fusion, "dynatex_vs_flat_fusion")

if __name__ == "__main__":
    main()
