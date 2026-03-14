#!/bin/bash
# 抖音视频学习助手 - 完整流程
# 功能：抖音视频链接 → 音频下载 → ASR 转录 → 笔记生成 → 飞书上传 → 清理文件

set -e

# ========== 配置 ==========
WORKSPACE="/home/ubuntu/.openclaw/workspace-video-learner"
OUTPUT_DIR="${WORKSPACE}/output"
TMP_DIR="/tmp"
SCRIPT_DIR="${WORKSPACE}/scripts"

# Feishu 配置（从环境变量读取，或手动配置）
FEISHU_SPACE_ID="${FEISHU_SPACE_ID:-YOUR_SPACE_ID}"
FEISHU_PARENT_TOKEN="${FEISHU_PARENT_TOKEN:-YOUR_PARENT_NODE_TOKEN}"

# ASR 配置
ASR_ENGINE="${ASR_ENGINE:-aliyun}"
ALIYUN_ASR_API_KEY="${ALIYUN_ASR_API_KEY:-your_aliyun_api_key}"
ASR_MODEL="${ASR_MODEL:-fun-asr-mtl}"
WHISPER_MODEL="${WHISPER_MODEL:-base}"

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

# ========== 主处理流程 ==========
process_douyin() {
    local video_url=$1
    local start_time=$(date +%s)

    if [[ -z "$video_url" ]]; then
        log_error "❌ 请提供抖音视频链接"
        return 1
    fi

    echo "" >&2
    echo "🎵 开始处理抖音视频" >&2
    echo "========================================" >&2

    # 1. 下载音频
    log_step "步骤 1/5: 下载抖音音频..."

    local output="${TMP_DIR}/douyin_%(id)s.%(ext)s"

    # 使用 yt-dlp 下载抖音视频音频
    yt-dlp -f "bestaudio" -o "$output" "$video_url" > /dev/null 2>&1

    local audio_file=$(ls -t "${TMP_DIR}/douyin_"*.* 2>/dev/null | grep -v '\.txt$' | head -1)

    if [[ -z "$audio_file" ]]; then
        log_error "❌ 音频下载失败"
        return 1
    fi

    local video_id=$(basename "$audio_file" | grep -oP 'douyin_\K\w+')
    local platform="douyin"

    log_info "✓ 音频已下载: $(basename "$audio_file") ($(du -h "$audio_file" | cut -f1))"

    # 2. 语音转录（支持阿里云 ASR 和 Whisper）
    log_step "步骤 2/5: 语音转录..."

    local transcript_file="${TMP_DIR}/douyin_${video_id}.txt"

    # 激活 Python 虚拟环境
    source /home/ubuntu/.openclaw/venv/bin/activate > /dev/null 2>&1

    # 使用 ASR 路由器进行转录
    if [[ "$ASR_ENGINE" == "aliyun" ]]; then
        log_info "使用阿里云 ASR (模型: $ASR_MODEL)..."
        
        python3 "${SCRIPT_DIR}/asr_router.py" \
            --engine aliyun \
            --api-key "$ALIYUN_ASR_API_KEY" \
            --model "$ASR_MODEL" \
            --timeout 60 \
            --output "$transcript_file" \
            "$audio_file" 2>&1 | grep -E '(✓|❌|错误)' || true
    else
        log_info "使用本地 Whisper (模型: $WHISPER_MODEL)..."
        
        python3 "${SCRIPT_DIR}/asr_router.py" \
            --engine whisper \
            --whisper-model "$WHISPER_MODEL" \
            --output "$transcript_file" \
            "$audio_file" 2>&1 | grep -E '(✓|❌|错误)' || true
    fi

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
        video_title="抖音视频 ${video_id}"
    fi

    log_info "✓ 视频标题: $video_title"

    # 4. 生成笔记（支持 smart 和 glm 两种引擎）
    log_step "步骤 4/5: 生成学习笔记..."

    local note_file="${OUTPUT_DIR}/douyin_${video_id}_note.md"

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
        local final_note_file="${OUTPUT_DIR}/douyin_${video_id}_note.md"
        mv "$note_file" "$final_note_file"
        note_file="$final_note_file"
    fi

    log_info "✓ 笔记已生成: $(basename "$note_file") ($(du -h "$note_file" | cut -f1))"

    # 5. 上传到飞书
    log_step "步骤 5/6: 上传到飞书知识库..."

    # 读取笔记内容
    local note_content=$(cat "$note_file")

    # 5.1 创建文档节点
    local create_output=$(feishu_wiki action=create space_id="$FEISHU_SPACE_ID" parent_node_token="$FEISHU_PARENT_TOKEN" title="$video_title" obj_type=docx 2>&1)

    # 提取 doc_token（从返回中查找）
    local doc_token=$(echo "$create_output" | grep -oP 'node_token:\s*\K\S+' | head -1)

    if [[ -z "$doc_token" ]]; then
        log_warn "⚠️  飞书文档节点创建失败或无法提取 doc_token"
        log_warn "输出: $create_output"
    else
        log_info "✓ 飞书文档节点已创建: $doc_token"

        # 5.2 写入内容
        if feishu_doc action=write doc_token="$doc_token" content="$note_content" 2>&1 | grep -q "成功\|成功写入\|文档已更新"; then
            log_info "✓ 笔记内容已写入"
        else
            log_warn "⚠️  笔记内容写入可能失败"
        fi

        # 5.3 返回文档链接
        local feishu_link="https://vicyrpffceo.feishu.cn/wiki/$doc_token"
        log_info "✓ 飞书文档链接: $feishu_link"

        # 保存链接到文件
        echo "$feishu_link" > "${note_file}.link"
    fi

    # 6. 清理临时文件
    log_step "步骤 6/6: 清理临时文件..."

    # 保留转录文件和笔记，删除音频文件
    rm -f "$audio_file" 2>/dev/null || true

    log_info "✓ 临时文件清理完成"

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "" >&2
    echo "========================================" >&2
    echo "  ✅ 抖音视频处理完成" >&2
    echo "========================================" >&2
    echo "  视频：抖音 ${video_id}" >&2
    echo "  耗时：${duration} 秒" >&2
    echo "  笔记：$note_file" >&2
    echo "========================================" >&2

    # 返回笔记文件路径
    echo "$note_file"
}

# ========== 入口 ==========
main() {
    if [[ $# -eq 0 ]]; then
        log_error "用法：$0 <抖音视频链接>"
        echo ""
        echo "示例:"
        echo "  $0 https://www.douyin.com/video/1234567890"
        echo ""
        echo "环境变量配置:"
        echo "  ASR_ENGINE          - ASR 引擎（aliyun/whisper，默认：aliyun）"
        echo "  ALIYUN_ASR_API_KEY  - 阿里云 API Key"
        echo "  ASR_MODEL           - ASR 模型名称（默认：fun-asr-mtl）"
        echo "  WHISPER_MODEL       - Whisper 模型（默认：base）"
        exit 1
    fi

    process_douyin "$1"
}

main "$@"
