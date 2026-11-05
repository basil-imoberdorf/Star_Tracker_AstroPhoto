
from pathlib import Path

import rawpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors



TESTDATA = Path(__file__).resolve().parents[2] / 'TestData'  # repo-level TestData folder, independent of the working directory
file = str(TESTDATA / 'M1M23818.ORF')  # RAW light frame (Andromeda, 23.08.2026); rawpy.imread expects a string path

with rawpy.imread(file) as raw:
    # Access the raw 2D grid of pixel values directly from the sensor
    # This is a 2D NumPy array matching the resolution of the sensor
    img_raw = raw.raw_image.copy()
    black_lv = raw.black_level_per_channel

    print('type(raw):', type(raw))
    print('raw.raw_pattern: \n', raw.raw_pattern)
    print('raw.color_desc:', raw.color_desc)
    print('raw.num_colors:', raw.num_colors)
    print('raw.raw_type:', raw.raw_type)
    print('raw.white_level:', raw.white_level, '  --> level at which the raw pixel value is considered to be saturated \n')
    print('Shape of raw image:', img_raw.shape)
    print('type(img_raw):', type(img_raw))
    print('type(img_raw[0, 0]):', type(img_raw[0, 0]), '\n')
    print('Minimum value in raw image: ', np.min(img_raw))  # Check the minimum value in the raw image for normalization purposes
    print('Maximum value in raw image: ', np.max(img_raw), '\n')  # Check the maximum value in the raw image for normalization purposes   
    
    

def bg_robust_kappa_sigma_clipping(array, kappa=2.0, max_iterations=5):
    """
    Perform robust kappa-sigma clipping on the input data to remove outliers and estimate the background level.
    Clipped data is not reused for the next iteration to ensure that the background estimation is not biased by replaced values.

    Parameters:
    - array: 2D NumPy array of pixel values.
    - kappa: The number of standard deviations to use for clipping.
    - max_iterations: Maximum number of iterations for the clipping process.

    Returns:
    - keep_mask: 2D boolean NumPy array indicating which values belong to the background (True) and which are considered outliers (False).
    """

    keep_mask = np.zeros(array.shape, dtype=bool)
    
    for iteration in range(max_iterations):
                       
        # Use robust statistics to estimate the background level and standard deviation
        median = np.median(array[keep_mask])
        MAD = np.median(np.abs(array[keep_mask] - median))
        sigma = 1.4826 * MAD 
               
        # Get the mask of values to keep based on the kappa-sigma clipping criteria
        keep_mask = (array - median) < (kappa * sigma)
                
        print(f"Iteration {iteration + 1}: median={median}, std_dev={sigma}, threshold={kappa * sigma}")
    
    return keep_mask


# 1. Extract per-channel black levels
bl_r, bl_gr, bl_gb, bl_b = black_lv

print('Black level - Red:', bl_r)
print('Black level - Green (Red):', bl_gr)
print('Black level - Green (Blue):', bl_gb)
print('Black level - Blue:', bl_b, '\n')

# 2. Apply the subtraction to the 2x2 interleaved grid
img_black_subtracted = img_raw.copy().astype(np.float32)  # Copy and convert to float for processing 
print('type(img_raw[0, 0]):',type(img_black_subtracted[0, 0]))
print('Minimum value BEFORE black level subtraction: ', np.min(img_black_subtracted))
print('Maximum value BEFORE black level subtraction: ', np.max(img_black_subtracted), '\n')

img_black_subtracted[0::2, 0::2] -= bl_r   # Top-left of the 2x2 block (Even rows, Even cols)
img_black_subtracted[0::2, 1::2] -= bl_gr  # Top-right of the 2x2 block (Even rows, Odd cols)
img_black_subtracted[1::2, 0::2] -= bl_gb  # Bottom-left of the 2x2 block (Odd rows, Even cols)
img_black_subtracted[1::2, 1::2] -= bl_b   # Bottom-right of the 2x2 block (Odd rows, Odd cols)

print('type(img_black_subtracted[0, 0]):',type(img_black_subtracted[0, 0]))
print('Minimum value AFTER black level subtraction: ', np.min(img_black_subtracted))
print('Maximum value AFTER black level subtraction: ', np.max(img_black_subtracted), '\n')

# 3. Clip negative values to 0 (since true black cannot be less than zero)
img_black_subtracted = np.clip(img_black_subtracted, 0, None)
print('type(img_black_subtracted[0, 0]):',type(img_black_subtracted[0, 0]))
print('Minimum value after CLIPPING black level subtracted image: ', np.min(img_black_subtracted))
print('Maximum value after CLIPPING black level subtracted image: ', np.max(img_black_subtracted), '\n')

# Superpixels are binned 2x2 blocks of pixels that correspond to a single element of the Bayer color filter array (CFA)
img_superpixel = (img_black_subtracted[0::2, 0::2] + img_black_subtracted[0::2, 1::2] + img_black_subtracted[1::2, 0::2] + img_black_subtracted[1::2, 1::2]) / 1
print('type(img_superpixel[0, 0]):',type(img_superpixel[0, 0]))
print('Minimum value after binning to 2x2 superpixels: ', np.min(img_superpixel))
print('Maximum value after binning to 2x2 superpixels: ', np.max(img_superpixel), '\n')

# Print the shapes of the images for verification
print('Shape of raw image: ', img_raw.shape)
print('Shape of black level subtracted image BEFORE binning: ', img_black_subtracted.shape)
print('Shape of black level subtracted image AFTER binning to 2x2 superpixels: ', img_superpixel.shape, '\n')



# Plotting the raw image and the black level subtracted image for comparison
fig, axs = plt.subplots(nrows=1, ncols=3, sharex=True, sharey=True)
fig.canvas.manager.window.wm_geometry("2400x1200+100+100")

PLOT_FULL_SIZE = True  # Set to True to plot the full size of the images, False to plot a smaller region for better visibility
PLOT_LOG_SCALE = False  # Set to True to plot the images in log scale, False for linear scale
COLORMAP = 'plasma'  # Choose a colormap for visualization

if PLOT_FULL_SIZE:
    size_x = img_raw.shape[1]  # Size of the region to display
    size_y = img_raw.shape[0]  # Size of the region to display
else:
    size_x = 2200  # Size of the region to display
    size_y = 1200  # Size of the region to display

if PLOT_LOG_SCALE:
    raw_display = np.log2(img_raw[:size_x, :size_y] + 1)  # + 1 is added to avoid log(0) which is undefined and at 1 the log2(1) = 0, which is a valid value for display purposes
    black_subtracted_display = np.log2(img_black_subtracted[:size_x, :size_y] + 1)  # + 1 is added to avoid log(0) which is undefined and at 1 the log2(1) = 0, which is a valid value for display purposes
    superpixel_display = np.log2(img_superpixel[:size_x//2, :size_y//2] + 1)  # Adjust size for superpixel image
    vmin = 0
    vmax = 12
else:
    raw_display = img_raw[:size_x, :size_y]
    black_subtracted_display = img_black_subtracted[:size_x, :size_y]
    superpixel_display = img_superpixel[:size_x//2, :size_y//2]  # Adjust size for superpixel image
    vmin = 0
    vmax = 2**12
    

img_ax0 = axs[0].imshow(raw_display, cmap=COLORMAP, extent=[0, size_x, size_y, 0], vmin=vmin, vmax=vmax) # + 1 is added to avoid log(0) which is undefined and at 1 the log2(1) = 0, which is a valid value for display purposes
axs[0].set_title('Raw Image')

img_ax1 = axs[1].imshow(black_subtracted_display, cmap=COLORMAP, extent=[0, size_x, size_y, 0], vmin=vmin, vmax=vmax)  # + 1 is added to avoid log(0) which is undefined and at 1 the log2(1) = 0, which is a valid value for display purposes   
axs[1].set_title('Black Level Subtracted Image')

img_ax2 = axs[2].imshow(superpixel_display, cmap=COLORMAP, extent=[0, size_x, size_y, 0], vmin=vmin, vmax=vmax)  # Adjust extent to match the original image size
axs[2].set_title('Superpixel Image')

for ax, im in zip(axs, [img_ax0, img_ax1, img_ax2]):

    cbar = fig.colorbar(
        im,
        ax=ax,
        orientation='horizontal',
        location='top',
        pad=0.08,
        fraction=0.05
    )
    # Tick positions
    ticks = np.arange(0, 13, 1)
    cbar.set_ticks(ticks)

    # Tick labels
    cbar.set_ticklabels([
        f'$2^{{{n}}}$' for n in ticks
    ])



# Optimize the spacing between the panels automatically
plt.tight_layout()
plt.show()





