# Video Learner - OpenClaw Skill 🎬

> Automatically download, transcribe, and generate intelligent notes from videos (Bilibili, YouTube), with Feishu knowledge base integration.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)
![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)

## Features

- 🎬 **Video Download**: Support for Bilibili and YouTube
- 🎙️ **Audio Transcription**: Whisper-based transcription (Chinese language optimized)
- 📝 **Smart Note Generation**: Automatic extraction of keywords, core points, tips, and quotes
- 📚 **Feishu Integration**: Direct upload to Feishu knowledge base
- 🧹 **Automatic Cleanup**: Clean up temporary files after processing
- 🚀 **Fast Processing**: 2-5 minute videos processed in ~36-86 seconds

## Quick Start

### Installation

This skill is installed as part of OpenClaw. No additional installation required.

### Configuration

1. **Feishu Setup** (Required for upload)

   ```bash
   export FEISHU_SPACE_ID="your_space_id"
   export FEISHU_PARENT_TOKEN="your_parent_node_token"
   ```

2. **Bilibili Cookies** (Optional but recommended)

   See [COOKIES.md](COOKIES.md) for detailed instructions.

### Usage

```bash
cd ~/.openclaw/workspace-video-learner

# Full pipeline (download → transcript → note → upload)
./scripts/video_with_feishu.sh "https://www.bilibili.com/video/BVxxxxx"
```

## Documentation

- [SKILL.md](SKILL.md) - Complete OpenClaw skill documentation
- [README.md](README.md) - Quick reference guide
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [COOKIES.md](COOKIES.md) - Bilibili cookies setup
- [CHANGELOG.md](CHANGELOG.md) - Version history

## Scripts

| Script | Purpose |
|--------|---------|
| `video_with_feishu.sh` | Full pipeline with Feishu upload |
| `video_processor.sh` | Download, transcript, and note generation |
| `smart_note_generator.py` | Intelligent note extraction |
| `upload_feishu.sh` | Feishu upload helper |

## Performance

| Video Duration | Total Time |
|----------------|------------|
| 2 minutes | ~36 seconds |
| 3 minutes | ~53 seconds |
| 5 minutes | ~86 seconds |

## Smart Note Features

Generated notes include:

- 🔑 15 keywords (frequency-based)
- ⭐ 3-5 core points
- 💡 3-5 practice tips
- ✨ 5 core quotes
- 📝 Complete transcript

## Requirements

- **Python**: 3.8+
- **yt-dlp**: Video downloader
- **openai-whisper**: Audio transcription
- **OpenClaw**: Agent framework

## Security

⚠️ **Important**: This skill does not include sensitive configuration:

- **Feishu credentials**: Configure via environment variables or `.env` file
- **Bilibili cookies**: Export from browser and save to `cookies/bilibili_cookies.txt`
- **No API keys**: Uses only local tools (yt-dlp, Whisper)

See [CONFIGURATION.md](CONFIGURATION.md) for details.

## Troubleshooting

### Download Fails

**Error**: `HTTP Error 412: Precondition Failed` (Bilibili)

**Solution**: Add valid Bilibili cookies. See [COOKIES.md](COOKIES.md).

### Whisper Not Found

**Solution**:
```bash
source ~/.openclaw/venv/bin/activate
pip install openai-whisper
```

### Slow Transcription

**Solution**: Use smaller model
```bash
whisper audio.m4a --model tiny --language Chinese
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloader
- [OpenAI Whisper](https://github.com/openai/whisper) - Audio transcription
- [OpenClaw](https://github.com/openclaw/openclaw) - Agent framework

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Author**: Video Assistant (OpenClaw)
**Version**: 1.0.0
**Status**: Production Ready ✅
