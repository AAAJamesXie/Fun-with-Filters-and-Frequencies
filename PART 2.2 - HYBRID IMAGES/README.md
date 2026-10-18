# Part 2.2: Hybrid Images + mandatory color experiment

Three pairs: course-provided Derek + Nutmeg; self-selected Obama + Trump official portraits; Chelsea + a frontal owl. Input originals, license/source records, and all transformations are documented in `input/sources.json` and the report. Earlier tiger candidates and outputs are retained as unused history. No dependencies are installed.

From this directory, using the existing NumPy, SciPy, OpenCV and Pillow environment:

```powershell
python -B -m unittest test_hybrid.HybridTests -v
python -B run_experiments.py
python -B build_report.py
```

Open `index.html`. `pairs.json` stores manually selected eye landmarks on prepared width-512 images, output-canvas targets, frequency roles, sigmas, gain and chosen color mode. Bilinear similarity warps are cropped to the largest all-valid common rectangle, before filtering. This avoids artificial black padding entering the image bands. Two-point coordinate error is a transform consistency check, not a measured guarantee of anatomical alignment.

Normalized spatial Gaussian filters use a radius of ceil(4 sigma), applied separably to spatial axes with symmetric extension. High-pass is original minus Gaussian blur. Combined arrays remain signed/unclipped until PNG display. Approximate half-amplitude cutoff is sqrt(2 ln 2)/(2 pi sigma), also recorded in cycles per cropped image width. Sigmas refer to aligned/cropped pixels; finite Gaussian support makes this an approximation.

All three pairs have cutoff sweeps, frequency-role reversal and four color variants. Full color/gray processing and gain stay fixed within the relevant comparisons. Favorite Chelsea + Owl uses sigma low 10, sigma high 2, and high-band gain 1.5 (increased from the experiment's 1). It has original/marked/aligned inputs, both filtered bands, the raw hybrid and all five Fourier log-magnitude plots in the webpage. Spectra are computed before clipping or display offsets, with a shared visualization range. Small views are antialiased downsampling of the same displayed hybrid, not a calibrated simulation of physical viewing distance.

The cat/owl derived images are shared under CC BY-SA 4.0, with attribution to Rhododendrites (owl, CC BY-SA 4.0) and Stefan van der Walt (Chelsea, CC0). Source and license links are in the report and `input/sources.json`. This derived-image license does not relicense unrelated code or other cases.

`results/metrics.json` records parameters, input SHA-256 hashes, transforms' landmark residuals, common crops, clipping fractions and display ranges. Each case's `arrays.npz` stores raw selected components, transforms, all four color hybrids and five spectra. PNGs are display-only. `observations.json` contains the visual choices and limitations; changing parameters should be followed by a fresh visual review before rebuilding the report.
