import uuid
from queue import Queue,Empty
import threading
from typing import Callable
from paddleocr import PaddleOCR
from image_utils import preprocess

class Task:
    def __init__(self,task_id,img_path,callback:Callable):
        self.task_id = task_id
        self.img_path = img_path
        self.callback = callback

class  OcrEngine:
    def __init__(self):
        self.ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            engine="paddle",
        )

        self.task_queue=Queue()
        self.is_running=True
        self.worker_thread=threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()
    

    def submit(self,img_path,callback:Callable)->str:
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id, img_path, callback)
        self.task_queue.put(task)
        return task_id
    


    def submit_batch(self,img_paths:list,callback:Callable)->list:
        task_ids=[]
        for img_path in img_paths:
            task_id=self.submit(img_path,callback)
            task_ids.append(task_id)
        return task_ids
    

    def worker_loop(self):
        while self.is_running:
            try:
                task=self.task_queue.get(block=True,timeout=1)
            except Empty:
                continue
            else:
                preprocessed_img=preprocess(task.img_path) #预处理
                result=self.ocr.predict(preprocessed_img)
                text=[]
                for res in result:
                    text.extend(' '.join(res.json['res']['rec_texts']))
                full_text=' '.join(text)
                task.callback(task.task_id,full_text,True)
    

    def shutdown(self):
        self.is_running=False

    
