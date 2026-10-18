# Fun with Filters and Frequencies

SYDE 671 Assignment 2 · James Xie

The repository contains the code, English project webpages, input photographs (including the author's personal selfie), generated results, source attribution and experiment records for Parts 1.1–2.4.

## Browse

Open `index.html` in a browser to navigate all seven sections:

- Part 1.1: Convolutions from Scratch
- Part 1.2: Finite Difference Operator
- Part 1.3: Derivative of Gaussian and mandatory gradient orientations
- Part 2.1: Image Sharpening
- Part 2.2: Hybrid Images and mandatory color exploration
- Part 2.3: Gaussian and Laplacian Stacks
- Part 2.4: Multiresolution Blending and mandatory color exploration

All website images and styles are ordinary Git files. Raw NumPy array archives (`*.npz`) use Git LFS; they are optional downloads and are not loaded by the webpages. Referenced course and paper PDFs are in `references/`. This repository upload does not enable GitHub Pages.

## Clone with raw arrays

Git LFS is required to retrieve the full numerical archives. After installing Git and Git LFS:

```sh
git lfs install
git clone https://github.com/AAAJamesXie/Fun-with-Filters-and-Frequencies.git
cd Fun-with-Filters-and-Frequencies
git lfs pull
```

For a smaller website/code-only checkout, set `GIT_LFS_SKIP_SMUDGE=1` during cloning. LFS files then remain small pointers until `git lfs pull` is run. A GitHub ZIP download may omit LFS contents depending on repository settings.

## Reproduce

Python experiments use NumPy, SciPy, OpenCV and Pillow. Each part includes a README, implementation, experiment generator, report generator, and targeted unit tests. Run commands from the corresponding part's directory. Keep the sibling part directories together: Part 2.4 reuses the Part 2.3 stack implementation and Part 2.2 alignment code. Browser verification scripts were run using Playwright and Microsoft Edge on Windows; their executable/runtime paths may need adjustment on another machine.

Original inputs are preserved. Source JSON records include original acquisition paths for provenance; those historical absolute paths are not required to view the reports or run the main experiment generators. IDE settings and Python caches are excluded.

## Attribution and personal photographs

See every part's webpage and `input/source.json` or `input/sources.json` for photograph sources, licenses, modifications, and references. Source licenses differ; this repository has no blanket license granting rights over all photographs, course materials, and code. In particular, the author's personal selfie is included with permission for this private repository and is not given an open-image license. Cat/owl derivatives retain CC BY-SA 4.0 attribution; tiger derivatives credit Steve Wilson under CC BY 2.0.

The original coursework PDF and supplied Burt–Adelson paper are included as report references. All composites are educational image-processing results.
