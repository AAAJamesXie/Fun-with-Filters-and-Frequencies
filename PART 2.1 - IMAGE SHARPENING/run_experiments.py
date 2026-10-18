"""Reproducible color sharpening experiments and artificial-blur evaluation."""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import cv2
import numpy as np
import scipy
from PIL import Image, ImageOps, ImageDraw, __version__ as pillow_version

from sharpen import gaussian_kernel, filter_image, unsharp_mask

HERE = Path(__file__).resolve().parent
AMOUNTS = [0., .5, 1., 2., 4.]


def load_rgb(path, max_width=480):
    with Image.open(path) as im:
        image = ImageOps.exif_transpose(im).convert('RGB')
        original_size = list(image.size)
        if image.width > max_width:
            image = image.resize((max_width, round(image.height * max_width / image.width)), Image.Resampling.LANCZOS)
        return np.asarray(image, dtype=np.float64) / 255., original_size


def save_rgb(array, path):
    Image.fromarray(np.round(np.clip(array, 0, 1) * 255).astype(np.uint8)).save(path)


def clipping(array):
    return {'below_zero_fraction': float(np.mean(array < 0)),
            'above_one_fraction': float(np.mean(array > 1)),
            'outside_fraction': float(np.mean((array < 0) | (array > 1))),
            'raw_range': [float(array.min()), float(array.max())]}


def evaluation(reference, candidate):
    raw_mse = float(np.mean((reference - candidate) ** 2))
    display = np.clip(candidate, 0, 1)
    display_mse = float(np.mean((reference - display) ** 2))
    return {'raw_mse': raw_mse, 'display_mse_before_quantization': display_mse,
            'display_psnr_db_before_quantization': None if display_mse == 0 else float(-10 * np.log10(display_mse))}


def crop_preview(array, box, path):
    x0, y0, x1, y1 = box
    image = Image.fromarray(np.round(np.clip(array[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8))
    image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST).save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sigma', type=float, default=1.5)
    args = parser.parse_args()
    gaussian_kernel(args.sigma)
    output = HERE / 'results'
    output.mkdir(exist_ok=True)
    arrays = {}
    report = {'sigma': args.sigma, 'selected_alpha': 1., 'amounts': AMOUNTS,
              'mode': 'same', 'boundary': 'symm', 'color': 'Independent spatial RGB convolutions on normalized encoded RGB values; no gamma linearization.',
              'display': {'high_frequency_abs_scale': .25, 'high_frequency_mapping': '0.5 + high/(2*0.25), clipped only for viewing',
                          'image_mapping': 'clip to [0,1], multiply by 255, round to uint8', 'crop_scale': '2x nearest neighbor'},
              'clipping_unit': 'fraction of scalar RGB channel samples, not fraction of pixels',
              'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                           'opencv': cv2.__version__, 'pillow': pillow_version}, 'images': {}}
    for name, box in [('taj', [85, 15, 215, 205]), ('selfie', [155, 135, 345, 370])]:
        path = HERE / f'input/{name}.jpg'
        image, original_size = load_rgb(path)
        selected = unsharp_mask(image, args.sigma, 1.)
        record = {'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'original_size_wh': original_size,
                  'working_size_wh': [image.shape[1], image.shape[0]], 'crop_xyxy': box,
                  'gaussian_shape': list(selected['gaussian'].shape), 'amounts': []}
        arrays[f'{name}_original'] = image
        arrays[f'{name}_blurred'] = selected['blurred']
        arrays[f'{name}_high'] = selected['high']
        for suffix, array in [('original', image), ('blurred', selected['blurred']),
                              ('high', .5 + selected['high'] / .5), ('selected', selected['sharpened'])]:
            save_rgb(array, output / f'{name}-{suffix}.png')
        for alpha in AMOUNTS:
            result = selected if alpha == 1. else unsharp_mask(image, args.sigma, alpha)
            np.testing.assert_allclose(result['sharpened'], result['single'], rtol=1e-12, atol=1e-14)
            tag = f'{name}-alpha-{alpha:.2f}'
            arrays[tag] = result['sharpened']
            arrays[tag + '-single'] = result['single']
            save_rgb(result['sharpened'], output / f'{tag}.png')
            crop_preview(result['sharpened'], box, output / f'{tag}-crop.png')
            record['amounts'].append({'alpha': alpha, 'file': f'{tag}.png', 'crop': f'{tag}-crop.png',
                                      'max_route_error': float(np.max(np.abs(result['sharpened'] - result['single']))),
                                      'kernel_sum': float(result['kernel'].sum()), **clipping(result['sharpened'])})
        report['images'][name] = record
        # Contact sheet gives a compact visual check of all sharpening amounts.
        sheet = Image.new('RGB', (len(AMOUNTS) * 220, 320), '#ece8e6')
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(record['amounts']):
            with Image.open(output / row['crop']) as preview:
                preview.thumbnail((212, 280))
                sheet.paste(preview, (i * 220 + (220 - preview.width) // 2, 0))
            draw.text((i * 220 + 8, 292), f'alpha = {row["alpha"]:g}', fill='#111111')
        sheet.save(output / f'{name}-amount-contact.png')
    reference = arrays['selfie_original']
    degraded = filter_image(reference, gaussian_kernel(2.))
    arrays['restore_reference'] = reference
    arrays['restore_degraded'] = degraded
    save_rgb(reference, output / 'restore-reference.png')
    save_rgb(degraded, output / 'restore-degraded.png')
    box = report['images']['selfie']['crop_xyxy']
    crop_preview(reference, box, output / 'restore-reference-crop.png')
    crop_preview(degraded, box, output / 'restore-degraded-crop.png')
    restore = {'degradation_sigma': 2., 'sharpen_sigma': args.sigma, 'selected_alpha': 2.,
               'reference': 'The resized selfie is the sharp reference for artificial Gaussian degradation; not a claim of an optically perfect photograph.',
               'degraded': evaluation(reference, degraded), 'amounts': []}
    for alpha in AMOUNTS:
        result = unsharp_mask(degraded, args.sigma, alpha)
        np.testing.assert_allclose(result['sharpened'], result['single'], rtol=1e-12, atol=1e-14)
        tag = f'restore-alpha-{alpha:.2f}'
        arrays[tag] = result['sharpened']
        save_rgb(result['sharpened'], output / f'{tag}.png')
        crop_preview(result['sharpened'], box, output / f'{tag}-crop.png')
        restore['amounts'].append({'alpha': alpha, 'file': f'{tag}.png', 'crop': f'{tag}-crop.png',
                                   'max_route_error': float(np.max(np.abs(result['sharpened'] - result['single']))),
                                   **evaluation(reference, result['sharpened']), **clipping(result['sharpened'])})
    report['restoration'] = restore
    np.savez_compressed(output / 'sharpen-arrays.npz', **arrays)
    (output / 'metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'sigma': args.sigma, 'route_errors': {key: max(row['max_route_error'] for row in value['amounts'])
                       for key, value in report['images'].items()}, 'restoration': restore}, indent=2))
    from build_report import build_report
    build_report()


if __name__ == '__main__':
    main()
