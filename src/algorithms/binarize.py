import numpy as np

def manual_adaptive_binarize(gray_img, window_size=25, C=5):
    height, width = gray_img.shape
    binary_result = np.zeros((height, width), dtype=np.uint8)
    half_win = window_size // 2

    for y in range(height):
        for x in range(width):
            top = max(0, y - half_win)
            bottom = min(height, y + half_win + 1)
            left = max(0, x - half_win)
            right = min(width, x + half_win + 1)

            local_area = gray_img[top:bottom, left:right]
            local_threshold = np.mean(local_area) - C  # 减去偏移C

            if gray_img[y, x] < local_threshold:
                binary_result[y, x] = 0
            else:
                binary_result[y, x] = 255
    return binary_result