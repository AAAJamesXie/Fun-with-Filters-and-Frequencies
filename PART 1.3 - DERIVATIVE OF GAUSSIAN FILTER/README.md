# Part 1.3: Derivative of Gaussian + mandatory gradient orientation

Uses the same modern 512x512 cameraman input and attribution as Part 1.2. No original files are modified. NumPy, SciPy, Pillow and OpenCV are already available; nothing is installed.

From this directory:

```powershell
python -B -m unittest test_dog.DogTests -v
python -B run_experiments.py --sigma 2 --threshold 0.04
```

The Gaussian is the outer product of `cv2.getGaussianKernel` with its transpose, using radius `ceil(3*sigma)`. DoG kernels use full convolution with `[1,-1]` and its transpose. Both image routes use `same` output and symmetric boundaries. Comparisons report full-image and interior errors separately; the conservative interior margin is Gaussian radius + 1.

Default experiments compare sigma 1, 2 and 3; show a fixed-threshold comparison at 0.20 with the Part 1.2 baseline; and sweep smoothed thresholds from 0.02 through 0.10. PNG display mappings are recorded in `results/metrics.json`; all thresholding operates on raw float64 magnitudes. `observations.txt` records the qualitative choice after reviewing the generated images. Rebuild text alone with `python -B build_report.py`.

Mandatory Bells & Whistles: manual gradient angle in [0,2pi), clockwise from +x in image coordinates. A range-reduced 24-term alternating arctangent series and manual quadrant reconstruction avoid all built-in angle functions. HSV hue represents direction, saturation is 1, and value is magnitude divided by a shared 0.15 display scale, clipped to [0,1]. Zero strength appears black. A matching color wheel is included. Raw and smoothed directions are both visualized.

Open `index.html` for the English report. `results/dog-arrays.npz` contains raw filters, both derivative routes, magnitudes, directions and selected edges. `results/metrics.json` records errors, parameters, display scales, source hash and software versions. `test_dog.py` contains seven real-array unit tests.
