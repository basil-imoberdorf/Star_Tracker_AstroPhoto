import time
import numpy as np
import matplotlib.pyplot as plt

from Python_PlateSolving.functions.ccl import connected_component_labeling


def find(a, parent):
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
        



# Create dummy mask for testing
img_mask = np.array([[1, 1, 0, 0, 1, 1, 0, 0],
[1, 0, 0, 0, 1, 1, 0, 0],
[0, 1, 1, 1, 0, 0, 0, 0],
[1, 1, 1, 1, 0, 0, 0, 0],
[1, 1, 1, 0, 0, 0, 0, 0],
[1, 1, 0, 1, 1, 0, 1, 0],
[0, 0, 0, 1, 0, 0, 1, 0],
[0, 0, 0, 0, 0, 0, 1, 0],
[0, 1, 0, 1, 0, 1, 0, 0],
[0, 1, 0, 1, 0, 1, 0, 0],
[1, 1, 1, 1, 1, 1, 1, 0],
[1, 1, 1, 1, 1, 1, 1, 0],
[0, 1, 0, 1, 0, 1, 0, 0]])



#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask, img_mask, img_mask], 1)
#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask], 1)
#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask], 1)
#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
#img_mask = np.concat([img_mask, img_mask, img_mask, img_mask], 1)

img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
img_mask = np.concat([img_mask, img_mask, img_mask, img_mask, img_mask, img_mask], 1)
img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
img_mask = np.concat([img_mask, img_mask, img_mask, img_mask], 1)
img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
img_mask = np.concat([img_mask, img_mask, img_mask, img_mask], 1)
img_mask = np.concat([img_mask, img_mask, img_mask, img_mask])
img_mask = np.concat([img_mask, img_mask, img_mask, img_mask], 1)


img_len_y = img_mask.shape[0]
img_len_x = img_mask.shape[1]

print(img_mask)
print('Image width: ', img_len_x, ' px')
print('Image height: ', img_len_y, ' px\n')

# 6. Connected Component Labeling
label_count = 0
max_possible_labels = int(np.ceil((img_len_y * img_len_x) / 2)) + 1
parent = np.arange(max_possible_labels, dtype='int')
img_labels = np.zeros(img_mask.shape, dtype='int')
img_labels = img_labels.tolist()
img_mask_list = img_mask.tolist()
    
#img_labels = [[0] * img_len_x for _ in range(img_len_y)]


prev_row = img_labels[0] # for the first iteration of i where the boarder of the image is set all labels to zero

start_time = time.perf_counter()
for i in range(img_len_y):
    
    mask_row_i = img_mask_list[i]
    row = img_labels[i] # no copy: "row" is a second name for img_labels[1]
    left_label = 0 # initialize at 0 at the left pixture edge
    
    for j in range(img_len_x):
        
        if mask_row_i[j]:
            # Edge guard to avoid indexing into -1 which would be the edge on the opposite side of the image
            #up_label   = img_labels[i-1][j] if i > 0 else 0
            #left_label = img_labels[i][j-1] if j > 0 else 0

            up_label = prev_row[j]
                        
            # Case 1: Both the upper and the left label are empty meaning we detect a (new) object so increase the counter for the (provisional) labels
            if (up_label == 0) and (left_label == 0):
                label_count += 1
                label = label_count
            # Case 2: The left label is zero but not the upper one
            elif left_label==0:
                label = up_label
            # Case 3: The upper label is zero but not the left one  
            elif up_label==0:
                label = left_label
            # Case 4: Both upper and left label are the same but nonzero            
            elif left_label==up_label: # If both are equal we just propagate the same (provisional) label. We chose here the left label for convention
                label = left_label
            # Case 5: Two different objects are connected when both uper and left pixels are different but nonzero!      
            else:
                label = left_label # We also have to propagate in this case the label. We chose here the left label for convention
                union(up_label, left_label, parent)

            row[j] = label
            #img_labels[i][j] = label
            left_label = label # neighbour of pixel j+1 which becomes in the next round the left neighbour of pixel j
        
        else: # the current pixel is empty, so the left neighbour of the pixel in next round will be too
            left_label = 0
        
    prev_row = row       
     
# Drop the entries that where over preallocated
parent = parent[0:label_count + 1]

mid_time = time.perf_counter()

# Flatten on the list (parent[k] <= k, so one forward pass is enough)
len_parent = len(parent)
for k in range(len_parent):
    parent[k] = parent[parent[k]]

# Second pass: vectorized relabel, back in numpy
parent = np.array(parent)
root_idx = parent == np.arange(len_parent)
label_map = np.zeros(len_parent, dtype=int)
label_map[root_idx] = np.arange(np.count_nonzero(root_idx))
final_map = label_map[parent]
img_labels = final_map[np.array(img_labels)]


end_loop2_time = time.perf_counter()

execution_time = mid_time - start_time
print(f"Loop 1 Execution Time: {1000*execution_time:.3f} ms")

execution2_time = end_loop2_time - mid_time
print(f"Loop 2 Execution Time: {1000*execution2_time:.3f} ms \n")

total_execution_time = end_loop2_time - start_time
print(f"Both Loops Execution Time: {1000*total_execution_time:.3f} ms \n")


# print(np.array(img_labels))

fun_start_time = time.perf_counter()
img_labels = connected_component_labeling(img_mask)
fun_end_time = time.perf_counter()
total_fun_execution_time = fun_end_time - fun_start_time
print(f"CLL Function Execution Time: {1000*total_fun_execution_time:.3f} ms \n")


#print('Provisional Labels:', img_labels)

#print('Parent:', parent, '\n')


#plt.figure(figsize=(16, 12))
#plt.imshow(img_labels, cmap='Accent')
#plt.show()

img_labels = np.array(img_labels)

fig, ax = plt.subplots(figsize=(14, 10))

im = ax.imshow(img_labels, cmap="inferno", interpolation="nearest", vmin=0, vmax=img_labels.max())

for label in range(1, int(img_labels.max()) + 1):

    y, x = np.where(img_labels == label)

    if len(x) == 0:
        continue

    # Use median rather than mean for a more robust visual center
    x_center = np.median(x)
    y_center = np.median(y)

    ax.text(x_center, y_center, str(label), color="white", fontsize=7, ha="center", va="center")

plt.colorbar(im, ax=ax, label="Component label")
#plt.show()

