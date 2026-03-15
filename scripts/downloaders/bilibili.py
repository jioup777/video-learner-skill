"""
Bilibili下载处理器
使用 yt-dlp + cookies 下载B站视频音频
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from dataclasses import dataclass

YT_DLP_CMD = [sys.executable, '-m', 'yt_dlp']
PROXY = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY') or os.getenv('VIDEO_LEARNER_PROXY')  # 可选代理


@dataclass
class DownloadResult:
    title: str
    audio_file: str = None
    subtitle_file: str = None
    subtitle_text: str = None
    needs_transcription: bool = True


class BilibiliDownloader:
    def __init__(self):
        self.cookies_file = os.getenv(
            'BILIBILI_COOKIES',
            str(Path(__file__).parent.parent.parent / 'cookies' / 'bilibili_cookies.txt')
        )
    
    def process(self, url: str) -> DownloadResult:
        """处理B站视频"""
        video_id = self._extract_bvid(url)
        
        title = self._get_title(url)
        
        audio_file = self._download_audio(url, video_id)
        
        return DownloadResult(
            title=title,
            audio_file=audio_file,
            needs_transcription=True
        )
    
    def _extract_bvid(self, url: str) -> str:
        """提取BV号"""
        match = re.search(r'BV[a-zA-Z0-9]+', url)
        if match:
            return match.group(0)
        return "unknown"
    
    def _get_title(self, url: str) -> str:
        try:
            cmd = YT_DLP_CMD + ['--get-title']
            if PROXY:
                cmd.extend(['--proxy', PROXY])
            cmd.append(url)
            if Path(self.cookies_file).exists():
                cmd.extend(['--cookies', str(self.cookies_file)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        
        return "B站视频"
    
    def _download_audio(self, url: str, video_id: str) -> str:
        temp_dir = tempfile.gettempdir()
        output_template = str(Path(temp_dir) / f"bilibili_{video_id}.%(ext)s")
        
        cmd = YT_DLP_CMD + [
            '-f', 'bestaudio',
            '-o', output_template,
            '--no-playlist',
        ]
        
        if PROXY:
            cmd.extend(['--proxy', PROXY])
        
        if Path(self.cookies_file).exists():
            cmd.extend(['--cookies', str(self.cookies_file)])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "未知错误"
            if "412" in error_msg or "Precondition Failed" in error_msg:
                raise RuntimeError(f"B站下载失败(412): 需要有效的cookies")
            raise RuntimeError(f"B站下载失败: {error_msg}")
        
        for ext in ['.m4a', '.webm', '.opus', '.mp3']:
            audio_file = Path(temp_dir) / f"bilibili_{video_id}{ext}"
            if audio_file.exists():
                return str(audio_file)
        
        raise RuntimeError("音频文件未找到，下载可能失败")
