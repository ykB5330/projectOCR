@echo off
chcp 65001 >nul
title OCR文字识别工具 — 一键打包

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   OCR文字识别工具 — 一键打包脚本    ║
echo  ╚══════════════════════════════════════╝
echo.
echo  [1/3] 安装依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo  [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo  [2/3] 安装 PyInstaller...
pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo  [错误] PyInstaller 安装失败
    pause
    exit /b 1
)

echo  [3/3] 开始打包（预计 5-15 分钟，请耐心等待）...
pyinstaller app.spec --noconfirm
if %errorlevel% neq 0 (
    echo.
    echo  [错误] 打包失败，请检查上方错误信息
    pause
    exit /b 1
)

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   ✅ 打包完成！                      ║
echo  ║                                      ║
echo  ║   输出目录: dist\OCR文字识别工具\     ║
echo  ║   启动文件: OCR文字识别工具.exe       ║
echo  ╚══════════════════════════════════════╝
echo.
echo  将整个 "dist\OCR文字识别工具" 文件夹复制给别人即可使用
echo  无需安装 Python 或任何依赖
echo.

start "" "dist\OCR文字识别工具"
pause
