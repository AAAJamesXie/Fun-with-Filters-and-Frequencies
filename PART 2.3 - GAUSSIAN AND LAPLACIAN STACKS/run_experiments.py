"""Generate full-resolution stacks, an oraple, and Figure 3.42-style panels."""
import hashlib
import json
from pathlib import Path
import platform
import string

import cv2
import numpy as np
import scipy
from PIL import Image, ImageDraw, __version__ as pillow_version

from stacks import IMAGE_SIGMAS, MASK_SIGMAS, gaussian_stack, laplacian_stack, blend_stacks

HERE = Path(__file__).resolve().parent


def display(array):
    return Image.fromarray(np.round(np.clip(array, 0, 1) * 255).astype(np.uint8))


def save(array, path):
    display(array).save(path)


def main():
    output = HERE / 'results'; output.mkdir(exist_ok=True)
    images, inputs = {}, {}
    for key in ('apple', 'orange'):
        path = HERE / f'input/{key}.png'
        with Image.open(path) as im:
            images[key] = np.asarray(im.convert('RGB'), dtype=np.float64) / 255.
        inputs[key] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'size_wh': [images[key].shape[1], images[key].shape[0]]}
        save(images[key], output / f'original-{key}.png')
    if images['apple'].shape != images['orange'].shape:
        raise ValueError('Apple and orange must have the same dimensions.')
    height, width = images['apple'].shape[:2]
    hard_mask = np.zeros((height, width)); hard_mask[:, :width // 2] = 1.
    masks = np.clip(gaussian_stack(hard_mask, MASK_SIGMAS), 0., 1.)
    gs, ls = {}, {}
    for key, image in images.items():
        gs[key] = gaussian_stack(image, IMAGE_SIGMAS)
        ls[key] = laplacian_stack(gs[key])
        np.testing.assert_allclose(ls[key].sum(axis=0), image, atol=1e-14, rtol=1e-12)
        print(key, 'Gaussian/Laplacian stacks built', flush=True)
    result = blend_stacks(ls['apple'], ls['orange'], masks)
    np.testing.assert_allclose(result['left'] + result['right'], result['image'], atol=1e-14, rtol=1e-12)
    hard_join = hard_mask[..., None] * images['apple'] + (1 - hard_mask[..., None]) * images['orange']
    feather = masks[4, ..., None] * images['apple'] + (1 - masks[4, ..., None]) * images['orange']
    save(hard_mask, output / 'mask-binary.png')
    save(hard_join, output / 'hard-join.png'); save(feather, output / 'single-feather.png')
    save(result['image'], output / 'oraple.png')
    oraple_g = gaussian_stack(result['image'], IMAGE_SIGMAS)
    oraple_l = laplacian_stack(oraple_g)
    band_scales = []
    for level in range(len(IMAGE_SIGMAS)):
        save(masks[level], output / f'mask-{level}.png')
        scale = max(float(np.abs(ls['apple'][level]).max()), float(np.abs(ls['orange'][level]).max()),
                    float(np.abs(oraple_l[level]).max())) or 1.
        band_scales.append(scale)
        for key in ('apple', 'orange', 'oraple'):
            gaussian = oraple_g if key == 'oraple' else gs[key]
            laplacian = oraple_l if key == 'oraple' else ls[key]
            save(gaussian[level], output / f'{key}-gaussian-{level}.png')
            shown = laplacian[level] if level == len(IMAGE_SIGMAS) - 1 else .5 + laplacian[level] / (2 * scale)
            save(shown, output / f'{key}-laplacian-{level}.png')
    panels = []
    for level in (0, 2, 4):
        arrays = [result['left_bands'][level], result['right_bands'][level], result['bands'][level]]
        scale = max(float(np.abs(array).max()) for array in arrays) or 1.
        for column, array in zip(('left', 'right', 'combined'), arrays):
            filename = f'figure-{string.ascii_lowercase[len(panels)]}.png'
            save(.5 + array / (2 * scale), output / filename)
            panels.append({'letter': string.ascii_lowercase[len(panels)], 'file': filename,
                           'level': level, 'column': column, 'signed_abs_scale': scale})
    for column in ('left', 'right', 'image'):
        filename = f'figure-{string.ascii_lowercase[len(panels)]}.png'
        save(result[column], output / filename)
        panels.append({'letter': string.ascii_lowercase[len(panels)], 'file': filename,
                       'level': 'sum of all six levels', 'column': column, 'display': 'ordinary RGB [0,1]'})
    sheet = Image.new('RGB', (3 * 320, 4 * 258), '#ece8e6')
    draw = ImageDraw.Draw(sheet)
    for i, panel in enumerate(panels):
        with Image.open(output / panel['file']) as im:
            im = im.resize((310, round(height * 310 / width)), Image.Resampling.LANCZOS)
        x, y = i % 3 * 320 + 5, i // 3 * 258
        sheet.paste(im, (x, y))
        label = f'({panel["letter"]}) ' + (f'L{panel["level"]}' if isinstance(panel['level'], int) else 'reconstruction')
        draw.text((x + 5, y + im.height + 9), label, fill='#111111')
    sheet.save(output / 'figure-3-42.png')
    errors = {key: float(np.max(np.abs(ls[key].sum(axis=0) - image))) for key, image in images.items()}
    errors['oraple_reconstruction'] = float(np.max(np.abs(oraple_l.sum(axis=0) - result['image'])))
    errors['left_plus_right'] = float(np.max(np.abs(result['left'] + result['right'] - result['image'])))
    errors['mask_complement'] = float(np.max(np.abs(masks + (1 - masks) - 1)))
    arrays = {'apple': images['apple'], 'orange': images['orange'], 'apple_gaussian': gs['apple'],
              'orange_gaussian': gs['orange'], 'apple_laplacian': ls['apple'], 'orange_laplacian': ls['orange'],
              'mask_binary': hard_mask, 'mask_gaussian': masks, 'mask_complement': 1 - masks,
              'hard_join': hard_join, 'single_feather': feather, 'oraple_gaussian': oraple_g,
              'oraple_laplacian': oraple_l, **result}
    np.savez_compressed(output / 'stack-arrays.npz', **arrays)
    metrics = {'inputs': inputs, 'image_sigmas': list(IMAGE_SIGMAS), 'mask_sigmas': list(MASK_SIGMAS),
               'incremental_sigmas': [0.] + [float(np.sqrt(b*b-a*a)) for a,b in zip(IMAGE_SIGMAS,IMAGE_SIGMAS[1:])],
               'mask_incremental_sigmas': [MASK_SIGMAS[0]] + [float(np.sqrt(b*b-a*a)) for a,b in zip(MASK_SIGMAS,MASK_SIGMAS[1:])],
               'levels': len(IMAGE_SIGMAS), 'gaussian_shape': list(gs['apple'].shape), 'laplacian_shape': list(ls['apple'].shape),
               'mask_shape': list(masks.shape), 'downsampling': False, 'boundary': 'reflect (half-sample symmetric)',
               'gaussian_radius': 'ceil(4*incremental_sigma)', 'last_laplacian_level': 'coarse Gaussian residual, essential for reconstruction',
               'split_column': width // 2, 'mask_fine_sigma': MASK_SIGMAS[0],
               'single_feather_sigma': MASK_SIGMAS[4], 'errors': errors, 'band_display_scales': band_scales,
               'figure_panels': panels, 'figure_selected_levels': [0, 2, 4],
               'raw_result_range': [float(result['image'].min()), float(result['image'].max())],
               'display_clip_fraction': float(np.mean((result['image'] < 0) | (result['image'] > 1))),
               'display': 'Signed bands: 0.5 + band/(2*scale). Same scale within each figure row and each displayed stack level. Ordinary photographs/coarse residual: clip [0,1], round to uint8. No clipping in reconstruction.',
               'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                            'opencv': cv2.__version__, 'pillow': pillow_version}}
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(json.dumps({'shape': metrics['gaussian_shape'], 'errors': errors, 'raw_result_range': metrics['raw_result_range']}, indent=2))


if __name__ == '__main__':
    main()
