import numpy as np
from PIL import Image

def down_sample_2x(img_arr):

    if img_arr.ndim == 2:
        # 二维灰度图
        H, W = img_arr.shape
        C = 1
        is_gray = True
    else:
        # 三维彩色图
        H, W, C = img_arr.shape
        is_gray = False

    new_H = H // 2
    new_W = W // 2
    dst = np.zeros((new_H, new_W, C), dtype=np.uint8)

    # 隔行隔列采样，只取偶数坐标像素
    for y in range(new_H):
        for x in range(new_W):
            dst[y, x] = img_arr[2 * y, 2 * x]

    # 灰度图去除通道维度，变回二维数组
    if is_gray:
        dst = np.squeeze(dst, axis=-1)
    return dst


def up_sample_2x(img_arr):
    if img_arr.ndim == 2:
        H, W = img_arr.shape
        C = 1
        is_gray = True
    else:
        H, W, C = img_arr.shape
        is_gray = False

    new_H = H * 2
    new_W = W * 2
    dst = np.zeros((new_H, new_W, C), dtype=np.uint8)

    # 一个源像素填充2×2区域
    for y in range(new_H):
        for x in range(new_W):
            src_y = y // 2
            src_x = x // 2
            dst[y, x] = img_arr[src_y, src_x]

    if is_gray:
        dst = np.squeeze(dst, axis=-1)
    return dst