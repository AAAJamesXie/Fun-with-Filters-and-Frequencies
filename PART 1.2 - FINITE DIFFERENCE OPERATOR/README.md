# Part 1.2: Finite Difference Operator

Uses the user-approved modern 512x512 camera image from the official scikit-image v0.25.2 repository. This differs from the legacy ResearchGate figure, whose image download was restricted. Source, license attribution and URLs are in `input/source.json`. No scikit-image installation is needed.

From this directory, using the existing NumPy, SciPy and Pillow environment:

```powershell
python -B -m unittest test_edges.EdgeTests -v
python -B run_experiments.py --threshold 0.20
```

Open `index.html` for the English report. To choose a different threshold, rerun the experiment with `--threshold VALUE`, review `results/threshold-contact.png`, update `observations.txt` with the visual justification and rebuild the page with `python -B build_report.py`.

The input is normalized to float64 [0, 1] without resizing or smoothing. Finite difference kernels are `[1, -1]` and its transpose. SciPy convolution uses `mode='same', boundary='symm'`; this avoids the spurious black-background border produced by zero fill. Edge pixels satisfy `raw_magnitude > threshold`. All thresholds use identical raw data and display conventions. Edge density is not an accuracy measure.

Outputs:

- `results/`: grayscale input, signed derivatives, gradient magnitude, selected edge map, threshold sweep and contact sheet.
- `results/gradient-arrays.npz`: raw float64 original/derivatives/magnitude and boolean selected mask.
- `results/metrics.json`: parameters, threshold densities, display mappings, image SHA-256 and environment versions.

The visual style and image-report pattern follow Part 1.1. Existing Part 1.1 outputs are unchanged.
