"""图像金字塔缩放算法测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from algorithms.resize import down_sample_2x, up_sample_2x


def test_down_sample_size():
    img = np.random.randint(0, 255, (40, 60), dtype=np.uint8)
    result = down_sample_2x(img)
    assert result.shape == (20, 30)


def test_down_sample_avg():
    img = np.array([[10, 20, 30, 40], [30, 40, 50, 60],
                    [50, 60, 70, 80], [70, 80, 90, 100]], dtype=np.uint8)
    result = down_sample_2x(img)
    assert result.shape == (2, 2)
    assert abs(int(result[0, 0]) - 25) <= 1


def test_up_sample_size():
    img = np.random.randint(0, 255, (10, 15), dtype=np.uint8)
    result = up_sample_2x(img)
    assert result.shape == (20, 30)


def test_down_then_up():
    img = np.random.randint(0, 255, (32, 32), dtype=np.uint8)
    down = down_sample_2x(img)
    up = up_sample_2x(down)
    assert up.shape == img.shape


def test_output_dtype():
    img = np.random.randint(0, 255, (20, 20), dtype=np.uint8)
    assert down_sample_2x(img).dtype == np.uint8
    assert up_sample_2x(img).dtype == np.uint8


if __name__ == "__main__":
    test_down_sample_size(); test_down_sample_avg()
    test_up_sample_size(); test_down_then_up(); test_output_dtype()
    print("✅ 金字塔缩放算法测试全部通过")
