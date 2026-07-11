"""中值滤波算法测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from algorithms.filter import manual_median_filter


def test_flat_image():
    gray = [[100 for _ in range(10)] for _ in range(10)]
    result = manual_median_filter(gray, kernel_size=3)
    for row in result:
        assert all(v == 100 for v in row)


def test_salt_pepper():
    gray = [[100 for _ in range(5)] for _ in range(5)]
    gray[2][2] = 255
    result = manual_median_filter(gray, kernel_size=3)
    assert result[2][2] == 100


def test_output_shape():
    gray = [[i + j for j in range(15)] for i in range(10)]
    result = manual_median_filter(gray, kernel_size=5)
    assert len(result) == 10 and len(result[0]) == 15


def test_edge_clamp():
    gray = [[50 for _ in range(5)] for _ in range(5)]
    result = manual_median_filter(gray, kernel_size=3)
    assert result[0][0] == 50


if __name__ == "__main__":
    test_flat_image(); test_salt_pepper()
    test_output_shape(); test_edge_clamp()
    print("✅ 中值滤波算法测试全部通过")
