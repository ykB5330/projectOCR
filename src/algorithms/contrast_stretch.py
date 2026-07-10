import numpy as np
def contrast_stretch(image,low_percent=2,high_percent=98):
    low_val=np.percentile(image, low_percent)
    high_val=np.percentile(image, high_percent)
    if high_val - low_val < 1:
      return image
    stretched= (image - low_val) * 255.0 / (high_val - low_val)
    return np.clip(stretched, 0, 255).astype(np.uint8)




