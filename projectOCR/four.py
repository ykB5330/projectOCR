import numpy as np
from PIL import Image

def down_sample_2x(img_arr):
    H, W, C = img_arr.shape
    new_H = H // 2
    new_W = W // 2
    dst = np.zeros((new_H, new_W, C), dtype=np.uint8)
    for y in range(new_H):
        for x in range(new_W):
            dst[y, x] = img_arr[2 * y, 2 * x]
    return dst

def up_sample_2x(img_arr):
    H, W, C = img_arr.shape
    new_H = H * 2
    new_W = W * 2
    dst = np.zeros((new_H, new_W, C), dtype=np.uint8)
    for y in range(new_H):
        for x in range(new_W):
            src_y = y // 2
            src_x = x // 2
            dst[y, x] = img_arr[src_y, src_x]
    return dst

if __name__ == "__main__":
    img = Image.open("test.jpg")
    img_np = np.array(img)
    img_down = down_sample_2x(img_np)
    img_up = up_sample_2x(img_down)
    Image.fromarray(img_np).save("origin.jpg")
    Image.fromarray(img_down).save("down_2x.jpg")
    Image.fromarray(img_up).save("up_2x.jpg")
    print("原图尺寸：", img_np.shape[:2])
    print("下采样后尺寸：", img_down.shape[:2])
    print("上采样后尺寸：", img_up.shape[:2])