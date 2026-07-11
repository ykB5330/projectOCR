import numpy as np
from PIL import Image

def down_sample_2x(img_arr):

    H, W = img_arr.shape
    new_H = H // 2
    new_W = W // 2
    dst = np.zeros((new_H, new_W), dtype=np.uint8)
    for y in range(new_H):
        for x in range(new_W):
            # 对2x2像素块取均值，作为下采样后的像素值（块平均抗锯齿）
            block = img_arr[2*y : 2*y+2, 2*x : 2*x+2]
            dst[y, x] = np.uint8(np.mean(block))
    return dst

def up_sample_2x(img_arr):

    H, W = img_arr.shape
    new_H = H * 2
    new_W = W * 2
    dst = np.zeros((new_H, new_W), dtype=np.uint8)
    for y in range(new_H):
        for x in range(new_W):
            src_y = y // 2
            src_x = x // 2
            dst[y, x] = img_arr[src_y, src_x]
    return dst


if __name__ == "__main__":
    img = Image.open("test.jpg")
    img_np = np.array(img)
    gray = np.mean(img_np, axis=-1).astype(np.uint8)
    img_down = down_sample_2x(gray)
    img_up = up_sample_2x(img_down)
    Image.fromarray(gray).save("origin_gray.jpg")
    Image.fromarray(img_down).save("down_2x.jpg")
    Image.fromarray(img_up).save("up_2x.jpg")
    print("原图灰度尺寸：", gray.shape[:2])
    print("下采样后尺寸：", img_down.shape[:2])
    print("上采样后尺寸：", img_up.shape[:2])
    Image.fromarray(img_down).save("down_2x_avg.jpg")
    print("灰度原图尺寸", gray.shape)
    print("均值下采样尺寸", img_down.shape)
