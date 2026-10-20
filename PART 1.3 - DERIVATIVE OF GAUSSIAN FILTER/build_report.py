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
<p class="project-deck">I blur the image before finding edges to reduce grass texture. I also combine the blur and difference filters into one filter, then use color to show gradient direction.</p>
<p class="badge">Includes Part 1 Bells &amp; Whistles · Mandatory gradient orientation</p></section>
<section id="gaussian"><h2>01 / Constructing the filters</h2><div class="triple">{kernels}</div>
<p>I use the same 512 × 512 grayscale image as Part 1.2, with float64 values from 0 to 1. The Gaussian blur has σ = {sigma:g}. Its radius is ceil(3σ), so the filter is {m['kernel_shape'][0]} × {m['kernel_shape'][1]}. I make a one-dimensional Gaussian with OpenCV, then multiply it by its transpose to make the two-dimensional filter.</p>
<pre><code>g = cv2.getGaussianKernel(2 * ceil(3 * sigma) + 1, sigma, cv2.CV_64F)
G = g @ g.T
Kx = scipy.signal.convolve2d(G, [[1., -1.]], mode="full")
Ky = scipy.signal.convolve2d(G, [[1.], [-1.]], mode="full")</code></pre>
<p>DoG means <strong>derivative of Gaussian</strong> here. I combine the Gaussian with the same difference filters as Part 1.2. I use full convolution so no filter values are cut off. This adds one column to the x filter and one row to the y filter. The Gaussian sums to {m['kernel_sums']['gaussian']:.16f}; the DoG sums are {m['kernel_sums']['kx']:.3e} and {m['kernel_sums']['ky']:.3e}. Their near-zero sums mean a constant image gives almost no derivative response.</p>
<p>I enlarge the filter pictures with nearest-neighbor resizing so each value is visible. Gaussian brightness is divided by its maximum. Both DoG pictures use the same scale: gray is zero, brighter is positive and darker is negative.</p></section>
<section id="routes"><h2>02 / Two steps or one convolution?</h2>
<p class="formula">Route A: (I * G) * D<sub>x</sub> &nbsp; · &nbsp; Route B: I * (G * D<sub>x</sub>)<br>The same construction applies to D<sub>y</sub>.</p>
<p>Both methods use SciPy with the same output size and reflected borders. Route A blurs the image, then finds its derivatives. Route B first combines the two filters, then filters the image once per direction.</p>
{route_panels}<table><thead><tr><th>Direction</th><th>Interior max absolute error</th><th>Full-image max absolute error</th></tr></thead><tbody>{errors}</tbody></table>
<p>Combining the filters should give the same result, but borders and cropping can affect it. I leave out a {m['comparison_margin']}-pixel border when checking the interior. Both directions pass rtol = 1e-11 and atol = 1e-14. For these filters and reflected borders, the full images also match to floating-point precision. The difference pictures are enlarged in brightness to show tiny rounding errors. Other border rules or cutting off the combined filter could give different results.</p>
<details><summary>Filter implementation</summary><pre><code>{filter_code}</code></pre></details></section>
<section id="comparison"><h2>03 / Compared with finite differences alone</h2><h3>Without smoothing · Part 1.2</h3><div class="triple">{raw}</div>
<h3>With Gaussian smoothing · Part 1.3</h3><div class="triple">{smooth}</div>
<p>All magnitude pictures use white for 0.25; larger values are clipped only in the pictures. The derivative pictures also share one scale. I always make edge maps from the saved float values.</p>
<p>At T = 0.20, {m['fixed_threshold_020']['raw']:.2%} of pixels are edges before smoothing and {m['fixed_threshold_020']['smoothed']:.2%} after smoothing. Blur makes gradients weaker, so I choose a lower threshold for the smoothed image. The two selected maps use different thresholds. They show the visual difference, not an accuracy score.</p>
<p>{escape(observation.strip())}</p>
<h3>Threshold sweep after smoothing</h3><div class="triple">{sweep}</div>
<h3>Gaussian scale sweep</h3><p>I keep T = {threshold:.2f} and the display scales fixed below. Each Gaussian radius is ceil(3σ). A larger σ removes more fine texture, but it also widens edges and can merge nearby details.</p>{sigma_panels}</section>
<section id="orientation"><h2>04 / Bells &amp; Whistles: gradient orientation</h2>
<p class="badge">Mandatory extension · No built-in angle functions</p><div class="triple">{figure('orientation-raw.png', 'Raw gradient orientation', 'Hue = direction; brightness = magnitude')}{figure('orientation-smoothed.png', 'Smoothed gradient orientation', 'Same hue and brightness mapping')}{figure('orientation-wheel.png', 'Direction color wheel', 'Degrees clockwise from +x; image y increases downward')}</div>
<p>The <strong>gradient direction</strong> points toward brighter pixels and is perpendicular to the edge. In image coordinates, x points right and y points down. Angles therefore go clockwise: 0° right, 90° down, 180° left and 270° up. Reversing dark and light changes the angle by 180°.</p>
<p>I first calculate r = min(|I<sub>x</sub>|, |I<sub>y</sub>|) / max(|I<sub>x</sub>|, |I<sub>y</sub>|), so r stays between 0 and 1. For r &gt; √2 − 1, I use z = (r − 1)/(r + 1) and add π/4 after the series. Otherwise, z = r. This keeps |z| small so the following 24-term series converges quickly:</p>
<p class="formula">a(z) = z − z³/3 + z⁵/5 − … &nbsp; (24 terms)</p>
<p>The next term, |z|<sup>49</sup>/49, is below 4 × 10<sup>−21</sup>. Floating-point rounding is larger than this series error. I use π/2 − a when |I<sub>y</sub>| &gt; |I<sub>x</sub>|, then use the signs to choose the correct quadrant. I handle zero denominators separately. A zero gradient is stored with angle zero and shown as black; it has no real direction.</p>
<p class="formula">H = θ / (2π) &nbsp; · &nbsp; S = 1 &nbsp; · &nbsp; V = clip(M / 0.15, 0, 1)</p>
<p>I convert HSV to RGB with six color ranges using NumPy. Both images use the same brightness scale. Weak gradients look dark, so flat areas do not fill with bright colors. I do not use built-in inverse trigonometric or angle functions.</p>
<details><summary>Manual direction calculation</summary><pre><code>{angle_code}</code></pre></details></section>
<section><h2>Verification and reproducibility</h2><p>Seven unit tests check Gaussian shape and sum, DoG size and sum, agreement between the two methods, constant images, known directions, HSV colors and zero gradients. The raw files keep both methods, signed gradients and angles in radians.</p>
<p>I copy the input and source record from Part 1.2. It is the scikit-image camera sample by Lav Varshney, listed as CC0 in the <a href="https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.camera">official documentation</a>. Input SHA-256: <code class="hash">{m['input_sha256']}</code>.</p>
<p><a href="dog.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_dog.py">Unit tests</a> · <a href="results/metrics.json">Measurements</a> · <a href="results/dog-arrays.npz">Raw arrays</a> · <a href="input/source.json">Image source record</a></p>
<h3>What I learned</h3><p>I learned that blur reduces texture, but also weakens and widens edges. The threshold needs to change with it. Combining the two filters gives the same result here, including the borders. The color view adds direction information that the edge magnitude does not show. The sigma comparison helped me see when stronger blur starts to remove useful detail. Lowering the threshold can keep weaker responses, but it cannot bring back detail already lost to blur.</p>
<p class="versions">Python {m['versions']['python']} · NumPy {m['versions']['numpy']} · SciPy {m['versions']['scipy']} · OpenCV {m['versions']['opencv']} · Pillow {m['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 1.3 + Mandatory Bells &amp; Whistles</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
