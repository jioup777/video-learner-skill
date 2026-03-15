"""
阿里云ASR语音转录模块
使用DashScope SDK和fun-asr-mtl模型进行语音识别
"""

import os
import json
import time
import subprocess
from typing import Optional
from http import HTTPStatus

try:
    import dashscope
    from dashscope.audio.asr import Transcription
    from dashscope import Files
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False


class AliyunASR:
    MODEL = "fun-asr-mtl"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY') or os.getenv('ALIYUN_ASR_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "未配置阿里云ASR API Key。\n"
                "请设置环境变量: export DASHSCOPE_API_KEY='your_api_key'\n"
                "获取API Key: https://dashscope.console.aliyun.com/"
            )
        
        if not DASHSCOPE_AVAILABLE:
            raise ImportError(
                "dashscope库未安装。\n"
                "请运行: pip install dashscope"
            )
        
        dashscope.api_key = self.api_key
    
    def transcribe(self, audio_file: str, language: str = "zh") -> str:
        """
        转录音频文件
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码 (zh/en)
        
        Returns:
            转录文本
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        file_size = os.path.getsize(audio_file)
        file_size_mb = file_size / 1024 / 1024
        print(f"  [ASR] 音频文件: {os.path.basename(audio_file)} ({file_size_mb:.1f} MB)")
        
        LARGE_FILE_THRESHOLD_MB = 9  # 9MB阈值
        
        if file_size_mb > LARGE_FILE_THRESHOLD_MB:
            print(f"  [ASR] 大文件检测: {file_size_mb:.1f}MB > {LARGE_FILE_THRESHOLD_MB}MB，启用分段处理")
            return self._transcribe_with_segments(audio_file, file_size_mb, language)
        else:
            converted_file = self._convert_audio(audio_file)
            if converted_file != audio_file:
                print(f"  [ASR] 已转换为WAV格式")
            
            try:
                result = self._transcribe_with_upload(converted_file)
            finally:
                if converted_file != audio_file:
                    try:
                        os.unlink(converted_file)
                    except:
                        pass
            
            return result
    
    def _transcribe_with_segments(self, audio_file: str, file_size_mb: float, language: str) -> str:
        """
        分段处理大文件
        
        Args:
            audio_file: 音频文件路径
            file_size_mb: 文件大小(MB)
            language: 语言代码
        
        Returns:
            合并的转录文本
        """
        LARGE_FILE_THRESHOLD_MB = 9
        MAX_SEGMENT_SIZE_MB = 8  # 每段最大8MB
        MAX_SEGMENT_SIZE_BYTES = MAX_SEGMENT_SIZE_MB * 1024 * 1024
        
        # 使用ffmpeg分段音频
        segments = self._split_audio_by_size(audio_file, MAX_SEGMENT_SIZE_BYTES)
        num_segments = len(segments)
        
        print(f"  [ASR] 音频已分段为 {num_segments} 段")
        
        all_texts = []
        for i, segment_file in enumerate(segments):
            print(f"  [ASR] 处理分段 {i+1}/{num_segments}")
            
            try:
                converted_file = self._convert_audio(segment_file)
                if converted_file != segment_file:
                    print(f"  [ASR] 分段已转换为WAV格式")
                
                text = self._transcribe_single_file(converted_file)
                all_texts.append(text)
                
                if converted_file != segment_file:
                    try:
                        os.unlink(converted_file)
                    except:
                        pass
            except Exception as e:
                print(f"  [ASR] 分段{i+1}转录失败: {e}")
                all_texts.append("")  # 保持数组长度
        
        # 合并转录结果
        combined_text = '\n'.join(all_texts)
        print(f"  [ASR] 分段转录完成，总字符数: {len(combined_text)}")
        return combined_text
    
    def _split_audio_by_size(self, audio_file: str, max_size_bytes: int) -> list:
        """
        按文件大小分段音频
        
        Args:
            audio_file: 音频文件路径
            max_size_bytes: 最大字节数
        
        Returns:
            分段文件列表
        """
        # 获取音频总时长
        duration = self._get_audio_duration(audio_file)
        if duration is None:
            print(f"  [ASR] 无法获取音频时长，使用固定分段")
            return [audio_file]  # 无法分段则返回原文件
        
        # 计算分段数量
        file_size = os.path.getsize(audio_file)
        num_segments = int(file_size / max_size_bytes) + 1
        
        segments = []
        for i in range(num_segments):
            start_time = (i * duration) / num_segments
            segment_duration = duration / num_segments
            output_file = f"{audio_file}_part{i}.wav"
            
            self._split_audio_segment(audio_file, start_time, segment_duration, output_file)
            segments.append(output_file)
        
        return segments
    
    def _get_audio_duration(self, audio_file: str) -> Optional[float]:
        """
        获取音频时长
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            音频时长（秒），失败返回None
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-i', audio_file, '-show_entries', 'format=duration', '-v', 'quiet'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 解析时长
                duration_str = result.stderr.strip()
                # 格式类似 "0:01:23.45"
                parts = duration_str.split(':')
                if len(parts) >= 3:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    return total_seconds
        except Exception as e:
            print(f"  [ASR] 获取音频时长失败: {e}")
        
        return None
    
    def _split_audio_segment(self, audio_file: str, start_time: float, duration: float, output_file: str):
        """
        分割音频段
        
        Args:
            audio_file: 源音频文件
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            output_file: 输出文件路径
        """
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', audio_file,
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'copy',
                '-vn', '-sn', '-dn',
                output_file
            ], check=True)
        except Exception as e:
            print(f"  [ASR] ffmpeg分割失败: {e}")
    
    def _transcribe_single_file(self, audio_file: str) -> str:
        """
        转录单个文件
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            转录文本
        """
        converted_file = self._convert_audio(audio_file)
        if converted_file != audio_file:
            print(f"  [ASR] 已转换为WAV格式")
        
        try:
            result = self._transcribe_with_upload(converted_file)
        finally:
            if converted_file != audio_file:
                try:
                    os.unlink(converted_file)
                except:
                    pass
        
        return result
    
    def _convert_audio(self, audio_file: str) -> str:
        ext = os.path.splitext(audio_file)[1].lower()
        if ext in ['.wav', '.pcm']:
            return audio_file
        
        wav_file = audio_file.rsplit('.', 1)[0] + '_converted.wav'
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', audio_file, '-ar', '16000', '-ac', '1', '-f', 'wav', wav_file],
                capture_output=True,
                timeout=60
            )
            if result.returncode == 0 and os.path.exists(wav_file):
                return wav_file
        except Exception as e:
            print(f"  [ASR] ffmpeg转换失败: {e}")
        
        return audio_file
    
    def _transcribe_with_upload(self, audio_file: str) -> str:
        start_time = time.time()
        
        try:
            print(f"  [ASR] 上传文件到DashScope...")
            upload_result = Files.upload(
                file_path=audio_file,
                purpose='inference'
            )
            
            if upload_result.status_code != HTTPStatus.OK:
                raise RuntimeError(f"文件上传失败: {upload_result.message}")
            
            uploaded = upload_result.output.get('uploaded_files', [])
            if not uploaded:
                raise RuntimeError(f"文件上传失败: 无上传结果")
            
            file_id = uploaded[0].get('file_id')
            if not file_id:
                raise RuntimeError(f"文件上传失败: 缺少file_id")
            
            file_info = Files.get(file_id=file_id)
            if file_info.status_code != HTTPStatus.OK:
                raise RuntimeError(f"获取文件信息失败: {file_info.message}")
            
            file_url = file_info.output.get('url')
            if not file_url:
                raise RuntimeError(f"获取文件URL失败")
            
            print(f"  [ASR] 文件上传成功，开始转录...")
            
            task_response = Transcription.async_call(
                model=self.MODEL,
                file_urls=[file_url]
            )
            
            if task_response.status_code != HTTPStatus.OK:
                raise RuntimeError(f"ASR任务提交失败: {task_response.message}")
            
            task_id = task_response.output.task_id
            print(f"  [ASR] 任务ID: {task_id}")
            
            transcribe_response = Transcription.wait(task=task_id)
            
            elapsed = time.time() - start_time
            print(f"  [ASR] 转录完成 (耗时 {elapsed:.1f}s)")
            
            if transcribe_response.status_code == HTTPStatus.OK:
                text = self._extract_text(transcribe_response.output)
                try:
                    Files.delete(file_id=file_id)
                except:
                    pass
                return text
            else:
                raise RuntimeError(f"ASR转录失败: {transcribe_response.message}")
                
        except Exception as e:
            raise RuntimeError(f"ASR转录异常: {str(e)}")
    
    def _extract_text(self, output) -> str:
        if hasattr(output, 'results'):
            results = output.results
            texts = []
            for result in results:
                if isinstance(result, dict):
                    if 'transcription_url' in result:
                        text = self._fetch_transcription(result['transcription_url'])
                        if text:
                            texts.append(text)
                    elif 'transcription_text' in result:
                        texts.append(result['transcription_text'])
                    elif 'text' in result:
                        texts.append(result['text'])
                elif hasattr(result, 'transcription_url'):
                    text = self._fetch_transcription(result.transcription_url)
                    if text:
                        texts.append(text)
                elif hasattr(result, 'transcription_text'):
                    texts.append(result.transcription_text)
                elif hasattr(result, 'text'):
                    texts.append(result.text)
            if texts:
                return '\n'.join(texts)
        
        output_dict = output if isinstance(output, dict) else (vars(output) if hasattr(output, '__dict__') else {})
        
        if 'results' in output_dict:
            texts = []
            for result in output_dict['results']:
                if isinstance(result, dict):
                    if 'transcription_url' in result:
                        text = self._fetch_transcription(result['transcription_url'])
                        if text:
                            texts.append(text)
                    elif 'transcription_text' in result:
                        texts.append(result['transcription_text'])
                    elif 'text' in result:
                        texts.append(result['text'])
            if texts:
                return '\n'.join(texts)
        
        if 'transcription_text' in output_dict:
            return output_dict['transcription_text']
        
        return str(output)
    
    def _fetch_transcription(self, url: str) -> str:
        import urllib.request
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                texts = []
                if 'transcripts' in data:
                    for item in data['transcripts']:
                        if 'text' in item:
                            texts.append(item['text'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'text' in item:
                            texts.append(item['text'])
                elif isinstance(data, dict) and 'text' in data:
                    texts.append(data['text'])
                return '\n'.join(texts) if texts else ''
        except Exception as e:
            print(f"  [ASR] Warning: Failed to fetch transcription: {e}")
            return ''


def transcribe_file(audio_file: str, api_key: str = None) -> str:
    asr = AliyunASR(api_key=api_key)
    return asr.transcribe(audio_file)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python asr_aliyun.py <音频文件> [API_KEY]")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        text = transcribe_file(audio_file, api_key)
        print(f"\n[OK] 转录完成:\n{text}")
    except Exception as e:
        print(f"\n[ERROR] 转录失败: {e}")
        sys.exit(1)
