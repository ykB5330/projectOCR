def parse_ocr_result(ocr_data):
    if not ocr_data or not ocr_data[0]:
        return"未识别到文字"
    text_lines=[]
    for line in ocr_data:
        for word_info in line:
            text=word_info[1][0]
            confidence=word_info[1][1]
            if confidence>0.5:
                text_lines.append(text)
    return"\n".join(text_lines)
def format_for_export(text):
    from datetime import datetime
    return f"识别时间：{datetime.now()}\n{text}"




