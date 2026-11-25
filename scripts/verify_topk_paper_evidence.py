"""Rebuild manuscript aggregates from versioned E1 and online predictions."""
from collections import Counter, defaultdict
from csv import DictReader
from hashlib import sha256
from json import dumps, loads
from math import floor, isclose, isfinite
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "carlos/analisis_paper"
ANALYSIS = ROOT / "results/analysis"
E1 = ANALYSIS / "top4_fixed_kth_completion_audit_20261115_v1"
PANEL = ANALYSIS / "thesis_accuracy_primary_20261115_v3"
INDEX = ANALYSIS / "consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv"
COVERAGE = ANALYSIS / "blocker_resolution_20261101/full_panel_online_v1/coverage.json"
DATASETS = {"DTD", "FMD", "CUReT", "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"}
POLICIES = {"Top-4", "Completa-22", "Ens-tombola", "Ens-diversidad", "Adaptive-selection-margin"}


def require(condition, context):
    if not condition:
        raise ValueError(context)


def read(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(DictReader(stream))


def index(rows, *fields):
    result = {tuple(row[field] for field in fields): row for row in rows}
    require(len(result) == len(rows), f"Duplicate keys in {fields}")
    return result


def check(actual, expected, label, tolerance=1e-9):
    require(isclose(actual, float(expected), rel_tol=0, abs_tol=tolerance),
            f"{label}: calculated {actual}, expected {expected}")


def metrics(truth, predicted):
    support = Counter(truth)
    outputs = Counter(predicted)
    hits = Counter(y for y, fitted in zip(truth, predicted, strict=True) if y == fitted)
    classes = support.keys()
    return {
        "accuracy": sum(hits.values()) / len(truth),
        "precision_macro": mean(hits[y] / outputs[y] if outputs[y] else 0 for y in classes),
        "recall_macro": mean(hits[y] / support[y] for y in classes),
        "macro_f1": mean(2 * hits[y] / (support[y] + outputs[y]) for y in classes),
    }


def verify_e1():
    per_condition = defaultdict(list)
    for row in read(PAPER / "e1_por_imagen.csv"):
        per_condition[(row["id"],)].append(row)
    published = index(read(E1 / "e1_conditions.csv"), "id")
    require(per_condition.keys() == published.keys() and len(published) == 27, "E1 coverage")
    protocol_paths = {ROOT / Path(row["source_folder"]).parents[1] / "protocol_frozen.json"
                      for row in published.values()}
    protocols = {path: index(loads(path.read_text(encoding="utf-8"))["conditions"], "id")
                 for path in protocol_paths}
    by_dataset = defaultdict(list)
    pooled = Counter()
    for key, rows in per_condition.items():
        expected = published[key]
        require(all(row["dataset"] == expected["dataset"] for row in rows), f"{key}: dataset")
        protocol_path = ROOT / Path(expected["source_folder"]).parents[1] / "protocol_frozen.json"
        condition = protocols[protocol_path][key]
        require([int(row["test_index"]) for row in rows] == condition["test_indices"],
                f"{key}: frozen test indices")
        require(condition["dataset"] == expected["dataset"], f"{key}: frozen dataset")
        truth = [row["y"] for row in rows]
        computed = {}
        for route, col in (("direct", "top4"), ("cascade", "cascade")):
            predicted = [row[col] for row in rows]
            for name, value in metrics(truth, predicted).items():
                field = f"{route}_{name}"
                check(value, expected[field], f"{key} {field}")
                computed[field] = value
        escalated = 0
        for row in rows:
            require(row["escalated"] in {"0", "1"}, f"{key}: invalid escalation flag")
            escalates = row["escalated"] == "1"
            require(row["cascade"] == row["top4" if escalates else "cheap"], f"{key}: wrong route")
            top4_ok = row["y"] == row["top4"]
            first_ok = row["y"] == row["cheap"]
            pooled.update({"calls": 1, "escalated": escalates,
                           "correctable": top4_ok and not first_ok,
                           "corrected": escalates and top4_ok and not first_ok,
                           "lost": escalates and first_ok and not top4_ok,
                           "retained": not escalates and first_ok and not top4_ok})
            escalated += escalates
        computed["request_fraction"] = escalated / len(rows)
        costs = condition["component_costs_ms"]
        blocks = condition["top4_blocks"]
        base = expected["cheap"]
        computed["direct_projected_ms"] = sum(costs[block] for block in blocks)
        computed["cascade_projected_ms"] = (
            costs[base] + computed["request_fraction"] * sum(costs[block] for block in blocks if block != base)
        )
        for field in ("request_fraction", "direct_projected_ms", "cascade_projected_ms"):
            check(computed[field], expected[field], f"{key} {field}")
        by_dataset[(expected["dataset"],)].append(computed)
    dataset_means = index(read(E1 / "e1_complete_dataset_means.csv"), "dataset")
    require(by_dataset.keys() == dataset_means.keys() and {k[0] for k in by_dataset} == DATASETS,
            "E1 dataset coverage")
    for key, group in by_dataset.items():
        for field in group[0]:
            check(mean(row[field] for row in group), dataset_means[key][field], f"{key} {field}")
    require(dict(pooled) == {"calls": 31984, "escalated": 6963, "correctable": 1327,
                            "corrected": 1176, "lost": 472, "retained": 168},
            f"E1 counts differ from the manuscript: {dict(pooled)}")
    report = dict(pooled)
    for field in ("direct_accuracy", "cascade_accuracy", "request_fraction",
                  "direct_projected_ms", "cascade_projected_ms"):
        report[field] = mean(mean(row[field] for row in group) for group in by_dataset.values())
    report["projected_cost_reduction"] = 1 - report["cascade_projected_ms"] / report["direct_projected_ms"]
    return report


def quantile_95(values):
    ordered = sorted(values)
    pos = .95 * (len(ordered) - 1)
    lo = floor(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def verify_online():
    manifest = index(read(INDEX), "id")
    published = index(read(PANEL / "online_condition_metrics.csv"), "id", "policy")
    means = index(read(PANEL / "online_means.csv"), "dataset", "classifier", "policy")
    tail = index(read(PAPER / "latencia_p95_reunida.csv"), "dataset", "classifier", "policy")
    coverage = loads(COVERAGE.read_text(encoding="utf-8"))
    require(len(manifest) == coverage["unique_conditions"] == 94, "Online condition coverage")
    require(set(published) == {(ident, policy) for (ident,) in manifest for policy in POLICIES},
            "Online condition-policy coverage")
    aggregate = defaultdict(list)
    pooled_times = defaultdict(list)
    calls = 0
    for (ident,), record in manifest.items():
        path = ROOT / record["calls_csv"]
        require(sha256(path.read_bytes()).hexdigest() == record["sha256"], f"{ident}: trace hash mismatch")
        rows = read(path)
        require(len(rows) == int(record["calls"]), f"{ident}: trace size mismatch")
        calls += len(rows)
        groups = defaultdict(list)
        for row in rows:
            groups[row["policy"]].append(row)
        require(groups.keys() == POLICIES, f"{ident}: incomplete policy set")
        reference = None
        for policy, group in groups.items():
            sample = index(group, "row_index")
            labels = {key: value["label"] for key, value in sample.items()}
            if reference is None:
                reference = labels
            require(labels == reference and all(row["repeat"] == "0" for row in group), f"{ident}: pairing")
            times = [float(row["ms"]) for row in group]
            require(all(value >= 0 and isfinite(value) for value in times), f"{ident}: invalid times")
            result = metrics([row["label"] for row in group], [row["prediction"] for row in group])
            result["mean_ms"] = mean(times)
            expected = published[ident, policy]
            key = (record["dataset"], record["classifier"], policy)
            require(key[:2] == (expected["dataset"], expected["classifier"]), f"{ident}: split identity")
            for field, value in result.items():
                check(value, expected[field], f"{ident} {policy} {field}")
            aggregate[key].append(result)
            pooled_times[key].extend(times)
    require(calls == coverage["primary_calls"] == 362640, "Primary call coverage")
    require(aggregate.keys() == means.keys() and len(means) == 60, "Online mean coverage")
    for key, group in aggregate.items():
        for field in group[0]:
            check(mean(row[field] for row in group), means[key][field], f"{key} {field}")
    require(set(tail) == {key for key in aggregate
                          if key[-1] in {"Top-4", "Completa-22", "Adaptive-selection-margin"}},
            "Published latency percentile coverage")
    for key, published_tail in tail.items():
        times = pooled_times[key]
        require(len(times) == int(published_tail["calls"]), f"{key}: pooled count")
        check(median(times), published_tail["median_ms"], f"{key} median", tolerance=.00500001)
        check(quantile_95(times), published_tail["p95_ms"], f"{key} p95", tolerance=.00500001)
    return {"conditions": len(manifest), "hashed_traces": len(manifest), "calls": calls,
            "policy_condition_rows": len(published), "dataset_policy_rows": len(means),
            "pooled_latency_rows": len(tail)}


if __name__ == "__main__":
    print(dumps({"E1": verify_e1(), "online": verify_online()}, indent=2))
