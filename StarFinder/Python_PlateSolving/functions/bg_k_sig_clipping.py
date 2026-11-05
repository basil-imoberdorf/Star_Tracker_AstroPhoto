import numpy as np

def bg_robust_kappa_sigma_clipping(array, kappa=3.0, max_iterations=20):
    """
    Perform robust kappa-sigma clipping on the input data to remove outliers and estimate the background level.
    Clipped data is not reused for the next iteration to ensure that the background estimation is not biased by replaced values.

    Parameters:
    - array: 2D NumPy array of pixel values.
    - kappa: The number of standard deviations to use for detection.
    - max_iterations: Maximum number of iterations for outlier removal.

    Returns:
    - background_level: The estimated background level as numpy float64 value.
    - background_noise: The estimated background noise as numpy float64 value.
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
                
        #print(f"Iteration {iteration + 1}: median = {np.round(median, 2)}, std_dev = {np.round(sigma, 2)}, threshold = {np.round(kappa * sigma, 2)}, kept pixels = {np.sum(keep_mask)}")
    
        if np.array_equal(keep_mask, last_mask):
            #print("No more outliers detected. Stopping iterations.")
            break
        last_mask = keep_mask.copy()  # Store the last mask to check for convergence in the next iteration
        
        if iteration == max_iterations - 1:
            print("Maximum iterations reached. Check convergence!")
    
    background_level = np.mean(array[keep_mask].astype('float64')) # estimate the background level 
    background_noise = np.std(array[keep_mask].astype('float64'))  # estimate the background noise 
    
    return background_level, background_noise, keep_mask