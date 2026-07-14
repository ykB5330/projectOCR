Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' 脚本所在目录作为工作目录
WshShell.CurrentDirectory = FSO.GetParentFolderName(WScript.ScriptFullName)

' 使用系统默认环境的 pythonw（无终端窗口）
WshShell.Run "pythonw src\main.py", 0, False
