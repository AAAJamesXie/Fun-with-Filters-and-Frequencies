# Part 2.1: Image Sharpening

Taj Mahal is the supplied course image; the additional selfie is copied from Part 1.1. Original files remain unchanged. Uses the already available NumPy, SciPy, OpenCV and Pillow environment.

From this directory:

```powershell
python -B -m unittest test_sharpen.SharpenTests -v
python -B run_experiments.py --sigma 1.5
```

Unsharp masking: `S = I + alpha*(I - G*I)`. The equivalent kernel is `(1+alpha)*delta - alpha*G`. Spatial convolution acts on each RGB channel separately, with same-size output and symmetric boundaries. Float64 computations remain unclipped. The script verifies equivalence before producing display images.

The experiment shows amounts 0, 0.5, 1, 2 and 4 on both images. High-frequency images use the same centered display scale of +/-0.25. Crops use identical coordinates and 2x nearest-neighbor enlargement. A controlled recovery experiment first blurs the resized selfie with sigma 2 and then sharpens it, reporting raw MSE, display-clipped MSE, PSNR and clipping fractions. The displayed recovery example uses alpha 2.

Open `index.html` for the English report. Raw arrays are in `results/sharpen-arrays.npz`, all parameters and measurements in `results/metrics.json`, and source provenance in `input/source.json`. Update `observations.txt` after visual review, then rebuild text alone with `python -B build_report.py`.
