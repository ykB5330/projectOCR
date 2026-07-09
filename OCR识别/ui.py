import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from tkinterdnd2 import TkinterDnD, DND_FILES

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

mwindow = TkinterDnD.Tk()
mwindow.title("文字识别工具")


def close():
    jud = messagebox.askokcancel("退出","是否退出程序")
    if jud == True:
        mwindow.destroy()


#主界面基本设置
mwindow.columnconfigure(0, weight=0)
mwindow.columnconfigure(1, weight=0, minsize=20)
mwindow.columnconfigure(2, weight=1)
mwindow.columnconfigure(3, weight=1)
mwindow.columnconfigure(4, weight=0)
mwindow.rowconfigure(0, weight=0)
mwindow.rowconfigure(1, weight=0, minsize=10)
mwindow.rowconfigure(2, weight=1)
mwindow.rowconfigure(3, weight=0)
mwindow.rowconfigure(4, weight=0)
ctk.CTkLabel(mwindow,text="图片识别",font=("微软雅黑",20),text_color="black",fg_color="#F7FEFE").grid(row=0,column=0, sticky="nw",padx=(10, 0),pady=(10, 0))
mwindow.geometry("1000x800")
mwindow.resizable(True,True)
mwindow.iconbitmap(r"favicon.ico")
mwindow.configure(bg="#F7FEFE")
mwindow.attributes("-alpha",1)
mwindow.attributes("-topmost",False)


#画布

#canvas_in = ctk.CTkCanvas(mwindow,width=550,height=650,bg="#C1EBEB")
#canvas_in.grid(row=1,column=2,sticky="nsew",padx=(10, 0),pady=(10, 0))

#canvas_out = ctk.CTkCanvas(mwindow,width=550,height=650,bg="#F7FEFE")
#canvas_out.grid(row=1,column=3,sticky="nsew",padx=(10, 0),pady=(10, 0))

frame_in = ctk.CTkFrame(mwindow, fg_color="transparent")
frame_in.grid(row=1, column=2, sticky="nsew", padx=(10, 0), pady=(10, 0))
frame_in.columnconfigure(0, weight=1)
frame_in.rowconfigure(1, weight=1)
frame_out = ctk.CTkFrame(mwindow, fg_color="transparent")
frame_out.grid(row=1, column=3, sticky="nsew", padx=(10, 0), pady=(10, 0))
frame_out.columnconfigure(0, weight=1)
frame_out.rowconfigure(1, weight=1)


# 清除按钮

def clear_canvas():
    global label1, label2, label3, icon_img_tk
    canvas_in.delete("all")
    icon = Image.open(r"OCR识别\1984981.png").resize((80, 80), Image.Resampling.LANCZOS).convert("RGBA")
    bg = Image.new("RGBA", icon.size, (193, 235, 235, 255))
    icon_img_tk = ImageTk.PhotoImage(Image.alpha_composite(bg, icon))
    canvas_in.create_image(canvas_in.winfo_width()/2, 160, image=icon_img_tk, anchor="center", tags="icon")
    canvas_in.image = icon_img_tk
    if label1: label1.place(relx=0.5, rely=0.55, anchor="center")
    if label2: label2.place(relx=0.5, rely=0.66, anchor="center")
    if label3: label3.place(relx=0.5, rely=0.77, anchor="center")
    drag_leave(None)
    label.configure(text="未选择图片文件")
clear_bt = ctk.CTkButton(frame_in, text="清除", width=60, height=30,font=("微软雅黑",15), text_color="black", fg_color="#5EDEDE", command=clear_canvas)
clear_bt.grid(row=0, column=0, sticky="ne", padx=5, pady=5)

canvas_in = ctk.CTkCanvas(frame_in, width=550, height=650, bg="#C1EBEB")
canvas_in.grid(row=1, column=0, sticky="nsew")


#开始识别按钮
recognize_bt = ctk.CTkButton(mwindow,text="开始识别",command = "",width=15,font=("微软雅黑",20),text_color="black",fg_color="#91A5E0")
recognize_bt.grid(row=2,column=3,sticky="w",padx=(10, 0),pady=(10, 0))
def start_recognize():
    if not file_list: 
        messagebox.showwarning("提示", "请先导入图片")
        return
    path = file_list[-1]
    #接入OCR
    display_ocr_result(text)

recognize_bt.configure(command=start_recognize) 

#复制按钮

def copy_canvas_text():
    texts = []
    for item in canvas_out.find_all():
        if canvas_out.type(item) == "text":
            texts.append(canvas_out.itemcget(item, "text"))
    content = "\n".join(texts)
    if content.strip():
        mwindow.clipboard_clear()
        mwindow.clipboard_append(content)
        messagebox.showinfo("提示", "文字已复制到剪贴板")
    else:
        messagebox.showwarning("提示", "暂无文字可复制")
copy_btn = ctk.CTkButton(frame_out, text="复制", width=60,height=30,font=("微软雅黑", 15), text_color="black",fg_color="#5EDEDE", command=copy_canvas_text)
copy_btn.grid(row=0, column=0, sticky="ne", padx=5, pady=5)
canvas_out = ctk.CTkCanvas(frame_out, width=550, height=650, bg="#F7FEFE")
canvas_out.grid(row=1, column=0, sticky="nsew")


#导入图片区域
label1 = None
label2 = None
label3 = None

def drag_into (event):
    canvas_in.configure(bg="#9AEF84")

def drag_leave (event):
    canvas_in.configure(bg="#C1EBEB")

def drop (event):
    global canvas_in,label1,label2,label3
    files = mwindow.tk.splitlist(event.data)
    files_path = files[0]
    files_name = os.path.basename(files_path)
    files_extension = os.path.splitext(files_name)[1]
    if files_extension.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
        print("拖入的文件路径:", files_path)
        img = Image.open(files_path)
        img = img.resize((550, 450), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        canvas_in.delete("all")
        canvas_in.create_image(canvas_in.winfo_width()/2, canvas_in.winfo_height()/2, anchor="center", image=photo)
        canvas_in.image = photo
        label.configure(text=f"已选择文件: {files_path}")
        if label1:
            label1.place_forget()
        if label2:
            label2.place_forget()
        if label3:
            label3.place_forget()
        add_file_to_list(files_path)



def creat_area(mwindow):
    global label1, label2, label3, icon_img_tk
    icon = Image.open(r"OCR识别\1984981.png").resize((80, 80), Image.Resampling.LANCZOS).convert("RGBA")
    bg = Image.new("RGBA", icon.size, (193, 235, 235, 255))
    icon_img_tk = ImageTk.PhotoImage(Image.alpha_composite(bg, icon))
    canvas_in.create_image(275, 160, image=icon_img_tk, anchor="center", tags="icon")
    canvas_in.image = icon_img_tk
    def keep_on_vertical_center(event):
        canvas_in.coords("icon", event.width / 2, 160)
    canvas_in.bind("<Configure>", keep_on_vertical_center)
    label1 = ctk.CTkLabel(canvas_in,text="拖入图片文件",font=("微软雅黑",20),text_color="black",fg_color="transparent")
    label1.place(relx=0.5, rely=0.55, anchor="center")
    label2 = ctk.CTkLabel(canvas_in,text="支持格式：jpg、jpeg、png、bmp、gif",font=("微软雅黑",15),text_color="black",fg_color="transparent")
    label2.place(relx=0.5, rely=0.66, anchor="center")
    label3 = ctk.CTkLabel(canvas_in,text="或点击“导入图片”按钮选择文件",font=("微软雅黑",15),text_color="black",fg_color="transparent")
    label3.place(relx=0.5, rely=0.77, anchor="center")
    canvas_in.drop_target_register(DND_FILES)
    canvas_in.dnd_bind('<<DropEnter>>', drag_into)
    canvas_in.dnd_bind('<<DropLeave>>', drag_leave)
    canvas_in.dnd_bind('<<Drop>>', drop)

creat_area(mwindow)




#导入图片按钮

def Import_file():
    file_path = filedialog.askopenfilename(title="选择图片文件",filetypes=[("自定义文件", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")])
    if file_path:
        print("选择的文件路径:", file_path)
        img = Image.open(file_path)
        img = img.resize((550, 450), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        canvas_in.delete("all")
        canvas_in.create_image(canvas_in.winfo_width()/2, canvas_in.winfo_height()/2, anchor="center",image=photo)
        canvas_in.image = photo
        if label1:
            label1.place_forget()
        if label2:
            label2.place_forget()
        if label3:
            label3.place_forget()
        #功能待完善
        label.configure(text=f"已选择文件: {file_path}")
        add_file_to_list(file_path)
    else:
        print("未选择文件")

button = ctk.CTkButton(mwindow,text="导入图片",command = Import_file,width=15,font=("微软雅黑",20),text_color="black",fg_color="#91A5E0")
button.grid(row=2,column=2,sticky="w",padx=(10, 0),pady=(10, 0))
label = ctk.CTkLabel(mwindow,text="未选择图片文件",width=15,font=("微软雅黑",15),text_color="black",fg_color="#F7FEFE")
label.grid(row=0,column=3)

#左侧目录
def add_file_to_list(path):
    if path not in file_list:
        file_list.append(path)
        listbox.insert(tk.END, os.path.basename(path))
file_list = []
current_photo = None
left_frame = ctk.CTkFrame(mwindow, fg_color="transparent")
left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
left_frame.rowconfigure(0, weight=1)
left_frame.columnconfigure(0, weight=1)

listbox = tk.Listbox(left_frame, bg="#F7FEFE", fg="black", font=("微软雅黑", 12))
listbox.grid(row=0, column=0, sticky="nsew")
listbox.bind('<<ListboxSelect>>', lambda e: on_select_listbox(e))

def on_select_listbox(event):
    global current_photo, label1, label2, label3
    sel = listbox.curselection()
    if not sel:
        return
    path = file_list[sel[0]]
    img = Image.open(path).resize((550, 450), Image.Resampling.LANCZOS)
    current_photo = ImageTk.PhotoImage(img)
    canvas_in.delete("all")
    canvas_in.create_image(canvas_in.winfo_width()/2,canvas_in.winfo_height()/2,anchor="center",image=current_photo)
    canvas_in.image = current_photo
    label.configure(text=f"已选择文件: {path}")
    for lbl in (label1, label2, label3):
        if lbl: lbl.place_forget()
    canvas_out.delete("all")
    canvas_out.create_text(canvas_out.winfo_width()/2, 20, anchor="n",text="（等待识别）", fill="gray", font=("微软雅黑", 12))

def display_ocr_result(text):
    canvas_out.delete("all")
    y = 20
    for line in text.split('\n'):
        canvas_out.create_text(10, y, anchor="nw", text=line,fill="black",font=("微软雅黑", 14),tags="result")
        y += 25






mwindow.protocol("WM_DELETE_WINDOW", close)
mwindow.mainloop()
