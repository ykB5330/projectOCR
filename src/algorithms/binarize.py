import numpy as np

def manual_adaptive_binarize(gray_img, window_size=25, C=5):
    """
    自适应二值化（积分图优化版本）
    接口完全不变，内部使用积分图加速
    """
    height, width = gray_img.shape
    half_win = window_size // 2
    
    # 1. 构建积分图
    integral = np.zeros((height + 1, width + 1), dtype=np.uint64)
    integral[1:, 1:] = np.cumsum(np.cumsum(gray_img, axis=0), axis=1)
    
    # 2. 生成所有像素的坐标网格
    y = np.arange(height)[:, None] 
    x = np.arange(width)[None, :] 
    
    # 3. 计算每个像素对应的窗口边界
    top    = np.maximum(0, y - half_win)
    bottom = np.minimum(height, y + half_win + 1)
    left   = np.maximum(0, x - half_win)
    right  = np.minimum(width, x + half_win + 1)
    
    # 4. 使用积分图快速计算窗口和
    sum_window = (integral[bottom, right] - integral[top, right]
                  - integral[bottom, left] + integral[top, left])
    
    # 5. 计算窗口面积和均值
    area = (bottom - top) * (right - left) 
    mean = sum_window / area.astype(np.float64)
    
    # 6. 计算阈值并生成二值图像
    threshold = mean - C
    binary = (gray_img >= threshold).astype(np.uint8) * 255
    
    return binary