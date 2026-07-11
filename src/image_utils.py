"""
图像预处理流水线 — 支持按步骤开关
"""
from PIL import Image
import numpy as np
from algorithms.grayscale import weighted_rgb2gray
from algorithms.binarize import manual_adaptive_binarize
from algorithms.filter import manual_median_filter
from algorithms.deskew import hough_transform, get_skew_angle, rotate_image
import algorithms.resize as pyramid
from algorithms.USM import usm_sharpen
from algorithms.gamma import gamma_correction
from algorithms.clahe import clahe_enhance

# 预处理步骤名称常量
ALL_STEPS = [
    'grayscale', 'median_filter', 'down_sample', 'binarize',
    'deskew', 'usm', 'gamma', 'clahe'
]


def preprocess(image_input, enabled_steps=None):
    """
    图像预处理流水线（按需执行）

    Args:
        image_input: str（文件路径）或 PIL.Image 对象
        enabled_steps: set，启用的步骤名。None=全部启用，空set=跳过全部

    Returns:
        numpy.ndarray: 预处理后的RGB图像数组
    """
    # 接受文件路径或PIL Image
    if isinstance(image_input, str):
        img_pil = Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        img_pil = image_input
    else:
        raise TypeError("image_input 必须是文件路径(str)或PIL.Image对象")

    rgb_data = np.array(img_pil)

    # 空集 = 不启用任何预处理，直接返回原图
    if enabled_steps is not None and len(enabled_steps) == 0:
        h, w = rgb_data.shape[:2]
        if max(h, w) > 2048:
            scale = 2048 / max(h, w)
            nh, nw = int(h * scale), int(w * scale)
            rgb_data = np.array(Image.fromarray(rgb_data).resize((nw, nh), Image.LANCZOS))
        return rgb_data

    def enabled(name):
        """检查步骤是否启用"""
        return enabled_steps is None or name in enabled_steps

    # ===== 1. 灰度化（其他步骤的基础，只要启用任何步骤就执行） =====
    gray_data = weighted_rgb2gray(rgb_data)
    current = gray_data
    med_pil = Image.fromarray(current)  # 用于后续旋转参考

    # ===== 2. 中值滤波 =====
    if enabled('median_filter'):
        gray_list = current.tolist()
        med_list = manual_median_filter(gray_list, kernel_size=3)
        current = np.array(med_list, dtype=np.uint8)
        med_pil = Image.fromarray(current)

    # ===== 3. 金字塔下采样 =====
    if enabled('down_sample'):
        current = pyramid.down_sample_2x(current)

    # ===== 4. 自适应二值化 =====
    if enabled('binarize'):
        current = manual_adaptive_binarize(current, window_size=15)

    # ===== 5. Hough倾斜矫正 =====
    if enabled('deskew'):
        # Hough需要二值图，如果没开二值化则临时二值化用于检测
        if enabled('binarize'):
            bin_for_hough = current
        else:
            bin_for_hough = manual_adaptive_binarize(current, window_size=15)

        accumulator, thetas, rhos = hough_transform(bin_for_hough)
        angle = get_skew_angle(accumulator, thetas, rhos)
        print(f"检测到的倾斜角度：{angle:.2f}度")
        if abs(angle) > 1:
            rotated_pil = rotate_image(med_pil, angle)
            current = np.array(rotated_pil)
        # 角度太小不旋转，current不变

    # ===== 6. USM锐化 =====
    if enabled('usm'):
        current = usm_sharpen(current, radius=1.0, amount=1.0, threshold=0)

    # ===== 7. 伽马校正 =====
    if enabled('gamma'):
        current = gamma_correction(current, gamma=1.2)

    # ===== 8. CLAHE增强 =====
    if enabled('clahe'):
        current = clahe_enhance(current, clip_limit=0.03, tile_size=8)

    # ===== 安全缩放：防止过大图片触发PaddleOCR推理上限 =====
    h, w = current.shape[:2]
    if max(h, w) > 2048:
        scale = 2048 / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        current = np.array(Image.fromarray(current).resize((new_w, new_h), Image.LANCZOS))

    # ===== 输出RGB =====
    final_pil = Image.fromarray(current)
    rgb_img = final_pil.convert('RGB')
    return np.array(rgb_img)
