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
        self.showing_processed = False      # 是否正在查看预处理效果图
        self.original_image_path = None
        self.original_pil_image = None

        # ===== 预处理选项 =====
        # None=全部启用, set()=全不启用, {'grayscale','deskew'}=部分启用
        self.enabled_steps = None

        # ===== 队列状态 =====
        self._queue_drained = True   # 当前无待识别图片
        self._last_results = {}      # {image_path: ocr_text} 导出用
        self._processed_images = {}  # {image_path: PIL.Image} 预处理效果图
        self._progress_tick_id = None   # 进度条计时器 ID

        # ===== 历史记录 =====
        self.history_manager = HistoryManager()
        self._history_id_map = {}           # listbox索引 → ocr_text
        self._history_dir = os.path.join(os.path.dirname(__file__), '..', 'history')
        self._load_history()                # 启动时加载持久化记录

        # ===== 搭建界面 =====
        self._setup_ui()
        self._refresh_history_listbox()     # 启动时展示已加载的历史记录

    def set_engine(self, engine):
        """注入OCR引擎（由main.py调用）"""
        self.engine = engine

    # ==================================================================
    # 界面搭建
    # ==================================================================

    def _setup_ui(self):
        """搭建全部UI组件"""
        self._assets_dir = os.path.join(os.path.dirname(__file__), 'assets')

        # ===== 配色方案 =====
        BG = "#EEF2F6"
        CARD = "#FFFFFF"
        TEXT = "#1E293B"
        SUBTEXT = "#64748B"
        PRIMARY = "#3B82F6"
        SUCCESS = "#22C55E"
        WARNING = "#F97316"
        CANVAS_BG = "#E2E8F0"

        # ===== 窗口基础设置 =====
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self._center_window(1400, 900)

        # ===== 网格布局：3列 × 4行 =====
        self.root.columnconfigure(0, weight=0, minsize=280)  # 左侧面板
        self.root.columnconfigure(1, weight=1)                # 输入画布
        self.root.columnconfigure(2, weight=1)                # 输出区域
        self.root.rowconfigure(0, weight=0)   # 标题
        self.root.rowconfigure(1, weight=1)   # 主区域
        self.root.rowconfigure(2, weight=0)   # 历史记录
        self.root.rowconfigure(3, weight=0)   # 状态栏

        # ================================================================
        # Row 0: 标题栏
        # ================================================================
        title_frame = ctk.CTkFrame(self.root, fg_color=BG)
        title_frame.grid(row=0, column=0, columnspan=3, sticky="ew",
                         padx=15, pady=(15, 5))

        ctk.CTkLabel(title_frame, text="本地OCR文字识别工具",
                     font=("微软雅黑", 22, "bold"), text_color=TEXT
                     ).pack(side="left")

        self.label = ctk.CTkLabel(title_frame, text="未选择图片文件",
                                  font=("微软雅黑", 13), text_color=SUBTEXT)
        self.label.pack(side="right")

        # ================================================================
        # Row 1, Col 0: 左侧面板
        # ================================================================
        sidebar = ctk.CTkFrame(self.root, fg_color=BG)
        sidebar.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=(5, 0))
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(0, weight=0)  # 文件操作卡片
        sidebar.rowconfigure(1, weight=1)  # 预处理卡片

        # --- 文件操作卡片 ---
        file_card = ctk.CTkFrame(sidebar, fg_color=CARD, corner_radius=10)
        file_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        file_card.columnconfigure(0, weight=1)

        file_header = ctk.CTkFrame(file_card, fg_color="transparent")
        file_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        ctk.CTkLabel(file_header, text="📁 文件列表",
                     font=("微软雅黑", 14, "bold"), text_color=TEXT
                     ).pack(side="left")
        self.file_count_label = ctk.CTkLabel(file_header, text="(0)",
                                              font=("微软雅黑", 12), text_color=SUBTEXT)
        self.file_count_label.pack(side="left", padx=4)

        # 按钮行
        btn_row = ctk.CTkFrame(file_card, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.button = ctk.CTkButton(
            btn_row, text="📥 导入图片", command=self._Import_file,
            width=110, height=32, font=("微软雅黑", 12),
            text_color="white", fg_color=PRIMARY, hover_color="#2563EB"
        )
        self.button.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="🗑 清空", command=self._clear_file_list,
            width=70, height=32, font=("微软雅黑", 12),
            text_color=TEXT, fg_color="#CBD5E1", hover_color="#94A3B8"
        ).pack(side="left")

        # 文件列表
        self.left_frame = ctk.CTkFrame(file_card, fg_color="transparent")
        self.left_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.left_frame.rowconfigure(0, weight=1)
        self.left_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            self.left_frame, bg="#F8FAFC", fg=TEXT,
            font=("微软雅黑", 11), width=28, height=8,
            selectbackground=PRIMARY, selectforeground="white",
            relief="flat", borderwidth=1, highlightthickness=0
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox_hscroll = tk.Scrollbar(
            self.left_frame, orient="horizontal", command=self.listbox.xview
        )
        self.listbox_hscroll.grid(row=1, column=0, sticky="ew")
        self.listbox.config(xscrollcommand=self.listbox_hscroll.set)
        self.listbox.bind('<<ListboxSelect>>', self._on_select_listbox)
        self.listbox.bind('<Button-3>', self._on_listbox_right_click)
        self._listbox_menu = tk.Menu(self.root, tearoff=0)
        self._listbox_menu.add_command(label="删除选中", command=self._remove_selected_file)
        self._listbox_menu.add_command(label="清空列表", command=self._clear_file_list)

        # --- 预处理卡片 ---
        self._create_preprocess_panel(sidebar)

        # ================================================================
        # Row 1, Col 1: 输入画布
        # ================================================================
        self.frame_in = ctk.CTkFrame(self.root, fg_color=CARD, corner_radius=10)
        self.frame_in.grid(row=1, column=1, sticky="nsew", padx=(4, 4), pady=(5, 0))
        self.frame_in.columnconfigure(0, weight=1)
        self.frame_in.rowconfigure(0, weight=0)
        self.frame_in.rowconfigure(1, weight=1)

        # 工具栏
        in_toolbar = ctk.CTkFrame(self.frame_in, fg_color="transparent")
        in_toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.region_btn = ctk.CTkButton(
            in_toolbar, text="✂ 框选区域", command=self._toggle_region_selection,
            width=100, height=30, font=("微软雅黑", 12),
            text_color="white", fg_color=WARNING, hover_color="#EA580C"
        )
        self.region_btn.pack(side="left", padx=(0, 5))

        self.reset_region_btn = ctk.CTkButton(
            in_toolbar, text="↺ 重置区域", command=self._reset_region,
            width=100, height=30, font=("微软雅黑", 12),
            text_color=TEXT, fg_color="#CBD5E1", hover_color="#94A3B8"
        )
        self.reset_region_btn.pack(side="left", padx=5)

        self.clear_bt = ctk.CTkButton(
            in_toolbar, text="✕ 清除", command=self._clear_canvas,
            width=80, height=30, font=("微软雅黑", 12),
            text_color=TEXT, fg_color="#CBD5E1", hover_color="#94A3B8"
        )
        self.clear_bt.pack(side="left", padx=5)

        self.toggle_preprocess_btn = ctk.CTkButton(
            in_toolbar, text="🔬 查看预处理", command=self._toggle_processed_view,
            width=120, height=30, font=("微软雅黑", 12),
            text_color=TEXT, fg_color="#E2E8F0", hover_color="#CBD5E1",
            state="disabled"
        )
        self.toggle_preprocess_btn.pack(side="right")

        # 画布
        self.canvas_in = ctk.CTkCanvas(
            self.frame_in, bg=CANVAS_BG, highlightthickness=0
        )
        self.canvas_in.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # ================================================================
        # Row 1, Col 2: 输出区域
        # ================================================================
        self.frame_out = ctk.CTkFrame(self.root, fg_color=CARD, corner_radius=10)
        self.frame_out.grid(row=1, column=2, sticky="nsew", padx=(4, 15), pady=(5, 0))
        self.frame_out.columnconfigure(0, weight=1)
        self.frame_out.rowconfigure(0, weight=0)
        self.frame_out.rowconfigure(1, weight=1)

        # 工具栏
        out_toolbar = ctk.CTkFrame(self.frame_out, fg_color="transparent")
        out_toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.recognize_bt = ctk.CTkButton(
            out_toolbar, text="🚀 开始识别", command=self._start_recognize,
            width=120, height=34, font=("微软雅黑", 13, "bold"),
            text_color="white", fg_color=SUCCESS, hover_color="#16A34A"
        )
        self.recognize_bt.pack(side="left", padx=(0, 8))

        self.copy_btn = ctk.CTkButton(
            out_toolbar, text="📋 复制", command=self._copy_canvas_text,
            width=80, height=30, font=("微软雅黑", 12),
            text_color=TEXT, fg_color="#CBD5E1", hover_color="#94A3B8"
        )
        self.copy_btn.pack(side="left", padx=4)

        self.export_txt_btn = ctk.CTkButton(
            out_toolbar, text="📄 导出TXT", command=self._export_txt,
            width=90, height=30, font=("微软雅黑", 12),
            text_color=TEXT, fg_color="#CBD5E1", hover_color="#94A3B8"
        )
        self.export_txt_btn.pack(side="left", padx=4)

        self.export_jpg_btn = ctk.CTkButton(
            out_toolbar, text="🖼 导出对比图", command=self._export_jpg,
            width=110, height=30, font=("微软雅黑", 12),
            text_color=TEXT, fg_color="#CBD5E1", hover_color="#94A3B8"
        )
        self.export_jpg_btn.pack(side="left", padx=4)

        # 文本框
        self.canvas_out = ctk.CTkTextbox(
            self.frame_out, fg_color="#F8FAFC", text_color=TEXT,
            font=("微软雅黑", 14), wrap="word", border_width=0
        )
        self.canvas_out.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # ================================================================
        # 拖拽提示 + 鼠标事件
        # ================================================================
        self._creat_area()
        self.canvas_in.bind('<ButtonPress-1>', self._on_canvas_mouse_down)
        self.canvas_in.bind('<B1-Motion>', self._on_canvas_mouse_move)
        self.canvas_in.bind('<ButtonRelease-1>', self._on_canvas_mouse_up)
        self.root.bind('<Escape>', self._on_escape_key)

        # ================================================================
        # Row 2: 历史记录面板
        # ================================================================
        self.history_frame = ctk.CTkFrame(self.root, fg_color=CARD, corner_radius=10)
        self.history_frame.grid(row=2, column=0, columnspan=3, sticky="nsew",
                                padx=15, pady=(8, 0))
        self.history_frame.columnconfigure(0, weight=1)
        self.history_frame.rowconfigure(0, weight=0)
        self.history_frame.rowconfigure(1, weight=1)

        hist_header = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        hist_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        ctk.CTkLabel(hist_header, text="📋 历史记录",
                     font=("微软雅黑", 14, "bold"), text_color=TEXT
                     ).pack(side="left")

        self.history_search_var = tk.StringVar()
        self.history_search_var.trace_add('write', self._on_history_search)
        self.history_search_entry = ctk.CTkEntry(
            hist_header, placeholder_text="🔍 搜索关键词...",
            textvariable=self.history_search_var, width=200, height=30
        )
        self.history_search_entry.pack(side="right", padx=5)

        self.clear_history_btn = ctk.CTkButton(
            hist_header, text="清空", width=55, height=28,
            font=("微软雅黑", 11), text_color="white", fg_color="#EF4444",
            hover_color="#DC2626", command=self._clear_history
        )
        self.clear_history_btn.pack(side="right", padx=3)

        self.export_history_btn = ctk.CTkButton(
            hist_header, text="导出", width=55, height=28,
            font=("微软雅黑", 11), text_color=TEXT, fg_color="#CBD5E1",
            hover_color="#94A3B8", command=self._export_history
        )
        self.export_history_btn.pack(side="right", padx=3)

        # 历史列表 + 滚动条
        hist_list_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        hist_list_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        hist_list_frame.columnconfigure(0, weight=1)
        hist_list_frame.rowconfigure(0, weight=1)

        self.history_listbox = tk.Listbox(
            hist_list_frame, bg="#F8FAFC", fg=TEXT,
            font=("微软雅黑", 11), height=5,
            selectbackground=PRIMARY, selectforeground="white",
            relief="flat", borderwidth=1, highlightthickness=0
        )
        self.history_listbox.grid(row=0, column=0, sticky="nsew")
        self.history_listbox.bind('<<ListboxSelect>>', self._on_select_history)

        self.history_scrollbar = tk.Scrollbar(hist_list_frame, orient="vertical")
        self.history_scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_listbox.config(yscrollcommand=self.history_scrollbar.set)
        self.history_scrollbar.config(command=self.history_listbox.yview)

        self.history_listbox.insert(tk.END, "（暂无历史记录）")
        self.history_listbox.config(fg=SUBTEXT)

        # ================================================================
        # Row 3: 状态栏 + 进度条
        # ================================================================
        status_frame = ctk.CTkFrame(self.root, fg_color=BG)
        status_frame.grid(row=3, column=0, columnspan=3, sticky="ew",
                         padx=15, pady=(8, 12))
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            status_frame, text="就绪 — 请导入图片或拖入文件",
            font=("微软雅黑", 12), text_color=SUBTEXT
        )
        self.status_label.pack(side="left")

        # 进度条区域（初始隐藏）
        self.progress_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, width=180, height=10,
            progress_color=SUCCESS, fg_color="#E2E8F0"
        )
        self.progress_bar.pack(side="left", padx=(0, 8))
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="0%",
            font=("微软雅黑", 12, "bold"), text_color=SUCCESS
        )
        self.progress_label.pack(side="left")

        # ===== 图标 & 关闭协议 =====
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
        bg = Image.new("RGBA", icon.size, (226, 232, 240, 255))
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
        self.canvas_in.itemconfigure("icon", state="hidden")
        for lbl in [self._hint_label1, self._hint_label2, self._hint_label3]:
            if lbl:
                lbl.place_forget()

    def _show_hints(self):
        """显示拖拽提示"""
        # 确保图标在canvas上
        if self.icon_img_tk:
            icons = self.canvas_in.find_withtag("icon")
            if not icons:
                cw = self.canvas_in.winfo_width() or 550
                self.canvas_in.create_image(cw / 2, 160, image=self.icon_img_tk,
                                            anchor="center", tags="icon")
            else:
                self.canvas_in.itemconfigure("icon", state="normal")
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
        self.canvas_in.configure(bg="#E2E8F0")

    def _drop(self, event):
        """拖放文件处理"""
        files = self.root.tk.splitlist(event.data)
        if files:
            # 上一批已识别完 → 清空旧列表开始新批次；否则追加
            if self._queue_drained:
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
        self.canvas_in.delete("displayed")
        self.canvas_in.create_image(cw / 2, ch / 2, anchor="center",
                                    image=photo, tags="displayed")
        self.canvas_in.image = photo
        self.current_photo = photo
        self.canvas_in.configure(bg="#E2E8F0")

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
        self.file_count_label.configure(text=f"({len(self.file_list)})")

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

        # 切换文件时更新预处理图切换按钮状态
        self.showing_processed = False
        if path in self._processed_images:
            self.toggle_preprocess_btn.configure(state="normal", text="🔬 查看预处理",
                                                 fg_color="#E2E8F0")
        else:
            self.toggle_preprocess_btn.configure(state="disabled", text="🔬 查看预处理",
                                                 fg_color="#E2E8F0")

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
        self.file_count_label.configure(text="(0)")
        self._status("文件列表已清空")

    def _clear_canvas(self):
        """清除输入画布、输出文字、文件列表（保留历史记录）"""
        self.canvas_in.delete("displayed")
        self._show_hints()
        self.canvas_in.configure(bg="#E2E8F0")
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
        self._processed_images.clear()
        self.showing_processed = False
        self.file_count_label.configure(text="(0)")
        self.toggle_preprocess_btn.configure(state="disabled", text="🔬 查看预处理",
                                             fg_color="#E2E8F0")
        if self._progress_tick_id is not None:
            self.root.after_cancel(self._progress_tick_id)
            self._progress_tick_id = None
        if hasattr(self, '_current_image_start'):
            del self._current_image_start
        self.progress_frame.pack_forget()
        self._status("已清除，可导入新图片开始识别")

    def _reset_region_state(self):
        """重置区域选择状态（不重绘Canvas）"""
        self.current_region = None
        if self.region_selector:
            self.region_selector.clear_selection()
            self.region_selector.deactivate()
        self.selection_active = False
        self.showing_processed = False
        self.region_btn.configure(text="框选区域", fg_color="#F97316")
        self.canvas_in.config(cursor='')

    def _reset_region(self):
        """重置区域：恢复完整图像显示"""
        self._reset_region_state()
        if self.original_image_path:
            self._display_on_canvas(self.original_image_path)
            self._hide_hints()
            self._status("区域已重置 — 将对完整图像进行识别")

    def _toggle_processed_view(self):
        """切换显示：原图 ←→ 预处理效果图"""
        if not self.showing_processed:
            path = self.original_image_path
            if path and path in self._processed_images:
                self._display_on_canvas(self._processed_images[path])
                self.showing_processed = True
                self.toggle_preprocess_btn.configure(text="查看原图", fg_color="#F97316")
                self._status("正在查看预处理效果图")
        else:
            if self.original_image_path and os.path.exists(self.original_image_path):
                self._display_on_canvas(self.original_image_path)
            self.showing_processed = False
            self.toggle_preprocess_btn.configure(text="🔬 查看预处理", fg_color="#E2E8F0")
            self._status("正在查看原始图片")

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
                        self.region_selector.clear_selection()
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
            self.region_btn.configure(text="框选区域", fg_color="#F97316")
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
            self.region_btn.configure(text="框选区域", fg_color="#F97316")
            self.canvas_in.config(cursor='')
            self._status("框选已取消")

    def _get_cropped_image(self):
        """获取裁剪后的PIL图像（有选区时返回裁剪，无选区返回原图）

        直接使用 self.current_region 坐标裁剪，不依赖 RegionSelector 内部状态
        （因为 _toggle_region_selection 确认选区后会 clear_selection，
        导致 RegionSelector 内部坐标丢失，所以必须用 self.current_region）。
        """
        if self.original_pil_image is None:
            return None
        if self.current_region is None:
            return self.original_pil_image

        cw = self.canvas_in.winfo_width() or 550
        ch = self.canvas_in.winfo_height() or 450
        img_w, img_h = self.original_pil_image.size

        # 坐标映射：Canvas坐标 → 原始图像坐标（与 RegionSelector 逻辑一致）
        scale = min(cw / img_w, ch / img_h)
        offset_x = (cw - img_w * scale) / 2
        offset_y = (ch - img_h * scale) / 2

        x1, y1, x2, y2 = self.current_region

        def _to_image(cx, cy):
            """Canvas坐标 → 图像像素坐标"""
            ix = (cx - offset_x) / scale if scale > 0 else cx
            iy = (cy - offset_y) / scale if scale > 0 else cy
            return (
                max(0, min(img_w - 1, int(round(ix)))),
                max(0, min(img_h - 1, int(round(iy)))),
            )

        img_x1, img_y1 = _to_image(x1, y1)
        img_x2, img_y2 = _to_image(x2, y2)

        crop_x1, crop_x2 = min(img_x1, img_x2), max(img_x1, img_x2)
        crop_y1, crop_y2 = min(img_y1, img_y2), max(img_y1, img_y2)

        if crop_x2 - crop_x1 < 5 or crop_y2 - crop_y1 < 5:
            return self.original_pil_image

        return self.original_pil_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))

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

        # 显示进度条 + 启动 10 秒计时
        self._current_image_start = time.time()
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color="#3B82F6")
        self.progress_label.configure(text="0%", text_color="#3B82F6")
        self.progress_frame.pack(side="right")
        if self._progress_tick_id is not None:
            self.root.after_cancel(self._progress_tick_id)
        self._progress_tick_id = self.root.after(100, self._tick_progress)

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
                    lambda tid, txt, ok, proc: self._on_single_result(tid, txt, ok, img_path, proc),
                    enabled_steps=steps
                )
                return

        # 多张图片：分别提交，每张完成即刻追加显示
        if self.file_list:
            self._pending_tasks = len(self.file_list)
            for f in self.file_list:
                def make_callback(img_path):
                    return lambda tid, txt, ok, proc: self._on_single_result(tid, txt, ok, img_path, proc)
                self.engine.submit(f, make_callback(f), enabled_steps=steps)
        else:
            self._pending_tasks = 1
            img_path = self.original_image_path or ""
            self.engine.submit_image(
                self.original_pil_image,
                lambda tid, txt, ok, proc: self._on_single_result(tid, txt, ok, img_path, proc),
                enabled_steps=steps
            )

        # 提交完毕 → 标记队列已排空，保留列表供浏览
        self._queue_drained = True

    def _on_single_result(self, task_id, text, success, image_path="", processed_image=None):
        """单张识别完成回调 — 立即追加到输出画布"""
        self._completed_tasks += 1

        def update_ui():
            # ===== 进度 / 状态更新 =====
            if self._completed_tasks >= self._pending_tasks:
                self.recognize_bt.configure(state="normal")
                self._status(f"✅ 识别完成 — 共 {self._completed_tasks} 张")
            else:
                self._current_image_start = time.time()  # 下一张图重新计时
                pct = int(self.progress_bar.get() * 100)
                self._status(f"⏳ 识别中... {self._completed_tasks}/{self._pending_tasks} ({pct}%)")

            if not success:
                return

            # 存储预处理效果图
            if processed_image is not None and image_path:
                self._processed_images[image_path] = processed_image

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
            self._save_history()

            # 更新切换按钮状态
            if image_path and image_path in self._processed_images:
                self.toggle_preprocess_btn.configure(state="normal")
            else:
                self.toggle_preprocess_btn.configure(state="disabled")

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
            header = f"图片来源: {path}\n{'=' * 50}\n\n"
            content = header + (text or "(无识别结果)")
            ResultParser.export_to_file(content, os.path.join(out_dir, fname))
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
            self._save_history()  # 持久化空状态，防止重启后旧记录复活
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

    def _create_preprocess_panel(self, parent):
        """创建预处理选项面板（嵌入侧边栏卡片）"""
        TEXT = "#1E293B"
        PRIMARY = "#3B82F6"

        self.preprocess_frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10)
        self.preprocess_frame.grid(row=1, column=0, sticky="nsew")
        self.preprocess_frame.columnconfigure(0, weight=1)
        self.preprocess_frame.rowconfigure(0, weight=0)
        self.preprocess_frame.rowconfigure(1, weight=1)

        # 标题 + 快捷按钮
        pp_header = ctk.CTkFrame(self.preprocess_frame, fg_color="transparent")
        pp_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        ctk.CTkLabel(pp_header, text="🔧 预处理选项",
                     font=("微软雅黑", 14, "bold"), text_color=TEXT
                     ).pack(side="left")

        self.preprocess_all_btn = ctk.CTkButton(
            pp_header, text="全选", width=50, height=24,
            font=("微软雅黑", 11), text_color=TEXT, fg_color="#DBEAFE",
            hover_color="#BFDBFE", command=self._preprocess_select_all
        )
        self.preprocess_all_btn.pack(side="right", padx=3)

        self.preprocess_none_btn = ctk.CTkButton(
            pp_header, text="全不选", width=50, height=24,
            font=("微软雅黑", 11), text_color=TEXT, fg_color="#FEE2E2",
            hover_color="#FECACA", command=self._preprocess_select_none
        )
        self.preprocess_none_btn.pack(side="right", padx=3)

        # 复选框网格（4列 × 2行）
        self.checkbox_frame = ctk.CTkFrame(self.preprocess_frame, fg_color="transparent")
        self.checkbox_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        for c in range(4):
            self.checkbox_frame.columnconfigure(c, weight=1)

        self.step_vars = {}
        self.step_widgets = {}
        self._updating_steps = False
        for i, (key, label) in enumerate(self.PREPROCESS_STEPS):
            var = tk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                self.checkbox_frame, text=label, variable=var,
                font=("微软雅黑", 12), text_color=TEXT,
                fg_color=PRIMARY, hover_color="#2563EB",
                checkmark_color="white", border_color="#CBD5E1"
            )
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=5, pady=4)
            self.step_vars[key] = var
            self.step_widgets[key] = cb
            var.trace_add('write', lambda *_, k=key: self._on_step_toggled(k))

    def _toggle_preprocess_panel(self):
        """预处理面板已默认展开，此方法保留以兼容旧代码"""
        pass

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

    def _tick_progress(self):
        """10秒计划进度 — 多图按比例分配，提前完成加速冲线，超时卡在份额的95%"""
        if self._progress_tick_id is None:
            return
        if not hasattr(self, '_current_image_start'):
            return

        total = max(self._pending_tasks, 1)
        share = 1.0 / total  # 每张图分得的进度条份额

        if self._completed_tasks >= self._pending_tasks:
            # 全部完成 → 加速冲到 100%
            current = self.progress_bar.get()
            target = min(current + 0.15, 1.0)
            self.progress_bar.set(target)
            pct = int(target * 100)
            self.progress_label.configure(text=f"{pct}%")
            if target >= 1.0:
                self.progress_bar.configure(progress_color="#22C55E")
                self.progress_label.configure(text_color="#22C55E")
                self.progress_bar.set(1.0)
                self.progress_label.configure(text="100%")
                self._progress_tick_id = None
                self.root.after(1500, self.progress_frame.pack_forget)
                return
            self._progress_tick_id = self.root.after(50, self._tick_progress)
            return

        # 当前图片进度（10秒计划，上限 95%）
        elapsed = time.time() - self._current_image_start
        image_progress = min(elapsed / 10.0, 0.95) * share

        # 总进度 = 已完成图片的份额 + 当前图片的进度
        target = self._completed_tasks * share + image_progress
        target = min(target, 1.0)

        self.progress_bar.set(target)
        pct = int(target * 100)
        self.progress_label.configure(text=f"{pct}%")
        self._progress_tick_id = self.root.after(100, self._tick_progress)

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
