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
<p class="project-deck">I find edges by measuring brightness changes in two directions. I then try different thresholds to keep strong edges and remove weaker texture.</p></section>
<section id="derivatives"><h2>01 / From intensity to gradients</h2><div class="four-grid">{main_figures}</div>
<p>I use the {metrics['size_wh'][0]} × {metrics['size_wh'][1]} grayscale image at its original size. Pixel values are float64 from 0 to 1. I do not blur or adjust the image first. I apply the difference filters with SciPy, which is allowed in Part 1.2.</p>
<p class="formula">I<sub>x</sub> = I * [1, −1] &nbsp; · &nbsp; I<sub>y</sub> = I * [1, −1]<sup>T</sup><br>M = √(I<sub>x</sub>² + I<sub>y</sub>²)</p>
<p>Away from the borders, I<sub>x</sub>[y,x] = I[y,x] − I[y,x−1] and I<sub>y</sub>[y,x] = I[y,x] − I[y−1,x]. The first finds vertical edges; the second finds horizontal edges. The magnitude combines both directions and is always nonnegative.</p>
<p>Both derivative pictures use the same scale, ±{metrics['display']['signed_scale']:.6f}, with gray for zero. The magnitude picture uses a fixed 0 to 1 display range. I apply the threshold to the saved float values, not to the displayed PNG.</p></section>
<section id="thresholds"><h2>02 / Choosing the edge threshold</h2>
<p class="formula">Edge[y,x] = M[y,x] &gt; {threshold:.2f}</p>
<div class="comparison-grid"><div>{figure('original.png', 'Original input')}</div><div>{figure('edges-selected.png', f'Selected edge map · T = {threshold:.2f}', f'{selected['edge_pixels']:,} edge pixels · {selected['edge_fraction']:.2%} of the image')}</div></div>
<p>{escape(observation.strip())}</p>
<h3>The threshold sweep</h3><div class="triple">{sweep}</div>
<div class="table-scroll"><table><thead><tr><th>Threshold</th><th>Edge pixels</th><th>Image fraction</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>The percentages show how many pixels are marked as edges. They do not measure accuracy because I do not have labeled edges to compare against. A lower threshold keeps more detail and grass texture. A higher threshold removes clutter but also breaks real outlines. I choose the threshold by looking at this image.</p></section>
<section id="method"><h2>03 / Method, boundaries and verification</h2>
<p>I use mode='same' to keep the image size and boundary='symm' to reflect pixels at the border. With these filters, the leftmost x derivative and topmost y derivative are zero. This avoids the false outer edges caused by zero padding in Part 1.1.</p>
<pre><code>DX = np.array([[1., -1.]])
DY = DX.T

{code}</code></pre>
<p>Six unit tests check the two directions, signed differences, constant-image borders, gradient magnitude, the strict threshold rule and invalid inputs. I also check that the saved edge maps match the saved magnitude values.</p>
<h3>Image source</h3><p>I use the camera image from the <a href="{escape(source['image_url'])}">official scikit-image repository, v0.25.2</a>. The <a href="{escape(source['documentation_url'])}">documentation</a> credits Lav Varshney and lists it as CC0. This is the newer 512 × 512 image. The original ResearchGate request used an older 256 × 256 image, but its download was blocked. The official replacement was approved.</p>
<h3>What I learned</h3><p>I learned that difference filters find texture as well as object outlines. Using both directions helps find more edges, but a threshold cannot tell grass texture from an important edge. In Part 1.3, I try blurring the image first. Looking at the camera and tripod helped me judge which useful edges were being lost. I would not reuse the same threshold on every image without checking the result.</p>
<p><a href="edges.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_edges.py">Unit tests</a> · <a href="results/metrics.json">Parameters and measurements</a> · <a href="results/gradient-arrays.npz">Raw arrays</a> · <a href="input/source.json">Source record</a></p>
<p class="versions">Python {metrics['versions']['python']} · NumPy {metrics['versions']['numpy']} · SciPy {metrics['versions']['scipy']} · Pillow {metrics['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 1.2 · Finite Difference Operator</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
