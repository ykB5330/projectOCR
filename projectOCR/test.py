from PIL import Image
import numpy as np
from gray_tool import weighted_rgb2gray
from two import manual_adaptive_binarize
from three import manual_median_filter
import four 

from paddleocr import PaddleOCR


INPUT_PATH = "./projectOCR/imgs/test.png"
OUTPUT_BIN = "out_final.jpg"

check_y, check_x = 60, 60

if __name__ == "__main__":
    img = Image.open(INPUT_PATH)
    rgb_data = np.array(img)

    # 1. 自定义灰度转换
    gray_data = weighted_rgb2gray(rgb_data)

    # 像素校验
    r, g, b = rgb_data[check_y, check_x]
    calc = 0.299 * r + 0.587 * g + 0.114 * b
    pixel_out = gray_data[check_y, check_x]
    
    # 3. 下采样
    img_np = np.array(img)
    img_down = four.down_sample_2x(img_np)

    # 2. 中值滤波
    gray_list = gray_data.tolist()
    med_list = manual_median_filter(gray_list, kernel_size=3)
    med_data = np.array(med_list, dtype=np.uint8)
    

    # 4. 自适应二值化
    bin_data = manual_adaptive_binarize(med_data, window_size=15)
    bin_img = Image.fromarray(bin_data)

    # 5. 上采样
    #img_up = four.up_sample_2x(img_down)


    result_np = bin_data

    # 只保存最终结果
    bin_img.save(OUTPUT_BIN)
    # print(result_np)

    # 只显示最终结果
    #bin_img.show()



    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        engine="paddle",
    )
    result = ocr.predict(OUTPUT_BIN)
    for res in result:
        res.print()
        res.save_to_img("output")
        res.save_to_json("output")
        print(' '.join(res.json['res']['rec_texts']))




