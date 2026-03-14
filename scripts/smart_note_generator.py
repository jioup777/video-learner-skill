#!/usr/bin/env python3
"""
智能笔记生成器 v1.0
功能：从转录文本中自动提取核心观点、关键信息、实践建议、核心金句
"""

import re
import sys
import os
from collections import Counter
from datetime import datetime

def extract_keywords(text, top_n=10):
    """提取关键词"""
    # 简单的分词（提取中文词组）
    words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)

    # 过滤停用词
    stopwords = {'这个', '那个', '一个', '就是', '可以', '我们', '他们', '你们',
                 '它们', '这样', '那样', '什么', '怎么', '如何', '为什么', '因为',
                 '所以', '但是', '而且', '或者', '如果', '虽然', '那么', '的', '了',
                 '是', '在', '有', '和', '与', '要', '会', '能', '也', '都', '很',
                 '就', '这', '那', '还', '要', '又', '不', '就', '而', '但', '为'}

    filtered_words = [w for w in words if w not in stopwords and len(w) >= 2]

    # 统计词频
    word_freq = Counter(filtered_words)

    # 返回前 N 个关键词
    return [word for word, count in word_freq.most_common(top_n)]

def extract_key_sentences(text, keywords, min_length=20):
    """提取包含关键词的句子"""
    # 按句号、感叹号、问号分割
    sentences = re.split(r'[。！？\n]', text)

    # 筛选包含关键词的句子
    key_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) >= min_length:
            # 计算句子中包含的关键词数量
            keyword_count = sum(1 for keyword in keywords if keyword in sentence)
            if keyword_count >= 2:  # 至少包含 2 个关键词
                key_sentences.append(sentence)

    return key_sentences[:10]  # 返回前 10 个句子

def extract_core_points(text):
    """提取核心观点"""
    # 寻找包含"观点"、"认为"、"核心"、"关键"等词的句子
    patterns = [
        r'(核心观点|关键点|重要|主要)[是为][^。！？]{10,80}',
        r'(认为|觉得|应该|需要)[^。！？]{10,80}',
        r'第一[是为][^。！？]{10,60}',
        r'第二[是为][^。！？]{10,60}',
        r'第三[是为][^。！？]{10,60}',
    ]

    points = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        points.extend(matches)

    return points[:5]

def extract_golden_quotes(text):
    """提取核心金句（简短有力的句子）"""
    # 按句号、感叹号、问号分割
    sentences = re.split(r'[。！？\n]', text)

    # 筛选简短有力的句子（15-50 字符）
    golden_quotes = []
    for sentence in sentences:
        sentence = sentence.strip()
        if 15 <= len(sentence) <= 50:
            # 检查是否包含有意义的词汇
            if re.search(r'[\u4e00-\u9fa5]{4,}', sentence):
                golden_quotes.append(sentence)

    # 返回前 5 个金句
    return golden_quotes[:5]

def extract_practice_tips(text):
    """提取实践建议"""
    # 寻找包含"建议"、"推荐"、"可以"、"试试"等词的句子
    patterns = [
        r'建议[^。！？]{10,60}',
        r'推荐[^。！？]{10,60}',
        r'可以[^。！？]{10,60}',
        r'试试[^。！？]{10,60}',
        r'注意[^。！？]{10,60}',
    ]

    tips = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        tips.extend(matches)

    return tips[:5]

def generate_smart_note(transcript_file, video_title):
    """生成智能笔记"""

    # 读取转录文本
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript = f.read()

    print(f"📝 转录文本长度: {len(transcript)} 字符")

    # 提取关键词
    keywords = extract_keywords(transcript, top_n=15)
    print(f"🔑 提取到 {len(keywords)} 个关键词: {', '.join(keywords[:5])}...")

    # 提取关键句子
    key_sentences = extract_key_sentences(transcript, keywords)
    print(f"💡 提取到 {len(key_sentences)} 个关键句子")

    # 提取核心观点
    core_points = extract_core_points(transcript)
    print(f"⭐ 提取到 {len(core_points)} 个核心观点")

    # 提取核心金句
    golden_quotes = extract_golden_quotes(transcript)
    print(f"✨ 提取到 {len(golden_quotes)} 个核心金句")

    # 提取实践建议
    practice_tips = extract_practice_tips(transcript)
    print(f"🎯 提取到 {len(practice_tips)} 个实践建议")

    # 生成笔记
    note = f"""# {video_title}

## 📹 视频信息
- **视频标题**: {video_title}
- **处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **处理状态**: ✅ 智能提取完成
- **提取统计**: 关键词 {len(keywords)} | 核心观点 {len(core_points)} | 金句 {len(golden_quotes)}

---

## 🔑 关键词
{', '.join(keywords)}

---

## ⭐ 核心观点
"""
    if core_points:
        for i, point in enumerate(core_points, 1):
            note += f"{i}. {point}\n"
    else:
        note += "> （未提取到明确的观点，请查看关键句子）\n"

    note += "\n---\n\n## 💡 关键句子\n"
    if key_sentences:
        for i, sentence in enumerate(key_sentences[:5], 1):
            note += f"{i}. {sentence}\n"
    else:
        note += "> （未提取到关键句子）\n"

    note += "\n---\n\n## 🎯 实践建议\n"
    if practice_tips:
        for i, tip in enumerate(practice_tips, 1):
            note += f"{i}. {tip}\n"
    else:
        note += "> （未提取到明确的实践建议）\n"

    note += "\n---\n\n## ✨ 核心金句\n"
    if golden_quotes:
        for quote in golden_quotes:
            note += f'- "{quote}"\n'
    else:
        note += "> （未提取到核心金句）\n"

    note += f"""
---

## 📝 完整转录内容

```
{transcript}
```

---

*🤖 此笔记由 [视频助手](https://github.com/openclaw/openclaw) 智能生成*
*📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*📊 提取统计: 关键词 {len(keywords)} | 核心观点 {len(core_points)} | 金句 {len(golden_quotes)} | 实践建议 {len(practice_tips)}*
"""

    return note

def main():
    if len(sys.argv) < 2:
        print("用法: python3 smart_note_generator.py <转录文件路径> [视频标题]")
        sys.exit(1)

    transcript_file = sys.argv[1]
    video_title = sys.argv[2] if len(sys.argv) > 2 else "视频笔记"

    if not os.path.exists(transcript_file):
        print(f"❌ 文件不存在: {transcript_file}")
        sys.exit(1)

    print(f"🎬 开始生成智能笔记...")
    print(f"📹 视频标题: {video_title}")
    print(f"📄 转录文件: {transcript_file}")
    print()

    note = generate_smart_note(transcript_file, video_title)

    # 保存笔记
    output_file = transcript_file.replace('.txt', '_smart_note.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(note)

    print(f"\n✅ 智能笔记已生成: {output_file}")
    print(f"📊 笔记大小: {len(note)} 字符")

if __name__ == "__main__":
    main()
