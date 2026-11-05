import numpy as np
from numba import njit

# Explicit signature -> eager compilation at import (loaded from disk cache after the first run).
# Inputs: int32 label image (from connected_component_labeling_numba), float64 intensity image,
# both 2D C-contiguous. Returns (x_center, y_center) as float64 arrays in pixel units.
@njit("Tuple((float64[::1], float64[::1]))(int32[:, ::1], float64[:, ::1])", cache=True)
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
            
            label = img_label[i, j] # img_label ranges naturally from 1 to n_labels and has 0 everywhere the background is
            
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
   
    return x_center, y_center


# Two-threshold (hysteresis) centroids: detect stars on a high-threshold label image, but measure the
# centroid over the larger low-threshold region that contains each detection, so the star wings are included.
# Inputs (all 2D, C-contiguous, same shape):
#   img_label_high : int32 labels of the detection mask (e.g. I > 12 sigma), from connected_component_labeling_numba
#   img_label_low  : int32 labels of the measurement mask (e.g. I > 3 sigma), from connected_component_labeling_numba
#   Intensity_img  : float64 background-subtracted intensity [counts]
# Requires: high mask is a subset of low mask (high threshold >= low threshold on the same image).
# Detection rule is identical to star_stats: a star is a high-threshold object with more than 3 pixels.
# If a low-threshold region contains more than one high-threshold object (blend of close stars), each of those
# stars falls back to its high-threshold region, so close pairs are not merged into one wrong centroid.
# Returns: x_center, y_center [px] (float64) and is_blended (bool, True where the high-threshold fallback was used).
@njit("Tuple((float64[::1], float64[::1], boolean[::1]))(int32[:, ::1], int32[:, ::1], float64[:, ::1])", cache=True)
def star_stats_two_threshold(img_label_high, img_label_low, Intensity_img):

    len_y, len_x = img_label_high.shape

    n_high = img_label_high.max()
    n_low  = img_label_low.max()

    sum_xw_high      = np.zeros(n_high)
    sum_yw_high      = np.zeros(n_high)
    sum_w_high       = np.zeros(n_high)
    pixelcount_high  = np.zeros(n_high, dtype=np.int64)
    low_of_high      = np.zeros(n_high, dtype=np.int32)    # low-threshold label that contains each high-threshold object

    sum_xw_low       = np.zeros(n_low)
    sum_yw_low       = np.zeros(n_low)
    sum_w_low        = np.zeros(n_low)

    # Accumulate first moments for both label images in one scan
    for i in range(len_y):
        for j in range(len_x):
            label_low = img_label_low[i, j]
            if label_low > 0:
                intensity_ij = Intensity_img[i, j]   # not clipped: zero-mean noise keeps the first moment unbiased
                idx_low = label_low - 1
                sum_xw_low[idx_low] += j * intensity_ij
                sum_yw_low[idx_low] += i * intensity_ij
                sum_w_low[idx_low]  += intensity_ij

                label_high = img_label_high[i, j]    # high mask is a subset of low mask, so only check inside low regions
                if label_high > 0:
                    idx_high = label_high - 1
                    sum_xw_high[idx_high] += j * intensity_ij
                    sum_yw_high[idx_high] += i * intensity_ij
                    sum_w_high[idx_high]  += intensity_ij
                    pixelcount_high[idx_high] += 1
                    low_of_high[idx_high] = label_low   # a connected high object lies entirely inside one low region

    # Count how many high-threshold objects (any size) sit inside each low-threshold region
    seeds_per_low = np.zeros(n_low, dtype=np.int64)
    for k in range(n_high):
        seeds_per_low[low_of_high[k] - 1] += 1

    # Detection rule as in star_stats: more than three pixels above the high threshold
    n_stars = 0
    for k in range(n_high):
        if pixelcount_high[k] > 3:
            n_stars += 1

    x_center   = np.empty(n_stars)
    y_center   = np.empty(n_stars)
    is_blended = np.zeros(n_stars, dtype=np.bool_)

    star = 0
    for k in range(n_high):
        if pixelcount_high[k] > 3:
            idx_low = low_of_high[k] - 1
            if seeds_per_low[idx_low] == 1:      # isolated star: centroid over the full low-threshold region
                x_center[star] = sum_xw_low[idx_low] / sum_w_low[idx_low]
                y_center[star] = sum_yw_low[idx_low] / sum_w_low[idx_low]
            else:                                # blend: fall back to the high-threshold region of this star
                x_center[star]   = sum_xw_high[k] / sum_w_high[k]
                y_center[star]   = sum_yw_high[k] / sum_w_high[k]
                is_blended[star] = True
            star += 1

    return x_center, y_center, is_blended
    
    
    