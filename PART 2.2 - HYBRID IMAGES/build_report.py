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
<p class="project-deck">A hybrid combines two pictures. Fine detail is easier to see up close; broad shapes are easier to see from farther away or in a smaller view.</p>
<p class="badge">Includes mandatory Bells &amp; Whistles: color placement</p></section>
<section id="gallery"><h2>01 / Three hybrid images</h2><p>Look at the large pictures, then step back or compare the small versions. The source pictures are shown before alignment; the hybrids use the shared aligned crop. The effect depends on the screen, viewing distance and eyesight. I judge these examples by looking at them.</p>{gallery}</section>
<section id="process"><h2>02 / Full process: Chelsea + Owl</h2>
<p>I chose cat and owl because their eyes can be lined up, while their noses and textures look different. The cat provides broad shapes; the owl provides fine detail. I tried gains from 1 to 2 and chose 1.5 to make the owl clearer. I kept σ low = 10 and σ high = 2.</p>
<h3>Alignment before filtering</h3>{alignment}
<p>I correct photo orientation and resize each source to width 512 with Lanczos, keeping its shape. I mark two eye centers and use them to find the shift, rotation and uniform scale. I map both images onto a 480 × 560 canvas with bilinear interpolation. I then crop the largest rectangle that contains valid pixels from both sources.</p>
<p>The shared crop is {favorite['size_wh'][0]} × {favorite['size_wh'][1]} pixels. The chosen eye coordinates reach their targets with error below {max(favorite['landmark_max_abs_error']):.2e} pixels. This checks the transform calculation, not every facial feature. The cat mouth and owl beak still differ. I follow the two-point alignment idea from the MATLAB starter and implement it in Python.</p>
<h3>Low-pass, high-pass, combine</h3><p class="formula">L = G<sub>σL</sub> * A &nbsp; · &nbsp; H = B − G<sub>σH</sub> * B<br>Hybrid = L + gH</p>
{bands}<p>I apply the Gaussian along x and y, separately for each RGB channel. Its radius is ceil(4σ), with reflected borders. The high-pass result is the original minus its blur. The low band keeps broad shapes and colors; the high band keeps edges and texture. Gain g changes only the high band. I keep the raw values, then clip to 0–1 and round to 8-bit only when saving PNGs. All color comparisons use this same display step.</p>
<details><summary>Hybrid implementation</summary><pre><code>{code}</code></pre></details></section>
<section id="frequency"><h2>03 / Five Fourier views</h2>{fft}
<pre><code>gray = image @ [0.2126, 0.7152, 0.0722]
log_magnitude = np.log(np.maximum(
    np.abs(np.fft.fftshift(np.fft.fft2(gray))), 1e-8))</code></pre>
<p>The five FFT plots show the two aligned inputs, their filtered parts and the raw hybrid. I use the same grayscale weights for all of them. The high-pass FFT uses the signed detail values, not the gray display picture. The hybrid FFT also uses values before clipping. The small floor value avoids log(0).</p>
<p>The center shows the lowest frequencies, including the average brightness (DC). Frequency increases toward the outside, reaching about ±0.5 cycles/pixel on each axis. All plots use the same log range, [{favorite['spectrum_display_range'][0]:.3f}, {favorite['spectrum_display_range'][1]:.3f}], from the pooled 1st and 99.8th percentiles. Low-pass filtering keeps more near the center. High-pass filtering reduces the center and keeps more outer detail. The hybrid contains both. Cropping and border handling mean the patterns are not perfect circles.</p>
<h3>Choosing the cutoffs</h3><p>For a Gaussian, G(f) = exp(−2π²σ²f²). I use the frequency where its response falls to half: f½ = √(2 ln 2)/(2πσ) cycles/pixel. The high-pass response reaches half at the same frequency. Multiplying by image width gives cycles per image width. These are approximate cutoffs, not sharp boundaries. Larger σ low removes more fine detail from the low band. Larger σ high lets broader shapes enter the high band.</p>{params}
<h3>Swapping the favorite pair</h3>{figure(key, 'roles-contact.png', 'Selected versus reversed frequency roles', 'The comparison keeps sigma values, high-band gain and color assignment fixed.', 'contact')}
<p>{escape(observations[key]['roles'])}</p></section>
<section id="color"><h2>04 / Bells &amp; Whistles: where should color go?</h2>
<p class="badge">Mandatory extension · Four controlled variants</p><p>I try four versions: grayscale, color only in the low band, color only in the high band, and color in both. Alignment, crop, filters and gain stay the same. I make grayscale with fixed RGB weights and copy it into three channels. I use RGB values from 0 to 1 without gamma correction.</p>
<h3>Favorite pair, full-size variants</h3>{detailed_colors}{colors}
<p>Color can make one image easier to recognize, but can also make it stay visible at the wrong size. I choose the color setting separately for each pair.</p></section>
<section><h2>Verification, sources and reproduction</h2>
<p>Eight unit tests check alignment, warping, shared cropping, high-pass filtering, reconstruction, grayscale, FFT plots and invalid inputs. The raw files keep aligned images, transforms, filtered parts, color versions, swapped roles and all five FFT results. I also save the parameters, source hashes and clipped fractions.</p>
<p>Derek and Nutmeg are course samples. I chose the other two pairs from openly available photos; I did not take those photos. The downloaded files stay unchanged. I resize, align, crop and filter copies to make the results.</p><ul>{credits}</ul>
<p>The Chelsea + Owl results use <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>, with credit to Rhododendrites and Stefan van der Walt. Source links are above. This license applies to these images, not to unrelated code or other pairs.</p>
<p>Method: Aude Oliva, Antonio Torralba and Philippe G. Schyns, <a href="https://doi.org/10.1145/1141911.1141919">Hybrid images, 2006</a> (<a href="https://stanford.edu/class/ee367/reading/OlivaTorralb_Hybrid_Siggraph06.pdf">paper</a>). I use Gaussian filters as required by the assignment. I also consider alignment, shape and color when choosing the pairs.</p>
<p><a href="hybrid.py">Algorithm source</a> · <a href="run_experiments.py">Experiment source</a> · <a href="test_hybrid.py">Unit tests</a> · <a href="pairs.json">Landmarks and settings</a> · <a href="results/metrics.json">Measurements</a> · <a href="input/sources.json">Source and license records</a></p>
<h3>What I learned</h3><p>I learned that adding the two bands is simple, but making both images recognizable takes more work. Lining up the eyes helps, but does not fix different mouths or face shapes. Filter sizes, gain and color all affect the result. At some middle sizes, both images are still visible.</p>
<p class="versions">Python {metrics['versions']['python']} · NumPy {metrics['versions']['numpy']} · SciPy {metrics['versions']['scipy']} · OpenCV {metrics['versions']['opencv']} · Pillow {metrics['versions']['pillow']}</p></section>
<footer class="site-footer"><a href="../index.html">Assignment overview</a><span>Part 2.2 · Hybrid Images + Mandatory Color</span></footer></main></body></html>'''
    (HERE / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    build_report()
