import time
import numpy as np
import matplotlib.pyplot as plt

from functions.ccl_naive import connected_component_labeling_naive
from functions.ccl_numba import connected_component_labeling_numba
from functions.ccl import connected_component_labeling
from scipy.ndimage import label


# Create synthetic mask for testing
len_y = 2500
len_x = 1900

mask = np.random.rand(len_y, len_x) > 0.9         # boolean mask with ~10 % foreground pixels; connected_component_labeling_numba only accepts bool (same density as the former np.round(rand - 0.4))
connected_component_labeling_numba(mask)        # first call compiles: don't time this one

# Time my naive approach to Connected Component Labeling
start_time = time.perf_counter()
img_labels_naive = connected_component_labeling_naive(mask)
end_time = time.perf_counter()

execution_time = end_time - start_time
print(f"Naive Execution Time: {1000*execution_time:.2f} ms \n")

# Time my better appraoch to Connected Component Labeling
start_time = time.perf_counter()
img_labels_liststyle = connected_component_labeling(mask)
end_time = time.perf_counter()

execution_time = end_time - start_time
print(f"List-style Execution Time: {1000*execution_time:.2f} ms \n")

# Time Claude Numba approach to Connected Component Labeling
start_time = time.perf_counter()
img_labels_numba = connected_component_labeling_numba(mask)
end_time = time.perf_counter()

execution_time = end_time - start_time
print(f"Numba Execution Time: {1000*execution_time:.2f} ms \n")

# Time the SciPy implementation
start_time = time.perf_counter()
img_labels_scipy = label(mask)
end_time = time.perf_counter()

execution_time = end_time - start_time
print(f"SciPy Execution Time: {1000*execution_time:.2f} ms \n")


# Check if both solutions are equal
print('SciPy solution is same as naive : ', (img_labels_naive==img_labels_scipy[0]).all())
# Check if both solutions are equal
print('SciPy solution is same as My : ', (img_labels_liststyle==img_labels_scipy[0]).all())
# Check if both solutions are equal
print('SciPy solution is same as Numba : ', (img_labels_numba==img_labels_scipy[0]).all())



# Plot both results
fig, ax = plt.subplots(1,2, figsize=(16, 6), sharex=True, sharey=True)

ax[0].imshow(img_labels_scipy[0], cmap='magma')
ax[0].set_title('SciPy')
ax[1].imshow(img_labels_numba, cmap='magma')
ax[1].set_title('Numba')

plt.show()







