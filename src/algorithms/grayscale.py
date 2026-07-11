import numpy as np

def weighted_rgb2gray(rgb_array):
    """
    加权灰度化（NumPy向量化优化版）
    输入：rgb_array - uint8 (H, W, 3)
    输出：gray - uint8 (H, W)
    完全兼容原接口，内部使用向量化加速。
    """
    # 向量化加权计算（广播乘法）
    gray = (0.299 * rgb_array[:, :, 0] +
            0.587 * rgb_array[:, :, 1] +
            0.114 * rgb_array[:, :, 2])

    # 对比度拉伸（与原逻辑完全一致）
    min_val = gray.min()
    max_val = gray.max()
    if max_val > min_val:
        gray = (gray - min_val) / (max_val - min_val) * 255
    # else: gray保持不变（均匀图像）

    # 安全裁剪并转为uint8（与原输出类型一致）
    gray = np.clip(gray, 0, 255).astype(np.uint8)
    return gray