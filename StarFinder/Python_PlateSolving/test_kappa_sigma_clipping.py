
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def bg_robust_kappa_sigma_clipping(array, kappa=2.0, max_iterations=10):
    """
    Perform robust kappa-sigma clipping on the input data to remove outliers and estimate the background level.
    Clipped data is not reused for the next iteration to ensure that the background estimation is not biased by replaced values.

    Parameters:
    - array: 2D NumPy array of pixel values.
    - kappa: The number of standard deviations to use for detection.
    - max_iterations: Maximum number of iterations for outlier removal.

    Returns:
    - background_estimate: The estimated background level after robust kappa-sigma clipping.
    - keep_mask: 2D boolean NumPy array indicating which values belong to the background (True) and which are considered outliers (False).
    """

    keep_mask = np.ones(array.shape, dtype=bool)
    last_mask = np.zeros(array.shape, dtype=bool)
    
    for iteration in range(max_iterations):
                       
        # Use robust statistics to estimate the background level and standard deviation   
        median = np.median(array[keep_mask])
        MAD = np.median(np.abs(array[keep_mask] - median))
        sigma = 1.4826 * MAD 
               
        # Get the mask of values to keep based on the kappa-sigma clipping criteria
        keep_mask = (array - median) < (kappa * sigma)
                
        print(f"Iteration {iteration + 1}: median = {np.round(median, 2)}, std_dev = {np.round(sigma, 2)}, threshold = {np.round(kappa * sigma, 2)}, kept pixels = {np.sum(keep_mask)}")
    
        if np.array_equal(keep_mask, last_mask):
            print("No more outliers detected. Stopping iterations.")
            
            break
        last_mask = keep_mask.copy()  # Store the last mask to check for convergence in the next iteration
        
        if iteration == max_iterations - 1:
            print("Maximum iterations reached. Check convergence!")
    
    background_level = median # estimate the background level as the median of the background pixels
    background_noise = sigma  # estimate the background noise as the standard deviation of the background pixels
    
    return background_level, background_noise, keep_mask



mu_bg = 258  # Mean background level
sigma_bg = 16  # Standard deviation of the background noise


len_x = 4000
len_y = 3000

arr = np.random.normal(mu_bg, sigma_bg, (len_y, len_x))

print(f"Synthetic background - min: {np.round(np.min(arr), 2)}")  # Calculate the minimum of the array
print(f"Synthetic background - max: {np.round(np.max(arr), 2)}")  # Calculate the maximum of the array
print(f"Synthetic background - median: {np.round(np.median(arr), 2)}")  # Calculate the median of the array
print(f"Synthetic background - std dev: {np.round(np.std(arr), 2)}, \n")  # Calculate the standard deviation of the array

plt.imshow(arr, cmap='gray')
plt.clim(0, 4095)  # Set color limits to the full range of 12-bit data
plt.colorbar(label='Pixel Value')
plt.show()

star_mask = np.random.rand(len_y, len_x) < 0.1  # Randomly generate a mask for stars (10% of the pixels)
arr[star_mask] += np.random.normal(3000, 50, np.sum(star_mask))  # Add stars with higher intensity

star_mask = np.random.rand(len_y, len_x) < 0.1  # Randomly generate a mask for stars (10% of the pixels)
arr[star_mask] += np.random.normal(3800, 10, np.sum(star_mask))  # Add stars with higher intensity

plt.imshow(arr, cmap='gray')
plt.clim(0, 4095)  # Set color limits to the full range of 12-bit data
plt.colorbar(label='Pixel Value')
plt.show()

print(f"Synthetic background with stars - min: {np.round(np.min(arr), 2)}")  # Calculate the minimum of the array
print(f"Synthetic background with stars - max: {np.round(np.max(arr), 2)}")  # Calculate the maximum of the array
print(f"Synthetic background with stars - median: {np.round(np.median(arr), 2)}")  # Calculate the median of the array
print(f"Synthetic background with stars - std dev: {np.round(np.std(arr), 2)}, \n")  # Calculate the standard deviation of the array


background_estimate, background_noise, keep_mask = bg_robust_kappa_sigma_clipping(arr, kappa=3)

background = arr[keep_mask]

print(f"\nKappa-sigma clipped background - min: {np.round(np.min(background), 2)}")  # Calculate the minimum of the array
print(f"Kappa-sigma clipped background - max: {np.round(np.max(background), 2)}")  # Calculate the maximum of the array
print(f"Kappa-sigma clipped background - median: {np.round(np.median(background), 2)}")  # Calculate the median of the array
print(f"Kappa-sigma clipped background - std dev: {np.round(np.std(background), 2)}, \n")  # Calculate the standard deviation of the array

print(f"Estimated background level: {np.round(background_estimate, 2)}")
print(f"Estimated background noise: {np.round(background_noise, 2)}")




