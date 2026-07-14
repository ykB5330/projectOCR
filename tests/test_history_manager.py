"""BST历史记录管理器测试"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from history_manager import HistoryRecord, BSTree, HistoryManager


def test_insert_and_size():
    tree = BSTree()
    t = time.time()
    tree.insert(t, HistoryRecord("1", "/a.png", "a", t, 100))
    tree.insert(t + 1, HistoryRecord("2", "/b.png", "b", t + 1, 200))
    assert tree.size() == 2


def test_inorder_sorted():
    tree = BSTree()
    t = time.time()
    tree.insert(t + 2, HistoryRecord("3", "/c.png", "c", t + 2, 300))
    tree.insert(t,     HistoryRecord("1", "/a.png", "a", t, 100))
    tree.insert(t + 1, HistoryRecord("2", "/b.png", "b", t + 1, 200))
    records = tree.inorder_traversal()
    assert [r.record_id for r in records] == ["1", "2", "3"]


def test_reverse_inorder():
    tree = BSTree()
    t = time.time()
    tree.insert(t, HistoryRecord("1", "/a.png", "a", t, 100))
    tree.insert(t + 1, HistoryRecord("2", "/b.png", "b", t + 1, 200))
    assert tree.reverse_inorder()[0].record_id == "2"


def test_search_by_keyword():
    tree = BSTree()
    tree.insert(1, HistoryRecord("1", "/a.png", "Hello World", 1, 100))
    tree.insert(2, HistoryRecord("2", "/b.png", "Python OCR", 2, 200))
    assert len(tree.search_by_keyword("hello")) == 1
    assert len(tree.search_by_keyword("python")) == 1
    assert len(tree.search_by_keyword("不存在")) == 0


def test_delete_and_clear():
    tree = BSTree()
    tree.insert(1, HistoryRecord("1", "/a.png", "a", 1, 100))
    tree.insert(2, HistoryRecord("2", "/b.png", "b", 2, 200))
    assert tree.delete(2) and tree.size() == 1
    tree.clear()
    assert tree.is_empty()


def test_history_manager():
    mgr = HistoryManager()
    mgr.add_record("/img.png", "识别文本", file_size=1024)
    assert mgr.get_record_count() == 1
    mgr.add_record("/img2.png", "Python 文本", file_size=2048)
    assert mgr.get_record_count() == 2
    assert len(mgr.search_by_keyword("Python")) == 1
    assert len(mgr.get_all_records()) == 2
    mgr.clear_all()
    assert mgr.get_record_count() == 0


def test_search_by_filename():
    """搜索文件名"""
    tree = BSTree()
    tree.insert(1, HistoryRecord("1", "/home/user/screenshot_2024.png", "some text", 1, 100))
    tree.insert(2, HistoryRecord("2", "/home/user/photo.jpg", "unrelated", 2, 200))
    assert len(tree.search_by_keyword("screenshot")) == 1
    assert tree.search_by_keyword("screenshot")[0].record_id == "1"
    assert len(tree.search_by_keyword("photo")) == 1
    assert len(tree.search_by_keyword("nonexistent")) == 0


def test_search_by_time_string():
    """搜索时间字符串（如 07-14、07-14 15:30）"""
    tree = BSTree()
    # 使用本地时间构造时间戳，确保 strftime 输出与预期一致
    ts = time.mktime((2024, 7, 14, 15, 30, 0, 0, 0, -1))
    tree.insert(ts, HistoryRecord("1", "/a.png", "text", ts, 100))
    time_str = time.strftime('%m-%d %H:%M', time.localtime(ts))
    assert len(tree.search_by_keyword(time_str)) == 1
    assert len(tree.search_by_keyword("07-15")) == 0


def test_json_roundtrip():
    mgr1 = HistoryManager()
    mgr1.add_record("/img.png", "测试", file_size=100)
    path = os.path.join(os.path.dirname(__file__), "test_export.json")
    mgr1.export_to_json(path)
    mgr2 = HistoryManager()
    assert mgr2.import_from_json(path) == 1
    os.remove(path)


if __name__ == "__main__":
    test_insert_and_size(); test_inorder_sorted(); test_reverse_inorder()
    test_search_by_keyword(); test_delete_and_clear()
    test_history_manager(); test_json_roundtrip()
    test_search_by_filename(); test_search_by_time_string()
    print("✅ BST历史记录管理器测试全部通过")
