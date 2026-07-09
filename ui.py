# ui.py
import fileIO
import tkinter as tk

root = tk.Tk()
text_box = tk.Text(root)
text_box.pack()

def update_ui():
    content = fileIO.get_ocr_text()
    if content is not None:
        text_box.delete(1.0, tk.END)
        text_box.insert(tk.END, content)
    root.after(100, update_ui)

update_ui()
root.mainloop()