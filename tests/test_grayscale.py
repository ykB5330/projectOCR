"""加权灰度化算法测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from algorithms.grayscale import weighted_rgb2gray


def test_pure_white():
    img = np.full((10, 10, 3), 255, dtype=np.uint8)
    result = weighted_rgb2gray(img)
    assert result.shape == (10, 10)
    assert result.max() == 255 and result.min() == 255


def test_pure_black():
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    result = weighted_rgb2gray(img)
    assert result.min() == 0 and result.max() == 0


def test_pure_red():
    img = np.zeros((1, 1, 3), dtype=np.uint8)
    img[0, 0] = [255, 0, 0]
    result = weighted_rgb2gray(img)
    assert abs(int(result[0, 0]) - 76) <= 2


def test_output_dtype():
    img = np.random.randint(0, 255, (20, 20, 3), dtype=np.uint8)
    assert weighted_rgb2gray(img).dtype == np.uint8


def test_output_shape():
    img = np.random.randint(0, 255, (15, 30, 3), dtype=np.uint8)
    result = weighted_rgb2gray(img)
    assert result.ndim == 2 and result.shape == (15, 30)


if __name__ == "__main__":
    test_pure_white(); test_pure_black(); test_pure_red()
    test_output_dtype(); test_output_shape()
    print("✅ 灰度化算法测试全部通过")
