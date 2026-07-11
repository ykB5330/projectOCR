"""Hough变换倾斜矫正算法测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from PIL import Image
from algorithms.deskew import (
    detect_edges, hough_transform, get_skew_angle, rotate_image
)


def test_detect_edges_blank():
    img = np.zeros((30, 30), dtype=np.uint8)
    edges = detect_edges(img)
    assert np.all(edges == 0)


def test_detect_edges_line():
    img = np.zeros((30, 30), dtype=np.uint8)
    img[:, 15] = 255
    edges = detect_edges(img)
    assert np.any(edges > 0)


def test_hough_empty():
    img = np.zeros((20, 20), dtype=np.uint8)
    acc, thetas, rhos = hough_transform(img)
    assert acc.shape[0] == len(rhos) and acc.shape[1] == len(thetas)


def test_get_skew_angle_empty():
    acc = np.zeros((100, 180), dtype=np.int64)
    thetas = np.deg2rad(np.arange(0, 180))
    rhos = np.arange(-50, 51)
    assert get_skew_angle(acc, thetas, rhos) == 0.0


def test_rotate_white_bg():
    img = Image.new('L', (100, 100), color=200)
    rotated = rotate_image(img, 15)
    arr = np.array(rotated)
    assert arr[0, 0] > 100  # 白底旋转，背景为白色


def test_rotate_zero():
    img = Image.new('L', (50, 50), color=150)
    rotated = rotate_image(img, 0)
    assert rotated.size == (50, 50)


def test_hough_output_shape():
    img = np.random.randint(0, 2, (50, 50), dtype=np.uint8) * 255
    acc, thetas, rhos = hough_transform(img)
    assert len(thetas) == 180 and acc.ndim == 2


if __name__ == "__main__":
    test_detect_edges_blank(); test_detect_edges_line()
    test_hough_empty(); test_get_skew_angle_empty()
    test_rotate_white_bg(); test_rotate_zero()
    test_hough_output_shape()
    print("✅ Hough倾斜矫正算法测试全部通过")
