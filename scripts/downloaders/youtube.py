"""
YouTube下载处理器
优先使用官方字幕，无字幕时使用ASR
"""

import os
import re
import subprocess
import tempfile
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple

YT_DLP_CMD = [sys.executable, '-m', 'yt_dlp']
PROXY = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY') or os.getenv('VIDEO_LEARNER_PROXY')  # 可选代理


@dataclass
class DownloadResult:
    title: str
    audio_file: str = None
    subtitle_file: str = None
    subtitle_text: str = None
    needs_transcription: bool = True


class YouTubeDownloader:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def process(self, url: str) -> DownloadResult:
        """处理YouTube视频"""
        video_id = self._extract_video_id(url)
        
        title = self._get_title(url)
        
        has_subtitle, subtitle_lang = self._check_subtitles(url)
        
        if has_subtitle:
            subtitle_file = self._download_subtitle(url, video_id, subtitle_lang)
            subtitle_text = self._parse_subtitle(subtitle_file)
            
            return DownloadResult(
                title=title,
                subtitle_file=subtitle_file,
                subtitle_text=subtitle_text,
                needs_transcription=False
            )
        else:
            audio_file = self._download_audio(url, video_id)
            
            return DownloadResult(
                title=title,
                audio_file=audio_file,
                needs_transcription=True
            )
    
    def _extract_video_id(self, url: str) -> str:
        """提取YouTube视频ID"""
        patterns = [
            r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return "unknown"
    
    def _get_title(self, url: str) -> str:
        try:
            cmd = YT_DLP_CMD + ['--get-title']
            if PROXY:
                cmd.extend(['--proxy', PROXY])
            cmd.append(url)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return "YouTube视频"
    
    def _check_subtitles(self, url: str) -> Tuple[bool, Optional[str]]:
        try:
            cmd = YT_DLP_CMD + ['--list-subs']
            if PROXY:
                cmd.extend(['--proxy', PROXY])
            cmd.append(url)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            
            chinese_langs = ['zh-CN', 'zh-Hans', 'zh', 'zh-TW', 'zh-Hant', 'Chinese']
            
            for line in output.split('\n'):
                for lang in chinese_langs:
                    if lang in line:
                        return True, lang.split('-')[0] if '-' in lang else lang
            
            for line in output.split('\n'):
                for lang in chinese_langs:
                    if lang.lower() in line.lower():
                        if 'zh-cn' in line.lower() or 'zh-hans' in line.lower():
                            return True, 'zh-Hans'
                        elif 'zh-tw' in line.lower() or 'zh-hant' in line.lower():
                            return True, 'zh-Hant'
                        elif 'zh' in line.lower():
                            return True, 'zh'
            
        except Exception:
            pass
        
        return False, None
    
    def _download_subtitle(self, url: str, video_id: str, lang: str) -> str:
        output_path = Path(self.temp_dir) / f"youtube_{video_id}"
        
        cmd = YT_DLP_CMD + [
            '--write-subs',
            '--sub-langs', lang,
            '--skip-download',
            '-o', str(output_path),
        ]
        if PROXY:
            cmd.extend(['--proxy', PROXY])
        
        cmd.append(url)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        for ext in ['.zh-Hans.vtt', '.zh-CN.vtt', '.zh.vtt', '.vtt',
                     '.zh-Hans.srt', '.zh-CN.srt', '.zh.srt', '.srt']:
            subtitle_file = Path(self.temp_dir) / f"youtube_{video_id}{ext}"
            if subtitle_file.exists():
                return str(subtitle_file)
        
        possible_files = list(Path(self.temp_dir).glob(f"youtube_{video_id}.*"))
        for f in possible_files:
            if f.suffix in ['.vtt', '.srt']:
                return str(f)
        
        raise RuntimeError("字幕文件下载失败")
    
    def _parse_subtitle(self, subtitle_file: str) -> str:
        """解析字幕文件为纯文本"""
        text_lines = []
        
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith(('WEBVTT', 'NOTE')):
                continue
            
            if '-->' in line:
                continue
            
            if line.isdigit():
                continue
            
            if line.startswith('<'):
                line = re.sub(r'<[^>]+>', '', line)
            
            if line:
                text_lines.append(line)
        
        seen = set()
        unique_lines = []
        for line in text_lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def _download_audio(self, url: str, video_id: str) -> str:
        output_template = str(Path(self.temp_dir) / f"youtube_{video_id}.%(ext)s")
        
        cmd = YT_DLP_CMD + [
            '-f', 'bestaudio',
            '-o', output_template,
            '--no-playlist',
        ]
        if PROXY:
            cmd.extend(['--proxy', PROXY])
        
        cmd.append(url)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"YouTube下载失败: {result.stderr.strip()}")
        
        for ext in ['.m4a', '.webm', '.opus', '.mp3']:
            audio_file = Path(self.temp_dir) / f"youtube_{video_id}{ext}"
            if audio_file.exists():
                return str(audio_file)
        
        raise RuntimeError("音频文件未找到，下载可能失败")
