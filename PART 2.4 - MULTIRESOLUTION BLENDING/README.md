# Part 2.4: Multiresolution Blending

Three custom composites: Obama/Trump (vertical step seam), owl/Chelsea (irregular nine-point mask), tiger/selfie (a different irregular nine-point mask). Both-color versions are selected. Each case shows gray, A-only color, B-only color and both-color variants with rationale in the English report.

## Reproduction

Use the existing Python environment with NumPy, SciPy, OpenCV and Pillow. No dependency was added.

```powershell
python -B -m unittest test_blending.BlendingTests -v
python -B run_experiments.py
python -B build_report.py
```

`blending.py` imports the Part 2.3 Gaussian/Laplacian stack implementation. `run_experiments.py` imports the Part 2.2 two-landmark similarity transform and common-support crop. Keep these sibling directories present. The source generator refreshes byte-identical input copies from Parts 1.1/2.2; it does not download images.

All landmark coordinates refer to EXIF-corrected source images prepared at width 512. Alignment resamples only during preparation; every subsequent stack layer retains the full cropped resolution. RGB is encoded, not gamma-linearized. White masks select A. Image sigmas: `[0,2,4,8,16,32]`; mask sigmas: `[1,2,4,8,16,32]`. Blur is spatial and separable with reflected boundaries. No built-in pyramid functions are used. The coarse residual is included in the six-level sum. Clipping occurs only at display export.

## Evidence

- `results/metrics.json`: source sizes, eye points, transforms' crop, polygon vertices, parameter schedules, float64 reconstruction errors, display clipping fractions and archive sizes.
- `results/<case>/arrays.npz`: aligned A/B, their signed Laplacian stacks `la/lb`, mask stack, raw blend, weighted source sums, hard/feather baselines, matrices and four color results. Weighted bands can be regenerated as `masks[...,None]*la` and `(1-masks[...,None])*lb`. Gaussian levels are reverse cumulative sums of the Laplacian levels.
- `results/<case>/band-*.png`: selected signed weighted bands, centered at gray with a shared scale within each three-panel row. These are construction bands, not the Laplacian stack of the final blend.
- `input/sources.json`: provenance, source hashes, modification description and licenses. Original input files are unmodified copies.
- `index.html`: generated report with mandatory-item checklist, source attribution, color studies, best-result process and what was learned.

Raw archives total about 264 MiB and are optional downloads, not loaded by the webpage. The cat/owl process illustrates selected levels 0,2,4 plus all-six-level sums; it is an adaptation of the paper's visualization, not a pixel-identical pyramid reproduction. Apple/orange stacks and Figure 3.42(a-l) are in Part 2.3 and linked from this report.

## Limitations and lesson

Two eye landmarks do not align mouths, fur directions, facial disks or eyeglasses. The cat/owl blend is the favorite. The portrait retains a mouth mismatch, and the tiger/selfie is an exploratory patch with interrupted glasses. Multiresolution blending can smooth frequency-dependent transitions but cannot repair incompatible geometry. Four color modes isolate the contribution of color; three mask schedules explore transition width without claiming an objective winner.

Cat/owl derivatives: Rhododendrites (CC BY-SA 4.0 owl) and Stefan van der Walt (CC0 Chelsea), adapted by James Xie, distributed under CC BY-SA 4.0. Tiger: Steve Wilson, CC BY 2.0, adapted with James Xie's personal selfie; no blanket open-license grant for that selfie. Portrait source photographs are U.S. federal government public-domain works. Full original links and license links are in the report and source JSON.
