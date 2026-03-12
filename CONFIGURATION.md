# Configuration Guide

## Quick Setup

1. **Clone or Download Skill**
   ```bash
   # The skill will be in:
   ~/.npm-global/lib/node_modules/openclaw/skills/video-learner/
   ```

2. **Configure Feishu**

   Get your Feishu credentials:

   a. Open your Feishu workspace
   b. Navigate to the target knowledge base
   c. Copy the Space ID from the URL: `https://vicyrpffceo.feishu.cn/wiki/<space_id>`
   d. Right-click the folder where you want to upload documents → Copy Node Token

   Configure:

   ```bash
   # Method 1: Environment Variables (Recommended)
   export FEISHU_SPACE_ID="your_space_id"
   export FEISHU_PARENT_TOKEN="your_parent_node_token"

   # Method 2: Create .env file
   cp .env.example .env
   # Edit .env and fill in your values
   ```

3. **Configure Bilibili Cookies (Optional but Recommended)**

   See [COOKIES.md](COOKIES.md) for detailed instructions.

## Configuration Files

### .env (Recommended)

Create a `.env` file in the skill directory:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Workspace
WORKSPACE="${HOME}/.openclaw/workspace-video-learner"

# Feishu
FEISHU_SPACE_ID="your_space_id"
FEISHU_PARENT_TOKEN="your_parent_node_token"

# Whisper
WHISPER_MODEL="base"

# Bilibili
BILIBILI_COOKIES="${WORKSPACE}/cookies/bilibili_cookies.txt"
```

### Scripts Configuration

If you prefer to edit scripts directly (not recommended):

Edit `scripts/video_with_feishu.sh`:

```bash
# Find this section
# Feishu 配置（从环境变量读取，或手动配置）
FEISHU_SPACE_ID="${FEISHU_SPACE_ID:-YOUR_SPACE_ID}"
FEISHU_PARENT_TOKEN="${FEISHU_PARENT_TOKEN:-YOUR_PARENT_NODE_TOKEN}"

# Replace with your values
FEISHU_SPACE_ID="your_actual_space_id"
FEISHU_PARENT_TOKEN="your_actual_parent_node_token"
```

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `WORKSPACE` | Workspace directory | No | `${HOME}/.openclaw/workspace-video-learner` |
| `FEISHU_SPACE_ID` | Feishu space ID | Yes (for upload) | `7566441763399581724` |
| `FEISHU_PARENT_TOKEN` | Feishu parent node token | Yes (for upload) | `I1GtwmgL4iok6WkfOghcR1uwnld` |
| `WHISPER_MODEL` | Whisper model size | No | `base` |
| `BILIBILI_COOKIES` | Bilibili cookies file path | No (for Bilibili) | `/path/to/cookies.txt` |

## Security Notes

### ⚠️ Important Security Practices

1. **Never Commit Sensitive Data**
   - Do not commit `.env` file
   - Do not commit `cookies/bilibili_cookies.txt`
   - Use `.env.example` for templates

2. **Environment Variables Are Safer**
   - Use environment variables for credentials
   - Do not hardcode in scripts
   - Scripts check environment first, then fallback to defaults

3. **Rotate Credentials**
   - Feishu tokens: No expiration (but rotate periodically)
   - Bilibili cookies: Expire, update when downloads fail
   - API keys: Rotate if compromised

4. **Git Ignore**
   The `.gitignore` file excludes sensitive files:
   ```
   .env
   cookies/
   tmp/
   output/
   ```

## Troubleshooting

### Feishu Upload Fails

**Error**: Space ID or parent token invalid

**Solution**:
1. Verify Space ID in Feishu URL
2. Verify parent node token is correct
3. Check permissions (must have write access)

### Bilibili Download Fails

**Error**: HTTP Error 412: Precondition Failed

**Solution**:
1. Cookies are invalid or expired
2. Export fresh cookies from browser
3. Update `cookies/bilibili_cookies.txt`

### Scripts Can't Find Configuration

**Error**: `YOUR_SPACE_ID` or similar placeholder

**Solution**:
1. Set environment variables
2. Or edit scripts and replace placeholders
3. Or create `.env` file (not recommended)

## Testing Configuration

### Test Feishu Configuration

```bash
# Set environment variables
export FEISHU_SPACE_ID="your_space_id"
export FEISHU_PARENT_TOKEN="your_parent_node_token"

# Test by running script
cd ~/.openclaw/workspace-video-learner
./scripts/upload_feishu.sh /tmp/test_note.md "Test Video"

# If successful, should see: "飞书上传任务信息"
```

### Test Bilibili Cookies

```bash
# Test download
yt-dlp --cookies ~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt \
  -f "bestaudio" \
  -o "/tmp/test.%(ext)s" \
  "https://www.bilibili.com/video/BV1xx411c7mD/" \
  --skip-download

# If successful, should see video information
# If failed, cookies are invalid
```

### Test Whisper

```bash
# Activate virtual environment
source ~/.openclaw/venv/bin/activate

# Test Whisper
whisper --version

# Should see version number, e.g., "20230314"
```

## Advanced Configuration

### Custom Whisper Model

```bash
# Edit script or use environment variable
export WHISPER_MODEL="small"  # Options: tiny, base, small, medium, large
```

Model comparison:
| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~32MB | Fastest | Good |
| base | ~74MB | Fast | Better |
| small | ~244MB | Medium | Good |
| medium | ~769MB | Slow | Better |
| large | ~1550MB | Slowest | Best |

### Custom Output Directory

```bash
# Edit WORKSPACE in .env or scripts
export WORKSPACE="${HOME}/custom/workspace"
```

### Multiple Feishu Spaces

You can use different configurations by:

1. Creating multiple `.env` files
2. Loading different configuration before each run
3. Passing parameters to scripts

```bash
# Load custom configuration
source .env.production

# Or set inline
FEISHU_SPACE_ID="space1" ./scripts/video_with_feishu.sh "url"
```

---

Last Updated: 2026-03-12
