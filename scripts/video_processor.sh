#!/bin/bash
# 视频学习助手 - 完整处理流程 (最终版)
# 功能：视频链接 → 音频下载 → Whisper 转录 → 笔记生成 → 飞书上传播 → 清理文件

set -e

# ========== 配置 ==========
WORKSPACE="/home/ubuntu/.openclaw/workspace-video-learner"
OUTPUT_DIR="${WORKSPACE}/output"
TMP_DIR="/tmp"
SCRIPT_DIR="${WORKSPACE}/scripts"

# B站 Cookies（可选）
BILIBILI_COOKIES="${WORKSPACE}/cookies/bilibili_cookies.txt"

# 笔记生成引擎选择（smart 或 glm，默认 glm）
NOTE_ENGINE="${NOTE_ENGINE:-glm}"

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

# 初始化目录
init_dirs() {
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$(dirname "$BILIBILI_COOKIES")"
}

# ========== 视频识别 ==========
detect_platform() {
    local url=$1
    if [[ $url =~ bilibili\.com ]]; then
        echo "bilibili"
        echo "$url" | grep -oP 'BV[a-zA-Z0-9]+' || echo "unknown"
    elif [[ $url =~ (youtube\.com|youtu\.be) ]]; then
        echo "youtube"
        echo "$url" | grep -oP '(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})' | head -1 || echo "unknown"
    else
        echo "unknown"
        echo "unknown"
    fi
}

# ========== 音频下载 ==========
download_audio() {
    local platform=$1
    local video_id=$2
    local url=$3

    log_step "步骤 1/4: 下载音频..."

    local output="${TMP_DIR}/${platform}_${video_id}.%(ext)s"
    local download_cmd="yt-dlp"

    if [[ $platform == "bilibili" && -f "$BILIBILI_COOKIES" ]]; then
        download_cmd="$download_cmd --cookies $BILIBILI_COOKIES"
    fi

    $download_cmd -f "bestaudio" -o "$output" "$url" > /dev/null 2>&1

    local audio_file=$(ls -t "${TMP_DIR}/${platform}_${video_id}".* 2>/dev/null | grep -v '\.txt$' | head -1)

    if [[ -z "$audio_file" ]]; then
        log_error "音频下载失败"
        return 1
    fi

    log_info "✓ 音频已下载：$(basename "$audio_file") ($(du -h "$audio_file" | cut -f1))"
    echo "$audio_file"
}

# ========== Whisper 转录 ==========
transcribe_audio() {
    local audio_file=$1
    local platform=$2
    local video_id=$3
    local transcript_file="${TMP_DIR}/${platform}_${video_id}.txt"

    if [[ -f "$transcript_file" ]]; then
        log_info "找到已存在的转录文件：$(basename "$transcript_file")"
        local transcript_size=$(du -h "$transcript_file" | cut -f1)
        local word_count=$(wc -m < "$transcript_file")
        log_info "✓ 转录文件大小：$transcript_size (${word_count} 字符)"
        echo "$transcript_file"
        return 0
    fi

    log_step "步骤 2/4: 语音转录（Whisper）..."

    source /home/ubuntu/.openclaw/venv/bin/activate > /dev/null 2>&1

    whisper "$audio_file" \
        --language Chinese \
        --model base \
        --output_dir "$TMP_DIR" \
        --output_format txt \
        --verbose False > /dev/null 2>&1

    if [[ ! -f "$transcript_file" ]]; then
        log_error "转录失败"
        return 1
    fi

    local transcript_size=$(du -h "$transcript_file" | cut -f1)
    local word_count=$(wc -m < "$transcript_file")

    log_info "✓ 转录完成：$transcript_size (${word_count} 字符)"
    echo "$transcript_file"
}

# ========== 获取视频标题 ==========
get_video_title() {
    local platform=$1
    local video_id=$2
    local url=$3

    log_step "获取视频信息..."

    local title=$(yt-dlp --get-title "$url" 2>/dev/null | head -1)

    if [[ -z "$title" ]]; then
        title="${platform^} 视频 ${video_id}"
    fi

    log_info "✓ 视频标题：$title"
    echo "$title"
}

# ========== 生成笔记 ==========
generate_note() {
    local transcript_file=$1
    local video_title=$2
    local platform=$3
    local video_id=$4

    log_step "步骤 3/4: 生成学习笔记..."

    if [[ ! -f "$transcript_file" ]]; then
        log_error "转录文件不存在：$transcript_file"
        return 1
    fi

    local note_file

    # 选择笔记生成引擎
    if [[ "$NOTE_ENGINE" == "smart" ]]; then
        log_info "使用词频提取引擎..."
        python3 "${SCRIPT_DIR}/smart_note_generator.py" "$transcript_file" "$video_title"
        note_file="${transcript_file%.txt}_smart_note.md"
    else
        log_info "使用 GLM-4-Flash 引擎..."
        python3 "${SCRIPT_DIR}/glm_note_generator.py" "$transcript_file" "$video_title"
        note_file="${transcript_file%.txt}_glm_note.md"
    fi

    if [[ ! -f "$note_file" ]]; then
        log_error "❌ 笔记生成失败"
        return 1
    fi

    # 如果笔记不在输出目录，移动到输出目录
    if [[ ! "$note_file" =~ ^"$OUTPUT_DIR" ]]; then
        local final_note_file="${OUTPUT_DIR}/${platform}_${video_id}_note.md"
        mv "$note_file" "$final_note_file"
        note_file="$final_note_file"
    fi

    log_info "✓ 笔记已生成：$(basename "$note_file") ($(du -h "$note_file" | cut -f1))"
    echo "$note_file"
}

# ========== 清理临时文件 ==========
cleanup_temp_files() {
    local platform=$1
    local video_id=$2

    log_step "步骤 4/4: 清理临时文件..."

    find "${TMP_DIR}/${platform}_${video_id}".* \
        ! -name "*.txt" \
        ! -name "*_note.md" \
        ! -name "*.link" \
        -delete 2>/dev/null || true

    log_info "✓ 临时文件清理完成（保留转录文本和笔记）"
}

# ========== 打印汇总 ==========
print_summary() {
    local platform=$1
    local video_id=$2
    local note_file=$3
    local start_time=$4

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
}

# ========== 主函数 ==========
process_single_video() {
    local video_url=$1
    local start_time=$(date +%s)

    if [[ -z "$video_url" ]]; then
        log_error "❌ 请提供视频链接"
        return 1
    fi

    echo "" >&2
    echo "🎬 开始处理视频" >&2
    echo "========================================" >&2

    local platform_info=$(detect_platform "$video_url")
    local platform=$(echo "$platform_info" | head -1)
    local video_id=$(echo "$platform_info" | tail -1)

    if [[ $video_id == "unknown" ]]; then
        log_error "❌ 无法识别视频 ID"
        return 1
    fi

    log_info "平台：${platform^} | 视频 ID: $video_id"
    echo "" >&2

    local audio_file=$(download_audio "$platform" "$video_id" "$video_url")
    if [[ -z "$audio_file" ]]; then
        return 1
    fi

    local transcript_file=$(transcribe_audio "$audio_file" "$platform" "$video_id")
    if [[ -z "$transcript_file" ]]; then
        return 1
    fi

    local video_title=$(get_video_title "$platform" "$video_id" "$video_url")

    local note_file=$(generate_note "$transcript_file" "$video_title" "$platform" "$video_id")
    if [[ -z "$note_file" ]]; then
        return 1
    fi

    cleanup_temp_files "$platform" "$video_id"

    print_summary "$platform" "$video_id" "$note_file" "$start_time"

    # 输出笔记文件路径（供调用者使用）
    echo "$note_file"
}

# ========== 入口 ==========
main() {
    init_dirs

    if [[ $# -eq 0 ]]; then
        log_error "用法：$0 <视频链接>"
        echo ""
        echo "示例:"
        echo "  $0 https://www.bilibili.com/video/BVxxxxx"
        exit 1
    fi

    process_single_video "$1"
}

main "$@"
