import os
import sys

# 确保 src 目录在搜索路径中
sys.path.insert(0, os.path.dirname(__file__))


def main():
    from ocr_engine import OcrEngine
    from ui import OcrUI

    print("=" * 50)
    print("  OCR文字识别工具 v2.0")
    print("=" * 50)

    # 初始化OCR引擎
    try:
        engine = OcrEngine()
    except ImportError as e:
        print(f"\n[错误] 缺少必要依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        # 启动UI但不带引擎（可浏览图片，但无法OCR）
        from ui import OcrUI
        window = OcrUI()
        window._status("⚠️ OCR引擎未加载：请安装依赖后重启")
        window.run()
        return
    except Exception as e:
        print(f"\n[错误] OCR引擎初始化失败: {e}")
        from ui import OcrUI
        window = OcrUI()
        window._status(f"⚠️ OCR引擎初始化失败: {e}")
        window.run()
        return

    window = OcrUI()
    window.set_engine(engine)
    window.run()


if __name__ == "__main__":
    main()


