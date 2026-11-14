"""Verify the saved cascade cases whose rescue is exactly the fixed Top-4."""
from pathlib import Path
import hashlib
import json
import pandas as pd
from build_topk_margin_thesis_20261113 import table, number

ROOT = Path(__file__).resolve().parents[1]


def run():
    audit = ROOT / "results/analysis/topk_margin_rewrite_20261113_v1"
    folder = ROOT / "results/exploratory/topk_cascade/cheap_stage_selected_primary22"
    paths = sorted((ROOT / "results/exploratory/k_sweep").glob("*/k_sweep.csv"))
    sweep = pd.concat([pd.read_csv(p) for p in paths])
    paired = audit / "paired_cascade_audit.csv"
    rows = pd.read_csv(paired)
    records, sources, rendered = [], paths + [paired], []
    names = {"official10": "DTD / split 10", "official8": "DTD / split 8",
             "stratified_group_kfold5_fold2": "FMD / fold 2",
             "stratified_group_kfold5_fold3": "FMD / fold 3",
             "curet_half_indices:a_to_b": "CUReT / A a B"}
    for _, row in rows[rows.k.eq(4)].iterrows():
        stem = f"{row.dataset}_{row.protocol}".replace(":", "__")
        path = folder / f"{stem}_result.json"
        result = json.loads(path.read_text())
        archive_path = Path(result["source_archive"]["path"])
        archive = json.loads(archive_path.read_text())
        sources.extend([path, archive_path])
        match = sweep[sweep.dataset.eq(row.dataset) & sweep.outer_fold.eq(archive["outer_fold"])
                      & sweep.seed.eq(archive.get("seed", 42)) & sweep.k.eq(4) & sweep.classifier.eq("svm")]
        same = len(match) == 1 and set(match.iloc[0].selected.split("+")) == set(result["topk_blocks"])
        if not same:
            raise ValueError(f"Top-4 identity requires review: {stem}")
        records.append({"dataset": row.dataset, "protocol": row.protocol,
            "same_selected_blocks_as_fixed4_sweep": bool(same),
            "direct_f1": row.direct_f1, "margin_f1": row.conditional_f1,
            "requested_fraction": row.request_fraction, "source": str(archive_path)})
        rendered.append([names.get(row.protocol, row.dataset), number(row.direct_f1, 6),
                         number(row.conditional_f1, 6), number(row.conditional_f1-row.direct_f1, 6),
                         number(100*row.request_fraction, 2)])
    assert len(records) == 5
    output = audit / "top4_margin_subset.json"
    if output.exists():
        assert json.loads(output.read_text()) == records
    else:
        output.write_text(json.dumps(records, indent=2) + "\n")
    dest = ROOT / "paper/generated_topk_margin/top4_margin_subset.tex"
    contents = table("Condiciones donde el rescate coincide con el Top-4 del barrido, SVM.",
        "tab:tm-fixed4-margin", ["Condición", "Directo F1", "Margen F1", r"$\Delta$ F1", r"Rescate \%"],
        rendered, "Subconjunto definido por k=4 y coincidencia de bloques, no por signo del resultado. Son cinco condiciones de tres datasets; no una evaluación Top-4 por margen completa en seis datasets.")
    if dest.exists():
        assert dest.read_text() == contents
    else:
        dest.write_text(contents)
    provenance = {"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "output_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (output, dest)},
        "new_fits": 0, "new_predictions": 0}
    p = audit / "top4_margin_subset_provenance.json"
    if p.exists():
        assert json.loads(p.read_text()) == provenance
    else:
        p.write_text(json.dumps(provenance, indent=2) + "\n")
    print("Verified five matching Top-4 rescues, with gains, losses and ties retained.")


if __name__ == "__main__":
    run()
