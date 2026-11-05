import numpy as np
from numba import njit


@njit(cache=True)
def find(a, parent):
    while parent[a] != a:
        parent[a] = parent[parent[a]]   # path halving
        a = parent[a]
    return a


@njit(cache=True)
def union(a, b, parent):
    root_a = find(a, parent)
    root_b = find(b, parent)
    if root_a > root_b:
        parent[root_a] = root_b
    elif root_b > root_a:
        parent[root_b] = root_a


# Explicit signature -> eager compilation at import (loaded from disk cache after the first run).
# Input: C-contiguous 2D bool mask. Output: 2D int32 label image. Other dtypes raise a TypeError
# instead of silently triggering a slow recompilation.
@njit("int32[:, ::1](boolean[:, ::1])", cache=True)
def connected_component_labeling_numba(img_mask):
    img_len_y, img_len_x = img_mask.shape
    img_labels = np.zeros((img_len_y, img_len_x), dtype=np.int32)
    parent = np.arange((img_len_y * img_len_x + 1) // 2 + 1, dtype=np.int32)
    label_count = 0

    # First pass: provisional labels and merges
    for i in range(img_len_y):
        left_label = 0
        for j in range(img_len_x):
            if img_mask[i, j]:
                up_label = img_labels[i - 1, j] if i > 0 else 0

                if up_label == 0 and left_label == 0:          # Case 1: new object
                    label_count += 1
                    label = label_count
                elif left_label == 0:                           # Case 2
                    label = up_label
                elif up_label == 0 or up_label == left_label:   # Cases 3 and 4
                    label = left_label
                else:                                           # Case 5: merge
                    label = left_label
                    union(up_label, left_label, parent)

                img_labels[i, j] = label
                left_label = label
            else:
                left_label = 0

    # Flatten parent and number the roots 1, 2, 3, ... in one pass over the labels
    label_map = np.zeros(label_count + 1, dtype=np.int32)
    n_labels = 0
    for k in range(1, label_count + 1):
        parent[k] = parent[parent[k]]
        if parent[k] == k:
            n_labels += 1
            label_map[k] = n_labels
        else:
            label_map[k] = label_map[parent[k]]   # root < k, so already numbered

    # Second pass: relabel
    for i in range(img_len_y):
        for j in range(img_len_x):
            img_labels[i, j] = label_map[img_labels[i, j]]

    return img_labels