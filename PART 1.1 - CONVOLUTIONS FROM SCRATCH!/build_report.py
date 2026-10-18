"""Build an English webpage from saved metrics; never rerun convolution."""
from html import escape
import inspect
import json
from pathlib import Path

import convolution

HERE = Path(__file__).resolve().parent


def image(src, alt, caption):
    # Reused pattern from Assignment 1 part-two/build_report.py.
    return (f'<figure><a href="{escape(src)}"><img src="{escape(src)}" '
            f'alt="{escape(alt)}" loading="lazy"></a><figcaption>{caption}</figcaption></figure>')


def build_report():
    report = json.loads((HERE / 'results/metrics.json').read_text(encoding='utf-8'))
    names = {'four_loops': 'Four loops', 'two_loops': 'Two loops', 'scipy': 'SciPy'}
    labels = {'box': '9 × 9 box filter', 'dx': 'Horizontal derivative', 'dy': 'Vertical derivative'}
    rows = []
    comparisons = []
    for key, item in report['filters'].items():
        for method, measurements in item['methods'].items():
            rows.append(f'<tr><th>{labels[key]}</th><td>{names[method]}</td>'
                        f'<td>{measurements["median_seconds"]:.6f}</td>'
                        f'<td>{measurements["max_abs_error"]:.3e}</td></tr>')
        comparisons.append(f'<h3>{labels[key]}</h3><div class="triple">' + ''.join(
            image(f'results/{key}-{method}.png', f'{labels[key]} using {names[method]}', names[method])
            for method in names) + '</div>')
    snippets = ''.join(f'<h3>{title}</h3><pre><code>{escape(inspect.getsource(function))}</code></pre>'
                       for title, function in [('Shared zero padding and kernel flip', convolution.prepare),
                                               ('Four-loop implementation', convolution.convolve_four_loops),
                                               ('Two-loop implementation', convolution.convolve_two_loops)])
    box = report['filters']['box']['methods']
    speedup = box['four_loops']['median_seconds'] / box['two_loops']['median_seconds']
    width, height = report['working_size_wh']
    scale = report['derivative_display']['shared_abs_scale']
    original = image('results/original-gray.png', 'Grayscale selfie input', f'Grayscale input · {width} × {height}')
    results = ''.join(image(f'results/{key}-two_loops.png', labels[key], labels[key]) for key in labels)
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part 1.1 · Convolutions from Scratch!</title><link rel="stylesheet" href="../style.css">
<link rel="stylesheet" href="page.css"></head><body><main class="shell">
<header class="site-header"><a class="brand" href="../index.html">Fun with Filters<br>and Frequencies!</a>
<nav class="header-nav"><a href="#results">Filter results <span>01</span></a><a href="#implementation">Implementation <span>02</span></a><a href="#comparison">Comparison <span>03</span></a></nav></header>
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p>
<h1>PART 1.1:<br>CONVOLUTIONS<br>FROM SCRATCH!</h1>
<p class="project-deck">One selfie, three filters, and two handwritten implementations. A neighborhood of pixels becomes blur or a directional change through convolution.</p></section>
<section id="results"><h2>01 / A selfie through three filters</h2><div class="four-grid">{original}{results}</div>
<p>The original JPEG is {report['original_size_wh'][0]} × {report['original_size_wh'][1]} pixels. Pillow converts it to grayscale, resizes it proportionally to {width} × {height} with Lanczos resampling, and NumPy represents it as float64 in [0, 1]. Every convolution uses this same input. Pillow is used only for image I/O and preparation; both handwritten convolution algorithms use NumPy alone.</p>
<p class="formula">Box = ones((9, 9)) / 81 &nbsp; · &nbsp; D<sub>x</sub> = [1, −1] &nbsp; · &nbsp; D<sub>y</sub> = [1, −1]<sup>T</sup></p>
<p>The box filter averages 81 samples, softening the hair, glasses and jacket detail. D<sub>x</sub> measures left-to-right intensity changes and emphasizes vertical boundaries; D<sub>y</sub> measures top-to-bottom changes and emphasizes horizontal boundaries. With convolution and these kernels, interior derivatives are I[y, x] − I[y, x−1] and I[y, x] − I[y−1, x].</p>
<p>Derivative arrays retain their signed values. For display only, zero becomes middle gray, positive changes become brighter, and negative changes darker. Both directions use the same scale, ±{scale:.6f}; they are not independently normalized or clipped to positive values.</p></section>
<section id="implementation"><h2>02 / Convolution, written by hand</h2>
<p>Convolution flips the kernel along both axes before the multiply-and-sum operation. Omitting this flip would implement correlation, which changes the sign or orientation of asymmetric filters.</p>
<p>Both versions have O(HWk<sub>h</sub>k<sub>w</sub>) arithmetic cost. Four loops visit every output pixel and every kernel coefficient in Python. Two loops still visit every output pixel, but NumPy handles the kernel-sized multiplication and sum. No built-in convolution, FFT, stride trick or high-level filtering function is used inside either implementation.</p>
{snippets}<h3>Boundary handling</h3>
<p>Values outside the image are zero; the output has the same dimensions as the input. A 9 × 9 kernel receives four zeros on each side. A 1 × 2 kernel receives one zero on the left and none on the right; a 2 × 1 kernel receives one above and none below. This asymmetric padding matches SciPy's centering convention for even kernels.</p>
<p>Zero padding darkens the outer rim of the box-filter image because some of its 81 samples are zero. It also creates artificial differences against zero at the left boundary for D<sub>x</sub> and the top boundary for D<sub>y</sub>. These are boundary effects, not scene edges; reflection or edge replication would produce different results.</p></section>
<section id="comparison"><h2>03 / Checking against SciPy</h2>
<pre><code>reference = scipy.signal.convolve2d(image, kernel,
    mode="same", boundary="fill", fillvalue=0)
np.testing.assert_allclose(result, reference, rtol=1e-12, atol=1e-12)</code></pre>
<div class="table-scroll"><table><thead><tr><th>Filter</th><th>Method</th><th>Median time (s)</th><th>Max absolute error</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>Timings are medians of {report['repeats']} sequential runs per method/filter, after an untimed 16 × 16 warm-up. They include padding and result allocation, and exclude loading, resizing, comparisons and saving. All measurements use the same {width} × {height} float64 input. The two-loop box filter is {speedup:.2f}× faster than the four-loop version in this run. Tiny two-coefficient filters may favor four loops because per-pixel NumPy call overhead can dominate. SciPy executes its convolution in compiled code; these measurements describe this machine, not a universal speed ranking.</p>
<p>All nine outputs passed the numerical comparison at rtol = atol = 1e-12. Five real-array unit tests cover asymmetric kernels, even-kernel alignment, signed derivatives on uint8 input, a kernel larger than the image, an impulse at the boundary, and identity/zero filters.</p>
{''.join(comparisons)}</section>
<section><h2>What I learned</h2><p>A correct convolution depends on both the kernel flip and its boundary convention. Vectorizing the inner calculation reduces Python overhead without changing the mathematics, but for very small kernels that overhead tradeoff can reverse. Signed derivatives also need a different display mapping from ordinary photographs.</p>
<p>Image I/O, timing and figure-generation patterns were adapted from my Assignment 1 project, Perspective Through the Lens. Its alignment algorithms were not used here.</p>
<p><a href="convolution.py">Convolution source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_convolution.py">Unit tests</a> · <a href="results/metrics.json">Measurements</a> · <a href="results/convolution-arrays.npz">Raw arrays</a></p>
<p class="versions">Python {report['versions']['python']} · NumPy {report['versions']['numpy']} · SciPy {report['versions']['scipy']} · Pillow {report['versions']['pillow']}</p></section>
<footer class="site-footer"><span>SYDE 671 · Assignment 2</span><span>Part 1.1 · Convolutions from Scratch!</span></footer>
</main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
