from PIL import Image
import numpy as np
from gray_tool import weighted_rgb2gray
from two import manual_adaptive_binarize
from three import manual_median_filter
import four 
INPUT_PATH = "test.jpg"
OUTPUT_BIN = "out_final.jpg"

check_y, check_x = 60, 60

if __name__ == "__main__":
    img = Image.open(INPUT_PATH)
    rgb_data = np.array(img)

    # 1. 自定义灰度转换
    gray_data = weighted_rgb2gray(rgb_data)
    gray_img = Image.fromarray(gray_data)

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
    med_img = Image.fromarray(med_data)

    # 3. 自适应二值化
    bin_data = manual_adaptive_binarize(med_data, window_size=15)
    bin_img = Image.fromarray(bin_data)
    #4. 2倍下采样
    #5. 2倍上采样
    img_np = np.array(img)
    img_down = four.down_sample_2x(img_np)
    img_up = four.up_sample_2x(img_down)


    result_np = bin_data

    # 只保存最终结果
    bin_img.save(OUTPUT_BIN)
    print(f"最终处理结果已保存：{OUTPUT_BIN}")

    print("\n统一存储处理后图像的numpy数组变量 result_np：")
    print(f"数组形状：{result_np.shape}")
    print(f"数据类型：{result_np.dtype}")
    print(result_np)

    # 只显示最终结果
    bin_img.show()