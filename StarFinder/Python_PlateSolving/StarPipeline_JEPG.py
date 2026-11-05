import time
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from itertools import combinations

from pathlib import Path
from PIL import Image

from functions.ccl_numba import connected_component_labeling_numba
from functions.blacklv import subtract_blacklv
from functions.background import estimate_bg_and_noise_map
from functions.star_centroids import star_stats
from functions.triangle_match import tri_match


# ============================================================================================================
# 0. Load JEPG 
start_read_time = time.perf_counter()
PATH = Path(__file__).resolve().parents[2] / "TestData"  # repo-level TestData folder, independent of the working directory

filename = PATH / "_9264160.jpg"

image = Image.open(filename)

#with Image.open(filename) as image:

# ============================================================================================================
# 1. Aaggregate RGB channels
start_RGB_time = time.perf_counter()

image_array = np.array(image)
#img_raw = np.median(image_array, axis=2)
img_raw = image_array[:,:,0]

# ============================================================================================================
# 2. Remove image background
start_kappasigma_time = time.perf_counter()
background_lin, noise_map_lin = estimate_bg_and_noise_map(img_raw, tilesize=64, method='cub')
#background_cub, noise_map_cub = estimate_bg_and_noise_map(img_superpixel, tilesize=128, method='cub')

# ============================================================================================================
# 3. Final mask, ready for Connected Component Labeling
start_mask_time = time.perf_counter()
img_back_sub_lin = img_raw - background_lin
#img_back_sub_cub = img_superpixel - background_cub

maskappa = 30

mask = img_back_sub_lin > maskappa * noise_map_lin
#mask = img_back_sub_cub > maskappa * noise_map_cub

# ============================================================================================================
# 4. Connected Component Labeling
# No warm-up needed: the numba functions have explicit signatures and are compiled (or loaded from cache) at import
start_ccl_time = time.perf_counter()
img_labels = connected_component_labeling_numba(mask)

# ============================================================================================================
# 5. Star centroid and quality stats
start_centroid_time = time.perf_counter()
xc, yc, n_pixel = star_stats(img_labels, img_back_sub_lin)


# ============================================================================================================
# 6. Star centroid and quality stats
N_STARS = 30  # Number of stars / centroids to include in the calculation of the transform
K_NEIGH = 5  # Number of neighbours considered for the triangle generation

TOL = 5 # Tolerance to decide wheater two triangles are the same

# Get second image
# ============================================================================================================
# 0. Load JEPG 
filename_2 = PATH / "_9264161.jpg"
image_2 = Image.open(filename_2)
#with Image.open(filename_2) as image_2:
# ============================================================================================================
# 1. Aaggregate RGB channels
image_array_2 = np.array(image_2)
#img_raw_2 = np.median(image_array_2, axis=2)
img_raw_2 = image_array_2[:,:,0]
# ============================================================================================================
# 2. Remove image background
background_lin_2, noise_map_lin_2 = estimate_bg_and_noise_map(img_raw_2, tilesize=64, method='cub')
#background_cub_2, noise_map_cub_2 = estimate_bg_and_noise_map(img_raw_2, tilesize=128, method='cub')
# ============================================================================================================
# 3. Final mask, ready for Connected Component Labeling
img_back_sub_lin_2 = img_raw_2 - background_lin_2
#img_back_sub_cub_2 = img_raw_2 - background_cub_2
mask_2 = img_back_sub_lin_2 > maskappa * noise_map_lin_2
#mask_2 = img_back_sub_cub_2 > maskappa * noise_map_cub_2
# ============================================================================================================
# 4. Connected Component Labeling
img_labels_2 = connected_component_labeling_numba(mask_2)
# ============================================================================================================
# 5. Star centroid and quality stats
xc_img2, yc_img2, n_pixel_img2 = star_stats(img_labels_2, img_back_sub_lin_2)
# ============================================================================================================




# Diagnostic Plot
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

plt.ion()

fig, ax = plt.subplots(1, 2, figsize=(16, 8))

# Select the top N_STARS from both images
idx_img1 = np.argpartition(n_pixel, -N_STARS)[-N_STARS:]  # get the unsorted indices to the largest values in n_pixel 
xc_sub_img1 = xc[idx_img1]
yc_sub_img1 = yc[idx_img1]

idx_img2 = np.argpartition(n_pixel_img2, -N_STARS)[-N_STARS:]  # get the unsorted indices to the largest values in n_pixel 
xc_sub_img2 = xc_img2[idx_img2]
yc_sub_img2 = yc_img2[idx_img2]

im = ax[0].imshow(
    np.log2(np.clip(img_back_sub_lin, 1, None)),
    cmap="inferno",
    vmin=1,
    vmax=np.log2(np.clip(img_back_sub_lin, 1, None)).max()
)
#plt.colorbar(im, ax=ax[0], label="Intensity log2 scale")
im2 = ax[1].imshow(
    np.log2(np.clip(img_back_sub_lin_2, 1, None)),
    cmap="inferno",
    vmin=1,
    vmax=np.log2(np.clip(img_back_sub_lin_2, 1, None)).max()
)

# ax[0].scatter(xc, yc, s=25, facecolors='none', edgecolors='cyan', label='All centroids')
# ax[1].scatter(xc_img2, yc_img2, s=25, facecolors='none', edgecolors='cyan')

ax[0].scatter(xc_sub_img1, yc_sub_img1, s=40, color="g", marker='x', label='N_STARS centroids')
ax[1].scatter(xc_sub_img2, yc_sub_img2, s=40, color="g", marker='x')

ax[0].set_title("Image 1")
ax[1].set_title("Image 2")

# for a in ax:
#     a.set_aspect("equal", adjustable="datalim")
#     #a.invert_yaxis()

ax[0].legend()

plt.tight_layout()
plt.show(block=True)

# Find triangles
start_triangle_matching_time = time.perf_counter()
R, t = tri_match(xc,      yc,      n_pixel,
                xc_img2, yc_img2, n_pixel_img2,
                N_STARS, K_NEIGH, TOL, debug_axes=ax)

vec = np.stack([xc_img2, yc_img2])
vec_aligned = R @ vec + t

xc_img2_aligned = vec_aligned[0, :]
yc_img2_aligned = vec_aligned[1, :]

ax[0].scatter(xc_img2_aligned, yc_img2_aligned, s=25, color="m", marker='+', label='aligned img2 centroids')
ax[0].legend()

end_time = time.perf_counter()



SHOW_PLOTS = True

# ------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------
# Step Details 
print("\n")  
print("----------------------------------------------------------------------")   
print(f"Step 1 : RGB Aggregation ")   

print(img_raw.shape)
print(type(image))
print('type(image_array[0, 0]):',type(image_array[0, 0]))
print('Minimum value : ', np.min(image_array))
print('Maximum value : ', np.max(image_array), '\n')

print("----------------------------------------------------------------------")   
print(f"Step 2a : Kappa-Sigma Clipping")   
#diff = (background_lin - background_cub)
#print('max diff in units of sigma:', round(diff.max(),2))
#print('99th percentile:', round(np.percentile(diff, 99), 2))
print('\n')

print("----------------------------------------------------------------------")   
print(f"Step 2b : Background removed ")   
print('type(img_back_sub_lin[0, 0]):',type(img_back_sub_lin[0, 0]))
print('Superpixel image dimensions : ', img_back_sub_lin.shape)
print('Minimum value after Background removal : ', np.min(img_back_sub_lin))
print('Maximum value after Background removal : ', np.max(img_back_sub_lin), '\n')

print("----------------------------------------------------------------------")   
print(f"Step 3 : Mask creation")   
print('Applied Kappa : ', maskappa)

print("----------------------------------------------------------------------")   
print(f"Step 4 : Connected Component Labeling")   
print('Applied Kappa : ', maskappa)

print("----------------------------------------------------------------------")   
print(f"Step 5 : Star Centroids")   
print(f"Number of star centroids identified :", len(xc), '\n')


# Performance: Code execution time in milliseconds
read_execution_time = start_RGB_time - start_read_time
rgb_execution_time = start_kappasigma_time - start_RGB_time
kappasigma_execution_time = start_mask_time - start_kappasigma_time
mask_execution_time = start_ccl_time - start_mask_time
ccl_execution_time = start_centroid_time - start_ccl_time
centroid_execution_time = start_triangle_matching_time - start_centroid_time
triangle_execution_time = end_time - start_triangle_matching_time
total_execution_time = end_time - start_read_time

steps = [
    ("Step 0 : Read Raw", read_execution_time),
    ("Step 1 : RGB Aggregation", rgb_execution_time),
    ("Step 2 : Kappa-Sigma BG", kappasigma_execution_time),
    ("Step 3 : Mask", mask_execution_time),
    ("Step 4 : CCL", ccl_execution_time),
    ("Step 5 : Centroid", centroid_execution_time),    
    ("Step 6 : Triangles", triangle_execution_time),   
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
    # fig, ax = plt.subplots(1,3, figsize=(24, 8), sharex=True, sharey=True)

    # ax[0].imshow(image_array, cmap='jet')
    # ax[0].set_title('JPEG')
    # ax[1].imshow(img_superpixel, cmap='jet')
    # ax[1].set_title('RGB Aggregated')
    # ax[2].imshow(img_back_sub_lin, cmap='jet')
    # ax[2].set_title('Background Removed')
    
    # plt.tight_layout()
    # plt.show()
    

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
    
    
    # # ----------------------------------------------------------------------------------------------------------
    # # Step 6: Centroid
    # fig, ax = plt.subplots(figsize=(18, 10))
  
    # im = ax.imshow(
    #     np.log2(np.clip(img_back_sub_lin, 1, None)),
    #     cmap="inferno",
    #     vmin=1,
    #     vmax=np.log2(np.clip(img_back_sub_lin, 1, None)).max()
    # )
    # plt.colorbar(im, ax=ax, label="Intensity log2 scale")
    
    # # Plot centroids 
    # ax.scatter(xc, yc, s=20, c='cyan', marker='x', label='Centroids')

    # ax.legend()
    # plt.tight_layout()
    # plt.show()
    
    
    # ----------------------------------------------------------------------------------------------------------
    # Step 6.b: Centroid
    fig, ax = plt.subplots(1, 2, figsize=(20, 10), sharex=True, sharey=True, num='Centroids')
 
    im1 = ax[0].imshow(
        np.clip(image_array, 0, None),
        cmap="inferno",
        vmin=1,
        vmax=(np.clip(image_array, 0, None)).max()
    )
  
    im2 = ax[1].imshow(
        np.log2(np.clip(img_back_sub_lin, 1, None)),
        cmap="inferno",
        vmin=1,
        vmax=np.log2(np.clip(img_back_sub_lin, 1, None)).max()
    )
    fig.colorbar(im1, ax=ax[0], label="Intensity linear scale", location='top')
    fig.colorbar(im2, ax=ax[1], label="Intensity log2 scale", location='top')
    
    # Plot centroids 
    ax[0].scatter(xc, yc, s=20, c='magenta', marker='x', label='Centroids')
    ax[1].scatter(xc, yc, s=20, c='cyan', marker='x', label='Centroids')
    
    ax[0].scatter(xc_sub_img1, yc_sub_img1, s=20, c='cyan', marker='x', label='Centroids')
    ax[1].scatter(xc_sub_img2, yc_sub_img2, s=20, c='magenta', marker='x', label='Centroids')

    ax[0].legend()
    ax[1].legend()

    ax[0].set_title('JPEG Linear Scale')
    ax[1].set_title('Red Channel Log2 Scale')    
    
    plt.tight_layout()
    plt.show()