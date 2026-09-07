#!/usr/bin/env python3
"""Export all SCI2S CONTROLTEST/MULTIPLETEST results to one tidy CSV."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/confirmatory/nonparametric"
OUTPUT = BASE / "all_sci2s_tests.csv"

ANALYSES = {
    "primary_by_dataset": {
        "metric": "macro_f1",
        "unit": "dataset",
        "n": 4,
        "authority": "primary",
        "control": BASE / "primary_controltest.tex",
        "multiple": BASE / "primary_multipletest.tex",
    },
    "sensitivity_dataset_classifier": {
        "metric": "macro_f1",
        "unit": "dataset_classifier",
        "n": 8,
        "authority": "descriptive_sensitivity",
        "control": BASE / "sensitivity_controltest.tex",
        "multiple": BASE / "sensitivity_multipletest.tex",
    },
    "accuracy_primary_by_dataset": {
        "metric": "accuracy",
        "unit": "dataset",
        "n": 4,
        "authority": "secondary_primary",
        "control": BASE / "accuracy/primary_controltest.tex",
        "multiple": BASE / "accuracy/primary_multipletest.tex",
    },
    "accuracy_sensitivity_dataset_classifier": {
        "metric": "accuracy",
        "unit": "dataset_classifier",
        "n": 8,
        "authority": "descriptive_sensitivity",
        "control": BASE / "accuracy/sensitivity_controltest.tex",
        "multiple": BASE / "accuracy/sensitivity_multipletest.tex",
    },
}

FIELDS = [
    "analysis",
    "metric",
    "block_unit",
    "n_blocks",
    "k_strategies",
    "inferential_authority",
    "source_program",
    "scope",
    "test",
    "control",
    "comparison",
    "statistic_name",
    "statistic",
    "df1",
    "df2",
    "p_raw",
    "p_bonferroni_output",
    "p_holm_output",
    "p_hochberg_output",
    "p_hommel_output",
    "p_holland_output",
    "p_rom_output",
    "p_finner_output",
    "p_li_output",
    "p_nemenyi_output",
    "p_shaffer_output",
    "p_bergmann_hommel_output",
    "significant_0_05",
]


def base_row(name: str, meta: dict, program: str, scope: str, test: str) -> dict:
    row = {field: "" for field in FIELDS}
    row.update(
        {
            "analysis": name,
            "metric": meta["metric"],
            "block_unit": meta["unit"],
            "n_blocks": meta["n"],
            "k_strategies": 5,
            "inferential_authority": meta["authority"],
            "source_program": program,
            "scope": scope,
            "test": test,
        }
    )
    return row


def clean_number(value: str) -> str:
    """Remove sentence punctuation emitted immediately after SCI2S numbers."""
    return value.strip().rstrip(".")


def parse_omnibus(name: str, meta: dict, text: str) -> list[dict]:
    specs = [
        (
            "Friedman",
            "chi_square",
            r"Friedman statistic \(distributed according to chi-square with (\d+) degrees of freedom: ([0-9.Ee+-]+)\.\s*\nP-value computed by Friedman Test: ([0-9.Ee+-]+)",
        ),
        (
            "Iman-Davenport",
            "F",
            r"Iman and Davenport statistic \(distributed according to F-distribution with (\d+) and (\d+) degrees of freedom: ([0-9.Ee+-]+)\.\s*\nP-value computed by Iman and Daveport Test: ([0-9.Ee+-]+)",
        ),
        (
            "Friedman Aligned Ranks",
            "chi_square",
            r"Aligned Friedman statistic \(distributed according to chi-square with (\d+) degrees of freedom: ([0-9.Ee+-]+)\.\s*\nP-value computed by Aligned Friedman Test: ([0-9.Ee+-]+)",
        ),
        (
            "Quade",
            "F",
            r"Quade statistic \(distributed according to F-distribution with (\d+) and (\d+) degrees of freedom: ([0-9.Ee+-]+)\.\s*\nP-value computed by Quade Test: ([0-9.Ee+-]+)",
        ),
    ]
    rows = []
    for test, statistic_name, pattern in specs:
        match = re.search(pattern, text)
        if not match:
            raise RuntimeError(f"Could not parse omnibus {test} for {name}")
        row = base_row(name, meta, "CONTROLTEST", "omnibus", test)
        groups = match.groups()
        if statistic_name == "F":
            df1, df2, statistic, p_value = groups
        else:
            df1, statistic, p_value = groups
            df2 = ""
        statistic = clean_number(statistic)
        p_value = clean_number(p_value)
        row.update(
            {
                "statistic_name": statistic_name,
                "statistic": statistic,
                "df1": df1,
                "df2": df2,
                "p_raw": p_value,
                "significant_0_05": str(float(p_value) < 0.05).lower(),
            }
        )
        rows.append(row)
    return rows


def parse_control_posthoc(name: str, meta: dict, text: str) -> list[dict]:
    rows_by_key: dict[tuple[str, str], dict] = {}
    current_test = ""
    current_header: list[str] = []
    for line in text.splitlines():
        caption = re.search(r"Adjusted \$p\$-values \(([^)]+)\)", line)
        if caption:
            current_test = caption.group(1).replace("ALIGNED FRIEDMAN", "Friedman Aligned Ranks").title()
            if "Aligned" in current_test:
                current_test = "Friedman Aligned Ranks"
            elif current_test == "Friedman":
                current_test = "Friedman"
            elif current_test == "Quade":
                current_test = "Quade"
            current_header = []
            continue
        if line.startswith("i&algorithm&"):
            current_header = [part.replace("$", "").replace("p_{", "").replace("}", "") for part in line.rstrip("\\").split("&")]
            continue
        if not current_test or not current_header or not re.match(r"^\d+&", line):
            continue
        parts = line.rstrip("\\").split("&")
        if len(parts) != len(current_header):
            continue
        values = dict(zip(current_header, parts))
        algorithm = values["algorithm"]
        key = (current_test, algorithm)
        row = rows_by_key.setdefault(
            key,
            base_row(name, meta, "CONTROLTEST", "one_vs_control", current_test),
        )
        row["control"] = "best_mean_rank"
        row["comparison"] = f"best_mean_rank vs {algorithm}"
        mapping = {
            "unadjusted p": "p_raw",
            "Bonf": "p_bonferroni_output",
            "Holm": "p_holm_output",
            "Hoch": "p_hochberg_output",
            "Homm": "p_hommel_output",
            "Holl": "p_holland_output",
            "Rom": "p_rom_output",
            "Finn": "p_finner_output",
            "Li": "p_li_output",
        }
        for source, target in mapping.items():
            if source in values:
                row[target] = values[source]
    rows = list(rows_by_key.values())
    for row in rows:
        value = row["p_holm_output"] or row["p_raw"]
        row["significant_0_05"] = str(min(1.0, float(value)) < 0.05).lower()
    return rows


def parse_multiple_posthoc(name: str, meta: dict, text: str) -> list[dict]:
    marker = "i&hypothesis&unadjusted $p$&$p_{Neme}$&$p_{Holm}$&$p_{Shaf}$&$p_{Berg}$"
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"Could not find MULTIPLETEST adjusted table for {name}")
    rows = []
    for line in text[start:].splitlines()[1:]:
        if not re.match(r"^\d+&", line):
            if rows:
                break
            continue
        parts = line.rstrip("\\").split("&")
        if len(parts) != 7:
            continue
        _, comparison, raw, nemenyi, holm, shaffer, bergmann = parts
        comparison = comparison.replace(" vs .", " vs ")
        row = base_row(name, meta, "MULTIPLETEST", "all_pairs", "Friedman post-hoc")
        row.update(
            {
                "comparison": comparison,
                "p_raw": raw,
                "p_nemenyi_output": nemenyi,
                "p_holm_output": holm,
                "p_shaffer_output": shaffer,
                "p_bergmann_hommel_output": bergmann,
                "significant_0_05": str(min(1.0, float(holm)) < 0.05).lower(),
            }
        )
        rows.append(row)
    if len(rows) != 10:
        raise RuntimeError(f"Expected 10 all-pairs rows for {name}, got {len(rows)}")
    return rows


def main() -> None:
    rows = []
    for name, meta in ANALYSES.items():
        control_text = meta["control"].read_text(encoding="utf-8")
        multiple_text = meta["multiple"].read_text(encoding="utf-8")
        rows.extend(parse_omnibus(name, meta, control_text))
        rows.extend(parse_control_posthoc(name, meta, control_text))
        rows.extend(parse_multiple_posthoc(name, meta, multiple_text))
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
