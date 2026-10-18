"""Full-resolution Gaussian/Laplacian stacks and mask-weighted reconstruction."""
import cv2
import numpy as np
from scipy.ndimage import convolve1d

IMAGE_SIGMAS = (0., 2., 4., 8., 16., 32.)
MASK_SIGMAS = (1., 2., 4., 8., 16., 32.)


def gaussian_stack(image, sigmas=IMAGE_SIGMAS):
    """Successively blur without resizing; sigmas are nominal cumulative scales.

    Incremental sigma = sqrt(target**2 - previous**2), following Gaussian
    variance addition. Finite sampled kernels approximate this scale schedule.
    """
    current = np.asarray(image, dtype=np.float64)
    sigmas = np.asarray(sigmas, dtype=np.float64)
    if current.ndim not in (2, 3) or not current.size or not np.isfinite(current).all():
        raise ValueError('Expected a nonempty finite grayscale or RGB image.')
    if current.ndim == 3 and current.shape[2] != 3:
        raise ValueError('Color images require three RGB channels.')
    if sigmas.ndim != 1 or len(sigmas) < 2 or not np.isfinite(sigmas).all() or sigmas[0] < 0 or (np.diff(sigmas) <= 0).any():
        raise ValueError('At least two nonnegative, strictly increasing scales are required.')
    levels = []
    previous = 0.
    for target in sigmas:
        incremental = float(np.sqrt(target ** 2 - previous ** 2))
        if incremental > 0:
            radius = int(np.ceil(4 * incremental))
            weights = cv2.getGaussianKernel(2 * radius + 1, incremental, cv2.CV_64F).ravel()
            current = convolve1d(convolve1d(current, weights, axis=0, mode='reflect'), weights, axis=1, mode='reflect')
        else:
            current = current.copy()
        levels.append(current)
        previous = target
    return np.stack(levels)


def laplacian_stack(gaussian):
    """Adjacent Gaussian differences, with the final coarse residual retained."""
    gaussian = np.asarray(gaussian, dtype=np.float64)
    if gaussian.ndim not in (3, 4) or len(gaussian) < 2 or not np.isfinite(gaussian).all():
        raise ValueError('Expected a finite full-resolution Gaussian stack.')
    return np.concatenate((gaussian[:-1] - gaussian[1:], gaussian[-1:]), axis=0)


def blend_stacks(left_laplacian, right_laplacian, masks):
    left_laplacian = np.asarray(left_laplacian, dtype=np.float64)
    right_laplacian = np.asarray(right_laplacian, dtype=np.float64)
    masks = np.asarray(masks, dtype=np.float64)
    if left_laplacian.ndim not in (3, 4) or left_laplacian.shape != right_laplacian.shape:
        raise ValueError('Both Laplacian stacks must have the same shape.')
    if masks.shape != left_laplacian.shape[:3] or not np.isfinite(masks).all():
        raise ValueError('One finite 2D mask is required per stack level.')
    if not np.isfinite(left_laplacian).all() or not np.isfinite(right_laplacian).all():
        raise ValueError('Image stacks must be finite.')
    if masks.min() < -1e-12 or masks.max() > 1 + 1e-12:
        raise ValueError('Mask weights must lie in [0,1].')
    # Clamp only floating-point roundoff in mask weights, never image bands.
    masks = np.clip(masks, 0., 1.)
    weights = masks[..., None] if left_laplacian.ndim == 4 else masks
    left_bands = weights * left_laplacian
    right_bands = (1 - weights) * right_laplacian
    bands = left_bands + right_bands
    return {'left_bands': left_bands, 'right_bands': right_bands, 'bands': bands,
            'left': left_bands.sum(axis=0), 'right': right_bands.sum(axis=0), 'image': bands.sum(axis=0)}
