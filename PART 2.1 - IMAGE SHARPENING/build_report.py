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
    for key, title in [('taj', 'The Taj Mahal'), ('selfie', 'An additional image: my selfie')]:
        record = m['images'][key]
        four = ''.join(figure(f'{key}-{suffix}.png', label) for suffix, label in [
            ('original', 'Original'), ('blurred', 'Gaussian low frequencies'),
            ('high', 'Signed high frequencies'), ('selected', 'Sharpened · α = 1')])
        amounts = ''.join(figure(row['file'], f'α = {row["alpha"]:g}', f'{row["outside_fraction"]:.2%} channel samples outside [0, 1] before display clipping')
                          for row in record['amounts'])
        crops = ''.join(figure(row['crop'], f'Detail · α = {row["alpha"]:g}') for row in record['amounts'])
        errors = max(row['max_route_error'] for row in record['amounts'])
        examples += f'''<h3>{title}</h3><div class="four-grid">{four}</div>
<p>The original file is {record['original_size_wh'][0]} × {record['original_size_wh'][1]} pixels; the working image is {record['working_size_wh'][0]} × {record['working_size_wh'][1]}. Every variant uses the same RGB input and Gaussian σ = {m['sigma']:g}. The four panels show the full unsharp-mask construction.</p>
<h3>Varying the sharpening amount</h3><div class="triple">{amounts}</div>
<h3>The same detail region, enlarged 2×</h3><div class="triple">{crops}</div>
<p>Every crop uses the same rectangle and nearest-neighbor enlargement, so resampling does not create different detail between variants. Across these amounts, the maximum full-image discrepancy between the two implementations is {errors:.3e} before clipping.</p>'''
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
<p class="project-deck">Subtract the low frequencies, amplify the remaining detail, and add it back. Edges look crisper, but contrast enhancement cannot recreate all the information lost to blur.</p></section>
<section id="method"><h2>01 / The unsharp mask</h2>
<p>A Gaussian filter is a low-pass filter: it keeps broad intensity variations and suppresses rapid changes. Subtracting this blurred image from the original isolates a high-frequency residual. Adding a scaled residual increases local edge contrast.</p>
<p class="formula">B = G * I &nbsp; · &nbsp; H = I − B<br>S = I + αH = (1 + α)I − α(G * I)<br>K = (1 + α)δ − αG &nbsp; ⇒ &nbsp; S = K * I</p>
<p>δ is an impulse kernel with one at its center and zero elsewhere. The combined kernel K is applied with one spatial convolution per RGB channel, so no color channels are mixed. Both implementations use symmetric boundaries and preserve image dimensions. The Gaussian construction reuses Part 1.3: an outer product of a normalized OpenCV Gaussian column with radius ceil(3σ). Here σ = {m['sigma']:g} and the kernel is {m['images']['taj']['gaussian_shape'][0]} × {m['images']['taj']['gaussian_shape'][1]}.</p>
<p>At α = 0 the output is the original. Increasing α boosts the high-frequency residual more strongly. The kernel sums to one within floating-point precision, preserving constant colors. Computation uses float64 encoded RGB values normalized to [0, 1], without gamma linearization. PNG output alone clips values to [0, 1] and rounds to uint8. All implementation comparisons use unclipped floating-point arrays.</p>
<details><summary>Implementation and single-kernel construction</summary><pre><code>{source}</code></pre></details></section>
<section id="examples"><h2>02 / Two images, five sharpening amounts</h2>
<p>Signed high-frequency panels use middle gray for zero and a shared scale of ±0.25 per channel. Positive residuals appear brighter and negative residuals darker; large residuals can clip in the visualization. The saved raw arrays retain the actual signed values. Original, blurred and sharpened photographs use ordinary RGB display values, without independent contrast normalization.</p>
{examples}<h3>Visual observations</h3><p>{escape(comments.strip())}</p></section>
<section id="restore"><h2>03 / Can sharpening undo blur?</h2>
<p>I use the resized selfie as the sharp reference for this controlled experiment. It is first blurred with Gaussian σ = 2, then sharpened with σ = {m['sigma']:g}. This reference is the original digital image used here, not a claim that the photograph is optically perfect. There is no added noise. The following result uses α = {restoration['selected_alpha']:g}.</p>
<div class="triple">{trio}</div><h3>Identical detail crops</h3><div class="triple">{detail}</div>
<p>The blurred input has MSE {restoration['degraded']['display_mse_before_quantization']:.8f} and PSNR {restoration['degraded']['display_psnr_db_before_quantization']:.3f} dB relative to the reference. The α = {restored['alpha']:g} result has MSE {restored['display_mse_before_quantization']:.8f} and PSNR {restored['display_psnr_db_before_quantization']:.3f} dB. These metrics compare float RGB values after clipping but before 8-bit PNG quantization. Lower MSE and higher PSNR mean closer pixel agreement in this artificial-blur experiment, not universally better perceptual quality.</p>
<table><thead><tr><th>Amount α</th><th>MSE</th><th>PSNR (dB)</th><th>Outside range</th></tr></thead><tbody>{rows}</tbody></table>
<p>The α = 0 row is the blurred image without sharpening. The final column counts scalar RGB channel samples outside [0, 1] before clipping, not whole pixels. Raw, unclipped MSE is also saved in the measurement file. α = 2 is shown for visual comparison; the table reports all tested amounts rather than claiming a universal optimum.</p>
<p>Contrast around the glasses and mouth improves compared with the blurred image, but fine hair and facial detail remain much softer than the original reference. The process is not an exact inverse Gaussian filter. At extremely high frequencies, the blur has strongly attenuated the reference signal; multiplying the remaining residual by a finite amount cannot fully recover it. Stronger sharpening can also amplify noise, JPEG artifacts and halos. The original and resharpened crops should therefore be compared for actual fine detail, not just apparent crispness.</p></section>
<section><h2>Verification and reproducibility</h2>
<p>Six real-array unit tests cover RGB equivalence including boundaries, zero sharpening amount, preservation of constant colors without channel mixing, signed residuals and unclipped overshoot, unit kernel sum and invalid parameters. The experiment checks the two implementations for every amount on both natural images and on the artificially blurred selfie.</p>
<p>Taj Mahal is the supplied course image. The additional photo is my selfie, reused from Part 1.1; its working copy is resized proportionally to width 480 with Lanczos resampling before any experiment. Input hashes, dimensions, all sharpening amounts, clipping fractions and restoration metrics are recorded.</p>
<p><a href="sharpen.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_sharpen.py">Unit tests</a> · <a href="results/metrics.json">Measurements</a> · <a href="results/sharpen-arrays.npz">Raw arrays</a> · <a href="input/source.json">Input source record</a></p>
<h3>What I learned</h3><p>Sharpening changes local contrast rather than restoring a complete scene signal. The useful amount depends on image content: a setting that makes architectural detail clearer can overemphasize skin texture and compression artifacts. Keeping signed, unclipped intermediate arrays separate from display images makes both the mathematics and these limitations visible.</p>
<p class="versions">Python {m['versions']['python']} · NumPy {m['versions']['numpy']} · SciPy {m['versions']['scipy']} · OpenCV {m['versions']['opencv']} · Pillow {m['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 2.1 · Image Sharpening</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
