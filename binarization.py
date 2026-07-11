import numpy as np

def manual_adaptive_binarize(gray_img, window_size=25, C=5):

    height, width = gray_img.shape
    half_win = window_size // 2


    integral = np.zeros((height + 1, width + 1), dtype=np.uint64)

    integral[1:, 1:] = np.cumsum(np.cumsum(gray_img, axis=0), axis=1)

    y = np.arange(height)[:, None] 
    x = np.arange(width)[None, :] 

    top    = np.maximum(0, y - half_win)
    bottom = np.minimum(height, y + half_win + 1)
    left   = np.maximum(0, x - half_win)
    right  = np.minimum(width, x + half_win + 1)

    sum_window = (integral[bottom, right] - integral[top, right]
                  - integral[bottom, left] + integral[top, left])

    area = (bottom - top) * (right - left) 

    mean = sum_window / area.astype(np.float64)
    threshold = mean - C
    binary = (gray_img >= threshold).astype(np.uint8) * 255

    return binary