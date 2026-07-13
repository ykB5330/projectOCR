"""
UI界面模块 - Tkinter版本
OCR文字识别工具主窗口
"""
import os
import time
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from tkinterdnd2 import TkinterDnD, DND_FILES
import customtkinter as ctk

from region_selector import RegionSelector
from history_manager import HistoryManager
from result_parser import ResultParser


class OcrUI:
    """OCR识别工具主窗口"""

    def __init__(self):
        """初始化窗口"""
        # ===== 主题设置 =====
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ===== 创建主窗口 =====
        self.root = TkinterDnD.Tk()
        self.root.title("文字识别工具")

        # ===== 文件与显示变量 =====
        self.file_list = []           # 文件路径列表
        self.current_photo = None     # 当前显示的PhotoImage引用
        self.icon_img_tk = None       # 拖拽提示图标引用
        self.engine = None            # OCR引擎（由main.py注入）

        # ===== 区域选择相关 =====
        self.region_selector = None
        self.selection_active = False
        self.current_region = None          # (x1, y1, x2, y2) 图像坐标
        self.original_image_path = None
        self.original_pil_image = None

        # ===== 预处理选项 =====
        # None=全部启用, set()=全不启用, {'grayscale','deskew'}=部分启用
        self.enabled_steps = None

        # ===== 队列状态 =====
        self._queue_drained = True   # 当前无待识别图片
        self._last_results = {}      # {image_path: ocr_text} 导出用

        # ===== 历史记录 =====
        self.history_manager = HistoryManager()
        self._history_id_map = {}           # listbox索引 → ocr_text
        self._history_dir = os.path.join(os.path.dirname(__file__), '..', 'history')
        self._load_history()                # 启动时加载持久化记录

        # ===== 搭建界面 =====
        self._setup_ui()

    def set_engine(self, engine):
        """注入OCR引擎（由main.py调用）"""
        self.engine = engine

    # ==================================================================
    # 界面搭建
    # ==================================================================

    def _setup_ui(self):
        """搭建全部UI组件"""
        self._assets_dir = os.path.join(os.path.dirname(__file__), 'assets')

        # ----- 窗口基础设置 -----
        self.root.configure(bg="#F7FEFE")
        self.root.resizable(True, True)
        self._center_window(1200, 850)

        # ----- 网格布局配置 -----
        # 列：0=文件列表 | 1=间隔 | 2=输入画布 | 3=输出画布 | 4=间隔
        self.root.columnconfigure(0, weight=0)           # 文件列表（固定宽）
        self.root.columnconfigure(1, weight=0, minsize=10)  # 间隔
        self.root.columnconfigure(2, weight=1)           # 输入画布（可扩展）
        self.root.columnconfigure(3, weight=1)           # 输出画布（可扩展）
        self.root.columnconfigure(4, weight=0)           # 间隔

        # 行：固定顺序，只有canvas行可扩展
        self.root.rowconfigure(0, weight=0)   # 标题行
        self.root.rowconfigure(1, weight=1)   # Canvas行（★可扩展★）
        self.root.rowconfigure(2, weight=0)   # 主要按钮行
        self.root.rowconfigure(3, weight=0)   # 辅助按钮行
        self.root.rowconfigure(4, weight=0)   # 预处理选项面板
        self.root.rowconfigure(5, weight=0)   # 历史记录面板
        self.root.rowconfigure(6, weight=0)   # 状态栏

        # ----- 第0行：标题 -----
        ctk.CTkLabel(
            self.root, text="图片识别",
            font=("微软雅黑", 20), text_color="black", fg_color="#F7FEFE"
        ).grid(row=0, column=0, sticky="nw", padx=(10, 0), pady=(10, 0))

        self.label = ctk.CTkLabel(
            self.root, text="未选择图片文件",
            font=("微软雅黑", 15), text_color="black", fg_color="#F7FEFE"
        )
        self.label.grid(row=0, column=3, sticky="w")

        # ----- 第1行：文件列表（左侧）-----
        self.left_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        self.left_frame.rowconfigure(0, weight=1)
        self.left_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            self.left_frame, bg="#F7FEFE", fg="black", font=("微软雅黑", 12),
            width=28
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        # 水平滚动条
        self.listbox_hscroll = tk.Scrollbar(
            self.left_frame, orient="horizontal", command=self.listbox.xview
        )
        self.listbox_hscroll.grid(row=1, column=0, sticky="ew")
        self.listbox.config(xscrollcommand=self.listbox_hscroll.set)
        self.listbox.bind('<<ListboxSelect>>', self._on_select_listbox)
        # 右键菜单
        self.listbox.bind('<Button-3>', self._on_listbox_right_click)
        self._listbox_menu = tk.Menu(self.root, tearoff=0)
        self._listbox_menu.add_command(label="删除选中", command=self._remove_selected_file)
        self._listbox_menu.add_command(label="清空列表", command=self._clear_file_list)

        # ----- 第1行：输入画布（中间）-----
        self.frame_in = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_in.grid(row=1, column=2, sticky="nsew", padx=(10, 0), pady=(10, 0))
        self.frame_in.columnconfigure(0, weight=1)
        self.frame_in.rowconfigure(0, weight=0)   # 清除按钮
        self.frame_in.rowconfigure(1, weight=1)   # Canvas


        self.clear_bt = ctk.CTkButton(
            self.frame_in, text="清除", width=60, height=30,
            font=("微软雅黑", 13), text_color="black", fg_color="#5EDEDE",
            command=self._clear_canvas
        )
        self.clear_bt.grid(row=0, column=0, sticky="ne", padx=5, pady=5)

        self.canvas_in = ctk.CTkCanvas(
            self.frame_in, bg="#C1EBEB", highlightthickness=0
        )
        self.canvas_in.grid(row=1, column=0, sticky="nsew")

        # ----- 第1行：输出画布（右侧）-----
        self.frame_out = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_out.grid(row=1, column=3, sticky="nsew", padx=(10, 0), pady=(10, 0))
        self.frame_out.columnconfigure(0, weight=1)
        self.frame_out.rowconfigure(0, weight=0)   # 复制按钮
        self.frame_out.rowconfigure(1, weight=1)   # Canvas

        self.copy_btn = ctk.CTkButton(
            self.frame_out, text="复制", width=60, height=30,
            font=("微软雅黑", 13), text_color="black", fg_color="#5EDEDE",
            command=self._copy_canvas_text
        )
        self.copy_btn.grid(row=0, column=0, sticky="ne", padx=5, pady=5)

        self.canvas_out = ctk.CTkTextbox(
            self.frame_out, fg_color="#F7FEFE", text_color="black",
            font=("微软雅黑", 14), wrap="word"
        )
        self.canvas_out.grid(row=1, column=0, sticky="nsew")

        # ----- 拖拽提示区域（放在canvas_in上）-----
        self._creat_area()

        # ----- Canvas鼠标事件（区域选择）-----
        self.canvas_in.bind('<ButtonPress-1>', self._on_canvas_mouse_down)
        self.canvas_in.bind('<B1-Motion>', self._on_canvas_mouse_move)
        self.canvas_in.bind('<ButtonRelease-1>', self._on_canvas_mouse_up)
        self.root.bind('<Escape>', self._on_escape_key)

        # ----- 第2行：主要按钮 -----
        self.button = ctk.CTkButton(
            self.root, text="导入图片", command=self._Import_file,
            width=120, font=("微软雅黑", 16),
            text_color="black", fg_color="#91A5E0"
        )
        self.button.grid(row=2, column=2, sticky="w", padx=(10, 0), pady=(10, 5))

        self.recognize_bt = ctk.CTkButton(
            self.root, text="开始识别", command=self._start_recognize,
            width=120, font=("微软雅黑", 16),
            text_color="black", fg_color="#4CAF50"
        )
        self.recognize_bt.grid(row=2, column=3, sticky="w", padx=(10, 0), pady=(10, 5))

        self.region_btn = ctk.CTkButton(
            self.root, text="框选区域", command=self._toggle_region_selection,
            width=120, font=("微软雅黑", 16),
            text_color="black", fg_color="#FF9800"
        )
        self.region_btn.grid(row=2, column=2, sticky="e", padx=(0, 10), pady=(10, 5))

        # ----- 第3行：辅助按钮 -----
        self.reset_region_btn = ctk.CTkButton(
            self.root, text="重置区域", command=self._reset_region,
            width=120, font=("微软雅黑", 14),
            text_color="black", fg_color="#BDBDBD"
        )
        self.reset_region_btn.grid(row=3, column=2, sticky="w", padx=(10, 0), pady=(0, 10))

        self.export_txt_btn = ctk.CTkButton(
            self.root, text="导出 TXT", command=self._export_txt,
            width=90, font=("微软雅黑", 14),
            text_color="black", fg_color="#81C784"
        )
        self.export_txt_btn.grid(row=3, column=3, sticky="w", padx=(10, 0), pady=(0, 10))

        self.export_jpg_btn = ctk.CTkButton(
            self.root, text="导出对比图", command=self._export_jpg,
            width=110, font=("微软雅黑", 14),
            text_color="black", fg_color="#81C784"
        )
        self.export_jpg_btn.grid(row=3, column=3, sticky="e", padx=(0, 10), pady=(0, 10))

        # ----- 第4行：预处理选项面板 -----
        self._create_preprocess_panel()

        # ----- 第5行：历史记录面板 -----
        self.history_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.history_frame.grid(row=5, column=0, columnspan=5, sticky="nsew",
                                padx=10, pady=(5, 0))
        self.history_frame.columnconfigure(0, weight=1)
        self.history_frame.columnconfigure(1, weight=0)
        self.history_frame.rowconfigure(0, weight=0)
        self.history_frame.rowconfigure(1, weight=1)

        # 标题 + 搜索 + 按钮
        hist_title = ctk.CTkLabel(
            self.history_frame, text="📋 历史记录",
            font=("微软雅黑", 13, "bold"),
            text_color="black", fg_color="transparent"
        )
        hist_title.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))

        self.history_search_var = tk.StringVar()
        self.history_search_var.trace_add('write', self._on_history_search)
        self.history_search_entry = ctk.CTkEntry(
            self.history_frame, placeholder_text="搜索关键词...",
            textvariable=self.history_search_var, width=200, height=28
        )
        self.history_search_entry.grid(row=0, column=1, sticky="e", padx=5, pady=(5, 0))

        hist_btn_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        hist_btn_frame.grid(row=0, column=2, sticky="e", padx=5, pady=(5, 0))

        self.export_history_btn = ctk.CTkButton(
            hist_btn_frame, text="导出", width=50, height=28,
            font=("微软雅黑", 12), text_color="black", fg_color="#AED581",
            command=self._export_history
        )
        self.export_history_btn.grid(row=0, column=0, padx=2)

        self.clear_history_btn = ctk.CTkButton(
            hist_btn_frame, text="清空", width=50, height=28,
            font=("微软雅黑", 12), text_color="black", fg_color="#EF9A9A",
            command=self._clear_history
        )
        self.clear_history_btn.grid(row=0, column=1, padx=2)

        # 历史列表 + 滚动条
        hist_list_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        hist_list_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        hist_list_frame.columnconfigure(0, weight=1)
        hist_list_frame.rowconfigure(0, weight=1)

        self.history_listbox = tk.Listbox(
            hist_list_frame, bg="#F7FEFE", fg="black",
            font=("微软雅黑", 11), height=6
        )
        self.history_listbox.grid(row=0, column=0, sticky="nsew")
        self.history_listbox.bind('<<ListboxSelect>>', self._on_select_history)

        self.history_scrollbar = tk.Scrollbar(hist_list_frame, orient="vertical")
        self.history_scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_listbox.config(yscrollcommand=self.history_scrollbar.set)
        self.history_scrollbar.config(command=self.history_listbox.yview)

        # 默认占位文字
        self.history_listbox.insert(tk.END, "（暂无历史记录）")
        self.history_listbox.config(fg="gray")

        # ----- 第6行：状态栏 -----
        self.status_label = ctk.CTkLabel(
            self.root, text="就绪 — 请导入图片或拖入文件",
            font=("微软雅黑", 12), text_color="gray", fg_color="#F7FEFE"
        )
        self.status_label.grid(row=6, column=0, columnspan=5, sticky="ew",
                               padx=10, pady=(5, 10))

        # ----- 图标 & 关闭协议 -----
        try:
            self.root.iconbitmap(os.path.join(self._assets_dir, 'favicon.ico'))
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _center_window(self, width, height):
        """窗口居中显示"""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # ==================================================================
    # 文件导入 / 拖拽
    # ==================================================================

    def _creat_area(self):
        """创建拖拽提示区域"""
        icon = Image.open(os.path.join(self._assets_dir, 'drop_hint.png')).resize(
            (80, 80), Image.Resampling.LANCZOS).convert("RGBA")
        bg = Image.new("RGBA", icon.size, (193, 235, 235, 255))
        self.icon_img_tk = ImageTk.PhotoImage(Image.alpha_composite(bg, icon))
        self.canvas_in.create_image(275, 160, image=self.icon_img_tk,
                                    anchor="center", tags="icon")
        self.canvas_in.image = self.icon_img_tk

        def keep_icon_centered(event):
            self.canvas_in.coords("icon", event.width / 2, 160)
        self.canvas_in.bind("<Configure>", keep_icon_centered, add="+")

        self._hint_label1 = ctk.CTkLabel(
            self.canvas_in, text="拖入图片文件",
            font=("微软雅黑", 20), text_color="black", fg_color="transparent"
        )
        self._hint_label1.place(relx=0.5, rely=0.55, anchor="center")

        self._hint_label2 = ctk.CTkLabel(
            self.canvas_in, text="支持格式：jpg、jpeg、png、bmp、gif",
            font=("微软雅黑", 15), text_color="black", fg_color="transparent"
        )
        self._hint_label2.place(relx=0.5, rely=0.66, anchor="center")

        self._hint_label3 = ctk.CTkLabel(
            self.canvas_in, text="或点击「导入图片」按钮选择文件",
            font=("微软雅黑", 15), text_color="black", fg_color="transparent"
        )
        self._hint_label3.place(relx=0.5, rely=0.77, anchor="center")

        self.canvas_in.drop_target_register(DND_FILES)
        self.canvas_in.dnd_bind('<<DropEnter>>', self._drag_into)
        self.canvas_in.dnd_bind('<<DropLeave>>', self._drag_leave)
        self.canvas_in.dnd_bind('<<Drop>>', self._drop)

    def _hide_hints(self):
        """隐藏拖拽提示"""
        for lbl in [self._hint_label1, self._hint_label2, self._hint_label3]:
            if lbl:
                lbl.place_forget()

    def _show_hints(self):
        """显示拖拽提示"""
        if self._hint_label1:
            self._hint_label1.place(relx=0.5, rely=0.55, anchor="center")
        if self._hint_label2:
            self._hint_label2.place(relx=0.5, rely=0.66, anchor="center")
        if self._hint_label3:
            self._hint_label3.place(relx=0.5, rely=0.77, anchor="center")

    def _drag_into(self, event):
        """拖入文件时高亮"""
        if not self.selection_active:
            self.canvas_in.configure(bg="#9AEF84")

    def _drag_leave(self, event):
        """拖出时恢复"""
        self.canvas_in.configure(bg="#C1EBEB")

    def _drop(self, event):
        """拖放文件处理"""
        files = self.root.tk.splitlist(event.data)
        if files:
            self.file_list.clear()
            self.listbox.delete(0, tk.END)
            self._last_results.clear()
            self._queue_drained = False
            for f in files:
                self._load_image_file(f)

    def _Import_file(self):
        """点击导入图片按钮（支持多选）"""
        paths = filedialog.askopenfilenames(
            title="选择图片文件（可多选）",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if paths:
            # 上一批已识别完 → 清空旧列表开始新批次；否则追加
            if self._queue_drained:
                self.file_list.clear()
                self.listbox.delete(0, tk.END)
                self._last_results.clear()
            self._queue_drained = False
            for p in paths:
                self._load_image_file(p)

    def _load_image_file(self, file_path: str):
        """加载并显示图片文件"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            return

        print(f"加载文件: {file_path}")
        file_size = os.path.getsize(file_path)

        # 保存原始图像
        self.original_image_path = file_path
        self.original_pil_image = Image.open(file_path)

        # 重置区域选择
        self._reset_region_state()

        # 显示到Canvas
        self._display_on_canvas(file_path)

        # 加入文件列表
        self._add_file_to_list(file_path)

        # 状态
        fname = os.path.basename(file_path)
        self.label.configure(text=f"已选择: {fname}")
        self._status(f"已加载: {fname} ({file_size / 1024:.1f} KB)")

        # 隐藏提示
        self._hide_hints()

        # 新图片加入 → 队列未排空
        self._queue_drained = False

    def _display_on_canvas(self, file_path_or_image):
        """在canvas_in上显示图片（缩放适配）"""
        if isinstance(file_path_or_image, str):
            img = Image.open(file_path_or_image)
        else:
            img = file_path_or_image

        # 缩放适配Canvas
        cw = self.canvas_in.winfo_width() or 550
        ch = self.canvas_in.winfo_height() or 450
        img_resized = img.copy()
        img_resized.thumbnail((cw - 20, ch - 20), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(img_resized)
        self.canvas_in.delete("all")
        self.canvas_in.create_image(cw / 2, ch / 2, anchor="center", image=photo)
        self.canvas_in.image = photo
        self.current_photo = photo
        self.canvas_in.configure(bg="#C1EBEB")

    # ==================================================================
    # 文件列表管理
    # ==================================================================

    def _add_file_to_list(self, path):
        """添加文件到列表"""
        if path not in self.file_list:
            self.file_list.append(path)
            fname = os.path.basename(path)
            try:
                size_kb = os.path.getsize(path) / 1024
                self.listbox.insert(tk.END, f"{fname}  ({size_kb:.0f}KB)")
            except Exception:
                self.listbox.insert(tk.END, fname)

    def _on_select_listbox(self, event):
        """文件列表选择事件"""
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self.file_list):
            return

        path = self.file_list[idx]

        # ★ 修复：同步更新原始图像状态
        self.original_image_path = path
        try:
            self.original_pil_image = Image.open(path)
        except Exception:
            self.original_pil_image = None
        self._reset_region_state()

        # 显示图片
        self._display_on_canvas(path)
        self._hide_hints()
        fname = os.path.basename(path)
        self.label.configure(text=f"已选择: {fname}")

        # 切换文件时不自动清空输出画布，保留之前的识别结果
        try:
            size_kb = os.path.getsize(path) / 1024
            self._status(f"已切换: {fname} ({size_kb:.1f} KB)")
        except Exception:
            self._status(f"已切换: {fname}")

    def _on_listbox_right_click(self, event):
        """文件列表右键菜单"""
        try:
            idx = self.listbox.nearest(event.y)
            if idx >= 0:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(idx)
            self._listbox_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._listbox_menu.grab_release()

    def _remove_selected_file(self):
        """删除选中的文件"""
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self.file_list):
            return
        del self.file_list[idx]
        self.listbox.delete(idx)
        self._status("已从列表中移除文件")

    def _clear_file_list(self):
        """清空文件列表"""
        self.file_list.clear()
        self.listbox.delete(0, tk.END)
        self._status("文件列表已清空")

    def _clear_canvas(self):
        """清除输入画布、输出文字、文件列表（保留历史记录）"""
        self.canvas_in.delete("all")
        self._show_hints()
        self.canvas_in.configure(bg="#C1EBEB")
        self._drag_leave(None)
        self.label.configure(text="未选择图片文件")
        self._reset_region_state()
        self.original_image_path = None
        self.original_pil_image = None
        self.canvas_out.delete("0.0", "end")
        self.file_list.clear()
        self.listbox.delete(0, tk.END)
        self._queue_drained = True
        self._last_results.clear()
        self._status("已清除，可导入新图片开始识别")

    def _reset_region_state(self):
        """重置区域选择状态（不重绘Canvas）"""
        self.current_region = None
        if self.region_selector:
            self.region_selector.clear_selection()
            self.region_selector.deactivate()
        self.selection_active = False
        self.region_btn.configure(text="框选区域", fg_color="#FF9800")
        self.canvas_in.config(cursor='')

    def _reset_region(self):
        """重置区域：恢复完整图像显示"""
        self._reset_region_state()
        if self.original_image_path:
            self._display_on_canvas(self.original_image_path)
            self._hide_hints()
            self._status("区域已重置 — 将对完整图像进行识别")

    # ==================================================================
    # 区域选择（鼠标框选）
    # ==================================================================

    def _toggle_region_selection(self):
        """切换区域框选模式"""
        if not self.selection_active:
            # 进入框选模式
            if self.original_pil_image is None:
                messagebox.showwarning("提示", "请先导入图片")
                return
            self.selection_active = True
            self.region_selector = RegionSelector(self.canvas_in)
            self.region_selector.activate()
            self.region_btn.configure(text="确认区域", fg_color="#4CAF50")
            self._status("框选模式：拖拽鼠标框选区域，按 Esc 取消")
        else:
            # 确认框选
            if self.region_selector and self.region_selector.has_selection():
                cw = self.canvas_in.winfo_width()
                ch = self.canvas_in.winfo_height()
                if self.original_pil_image:
                    cropped = self.region_selector.crop_from_image(
                        self.original_pil_image, cw, ch
                    )
                    if cropped.size != self.original_pil_image.size:
                        self.current_region = self.region_selector.get_roi_coordinates()
                        self._display_on_canvas(cropped)
                        w, h = self.current_region[2] - self.current_region[0], \
                               self.current_region[3] - self.current_region[1]
                        self._status(f"✅ 已选取区域 ({w}×{h}px) — 仅对该区域识别")
                    else:
                        self._status("未检测到有效选区")
            else:
                self._status("未检测到有效选区")

            self.selection_active = False
            if self.region_selector:
                self.region_selector.deactivate()
            self.region_btn.configure(text="框选区域", fg_color="#FF9800")
            self.canvas_in.config(cursor='')

    def _on_canvas_mouse_down(self, event):
        """Canvas鼠标按下：仅框选模式处理"""
        if self.selection_active and self.region_selector:
            self.region_selector.on_mouse_down(event)

    def _on_canvas_mouse_move(self, event):
        """Canvas鼠标移动：仅框选模式处理"""
        if self.selection_active and self.region_selector:
            self.region_selector.on_mouse_move(event)

    def _on_canvas_mouse_up(self, event):
        """Canvas鼠标释放：仅框选模式处理"""
        if self.selection_active and self.region_selector:
            self.region_selector.on_mouse_up(event)

    def _on_escape_key(self, event):
        """Esc键：取消框选"""
        if self.selection_active:
            if self.region_selector:
                self.region_selector.clear_selection()
                self.region_selector.deactivate()
            self.selection_active = False
            self.region_btn.configure(text="框选区域", fg_color="#FF9800")
            self.canvas_in.config(cursor='')
            self._status("框选已取消")

    def _get_cropped_image(self):
        """获取裁剪后的PIL图像（有选区时返回裁剪，无选区返回原图）"""
        if self.original_pil_image is None:
            return None
        if self.current_region is None or self.region_selector is None:
            return self.original_pil_image
        cw = self.canvas_in.winfo_width()
        ch = self.canvas_in.winfo_height()
        return self.region_selector.crop_from_image(self.original_pil_image, cw, ch)

    # ==================================================================
    # OCR 识别
    # ==================================================================

    def _start_recognize(self):
        """开始识别 — 每张图片完成即追加显示结果"""
        if self._queue_drained:
            messagebox.showinfo("提示", "没有待识别图片。\n请导入新图片，或点击「清除」后重试。")
            return
        if not self.file_list and not self.original_pil_image:
            messagebox.showwarning("提示", "请先导入图片")
            return
        if not self.engine:
            messagebox.showwarning("提示", "OCR引擎未初始化")
            return

        # 获取当前预处理选项
        self._update_enabled_steps()
        steps = self.enabled_steps

        self.recognize_bt.configure(state="disabled")
        steps_desc = f"已选{len(steps)}项" if steps is not None else "全部"
        self._status(f"⏳ 识别中（预处理: {steps_desc}），请稍候...")
        self.canvas_out.delete("0.0", "end")

        # 追踪批量识别进度
        self._pending_tasks = 0
        self._completed_tasks = 0

        # 如果有区域选择，单张识别
        if self.current_region is not None and self.original_pil_image is not None:
            cropped = self._get_cropped_image()
            if cropped is not None:
                self._pending_tasks = 1
                img_path = self.original_image_path or ""
                self.engine.submit_image(
                    cropped,
                    lambda tid, txt, ok: self._on_single_result(tid, txt, ok, img_path),
                    enabled_steps=steps
                )
                return

        # 多张图片：分别提交，每张完成即刻追加显示
        if self.file_list:
            self._pending_tasks = len(self.file_list)
            for f in self.file_list:
                def make_callback(img_path):
                    return lambda tid, txt, ok: self._on_single_result(tid, txt, ok, img_path)
                self.engine.submit(f, make_callback(f), enabled_steps=steps)
        else:
            self._pending_tasks = 1
            img_path = self.original_image_path or ""
            self.engine.submit_image(
                self.original_pil_image,
                lambda tid, txt, ok: self._on_single_result(tid, txt, ok, img_path),
                enabled_steps=steps
            )

        # 提交完毕 → 标记队列已排空，保留列表供浏览
        self._queue_drained = True
        self.original_pil_image = None
        self.original_image_path = None

    def _on_single_result(self, task_id, text, success, image_path=""):
        """单张识别完成回调 — 立即追加到输出画布"""
        self._completed_tasks += 1

        def update_ui():
            if not success:
                return

            # 第一张结果：清空之前内容
            if self._completed_tasks == 1:
                self.canvas_out.delete("0.0", "end")

            # 追加文件标签和识别文本
            self._append_ocr_result(task_id, text, image_path)

            # 存入BST历史记录（每条单独存）
            file_size = os.path.getsize(image_path) if image_path and os.path.exists(image_path) else 0
            self.history_manager.add_record(
                image_path=image_path,
                ocr_text=text,
                file_size=file_size,
                region=self.current_region,
            )
            # 记录映射：导出时按图片分别保存
            self._last_results[image_path] = text
            # 每次追加记录后自动保存到 history/ 目录
            self._save_history()

            # 进度反馈
            if self._completed_tasks >= self._pending_tasks:
                self.recognize_bt.configure(state="normal")
                self._status(f"✅ 识别完成 — 共 {self._completed_tasks} 张")
            else:
                self._status(f"⏳ 识别中... {self._completed_tasks}/{self._pending_tasks}")
            self._refresh_history_listbox()

        self.root.after(0, update_ui)

    def _append_ocr_result(self, task_id, text, image_path=""):
        """追加一条识别结果到输出框底部（不覆盖已有内容）"""
        fname = os.path.basename(image_path) if image_path else f"任务{task_id}"
        # 如果不是第一条，先加分隔
        current = self.canvas_out.get("0.0", "end-1c")
        if current.strip():
            self.canvas_out.insert("end", "\n\n─── 📄 " + fname + " ───\n")
        else:
            self.canvas_out.insert("end", "📄 " + fname + "\n")
        self.canvas_out.insert("end", text + "\n")

    def _display_ocr_result(self, text):
        """全量显示识别结果（用于历史记录回显，会清空已有内容）"""
        self.canvas_out.delete("0.0", "end")
        self.canvas_out.insert("end", text)

    def _copy_canvas_text(self):
        """复制输出框文字到剪贴板"""
        try:
            # 优先复制用户选中部分
            content = self.canvas_out.selection_get()
        except tk.TclError:
            # 没有选中则复制全部
            content = self.canvas_out.get("0.0", "end-1c")
        if content.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self._status("✅ 文字已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "暂无文字可复制")

    def _export_txt(self):
        """导出 TXT：选目录 → 每图一个 .txt"""
        if not self.file_list:
            messagebox.showwarning("提示", "没有可导出的图片")
            return
        out_dir = filedialog.askdirectory(title="选择导出目录")
        if not out_dir:
            return
        count = 0
        for path in self.file_list:
            text = self._last_results.get(path, "")
            fname = os.path.splitext(os.path.basename(path))[0] + ".txt"
            ResultParser.export_to_file(text, os.path.join(out_dir, fname))
            count += 1
        self._status(f"✅ 已导出 {count} 个 TXT 到 {out_dir}/")

    def _export_jpg(self):
        """导出对比图：选目录 → 每图一张 OCR 可视化"""
        if not self.file_list:
            messagebox.showwarning("提示", "没有可导出的图片")
            return
        out_dir = filedialog.askdirectory(title="选择导出目录")
        if not out_dir:
            return
        count = 0
        for path in self.file_list:
            prefix = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0])
            try:
                self.engine.visualize(path, prefix)
                count += 1
            except Exception as e:
                print(f"可视化失败 {path}: {e}")
        self._status(f"✅ 已导出 {count} 张对比图到 {out_dir}/")

    # ==================================================================
    # 历史记录
    # ==================================================================

    def _refresh_history_listbox(self):
        """刷新历史记录列表"""
        self.history_listbox.delete(0, tk.END)
        self._history_id_map = {}

        keyword = self.history_search_var.get().strip()
        if keyword:
            records = self.history_manager.search_by_keyword(keyword)
            records.sort(key=lambda r: r.timestamp, reverse=True)
        else:
            records = self.history_manager.get_all_records(newest_first=True)

        if not records:
            self.history_listbox.insert(tk.END, "（暂无历史记录）")
            self.history_listbox.config(fg="gray")
            return

        self.history_listbox.config(fg="black")
        for r in records:
            time_str = time.strftime('%m-%d %H:%M', time.localtime(r.timestamp))
            fname = os.path.basename(r.image_path) if r.image_path else "(未知)"
            size_str = f"{r.file_size / 1024:.0f}KB" if r.file_size else "?"
            preview = r.ocr_text.replace('\n', ' ')[:40]
            display = f"[{time_str}] {fname} | {size_str} | {preview}"
            if r.region:
                display += " 📐"
            idx = self.history_listbox.size()
            self.history_listbox.insert(tk.END, display)
            self._history_id_map[idx] = r  # 存储完整记录（含图片路径）

    def _on_select_history(self, event):
        """点击历史记录回显结果 + 加载对应图片"""
        sel = self.history_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        record = self._history_id_map.get(idx)
        if not record:
            return
        self._display_ocr_result(record.ocr_text)
        # 图片路径存在则加载到输入画布
        if record.image_path and os.path.exists(record.image_path):
            self._display_on_canvas(record.image_path)
            self._hide_hints()
            self._status(f"📋 已回显历史记录 [{record.record_id}]")
        else:
            self._status(f"📋 已回显文字（图片已不可用）")

    def _on_history_search(self, *args):
        """搜索框文本变化实时过滤"""
        self._refresh_history_listbox()

    def _clear_history(self):
        """清空所有历史记录"""
        count = self.history_manager.get_record_count()
        if count == 0:
            messagebox.showinfo("提示", "历史记录为空")
            return
        if messagebox.askyesno("确认", f"确定清空全部 {count} 条历史记录吗？"):
            self.history_manager.clear_all()
            self._history_id_map = {}
            self._refresh_history_listbox()
            self._status("历史记录已清空")

    def _export_history(self):
        """导出历史记录为JSON"""
        count = self.history_manager.get_record_count()
        if count == 0:
            messagebox.showinfo("提示", "无历史记录可导出")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filepath:
            self.history_manager.export_to_json(filepath)
            self._status(f"✅ 已导出 {count} 条记录到: {os.path.basename(filepath)}")

    # ==================================================================
    # 预处理选项面板
    # ==================================================================

    # 预处理步骤定义：(key, label)
    PREPROCESS_STEPS = [
        ('grayscale',     '灰度化'),
        ('median_filter', '中值滤波'),
        ('down_sample',   '金字塔下采样'),
        ('binarize',      '自适应二值化'),
        ('deskew',        'Hough倾斜矫正'),
        ('usm',           'USM锐化'),
        ('gamma',         '伽马校正'),
        ('clahe',         'CLAHE增强'),
    ]

    def _create_preprocess_panel(self):
        """创建可展开的预处理选择面板"""
        self.preprocess_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.preprocess_frame.grid(row=4, column=0, columnspan=5, sticky="ew",
                                   padx=10, pady=(5, 0))

        # 展开/折叠按钮
        self.preprocess_expanded = tk.BooleanVar(value=False)
        self.preprocess_toggle_btn = ctk.CTkButton(
            self.preprocess_frame, text="🔧 预处理选项 ▸",
            width=160, height=28,
            font=("微软雅黑", 13), text_color="black", fg_color="#E0E0E0",
            command=self._toggle_preprocess_panel
        )
        self.preprocess_toggle_btn.grid(row=0, column=0, sticky="w")

        # 全选 / 全不选快捷按钮
        self.preprocess_all_btn = ctk.CTkButton(
            self.preprocess_frame, text="全选", width=60, height=24,
            font=("微软雅黑", 11), text_color="black", fg_color="#BBDEFB",
            command=self._preprocess_select_all
        )

        self.preprocess_none_btn = ctk.CTkButton(
            self.preprocess_frame, text="全不选", width=60, height=24,
            font=("微软雅黑", 11), text_color="black", fg_color="#FFCDD2",
            command=self._preprocess_select_none
        )

        # 复选框容器（初始隐藏）
        self.checkbox_frame = ctk.CTkFrame(self.preprocess_frame, fg_color="transparent")
        self.checkbox_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(5, 0))
        self.checkbox_frame.grid_remove()

        self.step_vars = {}
        self.step_widgets = {}
        self._updating_steps = False  # 防递归标志
        for i, (key, label) in enumerate(self.PREPROCESS_STEPS):
            var = tk.BooleanVar(value=False)  # 默认不勾选
            cb = ctk.CTkCheckBox(
                self.checkbox_frame, text=label, variable=var,
                font=("微软雅黑", 12), text_color="black",
                fg_color="#5EDEDE", hover_color="#4DB6AC",
            )
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=10, pady=3)
            self.step_vars[key] = var
            self.step_widgets[key] = cb
            # 每次勾选/取消时触发联动逻辑
            var.trace_add('write', lambda *_, k=key: self._on_step_toggled(k))

    def _toggle_preprocess_panel(self):
        """展开/折叠预处理面板"""
        if self.preprocess_expanded.get():
            self.preprocess_expanded.set(False)
            self.checkbox_frame.grid_remove()
            self.preprocess_all_btn.grid_remove()
            self.preprocess_none_btn.grid_remove()
            self.preprocess_toggle_btn.configure(text="🔧 预处理选项 ▸", fg_color="#E0E0E0")
        else:
            self.preprocess_expanded.set(True)
            self.checkbox_frame.grid()
            self.preprocess_all_btn.grid(row=0, column=1, sticky="w", padx=5)
            self.preprocess_none_btn.grid(row=0, column=2, sticky="w", padx=5)
            self.preprocess_toggle_btn.configure(text="🔧 预处理选项 ▾", fg_color="#FFF9C4")

    def _preprocess_select_all(self):
        """全选所有预处理步骤"""
        self._updating_steps = True
        for var in self.step_vars.values():
            var.set(True)
        self._updating_steps = False
        self._update_enabled_steps()

    def _preprocess_select_none(self):
        """全不选所有预处理步骤"""
        self._updating_steps = True
        for var in self.step_vars.values():
            var.set(False)
        self._updating_steps = False
        self._update_enabled_steps()

    def _on_step_toggled(self, key):
        """复选框变化时触发（防递归）"""
        if self._updating_steps:
            return
        self._updating_steps = True
        try:
            self._update_enabled_steps()
        finally:
            self._updating_steps = False

    def _update_enabled_steps(self):
        """根据复选框状态更新 self.enabled_steps，含灰度化自动绑定"""
        # 灰度化绑定：任意非灰度化步骤被勾选时，灰度化自动勾选+禁用
        has_other = any(
            var.get() for key, var in self.step_vars.items()
            if key != 'grayscale'
        )
        grayscale_var = self.step_vars.get('grayscale')
        grayscale_widget = self.step_widgets.get('grayscale')

        if has_other:
            if grayscale_var:
                grayscale_var.set(True)
            if grayscale_widget:
                grayscale_widget.configure(state='disabled')
        else:
            if grayscale_var:
                grayscale_var.set(False)
            if grayscale_widget:
                grayscale_widget.configure(state='normal')

        # 收集启用的步骤
        selected = set()
        for key, var in self.step_vars.items():
            if var.get():
                selected.add(key)
        self.enabled_steps = selected if selected else set()

        all_count = len(self.PREPROCESS_STEPS)
        sel_count = len(selected)
        if sel_count == 0:
            self._status("预处理：全部关闭（原图直传OCR）")
        elif sel_count == all_count:
            self._status("预处理：全部启用")
        else:
            self._status(f"预处理：已选 {sel_count}/{all_count} 项")

    # ==================================================================
    # 历史记录持久化
    # ==================================================================

    def _load_history(self):
        """启动时从 history/ 目录加载历史记录"""
        os.makedirs(self._history_dir, exist_ok=True)
        hist_file = os.path.join(self._history_dir, 'ocr_history.json')
        if os.path.exists(hist_file):
            try:
                count = self.history_manager.import_from_json(hist_file)
                if count > 0:
                    print(f"[历史] 已加载 {count} 条历史记录")
            except Exception as e:
                print(f"[历史] 加载失败: {e}")

    def _save_history(self):
        """保存历史记录到 history/ 目录"""
        os.makedirs(self._history_dir, exist_ok=True)
        hist_file = os.path.join(self._history_dir, 'ocr_history.json')
        try:
            self.history_manager.export_to_json(hist_file)
        except Exception as e:
            print(f"[历史] 保存失败: {e}")

    # ==================================================================
    # 状态栏
    # ==================================================================

    def _status(self, msg: str):
        """更新状态栏消息"""
        self.status_label.configure(text=msg)

    # ==================================================================
    # 关闭
    # ==================================================================

    def _close(self):
        """关闭窗口"""
        if not messagebox.askokcancel("退出", "是否退出程序？"):
            return
        if self.engine:
            self.engine.shutdown()
        # 自动保存历史记录
        if self.history_manager.get_record_count() > 0:
            try:
                self._save_history()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        """启动主循环"""
        self.root.mainloop()
