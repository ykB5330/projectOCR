import numpy as np

def manual_median_filter(gray_data, kernel_size=3):


    if not isinstance(gray_data, np.ndarray):
        gray_data = np.array(gray_data, dtype=np.uint8)
    
    h, w = gray_data.shape
    pad = kernel_size // 2

    padded = np.pad(gray_data, pad_width=pad, mode='edge')
    

    result = np.zeros_like(gray_data)
    
 
    for i in range(h):
        for j in range(w):
 
            window = padded[i:i + kernel_size, j:j + kernel_size]
            flat = window.flatten()
            sorted_flat = np.sort(flat) 
            median_val = sorted_flat[len(sorted_flat) // 2]
            result[i, j] = median_val
    
    return result.astype(np.uint8)
