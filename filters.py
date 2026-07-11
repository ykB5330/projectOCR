import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

def manual_median_filter(gray_data, kernel_size=3):

    if not isinstance(gray_data, np.ndarray):
        gray_data = np.array(gray_data, dtype=np.uint8)
    
    h, w = gray_data.shape
    pad = kernel_size // 2
    

    padded = np.pad(gray_data, pad_width=pad, mode='edge')
    
    windows = sliding_window_view(padded, window_shape=(kernel_size, kernel_size))
    
    result = np.median(windows, axis=(-2, -1))
    
    return result.astype(np.uint8)