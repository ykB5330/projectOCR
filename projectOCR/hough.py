def hough_transform(image):
    import numpy as np
    height, width = image.shape
    diag_len = int(np.ceil(np.sqrt(height**2 + width**2)))
    rhos = np.linspace(-diag_len, diag_len, diag_len * 2)
    thetas = np.deg2rad(np.arange(-90, 90))
    accumulator = np.zeros((len(rhos), len(thetas)), dtype=np.int)
    y_idxs, x_idxs = np.nonzero(image)
    for i in range(len(x_idxs)):
        x = x_idxs[i]
        y = y_idxs[i]
        for t_idx in range(len(thetas)):
            theta = thetas[t_idx]
            rho = int(round(x * np.cos(theta) + y * np.sin(theta))) + diag_len
            accumulator[rho, t_idx] += 1
    return accumulator, thetas, rhos




