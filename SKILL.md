---
name: video-learner
description: "Video learning assistant: download, transcribe, generate smart notes, and upload to Feishu. Use when: (1) processing Bilibili/YouTube videos, (2) generating structured notes from transcripts, (3) uploading notes to Feishu knowledge base. Supports: automatic download, Whisper transcription, intelligent note extraction, and Feishu integration."
metadata:
  openclaw:
    emoji: "🎬"
    requires:
      bins: ["yt-dlp", "whisper", "python3"]
      files: ["~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt"]
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
        label: "Install OpenAI Whisper (pip)"
---

# Video Learning Assistant 🎬

Process video links from Bilibili and YouTube, automatically transcribe with Whisper, generate intelligent notes, and upload to Feishu knowledge base.

## When to Use

✅ **USE this skill when:**

- Processing video links (Bilibili, YouTube)
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

# Verify Whisper installation
source ~/.openclaw/venv/bin/activate
python -c "import whisper; print('Whisper OK')"

# Verify yt-dlp installation
yt-dlp --version
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

# Step 2: Transcribe with Whisper
source ~/.openclaw/venv/bin/activate
whisper /tmp/video.m4a \
  --language Chinese \
  --model base \
  --output_dir "/tmp" \
  --output_format txt

# Step 3: Generate smart notes
python3 "$WORKSPACE/scripts/smart_note_generator.py" \
  /tmp/video.txt \
  "Video Title"

# Step 4: Upload to Feishu (via OpenClaw tools)
# Call feishu_wiki and feishu_doc in main workflow

# Step 5: Clean up temporary files
find /tmp/video.* ! -name "*.txt" ! -name "*_smart_note.md" -delete
```

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
│   ├── video_with_feishu.sh        # Full pipeline (download → transcript → note → upload)
│   ├── video_processor.sh           # Download → transcript → note
│   ├── smart_note_generator.py      # Intelligent note extraction
│   └── upload_feishu.sh           # Feishu upload helper
├── cookies/
│   └── bilibili_cookies.txt        # Bilibili cookies (optional)
├── output/
│   └── bilibili_BVxxxxx_note.md   # Generated notes
└── tmp/
    └── bilibili_BVxxxxx.txt       # Transcripts
```

## Feishu Integration

### Upload Notes to Feishu

The Feishu upload requires OpenClaw tools in the main workflow:

1. **Create Document Node**
```bash
feishu_wiki action=create \
  space_id="7566441763399581724" \
  parent_node_token="I1GtwmgL4iok6WkfOghcR1uwnld" \
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

| Video Duration | Download | Whisper | Note Gen | Upload | Total |
|----------------|----------|---------|----------|--------|-------|
| 2 min | ~2s | ~30s | <1s | ~3s | ~36s |
| 3 min | ~3s | ~45s | <1s | ~4s | ~53s |
| 5 min | ~5s | ~75s | <1s | ~5s | ~86s |

## Smart Note Features

### Automatic Extraction

- **Keywords**: Top 15 keywords by frequency (with stopword filtering)
- **Core Points**: 3-5 key insights extracted from transcript
- **Practice Tips**: 3-5 actionable suggestions
- **Core Quotes**: 5 impactful, short sentences
- **Transcript**: Full text preserved

### Note Structure

```markdown
# Video Title

## 📹 Video Information
- Video ID, Platform, Processing Time, Status

## 🔑 Keywords
15 most frequent keywords

## ⭐ Core Points
3-5 key insights

## 💡 Key Information
Important sentences containing keywords

## 🎯 Practice Tips
3-5 actionable suggestions

## ✨ Core Quotes
5 impactful quotes

## 📝 Complete Transcript
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

### Example 3: Generate Notes from Transcript

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
