"""
飞书文档上传模块
通过OpenClaw工具上传笔记到飞书知识库
"""

import os
import subprocess
import json
from typing import Optional


class FeishuUploader:
    def __init__(self, space_id: str = None, parent_token: str = None):
        self.space_id = space_id or os.getenv('FEISHU_SPACE_ID')
        self.parent_token = parent_token or os.getenv('FEISHU_PARENT_TOKEN')
        
        if not self.space_id:
            raise ValueError(
                "未配置飞书Space ID。\n"
                "请设置环境变量: export FEISHU_SPACE_ID='your_space_id'\n"
                "获取方式: 打开飞书知识库，从URL中复制Space ID"
            )
    
    def is_configured(self) -> bool:
        """检查是否配置完整"""
        return bool(self.space_id and self.parent_token)
    
    def upload(self, content: str, title: str) -> str:
        """
        上传笔记到飞书
        
        Args:
            content: 笔记内容（Markdown）
            title: 文档标题
        
        Returns:
            飞书文档链接
        """
        doc_token = self._create_document(title)
        
        self._write_content(doc_token, content)
        
        link = f"https://vicyrpffceo.feishu.cn/wiki/{doc_token}"
        
        return link
    
    def _create_document(self, title: str) -> str:
        """创建飞书文档节点"""
        try:
            result = subprocess.run(
                [
                    'feishu_wiki',
                    'action=create',
                    f'space_id={self.space_id}',
                    f'parent_node_token={self.parent_token}',
                    f'title={title}',
                    'obj_type=docx'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            import re
            match = re.search(r'node_token[:\s]+(\S+)', output)
            if match:
                return match.group(1)
            
            match = re.search(r'(\w{32})', output)
            if match:
                return match.group(1)
            
            raise RuntimeError(f"无法从输出中提取doc_token: {output[:200]}")
            
        except FileNotFoundError:
            raise RuntimeError(
                "feishu_wiki命令未找到。\n"
                "请确保OpenClaw工具已正确安装并配置。"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("创建飞书文档超时")
    
    def _write_content(self, doc_token: str, content: str) -> bool:
        """写入文档内容"""
        try:
            result = subprocess.run(
                [
                    'feishu_doc',
                    'action=write',
                    f'doc_token={doc_token}',
                    f'content={content}'
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout + result.stderr
            
            if '成功' in output or 'success' in output.lower():
                return True
            
            if result.returncode == 0:
                return True
            
            raise RuntimeError(f"写入内容失败: {output[:200]}")
            
        except FileNotFoundError:
            raise RuntimeError(
                "feishu_doc命令未找到。\n"
                "请确保OpenClaw工具已正确安装并配置。"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("写入飞书文档超时")
    
    def upload_local_file(self, file_path: str, title: str = None) -> str:
        """
        上传本地文件到飞书
        
        Args:
            file_path: 本地文件路径
            title: 文档标题（默认使用文件名）
        
        Returns:
            飞书文档链接
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not title:
            title = os.path.splitext(os.path.basename(file_path))[0]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.upload(content, title)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python feishu_uploader.py <笔记文件> [标题]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        uploader = FeishuUploader()
        link = uploader.upload_local_file(file_path, title)
        print(f"\n✅ 上传成功: {link}")
    except Exception as e:
        print(f"\n❌ 上传失败: {e}")
        sys.exit(1)
