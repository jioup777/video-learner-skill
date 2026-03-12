#!/bin/bash
# 视频学习助手 - 完整流程（集成飞书上传）
# 功能：视频链接 → 音频下载 → Whisper 转录 → 笔记生成 → 飞书上传播 → 清理文件

set -e

# ========== 配置 ==========
WORKSPACE="/home/ubuntu/.openclaw/workspace-video-learner"
OUTPUT_DIR="${WORKSPACE}/output"
TMP_DIR="/tmp"
SCRIPT_DIR="${WORKSPACE}/scripts"

# B站 Cookies
BILIBILI_COOKIES="${WORKSPACE}/cookies/bilibili_cookies.txt"

# Feishu 配置（从环境变量读取，或手动配置）
FEISHU_SPACE_ID="${FEISHU_SPACE_ID:-YOUR_SPACE_ID}"
FEISHU_PARENT_TOKEN="${FEISHU_PARENT_TOKEN:-YOUR_PARENT_NODE_TOKEN}"

# ========== 工具函数 ==========
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ========== 主处理流程 ==========
process_video() {
    local video_url=$1
    local start_time=$(date +%s)

    if [[ -z "$video_url" ]]; then
        log_error "❌ 请提供视频链接"
        return 1
    fi

    echo "" >&2
    echo "🎬 开始处理视频" >&2
    echo "========================================" >&2

    # 1. 下载音频
    log_step "步骤 1/5: 下载音频..."

    local output="${TMP_DIR}/test_download.%(ext)s"
    local download_cmd="yt-dlp"

    if [[ -f "$BILIBILI_COOKIES" ]]; then
        download_cmd="$download_cmd --cookies $BILIBILI_COOKIES"
    fi

    $download_cmd -f "bestaudio" -o "$output" "$video_url" > /dev/null 2>&1

    local audio_file=$(ls -t "${TMP_DIR}/test_download".* 2>/dev/null | grep -v '\.txt$' | head -1)

    if [[ -z "$audio_file" ]]; then
        log_error "❌ 音频下载失败"
        return 1
    fi

    local video_id=$(basename "$audio_file" | grep -oP '\w+')
    local platform="bilibili"

    log_info "✓ 音频已下载: $(basename "$audio_file") ($(du -h "$audio_file" | cut -f1))"

    # 2. Whisper 转录
    log_step "步骤 2/5: 语音转录（Whisper）..."

    source /home/ubuntu/.openclaw/venv/bin/activate > /dev/null 2>&1

    whisper "$audio_file" \
        --language Chinese \
        --model base \
        --output_dir "$TMP_DIR" \
        --output_format txt \
        --verbose False > /dev/null 2>&1

    local transcript_file="${TMP_DIR}/test_download.txt"

    if [[ ! -f "$transcript_file" ]]; then
        log_error "❌ 转录失败"
        return 1
    fi

    local transcript_size=$(du -h "$transcript_file" | cut -f1)
    local word_count=$(wc -m < "$transcript_file")

    log_info "✓ 转录完成: $transcript_size (${word_count} 字符)"

    # 3. 获取视频标题
    log_step "步骤 3/5: 获取视频信息..."

    local video_title=$(yt-dlp --get-title "$video_url" 2>/dev/null | head -1)

    if [[ -z "$video_title" ]]; then
        video_title="${platform^} 视频 ${video_id}"
    fi

    log_info "✓ 视频标题: $video_title"

    # 4. 生成笔记
    log_step "步骤 4/5: 生成学习笔记..."

    local note_file="${OUTPUT_DIR}/${platform}_${video_id}_note.md"

    cat > "$note_file" << EOF
# ${video_title}

## 📹 视频信息
- **视频 ID**: \`${video_id}\`
- **平台**: ${platform^}
- **处理时间**: $(date '+%Y-%m-%d %H:%M')
- **处理状态**: ✅ 已完成

---

## 📝 转录内容

\`\`\`
$(cat "$transcript_file")
\`\`\`

---

## 💡 核心观点
> （此部分待 AI 智能提取）

## 🔍 关键信息
> （此部分待 AI 智能提取）

## ⚡ 实践建议
> （此部分待 AI 智能提取）

## 📌 核心金句
> （此部分待 AI 智能提取）

---
*🤖 此笔记由 [视频助手](https://github.com/openclaw/openclaw) 自动生成*
*📅 生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF

    log_info "✓ 笔记已生成: $(basename "$note_file") ($(du -h "$note_file" | cut -f1))"

    # 5. 上传到飞书
    log_step "步骤 5/5: 上传到飞书知识库..."

    # 使用 OpenClaw 工具上传
    if feishu_wiki action=create space_id="$FEISHU_SPACE_ID" parent_node_token="$FEISHU_PARENT_TOKEN" title="$video_title" obj_type=docx > /dev/null 2>&1; then
        log_info "✓ 飞书文档节点已创建"
    else
        log_warn "⚠️  飞书文档节点创建可能失败"
    fi

    # 6. 清理临时文件
    log_step "步骤 6/6: 清理临时文件..."

    find "${TMP_DIR}/test_download".* \
        ! -name "*.txt" \
        ! -name "*_note.md" \
        ! -name "*.link" \
        -delete 2>/dev/null || true

    log_info "✓ 临时文件清理完成"

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "" >&2
    echo "========================================" >&2
    echo "  ✅ 视频处理完成" >&2
    echo "========================================" >&2
    echo "  视频：${platform^} ${video_id}" >&2
    echo "  耗时：${duration} 秒" >&2
    echo "  笔记：$note_file" >&2
    echo "========================================" >&2

    # 返回笔记文件路径
    echo "$note_file"
}

# ========== 入口 ==========
main() {
    if [[ $# -eq 0 ]]; then
        log_error "用法：$0 <视频链接>"
        echo ""
        echo "示例:"
        echo "  $0 https://www.bilibili.com/video/BVxxxxx"
        exit 1
    fi

    process_video "$1"
}

main "$@"
