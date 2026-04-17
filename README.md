# LocalVidRen - 本地短视频智能重命名系统

## 简介

LocalVidRen 是一个 Windows 专属的本地短视频桌面应用程序，通过 AI 模型分析 + 语音识别技术，快速生成短视频内容总结，并自动将总结作为视频的新文件名。

### 核心特性
- **100% 本地隐私**：数据完全不出电脑（本地模式）
- **秒级分析**：针对 500M 以内短视频优化
- **自动化处理**：文件夹监控 + 无人值守运行
- **灵活模型选择**：支持本地模型和在线 API

## 系统要求

- **操作系统**：Windows 10/11 (64 位)
- **Python**：3.11+
- **内存**：4GB+
- **硬盘空间**：2GB+（用于模型文件）

## 快速开始

### 方法一：使用安装包（推荐）

1. 下载并运行 `LocalVidRen_Setup.exe`
2. 按照安装向导完成安装
3. 安装完成后，桌面会出现快捷方式
4. 双击快捷方式启动程序

### 方法二：手动安装

1. **安装 Python 3.11+**
   - 下载地址：https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **安装依赖**
   ```bash
   cd LocalVidRen
   pip install -r requirements.txt
   ```

3. **启动程序**
   ```bash
   # 方式一：使用启动脚本
   LocalVidRen.bat
   
   # 方式二：直接运行
   python src/main.py
   ```

## 模型配置

### 本地模式（推荐）

1. **下载推荐模型**：
   - 语音模型：faster-whisper-base（自动下载）
   - 视觉模型：Qwen2-VL-2B-Instruct-q4_k_m.gguf

2. **配置模型路径**：
   - 打开设置 → 模型配置
   - 选择"本地 GGUF 模型"
   - 点击"浏览"选择下载的 GGUF 文件

### API 模式

1. 打开设置 → 模型配置
2. 选择"OpenAI 兼容 API"
3. 输入 API 密钥和基础 URL
4. 输入模型名称（如 gpt-4v）

## 功能说明

### 1. 视频扫描
- 点击"选择文件夹"按钮
- 选择包含短视频的文件夹
- 程序会自动过滤大于 500M 的文件

### 2. 视频处理
- 点击"开始处理"按钮
- 程序会分析每个视频并生成新文件名
- 处理完成后自动重命名

### 3. 文件夹监控
- 打开设置 → 文件夹监控
- 添加需要监控的文件夹
- 新增视频会自动加入处理队列

### 4. 撤销重命名
- 如果重命名结果不满意
- 程序保留最近 50 条历史记录
- 可在设置中配置撤销功能

## 常见问题

### Q: 程序启动失败？
A: 请检查 Python 版本是否为 3.11+，并确认所有依赖已安装。

### Q: 视频处理速度很慢？
A: 请尝试以下优化：
- 使用 CUDA 加速（需要 NVIDIA 显卡）
- 选择更小的模型（如 tiny 代替 base）
- 减少并发处理数

### Q: 语音识别不准确？
A: 可以尝试：
- 使用更大的模型（small 或 medium）
- 确保视频音频质量良好
- 检查视频是否有背景音乐干扰

### Q: 如何添加自定义模型？
A: 请参考 `MODEL_INTERFACE.md` 文档

## 文件说明

```
LocalVidRen/
├── src/                    # 源代码
│   ├── main.py            # 程序入口
│   ├── main_window.py     # 主窗口
│   ├── settings_dialog.py # 设置对话框
│   ├── ai_models.py       # AI 模型接口
│   ├── video_processor.py # 视频处理
│   └── config.py          # 配置管理
├── config/                 # 配置文件
│   └── config.yaml        # 主配置文件
├── models/                 # 模型文件目录
├── logs/                   # 日志目录
├── requirements.txt        # Python 依赖
├── LocalVidRen.bat         # 启动脚本
└── README.md              # 本文档
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
