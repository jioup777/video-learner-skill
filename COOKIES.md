# Bilibili Cookies Setup Guide

## Why Required

Bilibili requires authentication to download video audio. Without valid cookies, downloads fail with:

```
HTTP Error 412: Precondition Failed
```

## How to Get Cookies

### Option 1: Browser Extension (Recommended)

1. Login to [Bilibili](https://www.bilibili.com/)
2. Install browser extension: "Get cookies.txt LOCALLY" or similar
3. Click extension → Export cookies
4. Save to: `~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt`

### Option 2: Manual Export

1. Login to Bilibili
2. Open Developer Tools (F12)
3. Go to Application → Cookies → https://www.bilibili.com
4. Export required cookies:
   - `SESSDATA` (required)
   - `DedeUserID` (required)
   - `bili_jct` (required)

## Cookie File Format

```bash
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.bilibili.com	TRUE	/	FALSE	<timestamp>	SESSDATA	<your_value>
.bilibili.com	TRUE	/	FALSE	<timestamp>	DedeUserID	<your_value>
.bilibili.com	TRUE	/	FALSE	<timestamp>	bili_jct	<your_value>
```

## Testing Cookies

```bash
# Test download
yt-dlp --cookies ~/.openclaw/workspace-video-learner/cookies/bilibili_cookies.txt \
  -f "bestaudio" \
  -o "/tmp/test.%(ext)s" \
  "https://www.bilibili.com/video/BV1xx411c7mD/"

# If successful, should download audio
# If failed, cookies are invalid or expired
```

## Cookie Expiration

Bilibili cookies expire. If downloads start failing:

1. Export new cookies using same method
2. Replace content in `cookies/bilibili_cookies.txt`
3. Test again

## Alternative: No Cookies

If you cannot get cookies:

- **YouTube videos**: No cookies required (works without authentication)
- **Bilibili videos**: Cookies required (cannot download without authentication)

## Security Notes

- Never share your cookies publicly
- Cookies contain session tokens; treat like passwords
- Only share in trusted environments
- Rotate cookies periodically

## Troubleshooting

### "Cookies are invalid"

- Cookies expired → Export fresh cookies
- Corrupted file → Re-export cookies

### "Download still fails"

- Check cookie format (Netscape format required)
- Ensure file is at correct path
- Verify cookies are for `bilibili.com`, not `www.bilibili.com`

### "412 Precondition Failed"

- Cookies missing or invalid
- Video requires authentication (VIP content)
- IP blocked by Bilibili

---

Last Updated: 2026-03-12
