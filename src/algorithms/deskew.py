import numpy as np
from PIL import Image

def hough_transform(binary_image):
    h, w = binary_image.shape
    diag_len = int(np.ceil(np.sqrt(h**2 + w**2)))
    thetas = np.deg2rad(np.arange(0, 180))
    num_thetas = len(thetas)
    rhos = np.arange(-diag_len, diag_len + 1)
    num_rhos = len(rhos)
    accumulator = np.zeros((num_rhos, num_thetas), dtype=np.int64)

    y_idxs, x_idxs = np.nonzero(binary_image)
    if len(x_idxs) == 0:
        return accumulator, thetas, rhos

    cos_vals = np.cos(thetas)
    sin_vals = np.sin(thetas)
    for t_idx in range(num_thetas):
        rho_vals = (x_idxs * cos_vals[t_idx] + y_idxs * sin_vals[t_idx])
        rho_int = np.round(rho_vals).astype(np.int32) + diag_len
        rho_int = np.clip(rho_int, 0, num_rhos - 1)
        counts = np.bincount(rho_int, minlength=num_rhos)
        accumulator[:, t_idx] = counts

    return accumulator, thetas, rhos


def get_skew_angle(accumulator, thetas, rhos, diag_len):
    if np.max(accumulator) == 0:
        return 0.0

    col_max = np.max(accumulator, axis=0) 
    theta_deg = np.rad2deg(thetas) 


    sigma = 15.0
    weights = np.exp(-((theta_deg - 90) ** 2) / (2 * sigma ** 2))
    weighted_votes = col_max * weights


    best_idx = np.argmax(weighted_votes)
    best_theta = theta_deg[best_idx]
    best_vote = col_max[best_idx]

    if abs(best_theta - 90) > 30:
        if best_vote < 0.6 * np.max(col_max):
            return 0.0

    rotation_angle = 90.0 - best_theta
    if abs(rotation_angle) > 45.0:
        return 0.0

    return rotation_angle


def rotate_image(image_pil, angle):
    return image_pil.rotate(angle, expand=True, resample=Image.BICUBIC)
