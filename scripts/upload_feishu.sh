#!/bin/bash
# 飞书文档上传工具
# 将笔记上传到飞书知识库

set -e

# 配置（从环境变量读取，或手动配置）
FEISHU_SPACE_ID="${FEISHU_SPACE_ID:-YOUR_SPACE_ID}"
FEISHU_PARENT_TOKEN="${FEISHU_PARENT_TOKEN:-YOUR_PARENT_NODE_TOKEN}"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 上传到飞书
upload_to_feishu() {
    local note_file=$1
    local video_title=$2

    log_step "开始上传到飞书..."

    if [[ ! -f "$note_file" ]]; then
        echo "❌ 笔记文件不存在: $note_file"
        exit 1
    fi

    # 读取笔记内容
    local note_content=$(cat "$note_file")

    log_info "📝 笔记内容长度: ${#note_content} 字符"
    log_info "📹 视频标题: $video_title"

    # 调用 OpenClaw 工具（这里需要在 OpenClaw 主流程中调用）
    # 输出上传任务信息
    echo "飞书上传任务信息:"
    echo "  - 笔记文件: $note_file"
    echo "  - 视频标题: $video_title"
    echo "  - 知识库空间 ID: $FEISHU_SPACE_ID"
    echo "  - 父节点 Token: $FEISHU_PARENT_TOKEN"

    log_info "✓ 飞书上传任务已创建"
    log_info "  请在 OpenClaw 主流程中调用 feishu_wiki 和 feishu_doc 工具完成上传"

    echo "$note_file"
}

# 主函数
main() {
    if [[ $# -lt 2 ]]; then
        echo "用法: $0 <笔记文件> <视频标题>"
        exit 1
    fi

    local note_file=$1
    local video_title=$2

    upload_to_feishu "$note_file" "$video_title"
}

main "$@"
