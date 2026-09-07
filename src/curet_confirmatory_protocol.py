"""Validated train/test index construction for the confirmatory CUReT manifest."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence

import numpy as np


ROLES = {"alternating_a", "alternating_b"}
DIRECTIONS = {
    "a_to_b": ("alternating_a", "alternating_b"),
    "b_to_a": ("alternating_b", "alternating_a"),
}


def curet_half_indices(
    rows: Sequence[Mapping[str, object]], direction: str
) -> tuple[np.ndarray, np.ndarray]:
    """Return validated CUReT train/test row indices for one direction.

    The manifest halves are a deterministic alternating reproduction, not a
    claim that the exact historical assignment has been recovered.
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {sorted(DIRECTIONS)}, got {direction!r}")
    if not rows:
        raise ValueError("CUReT manifest must not be empty")

    required = {"benchmark_half", "group", "label"}
    for index, row in enumerate(rows):
        missing = required - set(row)
        if missing:
            raise ValueError(f"CUReT manifest row {index} is missing columns {sorted(missing)}")

    observed_roles = {str(row["benchmark_half"]) for row in rows}
    if observed_roles != ROLES:
        raise ValueError(f"benchmark_half roles must be exactly {sorted(ROLES)}")

    by_group: dict[str, list[int]] = defaultdict(list)
    group_role: dict[str, str] = {}
    for index, row in enumerate(rows):
        group = str(row["group"])
        label = str(row["label"])
        role = str(row["benchmark_half"])
        if not group or not label:
            raise ValueError(f"empty group or label in CUReT manifest row {index}")
        if role not in ROLES:
            raise ValueError(f"unexpected benchmark_half {role!r} in row {index}")
        by_group[group].append(index)
        previous = group_role.setdefault(group, role)
        if previous != role:
            raise ValueError(f"CUReT group {group!r} spans multiple benchmark halves")

    if len(by_group) != 92:
        raise ValueError(f"expected exactly 92 CUReT groups, found {len(by_group)}")
    all_labels = {str(row["label"]) for row in rows}
    if len(all_labels) != 61:
        raise ValueError(f"expected exactly 61 CUReT labels, found {len(all_labels)}")
    for group, indices in by_group.items():
        labels = {str(rows[index]["label"]) for index in indices}
        if len(indices) != 61 or labels != all_labels:
            raise ValueError(f"CUReT group {group!r} must contain one row for each of 61 labels")

    role_groups = Counter(group_role.values())
    if role_groups != Counter({"alternating_a": 46, "alternating_b": 46}):
        raise ValueError(f"expected 46 groups per benchmark half, found {dict(role_groups)}")

    train_role, test_role = DIRECTIONS[direction]
    train = [index for index, row in enumerate(rows) if row["benchmark_half"] == train_role]
    test = [index for index, row in enumerate(rows) if row["benchmark_half"] == test_role]
    if len(train) != 2806 or len(test) != 2806:
        raise ValueError(f"expected 2806 train/test rows, found {len(train)}/{len(test)}")

    for role, indices in ((train_role, train), (test_role, test)):
        per_class = Counter(str(rows[index]["label"]) for index in indices)
        if set(per_class) != all_labels or set(per_class.values()) != {46}:
            raise ValueError(f"benchmark half {role!r} must contain 46 rows per class")

    if set(train).intersection(test):
        raise AssertionError("CUReT train/test row overlap")
    train_groups = {str(rows[index]["group"]) for index in train}
    test_groups = {str(rows[index]["group"]) for index in test}
    if len(train_groups) != 46 or len(test_groups) != 46:
        raise ValueError("CUReT train/test must each contain exactly 46 groups")
    if train_groups.intersection(test_groups):
        raise AssertionError("CUReT train/test condition-group overlap")
    return np.asarray(train, dtype=np.int64), np.asarray(test, dtype=np.int64)
