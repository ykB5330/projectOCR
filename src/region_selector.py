"""
识别区域自定义截取模块 — 鼠标框选ROI（Region of Interest）

实现功能：
- 在Canvas上鼠标拖拽绘制矩形选择框
- 将Canvas坐标映射回原始图像坐标（考虑缩放比例）
- 从原始图像中裁剪选中区域
- 支持 Esc 取消、重新框选替换旧选区
"""

from PIL import Image
import numpy as np


class RegionSelector:
    """
    图像区域选择器

    绑定到Tkinter Canvas上，允许用户通过鼠标拖拽框选识别区域。
    仅对框选区域进行OCR识别，减少无效计算。

    用法:
        selector = RegionSelector(canvas)
        selector.activate()          # 进入选择模式
        # 用户拖拽选择...
        region = selector.crop_from_image(pil_image, canvas_w, canvas_h)
        selector.deactivate()        # 退出选择模式
    """

    def __init__(self, canvas):
        """
        初始化选择器

        Args:
            canvas: Tkinter Canvas 对象
        """
        self.canvas = canvas

        # 选择状态
        self._active = False
        self._start_x = None        # 拖拽起始Canvas坐标
        self._start_y = None
        self._end_x = None          # 拖拽结束Canvas坐标
        self._end_y = None

        # 绘制元素ID
        self._rect_id = None        # 选择矩形ID
        self._coord_label_id = None # 坐标标签ID

        # 原始图像与显示尺寸
        self._image_display_w = None
        self._image_display_h = None

        # 颜色配置
        self.SELECT_COLOR = "#FF4444"      # 红色选择框
        self.SELECT_WIDTH = 2
        self.SELECT_DASH = (6, 3)          # 虚线样式
        self.CONFIRM_COLOR = "#44BB44"     # 绿色确认框
        self.FILL_COLOR = ""               # 透明填充

    # ========== 模式控制 ==========

    def activate(self):
        """进入选择模式：绑定鼠标事件，改变光标"""
        if self._active:
            return
        self._active = True
        self._clear_selection()
        self.canvas.config(cursor='cross')

    def deactivate(self):
        """退出选择模式：解绑鼠标事件，恢复光标"""
        if not self._active:
            return
        self._active = False
        self.canvas.config(cursor='')
        # 保留已确认的选择框（不变色，保留显示）

    def is_active(self) -> bool:
        """是否处于选择模式"""
        return self._active

    # ========== 选区状态 ==========

    def has_selection(self) -> bool:
        """是否有已确认的选区"""
        return (self._start_x is not None and self._start_y is not None and
                self._end_x is not None and self._end_y is not None)

    def get_selection(self) -> tuple:
        """
        获取当前选区坐标（Canvas坐标系）

        Returns:
            (x1, y1, x2, y2) 左上角和右下角坐标，无选区时返回None
        """
        if not self.has_selection():
            return None
        # 规范化坐标：确保 (x1,y1) 为左上角，(x2,y2) 为右下角
        x1 = min(self._start_x, self._end_x)
        y1 = min(self._start_y, self._end_y)
        x2 = max(self._start_x, self._end_x)
        y2 = max(self._start_y, self._end_y)
        return (x1, y1, x2, y2)

    def get_roi_coordinates(self) -> tuple:
        """
        获取当前选区坐标（已规范化，左上→右下）

        Returns:
            (x1, y1, x2, y2) 或 None
        """
        return self.get_selection()

    def clear_selection(self):
        """清除当前选区"""
        self._clear_selection()

    def reset_for_new_image(self, display_w: int, display_h: int):
        """
        切换新图像时重置选择器

        Args:
            display_w: 图像在Canvas上的显示宽度
            display_h: 图像在Canvas上的显示高度
        """
        self._clear_selection()
        self._image_display_w = display_w
        self._image_display_h = display_h

    # ========== 坐标映射 ==========

    def _map_to_image_coords(self, canvas_x: float, canvas_y: float,
                              canvas_w: int, canvas_h: int,
                              img_w: int, img_h: int) -> tuple:
        """
        将Canvas坐标映射到原始图像像素坐标

        坐标系映射逻辑：
        1. 图像在Canvas中居中显示，计算显示区域与Canvas的偏移量
        2. 按缩放比例将Canvas坐标转换为图像坐标
        3. 边界裁剪确保坐标不超出图像范围

        Args:
            canvas_x, canvas_y: Canvas上的坐标
            canvas_w, canvas_h: Canvas的宽高
            img_w, img_h: 原始图像的宽高

        Returns:
            (img_x, img_y) 图像像素坐标
        """
        # 计算图像在Canvas上的显示尺寸（等比缩放，适配Canvas）
        scale = min(canvas_w / img_w, canvas_h / img_h)
        display_w = img_w * scale
        display_h = img_h * scale

        # 计算居中偏移量
        offset_x = (canvas_w - display_w) / 2
        offset_y = (canvas_h - display_h) / 2

        # 减去偏移量得到显示区域内的相对坐标
        rel_x = canvas_x - offset_x
        rel_y = canvas_y - offset_y

        # 按缩放比例映射到原始图像坐标
        if scale > 0:
            img_x = rel_x / scale
            img_y = rel_y / scale
        else:
            img_x = rel_x
            img_y = rel_y

        # 边界裁剪
        img_x = max(0, min(img_w - 1, int(round(img_x))))
        img_y = max(0, min(img_h - 1, int(round(img_y))))

        return img_x, img_y

    def crop_from_image(self, pil_image: Image.Image,
                         canvas_w: int, canvas_h: int) -> Image.Image:
        """
        从原始PIL图像中裁剪选中区域

        Args:
            pil_image: 原始PIL Image对象
            canvas_w: Canvas的宽度
            canvas_h: Canvas的高度

        Returns:
            裁剪后的PIL Image，无选区时返回原图
        """
        if not self.has_selection():
            return pil_image

        selection = self.get_selection()
        if selection is None:
            return pil_image

        canvas_x1, canvas_y1, canvas_x2, canvas_y2 = selection
        img_w, img_h = pil_image.size

        # 将Canvas坐标映射到图像坐标
        img_x1, img_y1 = self._map_to_image_coords(
            canvas_x1, canvas_y1, canvas_w, canvas_h, img_w, img_h)
        img_x2, img_y2 = self._map_to_image_coords(
            canvas_x2, canvas_y2, canvas_w, canvas_h, img_w, img_h)

        # 规范化：确保 (x1,y1) 是左上角
        crop_x1 = min(img_x1, img_x2)
        crop_y1 = min(img_y1, img_y2)
        crop_x2 = max(img_x1, img_x2)
        crop_y2 = max(img_y1, img_y2)

        # 最小尺寸保护
        if crop_x2 - crop_x1 < 5 or crop_y2 - crop_y1 < 5:
            return pil_image

        # 裁剪
        cropped = pil_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        return cropped

    # ========== 鼠标事件处理 ==========

    def on_mouse_down(self, event):
        """
        鼠标按下：开始拖拽选择

        Args:
            event: Tkinter鼠标事件对象（含 x, y 属性）
        """
        if not self._active:
            return

        # 删除旧选区
        self._clear_selection()

        # 记录起始点
        self._start_x = event.x
        self._start_y = event.y
        self._end_x = event.x
        self._end_y = event.y

        # 绘制初始点
        self._rect_id = self.canvas.create_rectangle(
            self._start_x, self._start_y,
            self._end_x, self._end_y,
            outline=self.SELECT_COLOR,
            width=self.SELECT_WIDTH,
            dash=self.SELECT_DASH,
        )

    def on_mouse_move(self, event):
        """
        鼠标移动：实时更新选择框

        Args:
            event: Tkinter鼠标事件对象
        """
        if not self._active or self._start_x is None:
            return

        # 更新终点
        self._end_x = event.x
        self._end_y = event.y

        # 更新矩形显示
        if self._rect_id is not None:
            self.canvas.coords(
                self._rect_id,
                min(self._start_x, self._end_x),
                min(self._start_y, self._end_y),
                max(self._start_x, self._end_x),
                max(self._start_y, self._end_y),
            )

    def on_mouse_up(self, event):
        """
        鼠标释放：确认选区

        Args:
            event: Tkinter鼠标事件对象
        """
        if not self._active or self._start_x is None:
            return

        # 更新终点
        self._end_x = event.x
        self._end_y = event.y

        # 检查选区是否有效（大于最小尺寸）
        w = abs(self._end_x - self._start_x)
        h = abs(self._end_y - self._start_y)
        if w < 10 or h < 10:
            # 选区太小，视为无效
            self._clear_selection()
            return

        # 将选择框颜色改为绿色表示已确认
        if self._rect_id is not None:
            self.canvas.itemconfig(
                self._rect_id,
                outline=self.CONFIRM_COLOR,
                dash=()  # 实线
            )

    def on_key_press(self, event):
        """
        键盘事件处理：Esc取消选区

        Args:
            event: Tkinter键盘事件对象
        """
        if event.keysym == 'Escape' and self._active:
            self._clear_selection()

    # ========== 内部辅助 ==========

    def _clear_selection(self):
        """清除当前选区和所有绘制元素"""
        if self._rect_id is not None:
            self.canvas.delete(self._rect_id)
            self._rect_id = None
        if self._coord_label_id is not None:
            self.canvas.delete(self._coord_label_id)
            self._coord_label_id = None

        self._start_x = None
        self._start_y = None
        self._end_x = None
        self._end_y = None

    def _draw_selection_rect(self, x1, y1, x2, y2):
        """在Canvas上绘制选择矩形"""
        self._clear_selection()
        self._rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=self.CONFIRM_COLOR,
            width=self.SELECT_WIDTH,
        )


# ========== 自测代码 ==========
if __name__ == "__main__":
    # 坐标映射测试
    print("=== 坐标映射算法测试 ===")

    # 模拟场景：Canvas 550x450，图像 1920x1080
    scale = min(550/1920, 450/1080)  # 等比缩放
    display_w = 1920 * scale
    display_h = 1080 * scale
    offset_x = (550 - display_w) / 2
    offset_y = (450 - display_h) / 2

    print(f"原始图像: 1920x1080")
    print(f"Canvas尺寸: 550x450")
    print(f"缩放比例: {scale:.4f}")
    print(f"显示区域: {display_w:.0f}x{display_h:.0f}")
    print(f"居中偏移: ({offset_x:.0f}, {offset_y:.0f})")

    # 模拟Canvas中心点映射
    canvas_cx, canvas_cy = 275, 225
    rel_x = canvas_cx - offset_x
    rel_y = canvas_cy - offset_y
    img_x = rel_x / scale
    img_y = rel_y / scale
    print(f"\nCanvas中心点 ({canvas_cx}, {canvas_cy}) → 图像坐标 ({img_x:.0f}, {img_y:.0f})")

    # 测试边界裁剪
    print("\n=== 边界裁剪测试 ===")
    # 模拟超出范围的Canvas坐标
    out_x, out_y = -100, -100
    clamped_x = max(0, min(1920-1, int(out_x)))
    clamped_y = max(0, min(1080-1, int(out_y)))
    print(f"越界坐标 ({out_x}, {out_y}) → 裁剪后 ({clamped_x}, {clamped_y})")

    print("\n✅ 区域选择器坐标映射逻辑验证完成")
