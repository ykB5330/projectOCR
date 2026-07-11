"""结果解析器测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from result_parser import ResultParser


def test_clean_strip():
    assert ResultParser.clean_text("  hello  \n") == "hello"


def test_clean_merge_spaces():
    assert ResultParser.clean_text("a    b    c") == "a b c"


def test_clean_merge_newlines():
    assert ResultParser.clean_text("a\n\n\n\nb") == "a\n\nb"


def test_clean_empty():
    assert ResultParser.clean_text("") == ""
    assert ResultParser.clean_text(None) == ""


def test_normalize():
    text = "a\r\nb\rc"
    result = ResultParser.normalize_line_breaks(text)
    assert "\r" not in result


def test_extract_stats():
    stats = ResultParser.extract_stats("Hello 世界\n第二行")
    assert stats['line_count'] == 2
    assert stats['char_count_no_spaces'] > 0


def test_format_plain():
    result = ResultParser.format_as_plain_text("  a  \n\n\n  b  ")
    assert "a" in result and "b" in result


def test_export():
    path = os.path.join(os.path.dirname(__file__), "test_export.txt")
    ResultParser.export_to_file("测试", path)
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        assert "测试" in f.read()
    os.remove(path)


if __name__ == "__main__":
    test_clean_strip(); test_clean_merge_spaces()
    test_clean_merge_newlines(); test_clean_empty()
    test_normalize(); test_extract_stats()
    test_format_plain(); test_export()
    print("✅ 结果解析器测试全部通过")
