# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 — 文件夹模式
用法: pyinstaller app.spec --noconfirm
输出: dist/OCR文字识别工具/
"""
import sys
import os
from pathlib import Path

project_root = Path('.').absolute()

# ── 收集 PaddlePaddle 的 C++ 库文件 ──
paddle_binaries = []
try:
    import paddle
    paddle_dir = Path(paddle.__file__).parent
    # Paddle 的 DLL 通常在 libs/ 目录
    libs_dir = paddle_dir / 'libs'
    if libs_dir.exists():
        for dll in libs_dir.glob('*.dll'):
            paddle_binaries.append((str(dll), '.'))
    # 也检查根目录
    for dll in paddle_dir.glob('*.dll'):
        paddle_binaries.append((str(dll), '.'))
except ImportError:
    pass  # 打包机器上没装 paddle 则跳过

# ── 收集 tkinterdnd2 的 tkdnd 库 ──
tkdnd_binaries = []
try:
    import tkinterdnd2
    tkdnd_dir = Path(tkinterdnd2.__file__).parent / 'tkdnd'
    if tkdnd_dir.exists():
        for f in tkdnd_dir.iterdir():
            tkdnd_binaries.append((str(f), str(Path('tkinterdnd2') / 'tkdnd')))
except ImportError:
    pass

a = Analysis(
    ['src/main.py'],
    pathex=[str(project_root), str(project_root / 'src')],
    binaries=paddle_binaries + tkdnd_binaries,
    datas=[
        # 资源文件
        ('src/assets/drop_hint.png', 'assets'),
        ('src/assets/favicon.ico', 'assets'),
    ],
    hiddenimports=[
        # GUI
        'tkinter', 'tkinterdnd2', 'customtkinter',
        # OCR 引擎
        'paddleocr', 'paddle', 'paddle.fluid', 'paddle.tensor',
        # 图像处理
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageFilter',
        'numpy',
        'skimage', 'skimage.exposure',
        # 标准库（有些可能被 tree-shaking 误删）
        'queue', 'threading', 'json', 'uuid', 'tempfile', 're',
        'os', 'sys', 'time', 'traceback', 'dataclasses',
        # 项目模块
        'ocr_engine', 'ui', 'image_utils', 'region_selector',
        'history_manager', 'result_parser',
        'algorithms', 'algorithms.grayscale', 'algorithms.binarize',
        'algorithms.filter', 'algorithms.deskew', 'algorithms.resize',
        'algorithms.USM', 'algorithms.gamma', 'algorithms.clahe',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy', 'pandas',
        'jupyter', 'IPython', 'notebook',
        'tkinter.test', 'unittest', 'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OCR_text_recognition',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 不显示命令行窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/assets/favicon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OCR_text_recognition',
)
