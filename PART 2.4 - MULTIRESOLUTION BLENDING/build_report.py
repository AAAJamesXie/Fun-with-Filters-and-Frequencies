"""Build the English coursework report from saved experiment records."""
import json
from html import escape
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent

NOTES = {'mars-cookie': {'description': 'I put Mars on the left and a chocolate-chip cookie on the right with a vertical mask. Both are round and brown, so I tried making an edible planet. The Mars source is a Viking photo mosaic.', 'result': 'The hard cut has a clear middle seam. Feathering softens it but mixes the details over a wide area. The stack blend keeps craters and cookie texture clearer while smoothing the color change. The outer shapes still do not match perfectly.', 'color': 'I choose color in both because the warm tones help Mars and cookie fit together. Grayscale keeps the texture but looks less like food. Color in only one source leaves an obvious gray half.'}, 'orange-basketball': {'description': 'I use an eleven-point irregular mask to put basketball texture into an orange. Basketball is A and orange is B. Their round shapes and bumpy surfaces are similar. I adjust the pinker ball color in Lab before comparing methods.', 'result': 'All three methods use the same adjusted A and unchanged B. The hard cut shows the mask border. Feathering makes the ball lines softer. The stack keeps the lines clearer, though the texture boundary is still visible. The color improvement comes from a separate preparation step.', 'color': 'I choose color in both so the orange still looks like fruit. Color in only one source makes the other area gray. Grayscale hides some color differences but loses the orange color. All four versions start with the same adjusted inputs.'}, 'kiwi-lime': {'description': 'I use a different eleven-point mask to put kiwi seeds inside a lime and keep its rind. I align the cut faces with three points and remove the whole lime beside the cut one.', 'result': 'This is my favorite. The green flesh and lime rind make the mix easy to understand. The hard cut shows the polygon edge. Feathering weakens the seed ring. The stack keeps the seeds clearer and softens the color change. Some texture change is still visible.', 'color': 'I choose color in both because the green tones help the fruits match. Grayscale loses that link. Kiwi-only color makes the insertion stand out; lime-only color makes it gray. I do not adjust the colors for this pair.'}}


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
<section class="project-hero"><p class="eyebrow">SYDE 671 · Assignment 2 · James Xie</p><h1>PART 2.4:<br>MULTIRESOLUTION<br>BLENDING</h1><p class="project-deck">I blend fine detail over a narrow area and broad colors over a wider area. I try one straight seam and two irregular masks.</p></section>
<section class="hero-result">''',fig('mars-cookie','blend','Mars Cookie: an edible planet · vertical multiresolution seam'),'''</section>
<section id="method"><h2>One mask, many transition widths</h2><p>I reuse my Gaussian and Laplacian stacks from <a class="text-link" href="../PART%202.3%20-%20GAUSSIAN%20AND%20LAPLACIAN%20STACKS/index.html">Part 2.3</a>. Every layer keeps the full image size. I do not use built-in pyramid functions or resize layers.</p>
<pre>G_A = Gaussian stack(A)       G_B = Gaussian stack(B)
L_A[l] = G_A[l] - G_A[l+1]   L_B[l] = G_B[l] - G_B[l+1]
L_A[5] = G_A[5]              L_B[5] = G_B[5]
M = Gaussian stack(binary region)
C[l] = M[l] * L_A[l] + (1 - M[l]) * L_B[l]
result = sum(C[l] for l = 0..5)</pre>
<p>White selects A and black selects B. The image scales are σ = [0, 2, 4, 8, 16, 32]; the mask scales are [1, 2, 4, 8, 16, 32] pixels. The finest mask already has a small blur of σ = 1. The hard-cut comparison uses the original sharp mask. To reach the next blur level, I apply σ = √(σ²<sub>next</sub> − σ²<sub>previous</sub>), with radius ceil(4σ) and reflected borders. Finite filters only approximate these scales.</p>
<p>I keep the last broad layer and add all six weighted layers to get the result. No layer expansion is needed. The two weights add to one, so I do not divide by two again. This follows the mask method on printed page 230 of Burt &amp; Adelson (1983).</p>
<p>I prepare the images before blending. Mars and cookie use black backgrounds; basketball and orange use white. I find their outer shapes, slightly soften the edges, and center them on 512 × 512 canvases with uniform scaling. For kiwi and lime, I use three points to align the cut faces with an affine transform. I also remove the neighboring whole lime. The source files stay unchanged. These steps and the basketball color adjustment affect the result separately from blending.</p>
<p>The stacks use float64 RGB values without gamma correction. I keep negative values in the detail layers. Only the display images are clipped to 0–1 and rounded to 8-bit.</p></section>
<section id="cases"><h2>Three custom blends</h2><p>I combine existing photos to make three imaginary objects. The first has a straight vertical seam. The other two use different irregular masks. Each includes the required color comparison.</p>''']
    for index,case in enumerate(metrics['cases'],1):
        name = case['id']; note = NOTES[name]
        parts.append(f'<article class="case" id="{name}"><p class="eyebrow">Experiment {index:02d} · {case["mask"]} mask</p><h3>{escape(case["title"])}</h3><p>{note["description"]}</p>')
        parts.append('<details><summary>Original photographs and alignment evidence</summary>')
        parts.append(grid(name,[('original-a','Supplied source A · '+case['a']),('original-b','Supplied source B · '+case['b'])],'two-grid originals'))
        parts.append(grid(name,[('aligned-a','Prepared A · before optional chroma matching'),('aligned-b','Prepared B'),('alignment-overlay','50/50 alignment overlay · diagnostic only')]))
        parts.append(f'<p>Prepared size: {case["size_wh"][0]} × {case["size_wh"][1]} pixels. The points, object bounds, transforms and mask vertices are in <a class="text-link" href="results/metrics.json">the experiment record</a>. The overlay shows how the selected inputs line up. A small calculation error does not tell us how well the shapes match.</p></details>')
        if case['chroma_shift_ab'] is not None:
            parts.append('<h4>Separate preprocessing: basketball color</h4>')
            parts.append(grid(name,[('aligned-a','A before chroma matching'),('prepared-a','Selected A after chroma matching'),('blend-original','Multiresolution blend without chroma matching')]))
            parts.append(f'<p>I adjust the Lab color channels a/b by {case["chroma_shift_ab"]} before blending. This offset is the difference between the median colors of A and B in a central circle of radius 150. I exclude dark A pixels with minimum RGB ≤ 0.12. Lab brightness L stays fixed, though conversion back to RGB can clip colors outside its range. The adjusted and unadjusted blends use the same shapes, masks and scales.</p>')
        parts.append(grid(name,[('mask','Binary mask · white = A, black = B')],'mask-preview'))
        parts.append(grid(name,[('hard','Hard cut · binary weights at every pixel'),('feather','Single-scale feather · σ = 16 pixels'),('blend','Selected multiresolution blend · both-color')],'three-grid methods'))
        parts.append('<p class="observation">'+note['result']+'</p>')
        parts.append('<h4>Mandatory Bells &amp; Whistles: color</h4><p>I keep the mask, alignment and blur scales fixed and change only the color setting. Grayscale uses RGB weights 0.2126, 0.7152 and 0.0722, copied into three channels.</p>')
        parts.append(grid(name,[('color-gray','Both inputs grayscale'),('color-a_color','Only A retains color'),('color-b_color','Only B retains color'),('color-both_color','Both inputs retain color · selected')],'four-grid color-study'))
        parts.append('<p>'+note['color']+'</p></article>')
    parts.append('''</section><section id="process"><h2>Inside the favorite: kiwi + lime</h2><p>Kiwi is A and lime is B. I blur the same irregular mask at each scale. Fine-detail layers use a narrow transition; broad layers spread the transition farther into the lime.</p>''')
    parts.append(grid('kiwi-lime',[(f'mask-{i}',f'M[{i}] · nominal σ = {s:g} px') for i,s in enumerate(metrics['mask_sigmas'])],'six-grid'))
    parts.append('''<h3>Masked frequency contributions</h3><p>The first three rows show weighted detail layers 0, 2 and 4. The last row adds all six layers, including broad layer 5. Each detail row shares one display scale: 0.5 + value / (2 × row maximum absolute value). Gray means zero and darker means negative. The bottom row uses normal RGB display.</p><p>I follow the contribution layout in Figure 10 of Burt &amp; Adelson and Figure 3.42 in Szeliski, using full-size stacks. These panels show M·L<sub>A</sub> and (1−M)·L<sub>B</sub>, the weighted layers used to build the image. They are not the layers found by filtering the final image. Masking before filtering can give a different result from masking afterward.</p>''')
    panels=[]
    letter=iter('abcdefghijkl')
    for level in (0,2,4):
        for key,label in [('a','Kiwi contribution'),('b','Lime contribution'),('combined','Combined band')]:
            panels.append((f'band-{level}-{key}',f'({next(letter)}) {label} · level {level}'))
    for key,label in [('masked-a','Sum of all kiwi contributions'),('masked-b','Sum of all lime contributions'),('blend','Final reconstructed blend')]:
        panels.append((key,f'({next(letter)}) {label}'))
    parts.append(grid('kiwi-lime',panels,'figure-grid'))
    parts.append('''<h3>Mask-scale exploration</h3><p>I keep the image stacks and polygon fixed and try three sets of mask blur scales. The widest option changes several scales, so this is a comparison of whole settings rather than one sigma.</p>''')
    parts.append(grid('kiwi-lime',[('trial-0','Sharp fine mask · [0, 2, 4, 8, 16, 32]'),('trial-1','Selected · [1, 2, 4, 8, 16, 32]'),('trial-3','Wider transition · [3, 4, 8, 16, 32, 64]')]))
    parts.append('''<p>The sharpest setting can leave a stronger detail border. The widest setting spreads kiwi texture and color over more of the lime. I choose the middle setting because it keeps the seed ring clear with a softer boundary. This is my visual choice, not an accuracy score.</p></section>
<section id="checks"><h2>Checks, coverage and lessons</h2><table><thead><tr><th>Case</th><th>A reconstruction</th><th>B reconstruction</th><th>Left + right</th><th>Display clipping</th></tr></thead><tbody>''')
    for case in metrics['cases']:
        err=case['errors']
        parts.append(f'<tr><td>{escape(case["title"])}</td><td>{err["source_a"]:.2e}</td><td>{err["source_b"]:.2e}</td><td>{err["contributions"]:.2e}</td><td>{100*case["clip_fraction"]:.3f}%</td></tr>')
    parts.append('''</tbody></table><p>The errors are the largest absolute differences in the raw float64 values before clipping. Display clipping counts individual RGB values outside 0–1, including tiny rounding errors. The archives keep the raw values and both source contributions.</p>
<p>Eight unit tests check polygon masks, straight masks, identical images, masks that select one source, reconstruction, color modes, separate channels and invalid inputs. I also inspect the actual pictures.</p>
<table><thead><tr><th>Required item</th><th>Evidence</th></tr></thead><tbody><tr><td>Straight seam</td><td>Mars + cookie</td></tr><tr><td>Two irregular pairs</td><td>Basketball + orange; kiwi + lime</td></tr><tr><td>Creative own idea</td><td>Mars Cookie: an edible planet</td></tr><tr><td>Gaussian mask stack</td><td>Six full-resolution levels above</td></tr><tr><td>Favorite-result process</td><td>Weighted bands and all-level sums in panels (a)–(l)</td></tr><tr><td>Mandatory color exploration</td><td>Four modes and selection rationale for every pair</td></tr><tr><td>Apple/orange stacks and Figure 3.42</td><td>Completed in linked Part 2.3</td></tr></tbody></table>
<h3>What I learned</h3><p>I learned that fine detail and broad color need different transition widths. A wide feather can blur details from both sources together. The stack keeps a narrow change for detail and a wider change for color. Keeping the last broad layer lets all layers add up correctly.</p>
<p>The mask and shape match matter as much as filtering. Round objects with similar colors work well here. The lime rind helps the kiwi fit, but the basketball texture boundary is still visible. I show color adjustment separately and keep it fixed when comparing methods. A tiny calculation error does not mean the blend looks natural.</p></section>
<section id="reproduce"><h2>Reproduce and inspect</h2><p>I use the existing NumPy, SciPy, OpenCV and Pillow environment. Run these commands from this part folder:</p><pre>python -B -m unittest test_blending.BlendingTests -v
python -B run_experiments.py
python -B build_report.py</pre><ul><li><a href="blending.py">Blending implementation</a> · <a href="run_experiments.py">Experiment generator</a> · <a href="prepare_objects.py">Object preparation</a> · <a href="test_blending.py">Unit tests</a> · <a href="build_report.py">Report generator</a></li><li><a href="results/metrics.json">Parameters, preparation transforms, masks and numerical results</a> · <a href="input/sources.json">Source records and original hashes</a> · <a href="README.md">README</a></li>''')
    for case in metrics['cases']:
        parts.append(f'<li><a href="https://github.com/AAAJamesXie/Fun-with-Filters-and-Frequencies/blob/main/PART%202.4%20-%20MULTIRESOLUTION%20BLENDING/results/{case["id"]}/arrays.npz">{escape(case["title"])} · raw array archive on GitHub / LFS ({case["archive_mb"]:.1f} MiB)</a></li>')
    parts.append('''</ul><p>The page does not load the optional array archives. Their links open GitHub because Pages only serves LFS pointers. Use Git LFS to download the actual files. Each archive keeps the prepared inputs, Laplacian layers, masks, raw result and source contributions. The code can rebuild the other layers.</p></section><section id="references"><h2>Sources and references</h2><p>All six source files stay unchanged. I prepare backgrounds, align objects, mask and blend copies. I also adjust the basketball color as shown above. The basketball source is the official 500px thumbnail. Mars is a mosaic of real Viking spacecraft photos. The combined objects are imaginary.</p><ul>''')
    for source in sources['images']:
        title=escape(source['title']);author=escape(source.get('attribution',source['author']));lic=escape(source['license'])
        link=f'<a href="{escape(source["page"],quote=True)}">{title}</a>' if source.get('page') else title
        license_link=f' · <a href="{escape(source["license_url"],quote=True)}">License</a>' if source.get('license_url') else ''
        parts.append(f'<li>{link} — {author}. {lic}{license_link}. <a href="input/{quote(source["file"])}">Supplied file</a>.</li>')
    parts.append('''</ul><p>Basketball/orange derivatives: freestock.ca and Photography by User: MrX, adapted by James Xie; <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>. Kiwi/lime derivatives: André Karwath aka Aka and Evan-Amos, adapted by James Xie; <a href="https://creativecommons.org/licenses/by-sa/2.5/">CC BY-SA 2.5</a>. Mars/cookie use public-domain sources credited to NASA/USGS and Renee Comet/NCI. No third-party endorsement is implied.</p><ul>
<li>Burt, P. J. &amp; Adelson, E. H. (1983). <a href="../references/burt-adelson-1983.pdf">A Multiresolution Spline With Application to Image Mosaics</a>. ACM TOG 2(4), 217–236. Region-mask algorithm: printed page 230; irregular insertion: Figure 8; contribution visualization: Figure 10.</li>
<li><a href="../references/assignment-2.pdf">SYDE 671 Assignment 2</a>, Part 2.4 and mandatory Bells &amp; Whistles, PDF pages 5–7.</li>
</ul></section><footer class="site-footer"><a href="../index.html">All parts</a><span>SYDE 671 · Assignment 2 · James Xie</span></footer></main></body></html>''')
    (HERE/'index.html').write_text('\n'.join(parts),encoding='utf-8')
    print('Generated index.html')


if __name__ == '__main__':
    main()
