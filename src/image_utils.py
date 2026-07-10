"""
图像预处理模块
整合所有预处理步骤：灰度化 → 滤波 → 二值化 → 倾斜矫正
"""
import cv2
import numpy as np
from PIL import Image
from algorithms.grayscale import weighted_rgb2gray
from algorithms.binarize import manual_adaptive_binarize
from algorithms.filter import manual_median_filter
from algorithms.deskew import hough_transform, get_skew_angle, rotate_image
import algorithms.resize as pyramid


def preprocess(image_path: str):
    """
    完整预处理流程
    
    Args:
        image_path: 图片路径
    
    Returns:
        PIL.Image: 预处理后的二值图
    """
    # ===== 1. 加载图片 =====
    img_pil = Image.open(image_path)
    if img_pil.mode != 'RGB':
        img_pil = img_pil.convert('RGB')
    rgb_data = np.array(img_pil)
    
    # ===== 2. 灰度化 =====
    gray_data = weighted_rgb2gray(rgb_data)
    
    # ===== 3. 中值滤波 =====
    gray_list = gray_data.tolist()
    med_list = manual_median_filter(gray_list, kernel_size=3)
    med_data = np.array(med_list, dtype=np.uint8)
    
    # ===== 4. 金字塔下采样（缩小2倍） =====
    med_down = pyramid.down_sample_2x(med_data)
    
    # ===== 5. 自适应二值化 =====
    bin_down = manual_adaptive_binarize(med_down, window_size=15)
    bin_down_pil = Image.fromarray(bin_down)
    
    # ===== 6. 霍夫变换检测倾斜角度 =====
    accumulator, thetas, rhos = hough_transform(bin_down)
    diag_len = int(np.ceil(np.sqrt(bin_down.shape[0]**2 + bin_down.shape[1]**2)))
    angle = get_skew_angle(accumulator, thetas, rhos, diag_len)
    print(f"检测到的倾斜角度：{angle:.2f}度")
    
    # ===== 7. 旋转矫正 =====
    if abs(angle) > 0.5:
        rotated_gray_pil = rotate_image(bin_down_pil, angle)
    else:
        rotated_gray_pil = bin_down_pil
    rotated_gray_np = np.array(rotated_gray_pil, dtype=np.uint8)
    processed = cv2.cvtColor(rotated_gray_np, cv2.COLOR_GRAY2BGR)
    return processed