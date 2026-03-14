#!/usr/bin/env python3
"""
阿里云 ASR 语音识别客户端（使用 HTTP API）
使用 fun-asr-mtl 模型进行语音转写
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Optional


class AliyunASR:
    """阿里云 ASR 客户端"""
    
    def __init__(self, api_key: str, model: str = "fun-asr-mtl"):
        """
        初始化 ASR 客户端
        
        Args:
            api_key: 阿里云 API Key
            model: ASR 模型名称，默认 fun-asr-mtl
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://nlp.cn-shanghai.aliyuncs.com"
    
    def transcribe(self, audio_file: str, timeout: int = 60) -> str:
        """
        转录音频文件
        
        Args:
            audio_file: 音频文件路径
            timeout: 超时时间（秒），默认 60 秒
        
        Returns:
            转录文本
        
        Raises:
            Exception: 转录失败时抛出异常
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        # 读取音频文件
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        
        try:
            # 步骤 1: 异步调用转录 API
            task_id = self._async_call(audio_data, timeout)
            
            # 步骤 2: 等待转录完成
            result = self._wait_for_result(task_id, timeout)
            
            # 步骤 3: 提取完整转录文本
            transcript = self._extract_transcript(result)
            
            return transcript
            
        except Exception as e:
            raise Exception(f"转录失败: {str(e)}")
    
    def _async_call(self, audio_data: bytes, timeout: int) -> str:
        """
        异步调用转录 API
        
        Args:
            audio_data: 音频二进制数据
            timeout: 超时时间（秒）
        
        Returns:
            任务 ID
        """
        url = f"{self.base_url}/transcription/async"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/octet-stream"
        }
        
        params = {
            "model": self.model
        }
        
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=audio_data,
            timeout=timeout
        )
        
        if response.status_code != 200:
            error_msg = f"API 调用失败 (HTTP {response.status_code})"
            try:
                error_detail = response.json()
                error_msg += f": {error_detail.get('message', response.text)}"
            except:
                error_msg += f": {response.text}"
            raise Exception(error_msg)
        
        result = response.json()
        task_id = result.get('task_id') or result.get('taskId')
        
        if not task_id:
            raise Exception(f"未获取任务 ID: {result}")
        
        return task_id
    
    def _wait_for_result(self, task_id: str, timeout: int) -> dict:
        """
        等待转录任务完成
        
        Args:
            task_id: 任务 ID
            timeout: 超时时间（秒）
        
        Returns:
            转录结果字典
        """
        url = f"{self.base_url}/transcription/wait"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "task_id": task_id
        }
        
        start_time = time.time()
        
        # 使用长轮询等待结果
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise Exception(f"转录超时（{timeout}秒）")
            
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=min(30, timeout - elapsed)  # 单次请求超时
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 检查任务状态
                    status = result.get('status')
                    if status == 'completed' or status == 'success':
                        return result
                    elif status == 'failed' or status == 'error':
                        error_msg = result.get('error') or result.get('message') or '未知错误'
                        raise Exception(f"转录失败: {error_msg}")
                    # 如果状态是 processing 或 pending，继续等待
                    
                elif response.status_code != 202:  # 202 表示仍在处理中
                    raise Exception(f"查询失败 (HTTP {response.status_code}): {response.text}")
                
            except requests.exceptions.Timeout:
                # 单次请求超时，继续等待
                pass
            
            # 等待一段时间后重试
            time.sleep(0.5)
    
    def _extract_transcript(self, result: dict) -> str:
        """
        从 API 响应中提取完整转录文本
        
        Args:
            result: API 响应结果
        
        Returns:
            完整的转录文本
        """
        transcript = ""
        
        # 尝试多种可能的格式
        if 'output' in result and 'text' in result['output']:
            transcript = result['output']['text']
        elif 'transcript' in result:
            transcript = result['transcript']
        elif 'result' in result:
            inner_result = result['result']
            if isinstance(inner_result, dict):
                if 'text' in inner_result:
                    transcript = inner_result['text']
                elif 'transcript' in inner_result:
                    transcript = inner_result['transcript']
                elif 'sentences' in inner_result:
                    # 如果是多句子格式，拼接所有句子
                    sentences = inner_result['sentences']
                    transcript = ' '.join([s.get('text', '') for s in sentences])
            elif isinstance(inner_result, str):
                transcript = inner_result
        elif 'sentences' in result:
            # 如果是多句子格式，拼接所有句子
            sentences = result['sentences']
            transcript = ' '.join([s.get('text', '') for s in sentences])
        elif 'text' in result:
            transcript = result['text']
        
        if not transcript:
            # 如果都失败，尝试将整个结果转为字符串（用于调试）
            print(f"警告：无法提取转录文本，返回原始结果", file=sys.stderr)
            transcript = json.dumps(result, ensure_ascii=False, indent=2)
        
        return transcript.strip()


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='阿里云 ASR 语音识别')
    parser.add_argument('audio_file', help='音频文件路径')
    parser.add_argument('--api-key', help='阿里云 API Key（或通过 ALIYUN_ASR_API_KEY 环境变量设置）')
    parser.add_argument('--model', default='fun-asr-mtl', help='ASR 模型名称')
    parser.add_argument('--timeout', type=int, default=60, help='超时时间（秒）')
    parser.add_argument('--output', help='输出文件路径（默认输出到标准输出）')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 获取 API Key
    api_key = args.api_key or os.getenv('ALIYUN_ASR_API_KEY')
    if not api_key:
        print("错误：请提供 API Key（--api-key 参数或 ALIYUN_ASR_API_KEY 环境变量）", file=sys.stderr)
        sys.exit(1)
    
    try:
        # 创建 ASR 客户端
        asr = AliyunASR(api_key=api_key, model=args.model)
        
        # 转录音频
        start_time = time.time()
        transcript = asr.transcribe(args.audio_file, timeout=args.timeout)
        elapsed = time.time() - start_time
        
        # 输出结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"✓ 转录完成: {args.output} ({elapsed:.2f}s)", file=sys.stderr)
        else:
            print(transcript)
        
        if args.debug:
            print(f"\n[调试] 耗时: {elapsed:.2f}s", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
