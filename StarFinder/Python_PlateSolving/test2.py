import rawpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

kappa = 2


m = np.array([[1, 2, 3],
            [4, 5, 6],
            [7, 80, 90]])
print(type(m))
print(m)





keep_mask = np.ones(m.shape, dtype=bool)
print(keep_mask)

median = np.median(m[keep_mask])
MAD = np.median(np.abs(m[keep_mask] - median))
sigma = 1.4826 * MAD 

print(f"median ={np.round(median, 2)}, std_dev={np.round(sigma, 2)}, threshold={np.round(kappa * sigma, 2)}")
               
# Get the mask of values to keep based on the kappa-sigma clipping criteria
keep_mask = (m - median) < (kappa * sigma)
print(keep_mask)

m[keep_mask] = median  # Replace outliers with the median value
print(m)
