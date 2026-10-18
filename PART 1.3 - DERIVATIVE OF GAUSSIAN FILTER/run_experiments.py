"""Generate Gaussian/DoG comparisons and the mandatory HSV direction result."""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import cv2
import numpy as np
import scipy
from PIL import Image, ImageDraw, __version__ as pillow_version
from scipy.signal import convolve2d

from dog import DX, DY, filter_routes, manual_orientation, orientation_rgb

HERE = Path(__file__).resolve().parent


def save_gray(array, path):
    Image.fromarray(np.round(np.clip(array, 0, 1) * 255).astype(np.uint8)).save(path)


def save_rgb(array, path):
    Image.fromarray(np.round(np.clip(array, 0, 1) * 255).astype(np.uint8)).save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sigma', type=float, default=2.)
    parser.add_argument('--threshold', type=float, default=.04)
    args = parser.parse_args()
    if not np.isfinite(args.threshold) or args.threshold < 0:
        parser.error('Threshold must be finite and nonnegative.')
    input_path = HERE / 'input/cameraman.png'
    with Image.open(input_path) as im:
        image = np.asarray(im.convert('L'), dtype=np.float64) / 255.
    output = HERE / 'results'
    output.mkdir(exist_ok=True)
    result = filter_routes(image, args.sigma)
    margin = result['margin']
    interior = (slice(margin, -margin), slice(margin, -margin))
    if image.shape[0] <= 2 * margin or image.shape[1] <= 2 * margin:
        raise ValueError('Image is too small for the selected Gaussian support.')
    raw_x = convolve2d(image, DX, mode='same', boundary='symm')
    raw_y = convolve2d(image, DY, mode='same', boundary='symm')
    raw_magnitude = np.sqrt(raw_x ** 2 + raw_y ** 2)
    magnitude = np.sqrt(result['sequential_x'] ** 2 + result['sequential_y'] ** 2)
    direct_magnitude = np.sqrt(result['direct_x'] ** 2 + result['direct_y'] ** 2)
    signed_scale = max(float(np.abs(raw_x).max()), float(np.abs(raw_y).max()))
    save_gray(image, output / 'original.png')
    save_gray(result['blurred'], output / 'blurred.png')
    for name, array in [('raw-x', raw_x), ('raw-y', raw_y),
                        ('sequential-x', result['sequential_x']), ('sequential-y', result['sequential_y']),
                        ('direct-x', result['direct_x']), ('direct-y', result['direct_y'])]:
        save_gray(.5 + array / (2 * signed_scale), output / f'{name}.png')
    for name, array in [('raw', raw_magnitude), ('sequential', magnitude), ('direct', direct_magnitude)]:
        # Shared contrast gain only for viewing; raw arrays are thresholded.
        save_gray(array / .25, output / f'{name}-magnitude.png')
        save_gray(array > .2, output / f'{name}-edges-020.png')
    save_gray(magnitude > args.threshold, output / 'edges-selected.png')
    kernel_scale = max(float(np.abs(result['kx']).max()), float(np.abs(result['ky']).max()))
    for name in ('gaussian', 'kx', 'ky'):
        array = result[name]
        display = array / array.max() if name == 'gaussian' else .5 + array / (2 * kernel_scale)
        tile = Image.fromarray(np.round(np.clip(display, 0, 1) * 255).astype(np.uint8))
        tile.resize((array.shape[1] * 24, array.shape[0] * 24), Image.Resampling.NEAREST).save(output / f'kernel-{name}.png')
    error = {}
    for axis in ('x', 'y'):
        delta = np.abs(result['sequential_' + axis] - result['direct_' + axis])
        np.testing.assert_allclose(result['sequential_' + axis][interior], result['direct_' + axis][interior],
                                   rtol=1e-11, atol=1e-14)
        error[axis] = {'full_max_abs': float(delta.max()), 'interior_max_abs': float(delta[interior].max())}
        scale = float(delta.max()) or 1.
        save_gray(delta / scale, output / f'route-difference-{axis}.png')
    threshold_rows = []
    thresholds = sorted(set([.02, .04, .06, .08, .10, args.threshold]))
    sheet = Image.new('RGB', (3 * 280, ((len(thresholds) + 2) // 3) * 310), '#ece8e6')
    draw = ImageDraw.Draw(sheet)
    for index, threshold in enumerate(thresholds):
        mask = magnitude > threshold
        filename = f'edges-{threshold:.4f}.png'
        save_gray(mask, output / filename)
        count = int(mask.sum())
        threshold_rows.append({'threshold': threshold, 'file': filename, 'edge_pixels': count,
                               'edge_fraction': count / mask.size})
        x, y = (index % 3) * 280, (index // 3) * 310
        tile = Image.fromarray(mask.astype(np.uint8) * 255).resize((280, 280), Image.Resampling.NEAREST).convert('RGB')
        sheet.paste(tile, (x, y))
        draw.text((x + 8, y + 287), f'T = {threshold:.2f} | {count / mask.size:.1%} edges', fill='#111111')
    sheet.save(output / 'threshold-contact.png')
    sigma_rows = []
    for sigma in sorted(set([1., 2., 3., args.sigma])):
        experiment = result if sigma == args.sigma else filter_routes(image, sigma)
        mag = np.sqrt(experiment['sequential_x'] ** 2 + experiment['sequential_y'] ** 2)
        name = f'sigma-{sigma:.2f}'
        save_gray(experiment['blurred'], output / f'{name}-blurred.png')
        save_gray(mag / .25, output / f'{name}-magnitude.png')
        save_gray(mag > args.threshold, output / f'{name}-edges.png')
        sigma_rows.append({'sigma': sigma, 'kernel_size': list(experiment['gaussian'].shape),
                           'prefix': name, 'edge_fraction': float(np.mean(mag > args.threshold))})
    angle_raw = manual_orientation(raw_x, raw_y)
    angle_smooth = manual_orientation(result['sequential_x'], result['sequential_y'])
    save_rgb(orientation_rgb(angle_raw, raw_magnitude, .15), output / 'orientation-raw.png')
    save_rgb(orientation_rgb(angle_smooth, magnitude, .15), output / 'orientation-smoothed.png')
    y, x = np.mgrid[-200:200, -200:200]
    disk = x ** 2 + y ** 2 <= 135 ** 2
    wheel = orientation_rgb(manual_orientation(x, y), np.ones(x.shape), 1.)
    wheel[~disk] = 1.
    legend = Image.fromarray(np.round(wheel * 255).astype(np.uint8))
    labels = ImageDraw.Draw(legend)
    labels.text((338, 192), '0 / +x', fill='black')
    labels.text((175, 350), '90 / +y', fill='black')
    labels.text((4, 192), '180 / -x', fill='black')
    labels.text((172, 40), '270 / -y', fill='black')
    legend.save(output / 'orientation-wheel.png')
    np.savez_compressed(output / 'dog-arrays.npz', original=image, raw_x=raw_x, raw_y=raw_y,
                        raw_magnitude=raw_magnitude, magnitude=magnitude, direct_magnitude=direct_magnitude,
                        angle_raw=angle_raw, angle_smoothed=angle_smooth, selected_edges=magnitude > args.threshold,
                        **{key: value for key, value in result.items() if key != 'margin'})
    metrics = {'sigma': args.sigma, 'threshold': args.threshold, 'kernel_shape': list(result['gaussian'].shape),
               'dog_shapes': {'x': list(result['kx'].shape), 'y': list(result['ky'].shape)},
               'kernel_sums': {key: float(result[key].sum()) for key in ('gaussian', 'kx', 'ky')},
               'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(), 'size_wh': [image.shape[1], image.shape[0]],
               'boundary': 'symm', 'mode': 'same', 'comparison_margin': margin, 'route_errors': error,
               'threshold_sweep': threshold_rows, 'sigma_sweep': sigma_rows,
               'selected_edge_fraction': float(np.mean(magnitude > args.threshold)),
               'fixed_threshold_020': {'raw': float(np.mean(raw_magnitude > .2)), 'smoothed': float(np.mean(magnitude > .2))},
               'display': {'derivative_abs_scale': signed_scale, 'magnitude_white_at': .25, 'orientation_value_white_at': .15},
               'orientation': {'method': '24-term alternating series with range reduction; manual quadrant recovery',
                               'units': 'radians', 'range': '[0, 2*pi)', 'convention': 'clockwise from +x; +y is down',
                               'hsv': 'H=theta/(2*pi), S=1, V=clip(magnitude/0.15,0,1)', 'zero_gradient': 'angle=0, V=0 (black)'},
               'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                            'opencv': cv2.__version__, 'pillow': pillow_version}}
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(json.dumps(metrics, indent=2))
    from build_report import build_report
    build_report()


if __name__ == '__main__':
    main()
