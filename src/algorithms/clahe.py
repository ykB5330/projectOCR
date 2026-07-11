import numpy as np

# skimage为可选依赖——未安装时CLAHE步骤自动跳过
try:
    from skimage.exposure import equalize_adapthist
    _HAS_SKIMAGE = True
except ImportError:
    _HAS_SKIMAGE = False


def clahe_enhance(image, clip_limit=0.03, tile_size=8):
    """
    限制对比度自适应直方图均衡化（CLAHE）增强

    Args:
        image: 输入灰度图像（uint8，0-255）
        clip_limit: 对比度限制阈值（默认0.03）
        tile_size: 分块大小（默认8），控制局部增强粒度

    Returns:
        uint8增强后的图像
    """
    if not _HAS_SKIMAGE:
        # skimage未安装时跳过CLAHE，直接返回原图
        return image

    img_norm = image.astype(float) / 255.0
    enhanced = equalize_adapthist(
        img_norm, clip_limit=clip_limit, nbins=256,
        kernel_size=tile_size
    )
    return (enhanced * 255).astype(np.uint8)
