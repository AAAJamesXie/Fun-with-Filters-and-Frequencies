"""Build an English report for three hybrid images and mandatory color trials."""
from html import escape
import inspect
import json
from pathlib import Path
import hybrid

HERE = Path(__file__).resolve().parent
MODE_NAMES = {'gray': 'Grayscale', 'low_color': 'Color in low frequencies',
              'high_color': 'Color in high frequencies', 'both_color': 'Color in both'}


def figure(case_id, filename, title, caption='', css=''):
    src = f'results/{case_id}/{filename}'
    return (f'<figure class="{css}"><a href="{escape(src)}"><img src="{escape(src)}" '
            f'alt="{escape(title)}" loading="lazy"></a><figcaption>{escape(title)}'
            f'<span>{escape(caption)}</span></figcaption></figure>')


def build_report():
    metrics = json.loads((HERE / 'results/metrics.json').read_text(encoding='utf-8'))
    observations = json.loads((HERE / 'observations.json').read_text(encoding='utf-8'))
    sources = json.loads((HERE / 'input/sources.json').read_text(encoding='utf-8'))
    favorite = next(case for case in metrics['cases'] if case['id'] == metrics['favorite'])
    gallery = ''
    params = ''
    colors = ''
    for case in metrics['cases']:
        key = case['id']; note = observations[key]
        gallery += f'<h3>{escape(case["title"])}</h3><div class="triple">'
        gallery += figure(key, 'original-low.png', f'Low-frequency source: {case["low"]}', 'Prepared source before alignment')
        gallery += figure(key, 'original-high.png', f'High-frequency source: {case["high"]}', 'Prepared source before alignment')
        gallery += figure(key, 'hybrid-selected.png', 'Final hybrid', MODE_NAMES[case['mode']]) + '</div>'
        gallery += figure(key, 'scale-strip.png', 'The same hybrid at five display widths', 'Click to inspect at full resolution. Downsampling is a viewing-scale aid, not a calibrated distance.', 'wide')
        gallery += f'<p>{escape(note["result"])}</p>'
        gallery += (f'<p class="measurement">Aligned crop: {case["size_wh"][0]} × {case["size_wh"][1]} · '
                    f'σ low = {case["sigma_low"]:g} px · σ high = {case["sigma_high"]:g} px · high-band gain = {case["gain"]:g}. '
                    f'Before display clipping, {case["outside_channel_fraction"]:.2%} of RGB channel samples lie outside [0, 1].</p>')
        cutoff = case['cutoff_half_gain_cycles_per_width']
        params += f'<h3>{escape(case["title"])}</h3>'
        params += figure(key, 'parameter-contact.png', 'Cutoff trials', 'Each tile shows a large and small version. Gain and color mode stay fixed within this contact sheet.', 'contact')
        params += f'<p>{escape(note["parameters"])}</p><p>Selected approximate half-amplitude cutoffs: low = {cutoff["low"]:.2f}, high = {cutoff["high"]:.2f} cycles per aligned image width.</p>'
        colors += f'<h3>{escape(case["title"])}</h3>'
        colors += figure(key, 'color-contact.png', 'Four color assignments', 'Order: grayscale, low-only color, high-only color, both color. Small previews use the same hybrid downsampled.', 'contact')
        colors += f'<p>{escape(note["color"])}</p>'
    key = favorite['id']
    alignment = '<div class="pair">' + figure(key, 'landmarks-low.png', 'Chelsea eye landmarks') + figure(key, 'landmarks-high.png', 'Owl eye landmarks') + '</div>'
    alignment += '<div class="triple">' + figure(key, 'aligned-low.png', 'Aligned Chelsea') + figure(key, 'aligned-high.png', 'Aligned owl')
    alignment += figure(key, 'alignment-overlay.png', '50/50 overlay for alignment', 'This ordinary blend is an alignment diagnostic, not the hybrid result.') + '</div>'
    bands = '<div class="triple">' + figure(key, 'filtered-low.png', 'Low-pass Chelsea')
    bands += figure(key, 'filtered-high.png', 'Signed high-pass owl', 'Display only: zero is middle gray; shared signed scale ±0.30. This panel shows H before the 1.5× combination gain.')
    bands += figure(key, 'hybrid-selected.png', 'Low + high = hybrid') + '</div>'
    fft = '<div class="triple fft-grid">' + ''.join(figure(key, 'fft-' + file + '.png', title) for file, title in [
        ('input-low', 'FFT: aligned low source'), ('input-high', 'FFT: aligned high source'),
        ('filtered-low', 'FFT: low-pass result'), ('filtered-high', 'FFT: signed high-pass result'), ('hybrid', 'FFT: raw hybrid')]) + '</div>'
    detailed_colors = '<div class="four-grid">'
    for mode in hybrid.MODES:
        detailed_colors += figure(key, f'hybrid-{mode}.png', MODE_NAMES[mode])
    detailed_colors += '</div><div class="four-grid far-grid">'
    for mode in hybrid.MODES:
        detailed_colors += figure(key, f'far-{mode}.png', 'Small view · ' + MODE_NAMES[mode])
    detailed_colors += '</div>'
    credits = ''
    for source in sources['images']:
        if source.get('status'): continue
        title = f'<a href="{escape(source["page"])}">{escape(source["title"])}</a>' if source['page'] else escape(source['title'])
        license_text = escape(source['license'])
        if source.get('license_url'): license_text = f'<a href="{escape(source["license_url"])}">{license_text}</a>'
        credits += f'<li>{title} — {escape(source["author"])}. {license_text}.</li>'
    code = escape(inspect.getsource(hybrid.make_hybrid))
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part 2.2 · Hybrid Images</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="page.css"></head>
<body><main class="shell"><header class="site-header"><a class="brand" href="../index.html">Fun with Filters<br>and Frequencies!</a>
<nav class="header-nav"><a href="#gallery">Three hybrids <span>01</span></a><a href="#process">Full process <span>02</span></a><a href="#frequency">Frequency analysis <span>03</span></a><a href="#color">Mandatory color <span>04</span></a></nav></header>
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p><h1>PART 2.2:<br>HYBRID<br>IMAGES</h1>
<p class="project-deck">One picture, two spatial scales. Fine detail carries one identity up close; broader structure becomes easier to see as the picture gets smaller or farther away.</p>
<p class="badge">Includes mandatory Bells &amp; Whistles: color placement</p></section>
<section id="gallery"><h2>01 / Three hybrid images</h2><p>View the larger versions up close, then step back or compare the smaller versions. The sources below are before alignment; the final images use the aligned common crop. Viewing distance, screen density and eyesight affect how clearly the interpretations separate. These are three constructed examples, not results from a perceptual user study.</p>{gallery}</section>
<section id="process"><h2>02 / Full process: Chelsea + Owl</h2>
<p>I selected this self-chosen pair because the eyes provide corresponding landmarks while the owl's beak and feather structure differ clearly from the cat's nose and fur. The cat supplies the low band and the owl the high band. After comparing gains from 1 to 2, I increased high-band gain from the trial value of 1 to 1.5 for more visible owl detail, while keeping σ low = 10 and σ high = 2 fixed.</p>
<h3>Alignment before filtering</h3>{alignment}
<p>Each source is EXIF-corrected and resized proportionally to width 512 with Lanczos resampling. I manually mark two eye centers in these prepared images and solve a two-point similarity transform for translation, rotation and uniform scale. Both sources are warped with bilinear interpolation to a shared 480 × 560 canvas. A separately warped support mask identifies valid source pixels; the largest rectangular region valid in both images is cropped before filtering.</p>
<p>For this pair, the common crop is {favorite['size_wh'][0]} × {favorite['size_wh'][1]} pixels. The transform maps the chosen eye coordinates to their common targets with residual below {max(favorite['landmark_max_abs_error']):.2e} pixels. This verifies the coordinate calculation, not the anatomical accuracy of manually selected landmarks: the cat's mouth and the owl's beak do not fully coincide. No face recognition or nonrigid face morph is used. The method follows the two-point alignment principle in the supplied MATLAB starter, implemented in Python.</p>
<h3>Low-pass, high-pass, combine</h3><p class="formula">L = G<sub>σL</sub> * A &nbsp; · &nbsp; H = B − G<sub>σH</sub> * B<br>Hybrid = L + gH</p>
{bands}<p>The normalized Gaussian is applied separably along x and y, independently for each RGB channel, using radius ceil(4σ) and symmetric boundaries. The high-pass filter is the impulse minus the Gaussian. The low band retains broad appearance, while the signed high band carries edges and texture. The gain g scales only the high band; the raw result is preserved without clipping. PNG output clips to [0, 1] and rounds to uint8, and this display conversion is identical for all color comparisons.</p>
<details><summary>Hybrid implementation</summary><pre><code>{code}</code></pre></details></section>
<section id="frequency"><h2>03 / Five Fourier views</h2>{fft}
<pre><code>gray = image @ [0.2126, 0.7152, 0.0722]
log_magnitude = np.log(np.maximum(
    np.abs(np.fft.fftshift(np.fft.fft2(gray))), 1e-8))</code></pre>
<p>These are transforms of the two aligned inputs, the two filtered components and the raw hybrid. The inputs use the same grayscale convention as the hybrid calculation. Crucially, the high-pass FFT uses the signed high-frequency array, not its middle-gray visualization; the final FFT uses the unclipped hybrid. The numerical floor prevents log(0).</p>
<p>DC is centered. Frequency runs approximately from −0.5 to +0.5 cycles/pixel along each axis; moving away from the center increases spatial frequency. All five plots share a log display range of [{favorite['spectrum_display_range'][0]:.3f}, {favorite['spectrum_display_range'][1]:.3f}], selected from pooled 1st and 99.8th percentiles. Values outside that range are clipped only for visualization. The low-pass result concentrates energy near the center; the high-pass result suppresses the central low frequencies while retaining more outer detail. The hybrid carries both bands. Finite cropping, boundary extension and the logarithmic display leave leakage and residual structure; an ideal perfectly circular band separation is not expected.</p>
<h3>Choosing the cutoffs</h3><p>For a continuous Gaussian, G(f) = exp(−2π²σ²f²). Following the paper's half-amplitude convention, the approximate cutoff is f½ = √(2 ln 2)/(2πσ), in cycles/pixel; the complementary high-pass reaches half gain at the same frequency. Multiplying by the aligned crop width expresses it in cycles per image width. The finite sampled kernels approximate these cutoffs and do not have a hard frequency boundary. Increasing σ low lowers the low-pass cutoff; increasing σ high lowers the complementary high-pass cutoff and admits broader structures into the high band.</p>{params}
<h3>Swapping the favorite pair</h3>{figure(key, 'roles-contact.png', 'Selected versus reversed frequency roles', 'The comparison keeps sigma values, high-band gain and color assignment fixed.', 'contact')}
<p>{escape(observations[key]['roles'])}</p></section>
<section id="color"><h2>04 / Bells &amp; Whistles: where should color go?</h2>
<p class="badge">Mandatory extension · Four controlled variants</p><p>I compare grayscale, low-frequency color only, high-frequency color only, and color in both. The transforms, crop, filter parameters and high-band gain are fixed within each pair; only the channels converted to grayscale change. Grayscale uses fixed RGB weights and is replicated into three channels before combining. Processing uses normalized encoded RGB, without gamma linearization.</p>
<h3>Favorite pair, full-size variants</h3>{detailed_colors}{colors}
<p>Color can strengthen broad grouping cues or add useful detail, but can also make one source persist at the wrong viewing scale. No single color assignment is best for every pair. The comparisons above support the choices rather than treating color as an automatic improvement.</p></section>
<section><h2>Verification, sources and reproduction</h2>
<p>Eight real-array unit tests cover similarity transforms, identity warping, common-support cropping, constant-image high-pass rejection, matching-band reconstruction, equal-channel grayscale, centered finite spectra and invalid inputs. Raw arrays preserve the aligned sources, transforms, selected components, every color variant, role reversal and five log spectra. Parameters, source hashes, cutoff estimates and display clipping fractions are recorded for each case.</p>
<p>The course samples provide Derek + Nutmeg. The two additional pairs are my own selection of openly available photographs, not photographs I took. All downloaded originals remain unchanged. Derived images are resized, aligned, cropped, converted, filtered and combined as described above.</p><ul>{credits}</ul>
<p>The Chelsea + Owl derived images are shared under <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>, with credit to Rhododendrites and Stefan van der Walt and the source links above. This image license does not change the license of unrelated project code or the other cases.</p>
<p>Method reference: Aude Oliva, Antonio Torralba and Philippe G. Schyns, <a href="https://doi.org/10.1145/1141911.1141919">Hybrid images, SIGGRAPH / ACM TOG, 2006</a> (<a href="https://stanford.edu/class/ee367/reading/OlivaTorralb_Hybrid_Siggraph06.pdf">paper</a>). This project implements the assignment's spatial Gaussian version and uses the paper's alignment, perceptual-grouping and color considerations.</p>
<p><a href="hybrid.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_hybrid.py">Unit tests</a> · <a href="pairs.json">Landmarks and settings</a> · <a href="results/metrics.json">Measurements</a> · <a href="input/sources.json">Source and license records</a></p>
<h3>What I learned</h3><p>Adding a low band to a high band is easy; creating two coherent interpretations depends on matching the geometry and controlling how much structure survives in each band. A similarity transform aligns eyes but cannot make different mouths or muzzles identical. Color and gain are useful controls, and intermediate-size ambiguity remains a meaningful limitation rather than a numerical filtering failure.</p>
<p class="versions">Python {metrics['versions']['python']} · NumPy {metrics['versions']['numpy']} · SciPy {metrics['versions']['scipy']} · OpenCV {metrics['versions']['opencv']} · Pillow {metrics['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 2.2 · Hybrid Images + Mandatory Color</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
