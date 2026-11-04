"""Check a minimal P0 rebuild in isolation and local Soil v1 identity.

Does not download, redistribute, re-extract, or overwrite scientific artifacts.
Temporary copies are created beneath this repository's tmp directory.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
P0 = Path("results/analysis/integration_v9/p0_gate_ablation_outex22_20261025")
HYBRID = Path("results/exploratory/integration_v8/carlos_hybrid_outex22_20261021")
OUT = ROOT / "results/analysis/mesa_grado_20261025_r2/reproduction"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    paths = [Path("scripts/build_p0_thesis_tables.py")]
    paths += [P0 / name for name in ("results.csv", "fold_results.csv", "prediction_views.csv",
                                    "validation_summary.json", "artifact_manifest.json")]
    paths += [HYBRID / name for name in ("results.csv", "fold0.json", "fold1.json", "fold2.json")]
    temp_root = ROOT / "tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p0_minimal_", dir=temp_root) as name:
        staging = Path(name).resolve()
        assert staging.is_relative_to(temp_root.resolve())
        (staging / "paper").mkdir()
        for relative in paths:
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        result = subprocess.run([sys.executable, str(staging / "scripts/build_p0_thesis_tables.py")],
                                cwd=staging, text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        comparisons = {}
        for file in ("barrido_p0.tex", "descomposicion_b60.tex"):
            expected = ROOT / "paper/generated_p0" / file
            generated = staging / "paper/generated_p0" / file
            assert generated.read_bytes() == expected.read_bytes(), file
            comparisons[file] = digest(generated)
    manifest = ROOT / "results/confirmatory/recovery/soil/Soil_Original_manifest.csv"
    archive = ROOT / "results/confirmatory/recovery/soil/source/comprehensive-soil-classification-datasets-v1.zip"
    with manifest.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1140 and len({r["label"] for r in rows}) == 7
    assert len({r["group"] for r in rows}) == 962
    assert len({r["source_sha256"] for r in rows}) == len(rows)
    assert {r["source_version"] for r in rows} == {"Kaggle ai4a-lab/comprehensive-soil-classification-datasets v1"}
    for row in rows:
        assert digest(ROOT / row["source_path"]) == row["source_sha256"], row["source_path"]
    archive_hash = digest(archive)
    assert archive_hash == "a4ae6ce5f918128104d79ccfbf12ec93e670fa6aa4617eb788df3e4dda08d97e"
    provenance = [manifest, archive, ROOT / "results/confirmatory/recovery/soil/build_soil_original_manifest.py",
                  ROOT / "requirements.txt", Path(__file__)]
    result = {"status": "ANALYZED", "scope": "Isolated cached-table reproduction and local image identity, not RGB model reproduction",
              "minimal_p0_files": len(paths), "tables_byte_identical": comparisons,
              "generator_stdout": result.stdout.strip(), "soil_source_images_checked": len(rows),
              "soil_classes": 7, "soil_groups": 962,
              "soil_archive_version": 1, "soil_archive_sha256": archive_hash,
              "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
                                [ROOT / relative for relative in paths] + provenance},
              "missing_publication_guarantee": "Local files are not presumed published or licensed for redistribution",
              "independent_RGB_extraction_performed": False}
    OUT.mkdir(parents=True)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print({k: v for k, v in result.items() if k not in ("input_sha256", "generator_stdout")})


if __name__ == "__main__":
    main()
