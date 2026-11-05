import numpy as np


def find(a, parent):
    while parent[a] != a:
        parent[a] = parent[parent[a]]   # path halving
        a = parent[a]
    return a

def union(a, b, parent):
    root_a = find(a, parent)
    root_b = find(b, parent)
    if root_a > root_b:
        parent[root_a] = root_b
    elif root_b > root_a:
        parent[root_b] = root_a


def connected_component_labeling(img_mask):
    img_len_y, img_len_x = img_mask.shape

    mask = img_mask.tolist()                         # numpy -> nested lists of Python ints
    labels = [[0] * img_len_x for _ in range(img_len_y)]
    parent = [0]                                     # index 0 = background, grows via append

    prev_row = [0] * img_len_x                       # acts as "row -1" (all background)

    for i in range(img_len_y):
        mask_row = mask[i]                           # row lookups once per row,
        row = labels[i]                              # not once per pixel
        left_label = 0                               # acts as "column -1" (background)

        for j in range(img_len_x):
            if mask_row[j]:
                up_label = prev_row[j]

                # Case 1: new object -> new provisional label
                if up_label == 0 and left_label == 0:
                    label = len(parent)
                    parent.append(label)
                # Case 2: only the upper neighbor is labeled
                elif left_label == 0:
                    label = up_label
                # Cases 3 and 4: only left is labeled, or both are equal
                elif up_label == 0 or up_label == left_label:
                    label = left_label
                # Case 5: two different labels meet -> merge
                else:
                    label = left_label
                    union(up_label, left_label, parent)

                row[j] = label
                left_label = label                   # left neighbor of pixel j+1
            else:
                left_label = 0

        prev_row = row                               # this row is "up" for the next one

    # Flatten on the list (parent[k] <= k, so one forward pass is enough)
    for k in range(len(parent)):
        parent[k] = parent[parent[k]]

    # Second pass: vectorized relabel, back in numpy
    parent = np.array(parent)
    root_idx = parent == np.arange(len(parent))
    label_map = np.zeros(len(parent), dtype=int)
    label_map[root_idx] = np.arange(np.count_nonzero(root_idx))
    return label_map[parent][np.array(labels)]