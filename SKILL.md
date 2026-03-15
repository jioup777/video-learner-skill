---
name: video-learner
description: "Video learning assistant: download, transcribe, generate smart notes, and upload to Feishu. Use when: (1) processing Bilibili/YouTube/Douyin videos, (2) generating structured notes from transcripts, (3) uploading notes to Feishu knowledge base. Supports: automatic download, Aliyun ASR transcription, intelligent note extraction with GLM-4-Flash, and Feishu integration."
metadata:
  openclaw:
    emoji: "🎬"
    requires:
      bins: ["yt-dlp", "python3", "ffmpeg", "f2"]
      files: ["~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt"]
      env: ["GLM_API_KEY", "ALIYUN_ASR_API_KEY", "FEISHU_SPACE_ID", "FEISHU_PARENT_TOKEN"]
    install:
      - id: yt-dlp
        kind: pip
        package: yt-dlp
        bins: ["yt-dlp"]
        label: "Install yt-dlp"
      - id: f2
        kind: pip
        package: f2
        bins: ["f2"]
        label: "Install f2 (Douyin downloader)"
      - id: ffmpeg
        kind: brew
        package: ffmpeg
        bins: ["ffmpeg"]
        label: "Install FFmpeg"
---

# Video Learner 🎬

从 Bilibili、YouTube、抖音视频自动生成学习笔记并上传飞书。

## 平台差异化策略

| 平台 | 下载方案 | 字幕来源 |
|------|----------|----------|
| **Bilibili** | cookies + yt-dlp | ASR转录 |
| **YouTube** | yt-dlp | 官方字幕优先，无则ASR |
| **Douyin** | f2 (无水印) | ASR转录 |

## 快速开始

```bash
# 设置环境变量
export GLM_API_KEY="your_key"
export ALIYUN_ASR_API_KEY="your_key"
export FEISHU_SPACE_ID="your_space_id"
export FEISHU_PARENT_TOKEN="your_token"

# 运行
cd ~/.openclaw/workspace-video-learner
python scripts/video_learner.py "https://www.bilibili.com/video/BVxxxxx"
```

## 使用示例

### B站视频
```bash
python scripts/video_learner.py "https://www.bilibili.com/video/BV1xx411c7mD"
```

### YouTube视频（自动检测官方字幕）
```bash
python scripts/video_learner.py "https://www.youtube.com/watch?v=xxxxx"
# 有官方字幕 → 直接使用，跳过ASR
# 无官方字幕 → 下载音频 + ASR转录
```

### 抖音视频（无水印下载）
```bash
python scripts/video_learner.py "https://v.douyin.com/xxxxx/"
```

### 不上传飞书
```bash
python scripts/video_learner.py "url" --no-upload
```

## 配置说明

### 必需配置 (4项)

```env
GLM_API_KEY=xxx           # GLM API密钥
ALIYUN_ASR_API_KEY=xxx    # 阿里云ASR密钥
FEISHU_SPACE_ID=xxx       # 飞书空间ID
FEISHU_PARENT_TOKEN=xxx   # 飞书父节点Token
```

### 可选配置

```env
BILIBILI_COOKIES=~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt
WORKSPACE=~/.openclaw/workspace-video-learner
```

## 处理流程

```
视频URL → 平台识别 → 下载/字幕获取 → ASR转录(如需) → GLM笔记生成 → 飞书上传
```

### YouTube特有逻辑

```
YouTube URL → 检测官方字幕
              ├─ 有字幕 → 下载字幕 → 解析为文本 → 跳过ASR
              └─ 无字幕 → yt-dlp下载音频 → ASR转录
```

### 抖音特有逻辑

```
抖音分享链接 → f2解析 → 无水印视频下载 → FFmpeg提取音频 → ASR转录
```

## 目录结构

```
~/.openclaw/workspace-video-learner/
├── scripts/
│   ├── video_learner.py       # 统一入口
│   ├── downloaders/
│   │   ├── __init__.py
│   │   ├── bilibili.py        # B站下载
│   │   ├── youtube.py         # YouTube下载+字幕
│   │   └── douyin.py          # 抖音下载(f2)
│   ├── asr_aliyun.py          # 阿里云ASR
│   ├── note_generator.py      # GLM笔记生成
│   └── feishu_uploader.py     # 飞书上传
├── cookies/
│   └── bilibili_cookies.txt   # B站cookies
└── output/                    # 生成的笔记
```

## 依赖安装

```bash
# 核心依赖
pip install yt-dlp dashscope python-dotenv

# JavaScript运行时 (YouTube需要)
# Windows: https://github.com/denoland/deno/releases
# macOS: brew install deno
# Linux: curl -fsSL https://deno.land/install.sh | sh
```

## 平台特殊要求

### B站
- 需要有效的cookies文件
- 获取方式：浏览器扩展导出Netscape格式cookies

### YouTube  
- **需要cookies** - YouTube反爬虫机制
- **建议安装deno** - JavaScript运行时，用于解析YouTube页面
- Cookies获取：使用 `yt-dlp --cookies-from-browser chrome "URL"` 或手动导出
- 参考：https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies

### 抖音
- 需要安装f2库：`pip install f2`

## 常见问题

### B站下载失败 (412错误)
需要配置有效的B站cookies：
1. 登录B站
2. 使用浏览器扩展导出cookies
3. 保存到 `cookies/bilibili_cookies.txt`

### 抖音下载失败
确保已安装f2：
```bash
pip install f2
f2 --version
```

### 飞书上传失败
检查：
- FEISHU_SPACE_ID 是否正确
- FEISHU_PARENT_TOKEN 是否有写权限
- OpenClaw飞书工具是否配置正确

### YouTube字幕未检测到
- 部分视频没有官方字幕，会自动回退到ASR
- 字幕检测支持：zh-CN, zh-Hans, zh, zh-TW, zh-Hant

## 获取API密钥

| 服务 | 获取地址 |
|------|----------|
| GLM | https://open.bigmodel.cn/ |
| 阿里云ASR | https://nls-portal.console.aliyun.com/ |

## 性能数据

| 视频时长 | 下载 | ASR | GLM笔记 | 飞书 | 总计 |
|----------|------|-----|---------|------|------|
| 2分钟 | ~2s | ~3s | ~5s | ~3s | ~13s |
| 5分钟 | ~5s | ~6s | ~10s | ~5s | ~26s |
| YouTube(有字幕) | ~2s | 跳过 | ~5s | ~3s | ~10s |

## 重构变更 (v2.0)

### 新增
- 统一入口 `video_learner.py`
- YouTube官方字幕优先
- 抖音f2无水印下载
- 平台差异化处理

### 删除
- ~~双ASR引擎切换~~ → 固定阿里云
- ~~双笔记引擎切换~~ → 固定GLM
- ~~Whisper本地支持~~ → 简化依赖
- ~~smart_note_generator.py~~ → 效果不佳
- ~~video_processor.sh~~ → 合并到统一入口

### 配置简化
- 从10+项 → 4项必需配置

---

*Video Learner v2.0 - Simplified & Refactored*
*Last Updated: 2026-03-15*
