import numpy as np

def subtract_blacklv(img_raw, black_lv):
    """
    Remove the black level added by the camera to each pixel.
    The indexing is for the Bayer pattern found in the Olympus OM-D EM1 MK2

    Parameters:
    - img_raw: 2D NumPy array of pixel values.
    - black_lv: List containg the black value for each of the four pixels of the Bayer grid

    Returns:
    - img_black_subtracted: 2D NumPy array of float32 pixel values
    """
    
    bl_r, bl_gr, bl_gb, bl_b = black_lv

    # Apply the subtraction to the 2x2 interleaved Bayer grid
    img_black_subtracted = img_raw.copy().astype(np.float32)  # Copy and convert to float for processing 
    img_black_subtracted[0::2, 0::2] -= bl_r   # Top-left of the 2x2 block (Even rows, Even cols)
    img_black_subtracted[0::2, 1::2] -= bl_gr  # Top-right of the 2x2 block (Even rows, Odd cols)
    img_black_subtracted[1::2, 0::2] -= bl_gb  # Bottom-left of the 2x2 block (Odd rows, Even cols)
    img_black_subtracted[1::2, 1::2] -= bl_b   # Bottom-right of the 2x2 block (Odd rows, Odd cols)
    
    return img_black_subtracted