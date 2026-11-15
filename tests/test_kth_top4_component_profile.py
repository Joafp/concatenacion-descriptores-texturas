import pytest
from scripts.benchmark_kth_top4_components import training_sample


def test_sample_uses_actual_class_count_and_only_training_rows():
    rows = [dict(label=str(i // 5)) for i in range(55)]
    train = [i for i in range(55) if i % 5 != 4]
    selected = training_sample(rows, train)
    assert len(selected) == 33
    assert len(set(selected)) == 33
    assert set(selected).issubset(train)
    assert selected == training_sample(rows, train)
    assert all(sum(rows[i]['label'] == str(c) for i in selected) == 3 for c in range(11))


def test_insufficient_class_cannot_be_silently_skipped():
    with pytest.raises(ValueError, match='too few'):
        training_sample([dict(label='a'), dict(label='b'), dict(label='b'), dict(label='b')], [0, 1, 2, 3])
