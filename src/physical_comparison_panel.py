"""Prepare frozen timing recipes, without inference, training or quality selection.

This is a preparation manifest, not a physical benchmark or a repeated audit of
the full embedding corpus. Existing source artifacts are never modified.
"""
import copy
import hashlib
import json
import math
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def checked_recipe(recipe, library):
    """Preserve vote multiplicity, and reject malformed/unknown feature recipes."""
    result = copy.deepcopy(recipe)
    members = result.get("members")
    if not isinstance(members, list):
        raise ValueError("members must be a list")
    allowed = set(library)
    for member in members:
        if not member or len(set(member)) != len(member) or not set(member) <= allowed:
            raise ValueError("empty, repeated or unknown extractor within a member")
    base = result.get("base")
    if base is not None:
        if base not in allowed:
            raise ValueError("unknown base")
        threshold = result.get("threshold")
        if members and (not isinstance(threshold, (int, float)) or not math.isfinite(threshold)):
            raise ValueError("a nonempty conditional rescue requires a finite threshold")
    elif not members:
        raise ValueError("an empty route needs a base")
    return result


def concat_recipe(choice, library):
    if not choice.get("feasible") or not choice.get("selected"):
        raise ValueError("infeasible concatenation cannot be turned into a timing recipe")
    return checked_recipe({"members": [choice["selected"]["blocks"]]}, library)


def locate(root, name):
    root = Path(root).resolve()
    p = Path(name)
    if p.is_absolute():
        # Sources store the Linux repository path; relocate only its repo-relative suffix.
        try:
            p = p.relative_to("/home/joaquin/tesis_claude")
        except ValueError:
            if not p.is_relative_to(root):
                raise ValueError(f"source outside the known repository: {name}")
    result = (root / p).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"source escapes repository: {name}")
    return result


def verify_sources(root, sources, audits):
    """Verify every recipe-bearing source against an existing audit binding."""
    expected = {}
    for audit in audits:
        for name, value in audit["input_sha256"].items():
            if name in expected and expected[name] != value:
                raise ValueError(f"conflicting audit hashes: {name}")
            expected[name] = value
    result = {}
    for path in sources:
        name = path.relative_to(root).as_posix()
        if name not in expected:
            raise ValueError(f"recipe source absent from audit: {name}")
        actual = digest(path)
        if actual != expected[name]:
            raise ValueError(f"recipe source changed after audit: {name}")
        result[name] = actual
    return result


def prepare_condition(root, condition):
    root = Path(root).resolve()
    audit_dir = ("matched_concat_20261026" if condition.startswith("FMD_")
                 else "matched_concat_outex_retry_20261026/audit")
    ca_path = root / "results/analysis" / audit_dir / f"{condition}.json"
    ha_path = root / "results/analysis/mesa_replication_20261026" / f"{condition}.json"
    ca, ha = read(ca_path), read(ha_path)
    joint_path = root / "results/analysis/matched_concat_panel_20261026/summary.json"
    joint = read(joint_path)
    if joint["status"] != "ANALYZED":
        raise ValueError("the existing joint panel is not audited")
    for path in (ca_path, ha_path):
        name = path.relative_to(root).as_posix()
        if digest(path) != joint["input_sha256"].get(name):
            raise ValueError(f"condition audit differs from the joint panel: {name}")
    if ca["status"] != "ANALYZED" or ha["status"] != "ANALYZED":
        raise ValueError("both existing condition audits must be ANALYZED")
    if ca["condition"]["dataset"] != ha["condition"]["dataset"]:
        raise ValueError("different datasets")
    if ca["condition"]["seed"] != ha["condition"]["seed"]:
        raise ValueError("different seeds")
    meta_names = [n for n in ca["input_sha256"] if n.endswith("/controls/metadata.json")]
    if len(meta_names) != 1:
        raise ValueError("ambiguous concatenation source")
    cm_path = root / meta_names[0]
    if digest(cm_path) != ca["input_sha256"][meta_names[0]]:
        raise ValueError("concatenation metadata differs from its audit")
    cm = read(cm_path)
    suite = root / "results/exploratory/integration_v11/replication_20261026" / condition
    hm_path = suite / "hybrid/metadata.json"
    hm = read(hm_path)
    ref = locate(root, hm["reference_run"])
    if locate(root, cm["reference_run"]) != ref:
        raise ValueError("the controls do not share their producer reference")
    if cm.get("external_test_evaluated") or hm.get("external_test_evaluated"):
        raise ValueError("this pilot is restricted to development")
    folds = [read(ref / f"fold{i}.json") for i in range(3)]
    decisions_path = cm_path.parent / "decisions.json"
    decisions = read(decisions_path)
    hybrid_path = suite / "hybrid/selections.json"
    paired_path = ref / "selections.json"
    hybrid, paired = read(hybrid_path), read(paired_path)
    carlos_path = locate(root, hm["carlos_run"]) / "folds.json"
    permanent = read(carlos_path)
    static_dir = suite / ("static_recovery" if (suite / "static_recovery").is_dir() else "static")
    static_path = static_dir / "decisions.json"
    static = read(static_path)
    sources = [ca_path, ha_path, cm_path, hm_path, decisions_path, hybrid_path,
               paired_path, carlos_path, static_path]

    def at(records, fold, policy=None):
        found = [r for r in records if r["producer_fold"] == fold
                 and (policy is None or r.get("policy") == policy)]
        if len(found) != 1:
            raise ValueError(f"ambiguous fold/policy {fold}/{policy}")
        return found[0]

    result = []
    for f, fold in enumerate(folds):
        decision = at(decisions, f)
        per = at(permanent, f)
        for record in (decision, per):
            if record["fit_indices"] != fold["fit_indices"] or record["validation_indices"] != fold["validation_indices"]:
                raise ValueError("unpaired producer folds")
        if set(fold["fit_indices"]) & set(fold["validation_indices"]):
            raise ValueError("fit/validation overlap")
        library = fold["library_order"]
        recipes = {
            "ensemble_permanent": {"members": per["diversity_members"]},
            "ensemble_static": at(static, f)["budget_selections"]["60.0"]["selected"],
            "adaptive_previous_pool": at(paired, f, "relevance_B60")["selected"],
            "adaptive_diversity_pool": at(hybrid, f, "pruned_relevance_B60")["selected"],
            "gfs": concat_recipe(decision["choices"]["gfs"], library),
            "topk": concat_recipe(decision["choices"]["topk_gfs_size"], library),
            "individual": {"members": [[fold["ranked_blocks"][0]]]},
            "complete22": {"members": [library]},
        }
        source = ref / f"fold{f}.json"
        sources.append(source)
        result.append({"producer_fold": f, "fit_indices": fold["fit_indices"],
                       "validation_indices": fold["validation_indices"],
                       "recipes": {k: checked_recipe(v, library) for k, v in recipes.items()},
                       "internal_budget_setting_ms": 60,
                       "timing_status": "NOT_MEASURED",
                       "full_physical_parity": "NOT_VERIFIED"})
    verified = verify_sources(root, sources[2:], (ca, ha))
    sources.append(joint_path)
    return {"condition": condition, "dataset": ca["condition"]["dataset"],
            "seed": ca["condition"]["seed"], "folds": result,
            "source_sha256": {str(p.relative_to(root)): digest(p) for p in sources},
            "verified_recipe_source_sha256": verified,
            "scope": "Frozen recipe preparation only; no re-audit of embeddings or prediction replay"}


def build(root, output, protocol):
    root, output, protocol = Path(root).resolve(), Path(output).resolve(), Path(protocol).resolve()
    if output.exists():
        raise FileExistsError(output)
    panel = [prepare_condition(root, c) for c in ("FMD_s42", "Outex_s123")]
    report = {"schema": "physical-comparison-preparation/1", "status": "PREPARED_NOT_MEASURED",
              "external_test_evaluated": False, "physical_latency_published": False,
              "new_quality_fits": 0, "selection_changed": False,
              "conditions": panel, "protocol_sha256": digest(protocol),
              "preparer_sha256": digest(__file__),
              "reference_methods_status": "RECIPE_AND_IMPLEMENTATION_VERIFICATION_REQUIRED",
              "note": "Recipe count is not evidence of runnable extractors, physical fidelity or speed."}
    output.mkdir(parents=True, exist_ok=False)
    (output / "manifest.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report
