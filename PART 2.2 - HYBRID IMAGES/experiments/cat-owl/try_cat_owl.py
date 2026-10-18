"""Standalone cat/owl trial; reuses the tested Part 2.2 algorithms unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageOps, ImageDraw

HERE = Path(__file__).resolve().parent
PART = HERE.parents[1]
sys.path.insert(0, str(PART))
from hybrid import similarity_matrix, warp_image, largest_rectangle, make_hybrid

TRIALS = [(6., 1.5, 1.5), (10., 2., 1.), (14., 2., .8),
          (10., 3., 1.), (14., 3., 1.2), (18., 1.5, 2.)]


def prepared(path):
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        im = im.resize((512, round(im.height * 512 / im.width)), Image.Resampling.LANCZOS)
        return np.asarray(im, dtype=np.float64) / 255.


def display(array):
    return Image.fromarray(np.round(np.clip(array, 0, 1) * 255).astype(np.uint8))


def thumbnail(image, width):
    return image.resize((width, max(1, round(image.height * width / image.width))), Image.Resampling.LANCZOS)


def comparison(rows, path):
    columns, tw, th = 3, 280, 265
    sheet = Image.new('RGB', (columns * tw, ((len(rows) + columns - 1) // columns) * th), '#ece8e6')
    draw = ImageDraw.Draw(sheet)
    for i, (image, label) in enumerate(rows):
        x, y = i % columns * tw, i // columns * th
        large = image.copy(); large.thumbnail((210, 185), Image.Resampling.LANCZOS)
        small = thumbnail(image, 44)
        sheet.paste(large, (x + 4, y + 4)); sheet.paste(small, (x + 226, y + 4))
        draw.multiline_text((x + 4, y + 198), label, fill='#111111', spacing=4)
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selected', type=int, default=1, choices=range(len(TRIALS)))
    args = parser.parse_args()
    output = HERE / 'results'; output.mkdir(exist_ok=True)
    source_paths = {'cat': PART / 'input/chelsea.png', 'owl': HERE / 'input/owl.jpg'}
    points = {'cat': [[193., 126.], [358., 155.]], 'owl': [[190., 126.], [330., 126.]]}
    target = np.array([[150., 160.], [330., 160.]])
    warped, masks, matrices = {}, {}, {}
    for name, path in source_paths.items():
        source = prepared(path)
        display(source).save(output / f'original-{name}.png')
        matrix = similarity_matrix(points[name], target)
        matrices[name] = matrix
        warped[name], masks[name] = warp_image(source, matrix, (480, 400))
        np.testing.assert_allclose(np.c_[points[name], np.ones(2)] @ matrix.T, target, atol=1e-12)
    x0, y0, x1, y1 = largest_rectangle(masks['cat'] & masks['owl'])
    assert (masks['cat'] & masks['owl'])[y0:y1, x0:x1].all()
    aligned = {key: array[y0:y1, x0:x1] for key, array in warped.items()}
    for name, array in aligned.items(): display(array).save(output / f'aligned-{name}.png')
    metadata = {'status': 'Experimental preview only; formal Part 2.2 cases unchanged',
                'points_prepared_width_512': points, 'target_points': target.tolist(), 'canvas_wh': [480, 400],
                'common_crop_xyxy': [x0, y0, x1, y1], 'size_wh': [x1-x0, y1-y0], 'selected_trial': args.selected,
                'input_sha256': {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in source_paths.items()},
                'matrices': {key: matrix.tolist() for key, matrix in matrices.items()}, 'trials': []}
    arrays = {'aligned_cat': aligned['cat'], 'aligned_owl': aligned['owl']}
    for low, high in [('cat', 'owl'), ('owl', 'cat')]:
        rows = []
        selected = None
        for i, (sl, sh, gain) in enumerate(TRIALS):
            for mode in ('gray', 'low_color'):
                result = make_hybrid(aligned[low], aligned[high], sl, sh, gain, mode)
                np.testing.assert_array_equal(result['hybrid'], result['low'] + gain * result['high'])
                filename = f'{low}-low-{high}-high-{i}-{mode}.png'
                image = display(result['hybrid']); image.save(output / filename)
                metadata['trials'].append({'low': low, 'high': high, 'index': i, 'sigma_low': sl,
                    'sigma_high': sh, 'gain': gain, 'mode': mode, 'file': filename,
                    'clipped_channel_fraction': float(np.mean((result['hybrid'] < 0) | (result['hybrid'] > 1)))})
                if mode == 'low_color':
                    rows.append((image, f'Trial {i+1}: {low} low / {high} high\nsigma L={sl:g}, H={sh:g}, gain={gain:g}'))
                    if i == args.selected: selected = result
        comparison(rows, output / f'{low}-low-contact.png')
        image = display(selected['hybrid'])
        image.save(output / f'selected-{low}-low.png')
        widths = [image.width, max(1,image.width//2), max(1,image.width//4), max(1,image.width//8), max(1,image.width//16)]
        sheet = Image.new('RGB', (sum(widths) + 18 * (len(widths)-1), image.height + 32), '#ece8e6')
        draw = ImageDraw.Draw(sheet); x = 0
        for width in widths:
            small = thumbnail(image, width); sheet.paste(small, (x, 0))
            draw.text((x + 2, small.height + 7), f'{width}px', fill='#111111'); x += width + 18
        sheet.save(output / f'selected-{low}-low-scales.png')
        for name in ('low', 'high', 'hybrid'): arrays[f'{low}_low_selected_{name}'] = selected[name]
    np.savez_compressed(output / 'selected-arrays.npz', **arrays)
    (output / 'metrics.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print('Common valid size:', metadata['size_wh'], 'trials:',len(metadata['trials']), 'selected:',args.selected+1)


if __name__ == '__main__':
    main()
