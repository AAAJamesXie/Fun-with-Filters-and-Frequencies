"""Generate the Part 1.3 and mandatory Bells & Whistles English webpage."""
from html import escape
import inspect
import json
from pathlib import Path

import dog

HERE = Path(__file__).resolve().parent


def figure(filename, title, caption=''):
    return (f'<figure><a href="results/{escape(filename)}"><img src="results/{escape(filename)}" '
            f'alt="{escape(title)}" loading="lazy"></a><figcaption>{escape(title)}'
            f'<span>{escape(caption)}</span></figcaption></figure>')


def build_report():
    m = json.loads((HERE / 'results/metrics.json').read_text(encoding='utf-8'))
    observations = HERE / 'observations.txt'
    observation = observations.read_text(encoding='utf-8') if observations.exists() else 'Visual review pending.'
    sigma, threshold = m['sigma'], m['threshold']
    errors = ''.join(f'<tr><th>{axis.upper()}</th><td>{values["interior_max_abs"]:.3e}</td>'
                     f'<td>{values["full_max_abs"]:.3e}</td></tr>' for axis, values in m['route_errors'].items())
    kernels = ''.join(figure(f'kernel-{name}.png', title, caption) for name, title, caption in [
        ('gaussian', 'Gaussian G', f'{m["kernel_shape"][0]} × {m["kernel_shape"][1]}; normalized sum = 1'),
        ('kx', 'DoG in x', f'{m["dog_shapes"]["x"][0]} × {m["dog_shapes"]["x"][1]}; signed coefficients'),
        ('ky', 'DoG in y', f'{m["dog_shapes"]["y"][0]} × {m["dog_shapes"]["y"][1]}; signed coefficients')])
    raw = ''.join(figure(file, title) for file, title in [('original.png', 'Original input'),
        ('raw-magnitude.png', 'Direct finite difference magnitude'), ('raw-edges-020.png', 'Part 1.2 baseline · T = 0.20')])
    smooth = ''.join(figure(file, title) for file, title in [('blurred.png', f'Gaussian smoothing · σ = {sigma:g}'),
        ('sequential-magnitude.png', 'Smoothed gradient magnitude'), ('edges-selected.png', f'Smoothed edges · T = {threshold:.2f}')])
    route_panels = ''
    for axis in ('x', 'y'):
        route_panels += f'<h3>{axis.upper()} derivative</h3><div class="triple">' + ''.join([
            figure(f'sequential-{axis}.png', 'Smooth, then differentiate'),
            figure(f'direct-{axis}.png', 'One DoG convolution'),
            figure(f'route-difference-{axis}.png', 'Absolute difference, amplified', 'Each error image is scaled by its own maximum; not a raw intensity image.')]) + '</div>'
    sweep = ''.join(figure(row['file'], f'T = {row["threshold"]:.2f}' + (' · selected' if row['threshold'] == threshold else ''),
                           f'{row["edge_fraction"]:.2%} of pixels classified as edges') for row in m['threshold_sweep'])
    sigma_panels = ''
    for row in m['sigma_sweep']:
        sigma_panels += f'<h3>σ = {row["sigma"]:g} · {row["kernel_size"][0]} × {row["kernel_size"][1]} Gaussian</h3><div class="triple">'
        sigma_panels += figure(row['prefix'] + '-blurred.png', 'Blurred image')
        sigma_panels += figure(row['prefix'] + '-magnitude.png', 'Magnitude · shared display scale')
        sigma_panels += figure(row['prefix'] + '-edges.png', f'Edges · T = {threshold:.2f}', f'{row["edge_fraction"]:.2%} edge density') + '</div>'
    filter_code = escape(inspect.getsource(dog.gaussian_kernel) + '\n' + inspect.getsource(dog.dog_kernels) + '\n' + inspect.getsource(dog.filter_routes))
    angle_code = escape(inspect.getsource(dog.manual_orientation))
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part 1.3 · Derivative of Gaussian &amp; Gradient Orientation</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="page.css"></head>
<body><main class="shell"><header class="site-header"><a class="brand" href="../index.html">Fun with Filters<br>and Frequencies!</a>
<nav class="header-nav"><a href="#gaussian">Gaussian &amp; DoG <span>01</span></a><a href="#routes">Two routes <span>02</span></a><a href="#comparison">Edges &amp; parameters <span>03</span></a><a href="#orientation">Mandatory orientation <span>04</span></a></nav></header>
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p><h1>PART 1.3:<br>DERIVATIVE<br>OF GAUSSIAN</h1>
<p class="project-deck">Smoothing reduces texture responses before differentiation. A composed filter gives the same interior result in one convolution. Color reveals the direction of each gradient.</p>
<p class="badge">Includes Part 1 Bells &amp; Whistles · Mandatory gradient orientation</p></section>
<section id="gaussian"><h2>01 / Constructing the filters</h2><div class="triple">{kernels}</div>
<p>I use the same unresized 512 × 512 grayscale cameraman input as Part 1.2, normalized to float64 [0, 1]. For σ = {sigma:g}, the Gaussian radius is ceil(3σ), giving a {m['kernel_shape'][0]} × {m['kernel_shape'][1]} finite support. OpenCV creates a normalized one-dimensional Gaussian column and its outer product produces the two-dimensional kernel.</p>
<pre><code>g = cv2.getGaussianKernel(2 * ceil(3 * sigma) + 1, sigma, cv2.CV_64F)
G = g @ g.T
Kx = scipy.signal.convolve2d(G, [[1., -1.]], mode="full")
Ky = scipy.signal.convolve2d(G, [[1.], [-1.]], mode="full")</code></pre>
<p>Here DoG means <strong>derivative of Gaussian</strong>. The finite-difference kernels are the same as in Part 1.2. Full kernel convolution preserves every coefficient; the resulting x/y kernels have one additional column/row. Using a cropped kernel here would discard support and change the result. The Gaussian coefficients sum to {m['kernel_sums']['gaussian']:.16f}; the x/y DoG sums are {m['kernel_sums']['kx']:.3e} and {m['kernel_sums']['ky']:.3e}, so constant intensities have essentially zero derivative.</p>
<p>Kernel images use nearest-neighbor enlargement so every coefficient remains visible. Gaussian brightness is normalized by its maximum. The two DoG kernels share a signed display scale: middle gray is zero, lighter positive and darker negative.</p></section>
<section id="routes"><h2>02 / Two steps or one convolution?</h2>
<p class="formula">Route A: (I * G) * D<sub>x</sub> &nbsp; · &nbsp; Route B: I * (G * D<sub>x</sub>)<br>The same construction applies to D<sub>y</sub>.</p>
<p>Both routes use SciPy convolution with same-size output and symmetric boundary extension. Route A first produces a blurred image and then differentiates it. Route B applies one precomputed DoG kernel directly to the input for each direction.</p>
{route_panels}<table><thead><tr><th>Direction</th><th>Interior max absolute error</th><th>Full-image max absolute error</th></tr></thead><tbody>{errors}</tbody></table>
<p>Convolution is associative on a consistently extended image, but finite-image cropping and boundary extension must still be checked. I exclude a conservative {m['comparison_margin']}-pixel margin on every side for the interior comparison; both x and y results pass rtol = 1e-11 and atol = 1e-14 there. With this symmetric Gaussian and the chosen symmetric boundary handling, the full-image results also agree to floating-point precision, including the borders. There is no material border discrepancy in this experiment. The difference panels are amplified by their own maxima and show rounding-level residuals, not visible edge differences. Different padding or truncated composed kernels can break this agreement.</p>
<details><summary>Filter implementation</summary><pre><code>{filter_code}</code></pre></details></section>
<section id="comparison"><h2>03 / Compared with finite differences alone</h2><h3>Without smoothing · Part 1.2</h3><div class="triple">{raw}</div>
<h3>With Gaussian smoothing · Part 1.3</h3><div class="triple">{smooth}</div>
<p>All magnitude panels share a display mapping of white at magnitude 0.25; stronger values clip only for viewing. Signed derivative panels also share one scale across the raw, sequential and direct results. Every edge map is computed from the original floating-point magnitudes, never from these display images.</p>
<p>At the same threshold T = 0.20, the raw image has {m['fixed_threshold_020']['raw']:.2%} edge pixels, while the smoothed image has {m['fixed_threshold_020']['smoothed']:.2%}. Smoothing reduces gradient amplitudes, so the threshold must be reconsidered. The two main selected edge maps use different thresholds; they illustrate a qualitative tradeoff rather than an accuracy score. No labeled ground truth is available.</p>
<p>{escape(observation.strip())}</p>
<h3>Threshold sweep after smoothing</h3><div class="triple">{sweep}</div>
<h3>Gaussian scale sweep</h3><p>The following comparisons hold T = {threshold:.2f} and all display scales fixed. Each Gaussian has a radius of ceil(3σ). Increasing σ suppresses finer texture but spreads intensity transitions and can remove or merge nearby details.</p>{sigma_panels}</section>
<section id="orientation"><h2>04 / Bells &amp; Whistles: gradient orientation</h2>
<p class="badge">Mandatory extension · No built-in angle functions</p><div class="triple">{figure('orientation-raw.png', 'Raw gradient orientation', 'Hue = direction; brightness = magnitude')}{figure('orientation-smoothed.png', 'Smoothed gradient orientation', 'Same hue and brightness mapping')}{figure('orientation-wheel.png', 'Direction color wheel', 'Degrees clockwise from +x; image y increases downward')}</div>
<p>I compute the direction of the <strong>gradient vector</strong>, which is perpendicular to an edge contour and points toward increasing brightness. Because image coordinates have x to the right and y downward, angles increase clockwise: 0° is right, 90° down, 180° left and 270° up. Reversing edge polarity rotates the direction by 180°.</p>
<p>First set r = min(|I<sub>x</sub>|, |I<sub>y</sub>|) / max(|I<sub>x</sub>|, |I<sub>y</sub>|). This limits r to [0, 1]. For r &gt; √2 − 1, use z = (r − 1)/(r + 1) and add π/4 after evaluating the series; otherwise z = r. This keeps |z| ≤ √2 − 1 and makes the alternating series converge rapidly:</p>
<p class="formula">a(z) = z − z³/3 + z⁵/5 − … &nbsp; (24 terms)</p>
<p>The next omitted term bounds the truncation error by |z|<sup>49</sup>/49, below 4 × 10<sup>−21</sup> over this reduced interval; actual accuracy is limited by floating-point rounding. I recover the first-quadrant direction using π/2 − a when |I<sub>y</sub>| &gt; |I<sub>x</sub>|, then recover all four quadrants from the signs of I<sub>x</sub> and I<sub>y</sub>. Axis-aligned vectors work without division by zero. A zero vector receives a stored angle of zero and is displayed black because its magnitude is zero; its direction has no geometric meaning.</p>
<p class="formula">H = θ / (2π) &nbsp; · &nbsp; S = 1 &nbsp; · &nbsp; V = clip(M / 0.15, 0, 1)</p>
<p>I implement HSV-to-RGB with six hue sectors using NumPy. Both images use the same brightness scale, so smoothing-related strength changes remain visible. Weak gradients become dark rather than producing prominent arbitrary colors in flat areas. This section uses no inverse trigonometric, complex-angle, OpenCV phase or Cartesian-to-polar angle function.</p>
<details><summary>Manual direction calculation</summary><pre><code>{angle_code}</code></pre></details></section>
<section><h2>Verification and reproducibility</h2><p>Seven real-array unit tests cover Gaussian normalization/symmetry, full DoG support and zero coefficient sum, interior route equivalence, constant inputs, eight axis/diagonal directions, known non-diagonal directions, HSV primary colors and zero-strength black. Raw arrays preserve both routes, signed gradients and direction in radians.</p>
<p>The input and its source record are copied from Part 1.2. The image is the modern scikit-image camera sample by Lav Varshney, identified as CC0 in the <a href="https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.camera">official documentation</a>. Input SHA-256: <code class="hash">{m['input_sha256']}</code>.</p>
<p><a href="dog.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_dog.py">Unit tests</a> · <a href="results/metrics.json">Measurements</a> · <a href="results/dog-arrays.npz">Raw arrays</a> · <a href="input/source.json">Image source record</a></p>
<h3>What I learned</h3><p>Smoothing changes both noise sensitivity and the strength and width of edge responses, so it also changes the useful threshold. Composing the Gaussian and difference kernels gives the same interior gradient with a single image convolution, but cropping and boundary extension must be accounted for. HSV adds direction information that a magnitude-only edge map discards.</p>
<p class="versions">Python {m['versions']['python']} · NumPy {m['versions']['numpy']} · SciPy {m['versions']['scipy']} · OpenCV {m['versions']['opencv']} · Pillow {m['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 1.3 + Mandatory Bells &amp; Whistles</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
