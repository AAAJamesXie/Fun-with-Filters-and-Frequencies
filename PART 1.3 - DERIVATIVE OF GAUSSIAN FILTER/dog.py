"""Gaussian derivatives and HSV gradient orientation, without angle APIs."""
import cv2
import numpy as np
from scipy.signal import convolve2d

DX = np.array([[1., -1.]])
DY = DX.T


def gaussian_kernel(sigma):
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError('Sigma must be finite and positive.')
    radius = int(np.ceil(3 * sigma))
    column = cv2.getGaussianKernel(2 * radius + 1, sigma, cv2.CV_64F)
    return column @ column.T


def dog_kernels(sigma):
    gaussian = gaussian_kernel(sigma)
    # Full convolution retains the complete derivative support and alignment.
    return (gaussian, convolve2d(gaussian, DX, mode='full'),
            convolve2d(gaussian, DY, mode='full'))


def filter_routes(image, sigma):
    image = np.asarray(image, dtype=np.float64)
    if image.ndim != 2 or not image.size or not np.isfinite(image).all():
        raise ValueError('Expected a nonempty finite 2D image.')
    gaussian, kx, ky = dog_kernels(sigma)
    blurred = convolve2d(image, gaussian, mode='same', boundary='symm')
    sequential_x = convolve2d(blurred, DX, mode='same', boundary='symm')
    sequential_y = convolve2d(blurred, DY, mode='same', boundary='symm')
    direct_x = convolve2d(image, kx, mode='same', boundary='symm')
    direct_y = convolve2d(image, ky, mode='same', boundary='symm')
    return {'gaussian': gaussian, 'kx': kx, 'ky': ky, 'blurred': blurred,
            'sequential_x': sequential_x, 'sequential_y': sequential_y,
            'direct_x': direct_x, 'direct_y': direct_y,
            'margin': gaussian.shape[0] // 2 + 1}


def manual_orientation(dx, dy):
    """Direction in [0, 2pi), clockwise from +x in image coordinates.

    Compute arctangent with a 24-term alternating series after reducing its
    argument to abs(z) <= sqrt(2)-1. No built-in inverse trig or angle API.
    Zero gradients receive direction zero; their displayed value is black.
    """
    dx, dy = np.broadcast_arrays(np.asarray(dx, dtype=np.float64),
                                 np.asarray(dy, dtype=np.float64))
    if not np.isfinite(dx).all() or not np.isfinite(dy).all():
        raise ValueError('Gradients must be finite.')
    ax, ay = np.abs(dx), np.abs(dy)
    largest = np.maximum(ax, ay)
    ratio = np.divide(np.minimum(ax, ay), largest, out=np.zeros_like(largest), where=largest > 0)
    reduce = ratio > np.sqrt(2.) - 1.
    z = np.where(reduce, (ratio - 1.) / (ratio + 1.), ratio)
    power = z.copy()
    series = np.zeros_like(z)
    for n in range(24):
        series += power / (2 * n + 1)
        power *= -z * z
    alpha = series + np.where(reduce, np.pi / 4, 0.)
    alpha = np.where(ay > ax, np.pi / 2 - alpha, alpha)
    angle = np.where(dx < 0, np.pi - alpha, alpha)
    angle = np.where(dy < 0, 2 * np.pi - angle, angle)
    return np.where(largest > 0, angle % (2 * np.pi), 0.)


def orientation_rgb(angle, magnitude, value_scale):
    """HSV: H=direction/(2pi), S=1, V=clip(magnitude/value_scale,0,1)."""
    if not np.isfinite(value_scale) or value_scale <= 0:
        raise ValueError('Display scale must be finite and positive.')
    hue = (np.asarray(angle) / (2 * np.pi)) % 1.
    value = np.clip(np.asarray(magnitude) / value_scale, 0., 1.)
    sector = np.floor(hue * 6).astype(int)
    fraction = hue * 6 - sector
    zero = np.zeros_like(value)
    q, t = value * (1 - fraction), value * fraction
    choices = ((value, t, zero), (q, value, zero), (zero, value, t),
               (zero, q, value), (t, zero, value), (value, zero, q))
    rgb = np.zeros(value.shape + (3,))
    for index, channels in enumerate(choices):
        mask = sector == index
        rgb[mask] = np.stack(channels, axis=-1)[mask]
    return rgb
