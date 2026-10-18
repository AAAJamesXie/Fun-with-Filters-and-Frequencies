"""Create finite differences, a threshold sweep, raw arrays and an HTML report."""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from PIL import Image, ImageDraw, __version__ as pillow_version

from edges import DX, DY, gradients, threshold_edges
from build_report import build_report

HERE = Path(__file__).resolve().parent


def save_gray(array, path):
    Image.fromarray(np.round(np.clip(array, 0, 1) * 255).astype(np.uint8)).save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=HERE / 'input/cameraman.png')
    parser.add_argument('--threshold', type=float, default=0.20)
    args = parser.parse_args()
    with Image.open(args.input) as source:
        image = np.asarray(source.convert('L'), dtype=np.float64) / 255.
    dx, dy, magnitude = gradients(image)
    selected = threshold_edges(magnitude, args.threshold)
    output = HERE / 'results'
    output.mkdir(exist_ok=True)
    signed_scale = max(float(np.abs(dx).max()), float(np.abs(dy).max())) or 1.
    save_gray(image, output / 'original.png')
    save_gray(0.5 + dx / (2 * signed_scale), output / 'dx.png')
    save_gray(0.5 + dy / (2 * signed_scale), output / 'dy.png')
    # Magnitude is displayed without per-image normalization; >1 clips only in PNG.
    save_gray(magnitude, output / 'magnitude.png')
    save_gray(selected, output / 'edges-selected.png')
    thresholds = sorted(set([0.05, 0.1, 0.15, 0.2, 0.25, 0.3, args.threshold]))
    records = []
    columns, tile = 3, 280
    sheet = Image.new('RGB', (columns * tile, ((len(thresholds) + columns - 1) // columns) * (tile + 32)), '#ece8e6')
    draw = ImageDraw.Draw(sheet)
    for index, threshold in enumerate(thresholds):
        mask = threshold_edges(magnitude, threshold)
        filename = f'edges-{threshold:.4f}.png'
        save_gray(mask, output / filename)
        count = int(mask.sum())
        records.append({'threshold': threshold, 'file': filename, 'edge_pixels': count,
                        'edge_fraction': count / mask.size})
        with Image.open(output / filename) as preview:
            preview = preview.resize((tile, tile), Image.Resampling.NEAREST).convert('RGB')
        x, y = (index % columns) * tile, (index // columns) * (tile + 32)
        sheet.paste(preview, (x, y))
        draw.text((x + 6, y + tile + 8), f'T = {threshold:.2f} | edges {count / mask.size:.1%}', fill='#111111')
    sheet.save(output / 'threshold-contact.png')
    np.savez_compressed(output / 'gradient-arrays.npz', original=image, dx=dx, dy=dy,
                        magnitude=magnitude, selected_edges=selected)
    report = {'input': args.input.name, 'sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
              'size_wh': [image.shape[1], image.shape[0]], 'input_range': [float(image.min()), float(image.max())],
              'dtype': str(image.dtype), 'kernels': {'dx': DX.tolist(), 'dy': DY.tolist()},
              'mode': 'same', 'boundary': 'symm', 'smoothing': False,
              'magnitude_formula': 'sqrt(dx**2 + dy**2)', 'selected_threshold': args.threshold,
              'threshold_rule': 'raw_magnitude > threshold', 'threshold_sweep': records,
              'magnitude_range': [float(magnitude.min()), float(magnitude.max())],
              'display': {'signed_scale': signed_scale, 'zero': 0.5,
                          'magnitude_mapping': 'clip(raw_magnitude, 0, 1); thresholding uses unclipped raw values'},
              'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                           'scipy': scipy.__version__, 'pillow': pillow_version}}
    (output / 'metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    build_report()
    print(json.dumps({'size_wh': report['size_wh'], 'selected_threshold': args.threshold,
                      'magnitude_range': report['magnitude_range'], 'threshold_sweep': records}, indent=2))


if __name__ == '__main__':
    main()
