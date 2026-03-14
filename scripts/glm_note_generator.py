#!/usr/bin/env python3
"""
GLM-4-Flash 笔记生成器
功能：使用 GLM-4-Flash LLM 从转录文本生成结构化学习笔记
"""

import os
import sys
import json
import time
from datetime import datetime

# GLM API 配置
GLM_API_KEY = os.getenv('GLM_API_KEY', '')
GLM_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
GLM_MODEL = 'glm-4-flash'


def count_tokens(text, model=GLM_MODEL):
    """
    估算 Token 数量
    粗略估算：中文约 1.5 字符 = 1 Token
    """
    if model.startswith('glm'):
        # GLM 模型粗略估算
        return len(text) // 1.5
    else:
        # 其他模型
        return len(text) // 4


def call_glm_api(transcript, video_title='视频笔记'):
    """
    调用 GLM-4-Flash API 生成笔记

    Args:
        transcript: 转录文本
        video_title: 视频标题

    Returns:
        (generated_text, input_tokens, output_tokens)
    """
    if not GLM_API_KEY:
        raise ValueError("GLM_API_KEY 环境变量未设置，请配置: export GLM_API_KEY='your_key'")

    # 构建提示词
    prompt = f"""你是一位专业的学习笔记整理专家。以下是视频的转录文本，请整理成结构化的学习笔记。

**视频标题**：
{video_title}

**转录文本**：
{transcript}

**输出要求**：
1. 核心主题
2. 核心观点（3-5 条）
3. 典型案例（如适用）
4. 识别方法（如适用）
5. 防骗建议（如适用）
6. 核心金句（5 句）

格式：Markdown，结构清晰，加粗关键内容。
"""

    # 估算输入 Token
    input_tokens = int(count_tokens(prompt))

    # 构建 API 请求
    headers = {
        'Authorization': f'Bearer {GLM_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': GLM_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'temperature': 0.7,
        'top_p': 0.9,
        'max_tokens': 4000
    }

    # 发送请求
    import requests
    start_time = time.time()

    try:
        response = requests.post(
            GLM_API_URL,
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise TimeoutError("GLM API 调用超时（60秒）")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"GLM API 调用失败: {str(e)}")

    elapsed = time.time() - start_time

    # 解析响应
    result = response.json()

    if 'choices' not in result or len(result['choices']) == 0:
        raise ValueError("GLM API 返回格式异常")

    generated_text = result['choices'][0]['message']['content']

    # 估算输出 Token
    output_tokens = int(count_tokens(generated_text))

    return generated_text, input_tokens, output_tokens, elapsed


def generate_smart_note(transcript_file, video_title='视频笔记'):
    """
    生成智能笔记（GLM-4-Flash）

    Args:
        transcript_file: 转录文本文件路径
        video_title: 视频标题

    Returns:
        note_content: 笔记内容
    """
    # 读取转录文本
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = f.read()

    print(f"📝 转录文本长度: {len(transcript)} 字符")
    print(f"📊 估算输入 Token: {int(count_tokens(transcript))}")

    # 调用 GLM API
    print(f"🤖 调用 GLM-4-Flash API...")
    generated_content, input_tokens, output_tokens, elapsed = call_glm_api(
        transcript, video_title
    )

    # Token 统计
    total_tokens = input_tokens + output_tokens
    print(f"✅ GLM 调用成功")
    print(f"   - 输入 Token: {input_tokens}")
    print(f"   - 输出 Token: {output_tokens}")
    print(f"   - 总计 Token: {total_tokens}")
    print(f"   - 耗时: {elapsed:.2f} 秒")

    # 生成笔记
    note_content = f"""# {video_title}

## 📹 视频信息
- **视频标题**: {video_title}
- **处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **处理状态**: ✅ AI 智能生成完成
- **生成引擎**: GLM-4-Flash
- **Token 消耗**: {total_tokens} (输入 {input_tokens} + 输出 {output_tokens})

---

{generated_content}

---

## 📝 完整转录内容

\`\`\`
{transcript}
\`\`\`

---

*🤖 此笔记由 [视频助手](https://github.com/openclaw/openclaw) 使用 GLM-4-Flash 智能生成*
*📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*📊 Token 消耗: {total_tokens} (输入 {input_tokens} + 输出 {output_tokens})*
"""

    return note_content


def main():
    if len(sys.argv) < 2:
        print("用法: python3 glm_note_generator.py <转录文件路径> [视频标题]")
        print("")
        print("环境变量:")
        print("  GLM_API_KEY  - GLM API Key (必需)")
        print("")
        print("示例:")
        print("  export GLM_API_KEY='your_key'")
        print("  python3 glm_note_generator.py /tmp/transcript.txt '视频标题'")
        sys.exit(1)

    transcript_file = sys.argv[1]
    video_title = sys.argv[2] if len(sys.argv) > 2 else "视频笔记"

    if not os.path.exists(transcript_file):
        print(f"❌ 文件不存在: {transcript_file}")
        sys.exit(1)

    if not GLM_API_KEY:
        print("❌ GLM_API_KEY 环境变量未设置")
        print("请配置: export GLM_API_KEY='your_key'")
        sys.exit(1)

    print(f"🎬 开始生成智能笔记 (GLM-4-Flash)...")
    print(f"📹 视频标题: {video_title}")
    print(f"📄 转录文件: {transcript_file}")
    print()

    try:
        note_content = generate_smart_note(transcript_file, video_title)

        # 保存笔记
        output_file = transcript_file.replace('.txt', '_glm_note.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(note_content)

        print(f"\n✅ 智能笔记已生成: {output_file}")
        print(f"📊 笔记大小: {len(note_content)} 字符")

        # 输出文件路径
        print(output_file)

    except Exception as e:
        print(f"\n❌ 笔记生成失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
