"""Custom masks and full-resolution multiresolution blending; reuse Part 2.3."""
import sys
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'PART 2.3 - GAUSSIAN AND LAPLACIAN STACKS'))
from stacks import gaussian_stack, laplacian_stack, blend_stacks, IMAGE_SIGMAS, MASK_SIGMAS


def polygon_mask(shape_hw, points):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3 or not np.isfinite(points).all():
        raise ValueError('At least three finite polygon vertices are required.')
    mask = np.zeros(shape_hw, dtype=np.uint8)
    cv2.fillPoly(mask, [np.round(points).astype(np.int32)], 1)
    return mask.astype(float)


def step_mask(shape_hw, fraction=.5):
    if not np.isfinite(fraction) or not 0 < fraction < 1:
        raise ValueError('Seam fraction must be between zero and one.')
    return (np.indices(shape_hw)[1] < round(shape_hw[1] * fraction)).astype(float)


def color_inputs(a, b, mode='both_color'):
    if mode not in ('gray', 'a_color', 'b_color', 'both_color'):
        raise ValueError('Unknown color mode.')
    gray = lambda x: np.repeat((x @ np.array([.2126, .7152, .0722]))[..., None], 3, axis=2)
    return (a if mode in ('a_color', 'both_color') else gray(a),
            b if mode in ('b_color', 'both_color') else gray(b))


def multiresolution_blend(a, b, mask, image_sigmas=IMAGE_SIGMAS, mask_sigmas=MASK_SIGMAS):
    a, b, mask = np.asarray(a, float), np.asarray(b, float), np.asarray(mask, float)
    if a.shape != b.shape or a.ndim != 3 or a.shape[2] != 3:
        raise ValueError('Aligned inputs must have equal RGB shapes.')
    if mask.shape != a.shape[:2] or not np.isfinite(mask).all() or (mask < 0).any() or (mask > 1).any():
        raise ValueError('A finite [0,1] mask matching the image is required.')
    if len(image_sigmas) != len(mask_sigmas):
        raise ValueError('Image and mask stacks must have the same level count.')
    ga, gb = gaussian_stack(a, image_sigmas), gaussian_stack(b, image_sigmas)
    la, lb = laplacian_stack(ga), laplacian_stack(gb)
    masks = np.clip(gaussian_stack(mask, mask_sigmas), 0., 1.)
    result = blend_stacks(la, lb, masks)
    result.update(left_gaussian=ga, right_gaussian=gb, left_laplacian=la, right_laplacian=lb, masks=masks)
    return result
