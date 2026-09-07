"""
filter_perfold_4clfs.py
========================
Filtra perfold_*.jsonl y baseline_*.csv a 4 classifiers (svm, knn, rf, resmlp).
Excluye 'mlp' (el multilayer perceptron de sklearn).
"""
import json
from pathlib import Path
import pandas as pd

TABLES = Path("results/tables")
KEEP_CLFS = ["svm", "knn", "rf", "resmlp"]
DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]


def filter_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("clf") in KEEP_CLFS:
                rows.append(r)
    if not rows:
        return 0
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return len(rows)


def filter_csv(path: Path) -> int:
    if not path.exists():
        return 0
    df = pd.read_csv(path)
    df = df[df["clf"].isin(KEEP_CLFS)].reset_index(drop=True)
    df.to_csv(path, index=False)
    return len(df)


def main():
    print(f"Filtrando a clfs={KEEP_CLFS} (excluye 'mlp')\n")
    for ds in DATASETS:
        # Per-fold JSONL
        for prefix in ["perfold", "perfold_concat", "perfold_greedy"]:
            p = TABLES / f"{prefix}_{ds}.jsonl"
            if p.exists():
                n = filter_jsonl(p)
                print(f"  {p.name}: {n} filas")
        # Baseline CSV
        b = TABLES / f"baseline_{ds}.csv"
        if b.exists():
            n = filter_csv(b)
            print(f"  {b.name}: {n} filas")
        # Concat CSV
        c = TABLES / f"concat_{ds}.csv"
        if c.exists():
            n = filter_csv(c)
            print(f"  {c.name}: {n} filas")
    # Aggregados
    for f_name in ["perfold_all.jsonl", "concat_summary.csv", "baseline_summary.csv"]:
        p = TABLES / f_name
        if not p.exists():
            continue
        if p.suffix == ".jsonl":
            n = filter_jsonl(p)
        else:
            n = filter_csv(p)
        print(f"  {f_name}: {n} filas")
    print("\n[OK] Filtrado completo")


if __name__ == "__main__":
    main()
