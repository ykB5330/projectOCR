"""区域选择器坐标映射测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from PIL import Image
from region_selector import RegionSelector


class MockCanvas:
    def __init__(self):
        self.cursor = ''
        self.items = {}
    def config(self, **kw):
        if 'cursor' in kw: self.cursor = kw['cursor']
    def create_rectangle(self, x1, y1, x2, y2, **kw):
        self.items['rect'] = (x1, y1, x2, y2); return 'rect'
    def delete(self, iid): self.items.pop(iid, None)
    def coords(self, iid, x1, y1, x2, y2): self.items[iid] = (x1, y1, x2, y2)
    def itemconfig(self, iid, **kw): pass


class FakeEvent:
    def __init__(self, x, y): self.x = x; self.y = y


def test_activate_deactivate():
    canvas = MockCanvas()
    sel = RegionSelector(canvas)
    assert not sel.is_active()
    sel.activate()
    assert sel.is_active() and canvas.cursor == 'cross'
    sel.deactivate()
    assert not sel.is_active() and canvas.cursor == ''


def test_no_selection_initially():
    sel = RegionSelector(MockCanvas())
    assert not sel.has_selection()


def test_select_and_clear():
    canvas = MockCanvas()
    sel = RegionSelector(canvas)
    sel.activate()
    sel.on_mouse_down(FakeEvent(50, 50))
    sel.on_mouse_move(FakeEvent(150, 150))
    sel.on_mouse_up(FakeEvent(150, 150))
    assert sel.has_selection()
    x1, y1, x2, y2 = sel.get_selection()
    assert (x1, y1, x2, y2) == (50, 50, 150, 150)
    sel.clear_selection()
    assert not sel.has_selection()


def test_tiny_selection_ignored():
    canvas = MockCanvas()
    sel = RegionSelector(canvas)
    sel.activate()
    sel.on_mouse_down(FakeEvent(10, 10))
    sel.on_mouse_up(FakeEvent(12, 12))
    assert not sel.has_selection()


def test_crop_from_image():
    canvas = MockCanvas()
    sel = RegionSelector(canvas)
    sel.activate()
    sel.on_mouse_down(FakeEvent(25, 25))
    sel.on_mouse_up(FakeEvent(75, 75))
    img = Image.new('RGB', (100, 100), color='white')
    cropped = sel.crop_from_image(img, 100, 100)
    assert cropped.size[0] > 0


def test_no_selection_crop_returns_original():
    sel = RegionSelector(MockCanvas())
    img = Image.new('RGB', (50, 50))
    assert sel.crop_from_image(img, 100, 100) is img


if __name__ == "__main__":
    test_activate_deactivate(); test_no_selection_initially()
    test_select_and_clear(); test_tiny_selection_ignored()
    test_crop_from_image(); test_no_selection_crop_returns_original()
    print("✅ 区域选择器测试全部通过")
