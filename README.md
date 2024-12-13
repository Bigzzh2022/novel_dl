# Novel Downloader

一个基于 Python 的网络小说下载工具，支持多个小说网站的内容爬取和导出。

## 功能特点

- 支持多个小说网站的内容爬取
- 自动生成目录和章节内容
- 支持导出为 TXT 格式
- 支持断点续传
- 自动处理乱码问题
- 支持并发下载，提高下载速度
- 提供图形界面（GUI）操作

## 环境要求

- Python 3.7+
- beautifulsoup4 4.12.2
- requests 2.31.0
- lxml 4.9.3
- EbookLib 0.18

## 安装方法

1. 克隆项目到本地：
```bash
git clone https://github.com/your-username/novel_dl.git
cd novel_dl
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行模式

直接运行 main.py：
```bash
python main.py
```

### 图形界面模式

运行 GUI 程序：
```bash
python -m gui.main
```

## 项目结构

```
novel_dl/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── core/               # 核心功能模块
├── gui/                # 图形界面模块
├── utils/              # 工具函数
└── outputs/            # 下载文件输出目录
```

## 配置说明

在 `config.py` 中可以修改以下配置：
- 下载线程数
- 请求超时时间
- 重试次数
- 下载间隔
- 输出路径

## 注意事项

1. 请合理使用，不要对目标网站造成过大压力
2. 下载的内容仅供学习交流使用
3. 请遵守相关网站的使用规则

## 开源协议

本项目采用 MIT 协议开源，详见 [LICENSE](LICENSE) 文件。
