# OCR Tool — 本地 OCR 文字识别工具

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PaddleOCR](https://img.shields.io/badge/OCR-PaddleOCR-orange)](https://github.com/PaddlePaddle/PaddleOCR)

基于 **PaddleOCR** 的桌面端 OCR 应用，**手动编码实现 8 种图像预处理算法**，支持模糊、倾斜、噪点图片的高精度文字识别。

---

## 功能特性

### 核心算法（手动实现，无 OpenCV 依赖）

| # | 算法 | 说明 |
|---|------|------|
| 1 | 加权灰度化 | 0.299R + 0.587G + 0.114B，逐像素遍历 |
| 2 | 自适应二值化 | 局部邻域均值阈值，去除光影干扰 |
| 3 | 中值滤波去噪 | 自定义卷积核 + 冒泡排序取中值 |
| 4 | Hough 倾斜矫正 | 极坐标投票 + 边缘检测 + 白底旋转 |
| 5 | 图像金字塔缩放 | 2× 块平均下采样 / 最近邻上采样 |
| 6 | 批量任务队列 | 基于 Queue 的 FIFO 多图调度 |
| 7 | 区域框选识别 | Canvas 鼠标拖拽 + 坐标映射裁剪 |
| 8 | BST 历史管理 | 二叉搜索树存储 / 关键词检索 |

### 界面功能

- 🖱️ **拖拽导入** — 支持拖入或浏览选择图片
- ✂️ **框选区域** — 鼠标框选局部识别，减少无效计算
- 📋 **历史记录** — BST 按时间排序，支持关键词实时搜索，关闭后自动持久化
- ⚙️ **预处理开关** — 可展开面板，按需勾选预处理步骤
- 📤 **结果导出** — 识别文本导出为 TXT，历史记录导出为 JSON

---

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/ykB5330/projectOCR.git
cd ocr-tool

# 2. 安装依赖
pip install -r requirements.txt
```

> **注意**：首次运行 PaddleOCR 会自动下载模型文件（约 50MB），请保持网络畅通。

---

## 运行

```bash
python src/main.py
```

---

## 项目结构

```
ocr-tool/
├── src/
│   ├── main.py                  # 入口
│   ├── ui.py                    # GUI 界面（Tkinter + CustomTkinter）
│   ├── ocr_engine.py            # OCR 引擎（PaddleOCR + 任务队列）
│   ├── image_utils.py           # 预处理流水线
│   ├── region_selector.py       # 鼠标框选 ROI
│   ├── history_manager.py       # BST 历史记录管理
│   ├── result_parser.py         # 结果文本清洗与导出
│   ├── algorithms/              # 8 种手动实现的预处理算法
│   │   ├── grayscale.py         #   加权灰度化
│   │   ├── binarize.py          #   自适应二值化
│   │   ├── filter.py            #   中值滤波
│   │   ├── deskew.py            #   Hough 倾斜矫正
│   │   ├── resize.py            #   金字塔缩放
│   │   ├── USM.py               #   USM 锐化
│   │   ├── gamma.py             #   伽马校正
│   │   └── clahe.py             #   CLAHE 增强
│   └── asserts/                 # 图标资源
├── tests/                       # 测试
├── examples/                    # 示例图片
├── history/                     # 历史记录持久化（运行时生成）
├── requirements.txt
└── README.md
```

---

## 预处理流水线

```
输入图片
  │
  ├─ [1] 灰度化         — 加权公式 RGB→Gray
  ├─ [2] 中值滤波       — 3×3 窗口冒泡排序取中值
  ├─ [3] 金字塔下采样    — 2×2 块平均缩小
  ├─ [4] 自适应二值化    — 局部窗口手动求均值阈值
  ├─ [5] Hough 倾斜矫正  — Sobel 边缘检测 → 极坐标投票 → 白底旋转
  ├─ [6] USM 锐化       — 高斯模糊 + 细节增强
  ├─ [7] 伽马校正       — 幂律变换调整亮度
  └─ [8] CLAHE 增强     — 限制对比度直方图均衡化
  │
  ▼
PaddleOCR 推理 → 输出文本
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| GUI | Tkinter + CustomTkinter + tkinterdnd2 |
| OCR | PaddleOCR (PP-OCRv6) |
| 图像处理 | PIL/Pillow + NumPy + scikit-image |
| 数据结构 | Queue（任务调度）+ BST（历史管理） |
| 测试 | pytest |

---

## License

MIT
