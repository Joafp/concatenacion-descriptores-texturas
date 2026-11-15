"""Validate ARS transport and frozen manuscript integrity, not scholarly truth."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

import jsonschema

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARS = Path("/mnt/c/Users/Joaquin/.codex/skills/academic-research-suite/ars")
ROLES = ["eic", "methodology", "domain", "perspective", "da"]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks = []


def check(name, args):
    run = subprocess.run(["python3", str(ARS/"scripts"/args[0]), *map(str,args[1:])],
                         cwd=ROOT, capture_output=True, text=True)
    checks.append({"name":name,"exit_code":run.returncode,"stdout":run.stdout,"stderr":run.stderr})
    if run.returncode:
        raise RuntimeError(f"{name} failed: {run.stdout} {run.stderr}")


for role in ROLES:
    common = ["check_phase_conformance.py", "--contract", HERE/"inputs/contract.json", "--role",role,
              "--phase1", HERE/f"reports/{role}_phase1.md", "--manuscript", HERE/"inputs/paper_content.txt",
              "--metadata",HERE/"inputs/metadata.json"]
    check(f"{role}_phase1", [*common,"--phase1-only"])
    check(f"{role}_phase2", [*common,"--phase2", HERE/f"reports/{role}_phase2.md"])
panel = ["check_panel_synthesis.py","--contract",HERE/"inputs/contract.json"]
for role in ROLES:
    panel += ["--report", HERE/f"reports/{role}_phase2.md"]
panel += ["--roles", ",".join(ROLES)]
check("panel_layer1", [*panel,"--layer1-only"])
check("panel_synthesis", [*panel,"--synthesis",HERE/"reports/editorial_synthesis.md"])
check("panel_provenance", ["review_panel_provenance.py","validate",HERE/"panel_provenance.json"])
roadmap = json.loads((HERE/"revision_roadmap.json").read_text())
schema = json.loads((ARS/"shared/contracts/revision/revision_roadmap.schema.json").read_text())
jsonschema.Draft202012Validator(schema).validate(roadmap)
assert roadmap["base_draft_sha256"] == sha(HERE/"inputs/review_working_draft.md")
assert roadmap["block_manifest_sha256"] == sha(HERE/"inputs/block_manifest.json")
blocks = {b["block_id"] for b in json.loads((HERE/"inputs/block_manifest.json").read_text())["blocks"]}
assert roadmap["total_items"] == len(roadmap["items"]) == 15
assert all(t["block_id"] in blocks for item in roadmap["items"] for t in item["proposed_targets"])
assert all(item["severity"] == "minor" for item in roadmap["items"])
assert {k:sum(i["obligation_class"]==k for i in roadmap["items"]) for k in roadmap["obligation_counts"]} == roadmap["obligation_counts"]
manifest = json.loads((HERE/"inputs/input_manifest.json").read_text())
unchanged = {name:sha(ROOT/name)==expected for name,expected in manifest["source_sha256"].items()}
assert all(unchanged.values())
assert sha(ROOT/manifest["pdf_path"]) == manifest["pdf_sha256"]
preflight = json.loads((HERE/"inputs/pdf_read_preflight_posix_bundled.json").read_text())
assert preflight["verdict"] == "PASS" and preflight["sha256"] == manifest["pdf_sha256"]
assert preflight["declared_page_count"] == preflight["enumerated_page_count"] == preflight["reader_page_count"] == 90
receipt = {"status":"passed", "recorded_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "scope":"ARS conformance, schema, provenance replay and artifact integrity; not calibrated correctness or academic approval",
           "checks":checks,"roadmap_schema":"PASS","roadmap_targets":"review-copy blocks only, no original LaTeX write authority",
           "manuscript_sources_unchanged":unchanged,"pdf_unchanged_sha256":manifest["pdf_sha256"],
           "pdf_structural_preflight":"PASS","new_fits":0,"new_neural_calls":0,"new_timing_benchmarks":0,
           "author_adjudication_inferred":False,
           "review_output_sha256":{str(p.relative_to(HERE)):sha(p) for p in HERE.rglob("*")
                                  if p.is_file() and p.name!="validation_receipt.json"},
           "skill_tool_sha256":{name:sha(ARS/"scripts"/name) for name in [
               "check_phase_conformance.py","check_panel_synthesis.py","review_panel_provenance.py","pdf_read_preflight.py"]}}
(HERE/"validation_receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
print(f"PASS: {len(checks)} ARS checks; roadmap schema/targets; manuscript and PDF unchanged")
