"""Finite differences and thresholding for Part 1.2; no smoothing."""
import numpy as np
from scipy.signal import convolve2d

DX = np.array([[1., -1.]])
DY = DX.T


def gradients(image):
    """Return signed x/y backward differences and Euclidean magnitude.

    Symmetric boundary extension avoids a spurious edge against zero.
    Convolution flips the kernel: interior dx[y,x] = I[y,x] - I[y,x-1].
    """
    image = np.asarray(image, dtype=np.float64)
    if image.ndim != 2 or not image.size or not np.isfinite(image).all():
        raise ValueError('Expected a nonempty, finite 2D grayscale array.')
    dx = convolve2d(image, DX, mode='same', boundary='symm')
    dy = convolve2d(image, DY, mode='same', boundary='symm')
    magnitude = np.sqrt(dx ** 2 + dy ** 2)
    return dx, dy, magnitude


def threshold_edges(magnitude, threshold):
    """An edge is a raw gradient magnitude strictly greater than threshold."""
    magnitude = np.asarray(magnitude, dtype=np.float64)
    if magnitude.ndim != 2 or not magnitude.size or not np.isfinite(magnitude).all() or (magnitude < 0).any():
        raise ValueError('Expected a nonempty, finite, nonnegative magnitude array.')
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError('Threshold must be finite and nonnegative.')
    return magnitude > threshold
