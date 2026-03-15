---
name: video-learner
description: "Video learning assistant: download, transcribe, generate smart notes, and upload to Feishu. Use when: (1) processing Bilibili/YouTube/Douyin videos, (2) generating structured notes from transcripts, (3) uploading notes to Feishu knowledge base. Supports: automatic download, Aliyun ASR transcription, intelligent note extraction with GLM-4-Flash, and Feishu integration."
metadata:
  openclaw:
    emoji: "🎬"
  requires:
    bins: ["yt-dlp", "python3", "ffmpeg"]
    files: ["~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt"]
    env: ["GLM_API_KEY", "ALIYUN_ASR_API_KEY", "FEISHU_APP_ID", "FEISHU_APP_SECRET"]
    install:
      - id: yt-dlp
        kind: pip
        package: yt-dlp
        bins: ["yt-dlp"]
        label: "Install yt-dlp"

      - id: ffmpeg
        kind: brew
        package: ffmpeg
        bins: ["ffmpeg"]
        label: "Install FFmpeg"
---

# Video Learner 🎬

从 Bilibili、YouTube、抖音视频自动生成学习笔记并上传飞书。

## 平台差异化策略

| 平台 | 下载方案 | 字幕来源 | 特殊功能 |
|------|----------|----------|----------|
| **Bilibili** | cookies + yt-dlp | ASR转录 | cookies验证、412错误提示 |
| **YouTube** | yt-dlp + cookies | 官方字幕优先，无则ASR | 多语言字幕检测、浏览器cookies支持 |
| **Douyin** | requests API | ASR转录 | 无需f2库、自动fallback |

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
FEISHU_APP_ID=xxx         # 飞书应用ID
FEISHU_APP_SECRET=xxx     # 飞书应用密钥
```

### 可选配置

```env
BILIBILI_COOKIES=~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt
WORKSPACE=~/.openclaw/workspace-video-learner
```

## 处理流程

```
视频URL → 平台识别 → 下载/字幕获取 → ASR转录(如需，自动分段) → GLM笔记生成 → 飞书上传(API)
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
│   │   ├── bilibili.py        # B站下载(cookies验证)
│   │   ├── youtube.py         # YouTube下载(字幕优先)
│   │   └── douyin.py          # 抖音下载(requests API)
│   ├── asr_aliyun.py          # 阿里云ASR(自动分段)
│   ├── note_generator.py      # GLM笔记生成
│   ├── feishu_uploader.py     # 飞书上传(直接API)
│   ├── exceptions.py          # 统一异常类
│   └── utils.py               # 工具函数(重试装饰器)
├── cookies/
│   └── bilibili_cookies.txt   # B站cookies
└── output/                    # 生成的笔记
```

## 依赖安装

```bash
# 核心依赖
pip install yt-dlp dashscope python-dotenv requests

# JavaScript运行时 (YouTube推荐，非必需)
# Windows: https://github.com/denoland/deno/releases
# macOS: brew install deno
# Linux: curl -fsSL https://deno.land/install.sh | sh

# FFmpeg (必需，用于音频处理)
# Windows: https://ffmpeg.org/download.html
# macOS: brew install ffmpeg
# Ubuntu: apt install ffmpeg
```

## 平台特殊要求

### B站
- 需要有效的cookies文件
- 获取方式：浏览器扩展导出Netscape格式cookies
- 自动验证cookies有效性
- 412错误时提供详细解决方案

### YouTube  
- **需要cookies** - YouTube反爬虫机制
- **建议安装deno** - JavaScript运行时，用于解析YouTube页面
- 支持浏览器cookies：`yt-dlp --cookies-from-browser chrome "URL"`
- 多语言字幕检测：zh-CN, zh-Hans, zh, zh-TW, zh-Hant, en
- 参考：https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies

### 抖音
- **无需f2库** - 使用requests API直接下载
- 自动fallback机制
- 支持分享链接：https://v.douyin.com/xxxxx/

## 常见问题

### B站下载失败 (412错误)
系统会提供详细解决方案：
1. 更新cookies文件（推荐使用EditThisCookie扩展）
2. 或使用浏览器cookies：`yt-dlp --cookies-from-browser chrome "URL"`
3. SESSDATA有效期约1个月，需定期更新

### 抖音下载失败
确保网络可访问douyin.com，无需安装f2库。

### ASR转录失败
- 检查DASHSCOPE_API_KEY是否正确
- 大文件会自动分段（9MB阈值）
- 确保FFmpeg已安装：`ffmpeg -version`

### 飞书上传失败
检查：
- FEISHU_APP_ID 和 FEISHU_APP_SECRET 是否正确
- 飞书应用权限是否包含"知识库文档写入"
- 可在飞书开放平台获取应用凭证

### YouTube字幕未检测到
- 部分视频没有官方字幕，会自动回退到ASR
- 字幕检测支持：zh-CN, zh-Hans, zh, zh-TW, zh-Hant, en

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
- YouTube官方字幕优先 + 多语言检测
- 抖音requests API下载（无需f2）
- ASR大文件自动分段（9MB阈值）
- Feishu直接API调用（无需OpenClaw CLI）
- 统一异常类和重试机制
- Cookies验证和详细错误提示

### 删除
- ~~双ASR引擎切换~~ → 固定阿里云
- ~~双笔记引擎切换~~ → 固定GLM
- ~~Whisper本地支持~~ → 简化依赖
- ~~smart_note_generator.py~~ → 效果不佳
- ~~video_processor.sh~~ → 合并到统一入口
- ~~f2库依赖~~ → 抖音改用requests API
- ~~OpenClaw飞书工具~~ → 直接API调用

### 配置简化
- 从10+项 → 4项必需配置
- 飞书认证从Token改为AppID+Secret

---

*Video Learner v2.0 - Simplified & Refactored*
*Last Updated: 2026-03-15*
