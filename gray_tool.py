import numpy as np

def weighted_rgb2gray(rgb_array):
    """
    纯手写加权灰度化，不使用任何内置灰度转换接口
    formula: gray = 0.299R + 0.587G + 0.114B
    参数：rgb_array 三维numpy数组 (H,W,3)
    返回：单通道灰度二维数组 (H,W)
    """
    h, w = rgb_array.shape[:2]
    gray_arr = np.zeros((h, w), dtype=np.uint8)

    # 双层循环逐像素手动计算
    for y in range(h):
        for x in range(w):
            r = rgb_array[y, x, 0]
            g = rgb_array[y, x, 1]
            b = rgb_array[y, x, 2]
            res = 0.299 * r + 0.587 * g + 0.114 * b
            gray_arr[y, x] = int(res)
    return gray_arr