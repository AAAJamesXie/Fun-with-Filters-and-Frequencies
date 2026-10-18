"""Build the English Part 1.2 webpage using saved results."""
from html import escape
import inspect
import json
from pathlib import Path

import edges

HERE = Path(__file__).resolve().parent


def figure(filename, title, description=''):
    return (f'<figure><a href="results/{escape(filename)}"><img src="results/{escape(filename)}" '
            f'alt="{escape(title)}" loading="lazy"></a><figcaption>{escape(title)}'
            f'<span>{escape(description)}</span></figcaption></figure>')


def build_report():
    metrics = json.loads((HERE / 'results/metrics.json').read_text(encoding='utf-8'))
    source = json.loads((HERE / 'input/source.json').read_text(encoding='utf-8'))
    observation_path = HERE / 'observations.txt'
    observation = observation_path.read_text(encoding='utf-8') if observation_path.exists() else 'Threshold selection is pending visual review.'
    threshold = metrics['selected_threshold']
    selected = next(row for row in metrics['threshold_sweep'] if row['threshold'] == threshold)
    main_figures = figure('original.png', 'Original cameraman', 'Grayscale input, unchanged resolution')
    main_figures += figure('dx.png', 'Horizontal derivative', 'Dx = [1, -1]; emphasizes vertical boundaries')
    main_figures += figure('dy.png', 'Vertical derivative', 'Dy = [1, -1] transpose; emphasizes horizontal boundaries')
    main_figures += figure('magnitude.png', 'Gradient magnitude', 'sqrt(Ix² + Iy²)')
    sweep = ''.join(figure(row['file'], f'T = {row["threshold"]:.2f}' + (' · selected' if row['threshold'] == threshold else ''),
                           f'{row["edge_pixels"]:,} edge pixels · {row["edge_fraction"]:.2%} of image')
                    for row in metrics['threshold_sweep'])
    rows = ''.join(f'<tr><th>{row["threshold"]:.2f}</th><td>{row["edge_pixels"]:,}</td>'
                   f'<td>{row["edge_fraction"]:.2%}</td></tr>' for row in metrics['threshold_sweep'])
    code = escape(inspect.getsource(edges.gradients) + '\n\n' + inspect.getsource(edges.threshold_edges))
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Part 1.2 · Finite Difference Operator</title>
<link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="page.css"></head>
<body><main class="shell"><header class="site-header"><a class="brand" href="../index.html">Fun with Filters<br>and Frequencies!</a>
<nav class="header-nav"><a href="#derivatives">Derivatives <span>01</span></a><a href="#thresholds">Threshold choice <span>02</span></a><a href="#method">Method &amp; code <span>03</span></a></nav></header>
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p>
<h1>PART 1.2:<br>FINITE DIFFERENCE<br>OPERATOR</h1>
<p class="project-deck">Directional intensity changes become an edge map. A single threshold trades fine detail against unwanted texture.</p></section>
<section id="derivatives"><h2>01 / From intensity to gradients</h2><div class="four-grid">{main_figures}</div>
<p>The {metrics['size_wh'][0]} × {metrics['size_wh'][1]} grayscale image is converted from uint8 to float64 in [0, 1]. No resizing, smoothing, denoising, sharpening or histogram adjustment is applied. The finite difference filters are convolved directly with the input using SciPy, as permitted in Part 1.2.</p>
<p class="formula">I<sub>x</sub> = I * [1, −1] &nbsp; · &nbsp; I<sub>y</sub> = I * [1, −1]<sup>T</sup><br>M = √(I<sub>x</sub>² + I<sub>y</sub>²)</p>
<p>In the interior, I<sub>x</sub>[y,x] = I[y,x] − I[y,x−1], while I<sub>y</sub>[y,x] = I[y,x] − I[y−1,x]. A vertical boundary changes intensity across x, so it appears in I<sub>x</sub>; a horizontal boundary changes intensity across y, so it appears in I<sub>y</sub>. The magnitude combines both directions without depending on the sign of the change.</p>
<p>The two signed derivative displays share a scale of ±{metrics['display']['signed_scale']:.6f}, with zero shown as middle gray. The magnitude is shown on a fixed [0, 1] display scale; raw values are preserved separately. Binarization uses raw magnitudes, not a contrast-normalized PNG.</p></section>
<section id="thresholds"><h2>02 / Choosing the edge threshold</h2>
<p class="formula">Edge[y,x] = M[y,x] &gt; {threshold:.2f}</p>
<div class="comparison-grid"><div>{figure('original.png', 'Original input')}</div><div>{figure('edges-selected.png', f'Selected edge map · T = {threshold:.2f}', f'{selected['edge_pixels']:,} edge pixels · {selected['edge_fraction']:.2%} of the image')}</div></div>
<p>{escape(observation.strip())}</p>
<h3>The threshold sweep</h3><div class="triple">{sweep}</div>
<div class="table-scroll"><table><thead><tr><th>Threshold</th><th>Edge pixels</th><th>Image fraction</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>These percentages measure edge density, not accuracy: no ground-truth edge labels are available. Increasing the threshold can only remove edge pixels. Lower thresholds retain weak detail and texture; higher thresholds isolate stronger transitions while losing faint or disconnected parts of real contours. This is a qualitative choice for this image, not a universally optimal threshold.</p></section>
<section id="method"><h2>03 / Method, boundaries and verification</h2>
<p>The convolution uses mode='same' and boundary='symm', so image size is preserved and boundary intensities are extended symmetrically. For these two-sample kernels, the leftmost x derivative and topmost y derivative are zero. Unlike the zero fill demonstrated in Part 1.1, this avoids a false outer contour against an assumed black background.</p>
<pre><code>DX = np.array([[1., -1.]])
DY = DX.T

{code}</code></pre>
<p>Six real-array unit tests verify horizontal and vertical direction, signed subtraction from uint8 input, constant-image boundaries, a 3–4–5 gradient magnitude, strict threshold comparison, and rejection of invalid inputs. The experiment also verifies that saved edge masks match direct thresholding of the saved floating-point magnitudes.</p>
<h3>Image source</h3><p>The image comes from the <a href="{escape(source['image_url'])}">scikit-image official repository, version v0.25.2</a>. The <a href="{escape(source['documentation_url'])}">official camera documentation</a> credits photographer Lav Varshney and identifies the image as CC0. This is the modern 512 × 512 replacement camera image, not the legacy 256 × 256 figure on the initially requested ResearchGate page. The download from that page was restricted; the official alternative was approved before use.</p>
<h3>What I learned</h3><p>Finite differences measure intensity changes, so they respond to texture as well as object boundaries. Combining both directions captures more contour orientations, but a magnitude threshold alone cannot distinguish texture from meaningful edges. Smoothing before differentiation is the next step to investigate in Part 1.3.</p>
<p><a href="edges.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_edges.py">Unit tests</a> · <a href="results/metrics.json">Parameters and measurements</a> · <a href="results/gradient-arrays.npz">Raw arrays</a> · <a href="input/source.json">Source record</a></p>
<p class="versions">Python {metrics['versions']['python']} · NumPy {metrics['versions']['numpy']} · SciPy {metrics['versions']['scipy']} · Pillow {metrics['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 1.2 · Finite Difference Operator</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
