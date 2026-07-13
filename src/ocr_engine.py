import os
import uuid
from queue import Queue, Empty
import threading
from typing import Callable
import numpy as np
from PIL import Image
from image_utils import preprocess


class Task:
    def __init__(self, task_id, img_input, callback: Callable, enabled_steps=None):
        self.task_id = task_id
        self.img_input = img_input          # 文件路径(str) 或 PIL.Image 对象
        self.callback = callback
        self.enabled_steps = enabled_steps  # set of str, 启用的预处理步骤


class OcrEngine:
    """OCR识别引擎，基于队列的任务调度与异步识别"""

    def __init__(self):
        self._ocr = None           # 延迟到 worker 线程内首次创建
        self._ocr_lock = threading.Lock()

        self.task_queue = Queue()
        self.is_running = True
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()

    def _get_ocr(self):
        """获取 PaddleOCR 实例（在调用线程内延迟创建，避免跨线程 oneDNN 崩溃）"""
        if self._ocr is None:
            with self._ocr_lock:
                if self._ocr is None:
                    from paddleocr import PaddleOCR
                    print("[OCR引擎] 正在初始化PaddleOCR模型...")
                    self._ocr = PaddleOCR(
                        use_doc_orientation_classify=True,
                        use_doc_unwarping=False,
                        use_textline_orientation=False,
                        engine="paddle",
                    )
                    print("[OCR引擎] 模型加载完成 ✓")
        return self._ocr

    def submit(self, img_input, callback: Callable, enabled_steps=None) -> str:
        """
        提交单个识别任务

        Args:
            img_input: 文件路径(str) 或 PIL.Image 对象
            callback: 回调函数 callback(task_id, text, success)
            enabled_steps: set，启用的预处理步骤名（None=全部，空set=跳过）

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id, img_input, callback, enabled_steps)
        self.task_queue.put(task)
        print(f"[OCR引擎] 任务 {task_id} 已加入队列 (预处理: {enabled_steps})")
        return task_id

    def submit_image(self, pil_image: Image.Image, callback: Callable,
                     enabled_steps=None) -> str:
        """提交PIL图像对象进行识别（用于区域选择后的局部识别）"""
        return self.submit(pil_image, callback, enabled_steps)

    def submit_batch(self, img_inputs: list, callback: Callable) -> list:
        """
        提交批量识别任务，所有任务完成后汇总回调

        Args:
            img_inputs: 文件路径列表 或 PIL.Image 列表
            callback: 回调函数 callback(batch_id, combined_text, success)
                     收到汇总后的全部识别结果

        Returns:
            task_ids: 所有子任务ID列表
        """
        batch_id = str(uuid.uuid4())[:8]
        results = {}
        total = len(img_inputs)
        lock = threading.Lock()

        def batch_callback(task_id, text, success):
            with lock:
                results[task_id] = (text, success)
                if len(results) == total:
                    # 所有子任务完成，汇总文本
                    combined_parts = []
                    for i, img_input in enumerate(img_inputs):
                        tid = task_ids[i]
                        if tid in results and results[tid][1]:
                            combined_parts.append(results[tid][0])
                    combined_text = "\n---\n".join(combined_parts) if combined_parts else "(识别失败)"
                    callback(batch_id, combined_text, True)

        task_ids = []
        for img_input in img_inputs:
            task_id = self.submit(img_input, batch_callback)
            task_ids.append(task_id)
        return task_ids

    def worker_loop(self):
        """后台工作线程：从队列取出任务，执行预处理+OCR识别"""
        while self.is_running:
            try:
                task = self.task_queue.get(block=True, timeout=1)
            except Empty:
                continue

            print(f"[OCR引擎] 开始处理任务 {task.task_id}")
            try:
                # 空步骤 → 跳过预处理，传文件路径给 PaddleOCR（避免 numpy→oneDNN 崩溃）
                steps_empty = (task.enabled_steps is not None and len(task.enabled_steps) == 0)
                _tmp_file = None
                if steps_empty:
                    if isinstance(task.img_input, str):
                        ocr_input = task.img_input
                    else:
                        import tempfile
                        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        task.img_input.save(tmp.name)
                        tmp.close()
                        ocr_input = tmp.name
                        _tmp_file = tmp.name
                    print(f"[OCR引擎] 任务 {task.task_id} 跳过预处理，直接传路径...")
                else:
                    ocr_input = preprocess(task.img_input, task.enabled_steps)
                    print(f"[OCR引擎] 任务 {task.task_id} 预处理完成 (尺寸: {ocr_input.shape[:2]})，开始OCR...")
                result = self._get_ocr().predict(ocr_input)

                # 正确提取rec_texts
                text_parts = []
                for res in result:
                    rec_texts = res.json['res']['rec_texts']
                    text_parts.extend(rec_texts)
                full_text = ' '.join(text_parts)
                print(f"[OCR引擎] 任务 {task.task_id} 识别完成: {full_text[:50]}...")
                if _tmp_file:
                    os.unlink(_tmp_file)
                task.callback(task.task_id, full_text, True)
            except RuntimeError as e:
                # PaddlePaddle C++ RuntimeError
                # 如果启用了预处理，可能是预处理导致的 → 重试原图
                # 如果没启用预处理，重试无意义 → 直接报错
                steps_empty = (task.enabled_steps is not None and len(task.enabled_steps) == 0)
                if steps_empty:
                    print(f"[OCR引擎] 任务 {task.task_id} RuntimeError（未启用预处理，无法降级）")
                    msg = (f"PaddleOCR推理引擎错误。\n"
                           f"建议：勾选任意预处理步骤后重试（改变图片格式可能绕过此问题）")
                    if _tmp_file:
                        os.unlink(_tmp_file)
                    task.callback(task.task_id, msg, False)
                else:
                    print(f"[OCR引擎] 任务 {task.task_id} RuntimeError，跳过预处理重试原图...")
                    try:
                        if isinstance(task.img_input, str):
                            raw_img = np.array(Image.open(task.img_input).convert('RGB'))
                        else:
                            raw_img = np.array(task.img_input.convert('RGB'))
                        result = self._get_ocr().predict(raw_img)
                        text_parts = []
                        for res in result:
                            text_parts.extend(res.json['res']['rec_texts'])
                        full_text = ' '.join(text_parts)
                        if _tmp_file:
                            os.unlink(_tmp_file)
                        task.callback(task.task_id, full_text, True)
                    except Exception as e2:
                        if _tmp_file:
                            os.unlink(_tmp_file)
                        task.callback(task.task_id, f"识别错误(RuntimeError): {str(e)}", False)
            except Exception as e:
                import traceback
                print(f"[OCR引擎] 任务 {task.task_id} 失败: {e}")
                traceback.print_exc()
                if _tmp_file:
                    os.unlink(_tmp_file)
                task.callback(task.task_id, f"识别错误: {str(e)}", False)

    def visualize(self, img_input, output_prefix):
        """生成 OCR 可视化对比图（在原图上标注检测框和识别文本）"""
        if isinstance(img_input, str):
            result = self._get_ocr().predict(img_input)
        else:
            result = self._get_ocr().predict(np.array(img_input))
        paths = []
        for res in result:
            paths.append(res.save_to_img(output_prefix))
        return paths

    def shutdown(self):
        """关闭引擎，停止工作线程"""
        print("[OCR引擎] 正在关闭...")
        self.is_running = False

    
