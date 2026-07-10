"""
图像预处理模块
整合所有预处理步骤：灰度化 → 滤波 → 二值化 → 倾斜矫正
"""
import numpy as np
from PIL import Image
from src.algorithms.grayscale import weighted_rgb2gray
from src.algorithms.binarize import manual_adaptive_binarize
from src.algorithms.filter import manual_median_filter
from src.algorithms.deskew import hough_transform, get_skew_angle, rotate_image
import src.algorithms.resize as pyramid


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
    
    return rotated_gray_pil


preprocessed_img=preprocess(r"C:\Users\AW\Desktop\general_ocr_002.png")
preprocessed_img.save(r"C:\Users\AW\Desktop\general_ocr_002_preprocessed.png")