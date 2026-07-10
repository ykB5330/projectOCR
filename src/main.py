from ocr_engine import OcrEngine
import os
from ui import OcrUI
def main():
    engine = OcrEngine()
    window=OcrUI()
    window.set_engine(engine)
    window.run()

if __name__ == "__main__":
    main()


