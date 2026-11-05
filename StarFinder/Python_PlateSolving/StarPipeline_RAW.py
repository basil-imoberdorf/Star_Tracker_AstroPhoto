import time
from pathlib import Path

import rawpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from functions.ccl_numba import connected_component_labeling_numba
from functions.blacklv import subtract_blacklv
from functions.background import estimate_bg_and_noise_map
from functions.star_centroids import star_stats


TESTDATA = Path(__file__).resolve().parents[2] / 'TestData'  # repo-level TestData folder, independent of the working directory
file = str(TESTDATA / 'M1M23818.ORF')  # RAW light frame (Andromeda, 23.08.2026); rawpy.imread expects a string path

# 0. Read raw
start_read_time = time.perf_counter()
with rawpy.imread(file) as raw:
    # Access the raw 2D grid of pixel values directly from the sensor
    # This is a 2D NumPy array matching the resolution of the sensor
    img_raw = raw.raw_image.copy()
    black_lv = raw.black_level_per_channel

    print('\ntype(raw):', type(raw))
    print('raw.raw_pattern: \n', raw.raw_pattern)
    print('raw.color_desc:', raw.color_desc)
    print('raw.num_colors:', raw.num_colors)
    print('raw.raw_type:', raw.raw_type)
    print('raw.white_level:', raw.white_level, '  --> level at which the raw pixel value is considered to be saturated \n')
    print('type(img_raw):', type(img_raw))
    print('type(img_raw[0, 0]):', type(img_raw[0, 0]), '\n')
    
    print('Shape of raw image:', img_raw.shape)
    print('Minimum value in raw image: ', np.min(img_raw))  # Check the minimum value in the raw image for normalization purposes
    print('Maximum value in raw image: ', np.max(img_raw), '\n')  # Check the maximum value in the raw image for normalization purposes   
    
# ============================================================================================================
# 1. Substract the black levels
start_blacklv_time = time.perf_counter()
img_black_subtracted = subtract_blacklv(img_raw, black_lv) # subtracts the Bayer pattern specific black levels from the raw image 

# ============================================================================================================
# 2. Superpixels are binned 2x2 blocks of pixels that correspond to a single element of the Bayer color filter array (CFA)
start_superpixel_time = time.perf_counter()
img_superpixel = (img_black_subtracted[0::2, 0::2] + img_black_subtracted[0::2, 1::2] + img_black_subtracted[1::2, 0::2] + img_black_subtracted[1::2, 1::2]) / 1

# ============================================================================================================
# 3. Remove image background
start_kappasigma_time = time.perf_counter()
background_lin, noise_map_lin = estimate_bg_and_noise_map(img_superpixel, tilesize=64, method='cub')
#background_cub, noise_map_cub = estimate_bg_and_noise_map(img_superpixel, tilesize=128, method='cub')

# ============================================================================================================
# 4. Final mask, ready for Connected Component Labeling
start_mask_time = time.perf_counter()
img_back_sub_lin = img_superpixel - background_lin
#img_back_sub_cub = img_superpixel - background_cub

maskappa = 12

mask = img_back_sub_lin > maskappa * noise_map_lin
#mask = img_back_sub_cub > maskappa * noise_map_cub

# ============================================================================================================
# 5. Connected Component Labeling
# No warm-up needed: the numba functions have explicit signatures and are compiled (or loaded from cache) at import
start_ccl_time = time.perf_counter()
img_labels = connected_component_labeling_numba(mask)

# ============================================================================================================
# 6. Star centroid and quality stats
start_centroid_time = time.perf_counter()
xc, yc, n_pixel = star_stats(img_labels, img_back_sub_lin)  # star_stats also returns the pixel count per star (same as in StarPipeline_JEPG.py)


end_time = time.perf_counter()




SHOW_PLOTS = False

# ------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------
# Step Details 
print("\n")  
print("----------------------------------------------------------------------")   
print(f"Step 1 : Black Levels ")   
bl_r, bl_gr, bl_gb, bl_b = black_lv
print('Black level - Red:', bl_r)
print('Black level - Green (Red):', bl_gr)
print('Black level - Green (Blue):', bl_gb)
print('Black level - Blue:', bl_b, '\n')

print('type(img_raw[0, 0]):',type(img_raw[0, 0]))
print('Minimum value BEFORE black level subtraction: ', np.min(img_raw))
print('Maximum value BEFORE black level subtraction: ', np.max(img_raw), '\n')

print('type(img_black_subtracted[0, 0]):',type(img_black_subtracted[0, 0]))
print('Minimum value AFTER black level subtraction: ', np.min(img_black_subtracted))
print('Maximum value AFTER black level subtraction: ', np.max(img_black_subtracted), '\n')
print('Raw image dimensions : ', img_black_subtracted.shape, '\n')

print("----------------------------------------------------------------------")   
print(f"Step 2 : Super Pixels ")   
print('type(img_superpixel[0, 0]):',type(img_superpixel[0, 0]))
print('Superpixel image dimensions : ', img_superpixel.shape)
print('Minimum value after binning to 2x2 superpixels: ', np.min(img_superpixel))
print('Maximum value after binning to 2x2 superpixels: ', np.max(img_superpixel), '\n')

print("----------------------------------------------------------------------")   
print(f"Step 3 : Kappa-Sigma Clipping")   
#diff = (background_lin - background_cub)
#print('max diff in units of sigma:', round(diff.max(),2))
#print('99th percentile:', round(np.percentile(diff, 99), 2))

print("----------------------------------------------------------------------")   
print(f"Step 6 : Star Centroids")   
print(f"Number of star centroids identified = {len(xc)}")


# Performance: Code Execution time
read_execution_time = start_blacklv_time - start_read_time
blacklv_execution_time = start_superpixel_time - start_blacklv_time
superpixel_execution_time = start_kappasigma_time - start_superpixel_time
kappasigma_execution_time = start_mask_time - start_kappasigma_time
mask_execution_time = start_ccl_time - start_mask_time
ccl_execution_time = start_centroid_time - start_ccl_time
centroid_execution_time = end_time - start_centroid_time
total_execution_time = end_time - start_read_time

steps = [
    ("Step 0 : Read Raw", read_execution_time),
    ("Step 1 : Black Lv", blacklv_execution_time),
    ("Step 2 : Superpixel binning", superpixel_execution_time),
    ("Step 3 : Kappa-Sigma BG", kappasigma_execution_time),
    ("Step 4 : Mask", mask_execution_time),
    ("Step 5 : CCL", ccl_execution_time),
    ("Step 6 : Centroid", centroid_execution_time),    
]

print("\n\nExecution Times")
print("-" * 65)
print(f"{'Step':<30} {'Time [ms]':>12} {'Relative [%]':>17}")
print("-" * 65)

for name, execution_time in steps:
    relative_time = 100 * execution_time / total_execution_time
    print(f"{name:<30} {1000*execution_time:>12.2f} {relative_time:>16.1f}%")

print("-" * 65)
print(f"{'Total  : All':<30} {1000*total_execution_time:>12.2f} {'100.0':>16}%")
print("-" * 65)
print("\n")

# ----------------------------------------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------------------------------------
if SHOW_PLOTS:


    # # ----------------------------------------------------------------------------------------------------------
    # # Step 5: CCL
    # fig, ax = plt.subplots(figsize=(16, 12))

    # im = ax.imshow(
    #     img_labels,
    #     cmap="magma",
    #     interpolation="nearest",
    #     vmin=0,
    #     vmax=img_labels.max()
    # )

    # plt.colorbar(im, ax=ax, label="Component label")
    # plt.show()
    
    
    # ----------------------------------------------------------------------------------------------------------
    # Step 6: Centroid
    fig, ax = plt.subplots(figsize=(18, 10))
  
    im = ax.imshow(
        np.log2(np.clip(img_back_sub_lin, 1, None)),
        #img_labels,
        cmap="inferno",
        vmin=1,
        vmax=np.log2(np.clip(img_back_sub_lin, 1, None)).max()
    )
    plt.colorbar(im, ax=ax, label="Component label")
    
    ax.scatter(
        xc,
        yc,
        s=20,
        c='cyan',
        marker='x',
        label='Centroids'
    )

    ax.legend()
    plt.tight_layout()
    plt.show()