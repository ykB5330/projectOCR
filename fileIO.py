
# file.py
from queue import Queue

# 创建线程安全队列，用来存放识别结果，UI从这里取数据
result_queue = Queue(maxsize=10)

# 供test.py调用：把识别后的文本送入队列
def send_recognize_text(ocr_text: str):
    """
    test调用这个方法，把AI识别得到的字符串传给file模块
    :param ocr_text: AI识别出来的文本字符串
    """
    global result_queue
    # 将识别文本放入队列
    result_queue.put(ocr_text)

# 供UI调用：UI读取识别结果
def get_ocr_text():
    """UI端调用，获取识别结果，队列无数据返回None"""
    if not result_queue.empty():
        return result_queue.get()
    return None
