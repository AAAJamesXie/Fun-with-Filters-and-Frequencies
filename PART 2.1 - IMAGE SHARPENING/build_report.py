"""Build the English sharpening report from saved measurements."""
from html import escape
import inspect
import json
from pathlib import Path
import sharpen

HERE = Path(__file__).resolve().parent


def figure(filename, title, caption=''):
    return (f'<figure><a href="results/{escape(filename)}"><img src="results/{escape(filename)}" '
            f'alt="{escape(title)}" loading="lazy"></a><figcaption>{escape(title)}'
            f'<span>{escape(caption)}</span></figcaption></figure>')


def build_report():
    m = json.loads((HERE / 'results/metrics.json').read_text(encoding='utf-8'))
    observation = HERE / 'observations.txt'
    comments = observation.read_text(encoding='utf-8') if observation.exists() else 'Visual review pending.'
    examples = ''
    for key, title in [('taj', 'The Taj Mahal'), ('cats', 'An additional image: cats')]:
        record = m['images'][key]
        four = ''.join(figure(f'{key}-{suffix}.png', label) for suffix, label in [
            ('original', 'Original'), ('blurred', 'Gaussian low frequencies'),
            ('high', 'Signed high frequencies'), ('selected', 'Sharpened · α = 1')])
        amounts = ''.join(figure(row['file'], f'α = {row["alpha"]:g}', f'{row["outside_fraction"]:.2%} channel samples outside [0, 1] before display clipping')
                          for row in record['amounts'])
        crops = ''.join(figure(row['crop'], f'Detail · α = {row["alpha"]:g}') for row in record['amounts'])
        errors = max(row['max_route_error'] for row in record['amounts'])
        examples += f'''<h3>{title}</h3><div class="four-grid">{four}</div>
<p>The source is {record['original_size_wh'][0]} × {record['original_size_wh'][1]} pixels. I work at {record['working_size_wh'][0]} × {record['working_size_wh'][1]}. All versions use the same RGB input and σ = {m['sigma']:g}. The panels show the original, blur, detail and sharpened result.</p>
<h3>Varying the sharpening amount</h3><div class="triple">{amounts}</div>
<h3>The same detail region, enlarged 2×</h3><div class="triple">{crops}</div>
<p>I crop the same area in each result and enlarge it with nearest-neighbor resizing. This keeps the comparison fair. The largest difference between the two sharpening methods is {errors:.3e} before clipping.</p>'''
    restoration = m['restoration']
    restored = next(row for row in restoration['amounts'] if row['alpha'] == restoration['selected_alpha'])
    trio = figure('restore-reference.png', 'Original reference') + figure('restore-degraded.png', 'Artificial Gaussian blur · σ = 2')
    trio += figure(restored['file'], f'Resharpened · α = {restored["alpha"]:g}')
    detail = figure('restore-reference-crop.png', 'Original detail') + figure('restore-degraded-crop.png', 'Blurred detail')
    detail += figure(restored['crop'], 'Resharpened detail')
    rows = ''.join(f'<tr><th>{row["alpha"]:g}</th><td>{row["display_mse_before_quantization"]:.8f}</td>'
                   f'<td>{row["display_psnr_db_before_quantization"]:.3f}</td><td>{row["outside_fraction"]:.2%}</td></tr>'
                   for row in restoration['amounts'])
    source = escape(inspect.getsource(sharpen.filter_image) + '\n' + inspect.getsource(sharpen.unsharp_mask))
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part 2.1 · Image Sharpening</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="page.css"></head>
<body><main class="shell"><header class="site-header"><a class="brand" href="../index.html">Fun with Filters<br>and Frequencies!</a>
<nav class="header-nav"><a href="#method">Unsharp masking <span>01</span></a><a href="#examples">Images &amp; amounts <span>02</span></a><a href="#restore">Blur &amp; resharpen <span>03</span></a></nav></header>
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p><h1>PART 2.1:<br>IMAGE<br>SHARPENING</h1>
<p class="project-deck">I subtract a blurred image to get the fine detail, then add some of that detail back. This makes edges look sharper, but cannot recover everything lost to blur.</p></section>
<section id="method"><h2>01 / The unsharp mask</h2>
<p>A Gaussian filter blurs the image and keeps its broad shapes and colors. Subtracting the blur from the original gives the high-frequency detail. Adding more of this detail makes edges stand out.</p>
<p class="formula">B = G * I &nbsp; · &nbsp; H = I − B<br>S = I + αH = (1 + α)I − α(G * I)<br>K = (1 + α)δ − αG &nbsp; ⇒ &nbsp; S = K * I</p>
<p>δ is a filter with one in the center and zeros elsewhere. I combine it with the Gaussian to make K, then apply K once to each RGB channel. Channels are kept separate. Both methods reflect the borders and keep the image size. I reuse the Gaussian method from Part 1.3, with radius ceil(3σ). Here σ = {m['sigma']:g} and the filter is {m['images']['taj']['gaussian_shape'][0]} × {m['images']['taj']['gaussian_shape'][1]}.</p>
<p>When α = 0, the image does not change. Larger α adds more detail contrast. The filter sums to one, so constant colors stay the same apart from rounding. I use float64 RGB values from 0 to 1 without gamma correction. I compare the raw results before clipping. Only the PNG output clips values to 0–1 and rounds them to 8-bit.</p>
<details><summary>Implementation and single-kernel construction</summary><pre><code>{source}</code></pre></details></section>
<section id="examples"><h2>02 / Two images, five sharpening amounts</h2>
<p>In the detail pictures, gray means zero, brighter means positive and darker means negative. All use the same scale, ±0.25 per channel. Large values may be clipped in the pictures, but the raw files keep them. The original, blurred and sharpened pictures use their normal RGB colors.</p>
{examples}<h3>Visual observations</h3><p>{escape(comments.strip())}</p></section>
<section id="restore"><h2>03 / Can sharpening undo blur?</h2>
<p>I use the resized cat photo as the reference. I blur it with σ = 2, then sharpen it with σ = {m['sigma']:g}. I do not add noise. The reference is just the original input for this test. The result below uses α = {restoration['selected_alpha']:g}.</p>
<div class="triple">{trio}</div><h3>Identical detail crops</h3><div class="triple">{detail}</div>
<p>Compared with the reference, the blurred image has MSE {restoration['degraded']['display_mse_before_quantization']:.8f} and PSNR {restoration['degraded']['display_psnr_db_before_quantization']:.3f} dB. With α = {restored['alpha']:g}, MSE is {restored['display_mse_before_quantization']:.8f} and PSNR is {restored['display_psnr_db_before_quantization']:.3f} dB. I calculate these after clipping to 0–1 but before converting to 8-bit. Lower MSE and higher PSNR mean closer pixel values in this test. They do not always mean a better-looking image.</p>
<table><thead><tr><th>Amount α</th><th>MSE</th><th>PSNR (dB)</th><th>Outside range</th></tr></thead><tbody>{rows}</tbody></table>
<p>α = 0 is the blurred image without sharpening. The last column counts individual RGB values outside 0–1 before clipping, rather than whole pixels. The measurement file also keeps MSE before clipping. I show α = 2 as one example and list all tested amounts.</p>
<p>The eyes and face outline look clearer after sharpening, but fine fur details are still softer than the reference. Sharpening increases the contrast that remains; it does not exactly undo the blur. Large amounts can also make noise, JPEG marks and bright/dark outlines stronger. Looking sharper is not the same as recovering the original detail.</p></section>
<section><h2>Verification and reproducibility</h2>
<p>Six unit tests check that both methods agree, including at the borders. They also check α = 0, constant colors, separate RGB channels, signed detail, values outside 0–1, the filter sum and invalid inputs. I compare both methods at every amount on both photos and the blurred cat photo.</p>
<p>Taj Mahal is the course image. The additional cat photo is the photo I selected for this assignment. I resize it to width 480, keeping its shape and using Lanczos. I use the same photo for the blur test. The records include input hashes, sizes, sharpening amounts, clipped fractions and blur-test scores. <a href="input/cats.jpg">View the supplied cat photo</a>.</p>
<p><a href="sharpen.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_sharpen.py">Unit tests</a> · <a href="results/metrics.json">Measurements</a> · <a href="results/sharpen-arrays.npz">Raw arrays</a> · <a href="input/source.json">Input source record</a></p>
<h3>What I learned</h3><p>I learned that sharpening makes edges stand out but does not fully restore a blurred image. A setting that works well on a building can make fur look too harsh. Keeping raw values separate from the pictures helps check the calculation.</p>
<p class="versions">Python {m['versions']['python']} · NumPy {m['versions']['numpy']} · SciPy {m['versions']['scipy']} · OpenCV {m['versions']['opencv']} · Pillow {m['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 2.1 · Image Sharpening</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
