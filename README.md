# Video Learner Skill

从 B站/YouTube/抖音 视频自动生成学习笔记并上传飞书。

## 快速开始

```bash
# 设置环境变量
export GLM_API_KEY="your_key"
export DASHSCOPE_API_KEY="your_key"
export FEISHU_SPACE_ID="your_space_id"
export FEISHU_PARENT_TOKEN="your_token"

# 运行 (B站)
python scripts/video_learner.py "https://www.bilibili.com/video/BVxxxxx"

# 运行 (YouTube)
python scripts/video_learner.py "https://www.youtube.com/watch?v=xxxxx"

# 运行 (抖音)
python scripts/video_learner.py "https://v.douyin.com/xxxxx/"

# 不上传飞书
python scripts/video_learner.py "url" --no-upload
```

## 平台要求

| 平台 | 下载方案 | 特殊要求 | 测试状态 |
|------|----------|----------|----------|
| **B站** | yt-dlp + cookies | cookies文件 | ✅ 通过 |
| **YouTube** | yt-dlp | cookies + deno(推荐) | ⚠️ 需cookies |
| **抖音** | f2库 | pip install f2 | ⏸️ f2安装问题 |

## 依赖安装

```bash
# 核心依赖
pip install yt-dlp dashscope python-dotenv

# 抖音支持 (可能需要 --user 或虚拟环境)
pip install f2
# 或
pip install f2 --user

# JavaScript运行时 (YouTube推荐)
# macOS: brew install deno
# Linux: curl -fsSL https://deno.land/install.sh | sh
# Windows: https://github.com/denoland/deno/releases

# FFmpeg (音频处理)
# macOS: brew install ffmpeg
# Ubuntu: apt install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

## 配置文件

复制 `.env.example` 为 `.env` 并填写：

| 变量 | 必需 | 说明 |
|------|------|------|
| `GLM_API_KEY` | ✅ | 智谱GLM API |
| `DASHSCOPE_API_KEY` | ✅ | 阿里云ASR API |
| `FEISHU_SPACE_ID` | ✅ | 飞书空间ID |
| `FEISHU_PARENT_TOKEN` | ✅ | 飞书父节点Token |
| `BILIBILI_COOKIES` | ❌ | B站cookies路径 |
| `VIDEO_LEARNER_PROXY` | ❌ | 代理地址(国内需要) |

## Cookies 获取

### B站
1. 登录 bilibili.com
2. 使用浏览器扩展导出Netscape格式
3. 保存到 `cookies/bilibili_cookies.txt`

### YouTube
1. 使用 `yt-dlp --cookies-from-browser chrome "URL"`
2. 或手动导出cookies文件

## 常见问题

### 412错误 (B站)
cookies过期，需重新导出

### YouTube需要登录
添加cookies或使用 `--cookies-from-browser`

### ASR失败
检查DASHSCOPE_API_KEY是否正确

### f2安装失败 (抖音)
```bash
# 尝试使用 --user 安装
pip install f2 --user

# 或使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
pip install f2
```

## 测试结果

| 平台 | 状态 | 备注 |
|------|------|------|
| B站 | ✅ | 需要有效cookies |
| YouTube | ⚠️ | 需要cookies + deno |
| 抖音 | ⏸️ | f2库安装问题 |

## 文件结构

```
scripts/
├── video_learner.py       # 统一入口
├── downloaders/
│   ├── bilibili.py        # B站下载
│   ├── youtube.py         # YouTube下载
│   └── douyin.py          # 抖音下载
├── asr_aliyun.py          # 阿里云ASR
├── note_generator.py      # GLM笔记生成
└── feishu_uploader.py     # 飞书上传
```

---
详细文档见 [SKILL.md](./SKILL.md)
