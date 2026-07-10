from skimage.exposure import equalize_adapthist 
from skimage.exposure import exposure
import numpy as np
def clahe_enhance(image, clip_limit=0.03):

    img_norm = image.astype(float) / 255.0

    enhanced = exposure.equalize_adapthist(img_norm, clip_limit=clip_limit, nbins=256, kernel_size=tile_size)
    return (enhanced * 255).astype(np.uint8)

