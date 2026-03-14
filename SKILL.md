---
name: video-learner
description: "Video learning assistant: download, transcribe, generate smart notes, and upload to Feishu. Use when: (1) processing Bilibili/YouTube videos, (2) generating structured notes from transcripts, (3) uploading notes to Feishu knowledge base. Supports: automatic download, ASR transcription (Aliyun/Whisper), intelligent note extraction, and Feishu integration."
metadata:
  openclaw:
    emoji: "🎬"
    requires:
      bins: ["yt-dlp", "python3", "ffmpeg"]
      files: ["~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt"]
      env: ["ALIYUN_ASR_API_KEY"]
    install:
      - id: yt-dlp
        kind: pip
        package: yt-dlp
        bins: ["yt-dlp"]
        label: "Install yt-dlp (pip)"
      - id: whisper
        kind: pip
        package: openai-whisper
        bins: ["whisper"]
        label: "Install OpenAI Whisper (pip, optional)"
      - id: ffmpeg
        kind: brew
        package: ffmpeg
        bins: ["ffmpeg"]
        label: "Install FFmpeg (brew)"
      - id: requests
        kind: pip
        package: requests
        label: "Install requests (for Aliyun ASR)"
---

# Video Learning Assistant 🎬

Process video links from Bilibili and YouTube, automatically transcribe with Whisper, generate intelligent notes, and upload to Feishu knowledge base.

## When to Use

✅ **USE this skill when:**

- Processing video links (Bilibili, YouTube, Douyin)
- Transcribing video audio to text
- Generating structured learning notes
- Uploading notes to Feishu knowledge base
- Extracting key insights, points, and quotes from videos

## When NOT to Use

❌ **DON'T use this skill when:**

- Local audio files (use `whisper` directly)
- Non-video content (articles, podcasts, etc.)
- Need only video download (use `yt-dlp` directly)
- Feishu operations unrelated to video notes (use `feishu-doc` skill)

## Setup

```bash
# Set workspace (one-time)
export WORKSPACE="${HOME}/.openclaw/workspace-video-learner"
mkdir -p "$WORKSPACE"/{output,tmp,cookies,scripts}

# Download Bilibili cookies (optional, recommended)
# 1. Login to Bilibili in browser
# 2. Export cookies using browser extension
# 3. Save to: $WORKSPACE/cookies/bilibili_cookies.txt

# ASR Configuration (阿里云 ASR 推荐)
export ASR_ENGINE="aliyun"  # 或 "whisper"
export ALIYUN_ASR_API_KEY="your_aliyun_api_key"
export ASR_MODEL="fun-asr-mtl"  # 模型：fun-asr-mtl, paraformer-realtime-8k-v1, paraformer-realtime-16k-v1
export ASR_TIMEOUT="60"  # 超时时间（秒）

# Note Generation Configuration (GLM-4-Flash 推荐)
export NOTE_ENGINE="glm"  # 或 "smart" (词频提取)
export GLM_API_KEY="your_glm_api_key"  # 从 https://open.bigmodel.cn/ 获取

# Verify Whisper installation (如果使用本地 Whisper)
source ~/.openclaw/venv/bin/activate
python -c "import whisper; print('Whisper OK')"

# Verify yt-dlp installation
yt-dlp --version

# Verify ASR dependencies
python3 -c "import requests; print('Requests OK')"
```

## Common Commands

### Quick Start - Full Pipeline

```bash
# Process a single video with all steps
cd "$WORKSPACE"
./scripts/video_with_feishu.sh "https://www.bilibili.com/video/BVxxxxx"
```

### Step-by-Step Processing

```bash
# Step 1: Download audio
yt-dlp --cookies "$WORKSPACE/cookies/bilibili_cookies.txt" \
  -f "bestaudio" \
  -o "/tmp/video.%(ext)s" \
  "https://www.bilibili.com/video/BVxxxxx"

# Step 2: Transcribe with ASR
# 选项 A: 使用阿里云 ASR（推荐，速度快 2-3 秒，准确率高）
export ASR_ENGINE="aliyun"
export ALIYUN_ASR_API_KEY="your_aliyun_api_key"
export ASR_MODEL="fun-asr-mtl"

python3 "$WORKSPACE/scripts/asr_router.py" \
  --engine aliyun \
  --output /tmp/video.txt \
  /tmp/video.m4a

# 选项 B: 使用本地 Whisper（免费，但速度较慢）
source ~/.openclaw/venv/bin/activate
whisper /tmp/video.m4a \
  --language Chinese \
  --model base \
  --output_dir "/tmp" \
  --output_format txt

# Step 3: Generate smart notes
# 选项 A: 使用 GLM-4-Flash（推荐，质量高）
export NOTE_ENGINE="glm"
export GLM_API_KEY="your_glm_api_key"

python3 "$WORKSPACE/scripts/glm_note_generator.py" \
  /tmp/video.txt \
  "Video Title"

# 选项 B: 使用词频提取（免费，快速）
export NOTE_ENGINE="smart"

python3 "$WORKSPACE/scripts/smart_note_generator.py" \
  /tmp/video.txt \
  "Video Title"

# Step 4: Upload to Feishu (via OpenClaw tools)
# Call feishu_wiki and feishu_doc in main workflow

# Step 5: Clean up temporary files
find /tmp/video.* ! -name "*.txt" ! -name "*_smart_note.md" -delete
```

### Process Douyin Videos

```bash
# Process Douyin video with full pipeline (download → extract → transcribe → notes → Feishu)
cd "$WORKSPACE"
./scripts/process_douyin.sh "https://v.douyin.com/xxxxx/"

# The script will:
# 1. Parse Douyin URL and extract video info
# 2. Download video (no watermark)
# 3. Extract audio using FFmpeg
# 4. Transcribe with SenseVoice (fast) or Whisper (free)
# 5. Generate smart notes (using smart_note_generator.py)
# 6. Upload to Feishu knowledge base
# 7. Clean up temporary files
```

**Note**: Douyin processing uses the `douyin-mcp-server` package which supports SenseVoice API for fast transcription. Requires `API_KEY` environment variable for SenseVoice.

### Intelligent Note Generation

```bash
# Generate notes from existing transcript
python3 "$WORKSPACE/scripts/smart_note_generator.py" \
  /path/to/transcript.txt \
  "Video Title"

# Output includes:
# - 15 keywords
# - 3-5 core points
# - 5 core quotes
# - 3-5 practice tips
# - Complete transcript
```

### Download Audio Only

```bash
# Bilibili (with cookies)
yt-dlp --cookies "$WORKSPACE/cookies/bilibili_cookies.txt" \
  -f "bestaudio" \
  -o "/tmp/%(title)s.%(ext)s" \
  "https://www.bilibili.com/video/BVxxxxx"

# YouTube
yt-dlp -f "bestaudio" \
  -o "/tmp/%(title)s.%(ext)s" \
  "https://www.youtube.com/watch?v=xxxxx"
```

## File Structure

```
~/.openclaw/workspace-video-learner/
├── scripts/
│   ├── video_with_feishu.sh        # Bilibili/YouTube pipeline (download → transcript → note → upload)
│   ├── video_processor.sh           # Bilibili/YouTube (download → transcript → note)
│   ├── process_douyin.sh           # Douyin pipeline (download → extract → transcribe → notes → Feishu)
│   ├── glm_note_generator.py       # GLM-4-Flash note generator (recommended)
│   ├── smart_note_generator.py      # Smart note extraction (word frequency based)
│   ├── asr_router.py               # ASR router (Aliyun/Whisper)
│   ├── aliyun_asr.py              # Aliyun ASR client
│   └── upload_feishu.sh            # Feishu upload helper
├── cookies/
│   └── bilibili_cookies.txt        # Bilibili cookies (optional)
├── douyin-mcp-server/              # Douyin processing (SenseVoice API)
│   └── douyin-video/scripts/
│       └── douyin_downloader.py
├── output/
│   ├── bilibili_BVxxxxx_note.md   # Bilibili/YouTube notes
│   └── douyin_xxxxx_note.md       # Douyin notes
└── tmp/
    ├── bilibili_BVxxxxx.txt       # Bilibili/YouTube transcripts
    └── douyin_xxxxx.txt           # Douyin transcripts
```

## Feishu Integration

### Upload Notes to Feishu

The Feishu upload requires OpenClaw tools in the main workflow:

1. **Create Document Node**
```bash
feishu_wiki action=create \
  space_id="your_space_id" \
  parent_node_token="your_parent_token" \
  title="Video Title (BVxxxxx)" \
  obj_type=docx
```

2. **Write Content**
```bash
feishu_doc action=write \
  doc_token="<doc_token_from_create>" \
  content="<markdown_content>"
```

3. **Document Link**
```
https://vicyrpffceo.feishu.cn/wiki/<node_token>
```

### Feishu Configuration

Feishu integration requires configuration:

```bash
# Set environment variables
export FEISHU_SPACE_ID="your_space_id"
export FEISHU_PARENT_TOKEN="your_parent_node_token"
```

Or configure in scripts (not recommended):

```bash
# Edit scripts/video_with_feishu.sh
FEISHU_SPACE_ID="your_space_id"
FEISHU_PARENT_TOKEN="your_parent_node_token"
```

### How to Get Feishu Configuration

1. Open your Feishu workspace
2. Navigate to the knowledge base
3. Copy the Space ID from URL: `https://vicyrpffceo.feishu.cn/wiki/<space_id>`
4. Copy the Parent Node Token where you want to upload documents

## Performance Data

### With Aliyun ASR + GLM-4-Flash

| Video Duration | Download | Aliyun ASR | GLM Note Gen | Upload | Total |
|----------------|----------|------------|--------------|--------|-------|
| 2 min | ~2s | ~3s | ~5s | ~3s | ~13s |
| 3 min | ~3s | ~4s | ~7s | ~4s | ~18s |
| 5 min | ~5s | ~6s | ~10s | ~5s | ~26s |

### With Whisper + Smart Note (Word Frequency)

| Video Duration | Download | Whisper | Smart Note Gen | Upload | Total |
|----------------|----------|---------|----------------|--------|-------|
| 2 min | ~2s | ~30s | <1s | ~3s | ~36s |
| 3 min | ~3s | ~45s | <1s | ~4s | ~53s |
| 5 min | ~5s | ~75s | <1s | ~5s | ~86s |

**Note**: GLM-4-Flash significantly improves note quality with ~5-10s overhead. Word frequency extraction is faster but less accurate.

## Smart Note Features

### Note Generation Engines

**GLM-4-Flash (Recommended)**
- Uses GLM-4-Flash LLM for context-aware note generation
- Extracts: Core Theme, Core Points, Typical Cases, Identification Methods, Anti-fraud Advice, Core Quotes
- Understands context and produces high-quality structured notes
- Requires GLM API Key

**Smart Note (Word Frequency)**
- Uses word frequency and pattern matching for note extraction
- Extracts: Keywords, Key Sentences, Core Points, Practice Tips, Golden Quotes
- Faster but less accurate
- Free, no API required

### Automatic Extraction (GLM-4-Flash)

- **Core Theme**: Main topic identification
- **Core Points**: 3-5 key insights extracted from transcript
- **Typical Cases**: Real-world examples and case studies
- **Identification Methods**: Methods for identifying patterns/issues
- **Anti-fraud Advice**: Fraud prevention tips (when applicable)
- **Core Quotes**: 5 impactful, short sentences
- **Transcript**: Full text preserved

### Note Structure (GLM-4-Flash)

```markdown
# Video Title

## 📹 视频信息
- Video ID, Platform, Processing Time, Status, Token Consumption

## 核心主题
Main topic of the video

## 核心观点
3-5 key insights from the content

## 典型案例
Real-world examples and case studies

## 识别方法
Methods for identifying patterns/issues

## 防骗建议
Fraud prevention tips (when applicable)

## 核心金句
5 impactful quotes

## 📝 完整转录内容
Full transcript text
```

### Note Structure (Smart Note)

```markdown
# Video Title

## 📹 视频信息
- Video ID, Platform, Processing Time, Status

## 🔑 关键词
15 most frequent keywords

## ⭐ 核心观点
3-5 key insights

## 💡 关键句子
Important sentences containing keywords

## 🎯 实践建议
3-5 actionable suggestions

## ✨ 核心金句
5 impactful quotes

## 📝 完整转录内容
Full transcript text
```

## Bilibili Cookies (Required)

### Why Required

Bilibili requires authentication to download video audio. Without cookies, downloads fail with `HTTP Error 412: Precondition Failed`.

### How to Get

1. Login to Bilibili in browser
2. Use browser extension to export cookies (e.g., "Get cookies.txt LOCALLY")
3. Save to `~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt`

### Cookie Format

```bash
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.bilibili.com	TRUE	/	FALSE	<timestamp>	SESSDATA	<value>
.bilibili.com	TRUE	/	FALSE	<timestamp>	DedeUserID	<value>
.bilibili.com	TRUE	/	FALSE	<timestamp>	bili_jct	<value>
...
```

## Troubleshooting

### Download Fails

**Problem**: `HTTP Error 412: Precondition Failed`

**Solution**: Bilibili requires cookies. Export cookies from browser and save to `cookies/bilibili_cookies.txt`.

### Transcription Fails

**Problem**: Whisper not found or fails

**Solution**:
```bash
# Activate virtual environment
source ~/.openclaw/venv/bin/activate

# Verify Whisper
python -c "import whisper; print('Whisper OK')"

# If missing, install
pip install openai-whisper
```

### Slow Transcription

**Problem**: Whisper takes too long

**Solution**: Use smaller model
```bash
whisper audio.m4a --model tiny --language Chinese --output_format txt
```

Models by speed: `tiny` < `base` < `small` < `medium` < `large`

### Feishu Upload Fails

**Problem**: Feishu tools not available in bash script

**Solution**: Feishu upload requires OpenClaw tools. Use `feishu_wiki` and `feishu_doc` in the main OpenClaw workflow.

### Keywords Extraction Poor

**Problem**: Extracted keywords are inaccurate

**Solution**: This is known limitation. Keywords are based on word frequency with basic stopword filtering. Improve by:
- Adding more stopwords in `smart_note_generator.py`
- Using local LLM for better extraction
- Manual review and editing

## Advanced Usage

### Batch Processing

```bash
# Process multiple videos
for url in "url1" "url2" "url3"; do
  cd "$WORKSPACE"
  ./scripts/video_processor.sh "$url"
done
```

### Custom Whisper Model

```bash
# Edit video_processor.sh or use directly
whisper audio.m4a \
  --language Chinese \
  --model medium \      # Use medium instead of base
  --output_dir "/tmp" \
  --output_format txt
```

### Transcribe Existing Audio

```bash
# Transcribe local audio file
source ~/.openclaw/venv/bin/activate
whisper /path/to/audio.m4a \
  --language Chinese \
  --model base \
  --output_dir /tmp \
  --output_format txt

# Generate notes
python3 "$WORKSPACE/scripts/smart_note_generator.py" \
  /tmp/audio.txt \
  "Custom Title"
```

## Scripts Reference

### video_with_feishu.sh

Full pipeline script. Includes all steps: download, transcript, note generation, Feishu upload, cleanup.

**Usage**:
```bash
./scripts/video_with_feishu.sh "https://www.bilibili.com/video/BVxxxxx"
```

### video_processor.sh

Basic pipeline script. Includes: download, transcript, note generation, cleanup.

**Usage**:
```bash
./scripts/video_processor.sh "https://www.bilibili.com/video/BVxxxxx"
```

### smart_note_generator.py

Intelligent note extraction from transcript.

**Usage**:
```bash
python3 scripts/smart_note_generator.py <transcript_file> [video_title]
```

**Output**: Markdown file with structured notes.

## Notes

- **Whisper Models**: `tiny` (fastest, ~32MB), `base` (balanced, ~74MB), `small` (~244MB), `medium` (~769MB), `large` (best, ~1550MB)
- **Language**: Set `--language Chinese` for Chinese videos. Auto-detect may be inaccurate.
- **Output Format**: Use `--output_format txt` for plain text, `--output_format srt` for subtitles.
- **Bilibili Cookies**: Required for Bilibili videos. Validity limited; update when downloads fail.
- **Feishu Limits**: Feishu API has rate limits. For bulk uploads, add delays between requests.

## Examples

### Example 1: Bilibili Video

```bash
# Process Bilibili video
cd ~/.openclaw/workspace-video-learner
./scripts/video_with_feishu.sh "https://www.bilibili.com/video/BV1c8NFzhEMi/"

# Output:
# - Audio: /tmp/bilibili_BV1c8NFzhEMi.m4a
# - Transcript: /tmp/bilibili_BV1c8NFzhEMi.txt
# - Notes: output/bilibili_BV1c8NFzhEMi_note.md
# - Feishu Link: https://vicyrpffceo.feishu.cn/wiki/<node_token>
```

### Example 2: YouTube Video

```bash
# Process YouTube video
cd ~/.openclaw/workspace-video-learner
./scripts/video_processor.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Note: Feishu upload not included (requires OpenClaw tools)
```

### Example 3: Douyin Video

```bash
# Process Douyin video
cd ~/.openclaw/workspace-video-learner
./scripts/process_douyin.sh "https://v.douyin.com/7600361826030865707/"

# Output:
# - Video: /tmp/douyin_7600361826030865707.mp4
# - Audio: /tmp/douyin_7600361826030865707.mp3
# - Transcript: /tmp/douyin_7600361826030865707.txt
# - Notes: output/douyin_7600361826030865707_note.md
# - Feishu Link: https://vicyrpffceo.feishu.cn/wiki/<node_token>
```

**Note**: Douyin processing requires SenseVoice API. If `API_KEY` is not set, the script falls back to Whisper (slower but free).

### Example 4: Generate Notes from Transcript

```bash
# Generate notes from existing transcript
python3 ~/.openclaw/workspace-video-learner/scripts/smart_note_generator.py \
  /tmp/existing_transcript.txt \
  "Custom Video Title"

# Output: /tmp/existing_transcript_smart_note.md
```

---

**Author**: Video Assistant (OpenClaw)
**Created**: 2026-03-12
**Version**: 1.0.0
**Status**: Production Ready ✅
