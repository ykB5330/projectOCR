"""
UI界面模块 - Tkinter版本
"""
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES
import customtkinter as ctk


class OcrUI:
    """OCR识别工具主窗口"""
    
    def __init__(self):
        """初始化窗口 - 原全局代码全部移到这里"""
        
        # ===== 原全局设置 =====
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # ===== 创建主窗口（原 mwindow → self.root） =====
        self.root = TkinterDnD.Tk()
        self.root.title("文字识别工具")
        
        # ===== 原全局变量 =====
        self.file_list = []
        self.current_photo = None
        self.label1 = None
        self.label2 = None
        self.label3 = None
        self.icon_img_tk = None
        self.engine = None  # 稍后注入
        
        # ===== 搭建界面 =====
        self._setup_ui()
    
    def set_engine(self, engine):
        """注入引擎（由 main.py 调用）"""
        self.engine = engine
    
    def _setup_ui(self):
        """搭建界面 - 原代码一字不改，只把 mwindow 改成 self.root"""
        
        # ===== 主界面基本设置（原 mwindow → self.root） =====
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=0, minsize=20)
        self.root.columnconfigure(2, weight=1)
        self.root.columnconfigure(3, weight=1)
        self.root.columnconfigure(4, weight=0)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=0, minsize=10)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=0)
        self.root.rowconfigure(4, weight=0)
        
        ctk.CTkLabel(
            self.root,
            text="图片识别",
            font=("微软雅黑", 20),
            text_color="black",
            fg_color="#F7FEFE"
        ).grid(row=0, column=0, sticky="nw", padx=(10, 0), pady=(10, 0))
        
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        self.root.iconbitmap(r"src\asserts\favicon.ico")  # 如果没有图标文件，注释掉
        self.root.configure(bg="#F7FEFE")
        self.root.attributes("-alpha", 1)
        self.root.attributes("-topmost", False)
        
        # ===== frame_in =====
        self.frame_in = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_in.grid(row=1, column=2, sticky="nsew", padx=(10, 0), pady=(10, 0))
        self.frame_in.columnconfigure(0, weight=1)
        self.frame_in.rowconfigure(1, weight=1)
        
        # ===== frame_out =====
        self.frame_out = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_out.grid(row=1, column=3, sticky="nsew", padx=(10, 0), pady=(10, 0))
        self.frame_out.columnconfigure(0, weight=1)
        self.frame_out.rowconfigure(1, weight=1)
        
        # ===== 清除按钮 =====
        self.clear_bt = ctk.CTkButton(
            self.frame_in,
            text="清除",
            width=60,
            height=30,
            font=("微软雅黑", 15),
            text_color="black",
            fg_color="#5EDEDE",
            command=self._clear_canvas
        )
        self.clear_bt.grid(row=0, column=0, sticky="ne", padx=5, pady=5)
        
        # ===== canvas_in =====
        self.canvas_in = ctk.CTkCanvas(self.frame_in, width=550, height=650, bg="#C1EBEB")
        self.canvas_in.grid(row=1, column=0, sticky="nsew")
        
        # ===== 开始识别按钮 =====
        self.recognize_bt = ctk.CTkButton(
            self.root,
            text="开始识别",
            command=self._start_recognize,
            width=15,
            font=("微软雅黑", 20),
            text_color="black",
            fg_color="#91A5E0"
        )
        self.recognize_bt.grid(row=2, column=3, sticky="w", padx=(10, 0), pady=(10, 0))
        
        # ===== 复制按钮 =====
        self.copy_btn = ctk.CTkButton(
            self.frame_out,
            text="复制",
            width=60,
            height=30,
            font=("微软雅黑", 15),
            text_color="black",
            fg_color="#5EDEDE",
            command=self._copy_canvas_text
        )
        self.copy_btn.grid(row=0, column=0, sticky="ne", padx=5, pady=5)
        
        # ===== canvas_out =====
        self.canvas_out = ctk.CTkCanvas(self.frame_out, width=550, height=650, bg="#F7FEFE")
        self.canvas_out.grid(row=1, column=0, sticky="nsew")
        
        # ===== 导入图片区域 =====
        self._creat_area()
        
        # ===== 导入图片按钮 =====
        self.button = ctk.CTkButton(
            self.root,
            text="导入图片",
            command=self._Import_file,
            width=15,
            font=("微软雅黑", 20),
            text_color="black",
            fg_color="#91A5E0"
        )
        self.button.grid(row=2, column=2, sticky="w", padx=(10, 0), pady=(10, 0))
        
        # ===== 状态标签 =====
        self.label = ctk.CTkLabel(
            self.root,
            text="未选择图片文件",
            width=15,
            font=("微软雅黑", 15),
            text_color="black",
            fg_color="#F7FEFE"
        )
        self.label.grid(row=0, column=3)
        
        # ===== 左侧目录 =====
        self.left_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        self.left_frame.rowconfigure(0, weight=1)
        self.left_frame.columnconfigure(0, weight=1)
        
        self.listbox = tk.Listbox(
            self.left_frame,
            bg="#F7FEFE",
            fg="black",
            font=("微软雅黑", 12)
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox.bind('<<ListboxSelect>>', self._on_select_listbox)
        
        # ===== 关闭协议 =====
        self.root.protocol("WM_DELETE_WINDOW", self._close)
    
    # ===== 原 clear_canvas =====
    def _clear_canvas(self):
        """清除按钮"""
        self.canvas_in.delete("all")
        icon = Image.open(r"src\asserts\drop_hint.png").resize((80, 80), Image.Resampling.LANCZOS).convert("RGBA")
        bg = Image.new("RGBA", icon.size, (193, 235, 235, 255))
        self.icon_img_tk = ImageTk.PhotoImage(Image.alpha_composite(bg, icon))
        self.canvas_in.create_image(
            self.canvas_in.winfo_width()/2,
            160,
            image=self.icon_img_tk,
            anchor="center",
            tags="icon"
        )
        self.canvas_in.image = self.icon_img_tk
        if self.label1:
            self.label1.place(relx=0.5, rely=0.55, anchor="center")
        if self.label2:
            self.label2.place(relx=0.5, rely=0.66, anchor="center")
        if self.label3:
            self.label3.place(relx=0.5, rely=0.77, anchor="center")
        self._drag_leave(None)
        self.label.configure(text="未选择图片文件")
    
    # ===== 原 drag_into =====
    def _drag_into(self, event):
        self.canvas_in.configure(bg="#9AEF84")
    
    # ===== 原 drag_leave =====
    def _drag_leave(self, event):
        self.canvas_in.configure(bg="#C1EBEB")
    
    # ===== 原 drop =====
    def _drop(self, event):
        files = self.root.tk.splitlist(event.data)
        files_path = files[0]
        files_name = os.path.basename(files_path)
        files_extension = os.path.splitext(files_name)[1]
        if files_extension.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
            print("拖入的文件路径:", files_path)
            img = Image.open(files_path)
            img = img.resize((550, 450), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.canvas_in.delete("all")
            self.canvas_in.create_image(
                self.canvas_in.winfo_width()/2,
                self.canvas_in.winfo_height()/2,
                anchor="center",
                image=photo
            )
            self.canvas_in.image = photo
            self.label.configure(text=f"已选择文件: {files_path}")
            if self.label1:
                self.label1.place_forget()
            if self.label2:
                self.label2.place_forget()
            if self.label3:
                self.label3.place_forget()
            self._add_file_to_list(files_path)
    
    # ===== 原 creat_area =====
    def _creat_area(self):
        icon = Image.open(r"src\asserts\drop_hint.png").resize((80, 80), Image.Resampling.LANCZOS).convert("RGBA")
        bg = Image.new("RGBA", icon.size, (193, 235, 235, 255))
        self.icon_img_tk = ImageTk.PhotoImage(Image.alpha_composite(bg, icon))
        self.canvas_in.create_image(275, 160, image=self.icon_img_tk, anchor="center", tags="icon")
        self.canvas_in.image = self.icon_img_tk
        
        def keep_on_vertical_center(event):
            self.canvas_in.coords("icon", event.width / 2, 160)
        self.canvas_in.bind("<Configure>", keep_on_vertical_center)
        
        self.label1 = ctk.CTkLabel(
            self.canvas_in,
            text="拖入图片文件",
            font=("微软雅黑", 20),
            text_color="black",
            fg_color="transparent"
        )
        self.label1.place(relx=0.5, rely=0.55, anchor="center")
        
        self.label2 = ctk.CTkLabel(
            self.canvas_in,
            text="支持格式：jpg、jpeg、png、bmp、gif",
            font=("微软雅黑", 15),
            text_color="black",
            fg_color="transparent"
        )
        self.label2.place(relx=0.5, rely=0.66, anchor="center")
        
        self.label3 = ctk.CTkLabel(
            self.canvas_in,
            text="或点击“导入图片”按钮选择文件",
            font=("微软雅黑", 15),
            text_color="black",
            fg_color="transparent"
        )
        self.label3.place(relx=0.5, rely=0.77, anchor="center")
        
        self.canvas_in.drop_target_register(DND_FILES)
        self.canvas_in.dnd_bind('<<DropEnter>>', self._drag_into)
        self.canvas_in.dnd_bind('<<DropLeave>>', self._drag_leave)
        self.canvas_in.dnd_bind('<<Drop>>', self._drop)
    
    # ===== 原 Import_file =====
    def _Import_file(self):
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("自定义文件", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")]
        )
        if file_path:
            print("选择的文件路径:", file_path)
            img = Image.open(file_path)
            img = img.resize((550, 450), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.canvas_in.delete("all")
            self.canvas_in.create_image(
                self.canvas_in.winfo_width()/2,
                self.canvas_in.winfo_height()/2,
                anchor="center",
                image=photo
            )
            self.canvas_in.image = photo
            if self.label1:
                self.label1.place_forget()
            if self.label2:
                self.label2.place_forget()
            if self.label3:
                self.label3.place_forget()
            self.label.configure(text=f"已选择文件: {file_path}")
            self._add_file_to_list(file_path)
        else:
            print("未选择文件")
    
    # ===== 原 add_file_to_list =====
    def _add_file_to_list(self, path):
        if path not in self.file_list:
            self.file_list.append(path)
            self.listbox.insert(tk.END, os.path.basename(path))
    
    # ===== 原 on_select_listbox =====
    def _on_select_listbox(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        path = self.file_list[sel[0]]
        img = Image.open(path).resize((550, 450), Image.Resampling.LANCZOS)
        self.current_photo = ImageTk.PhotoImage(img)
        self.canvas_in.delete("all")
        self.canvas_in.create_image(
            self.canvas_in.winfo_width()/2,
            self.canvas_in.winfo_height()/2,
            anchor="center",
            image=self.current_photo
        )
        self.canvas_in.image = self.current_photo
        self.label.configure(text=f"已选择文件: {path}")
        for lbl in (self.label1, self.label2, self.label3):
            if lbl:
                lbl.place_forget()
        self.canvas_out.delete("all")
        self.canvas_out.create_text(
            self.canvas_out.winfo_width()/2,
            20,
            anchor="n",
            text="（等待识别）",
            fill="gray",
            font=("微软雅黑", 12)
        )
    
    # ===== 原 display_ocr_result =====
    def _display_ocr_result(self, text):
        self.canvas_out.delete("all")
        y = 20
        for line in text.split('\n'):
            self.canvas_out.create_text(
                10, y,
                anchor="nw",
                text=line,
                fill="black",
                font=("微软雅黑", 14),
                tags="result"
            )
            y += 25
    
    # ===== 原 start_recognize =====
    def _start_recognize(self):
        if not self.file_list:
            messagebox.showwarning("提示", "请先导入图片")
            return
        
        # 如果有引擎，调用引擎
        if self.engine:
            self.recognize_bt.configure(state="disabled")
            self.label.configure(text="识别中...")
            self.canvas_out.delete("all")
            self.canvas_out.create_text(
                self.canvas_out.winfo_width()/2,
                20,
                text="⏳ 识别中，请稍候...",
                font=("微软雅黑", 14),
                fill="gray"
            )
            # 调用引擎
            self.engine.submit_batch(self.file_list, self._on_result)
        else:
            # 没有引擎时，显示示例文字
            text = "这是为引号内内容（识别文字）准备的示例输出\n可在此处显示 OCR 结果"
            self._display_ocr_result(text)
    
    def _on_result(self, task_id, text, success):
        """识别完成回调"""
        self.root.after(0, lambda: self._display_ocr_result(text))
        self.root.after(0, lambda: self.recognize_bt.configure(state="normal"))
        self.root.after(0, lambda: self.label.configure(text="✅ 识别完成"))
    
    # ===== 原 copy_canvas_text =====
    def _copy_canvas_text(self):
        texts = []
        for item in self.canvas_out.find_all():
            if self.canvas_out.type(item) == "text":
                texts.append(self.canvas_out.itemcget(item, "text"))
        content = "\n".join(texts)
        if content.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("提示", "文字已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "暂无文字可复制")
    
    # ===== 原 close =====
    def _close(self):
        jud = messagebox.askokcancel("退出", "是否退出程序")
        if jud:
            if self.engine:
                self.engine.shutdown()
            self.root.destroy()
    
    # ===== 启动 =====
    def run(self):
        """启动主循环"""
        self.root.mainloop()