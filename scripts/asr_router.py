#!/usr/bin/env python3
"""
ASR 路由器 - 统一的语音识别接口
支持多种 ASR 引擎：阿里云 ASR、本地 Whisper 等
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


class ASRRouter:
    """ASR 路由器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 ASR 路由器
        
        Args:
            config: 配置字典，包含：
                - engine: ASR 引擎（aliyun, whisper）
                - api_key: 阿里云 API Key
                - model: ASR 模型名称
                - timeout: 超时时间（秒）
        """
        self.config = config or {}
        
        # 默认配置
        self.engine = self.config.get('engine', os.getenv('ASR_ENGINE', 'aliyun'))
        self.api_key = self.config.get('api_key', os.getenv('ALIYUN_ASR_API_KEY'))
        self.model = self.config.get('model', os.getenv('ASR_MODEL', 'fun-asr-mtl'))
        self.timeout = self.config.get('timeout', int(os.getenv('ASR_TIMEOUT', '60')))
        self.whisper_model = self.config.get('whisper_model', os.getenv('WHISPER_MODEL', 'base'))
    
    def transcribe(self, audio_file: str) -> str:
        """
        转录音频文件
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            转录文本
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        # 根据引擎选择不同的 ASR 实现
        if self.engine == 'aliyun':
            return self._transcribe_aliyun(audio_file)
        elif self.engine == 'whisper':
            return self._transcribe_whisper(audio_file)
        else:
            raise ValueError(f"不支持的 ASR 引擎: {self.engine}")
    
    def _transcribe_aliyun(self, audio_file: str) -> str:
        """
        使用阿里云 ASR 转录
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            转录文本
        """
        if not self.api_key:
            raise ValueError("阿里云 ASR 需要 API Key（设置 ALIYUN_ASR_API_KEY 环境变量）")
        
        # 导入阿里云 ASR 客户端
        try:
            from aliyun_asr import AliyunASR
        except ImportError:
            raise ImportError("请确保 aliyun_asr.py 在同一目录下")
        
        # 创建客户端并转录
        asr = AliyunASR(api_key=self.api_key, model=self.model)
        return asr.transcribe(audio_file, timeout=self.timeout)
    
    def _transcribe_whisper(self, audio_file: str) -> str:
        """
        使用本地 Whisper 转录
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            转录文本
        """
        import whisper
        import tempfile
        
        # 加载 Whisper 模型
        model = whisper.load_model(self.whisper_model)
        
        # 转录音频
        result = model.transcribe(audio_file, language='Chinese')
        
        # 提取文本
        return result['text'].strip()


def load_config_from_env() -> Dict[str, Any]:
    """从环境变量加载配置"""
    config = {}
    
    # ASR 引擎
    if 'ASR_ENGINE' in os.environ:
        config['engine'] = os.environ['ASR_ENGINE']
    
    # 阿里云 API Key
    if 'ALIYUN_ASR_API_KEY' in os.environ:
        config['api_key'] = os.environ['ALIYUN_ASR_API_KEY']
    
    # ASR 模型
    if 'ASR_MODEL' in os.environ:
        config['model'] = os.environ['ASR_MODEL']
    
    # 超时时间
    if 'ASR_TIMEOUT' in os.environ:
        config['timeout'] = int(os.environ['ASR_TIMEOUT'])
    
    # Whisper 模型
    if 'WHISPER_MODEL' in os.environ:
        config['whisper_model'] = os.environ['WHISPER_MODEL']
    
    return config


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='ASR 路由器 - 统一的语音识别接口')
    parser.add_argument('audio_file', help='音频文件路径')
    parser.add_argument('--engine', choices=['aliyun', 'whisper'], 
                        help='ASR 引擎（默认：aliyun）')
    parser.add_argument('--api-key', help='阿里云 API Key')
    parser.add_argument('--model', default='fun-asr-mtl', help='ASR 模型名称')
    parser.add_argument('--whisper-model', default='base', help='Whisper 模型名称')
    parser.add_argument('--timeout', type=int, default=60, help='超时时间（秒）')
    parser.add_argument('--output', help='输出文件路径（默认输出到标准输出）')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 合并配置：环境变量 + 命令行参数
    config = load_config_from_env()
    
    if args.engine:
        config['engine'] = args.engine
    if args.api_key:
        config['api_key'] = args.api_key
    if args.model:
        config['model'] = args.model
    if args.whisper_model:
        config['whisper_model'] = args.whisper_model
    if args.timeout:
        config['timeout'] = args.timeout
    
    try:
        # 创建 ASR 路由器
        router = ASRRouter(config)
        
        if args.debug:
            print(f"[调试] 引擎: {router.engine}", file=sys.stderr)
            print(f"[调试] 模型: {router.model}", file=sys.stderr)
        
        # 转录音频
        import time
        start_time = time.time()
        transcript = router.transcribe(args.audio_file)
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
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
