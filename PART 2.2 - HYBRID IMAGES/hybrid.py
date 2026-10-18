"""Two-point alignment, Gaussian hybrid images, color variants and spectra."""
import cv2
import numpy as np
from scipy.ndimage import convolve1d

MODES = ('gray', 'low_color', 'high_color', 'both_color')


def similarity_matrix(source, target):
    source, target = np.asarray(source, dtype=float), np.asarray(target, dtype=float)
    if source.shape != (2, 2) or target.shape != (2, 2) or not np.isfinite([source, target]).all():
        raise ValueError('Two finite (x,y) landmarks are required per image.')
    s, t = source[1] - source[0], target[1] - target[0]
    denominator = float(s @ s)
    if denominator <= 1e-12 or float(t @ t) <= 1e-12:
        raise ValueError('Landmarks must be distinct.')
    a = float(s @ t) / denominator
    b = float(s[0] * t[1] - s[1] * t[0]) / denominator
    rotation_scale = np.array([[a, -b], [b, a]])
    return np.c_[rotation_scale, target[0] - rotation_scale @ source[0]]


def warp_image(image, matrix, size_wh):
    image = np.asarray(image, dtype=np.float64)
    result = cv2.warpAffine(image, matrix, size_wh, flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    support = cv2.warpAffine(np.ones(image.shape[:2]), matrix, size_wh, flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return result, support >= 1 - 1e-12


def largest_rectangle(mask):
    """Largest axis-aligned all-valid rectangle, returned as x0,y0,x1,y1."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2 or not mask.size:
        raise ValueError('Expected a nonempty 2D validity mask.')
    height = np.zeros(mask.shape[1], dtype=int)
    best_area, best = 0, None
    for y, row in enumerate(mask):
        height = np.where(row, height + 1, 0)
        stack = []
        for x in range(mask.shape[1] + 1):
            current = int(height[x]) if x < len(height) else 0
            start = x
            while stack and stack[-1][1] > current:
                left, h = stack.pop()
                area = h * (x - left)
                if area > best_area:
                    best_area, best = area, (left, y - h + 1, x, y + 1)
                start = left
            if current and (not stack or stack[-1][1] < current):
                stack.append((start, current))
    if best is None:
        raise ValueError('Images have no common valid rectangle.')
    return best


def luminance(image):
    image = np.asarray(image, dtype=np.float64)
    return image if image.ndim == 2 else image @ np.array([.2126, .7152, .0722])


def gaussian_blur(image, sigma):
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError('Sigma must be finite and positive.')
    image = np.asarray(image, dtype=np.float64)
    if image.ndim not in (2, 3) or not image.size or not np.isfinite(image).all():
        raise ValueError('Expected a nonempty finite image.')
    radius = int(np.ceil(4 * sigma))
    column = cv2.getGaussianKernel(2 * radius + 1, sigma, cv2.CV_64F).ravel()
    # Outer-product Gaussian applied separably, only along spatial axes.
    return convolve1d(convolve1d(image, column, axis=0, mode='reflect'), column, axis=1, mode='reflect')


def make_hybrid(low_image, high_image, sigma_low, sigma_high, gain=1., mode='gray'):
    low_image, high_image = np.asarray(low_image, dtype=float), np.asarray(high_image, dtype=float)
    if low_image.shape != high_image.shape or low_image.ndim != 3 or low_image.shape[2] != 3:
        raise ValueError('Aligned images must have equal RGB dimensions.')
    if mode not in MODES or not np.isfinite(gain) or gain < 0:
        raise ValueError('Invalid color mode or high-frequency gain.')
    low_input = low_image if mode in ('low_color', 'both_color') else np.repeat(luminance(low_image)[:, :, None], 3, axis=2)
    high_input = high_image if mode in ('high_color', 'both_color') else np.repeat(luminance(high_image)[:, :, None], 3, axis=2)
    low = gaussian_blur(low_input, sigma_low)
    high = high_input - gaussian_blur(high_input, sigma_high)
    return {'low_input': low_input, 'high_input': high_input, 'low': low,
            'high': high, 'hybrid': low + gain * high}


def log_spectrum(image):
    gray = luminance(image)
    return np.log(np.maximum(np.abs(np.fft.fftshift(np.fft.fft2(gray))), 1e-8))


def half_gain_frequency(sigma):
    """Continuous Gaussian approximation, cycles per pixel; gain = 1/2."""
    return np.sqrt(2 * np.log(2)) / (2 * np.pi * sigma)
