import numpy as np

def weighted_rgb2gray(rgb_array):

    gray = (0.299 * rgb_array[:, :, 0] +
            0.587 * rgb_array[:, :, 1] +
            0.114 * rgb_array[:, :, 2])

    min_val = gray.min()
    max_val = gray.max()
    if max_val > min_val:
        gray = (gray - min_val) / (max_val - min_val) * 255
    else:
        gray = gray  # 不做拉伸
    
    gray = np.clip(gray, 0, 255).astype(np.uint8)
    return gray