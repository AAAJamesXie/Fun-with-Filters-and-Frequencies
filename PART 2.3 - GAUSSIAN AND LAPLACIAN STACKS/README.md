# Part 2.3: Gaussian and Laplacian Stacks

Uses the provided 740x530 RGB apple and orange images without resizing. The existing NumPy, SciPy, OpenCV and Pillow environment is sufficient; no installation is performed.

From this directory:

```powershell
python -B -m unittest test_stacks.StackTests -v
python -B run_experiments.py
python -B build_report.py
```

Gaussian levels have nominal cumulative sigma 0,2,4,8,16,32. Every level remains 530x740x3. Successive filtering uses incremental sigma sqrt(target^2-previous^2), separable normalized Gaussian vectors, radius ceil(4*incremental sigma), and half-sample symmetric boundaries. No built-in pyramid or resampling function is used in the stack algorithms. Finite sampled kernels approximate the nominal Gaussian scale schedule.

Laplacian levels 0-4 are adjacent Gaussian differences; level 5 is the last Gaussian residual. Summing all six raw levels reconstructs the input. Mask scales are 1,2,4,8,16,32, with a narrow smooth transition even at the finest level. Complementary mask weights mix the corresponding image bands. Reconstruction directly sums the full-resolution bands, without expansion.

Open `index.html` for the English report, including apple/orange/oraple G/L stacks and the Figure 3.42 adaptation. The figure's first three rows show weighted levels 0,2,4; its final row sums all six levels of the left/right contributions and the combined result. Signed image displays are centered at middle gray and do not enter reconstruction. The final oraple's independently computed Laplacian decomposition is distinct from the weighted bands used to construct it.

`results/metrics.json` records scales, shape invariants, source hashes, display scales and errors. `results/stack-arrays.npz` preserves the float64 stacks and contributions; it is approximately 445 MB because all layers retain full image resolution. It is an optional local inspection artifact, not loaded by the webpage. `results/figure-3-42.png` is the assembled twelve-panel figure. `input/source.json` records the course sources and supplied paper. Existing source grain and panel labels are retained.
