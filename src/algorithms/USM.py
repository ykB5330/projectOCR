from PIL import Image, ImageFilter
import numpy as np

def usm_sharpen(image, radius=1.0, amount=1.0, threshold=0):


    img_pil = Image.fromarray(image)

    blurred_pil = img_pil.filter(ImageFilter.GaussianBlur(radius=radius))
    blurred = np.array(blurred_pil, dtype=np.float32)

    original = image.astype(np.float32)

    detail = original - blurred


    if threshold > 0:
        mask = np.abs(detail) < threshold
        detail[mask] = 0

    sharpened = original + amount * detail

    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    return sharpened