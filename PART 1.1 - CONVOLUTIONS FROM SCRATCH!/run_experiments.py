"""Generate selfie results and reproducible convolution comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
from time import perf_counter

import numpy as np
import scipy
from scipy.signal import convolve2d
from PIL import Image, ImageOps, __version__ as pillow_version

from convolution import convolve_four_loops, convolve_two_loops
from build_report import build_report

HERE = Path(__file__).resolve().parent


def load_gray(path, max_width):
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert('L')
        original_size = list(image.size)
        if image.width > max_width:
            image = image.resize((max_width, round(image.height * max_width / image.width)),
                                 Image.Resampling.LANCZOS)
        # Adapted from Assignment 1 colorize.normalize: uint8 to [0, 1].
        return np.asarray(image, dtype=np.float64) / 255, original_size


def save_gray(array, path, signed_scale=None):
    # Adapted from Assignment 1 save_rgb; signed values get a centered mapping.
    display = array if signed_scale is None else 0.5 + array / (2 * signed_scale)
    Image.fromarray(np.round(np.clip(display, 0, 1) * 255).astype(np.uint8)).save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=HERE / 'input/selfie.jpg')
    parser.add_argument('--max-width', type=int, default=480)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.max_width < 1 or args.repeats < 1:
        parser.error('max-width and repeats must be positive.')
    output = HERE / 'results'
    output.mkdir(exist_ok=True)
    image, original_size = load_gray(args.input, args.max_width)
    kernels = {'box': np.ones((9, 9), dtype=np.float64) / 81,
               'dx': np.array([[1., -1.]]), 'dy': np.array([[1.], [-1.]])}
    methods = {'four_loops': convolve_four_loops, 'two_loops': convolve_two_loops,
               'scipy': lambda a, k: convolve2d(a, k, mode='same', boundary='fill', fillvalue=0)}
    report = {'input': str(args.input.resolve()),
              'sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
              'original_size_wh': original_size, 'working_size_wh': [image.shape[1], image.shape[0]],
              'dtype': str(image.dtype), 'mode': 'same', 'boundary': 'zero fill',
              'repeats': args.repeats,
              'timing_scope': 'Convolution including padding/allocation; excludes I/O, resizing and visualization. One untimed warm-up on a 16x16 crop per method/kernel; median of sequential repeats.',
              'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                           'scipy': scipy.__version__, 'pillow': pillow_version}, 'filters': {}}
    arrays = {}
    save_gray(image, output / 'original-gray.png')
    for name, kernel in kernels.items():
        reference = methods['scipy'](image, kernel)
        rows = {}
        for method_name, function in methods.items():
            function(image[:16, :16], kernel)
            times = []
            for _ in range(args.repeats):
                start = perf_counter()
                result = function(image, kernel)
                times.append(perf_counter() - start)
            error = float(np.max(np.abs(result - reference)))
            np.testing.assert_allclose(result, reference, rtol=1e-12, atol=1e-12)
            rows[method_name] = {'seconds': times, 'median_seconds': float(np.median(times)),
                                 'max_abs_error': error, 'shape_hw': list(result.shape)}
            arrays[f'{name}_{method_name}'] = result
            print(f'{name}/{method_name}: {np.median(times):.6f}s; error={error:.3e}', flush=True)
        report['filters'][name] = {'kernel': kernel.tolist(), 'methods': rows,
                                   'range': [float(reference.min()), float(reference.max())]}
    scale = max(float(np.max(np.abs(arrays['dx_two_loops']))),
                float(np.max(np.abs(arrays['dy_two_loops'])))) or 1.
    report['derivative_display'] = {'zero': 0.5, 'shared_abs_scale': scale,
                                    'mapping': 'display = 0.5 + derivative / (2 * shared_abs_scale)'}
    for name in kernels:
        for method in methods:
            save_gray(arrays[f'{name}_{method}'], output / f'{name}-{method}.png',
                      None if name == 'box' else scale)
    np.savez_compressed(output / 'convolution-arrays.npz', original=image, **arrays)
    (output / 'metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    build_report()


if __name__ == '__main__':
    main()
