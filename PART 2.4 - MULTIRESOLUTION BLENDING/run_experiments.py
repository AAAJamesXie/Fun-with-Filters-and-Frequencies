"""Prepare authentic photographs, blend three custom pairs, save reproducible evidence."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from blending import (multiresolution_blend, color_inputs, polygon_mask, step_mask,
                      gaussian_stack, IMAGE_SIGMAS, MASK_SIGMAS)
from prepare_objects import prepare_cases, load_rgb, match_chroma

HERE = Path(__file__).resolve().parent


def save(array, path):
    Image.fromarray(np.round(np.clip(array, 0, 1)*255).astype('uint8')).save(path)


def main():
    out = HERE/'results'; out.mkdir(exist_ok=True)
    metrics = {'image_sigmas':IMAGE_SIGMAS, 'mask_sigmas':MASK_SIGMAS, 'favorite':'kiwi-lime',
               'convention':'Mask 1 selects A; mask 0 selects B. Encoded RGB, no gamma linearization. Float64 bands; display exports clipped. Basketball Lab chroma matching is separate preprocessing.',
               'cases':[]}
    for case in prepare_cases():
        dest = out/case['id']; dest.mkdir(exist_ok=True)
        raw_a, b = case['a'], case['b']
        vertices = case['vertices']
        mask = step_mask(raw_a.shape[:2]) if vertices is None else polygon_mask(raw_a.shape[:2], vertices)
        assert mask.min() == 0 and mask.max() == 1
        a = raw_a
        shift = None
        if case['id'] == 'orange-basketball':
            yy,xx = np.indices(mask.shape)
            roi = ((xx-256)**2+(yy-256)**2 < 150**2) & (raw_a.min(2) > .12)
            a, shift = match_chroma(raw_a,b,roi)
        result = multiresolution_blend(a,b,mask)
        unadjusted = result['image'] if shift is None else multiresolution_blend(raw_a,b,mask)['image']
        hard = mask[...,None]*a+(1-mask[...,None])*b
        feather_mask = gaussian_stack(mask, (0.,16.))[-1]
        feather = feather_mask[...,None]*a+(1-feather_mask[...,None])*b
        for key, value in {'original-a':load_rgb(case['source_a']['file']),
                           'original-b':load_rgb(case['source_b']['file']),
                           'aligned-a':raw_a,'prepared-a':a,'aligned-b':b,
                           'alignment-overlay':(a+b)/2,'mask':mask,'hard':hard,'feather':feather,
                           'blend-original':unadjusted,'blend':result['image'],
                           'masked-a':result['left'], 'masked-b':result['right']}.items():
            save(value,dest/(key+'.png'))
        variants = {}
        for mode in ('gray','a_color','b_color','both_color'):
            ac,bc = color_inputs(a,b,mode)
            if mode == 'both_color':
                image = result['image']
            else:
                image = multiresolution_blend(ac,bc,mask)['image']
            save(image,dest/('color-'+mode+'.png'))
            variants[mode] = image
        # Four-channel-independent combinations can also be reconstructed from
        # separately weighted source contributions, avoiding four stack archives.
        errors = {
            'source_a':float(np.max(np.abs(result['left_laplacian'].sum(0)-a))),
            'source_b':float(np.max(np.abs(result['right_laplacian'].sum(0)-b))),
            'contributions':float(np.max(np.abs(result['left']+result['right']-result['image'])))
        }
        for i in range(6):
            save(result['masks'][i],dest/f'mask-{i}.png')
        display_scales = {}
        for i in (0,2,4):
            bands = [result[key][i] for key in ('left_bands','right_bands','bands')]
            scale = max(float(np.abs(v).max()) for v in bands)
            display_scales[str(i)] = scale
            for key,value in zip(('a','b','combined'),bands):
                save(.5+value/(2*scale),dest/f'band-{i}-{key}.png')
        trials = []
        for fine in (0.,1.,3.):
            sigmas = (fine,4.,8.,16.,32.,64.) if fine == 3 else (fine,2.,4.,8.,16.,32.)
            image = result['image'] if fine == 1 else multiresolution_blend(a,b,mask,mask_sigmas=sigmas)['image']
            save(image,dest/f'trial-{int(fine)}.png')
            trials.append({'mask_sigmas':sigmas,'file':f'trial-{int(fine)}.png'})
        # Lossless float64 evidence stores independent ingredients; the weighted
        # bands and Gaussian stacks are regenerated deterministically from these.
        np.savez_compressed(dest/'arrays.npz', a=a,b=b,mask=mask,masks=result['masks'],
                            la=result['left_laplacian'],lb=result['right_laplacian'],image=result['image'],
                            left=result['left'],right=result['right'],hard=hard,feather=feather,
                            unaltered_color_a=raw_a, matrix_a=case['source_a']['matrix'],
                            matrix_b=case['source_b']['matrix'], **{'color_'+k:v for k,v in variants.items()})
        record = {key:value for key,value in case.items() if key not in ('a','b')}
        record.update(a=case['source_a']['file'], b=case['source_b']['file'],
                      size_wh=[a.shape[1],a.shape[0]], chroma_shift_ab=shift,
                      chroma_roi='center (256,256), radius 150; unadjusted A min RGB > .12' if shift else None,
                      mask_area_fraction=float(mask.mean()), errors=errors, trials=trials,
                      signed_row_scales=display_scales,
                      raw_range=[float(result['image'].min()),float(result['image'].max())],
                      clip_fraction=float(np.mean((result['image']<0)|(result['image']>1))),
                      archive_mb=round((dest/'arrays.npz').stat().st_size/1024**2,1))
        metrics['cases'].append(record)
        print(case['id'],record['size_wh'],errors,flush=True)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
