import numpy as np
def gamma_correction(image, gamma):
    normalized = image.astype(float) / 255.0
    
    corrected = np.power(normalized,1.0/gamma)
    
    return np.clip(corrected * 255.0, 0, 255).astype(np.uint8)


