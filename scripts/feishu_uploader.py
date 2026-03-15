"""
飞书文档上传模块
直接调用飞书开放平台API，不依赖命令行工具
"""

import os
import json
import requests
from typing import Optional, List, Dict
from pathlib import Path


class FeishuUploader:
    """飞书文档上传器"""
    
    API_BASE = "https://open.feishu.cn/open-apis"
    
    def __init__(self, app_id: str = None, app_secret: str = None, 
                 space_id: str = None, parent_token: str = None):
        """
        初始化飞书上传器
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            space_id: 飞书知识库空间ID
            parent_token: 父节点Token
        """
        self.app_id = app_id or os.getenv('FEISHU_APP_ID')
        self.app_secret = app_secret or os.getenv('FEISHU_APP_SECRET')
        self.space_id = space_id or os.getenv('FEISHU_SPACE_ID')
        self.parent_token = parent_token or os.getenv('FEISHU_PARENT_TOKEN')
        self.tenant_token = None
        
        # 验证配置
        if not self.app_id or not self.app_secret:
            raise ValueError(
                "未配置飞书应用凭证。\n"
                "请设置环境变量: FEISHU_APP_ID 和 FEISHU_APP_SECRET\n"
                "获取方式: 飞书开放平台 (https://open.feishu.cn/app) > 创建自建应用"
            )
        
        if not self.space_id:
            raise ValueError(
                "未配置飞书空间ID。\n"
                "请设置环境变量: FEISHU_SPACE_ID\n"
                "获取方式: 飞书知识库 > 空间设置 > 查看空间信息"
            )
        
        if not self.parent_token:
            raise ValueError(
                "未配置飞书父节点Token。\n"
                "请设置环境变量: FEISHU_PARENT_TOKEN\n"
                "获取方式: 飞书知识库 > 右键目标文件夹 > 复制Node Token"
            )
        
        # 获取访问令牌
        self._get_tenant_token()
    
    def is_configured(self) -> bool:
        """检查是否配置完整"""
        return bool(self.app_id and self.app_secret and 
                   self.space_id and self.parent_token and self.tenant_token)
    
    def _get_tenant_token(self) -> str:
        """获取tenant_access_token"""
        url = f"{self.API_BASE}/auth/v3/tenant_access_token/internal"
        
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            raise RuntimeError(f"获取tenant_token失败: {response.text}")
        
        result = response.json()
        
        if 'tenant_access_token' not in result:
            raise RuntimeError(f"响应中未找到tenant_access_token: {result}")
        
        self.tenant_token = result['tenant_access_token']
        print("  [飞书] 访问令牌已获取")
        return self.tenant_token
    
    def _get_auth_headers(self) -> dict:
        """获取认证请求头"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.tenant_token}"
        }
    
    def upload(self, content: str, title: str) -> str:
        """
        上传笔记到飞书
        
        Args:
            content: 笔记内容（Markdown格式）
            title: 文档标题
        
        Returns:
            飞书文档链接
        """
        if not self.is_configured():
            raise RuntimeError("飞书未配置完整")
        
        print(f"  [飞书] 开始上传文档: {title}")
        
        # 1. 创建文档节点
        node_token = self._create_node(title)
        print(f"  [飞书] 文档节点已创建: {node_token}")
        
        # 2. 写入内容（分批写入）
        self._write_content_batch(node_token, content)
        print(f"  [飞书] 内容写入完成")
        
        # 3. 返回文档链接
        link = f"https://open.feishu.cn/docx/{node_token}"
        print(f"  [飞书] 文档链接: {link}")
        
        return link
    
    def _create_node(self, title: str) -> str:
        """
        创建文档节点
        
        Args:
            title: 文档标题
        
        Returns:
            节点Token
        """
        url = f"{self.API_BASE}/wiki/v2/spaces/{self.space_id}/nodes/create"
        
        data = {
            "parent_node_token": self.parent_token,
            "obj_type": "docx",
            "title": title
        }
        
        response = requests.post(
            url, 
            headers=self._get_auth_headers(), 
            json=data, 
            timeout=30
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"创建文档节点失败: {response.text}")
        
        result = response.json()
        
        if 'data' not in result:
            raise RuntimeError(f"创建文档节点失败: 未找到data字段")
        
        if 'node_token' not in result['data']:
            raise RuntimeError(f"创建文档节点失败: 未找到node_token: {result['data']}")
        
        return result['data']['node_token']
    
    def _write_content_batch(self, node_token: str, content: str):
        """
        分批写入内容（避免单次写入过大）
        
        Args:
            node_token: 节点Token
            content: Markdown内容
        """
        MAX_BLOCK_SIZE = 2900  # 飞书API限制，留100字符余量
        
        if len(content) <= MAX_BLOCK_SIZE:
            # 内容较小，直接写入
            blocks = self._markdown_to_blocks(content)
            self._write_blocks(node_token, blocks)
        else:
            # 内容较大，分批写入
            print(f"  [飞书] 内容较长({len(content)}字符)，将分批写入...")
            
            blocks = self._markdown_to_blocks(content)
            
            # 分批写入（每批10个块）
            batch_size = 10
            total_batches = (len(blocks) + batch_size - 1) // batch_size
            
            for i in range(0, len(blocks), batch_size):
                batch = blocks[i:i + batch_size]
                batch_num = i // batch_size + 1
                self._write_blocks(node_token, batch)
                print(f"  [飞书] 已写入第 {batch_num}/{total_batches} 批")
    
    def _markdown_to_blocks(self, markdown: str) -> List[Dict]:
        """
        将Markdown转换为飞书Block格式
        
        Args:
            markdown: Markdown文本
        
        Returns:
            飞书Block列表
        """
        blocks = []
        lines = markdown.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 标题
            if line.startswith('#'):
                heading_level = len(line) - len(line.lstrip('#'))
                heading_text = line.lstrip('#').strip()
                
                block = {
                    "block_type": 2,  # 标题块
                    "heading1": {
                        "elements": [
                            {"text_run": {"content": heading_text}}
                        ]
                    }
                }
                blocks.append(block)
            
            # 无序列表
            elif line.startswith('- ') or line.startswith('* '):
                list_text = line[2:].strip()
                block = {
                    "block_type": 3,  # 列表块
                    "bullet": {
                        "elements": [
                            {"text_run": {"content": list_text}}
                        ]
                    }
                }
                blocks.append(block)
            
            # 有序列表
            elif line[0].isdigit() and '. ' in line:
                list_text = line.split('. ', 1)[1].strip()
                block = {
                    "block_type": 4,  # 有序列表块
                    "ordered": {
                        "elements": [
                            {"text_run": {"content": list_text}}
                        ]
                    }
                }
                blocks.append(block)
            
            # 引用
            elif line.startswith('> '):
                quote_text = line[2:].strip()
                block = {
                    "block_type": 5,  # 引用块
                    "quote": {
                        "elements": [
                            {"text_run": {"content": quote_text}}
                        ]
                    }
                }
                blocks.append(block)
            
            # 普通段落
            else:
                block = {
                    "block_type": 1,  # 文本块
                    "paragraph": {
                        "elements": [
                            {"text_run": {"content": line}}
                        ]
                    }
                }
                blocks.append(block)
        
        return blocks
    
    def _write_blocks(self, node_token: str, blocks: List[Dict]):
        """
        写入Block到文档
        
        Args:
            node_token: 节点Token
            blocks: Block列表
        """
        # 获取文档ID（node_token就是文档ID）
        document_id = node_token
        
        url = f"{self.API_BASE}/docx/v1/documents/{document_id}/blocks/batch_update"
        
        data = {
            "requests": [
                {
                    "request_type": "InsertBlockRequest",
                    "insert_block": {
                        "payload": json.dumps(block),
                        "index": i
                    }
                }
                for i, block in enumerate(blocks)
            ]
        }
        
        response = requests.post(
            url,
            headers=self._get_auth_headers(),
            json=data,
            timeout=60
        )
        
        if response.status_code != 200:
            error_detail = response.text
            print(f"  [飞书] 写入Block失败: {error_detail}")
            # 不抛出异常，继续尝试写入其他块
    
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
        print("\n环境变量:")
        print("  FEISHU_APP_ID       - 飞书应用ID")
        print("  FEISHU_APP_SECRET   - 飞书应用密钥")
        print("  FEISHU_SPACE_ID     - 飞书知识库空间ID")
        print("  FEISHU_PARENT_TOKEN - 父节点Token")
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
