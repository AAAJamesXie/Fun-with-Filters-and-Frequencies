"""Generate aligned hybrid examples, parameter trials, spectra and color studies."""
import hashlib
import json
from pathlib import Path
import platform

import cv2
import numpy as np
import scipy
from PIL import Image, ImageDraw, ImageOps, __version__ as pillow_version

from hybrid import (MODES, similarity_matrix, warp_image, largest_rectangle, luminance,
                    make_hybrid, log_spectrum, half_gain_frequency)

HERE = Path(__file__).resolve().parent
TRIALS = [(4., 2.), (7., 2.), (7., 4.), (10., 2.), (10., 4.), (14., 3.)]


def load_source(name):
    filename = name + ('.png' if name == 'chelsea' else '.jpg')
    path = HERE / 'input' / filename
    with Image.open(path) as im:
        image = ImageOps.exif_transpose(im).convert('RGB')
        original_size = list(image.size)
        image = image.resize((512, round(image.height * 512 / image.width)), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float64) / 255., {'filename': filename, 'original_size_wh': original_size,
            'prepared_size_wh': list(image.size), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def display_image(array):
    return Image.fromarray(np.round(np.clip(array, 0, 1) * 255).astype(np.uint8))


def save(array, path):
    display_image(array).save(path)


def scale_strip(array, path):
    image = display_image(array)
    widths = [max(1, image.width // factor) for factor in (1, 2, 4, 8, 16)]
    sheet = Image.new('RGB', (sum(widths) + 18 * (len(widths) - 1), image.height + 32), '#ece8e6')
    draw = ImageDraw.Draw(sheet)
    x = 0
    for width in widths:
        small = image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
        sheet.paste(small, (x, 0))
        draw.text((x + 3, small.height + 8), f'{width}px', fill='#111111')
        x += width + 18
    sheet.save(path)


def contact(candidates, path):
    tile_width, tile_height = 260, 330
    sheet = Image.new('RGB', (3 * tile_width, ((len(candidates) + 2) // 3) * tile_height), '#ece8e6')
    draw = ImageDraw.Draw(sheet)
    for index, (array, label) in enumerate(candidates):
        image = display_image(array)
        preview = image.copy(); preview.thumbnail((190, 275), Image.Resampling.LANCZOS)
        tiny = image.copy(); tiny.thumbnail((48, 70), Image.Resampling.LANCZOS)
        x, y = (index % 3) * tile_width, (index // 3) * tile_height
        sheet.paste(preview, (x, y)); sheet.paste(tiny, (x + 202, y))
        draw.text((x + 4, y + 290), label, fill='#111111')
    sheet.save(path)


def main():
    config = json.loads((HERE / 'pairs.json').read_text())
    output = HERE / 'results'; output.mkdir(exist_ok=True)
    metrics = {'canvas_wh': config['canvas_wh'], 'favorite': config['favorite'],
        'alignment': 'Manual eye landmarks; two-point similarity transform, bilinear warping; largest all-valid shared rectangle.',
        'filters': 'Separable normalized Gaussian, radius ceil(4*sigma), symmetric boundary extension; sigma in aligned cropped pixels.',
        'formula': 'hybrid = Gaussian(low,sigma_low) + gain*(high-Gaussian(high,sigma_high))',
        'display': {'photo': 'clip raw hybrid to [0,1] then round to uint8', 'signed_high_abs_scale': .3,
                    'spectrum': 'natural log(max(abs(fftshift(fft2(gray))),1e-8)); shared 1st/99.8th percentile display range per case',
                    'small_views': 'Lanczos downsampling of the same clipped hybrid; a viewing-scale aid, not a calibrated optical distance'},
        'color': 'Encoded RGB with fixed 0.2126/0.7152/0.0722 grayscale weights; no gamma linearization.',
        'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                     'opencv': cv2.__version__, 'pillow': pillow_version}, 'cases': []}
    for case in config['pairs']:
        name = case['id']; dest = output / name; dest.mkdir(exist_ok=True)
        low_source, low_info = load_source(case['low']); high_source, high_info = load_source(case['high'])
        target = np.asarray(case['target_points'])
        low_matrix = similarity_matrix(case['low_points'], target)
        high_matrix = similarity_matrix(case['high_points'], target)
        low_warped, low_valid = warp_image(low_source, low_matrix, tuple(config['canvas_wh']))
        high_warped, high_valid = warp_image(high_source, high_matrix, tuple(config['canvas_wh']))
        box = largest_rectangle(low_valid & high_valid); x0, y0, x1, y1 = box
        assert (low_valid & high_valid)[y0:y1, x0:x1].all()
        low, high = low_warped[y0:y1, x0:x1], high_warped[y0:y1, x0:x1]
        arrays = {'low_source': low_source, 'high_source': high_source, 'aligned_low': low,
                  'aligned_high': high, 'low_matrix': low_matrix, 'high_matrix': high_matrix}
        for role, source, points in [('low', low_source, case['low_points']), ('high', high_source, case['high_points'])]:
            save(source, dest / f'original-{role}.png')
            marked = display_image(source); draw = ImageDraw.Draw(marked)
            for index, (x, y) in enumerate(points):
                draw.ellipse((x-6, y-6, x+6, y+6), outline='red', width=2)
                draw.text((x+9, y), str(index+1), fill='red')
            marked.save(dest / f'landmarks-{role}.png')
        save(low, dest / 'aligned-low.png'); save(high, dest / 'aligned-high.png')
        save(.5 * low + .5 * high, dest / 'alignment-overlay.png')
        results = {}
        variants = []
        for mode in MODES:
            result = make_hybrid(low, high, case['sigma_low'], case['sigma_high'], case['gain'], mode)
            arrays['hybrid_' + mode] = result['hybrid']
            save(result['hybrid'], dest / f'hybrid-{mode}.png')
            display_image(result['hybrid']).resize((max(1, low.shape[1] // 8), max(1, low.shape[0] // 8)),
                                                     Image.Resampling.LANCZOS).save(dest / f'far-{mode}.png')
            variants.append((result['hybrid'], mode))
            results[mode] = result
        selected = results[case['mode']]
        for key in ('low_input', 'high_input', 'low', 'high', 'hybrid'): arrays[key] = selected[key]
        save(selected['low'], dest / 'filtered-low.png')
        save(.5 + selected['high'] / .6, dest / 'filtered-high.png')
        save(selected['hybrid'], dest / 'hybrid-selected.png')
        scale_strip(selected['hybrid'], dest / 'scale-strip.png')
        contact(variants, dest / 'color-contact.png')
        trials = []
        candidates = list(TRIALS)
        selected_parameters = (float(case['sigma_low']), float(case['sigma_high']))
        if selected_parameters not in candidates:
            candidates.append(selected_parameters)
        for index, (sl, sh) in enumerate(candidates):
            trial = make_hybrid(low, high, sl, sh, case['gain'], case['mode'])
            file = f'trial-{index}.png'; save(trial['hybrid'], dest / file)
            trials.append({'sigma_low': sl, 'sigma_high': sh, 'file': file})
        contact([(make_hybrid(low, high, row['sigma_low'], row['sigma_high'], case['gain'], case['mode'])['hybrid'],
                  f'sigma L={row["sigma_low"]:g}, H={row["sigma_high"]:g}') for row in trials], dest / 'parameter-contact.png')
        reversed_result = make_hybrid(high, low, case['sigma_low'], case['sigma_high'], case['gain'], case['mode'])
        save(reversed_result['hybrid'], dest / 'hybrid-reversed.png')
        contact([(selected['hybrid'], 'Selected assignment'), (reversed_result['hybrid'], 'Roles reversed')], dest / 'roles-contact.png')
        spectra = {'input-low': selected['low_input'], 'input-high': selected['high_input'],
                   'filtered-low': selected['low'], 'filtered-high': selected['high'], 'hybrid': selected['hybrid']}
        logs = {key: log_spectrum(array) for key, array in spectra.items()}
        display_low, display_high = np.percentile(np.concatenate([value.ravel() for value in logs.values()]), [1., 99.8])
        for key, value in logs.items():
            arrays['spectrum_' + key] = value
            save((value - display_low) / (display_high - display_low), dest / f'fft-{key}.png')
        arrays['reversed_hybrid'] = reversed_result['hybrid']
        np.savez_compressed(dest / 'arrays.npz', **arrays)
        errors = []
        for source, points, matrix in [(low_source, case['low_points'], low_matrix), (high_source, case['high_points'], high_matrix)]:
            transformed = np.c_[points, np.ones(2)] @ matrix.T
            errors.append(float(np.max(np.abs(transformed-target))))
        raw = selected['hybrid']
        record = {**case, 'low_source': low_info, 'high_source': high_info, 'crop_xyxy': box,
            'size_wh': [low.shape[1], low.shape[0]], 'landmark_max_abs_error': errors,
            'cutoff_half_gain_cpp': {'low': float(half_gain_frequency(case['sigma_low'])), 'high': float(half_gain_frequency(case['sigma_high']))},
            'cutoff_half_gain_cycles_per_width': {'low': float(half_gain_frequency(case['sigma_low']) * low.shape[1]),
                                                  'high': float(half_gain_frequency(case['sigma_high']) * low.shape[1])},
            'spectrum_display_range': [float(display_low), float(display_high)], 'trials': trials,
            'raw_hybrid_range': [float(raw.min()), float(raw.max())], 'outside_channel_fraction': float(np.mean((raw < 0) | (raw > 1)))}
        metrics['cases'].append(record)
        print(name, record['size_wh'], 'eye error', errors, 'clip', record['outside_channel_fraction'], flush=True)
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
