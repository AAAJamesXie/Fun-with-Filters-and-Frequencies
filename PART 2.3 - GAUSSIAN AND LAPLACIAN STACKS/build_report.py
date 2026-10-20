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
<p class="project-deck">I split an image into layers of fine detail and broad shapes. Every layer keeps the same size. I then combine apple and orange layers to make an oraple.</p></section>
<section><h2>The supplied images</h2><div class="pair">{figure('original-apple.png', 'Apple input')}{figure('original-orange.png', 'Orange input')}</div>
<p>Both course images are {size[0]} × {size[1]} pixels. I convert them to float64 values from 0 to 1 without resizing or aligning them. The original grain and small shape differences remain. Each image layer is {size[1]} × {size[0]} × 3, and each mask layer is {size[1]} × {size[0]}.</p></section>
<section id="stacks"><h2>01 / Gaussian and Laplacian stacks</h2>
<p>The Gaussian stack has six blur levels: σ = 0, 2, 4, 8, 16, 32 pixels. G0 is the original. To go from one level to the next, I use an extra blur of σ = √(σ target² − σ previous²). This works because Gaussian variances add. The finite filters only approximate the target scales. I make normalized OpenCV Gaussian vectors with radius ceil(4σ extra), apply them along x and y, and reflect the borders.</p>
<p class="formula">L<sub>i</sub> = G<sub>i</sub> − G<sub>i+1</sub>, i = 0,…,4<br>L<sub>5</sub> = G<sub>5</sub><br>I = L<sub>0</sub> + L<sub>1</sub> + … + L<sub>5</sub></p>
<p>I never shrink or enlarge the layers and do not call a built-in pyramid function. Each Laplacian layer is the difference between two blur levels and can contain negative values. The final layer keeps the remaining broad shapes and colors. Without it, the layers cannot add back to the original.</p>
<p>In the detail layers, gray means zero. At each level, apple, orange and oraple use the same display scale. Different levels use different scales so their details are visible. The last layer uses normal RGB display. I use the raw float64 values for reconstruction, not the clipped PNGs.</p>
{stack_sections}<p>I also make stacks from the final oraple. These are different from the weighted layers used to build it. Applying a mask before filtering is generally different from applying it afterward.</p>
<details><summary>Stack implementation</summary><pre><code>{code}</code></pre></details></section>
<section id="mask"><h2>02 / A different transition width at each scale</h2>
{figure('mask-binary.png', 'Binary region mask', f'Apple on the left, orange on the right; split at column {m["split_column"]}.')}
<div class="six-grid">{mask_images}</div>
<p>The starting mask is white (1) on the left and black (0) on the right. I blur it at σ = 1, 2, 4, 8, 16, 32. Even the finest mask has a small blur of σ = 1; coarser masks have wider transitions. I limit tiny rounding errors to 0–1 and set the orange weight to exactly one minus the apple weight.</p>
<p class="formula">A<sub>i</sub> = M<sub>i</sub>L<sub>apple,i</sub><br>B<sub>i</sub> = (1 − M<sub>i</sub>)L<sub>orange,i</sub><br>C<sub>i</sub> = A<sub>i</sub> + B<sub>i</sub> &nbsp; · &nbsp; Oraple = Σ C<sub>i</sub></p>
<p>Each RGB channel uses the same mask weights. The two weights already add to one, so I do not divide by two again. All layers have the same size, so I reconstruct the image by adding them directly.</p>
<details><summary>Mask-weighted reconstruction</summary><pre><code>{blend_code}</code></pre></details></section>
<section id="figure"><h2>03 / Figure 3.42, (a) through (l)</h2>
<p>I follow the layout of Figure 3.42 using full-size stacks. It is not an exact copy of the textbook pyramid result. The first three rows show levels 0, 2 and 4. Each row shows the apple part, orange part and their sum. The last row adds all six levels, including the last broad layer, to show each source and the final blend.</p>
<div class="figure-grid">{panels}</div>
<p>Each of the first three rows uses one display scale, based on its largest absolute value. A zero area appears gray rather than black. The bottom row uses normal RGB display. I add the raw values before clipping. <a href="results/figure-3-42.png">Open the complete twelve-panel figure</a>.</p>
<h3>What changes at the seam?</h3><div class="triple">{figure('hard-join.png', 'Hard left/right cut')}{figure('single-feather.png', 'Single-scale feather', 'One σ = 16 mask for the entire RGB image')}{figure('oraple.png', 'Multiresolution stack blend')}</div>
<p>{escape(observation.strip())}</p></section>
<section id="verification"><h2>04 / Reconstruction checks</h2>
<table><thead><tr><th>Check</th><th>Maximum absolute error</th></tr></thead><tbody>{errors}</tbody></table>
<p>Both image stacks have shape ({m['gaussian_shape'][0]}, {m['gaussian_shape'][1]}, {m['gaussian_shape'][2]}, {m['gaussian_shape'][3]}). The mask stack has shape ({m['mask_shape'][0]}, {m['mask_shape'][1]}, {m['mask_shape'][2]}). Adding each image stack recovers its input apart from rounding. The two source contributions also add up to the final blend.</p>
<p>The raw blend ranges from {m['raw_result_range'][0]:.6f} to {m['raw_result_range'][1]:.15f}. Combining detail layers can produce RGB values outside 0–1. Here, {m['display_clip_fraction']:.2%} of individual channel values are outside the range, including tiny rounding errors. I keep these in the raw files and clip only the display images.</p>
<p>Eight unit tests check layer sizes, reconstruction, constant images, increasing blur, masks that select one source, identical inputs, negative detail values and invalid settings. I also check reconstruction on the supplied apple and orange.</p>
<h3>Sources and reproduction</h3><p>I use the course apple and orange files without changing the originals. The method comes from Burt and Adelson (1983), <em>A Multiresolution Spline With Application to Image Mosaics</em>. The mask method is on printed page 230 of the <a href="../references/burt-adelson-1983.pdf">paper</a>. The twelve-panel layout follows Figure 3.42 in the <a href="../references/assignment-2.pdf">assignment</a>.</p>
<p><a href="stacks.py">Stack algorithms</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_stacks.py">Unit tests</a> · <a href="results/metrics.json">Parameters and errors</a> · <a href="results/stack-arrays.npz">Raw float64 arrays ({archive_mb:.0f} MB; optional download)</a> · <a href="input/source.json">Input source record</a></p>
<p>This page loads only the display images. The optional archive is large because it keeps full-size RGB stacks, masks and weighted layers.</p>
<h3>What I learned</h3><p>I learned that the layers separate fine detail from broad colors and still add back to the original. A good blend needs the final broad layer and different mask widths for different levels. A small reconstruction error confirms the calculation, but does not mean the seam is invisible.</p>
<p class="versions">Python {m['versions']['python']} · NumPy {m['versions']['numpy']} · SciPy {m['versions']['scipy']} · OpenCV {m['versions']['opencv']} · Pillow {m['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 2.3 · Gaussian and Laplacian Stacks</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
