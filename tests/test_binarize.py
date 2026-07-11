"""自适应二值化算法测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from algorithms.binarize import manual_adaptive_binarize


def test_binary_output():
    gray = np.random.randint(0, 255, (30, 30), dtype=np.uint8)
    result = manual_adaptive_binarize(gray, window_size=15)
    assert set(np.unique(result)).issubset({0, 255})


def test_all_white():
    gray = np.full((20, 20), 255, dtype=np.uint8)
    result = manual_adaptive_binarize(gray, window_size=9)
    assert np.all(result == 255)


def test_uniform_image():
    """均匀图像 → 阈值=均值-C，全图输出一致（0或255）"""
    gray = np.full((20, 20), 128, dtype=np.uint8)
    result = manual_adaptive_binarize(gray, window_size=9)
    # 局部均值≈128，阈值≈123。128>123 → 全白
    assert len(np.unique(result)) == 1


def test_output_shape():
    gray = np.random.randint(0, 255, (25, 35), dtype=np.uint8)
    result = manual_adaptive_binarize(gray, window_size=15)
    assert result.shape == gray.shape


def test_small_window():
    gray = np.random.randint(0, 255, (20, 20), dtype=np.uint8)
    result = manual_adaptive_binarize(gray, window_size=3)
    assert result.shape == gray.shape


if __name__ == "__main__":
    test_binary_output(); test_all_white(); test_uniform_image()
    test_output_shape(); test_small_window()
    print("✅ 自适应二值化算法测试全部通过")
