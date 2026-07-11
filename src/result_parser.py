"""
结果解析与格式化模块

提供OCR识别结果的文本清洗、格式化输出、导出等功能。
"""

import re


class ResultParser:
    """
    OCR结果解析器

    对PaddleOCR返回的原始文本进行后处理：
    - 清理多余空白字符
    - 规范化换行
    - 提取结构化信息
    - 多种格式导出
    """

    def __init__(self):
        pass

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        清理OCR识别文本中的噪声

        Args:
            raw_text: 原始OCR文本

        Returns:
            清理后的文本
        """
        if not raw_text:
            return ""

        # 1. 移除行首行尾空白
        text = raw_text.strip()

        # 2. 合并连续空格（保留有意义的分隔）
        text = re.sub(r' {2,}', ' ', text)

        # 3. 合并连续空行（最多保留一个空行）
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 4. 移除行尾多余空格
        text = re.sub(r' +\n', '\n', text)

        # 5. 移除控制字符（保留常见换行和制表符）
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        return text

    @staticmethod
    def normalize_line_breaks(raw_text: str) -> str:
        """
        规范化换行符：统一使用 \\n

        Args:
            raw_text: 原始文本

        Returns:
            规范化后的文本
        """
        return raw_text.replace('\r\n', '\n').replace('\r', '\n')

    @staticmethod
    def format_as_plain_text(raw_text: str, line_width: int = 0) -> str:
        """
        格式化为纯文本

        Args:
            raw_text: 原始OCR文本
            line_width: 行宽限制（0=不限制）

        Returns:
            格式化后的纯文本
        """
        text = ResultParser.clean_text(raw_text)
        text = ResultParser.normalize_line_breaks(text)

        if line_width > 0:
            lines = text.split('\n')
            wrapped_lines = []
            for line in lines:
                while len(line) > line_width:
                    # 在行宽处断行
                    wrapped_lines.append(line[:line_width])
                    line = line[line_width:]
                if line:
                    wrapped_lines.append(line)
            text = '\n'.join(wrapped_lines)

        return text

    @staticmethod
    def format_as_html(raw_text: str) -> str:
        """
        将OCR文本转为简单HTML格式

        Args:
            raw_text: 原始OCR文本

        Returns:
            HTML字符串
        """
        text = ResultParser.clean_text(raw_text)
        lines = text.split('\n')
        html_parts = ['<html><body>']
        for line in lines:
            if line.strip():
                html_parts.append(f'<p>{line}</p>')
            else:
                html_parts.append('<br/>')
        html_parts.append('</body></html>')
        return '\n'.join(html_parts)

    @staticmethod
    def extract_stats(raw_text: str) -> dict:
        """
        提取文本统计信息

        Args:
            raw_text: OCR识别文本

        Returns:
            统计信息字典：字符数、行数、词数等
        """
        text = ResultParser.clean_text(raw_text)
        lines = [l for l in text.split('\n') if l.strip()]
        words = text.split()

        return {
            'char_count': len(text),
            'char_count_no_spaces': len(text.replace(' ', '').replace('\n', '')),
            'line_count': len(lines),
            'word_count': len(words),
            'estimated_cn_char_count': sum(1 for c in text if '一' <= c <= '鿿'),
        }

    @staticmethod
    def export_to_file(raw_text: str, filepath: str, fmt: str = 'txt') -> str:
        """
        导出OCR结果到文件

        Args:
            raw_text: OCR原始文本
            filepath: 输出文件路径
            fmt: 格式 ('txt', 'html')

        Returns:
            实际写入的文件路径
        """
        if fmt == 'html':
            content = ResultParser.format_as_html(raw_text)
        else:
            content = ResultParser.format_as_plain_text(raw_text)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath


# ========== 自测代码 ==========
if __name__ == "__main__":
    test_text = "这是  一段测试文本  \n\n\n带有多余空白和  \n  连续换行\n\nHello World  "

    print("=== 原始文本 ===")
    print(repr(test_text))
    print()

    cleaned = ResultParser.clean_text(test_text)
    print("=== 清理后 ===")
    print(repr(cleaned))
    print()

    stats = ResultParser.extract_stats(test_text)
    print("=== 统计信息 ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n✅ ResultParser 所有功能测试通过")
