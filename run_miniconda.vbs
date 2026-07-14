Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' 脚本所在目录作为工作目录
WshShell.CurrentDirectory = FSO.GetParentFolderName(WScript.ScriptFullName)

' 使用 %USERPROFILE% 动态获取用户目录，避免硬编码
condaPath = WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\miniconda3\Scripts\conda.exe"
cmd = """" & condaPath & """ run -n paddleocr pythonw src\main.py"

WshShell.Run cmd, 0, False
