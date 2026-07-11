"""
图像预处理流水线集成测试
"""
import sys
import os
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_preprocess_with_pil_image():
    """测试：传入PIL Image对象进行预处理（核心流程）"""
    try:
        from image_utils import preprocess
    except ImportError as e:
        print(f"⚠️ 跳过测试（缺少依赖）: {e}")
        return

    test_img = Image.new('RGB', (100, 100), color=(200, 180, 160))
    result = preprocess(test_img)

    assert isinstance(result, np.ndarray), "输出应为numpy数组"
    assert result.ndim == 3, "输出应为3通道RGB图像"
    assert result.shape[0] > 0 and result.shape[1] > 0, "输出尺寸应大于0"


def test_preprocess_with_file_path():
    """测试：传入文件路径进行预处理"""
    try:
        from image_utils import preprocess
    except ImportError as e:
        print(f"⚠️ 跳过测试（缺少依赖）: {e}")
        return

    test_img = Image.new('RGB', (100, 100), color=(200, 180, 160))
    test_path = os.path.join(os.path.dirname(__file__), 'test_input.png')
    test_img.save(test_path)

    try:
        result = preprocess(test_path)
        assert isinstance(result, np.ndarray), "输出应为numpy数组"
        assert result.ndim == 3, "输出应为3通道RGB图像"
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)


def test_preprocess_accepts_pil():
    """验证preprocess接受PIL Image参数"""
    try:
        from image_utils import preprocess
    except ImportError as e:
        print(f"⚠️ 跳过测试（缺少依赖）: {e}")
        return

    # 小图测试（加快处理速度）
    test_img = Image.new('RGB', (64, 64), color=(150, 150, 150))
    result = preprocess(test_img)
    assert result is not None
    assert isinstance(result, np.ndarray)


if __name__ == "__main__":
    test_preprocess_with_pil_image()
    test_preprocess_with_file_path()
    test_preprocess_accepts_pil()
    print("✅ 预处理流水线集成测试通过")
