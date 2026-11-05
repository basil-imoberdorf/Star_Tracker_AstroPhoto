# Star Tracker AstroPhoto

> 🚧 **Work in progress.** This is an active learning and development project. Scripts are exploratory, interfaces change often, and not everything runs out of the box yet.

The goal is a DIY, closed-loop equatorial star tracker for astrophotography with a Micro Four Thirds camera. Polar alignment and tracking errors are measured directly from the sky by detecting stars in the camera images and matching them between frames, instead of relying on open-loop mechanics.

## Main workstream: StarFinder (Python)

Most of the current development happens in [`StarFinder/Python_PlateSolving/`](StarFinder/Python_PlateSolving/). It is a star detection and centroiding pipeline written from scratch, accelerated with Numba:

1. **Read and calibrate:** read Olympus RAW (`.ORF`) data with `rawpy` and subtract the per-channel black levels of the Bayer pattern.
2. **Superpixel binning:** combine each 2×2 Bayer cell into one superpixel.
3. **Background and noise map:** tile-wise kappa-sigma clipping, spline-interpolated to a smooth full-resolution background and noise map.
4. **Detection:** threshold relative to the local noise level, then connected component labeling.
5. **Centroiding:** intensity-weighted centre of mass for each detected star, at subpixel precision.
6. **Matching (in progress):** match star triangles between frames and estimate the rotation with the Kabsch algorithm.

| File / folder | Description |
| --- | --- |
| `StarPipeline_RAW.py` | Full pipeline on a RAW frame |
| `StarPipeline_JEPG.py` | Pipeline on JPEG frames, including the triangle matching step |
| `Fork_TwoThresholdCentroids/` | Experimental branch with two-threshold centroid regions |
| `functions/` | Pipeline building blocks: background, CCL (naive, pure Python and Numba), centroids, triangle matching |
| `Olympus_OM_D_MkII_RGB_RAW_Sensor.py` | Analysis of the camera's colour channels from red/green/blue test frames |
| `Compare_MyCCL_vs_SciPy.py` | Checks the custom connected component labeling against `scipy.ndimage.label` |
| `Preprocess_RAW.py`, `test*.py` | Scratch and test scripts |

**Dependencies:** `numpy`, `numba`, `rawpy`, `matplotlib`, `Pillow`, `scipy`. Tested versions are pinned in [`requirements.txt`](requirements.txt) (Python 3.13):

```
pip install -r requirements.txt
```

## Other contents

| File / folder | Description |
| --- | --- |
| `StarFinder/*.m`, `*.mlx` | Earlier MATLAB prototypes: background removal, kappa-sigma clipping, connected component labeling, centre of mass and the Kabsch algorithm |
| `TrackerDesign_DraftPlan.md` | Draft design notes: error budget, cascaded control architecture, and why plate solving replaced accelerometer-based alignment |
| `LearningRoadmap_TrackerProject.md` | Learning roadmap for the software and hardware parts of the project |
| `Basic_Visualizations.m`, `Calculation_Sheet_Misc.mlx` | Supporting calculations and plots |
| `TestData/` | Test frames from an Olympus E-M1 Mark II: a JPEG sequence, a RAW light frame (`M1M23818.ORF`) for the RAW pipelines, and red/green/blue sensor test raws |
