# Part 2.4: Multiresolution Blending

Three custom composites: Mars/cookie (vertical seam, an edible planet), basketball/orange and kiwi/lime (two independent eleven-vertex irregular masks). Kiwi/lime is the favorite process example. Each pair includes four color modes and a selection rationale.

## Reproduction

Use the existing NumPy, SciPy, OpenCV and Pillow environment. No new dependency is required. From this directory:

```powershell
python -B -m unittest test_blending.BlendingTests -v
python -B run_experiments.py
python -B build_report.py
```

`blending.py` reuses Part 2.3 stacks unchanged; keep that sibling directory present. `prepare_objects.py` prepares retained inputs without downloading: foreground extraction, black/white backgrounds, uniform scale/translation or three-point cut-face affine alignment onto 512x512 canvases. The neighboring whole lime is removed. Source bounds, coordinates and matrices are in `results/metrics.json`.

Basketball alone uses Lab a/b median matching to orange in the central radius-150 region, excluding dark donor pixels (minimum RGB <= .12). L is held fixed in Lab; conversion back to RGB can clip out-of-gamut colors. Its raw-color blend is retained. Hard-cut, feather, selected multiresolution and four color modes all use the SAME selected inputs.

Image sigmas: `[0,2,4,8,16,32]`; mask sigmas: `[1,2,4,8,16,32]`. Full-resolution float64 stacks use encoded RGB and separable spatial filtering with reflected boundaries. No pyramid downsampling is used. White selects A; the coarse residual is included. Signed bands remain unclipped; display exports clip and round to 8-bit. Preparation and Lab conversion are separate from this blending convention.

## Evidence

- `results/metrics.json`: preparation transforms, vertices, chroma offset, schedules, signed-row display scales, reconstruction errors and display-clipping fractions.
- `results/<case>/arrays.npz`: selected A/B, unadjusted A, Laplacian and mask stacks, raw image, weighted source sums, hard/feather baselines, matrices and four color variants. Weighted bands are `masks[...,None]*la` and `(1-masks[...,None])*lb`.
- `results/<case>/band-*.png`: weighted construction bands, centered at gray using one max-absolute scale per row. These differ from filtering the final blend afterward.
- `input/sources.json`: source pages, authors, licenses, modification notes and SHA256 hashes. All six supplied files remain unchanged. Basketball is the official 500px thumbnail; Mars is a Viking photographic mosaic.
- `index.html`: generated English report, coverage checklist, color studies, six mask levels and twelve favorite-process panels. Apple/orange stacks and Figure 3.42 are linked in Part 2.3.

Archives use Git LFS and are optional, never loaded by the page. GitHub Pages serves LFS pointers, so archive links open GitHub; use `git lfs pull` after cloning for actual binary arrays. Local PDFs and preview experiments are excluded from publication.

## Result and licenses

Round geometry and similar colors improve coherence. Blending cannot repair silhouette differences or erase every texture boundary. Reconstruction precision measures numerical consistency, not visual realism. Mask trials vary entire schedules, not just one sigma.

Basketball/orange: freestock.ca and Photography by User: MrX, adapted by James Xie, CC BY-SA 3.0. Kiwi/lime: Andre Karwath aka Aka and Evan-Amos, adapted by James Xie, CC BY-SA 2.5. Mars/cookie: public-domain sources credited to NASA/USGS and Renee Comet/NCI. Full source and license links are in the report and JSON.
