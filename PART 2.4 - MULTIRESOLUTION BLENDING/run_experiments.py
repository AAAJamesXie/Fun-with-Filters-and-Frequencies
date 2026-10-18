"""Prepare authentic photographs, blend three custom pairs, save reproducible evidence."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from blending import (multiresolution_blend, color_inputs, polygon_mask, step_mask,
                      gaussian_stack, IMAGE_SIGMAS, MASK_SIGMAS)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
HYBRID = ROOT / 'PART 2.2 - HYBRID IMAGES'
sys.path.insert(0, str(HYBRID))
from hybrid import similarity_matrix, warp_image, largest_rectangle

CASES = [
    dict(id='portraits', title='Two presidents, one portrait', a='obama.jpg', b='trump.jpg',
         points_a=[[230,109],[281,109]], points_b=[[217,231],[300,231]],
         target=[[180,210],[300,210]], canvas=[480,560], mask='vertical', vertices=None),
    dict(id='cat-owl', title='The owl behind the cat', a='owl.jpg', b='chelsea.png',
         points_a=[[190,126],[330,126]], points_b=[[193,126],[358,155]],
         target=[[150,160],[330,160]], canvas=[480,420], mask='irregular',
         vertices=[[243,80],[304,78],[363,115],[390,174],[365,232],[304,288],[250,252],[228,207],[251,167]]),
    dict(id='selfie-tiger', title='A glimpse of the tiger within', a='tiger-front.jpg', b='selfie.jpg',
         points_a=[[190,218],[322,225]], points_b=[[244,258],[315,259]],
         target=[[180,190],[300,190]], canvas=[480,500], mask='irregular',
         vertices=[[247,118],[297,123],[338,155],[352,215],[336,269],[304,297],[266,269],[242,235],[252,190]])
]


def save(array, path):
    Image.fromarray(np.round(np.clip(array, 0, 1)*255).astype('uint8')).save(path)


def load(name):
    with Image.open(HERE/'input'/name) as original:
        im = ImageOps.exif_transpose(original).convert('RGB')
        size = list(im.size)
        im = im.resize((512, round(im.height*512/im.width)), Image.Resampling.LANCZOS)
    return np.asarray(im, float)/255, size


def main():
    inp = HERE/'input'; inp.mkdir(exist_ok=True)
    out = HERE/'results'; out.mkdir(exist_ok=True)
    source_meta = json.loads((HYBRID/'input/sources.json').read_text(encoding='utf-8'))
    used = {case[role] for case in CASES for role in ('a','b')}
    sources = []
    for name in sorted(used):
        source = (ROOT/'PART 1.1 - CONVOLUTIONS FROM SCRATCH!'/ 'input'/name) if name == 'selfie.jpg' else HYBRID/'input'/name
        shutil.copy2(source, inp/name)
        record = next((dict(r) for r in source_meta['images'] if r['file'] == name),
                      {'file':name, 'title':'User-provided selfie', 'author':'James Xie', 'license':'Personal photograph; no open-license grant'})
        record.pop('status', None)
        record.update(sha256=hashlib.sha256(source.read_bytes()).hexdigest(), original_path=str(source))
        sources.append(record)
    (inp/'sources.json').write_text(json.dumps({'images':sources,
        'modifications':'EXIF correction, width-512 preparation, eye-based similarity alignment, common-valid crop, polygon masking and spatial-frequency blending. No generated imagery.',
        'derived_licenses':{'cat-owl':'CC BY-SA 4.0; Rhododendrites and Stefan van der Walt; adapted',
                            'selfie-tiger':'Adapted from Steve Wilson tiger (CC BY 2.0) and James Xie personal selfie; no blanket open-license claim for the selfie.',
                            'portraits':'Public-domain source photographs; educational composite, not a real portrait.'}}, indent=2), encoding='utf-8')
    metrics = {'image_sigmas':IMAGE_SIGMAS, 'mask_sigmas':MASK_SIGMAS, 'favorite':'cat-owl',
               'convention':'Mask 1 selects A; mask 0 selects B. Encoded RGB, no gamma linearization. Float64 bands; only display exports clipped.',
               'cases':[]}
    for case in CASES:
        dest = out/case['id']; dest.mkdir(exist_ok=True)
        a0, size_a = load(case['a']); b0, size_b = load(case['b'])
        ma, mb = [similarity_matrix(case['points_'+role], case['target']) for role in ('a','b')]
        aw, av = warp_image(a0, ma, tuple(case['canvas']))
        bw, bv = warp_image(b0, mb, tuple(case['canvas']))
        x0,y0,x1,y1 = largest_rectangle(av & bv)
        assert (av & bv)[y0:y1,x0:x1].all()
        a,b = aw[y0:y1,x0:x1], bw[y0:y1,x0:x1]
        vertices = None if case['vertices'] is None else np.asarray(case['vertices'])-[x0,y0]
        mask = step_mask(a.shape[:2]) if vertices is None else polygon_mask(a.shape[:2], vertices)
        assert mask.min() == 0 and mask.max() == 1
        result = multiresolution_blend(a,b,mask)
        hard = mask[...,None]*a+(1-mask[...,None])*b
        feather_mask = gaussian_stack(mask, (0.,16.))[-1]
        feather = feather_mask[...,None]*a+(1-feather_mask[...,None])*b
        for key, value in {'original-a':a0,'original-b':b0, 'aligned-a':a,'aligned-b':b,
                           'alignment-overlay':(a+b)/2,'mask':mask,'hard':hard,'feather':feather,
                           'blend':result['image'],'masked-a':result['left'], 'masked-b':result['right']}.items():
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
        for i in (0,2,4):
            bands = [result[key][i] for key in ('left_bands','right_bands','bands')]
            scale = max(float(np.abs(v).max()) for v in bands)
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
                            matrix_a=ma,matrix_b=mb, **{'color_'+k:v for k,v in variants.items()})
        eye_errors = [float(np.max(np.abs(np.c_[case['points_'+role],np.ones(2)]@mat.T-case['target']))) for role,mat in [('a',ma),('b',mb)]]
        record = {**case,'crop_xyxy':[x0,y0,x1,y1],'size_wh':[a.shape[1],a.shape[0]],
                  'vertices_cropped': None if vertices is None else vertices.tolist(),
                  'original_sizes':[size_a,size_b], 'alignment_eye_errors':eye_errors,
                  'mask_area_fraction':float(mask.mean()),'errors':errors,'trials':trials,
                  'raw_range':[float(result['image'].min()),float(result['image'].max())],
                  'clip_fraction':float(np.mean((result['image']<0)|(result['image']>1))),
                  'archive_mb':round((dest/'arrays.npz').stat().st_size/1024**2,1)}
        metrics['cases'].append(record)
        print(case['id'],record['size_wh'],errors,flush=True)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
