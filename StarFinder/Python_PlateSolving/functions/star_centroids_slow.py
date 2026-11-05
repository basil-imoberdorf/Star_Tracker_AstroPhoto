import numpy as np

def star_stats(img_label, Intenisty_img):
    
    len_y, len_x = img_label.shape
        
    n_labels = img_label.max()
    x_center = np.zeros(n_labels)
    y_center = np.zeros(n_labels)
       
    # Erstellt die Vektoren von 1 bis len_x / len_y (Matlab-Logik inklusive der Endpunkte)
    x_range = np.arange(len_x)
    y_range = np.arange(len_y)
    x_grid, y_grid = np.meshgrid(x_range, y_range)
        
    for i in range(n_labels):
        
        label_idx = img_label == i + 1  # the first label is 1 
        
        # Reject objects consisting of 3 or less pixels
        if np.count_nonzero(label_idx) > 3:

            x_pos = x_grid[label_idx]
            y_pos = y_grid[label_idx]
            I_weights = Intenisty_img[label_idx]

            sum_weights = np.sum(I_weights)
            x_center[i] = np.sum(I_weights * x_pos) / sum_weights
            y_center[i] = np.sum(I_weights * y_pos) / sum_weights
    
    # Remove the zeros from the rejected objects
    x_center = x_center[x_center != 0]
    y_center = y_center[y_center != 0]
    
    return x_center, y_center
    
    
    