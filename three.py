def bubble_sort(pixel_list):
    n = len(pixel_list)
    for i in range(n):
        for j in range(n - i - 1):
            if pixel_list[j] > pixel_list[j + 1]:
                pixel_list[j], pixel_list[j + 1] = pixel_list[j + 1], pixel_list[j]
    return pixel_list

def manual_median_filter(gray_matrix, kernel_size=3):
    height = len(gray_matrix)
    width = len(gray_matrix[0])
    half_k = kernel_size // 2
    output = [[0 for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            window = []
            for dy in range(-half_k, half_k + 1):
                for dx in range(-half_k, half_k + 1):
                    curr_y = y + dy
                    curr_x = x + dx
                    if curr_y < 0:
                        curr_y = 0
                    elif curr_y >= height:
                        curr_y = height - 1
                    if curr_x < 0:
                        curr_x = 0
                    elif curr_x >= width:
                        curr_x = width - 1
                    window.append(gray_matrix[curr_y][curr_x])
            sorted_win = bubble_sort(window)
            median_val = sorted_win[len(sorted_win) // 2]
            output[y][x] = median_val
    return output
__all__ = ["manual_median_filter", "bubble_sort"]