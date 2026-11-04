import pandas as pd
import pytest
from matched_reference_quality import aligned_quality


def test_rows_can_reorder_but_not_change_fold_or_labels():
    a = pd.DataFrame({"row_index": [1, 2], "producer_fold": [0, 1], "label": [0, 1], "prediction": [0, 1]})
    assert aligned_quality(a, a.iloc[::-1])["macro_f1"] == 1.
    with pytest.raises(ValueError):
        aligned_quality(a, a.assign(producer_fold=[1, 0]))
    with pytest.raises(ValueError):
        aligned_quality(a, a.assign(label=[1, 0]))
    with pytest.raises(ValueError):
        aligned_quality(a, a.iloc[:1])
    with pytest.raises(ValueError):
        aligned_quality(a, pd.concat([a, a.iloc[:1]]))
