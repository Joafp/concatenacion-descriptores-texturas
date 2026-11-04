"""Source-described formula components, NOT a complete AsTexNet implementation.

Local PDF DOI 10.3390/app16125743, equations 8-12 and 16-18.
Undefined zero divisors fail closed rather than adding undocumented smoothing.
These functions neither choose scale descriptors nor train a classifier.
"""
import numpy as np


def finite_array(values):
    values = np.asarray(values, dtype=np.float64)
    if not values.size or not np.isfinite(values).all():
        raise ValueError('nonempty finite values required')
    return values


def hellinger_l2(histogram):
    histogram = finite_array(histogram)
    if histogram.ndim != 1 or (histogram < 0).any() or histogram.sum() <= 0:
        raise ValueError('nonnegative nonzero histogram required')
    root = np.sqrt(histogram / histogram.sum())
    return root / np.linalg.norm(root)


def magnitude_histogram(magnitude):
    """Equation 8: floor(min(M,t99)/t99 * 7), not ordinary 8 equal-width bins.

    Input is the magnitude AFTER the separately specified Gaussian/Sobel stages.
    Quantile convention is NumPy linear; a declared implementation choice.
    """
    magnitude = finite_array(magnitude)
    if (magnitude < 0).any():
        raise ValueError('nonnegative magnitudes required')
    threshold = np.percentile(magnitude, 99, method='linear')
    if threshold <= 0:
        raise ValueError('undefined t99 divisor; no implicit epsilon')
    codes = np.floor(np.minimum(magnitude, threshold) / threshold * 7).astype(np.int64)
    return np.bincount(codes.ravel(), minlength=8) / magnitude.size


def center_histogram(gray):
    """Equation 10 uses strictly greater-than the 75th percentile."""
    gray = finite_array(gray)
    threshold = np.percentile(gray, 75, method='linear')
    codes = (gray > threshold).astype(np.int64)
    return np.bincount(codes.ravel(), minlength=2) / gray.size


def scale_weights(coefficient_matrices):
    """Equations 16-17 use Frobenius norms from independently trained models.

    Fitting those logistic models and their regularization are NOT defined here.
    """
    matrices = [finite_array(w) for w in coefficient_matrices]
    if not matrices or any(w.ndim != 2 for w in matrices):
        raise ValueError('one coefficient matrix per scale required')
    norms = np.asarray([np.linalg.norm(w, ord='fro') for w in matrices])
    if norms.sum() <= 0:
        raise ValueError('undefined all-zero scale weights')
    return norms / norms.sum()


def weighted_concatenation(blocks, weights):
    weights = finite_array(weights)
    blocks = [finite_array(block) for block in blocks]
    if (weights.ndim != 1 or len(blocks) != len(weights)
            or any(b.ndim != 1 for b in blocks) or (weights < 0).any()
            or not np.isclose(weights.sum(), 1., rtol=0., atol=1e-12)):
        raise ValueError('aligned blocks and normalized scale weights required')
    return np.concatenate([w * block for w, block in zip(weights, blocks)])
