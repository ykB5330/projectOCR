import numpy as np

def weighted_rgb2gray(rgb_array):
    h, w = rgb_array.shape[:2]
    gray_arr = np.zeros((h, w), dtype=np.float32)  # 先用浮点存储，不提前取整

    # 双层循环加权计算
    for y in range(h):
        for x in range(w):
            r = rgb_array[y, x, 0]
            g = rgb_array[y, x, 1]
            b = rgb_array[y, x, 2]
            val = 0.299 * r + 0.587 * g + 0.114 * b
            gray_arr[y, x] = val

    # OCR优化1：对比度拉伸，拉开黑白差距
    min_g = gray_arr.min()
    max_g = gray_arr.max()
    gray_arr = (gray_arr - min_g) / (max_g - min_g) * 255

    # OCR优化2：转uint8，限制0~255防止溢出
    gray_arr = gray_arr.astype(np.uint8)
    return gray_arr