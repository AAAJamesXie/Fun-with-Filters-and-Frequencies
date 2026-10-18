"""Unsharp masking with independent RGB channels and unclipped float results."""
import cv2
import numpy as np
from scipy.signal import convolve2d


def gaussian_kernel(sigma):
    """Reuse the Part 1.3 Gaussian construction: finite radius ceil(3 sigma)."""
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError('Sigma must be finite and positive.')
    radius = int(np.ceil(3 * sigma))
    column = cv2.getGaussianKernel(2 * radius + 1, sigma, cv2.CV_64F)
    return column @ column.T


def filter_image(image, kernel):
    """One spatial convolution per channel; symmetric extension, same size."""
    image = np.asarray(image, dtype=np.float64)
    if image.ndim not in (2, 3) or not image.size or not np.isfinite(image).all():
        raise ValueError('Expected a nonempty finite grayscale or RGB array.')
    if image.ndim == 3 and image.shape[2] != 3:
        raise ValueError('Color images must have three RGB channels.')
    if image.ndim == 2:
        return convolve2d(image, kernel, mode='same', boundary='symm')
    return np.stack([convolve2d(image[:, :, c], kernel, mode='same', boundary='symm')
                     for c in range(3)], axis=-1)


def unsharp_mask(image, sigma, alpha):
    if not np.isfinite(alpha) or alpha < 0:
        raise ValueError('Sharpening amount must be finite and nonnegative.')
    image = np.asarray(image, dtype=np.float64)
    gaussian = gaussian_kernel(sigma)
    blurred = filter_image(image, gaussian)
    high = image - blurred
    sharpened = image + alpha * high
    impulse = np.zeros_like(gaussian)
    impulse[gaussian.shape[0] // 2, gaussian.shape[1] // 2] = 1.
    kernel = (1 + alpha) * impulse - alpha * gaussian
    single = filter_image(image, kernel)
    return {'gaussian': gaussian, 'blurred': blurred, 'high': high,
            'sharpened': sharpened, 'kernel': kernel, 'single': single}
