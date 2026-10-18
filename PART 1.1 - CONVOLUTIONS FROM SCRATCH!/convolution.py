"""Part 1.1: handwritten same-size 2D convolution, using only NumPy."""
import numpy as np


def prepare(image, kernel):
    """Float64 avoids unsigned subtraction; padding matches SciPy 'same'."""
    image = np.asarray(image, dtype=np.float64)
    kernel = np.asarray(kernel, dtype=np.float64)
    if image.ndim != 2 or kernel.ndim != 2 or not image.size or not kernel.size:
        raise ValueError('Image and kernel must be nonempty 2D arrays.')
    if not np.isfinite(image).all() or not np.isfinite(kernel).all():
        raise ValueError('Image and kernel must contain finite values.')
    kh, kw = kernel.shape
    # Even kernels need one more zero before than after the image.
    padded = np.pad(image, ((kh // 2, (kh - 1) // 2),
                            (kw // 2, (kw - 1) // 2)), mode='constant')
    flipped = kernel[::-1, ::-1]
    return image, padded, flipped


def convolve_four_loops(image, kernel):
    """Two loops over output pixels and two over kernel coefficients."""
    image, padded, flipped = prepare(image, kernel)
    height, width = image.shape
    kh, kw = flipped.shape
    result = np.zeros((height, width), dtype=np.float64)
    for y in range(height):
        for x in range(width):
            for ky in range(kh):
                for kx in range(kw):
                    result[y, x] += padded[y + ky, x + kx] * flipped[ky, kx]
    return result


def convolve_two_loops(image, kernel):
    """Two loops over output pixels; NumPy multiplies and sums each patch."""
    image, padded, flipped = prepare(image, kernel)
    height, width = image.shape
    kh, kw = flipped.shape
    result = np.zeros((height, width), dtype=np.float64)
    for y in range(height):
        for x in range(width):
            result[y, x] = np.sum(padded[y:y + kh, x:x + kw] * flipped)
    return result
