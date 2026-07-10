import numpy as np
import PIL.Image as Image

def hough_transform(image):
    """
    向量化 Hough 变换，显著提升速度。
    """
    height, width = image.shape
    diag_len = int(np.ceil(np.sqrt(height**2 + width**2)))
    # 使用 2*diag_len+1 个 rho 值，确保索引不越界
    rhos = np.linspace(-diag_len, diag_len, 2 * diag_len + 1)
    thetas = np.deg2rad(np.arange(-90, 90, 1.0))
    accumulator = np.zeros((len(rhos), len(thetas)), dtype=np.int64)

    y_idxs, x_idxs = np.nonzero(image)
    if len(x_idxs) == 0:
        return accumulator, thetas, rhos

    # 预计算所有角度的 cos 和 sin
    cos_vals = np.cos(thetas)
    sin_vals = np.sin(thetas)

    # 对每个角度，一次性计算所有边缘点的 rho 值，并用 bincount 统计
    for t_idx in range(len(thetas)):
        rho_vals = np.round(x_idxs * cos_vals[t_idx] + y_idxs * sin_vals[t_idx]).astype(np.int32) + diag_len
        # 限制在有效索引范围内（防止因舍入误差导致越界）
        rho_vals = np.clip(rho_vals, 0, len(rhos) - 1)
        counts = np.bincount(rho_vals, minlength=len(rhos))
        accumulator[:, t_idx] = counts

    return accumulator, thetas, rhos


def get_skew_angle(accumulator, thetas, rhos, diag_len):
    """
    修正角度计算：将检测到的直线法线角转换为实际倾斜角，
    并返回可供 PIL.Image.rotate() 直接使用的旋转角度。
    """
    max_idx = np.unravel_index(np.argmax(accumulator), accumulator.shape)
    rho_idx, theta_idx = max_idx
    angle_rad = thetas[theta_idx]

    # 直线方向角（与 x 轴夹角） = theta + 90°
    line_angle = np.degrees(angle_rad) + 90.0
    # 归一化到 [-90, 90]
    line_angle = line_angle % 180.0
    if line_angle > 90.0:
        line_angle -= 180.0

    # 返回需要的旋转角度（逆时针为正），校正倾斜
    angle_deg = -line_angle
    return angle_deg


def rotate_image(img_pil, angle):
    return img_pil.rotate(angle, expand=True, fillcolor=255)