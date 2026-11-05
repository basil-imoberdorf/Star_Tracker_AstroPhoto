import numpy as np
from numba import njit

# Explicit signature -> eager compilation at import (loaded from disk cache after the first run).
# Inputs: int32 label image (from connected_component_labeling_numba), float64 intensity image,
# both 2D C-contiguous. Returns (x_center, y_center) as float64 arrays in pixel units.
@njit("Tuple((float64[::1], float64[::1], int64[::1]))(int32[:, ::1], float64[:, ::1])", cache=True)
def star_stats(img_label, Intenisty_img):
    
    len_y, len_x = img_label.shape
        
    n_labels = img_label.max()    
    accumsum_xw = np.zeros(n_labels)
    accumsum_yw = np.zeros(n_labels)
    accumsum_w  = np.zeros(n_labels)
    pixelcount  = np.zeros(n_labels, dtype=np.int64)
    
    # Accumulate all values in one scan of the image
    for i in range(len_y):
        for j in range(len_x):
            
            label = img_label[i, j] # img_label ranges from 1 to n_labels and has 0 everywhere the background is
            
            if label > 0:
                idx = label - 1 # align the start of the labels at 1 with the start from 0 Python indexing
                Intenisty_ij = Intenisty_img[i, j]  # deliberately NOT clipped: zero-mean noise keeps the first moment unbiased, clipping would bias towards the region center
                accumsum_xw[idx] += j * Intenisty_ij
                accumsum_yw[idx] += i * Intenisty_ij
                accumsum_w[idx] += Intenisty_ij
                pixelcount[idx] += 1
    
    # Keep only objects with more than three pixels
    # accumsum_w > 0 holds by construction as long as labelled pixels come from a mask with a positive threshold (I > kappa * noise)
    keep_mask = pixelcount > 3

    # Weighted average to get center of mass    
    x_center = accumsum_xw[keep_mask] / accumsum_w[keep_mask]
    y_center = accumsum_yw[keep_mask] / accumsum_w[keep_mask]   
    n_pixels = pixelcount[keep_mask]
   
    return x_center, y_center, n_pixels

