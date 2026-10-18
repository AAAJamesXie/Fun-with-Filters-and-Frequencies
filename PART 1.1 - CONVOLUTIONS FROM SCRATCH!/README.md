# Part 1.1: Convolutions from Scratch!

Two handwritten NumPy implementations, zero padding, a 9x9 normalized box filter, and horizontal/vertical finite differences on a selfie. SciPy is used only as the comparison reference. Pillow handles image I/O and preparation.

From this directory, with the existing NumPy, SciPy and Pillow environment:

```powershell
python -B -m unittest test_convolution.ConvolutionTests -v
python -B run_experiments.py
```

The experiment defaults to `input/selfie.jpg`, width 480 and three timed repetitions. It preserves the source, converts to grayscale and scales proportionally. All three methods use identical float64 data and `same` / zero-fill boundaries. Timing includes padding/allocation and excludes preparation and I/O. No dependencies are installed by these scripts.

Open `index.html` to view the English report. `results/metrics.json` contains measured times, errors, parameters, versions and the input SHA-256. `results/convolution-arrays.npz` preserves signed floating-point results; PNGs are visualization only. Both derivative directions share a zero-centered grayscale display scale.

Reuse: normalization and saving patterns from Assignment 1 `part-two/colorize.py`; convolution-only timing patterned after `part-two/run_experiments.py`; figure HTML adapted from `part-two/build_report.py`; the original shared stylesheet is copied into the parent folder. No Assignment 1 files are modified.

The folder uses a hyphen instead of the assignment title's colon because Windows filenames cannot contain a colon.
