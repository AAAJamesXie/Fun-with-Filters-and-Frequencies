"""Build the English stacks report and twelve-panel Figure 3.42 adaptation."""
from html import escape
import inspect
import json
from pathlib import Path
import stacks

HERE = Path(__file__).resolve().parent


def figure(filename, title, caption=''):
    return (f'<figure><a href="results/{escape(filename)}"><img src="results/{escape(filename)}" '
            f'alt="{escape(title)}" loading="lazy"></a><figcaption>{escape(title)}'
            f'<span>{escape(caption)}</span></figcaption></figure>')


def build_report():
    m = json.loads((HERE / 'results/metrics.json').read_text(encoding='utf-8'))
    observation = (HERE / 'observations.txt').read_text(encoding='utf-8')
    panel_names = {'left': 'Masked apple contribution', 'right': 'Masked orange contribution',
                   'combined': 'Combined band', 'image': 'Final reconstructed oraple'}
    panels = ''
    for panel in m['figure_panels']:
        level = panel['level']
        label = f'({panel["letter"]}) ' + panel_names[panel['column']]
        caption = f'Level {level} · signed display' if isinstance(level, int) else 'Sum of all six raw levels · ordinary RGB display'
        panels += figure(panel['file'], label, caption)
    stack_sections = ''
    for key, label in [('apple', 'Apple'), ('orange', 'Orange'), ('oraple', 'Final oraple')]:
        stack_sections += f'<h3>{label}: Gaussian stack</h3><div class="six-grid">'
        for i, sigma in enumerate(m['image_sigmas']):
            stack_sections += figure(f'{key}-gaussian-{i}.png', f'G{i} · σ = {sigma:g}', 'Original' if i == 0 else 'Nominal cumulative blur')
        stack_sections += f'</div><h3>{label}: Laplacian stack</h3><div class="six-grid">'
        for i in range(m['levels']):
            stack_sections += figure(f'{key}-laplacian-{i}.png', f'L{i}', 'Coarse Gaussian residual' if i == m['levels'] - 1 else f'G{i} − G{i+1} · signed band')
        stack_sections += '</div>'
    mask_images = ''.join(figure(f'mask-{i}.png', f'M{i} · σ = {sigma:g}', 'White = apple; black = orange')
                          for i, sigma in enumerate(m['mask_sigmas']))
    errors = ''.join(f'<tr><th>{name}</th><td>{m["errors"][key]:.3e}</td></tr>' for key, name in [
        ('apple', 'Apple reconstruction'), ('orange', 'Orange reconstruction'),
        ('oraple_reconstruction', 'Final oraple reconstruction'), ('left_plus_right', 'Left + right contribution'),
        ('mask_complement', 'Complementary mask sum minus one')])
    code = escape(inspect.getsource(stacks.gaussian_stack) + '\n' + inspect.getsource(stacks.laplacian_stack))
    blend_code = escape(inspect.getsource(stacks.blend_stacks))
    size = m['inputs']['apple']['size_wh']
    archive_mb = (HERE / 'results/stack-arrays.npz').stat().st_size / 1e6
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part 2.3 · Gaussian and Laplacian Stacks</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="page.css"></head>
<body><main class="shell"><header class="site-header"><a class="brand" href="../index.html">Fun with Filters<br>and Frequencies!</a>
<nav class="header-nav"><a href="#stacks">Full-resolution stacks <span>01</span></a><a href="#mask">Scale-dependent mask <span>02</span></a><a href="#figure">Figure 3.42 <span>03</span></a><a href="#verification">Reconstruction checks <span>04</span></a></nav></header>
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p><h1>PART 2.3:<br>GAUSSIAN &amp;<br>LAPLACIAN STACKS</h1>
<p class="project-deck">Decompose an image into spatial frequency bands without reducing its resolution. Recombine those bands to inspect how an apple and an orange form an oraple.</p></section>
<section><h2>The supplied images</h2><div class="pair">{figure('original-apple.png', 'Apple input')}{figure('original-orange.png', 'Orange input')}</div>
<p>Both supplied RGB images are {size[0]} × {size[1]} pixels. They are converted to float64 [0, 1] and processed at that resolution, without resizing or registration. Existing grain and small geometric differences remain. Every level of every image stack retains shape {size[1]} × {size[0]} × 3; the mask layers retain {size[1]} × {size[0]}.</p></section>
<section id="stacks"><h2>01 / Gaussian and Laplacian stacks</h2>
<p>The Gaussian stack contains six progressively blurred images with nominal cumulative σ = 0, 2, 4, 8, 16, 32 pixels. G0 is the original. To move from a scale σ previous to σ target, I apply a Gaussian with incremental σ = √(σ target² − σ previous²), using Gaussian variance addition. Finite sampled kernels approximate this schedule. Kernels are normalized OpenCV Gaussian vectors, truncated at radius ceil(4σ incremental), and applied separably along x and y with symmetric boundaries.</p>
<p class="formula">L<sub>i</sub> = G<sub>i</sub> − G<sub>i+1</sub>, i = 0,…,4<br>L<sub>5</sub> = G<sub>5</sub><br>I = L<sub>0</sub> + L<sub>1</sub> + … + L<sub>5</sub></p>
<p>No downsampling or upsampling is used. No built-in pyramid function is called. The final coarse residual is essential: dropping it would remove the image's broad intensity/color structure and prevent reconstruction. Adjacent differences keep positive and negative coefficients.</p>
<p>For display, signed bands use middle gray for zero, with a shared scale across apple, orange and final-oraple images at the same level. Scales vary between levels to make their different frequency content visible. The last residual is shown as an ordinary RGB image. Display PNGs are clipped and quantized; reconstruction uses raw float64 bands.</p>
{stack_sections}<p>The final oraple is also decomposed into its own Gaussian and Laplacian stacks. Those analysis bands are not claimed to equal the mask-weighted bands used to construct it: spatially varying mask multiplication does not generally commute with filtering.</p>
<details><summary>Stack implementation</summary><pre><code>{code}</code></pre></details></section>
<section id="mask"><h2>02 / A different transition width at each scale</h2>
{figure('mask-binary.png', 'Binary region mask', f'Apple on the left, orange on the right; split at column {m["split_column"]}.')}
<div class="six-grid">{mask_images}</div>
<p>The binary region mask is one on the left and zero on the right. Its Gaussian stack uses nominal σ = 1, 2, 4, 8, 16, 32. The finest mask is deliberately smoothed by σ = 1 instead of making a hard cut even in the finest band. Coarser bands use wider transitions. Weights are restricted to [0, 1] only to remove floating-point roundoff; the orange weight is computed as exactly one minus the apple weight.</p>
<p class="formula">A<sub>i</sub> = M<sub>i</sub>L<sub>apple,i</sub><br>B<sub>i</sub> = (1 − M<sub>i</sub>)L<sub>orange,i</sub><br>C<sub>i</sub> = A<sub>i</sub> + B<sub>i</sub> &nbsp; · &nbsp; Oraple = Σ C<sub>i</sub></p>
<p>The same scalar spatial weights are applied independently to all RGB channels. The contribution weights already form a weighted average, so I do not divide the combined bands by two again. Since these are full-resolution stacks, reconstruction is direct addition; the expansion step used for subsampled pyramids is unnecessary.</p>
<details><summary>Mask-weighted reconstruction</summary><pre><code>{blend_code}</code></pre></details></section>
<section id="figure"><h2>03 / Figure 3.42, (a) through (l)</h2>
<p>This is a stack-based reproduction of the structure of the assignment's Figure 3.42, not a pixel-identical reproduction of the textbook's subsampled pyramid. Rows one through three show levels 0, 2 and 4. Columns are the masked apple, masked orange and their sum. The bottom row sums all six raw levels, including the coarse residual, to show each source's total contribution and the final image.</p>
<div class="figure-grid">{panels}</div>
<p>Within each of the first three rows, all three panels share one signed display scale, computed from that row's maximum absolute coefficient. A masked-out region therefore appears middle gray in band images, not black. The bottom row uses ordinary RGB display. Summation happens before any clipping or display normalization. <a href="results/figure-3-42.png">Open the complete twelve-panel figure</a>.</p>
<h3>What changes at the seam?</h3><div class="triple">{figure('hard-join.png', 'Hard left/right cut')}{figure('single-feather.png', 'Single-scale feather', 'One σ = 16 mask for the entire RGB image')}{figure('oraple.png', 'Multiresolution stack blend')}</div>
<p>{escape(observation.strip())}</p></section>
<section id="verification"><h2>04 / Reconstruction checks</h2>
<table><thead><tr><th>Check</th><th>Maximum absolute error</th></tr></thead><tbody>{errors}</tbody></table>
<p>The Gaussian and Laplacian image stacks each have shape ({m['gaussian_shape'][0]}, {m['gaussian_shape'][1]}, {m['gaussian_shape'][2]}, {m['gaussian_shape'][3]}). The mask stack has shape ({m['mask_shape'][0]}, {m['mask_shape'][1]}, {m['mask_shape'][2]}). Reconstructed apple, orange and oraple match their inputs to floating-point precision. The left and right source contributions also sum to the complete blend.</p>
<p>Raw combined RGB values range from {m['raw_result_range'][0]:.6f} to {m['raw_result_range'][1]:.15f}. Mask-weighted frequency bands can produce values outside [0, 1], even when input photographs are in range. {m['display_clip_fraction']:.2%} of scalar RGB samples fall outside that interval before display, including tiny upper-bound rounding deviations. All such values are retained in raw arrays; only final PNG display clips them.</p>
<p>Eight real-array unit tests cover unchanged level dimensions, odd-size RGB reconstruction, constant-image residuals, progressive impulse smoothing, all-zero/all-one masks, identical-image invariance, signed bands and invalid scales/weights. The full experiment additionally checks source reconstruction and left-plus-right reconstruction on the supplied images.</p>
<h3>Sources and reproduction</h3><p>Inputs are the course-provided Burt apple and orange images, retained unchanged. Method reference: Peter J. Burt and Edward H. Adelson, <em>A Multiresolution Spline With Application to Image Mosaics</em>, ACM Transactions on Graphics 2(4), 217–236, 1983; the region-mask construction is described on printed page 230 of the <a href="../references/burt-adelson-1983.pdf">supplied paper</a>. The twelve-panel layout follows Figure 3.42 reproduced in the <a href="../references/assignment-2.pdf">assignment handout</a>.</p>
<p><a href="stacks.py">Stack algorithms</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_stacks.py">Unit tests</a> · <a href="results/metrics.json">Parameters and errors</a> · <a href="results/stack-arrays.npz">Raw float64 arrays ({archive_mb:.0f} MB; optional download)</a> · <a href="input/source.json">Input source record</a></p>
<p>The webpage loads only display images. The optional raw archive is large because it preserves full-resolution RGB Gaussian/Laplacian stacks, masks and weighted bands for numerical inspection.</p>
<h3>What I learned</h3><p>The stack's signed bands separate fine detail from broad appearance while retaining exact additive reconstruction. A useful multiresolution blend needs both the final coarse residual and a mask whose transition width changes with frequency. Correct reconstruction guarantees consistent arithmetic, but does not guarantee perfect geometric alignment or an invisible seam.</p>
<p class="versions">Python {m['versions']['python']} · NumPy {m['versions']['numpy']} · SciPy {m['versions']['scipy']} · OpenCV {m['versions']['opencv']} · Pillow {m['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 2.3 · Gaussian and Laplacian Stacks</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
