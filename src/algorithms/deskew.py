import numpy as np
from PIL import Image


def detect_edges(binary_image):
    """
    手动实现Sobel边缘检测，仅保留二值图中的边缘像素点。
    对二值图计算水平和垂直梯度，合并梯度幅值后阈值筛选边缘点。

    Args:
        binary_image: 二值图像（0/255）

    Returns:
        edge_map: 二值边缘图，仅边缘点为255
    """
    h, w = binary_image.shape
    edge_map = np.zeros((h, w), dtype=np.uint8)

    # Sobel卷积核：水平方向Gx检测垂直边缘，垂直方向Gy检测水平边缘
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            # 提取3x3邻域
            p00 = float(binary_image[y-1, x-1])
            p01 = float(binary_image[y-1, x])
            p02 = float(binary_image[y-1, x+1])
            p10 = float(binary_image[y, x-1])
            p12 = float(binary_image[y, x+1])
            p20 = float(binary_image[y+1, x-1])
            p21 = float(binary_image[y+1, x])
            p22 = float(binary_image[y+1, x+1])

            # Sobel Gx：水平梯度
            gx = (-p00 + p02 - 2 * p10 + 2 * p12 - p20 + p22)
            # Sobel Gy：垂直梯度
            gy = (-p00 - 2 * p01 - p02 + p20 + 2 * p21 + p22)

            # 梯度幅值
            mag = np.sqrt(gx * gx + gy * gy)

            # 阈值筛选（边缘点梯度较大）
            if mag > 100:
                edge_map[y, x] = 255

    return edge_map


def hough_transform(binary_image):
    """
    手动实现Hough变换直线检测。
    对二值图中的边缘点进行极坐标空间投票，检测直线参数。

    Args:
        binary_image: 二值图像（0/255）

    Returns:
        accumulator: Hough投票累加器
        thetas: 角度数组（弧度）
        rhos: 距离数组
    """
    h, w = binary_image.shape
    diag_len = int(np.ceil(np.sqrt(h**2 + w**2)))
    thetas = np.deg2rad(np.arange(0, 180))
    num_thetas = len(thetas)
    rhos = np.arange(-diag_len, diag_len + 1)
    num_rhos = len(rhos)
    accumulator = np.zeros((num_rhos, num_thetas), dtype=np.int64)

    # 仅对边缘点投票（先进行边缘检测，减少噪声干扰）
    edge_map = detect_edges(binary_image)
    y_idxs, x_idxs = np.nonzero(edge_map)
    if len(x_idxs) == 0:
        return accumulator, thetas, rhos

    cos_vals = np.cos(thetas)
    sin_vals = np.sin(thetas)
    for t_idx in range(num_thetas):
        rho_vals = (x_idxs * cos_vals[t_idx] + y_idxs * sin_vals[t_idx])
        rho_int = np.round(rho_vals).astype(np.int32) + diag_len
        rho_int = np.clip(rho_int, 0, num_rhos - 1)
        counts = np.bincount(rho_int, minlength=num_rhos)
        accumulator[:, t_idx] = counts

    return accumulator, thetas, rhos


def get_skew_angle(accumulator, thetas, rhos):
    if np.max(accumulator) == 0:
        return 0.0

    col_max = np.max(accumulator, axis=0) 
    theta_deg = np.rad2deg(thetas) 


    sigma = 15.0
    weights = np.exp(-((theta_deg - 90) ** 2) / (2 * sigma ** 2))
    weighted_votes = col_max * weights


    best_idx = np.argmax(weighted_votes)
    best_theta = theta_deg[best_idx]
    best_vote = col_max[best_idx]

    if abs(best_theta - 90) > 30:
        if best_vote < 0.6 * np.max(col_max):
            return 0.0

    rotation_angle = 90.0 - best_theta
    if abs(rotation_angle) > 45.0:
        return 0.0

    return rotation_angle


def rotate_image(image_pil, angle):
    """旋转图像，使用白色背景填充（OCR场景避免黑色边角干扰识别）"""
    # 先转为RGBA模式进行旋转，再合成到白色背景上
    if image_pil.mode != 'RGBA':
        image_rgba = image_pil.convert('RGBA')
    else:
        image_rgba = image_pil
    rotated_rgba = image_rgba.rotate(angle, expand=True, resample=Image.BICUBIC)
    # 创建白色背景并合成
    background = Image.new('RGBA', rotated_rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(background, rotated_rgba)
    return composited.convert('L')  # 转回灰度图
