import importlib.util
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[1]
OFFICIAL_SPEC = importlib.util.spec_from_file_location(
    "rgb_ngram_official", REPO / "src/run_rgb_ngram_outex13_official.py"
)
OFFICIAL = importlib.util.module_from_spec(OFFICIAL_SPEC)
assert OFFICIAL_SPEC.loader is not None
OFFICIAL_SPEC.loader.exec_module(OFFICIAL)


def test_impl1_vertical_joint_channel_encoding():
    image = np.zeros((2, 1, 3), dtype=np.uint8)
    image[0, 0] = [12, 24, 36]
    image[1, 0] = [48, 60, 72]
    alphabet = 22
    digits = [1, 4, 2, 5, 3, 6]
    expected = 0
    for digit in digits:
        expected = expected * alphabet + digit
    assert OFFICIAL.encoded_ngrams(image, "rgb_ngram_impl1").tolist() == [expected]


def test_impl2_keeps_channels_separate():
    image = np.zeros((4, 1, 3), dtype=np.uint8)
    image[:, 0, 0] = [11, 22, 33, 44]
    image[:, 0, 1] = [11, 22, 33, 44]
    image[:, 0, 2] = [11, 22, 33, 44]
    codes = OFFICIAL.encoded_ngrams(image, "rgb_ngram_impl2")
    assert len(np.unique(codes)) == 3
    assert codes[1] - codes[0] == 24**4
    assert codes[2] - codes[1] == 24**4


def test_count_image_is_deterministic_and_conserves_windows():
    image = np.arange(5 * 3 * 3, dtype=np.uint8).reshape(5, 3, 3)
    keys_a, counts_a = OFFICIAL.count_image(image, "rgb_ngram_impl1")
    keys_b, counts_b = OFFICIAL.count_image(image, "rgb_ngram_impl1")
    assert np.array_equal(keys_a, keys_b)
    assert np.array_equal(counts_a, counts_b)
    assert counts_a.sum() == (5 - 2 + 1) * 3


def test_vocabulary_uses_training_rows_only():
    cache = {
        "keys": np.asarray([1, 2, 2, 3, 99], dtype=np.uint64),
        "counts": np.asarray([2, 1, 4, 1, 7], dtype=np.uint32),
        "indptr": np.asarray([0, 2, 4, 5], dtype=np.int64),
    }
    vocabulary = OFFICIAL.training_vocabulary(cache, np.asarray([0, 1]))
    assert vocabulary.tolist() == [1, 2, 3]
    matrix = OFFICIAL.matrix_from_vocabulary(cache, vocabulary)
    assert matrix.shape == (3, 3)
    assert matrix[2].nnz == 0


def test_official_raw_matrix_preserves_counts():
    cache = {
        "keys": np.asarray([1, 2, 2, 3, 99], dtype=np.uint64),
        "counts": np.asarray([2, 1, 4, 1, 7], dtype=np.uint32),
        "indptr": np.asarray([0, 2, 4, 5], dtype=np.int64),
    }
    vocabulary = OFFICIAL.training_vocabulary(cache, np.asarray([0, 1]))
    matrix = OFFICIAL.raw_matrix_from_vocabulary(cache, vocabulary)
    assert matrix.toarray().tolist() == [[2.0, 1.0, 0.0], [0.0, 4.0, 1.0], [0.0, 0.0, 0.0]]


def test_official_classifier_matches_base_paper_configuration():
    classifier = OFFICIAL.make_classifier()
    assert classifier.kernel == "linear"
    assert classifier.C == 1.0
