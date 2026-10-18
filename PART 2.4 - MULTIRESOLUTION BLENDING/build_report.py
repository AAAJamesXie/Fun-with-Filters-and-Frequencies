"""Build the English coursework report from saved experiment records."""
import json
from html import escape
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent

NOTES = {
    'portraits': {
        'description':'A vertical step mask keeps Obama on the left and Trump on the right. Both eye centers are aligned before selecting the central seam.',
        'result':'The multiscale blend reduces the abrupt color boundary of the hard cut. The mouth, teeth, jaw and hairstyle still disagree: two eye landmarks cannot align every feature or change facial expression. A smoother transition is not proof of geometrically correct alignment.',
        'color':'Both-color is selected to retain the skin and blue clothing cues. Gray reduces some chromatic disagreement, but cannot fix the displaced teeth. Coloring only one source leaves an intentionally unnatural split between a colored half and a gray half.'},
    'cat-owl': {
        'description':'A hand-drawn nine-vertex polygon selects the owl’s image-right eye and surrounding facial disk; the cat supplies the remaining face. This is a localized irregular region, not a straight dividing line.',
        'result':'Favorite result: the green cat eye and nose remain recognizable alongside the orange owl eye. Hard cutting exposes the polygon border. A single broad feather can mix fine fur with the underlying cat eye; the stack blend retains a more decisive owl texture while allowing broad color transitions. Some change in fur direction remains visible below the owl eye.',
        'color':'Both-color is selected because the green-versus-orange iris contrast makes both animals legible. Owl-only color gives a strong selective-color accent, but makes the cat harder to recognize at a glance. Cat-only color suppresses the owl’s distinctive orange iris; gray removes the most helpful color cue.'},
    'selfie-tiger': {
        'description':'A second, independently drawn nine-vertex polygon transfers a tiger-eye and cheek patch into the image-right side of my selfie. The other eye, mouth, clothing and background remain supplied by the selfie.',
        'result':'This deliberately unusual composite exposes a limitation: the stripe boundary still looks like a patch and interrupts the glasses. Feathering broadens the mixture; multiscale blending retains sharper tiger markings, but neither method understands eyeglass continuity or human-versus-tiger anatomy. This is an exploratory result rather than an invisible retouch.',
        'color':'Both-color is retained for the warm tiger fur against the skin. Gray makes the stripes conspicuous but discards their orange identity. Tiger-only color creates a deliberate spotlight effect; selfie-only color makes the inserted patch look desaturated. Color helps the idea, but also makes the patch mismatch easier to see.'}
}


def fig(case, file, caption):
    return f'<figure><a href="results/{case}/{file}.png"><img loading="lazy" src="results/{case}/{file}.png" alt="{escape(caption)}"></a><figcaption>{escape(caption)}</figcaption></figure>'


def grid(case, entries, cls='three-grid'):
    return f'<div class="{cls}">'+''.join(fig(case,*entry) for entry in entries)+'</div>'


def main():
    metrics = json.loads((HERE/'results/metrics.json').read_text(encoding='utf-8'))
    sources = json.loads((HERE/'input/sources.json').read_text(encoding='utf-8'))
    parts = ['''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part 2.4 · Multiresolution Blending</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="page.css"></head><body><main class="shell">
<header class="site-header"><a class="brand" href="../index.html">Fun with Filters<br>and Frequencies!</a><nav class="header-nav" aria-label="Sections"><a href="#method">Method <span>01</span></a><a href="#cases">Three custom blends <span>02</span></a><a href="#process">Inside the favorite <span>03</span></a><a href="#checks">Checks &amp; lessons <span>04</span></a></nav></header>
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p><h1>PART 2.4:<br>MULTIRESOLUTION<br>BLENDING</h1><p class="project-deck">Blend fine detail over a narrow boundary and broad color over a wider one. Three photographic experiments test a straight seam and two irregular regions.</p></section>
<section class="hero-result">''',fig('cat-owl','blend','Favorite: Chelsea + owl · full-color irregular-mask blend'),'''</section>
<section id="method"><h2>One mask, many transition widths</h2><p>I reuse the handwritten Gaussian/Laplacian stacks from <a class="text-link" href="../PART%202.3%20-%20GAUSSIAN%20AND%20LAPLACIAN%20STACKS/index.html">Part 2.3</a>. Every level has the full aligned image resolution. No built-in pyramid function, downsampling or upsampling is used within the stack.</p>
<pre>G_A = Gaussian stack(A)       G_B = Gaussian stack(B)
L_A[l] = G_A[l] - G_A[l+1]   L_B[l] = G_B[l] - G_B[l+1]
L_A[5] = G_A[5]              L_B[5] = G_B[5]
M = Gaussian stack(binary region)
C[l] = M[l] * L_A[l] + (1 - M[l]) * L_B[l]
result = sum(C[l] for l = 0..5)</pre>
<p>White mask pixels select A; black selects B. Image scales are σ = [0, 2, 4, 8, 16, 32] pixels; mask scales are σ = [1, 2, 4, 8, 16, 32]. The finest mask is already softened by σ = 1; the sharp binary mask is retained for the hard-cut baseline. Successive blur kernels use √(σ²<sub>next</sub> − σ²<sub>previous</sub>) with radius ceil(4σ) and reflected boundaries. Discrete, finite kernels approximate the nominal Gaussian scales.</p>
<p>The final coarse residual is essential. Summing all six weighted levels reconstructs the blend directly; stacks need no expansion, and the weights already sum to one, so there is no extra division by two. This adapts the region-weighted algorithm on printed page 230 of Burt &amp; Adelson (1983).</p>
<p>Preparation is separate from the stack: EXIF-correct each photograph, resize it to width 512, map two manually selected eye centers onto shared targets with a similarity transform, then crop to the largest rectangle valid in both warped images. The original files are retained unchanged. Two-point agreement does not guarantee alignment of other features.</p>
<p>All processing uses float64 encoded RGB; this experiment does not linearize gamma or claim radiometric accuracy. Signed bands remain unclipped. Only exported display images are clipped to [0,1] and rounded to 8-bit.</p></section>
<section id="cases"><h2>Three custom blends</h2><p>These are custom composites of existing photographs, not generated scenes. The first uses a straight vertical seam; the next two use different irregular polygons. Each case includes the mandatory color study.</p>''']
    for index,case in enumerate(metrics['cases'],1):
        name = case['id']; note = NOTES[name]
        parts.append(f'<article class="case" id="{name}"><p class="eyebrow">Experiment {index:02d} · {case["mask"]} mask</p><h3>{escape(case["title"])}</h3><p>{note["description"]}</p>')
        parts.append('<details><summary>Original photographs and alignment evidence</summary>')
        parts.append(grid(name,[('original-a','Original A · '+case['a']),('original-b','Original B · '+case['b'])],'two-grid originals'))
        parts.append(grid(name,[('aligned-a','Aligned and cropped A'),('aligned-b','Aligned and cropped B'),('alignment-overlay','50/50 alignment overlay · diagnostic only')]))
        parts.append(f'<p>Common support: {case["size_wh"][0]} × {case["size_wh"][1]} pixels. Crop in the shared canvas: {case["crop_xyxy"]}. Maximum numerical target-eye error: {max(case["alignment_eye_errors"]):.2e} pixels. Manual landmark uncertainty is larger and is not estimated by this number. Landmarks, crop bounds and polygon coordinates are saved in <a class="text-link" href="results/metrics.json">the experiment record</a>; transform matrices are stored in each raw array archive linked below.</p></details>')
        parts.append(grid(name,[('mask','Binary mask · white = A, black = B')],'mask-preview'))
        parts.append(grid(name,[('hard','Hard cut · binary weights at every pixel'),('feather','Single-scale feather · σ = 16 pixels'),('blend','Selected multiresolution blend · both-color')],'three-grid methods'))
        parts.append('<p class="observation">'+note['result']+'</p>')
        parts.append('<h4>Mandatory Bells &amp; Whistles: color</h4><p>The mask, geometry and scale schedule stay fixed. Only input color changes. Gray uses the fixed encoded-RGB weights 0.2126, 0.7152 and 0.0722, repeated into three channels.</p>')
        parts.append(grid(name,[('color-gray','Both inputs grayscale'),('color-a_color','Only A retains color'),('color-b_color','Only B retains color'),('color-both_color','Both inputs retain color · selected')],'four-grid color-study'))
        parts.append('<p>'+note['color']+'</p></article>')
    parts.append('''</section><section id="process"><h2>Inside the favorite: Chelsea + owl</h2><p>The owl is source A and the cat is source B. The same irregular region is blurred separately at each scale. Fine-scale weights remain localized; coarse-scale weights spread farther into the cat image.</p>''')
    parts.append(grid('cat-owl',[(f'mask-{i}',f'M[{i}] · nominal σ = {s:g} px') for i,s in enumerate(metrics['mask_sigmas'])],'six-grid'))
    parts.append('''<h3>Masked frequency contributions</h3><p>Rows below show weighted bands at levels 0, 2 and 4; the last row sums all six levels, including the unshown coarse residual at level 5. Each signed row uses one shared max-absolute scale across its three panels: display = 0.5 + band / (2 × row maximum). Gray means zero, darker values are negative. The bottom row uses ordinary RGB display clipping.</p><p>This is a full-resolution stack adaptation of the contribution visualization in Figure 10 of Burt &amp; Adelson and Figure 3.42 in Szeliski. These are the weighted construction bands M·L<sub>A</sub> and (1−M)·L<sub>B</sub>, not the Laplacian stack obtained by filtering the final image afterward; spatial masking and filtering do not commute.</p>''')
    panels=[]
    letter=iter('abcdefghijkl')
    for level in (0,2,4):
        for key,label in [('a','Owl contribution'),('b','Cat contribution'),('combined','Combined band')]:
            panels.append((f'band-{level}-{key}',f'({next(letter)}) {label} · level {level}'))
    for key,label in [('masked-a','Sum of all owl contributions'),('masked-b','Sum of all cat contributions'),('blend','Final reconstructed blend')]:
        panels.append((key,f'({next(letter)}) {label}'))
    parts.append(grid('cat-owl',panels,'figure-grid'))
    parts.append('''<h3>Mask-scale exploration</h3><p>The image stacks and polygon stay fixed; these trials vary the entire mask schedule. The wider trial changes several scales at once, so it is a comparison of schedules, not an isolated experiment on the finest sigma.</p>''')
    parts.append(grid('cat-owl',[('trial-0','Sharp fine mask · [0, 2, 4, 8, 16, 32]'),('trial-1','Selected · [1, 2, 4, 8, 16, 32]'),('trial-3','Wider transition · [3, 4, 8, 16, 32, 64]')]))
    parts.append('''<p>The sharp trial risks retaining a more abrupt fine-detail border. The wider schedule spreads the owl texture and low-frequency color over more of the cat’s face; it is not automatically better. I select the middle schedule to keep the orange eye localized and recognizable without using an entirely sharp fine mask. These are visual judgments, not an objective quality ranking.</p></section>
<section id="checks"><h2>Checks, coverage and lessons</h2><table><thead><tr><th>Case</th><th>A reconstruction</th><th>B reconstruction</th><th>Left + right</th><th>Display clipping</th></tr></thead><tbody>''')
    for case in metrics['cases']:
        err=case['errors']
        parts.append(f'<tr><td>{escape(case["title"])}</td><td>{err["source_a"]:.2e}</td><td>{err["source_b"]:.2e}</td><td>{err["contributions"]:.2e}</td><td>{100*case["clip_fraction"]:.3f}%</td></tr>')
    parts.append('''</tbody></table><p>Errors are maximum absolute differences in float64 normalized image values, measured before display clipping. “Display clipping” counts RGB channel samples strictly outside [0,1], including tiny rounding excursions. Raw values and contributions are retained in the array archives.</p>
<p>Eight real-array unit tests cover irregular polygon interiors, straight-mask direction, identity blending, all-zero/all-one masks, contribution reconstruction, color selection, channel independence and invalid inputs. They do not replace visual inspection of the actual photographs.</p>
<table><thead><tr><th>Required item</th><th>Evidence</th></tr></thead><tbody><tr><td>Straight seam</td><td>Obama + Trump</td></tr><tr><td>Two irregular pairs</td><td>Chelsea + owl; selfie + tiger</td></tr><tr><td>Gaussian mask stack</td><td>Six full-resolution levels above</td></tr><tr><td>Favorite-result process</td><td>Weighted bands and all-level sums in panels (a)–(l)</td></tr><tr><td>Mandatory color exploration</td><td>Four modes and selection rationale for every pair</td></tr><tr><td>Apple/orange stacks and Figure 3.42</td><td>Completed in linked Part 2.3</td></tr></tbody></table>
<h3>What I learned</h3><p>The most important lesson is that a blend needs different transition widths for different spatial frequencies. A broad feather can soften color while also mixing incompatible detail. A stack lets fine texture switch over a narrow region while broad tones transition farther. Keeping the final residual makes reconstruction exact before display clipping.</p>
<p>Good masks and compatible geometry matter just as much as filtering. The cat/owl eye patch works better than the human/tiger patch because the nearby fur and eye placement are more compatible. The portrait mouth mismatch and broken glasses demonstrate what the algorithm cannot solve: it blends existing pixels, without understanding object shape, expression or occlusion.</p></section>
<section id="reproduce"><h2>Reproduce and inspect</h2><p>No new dependency is required. Run these commands from this part’s directory with the existing NumPy, SciPy, OpenCV and Pillow environment.</p><pre>python -B -m unittest test_blending.BlendingTests -v
python -B run_experiments.py
python -B build_report.py</pre><ul><li><a href="blending.py">Blending implementation</a> · <a href="run_experiments.py">Experiment generator</a> · <a href="test_blending.py">Unit tests</a> · <a href="build_report.py">Report generator</a></li><li><a href="results/metrics.json">Parameters, landmarks, crops and numerical results</a> · <a href="input/sources.json">Source records and original hashes</a> · <a href="README.md">README</a></li>''')
    for case in metrics['cases']:
        parts.append(f'<li><a href="results/{case["id"]}/arrays.npz">{escape(case["title"])} · raw array archive ({case["archive_mb"]:.1f} MiB)</a></li>')
    parts.append('''</ul><p>Archives are optional downloads and are not loaded by this page. Each retains aligned inputs, Laplacian stacks, masks, raw final image and source contributions. All remaining stacks and weighted bands can be regenerated by the code.</p></section><section id="references"><h2>Sources and references</h2><p>Photographs were preserved byte-for-byte, then resized, aligned, cropped, masked and blended for the displayed derivatives. These educational composites are not photographs of real people or animals in these combined forms.</p><ul>''')
    for source in sources['images']:
        title=escape(source['title']);author=escape(source['author']);lic=escape(source['license'])
        link=f'<a href="{escape(source["page"],quote=True)}">{title}</a>' if source.get('page') else title
        license_link=f' · <a href="{escape(source["license_url"],quote=True)}">License</a>' if source.get('license_url') else ''
        parts.append(f'<li>{link} — {author}. {lic}{license_link}. <a href="input/{quote(source["file"])}">Original file</a>.</li>')
    parts.append('''</ul><p>Cat/owl derivatives: Rhododendrites (owl) and Stefan van der Walt (Chelsea), adapted by James Xie; distributed under <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. Tiger derivatives credit Steve Wilson under <a href="https://creativecommons.org/licenses/by/2.0/">CC BY 2.0</a>; the personal selfie carries no blanket open-license grant. No third-party endorsement is implied.</p><ul>
<li>Burt, P. J. &amp; Adelson, E. H. (1983). <a href="../references/burt-adelson-1983.pdf">A Multiresolution Spline With Application to Image Mosaics</a>. ACM TOG 2(4), 217–236. Region-mask algorithm: printed page 230; irregular insertion: Figure 8; contribution visualization: Figure 10.</li>
<li><a href="../references/assignment-2.pdf">SYDE 671 Assignment 2</a>, Part 2.4 and mandatory Bells &amp; Whistles, PDF pages 5–7.</li>
</ul></section><footer class="site-footer"><a href="../index.html">All parts</a><span>SYDE 671 · Assignment 2 · James Xie</span></footer></main></body></html>''')
    (HERE/'index.html').write_text('\n'.join(parts),encoding='utf-8')
    print('Generated index.html')


if __name__ == '__main__':
    main()
