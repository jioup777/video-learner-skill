#!/bin/bash
# 飞书文档上传工具
# 将笔记上传到飞书知识库（完整流程）

set -e

# 配置（从环境变量读取）
FEISHU_SPACE_ID="${FEISHU_SPACE_ID:-YOUR_SPACE_ID}"
FEISHU_PARENT_TOKEN="${FEISHU_PARENT_TOKEN:-YOUR_PARENT_NODE_TOKEN}"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 上传到飞书
upload_to_feishu() {
    local note_file=$1
    local video_title=$2

    log_step "开始上传到飞书知识库..."

    # 检查笔记文件
    if [[ ! -f "$note_file" ]]; then
        log_error "笔记文件不存在: $note_file"
        exit 1
    fi

    # 检查配置
    if [[ "$FEISHU_SPACE_ID" == "YOUR_SPACE_ID" || "$FEISHU_PARENT_TOKEN" == "YOUR_PARENT_NODE_TOKEN" ]]; then
        log_error "飞书配置未设置，请设置环境变量:"
        log_error "  export FEISHU_SPACE_ID='your_space_id'"
        log_error "  export FEISHU_PARENT_TOKEN='your_parent_token'"
        exit 1
    fi

    # 读取笔记内容
    local note_content=$(cat "$note_file")

    log_info "📝 笔记内容长度: ${#note_content} 字符"
    log_info "📹 视频标题: $video_title"
    log_info "📚 知识库空间 ID: $FEISHU_SPACE_ID"
    log_info "📂 父节点 Token: $FEISHU_PARENT_TOKEN"
    echo ""

    # 步骤 1: 创建文档节点
    log_step "1/3: 创建飞书文档节点..."

    local create_output=$(feishu_wiki action=create \
        space_id="$FEISHU_SPACE_ID" \
        parent_node_token="$FEISHU_PARENT_TOKEN" \
        title="$video_title" \
        obj_type=docx 2>&1)

    # 提取 node_token（从返回中查找）
    local node_token=$(echo "$create_output" | grep -oP 'node_token:\s*\K\S+' | head -1)

    if [[ -z "$node_token" ]]; then
        log_error "❌ 飞书文档节点创建失败"
        log_error "返回内容: $create_output"
        exit 1
    fi

    log_info "✓ 文档节点已创建: $node_token"
    echo ""

    # 步骤 2: 写入内容
    log_step "2/3: 写入笔记内容..."

    if feishu_doc action=write doc_token="$node_token" content="$note_content" 2>&1 | grep -q "成功\|成功写入\|文档已更新\|write.*success"; then
        log_info "✓ 笔记内容已写入"
    else
        log_warn "⚠️  笔记内容写入可能失败（请检查飞书文档）"
    fi
    echo ""

    # 步骤 3: 返回文档链接
    log_step "3/3: 生成文档链接..."

    local feishu_link="https://vicyrpffceo.feishu.cn/wiki/$node_token"
    log_info "✓ 飞书文档链接: $feishu_link"

    # 保存链接到文件
    echo "$feishu_link" > "${note_file}.link"
    echo ""

    # 输出结果
    echo "========================================"
    echo "  ✅ 飞书上传成功"
    echo "========================================"
    echo "  文档链接: $feishu_link"
    echo "  节点 Token: $node_token"
    echo "  笔记文件: $note_file"
    echo "========================================"

    # 返回链接（供调用者使用）
    echo "$feishu_link"
}

# 主函数
main() {
    if [[ $# -lt 2 ]]; then
        echo "用法: $0 <笔记文件> <视频标题>"
        echo ""
        echo "环境变量:"
        echo "  FEISHU_SPACE_ID      - 飞书知识库空间 ID"
        echo "  FEISHU_PARENT_TOKEN  - 飞书父节点 Token"
        echo ""
        echo "示例:"
        echo "  export FEISHU_SPACE_ID='your_space_id'"
        echo "  export FEISHU_PARENT_TOKEN='your_parent_token'"
        echo "  $0 /tmp/note.md '视频标题'"
        exit 1
    fi

    local note_file=$1
    local video_title=$2

    upload_to_feishu "$note_file" "$video_title"
}

main "$@"
