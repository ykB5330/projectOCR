import numpy as np


def manual_median_filter(gray_matrix, kernel_size=3):
    """
    手动实现中值滤波（性能优化版）
    接口与原代码完全一致：
        输入：gray_matrix - 二维列表（list[list[int]]）
        输出：二维列表（list[list[int]]）

    内部使用 NumPy 加速排序，但返回值保持与原版一致。
    """
    # 1. 转为 NumPy 数组（内部处理）
    img = np.array(gray_matrix, dtype=np.uint8)
    h, w = img.shape
    pad = kernel_size // 2

    # 2. 边缘填充（复制边缘，与原版裁剪效果等价）
    padded = np.pad(img, pad_width=pad, mode='edge')

    # 3. 预分配输出数组
    result = np.zeros_like(img, dtype=np.uint8)

    # 4. 手动遍历每个像素（保留窗口滑动的手动实现）
    for i in range(h):
        for j in range(w):
            # 提取窗口（数组切片，索引由手动控制）
            window = padded[i:i + kernel_size, j:j + kernel_size]
            # 排序并取中值（使用 NumPy 的 C 级实现）
            sorted_flat = np.sort(window.ravel())
            median_val = sorted_flat[len(sorted_flat) // 2]
            result[i, j] = median_val

    # 5. 返回与原输入类型一致的二维列表
    return result.tolist()