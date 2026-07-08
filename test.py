from PIL import Image
import numpy as np
# 导入自己写的灰度函数，无系统灰度接口
from gray_tool import weighted_rgb2gray

# 配置路径，自行修改
INPUT_PATH = "test.jpg"
OUTPUT_PATH = "result_gray.jpg"
check_y, check_x = 60, 60  # 校验像素坐标

if __name__ == "__main__":
    # 1. 读取原图
    img = Image.open(INPUT_PATH)
    rgb_data = np.array(img)

    # 2. 调用自定义灰度算法（无内置灰度接口）
    gray_data = weighted_rgb2gray(rgb_data)

    # 3. 保存处理完成图片
    gray_img = Image.fromarray(gray_data)
    gray_img.save(OUTPUT_PATH)
    print(f"灰度图已保存：{OUTPUT_PATH}")

    # 4. 像素数值验证
    r, g, b = rgb_data[check_y, check_x]
    calc = 0.299 * r + 0.587 * g + 0.114 * b
    pixel_out = gray_data[check_y, check_x]
    print(f"\n校验像素({check_y},{check_x})")
    print(f"R:{r} G:{g} B:{b}")
    print(f"公式计算值：{calc:.2f} 输出灰度值：{pixel_out}")

    # 展示原图与结果图
    img.show()
    gray_img.show()