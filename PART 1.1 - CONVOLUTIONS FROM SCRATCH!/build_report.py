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
<p class="project-deck">I apply three filters to my selfie. I write convolution with four loops and two loops, then compare both with SciPy.</p></section>
<section id="results"><h2>01 / A selfie through three filters</h2><div class="four-grid">{original}{results}</div>
<p>The original photo is {report['original_size_wh'][0]} × {report['original_size_wh'][1]} pixels. I use Pillow to make it grayscale and resize it to {width} × {height}, keeping its shape. Lanczos is the resize method. I then store the pixels as float64 values from 0 to 1. All methods use this same input. The two handwritten filters use only NumPy.</p>
<p class="formula">Box = ones((9, 9)) / 81 &nbsp; · &nbsp; D<sub>x</sub> = [1, −1] &nbsp; · &nbsp; D<sub>y</sub> = [1, −1]<sup>T</sup></p>
<p>The box filter averages a 9 × 9 area, so hair, glasses and jacket details look softer. D<sub>x</sub> finds changes from left to right, making vertical edges stand out. D<sub>y</sub> finds changes from top to bottom, making horizontal edges stand out. Away from the borders, they calculate I[y,x] − I[y,x−1] and I[y,x] − I[y−1,x].</p>
<p>I keep both positive and negative derivative values. In the pictures, gray means zero, brighter means positive and darker means negative. Both directions use the same scale, ±{scale:.6f}. This display step does not change the saved values.</p></section>
<section id="implementation"><h2>02 / Convolution, written by hand</h2>
<p>I flip the filter horizontally and vertically before multiplying and adding the pixels. Without the flip, the operation is correlation. The difference matters for filters that are not symmetric.</p>
<p>Both versions do O(HWk<sub>h</sub>k<sub>w</sub>) calculations. The four-loop version uses Python loops for the pixels and filter values. The two-loop version keeps the pixel loops but lets NumPy do each small multiplication and sum. Neither version calls a built-in convolution, FFT or filtering function.</p>
{snippets}<h3>Boundary handling</h3>
<p>I treat values outside the image as zero and keep the output size unchanged. The 9 × 9 filter needs four zeros on every side. For the 1 × 2 filter, I add one zero on the left. For the 2 × 1 filter, I add one above. This matches how SciPy centers these filters.</p>
<p>Zero padding makes the blurred image darker at the border. It also creates false derivative responses at the left and top edges, where the image meets zero. Reflecting the image at its border would give different results.</p></section>
<section id="comparison"><h2>03 / Checking against SciPy</h2>
<pre><code>reference = scipy.signal.convolve2d(image, kernel,
    mode="same", boundary="fill", fillvalue=0)
np.testing.assert_allclose(result, reference, rtol=1e-12, atol=1e-12)</code></pre>
<div class="table-scroll"><table><thead><tr><th>Filter</th><th>Method</th><th>Median time (s)</th><th>Max absolute error</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>I run each method/filter {report['repeats']} times and report the median time. A small 16 × 16 warm-up runs first. Timing includes padding and creating the output, but not reading or saving images. Every method uses the same {width} × {height} input. Here, the two-loop box filter is {speedup:.2f}× faster than four loops. For very small filters, calling NumPy at every pixel can cost more time than a short Python loop. SciPy runs in compiled code. These times are specific to this computer.</p>
<p>All nine outputs match SciPy with rtol = atol = 1e-12. Five unit tests check filter direction, even-sized filters, signed differences from uint8 input, large filters, border pixels and simple identity/zero filters.</p>
{''.join(comparisons)}</section>
<section><h2>What I learned</h2><p>I learned that flipping the filter and handling the borders are both important. NumPy makes the inner calculation faster for the box filter, but it does not always help a tiny filter. I also learned to show negative derivatives around a gray midpoint. Comparing with SciPy helped me catch small errors that are hard to see in the pictures. The two-loop version still does the same calculations, but NumPy handles more of the work.</p>
<p>I reused image loading, timing and figure code patterns from my Assignment 1 project, Perspective Through the Lens. I did not use its alignment algorithms.</p>
<p><a href="convolution.py">Convolution source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_convolution.py">Unit tests</a> · <a href="results/metrics.json">Measurements</a> · <a href="results/convolution-arrays.npz">Raw arrays</a></p>
<p class="versions">Python {report['versions']['python']} · NumPy {report['versions']['numpy']} · SciPy {report['versions']['scipy']} · Pillow {report['versions']['pillow']}</p></section>
<footer class="site-footer"><span>SYDE 671 · Assignment 2</span><span>Part 1.1 · Convolutions from Scratch!</span></footer>
</main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
