"""
抖音下载处理器
使用 f2 库解析分享链接并下载无水印视频
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import asyncio
import json


@dataclass
class DownloadResult:
    title: str
    audio_file: str = None
    subtitle_file: str = None
    subtitle_text: str = None
    needs_transcription: bool = True


class DouyinDownloader:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self._check_f2()
    
    def _check_f2(self):
        """检查f2是否已安装"""
        try:
            result = subprocess.run(
                ['f2', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError("f2未安装，请运行: pip install f2")
        except FileNotFoundError:
            raise RuntimeError("f2未安装，请运行: pip install f2")
    
    def process(self, url: str) -> DownloadResult:
        """处理抖音视频"""
        video_id = self._extract_video_id(url)
        
        title, video_path = self._download_video(url, video_id)
        
        audio_file = self._extract_audio(video_path, video_id)
        
        if video_path.exists():
            video_path.unlink()
        
        return DownloadResult(
            title=title,
            audio_file=audio_file,
            needs_transcription=True
        )
    
    def _extract_video_id(self, url: str) -> str:
        """从分享链接提取视频ID"""
        return "douyin_video"
    
    def _download_video(self, url: str, video_id: str) -> tuple:
        """使用f2下载无水印视频"""
        output_dir = Path(self.temp_dir)
        
        cmd = [
            'f2', 'dy',
            '-M', 'one',
            '-u', url,
            '--path', str(output_dir),
            '--mode', 'json',
            '--no-config',
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            raise RuntimeError(f"抖音下载失败: {error_msg}")
        
        title = "抖音视频"
        video_path = None
        
        try:
            output = json.loads(result.stdout)
            if isinstance(output, dict):
                data = output.get('data', {})
                title = data.get('desc', title)
                video_path_str = data.get('video_path')
                if video_path_str:
                    video_path = Path(video_path_str)
        except json.JSONDecodeError:
            pass
        
        if video_path is None or not video_path.exists():
            mp4_files = list(output_dir.glob("*.mp4"))
            if mp4_files:
                mp4_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                video_path = mp4_files[0]
        
        if video_path is None or not video_path.exists():
            raise RuntimeError("视频文件下载失败")
        
        return title, video_path
    
    def _extract_audio(self, video_path: Path, video_id: str) -> str:
        """从视频中提取音频"""
        audio_file = Path(self.temp_dir) / f"douyin_{video_id}.m4a"
        
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',
            '-acodec', 'copy',
            '-y',
            str(audio_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            audio_file = Path(self.temp_dir) / f"douyin_{video_id}.mp3"
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',
                '-acodec', 'libmp3lame',
                '-y',
                str(audio_file)
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"音频提取失败: {result.stderr}")
        
        if not audio_file.exists():
            raise RuntimeError("音频文件创建失败")
        
        return str(audio_file)
