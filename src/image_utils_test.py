from typing import final
from PIL import Image
import numpy as np
from algorithms.grayscale import weighted_rgb2gray
from algorithms.binarize import manual_adaptive_binarize
from algorithms.filter import manual_median_filter
from algorithms.deskew import hough_transform, get_skew_angle, rotate_image
import algorithms.resize as pyramid
from algorithms.USM import usm_sharpen
from algorithms.contrast_stretch import contrast_stretch
from algorithms.gamma import gamma_correction

INPUT_PATH = "test.jpg"
OUTPUT_FINAL = "out_final.jpg"

check_y, check_x = 60, 60

if __name__ == "__main__":
    img_pil = Image.open(INPUT_PATH)
    rgb_data = np.array(img_pil)

    # 1. 自定义灰度转换
    gray_data = weighted_rgb2gray(rgb_data)
    gray_pil = Image.fromarray(gray_data)

    # 像素校验
    r, g, b = rgb_data[check_y, check_x]
    calc = 0.299 * r + 0.587 * g + 0.114 * b
    pixel_out = gray_data[check_y, check_x]
    print(f"\n校验像素({check_y},{check_x})")
    print(f"R:{r} G:{g} B:{b}")
    print(f"公式计算值：{calc:.2f} 输出灰度值：{pixel_out}")

    # 2. 中值滤波
    gray_list = gray_data.tolist()
    med_list = manual_median_filter(gray_list, kernel_size=3)
    med_data = np.array(med_list, dtype=np.uint8)
    med_pil = Image.fromarray(med_data)
    #金字塔变换
    med_down = pyramid.down_sample_2x(med_data)
    # 3. 自适应二值化
    bin_down = manual_adaptive_binarize(med_down, window_size=15)
    bin_down_pil = Image.fromarray(bin_down)


    #4. 霍夫变换检测倾斜角度并旋转
    accumulator, thetas, rhos = hough_transform(bin_down)
    diag_len = int(np.ceil(np.sqrt(bin_down.shape[0]**2 + bin_down.shape[1]**2)))
    angle = get_skew_angle(accumulator, thetas, rhos, diag_len)
    print(f"检测到的倾斜角度：{angle:.2f}度")

    if abs(angle)>1:
        rotated_gray_pil=rotate_image(med_pil,angle)
    else:
        rotated_gray_pil = gray_pil
    rotated_gray_data=np.array(rotated_gray_pil)
    #5. USM锐化
    usm_data=usm_sharpen(rotated_gray_data, radius=1.0, amount=1.0,threshold=0)

    #6. 伽马校正
    gamma_corrected_data=gamma_correction(usm_data, gamma=1.2)

    #7. 对比度拉伸
    final_pil=Image.fromarray(contrast_stretch(gamma_corrected_data,low_percent=2,high_percent=98))

    #输出最终结果
    final_pil.save(OUTPUT_FINAL)
    
    print(f"最终处理结果已保存：{OUTPUT_FINAL}")

    final_pil.show()


