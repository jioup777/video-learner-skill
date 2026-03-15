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
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        file_size = os.path.getsize(audio_file)
        print(f"  [ASR] 音频文件: {os.path.basename(audio_file)} ({file_size / 1024 / 1024:.1f} MB)")
        
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
