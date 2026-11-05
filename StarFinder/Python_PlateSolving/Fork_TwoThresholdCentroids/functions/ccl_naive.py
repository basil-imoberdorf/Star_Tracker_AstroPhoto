import numpy as np

def find(a, parent):
    a = int(a)
    while parent[a] != a:
        a = parent[a]
    return a
       
def union(a, b, parent):
    
    root_a = find(a, parent)
    root_b = find(b, parent)
    
    if root_a > root_b:  # if the root of a is bigger than the root of b, then make the parent of b the new index of the parent of a to attach a to the tree in b
        parent[root_a] = root_b  
    else:
        parent[root_b] = root_a  
        
    return parent

def connected_component_labeling_naive(img_mask):
    img_len_y, img_len_x = img_mask.shape
    label_count = 0
    max_possible_labels = int(np.ceil((img_len_y * img_len_x) / 2)) + 1
    parent = np.arange(max_possible_labels, dtype='int')
    img_labels = np.zeros(img_mask.shape, dtype='int')

    for i in range(img_len_y):
        for j in range(img_len_x):
            if img_mask[i, j]:
                
                up_idx = max(i-1, 0)
                left_idx = max(j-1, 0)
                
                up_label = img_labels[up_idx, j]
                left_label = img_labels[i, left_idx]
                
                # Case 1: Both the upper and the left label are empty meaning we detect a (new) object so increase the counter for the (provisional) labels
                if (up_label == 0) and (left_label == 0):
                    label_count += 1
                    img_labels[i, j] = label_count
                # Case 2: The left label is zero but not the upper one
                elif left_label==0:
                    img_labels[i, j] = up_label
                # Case 3: The upper label is zero but not the left one  
                elif up_label==0:
                    img_labels[i, j] = left_label
                # Case 4: Both upper and left label are the same but nonzero            
                elif left_label==up_label: # If both are equal we just propagate the same (provisional) label. We chose here the left label for convention
                    img_labels[i, j] = left_label
                # Case 4: Two different objects are connected when both uper and left pixels are different but nonzero!      
                else:
                    img_labels[i, j] = left_label # We also have to propagate in this case the label. We chose here the left label for convention
                    parent = union(up_label, left_label, parent)
            
                    
    # Drop the entries that where over preallocated
    parent = parent[:label_count + 1]

    # Create mapping to set unique label in order from 1 to label_count
    root_idx = parent == np.arange(label_count + 1)
    n_uniq_labels = sum(root_idx)
    label_map = np.zeros([label_count + 1], dtype=int)
    label_map[root_idx] = np.arange(n_uniq_labels)

    for i in range(img_len_y):
        for j in range(img_len_x):
            if img_labels[i,j] > 0:
                img_labels[i, j] = label_map[find(img_labels[i,j], parent)]
    
    return img_labels