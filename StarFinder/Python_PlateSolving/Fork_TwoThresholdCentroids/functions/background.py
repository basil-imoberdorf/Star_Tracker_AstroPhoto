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


#---------------------------------------------------------------------------------------------------------------------------
# Main function 
def estimate_bg_and_noise_map(img, tilesize=128, method='lin'):
    # a) Kappa-Sigma Clipping on tiled grid to get a grid of background levle and noise estimates
    img_len_y, img_len_x = img.shape

    n_tiles_x = int(np.ceil(img_len_x / tilesize))
    n_tiles_y = int(np.ceil(img_len_y / tilesize))

    background_level_grid = np.zeros([n_tiles_y, n_tiles_x])
    background_noise_grid = np.zeros([n_tiles_y, n_tiles_x])

    for i in range(n_tiles_y):
        for j in range(n_tiles_x):     

            # Calculate pixel boundary indices (handles edges elegantly)
            x_start = j * tilesize
            y_start = i * tilesize
                    
            x_end = min((j + 1) * tilesize, img_len_x) # With min() we snap back to th emaximum length if the running grid is bigger than the matrix is long in that direction
            y_end = min((i + 1) * tilesize, img_len_y) 
                            
            # Extract the current tile i,j 
            tile_ij = img[y_start:y_end, x_start:x_end]
            
            # print('\nTile i =', i,', j =',j, ' has shape :', tile_ij.shape)
            background_level, background_noise, keep_mask = bg_robust_kappa_sigma_clipping(tile_ij, kappa=3.0, max_iterations=20)
            background_level_grid[i, j] = background_level
            background_noise_grid[i, j] = background_noise  
            

    # b) 3x3 Median filter on the background grids
    background_level_grid_smooth = background_level_grid.copy()
    background_noise_grid_smooth = background_noise_grid.copy()
    for i in range(n_tiles_y):
        for j in range(n_tiles_x):
            
            x_start = max(j-1, 0)
            y_start = max(i-1, 0)
                    
            x_end = min(j+2, n_tiles_x) 
            y_end = min(i+2, n_tiles_y)   
            
            background_level_grid_smooth[i, j] = np.median(background_level_grid[y_start:y_end, x_start:x_end])
            background_noise_grid_smooth[i, j] = np.median(background_noise_grid[y_start:y_end, x_start:x_end])


    # c) Interpolate background level grid to full resolution to substract the background without introudcing artifacts on tile edges
    from scipy.interpolate import RectBivariateSpline
    yy, xx = np.arange(img_len_y), np.arange(img_len_x)

    # Get tile-center coordinates (half-pixel correct, handles partial edge tiles
    yc = np.array([(i*tilesize + min((i+1)*tilesize, img_len_y) - 1) / 2 for i in range(n_tiles_y)])
    xc = np.array([(j*tilesize + min((j+1)*tilesize, img_len_x) - 1) / 2 for j in range(n_tiles_x)])

    if (method == 'lin'):
        background_map = RectBivariateSpline(yc, xc, background_level_grid_smooth, kx=1, ky=1)(yy, xx)
        noise_map = RectBivariateSpline(yc, xc, background_noise_grid_smooth, kx=1, ky=1)(yy, xx)
    elif (method == 'cub'):
        background_map = RectBivariateSpline(yc, xc, background_level_grid_smooth, kx=3, ky=3)(yy, xx)
        noise_map = RectBivariateSpline(yc, xc, background_noise_grid_smooth, kx=3, ky=3)(yy, xx)       
    else:
        print('Error: Unknown method string. Chose "lin" or "cub"')

    return background_map, noise_map