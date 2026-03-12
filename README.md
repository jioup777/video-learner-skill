# Video Learner Skill - Quick Reference

## Quick Start

```bash
# Full pipeline (recommended)
cd ~/.openclaw/workspace-video-learner
./scripts/video_with_feishu.sh "https://www.bilibili.com/video/BVxxxxx"
```

## Essential Scripts

| Script | Purpose | Use When |
|--------|---------|----------|
| `video_with_feishu.sh` | Full pipeline with Feishu upload | Need complete workflow |
| `video_processor.sh` | Download, transcript, note generation | Don't need Feishu upload |
| `smart_note_generator.py` | Extract smart notes from transcript | Have existing transcript |
| `upload_feishu.sh` | Upload notes to Feishu | Have notes, need Feishu upload |

## Directory Structure

```
~/.openclaw/workspace-video-learner/
├── scripts/           # Processing scripts
├── cookies/           # Bilibili cookies (required)
├── output/            # Generated notes
└── tmp/              # Transcripts and temp files
```

## Common Issues

### Download Fails
**Error**: `HTTP Error 412: Precondition Failed`
**Fix**: Add Bilibili cookies to `cookies/bilibili_cookies.txt`

### Whisper Not Found
**Fix**:
```bash
source ~/.openclaw/venv/bin/activate
pip install openai-whisper
```

### Slow Transcription
**Fix**: Use smaller model
```bash
whisper audio.m4a --model tiny --language Chinese
```

## Feishu Integration

Feishu upload requires OpenClaw tools. In main workflow:

1. Create node: `feishu_wiki action=create ...`
2. Write content: `feishu_doc action=write ...`

## Links

- Full Documentation: See `SKILL.md`
- Workspace: `~/.openclaw/workspace-video-learner/`
- Feishu Space: 个人工作用记录

---
Last Updated: 2026-03-12
