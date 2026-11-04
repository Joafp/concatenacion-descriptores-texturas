import importlib.util
from pathlib import Path
import json


def test_loading_info_sets_serialize_without_loss():
    path = Path(__file__).resolve().parents[1] / "scripts/diagnose_deit_cls_local.py"
    spec = importlib.util.spec_from_file_location("deit_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = {"unexpected_keys": {"classifier.weight", "classifier.bias"},
        "missing_keys": set(), "checks": [{"pass": False, "error": .1925}]}
    restored = json.loads(json.dumps(module.json_safe(value), allow_nan=False))
    assert restored["unexpected_keys"] == ["classifier.bias", "classifier.weight"]
    assert restored["missing_keys"] == []
    assert restored["checks"][0]["pass"] is False
