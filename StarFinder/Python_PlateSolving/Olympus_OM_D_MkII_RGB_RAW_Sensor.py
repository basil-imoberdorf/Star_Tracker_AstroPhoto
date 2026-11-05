
from pathlib import Path

import rawpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


# 1. Custom Colormap von Schwarz ('black' oder '#000000') nach Rot ('red' oder '#FF0000') erstellen
cmap_black_red = mcolors.LinearSegmentedColormap.from_list(
    "BlackRed", ["black", "red"]
)
cmap_black_green = mcolors.LinearSegmentedColormap.from_list(
    "BlackGreen", ["black", "green"]
)
cmap_black_blue = mcolors.LinearSegmentedColormap.from_list(
    "BlackBlue", ["black", "blue"]
)


TESTDATA = Path(__file__).resolve().parents[2] / 'TestData'  # repo-level TestData folder, independent of the working directory
red_filepath   = str(TESTDATA / 'red1.ORF')    # rawpy.imread expects a string path
green_filepath = str(TESTDATA / 'green1.ORF')
blue_filepath  = str(TESTDATA / 'blue1.ORF')

filespaths = [red_filepath, green_filepath, blue_filepath]
n_files = len(filespaths)
raw_images = [None] * n_files  # preallocate list to hold raw images


for i in range(n_files):
    
    file = filespaths[i]
    
    with rawpy.imread(file) as raw:
        # Access the raw 2D grid of pixel values directly from the sensor
        # This is a 2D NumPy array matching the resolution of the sensor
        raw_grid = raw.raw_image.copy()

        print('type(raw):', type(raw))
        print('type(raw_grid):', type(raw_grid))
        print('raw.raw_pattern:', raw.raw_pattern)
        print('raw.color_desc:', raw.color_desc)
        print('raw.num_colors:', raw.num_colors)
        print('raw.raw_type:', raw.raw_type)

    # Store the raw grid in the list
    raw_images[i] = raw_grid
    

print(np.max(raw_images[i]))  # Check the maximum value in the raw image for normalization purposes
           
# Create a figure with 3 rows and 1 column
# figsize=(width, height) - adjusting height to fit 3 vertical panels nicely
fig, axs = plt.subplots(nrows=1, ncols=3, figsize=(18, 6), sharex=True)

colors = [cmap_black_red, cmap_black_green, cmap_black_blue]  # Color maps for each channel

for i in range(n_files):
    axs[i].imshow(raw_images[i][0:12, 0:12], cmap=colors[i])
    axs[i].set_title(f'{["Red", "Green", "Blue"][i]} Channel')

# Optimize the spacing between the panels automatically
plt.tight_layout()
plt.show()








