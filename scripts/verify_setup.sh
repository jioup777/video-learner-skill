#!/bin/bash
# Video Learner Skill - 验证脚本
# 验证所有修改是否正确

set -e

SKILL_DIR="$HOME/.npm-global/lib/node_modules/openclaw/skills/video-learner"
SCRIPTS_DIR="$SKILL_DIR/scripts"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_step() { echo -e "${BLUE}[步骤]${NC} $1"; }

echo "========================================"
echo "  Video Learner Skill 验证"
echo "========================================"
echo ""

# 1. 检查文件是否存在
log_step "检查新增文件..."
FILES=(
    "scripts/aliyun_asr.py"
    "scripts/asr_router.py"
    "scripts/process_douyin.sh"
    "scripts/test_asr.sh"
    "ASR_GUIDE.md"
    ".env.example"
)

for file in "${FILES[@]}"; do
    if [[ -f "$SKILL_DIR/$file" ]]; then
        log_info "$file 存在"
    else
        log_error "$file 不存在"
        exit 1
    fi
done

echo ""

# 2. 检查文件权限
log_step "检查脚本权限..."
SCRIPTS=(
    "aliyun_asr.py"
    "asr_router.py"
    "process_douyin.sh"
    "test_asr.sh"
    "video_with_feishu.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [[ -x "$SCRIPTS_DIR/$script" ]]; then
        log_info "$script 可执行"
    else
        log_error "$script 不可执行"
        chmod +x "$SCRIPTS_DIR/$script"
        log_warn "已修复 $script 权限"
    fi
done

echo ""

# 3. 检查 Python 模块
log_step "检查 Python 模块..."
cd "$SCRIPTS_DIR"

# 检查 requests
if python3 -c "import requests" 2>/dev/null; then
    log_info "requests 模块已安装"
else
    log_error "requests 模块未安装"
    log_info "请运行: pip install requests"
    exit 1
fi

# 检查 aliyun_asr 模块
if python3 -c "import sys; sys.path.insert(0, '.'); from aliyun_asr import AliyunASR" 2>/dev/null; then
    log_info "aliyun_asr 模块加载成功"
else
    log_error "aliyun_asr 模块加载失败"
    exit 1
fi

# 检查 asr_router 模块
if python3 asr_router.py --help > /dev/null 2>&1; then
    log_info "asr_router.py 命令行正常"
else
    log_error "asr_router.py 命令行异常"
    exit 1
fi

echo ""

# 4. 检查环境变量配置
log_step "检查环境变量..."
if [[ -n "$ALIYUN_ASR_API_KEY" ]]; then
    log_info "ALIYUN_ASR_API_KEY 已设置 (${ALIYUN_ASR_API_KEY:0:10}...)"
else
    log_warn "ALIYUN_ASR_API_KEY 未设置（将使用默认值）"
fi

if [[ -n "$ASR_ENGINE" ]]; then
    log_info "ASR_ENGINE = $ASR_ENGINE"
else
    log_info "ASR_ENGINE 未设置（默认: aliyun）"
fi

if [[ -n "$ASR_MODEL" ]]; then
    log_info "ASR_MODEL = $ASR_MODEL"
else
    log_info "ASR_MODEL 未设置（默认: fun-asr-mtl）"
fi

echo ""

# 5. 检查修改的文件
log_step "检查修改的文件..."

# 检查 video_with_feishu.sh 是否包含 ASR 路由器调用
if grep -q "asr_router.py" "$SCRIPTS_DIR/video_with_feishu.sh"; then
    log_info "video_with_feishu.sh 已更新（包含 ASR 路由器）"
else
    log_error "video_with_feishu.sh 未更新"
    exit 1
fi

# 检查 .env.example 是否包含 ASR 配置
if grep -q "ALIYUN_ASR_API_KEY" "$SKILL_DIR/.env.example"; then
    log_info ".env.example 已更新（包含 ASR 配置）"
else
    log_error ".env.example 未更新"
    exit 1
fi

# 检查 SKILL.md 是否包含 ASR 配置
if grep -q "阿里云 ASR" "$SKILL_DIR/SKILL.md"; then
    log_info "SKILL.md 已更新（包含 ASR 说明）"
else
    log_error "SKILL.md 未更新"
    exit 1
fi

echo ""

# 6. 语法检查
log_step "检查脚本语法..."

# 检查 Python 语法
if python3 -m py_compile "$SCRIPTS_DIR/aliyun_asr.py" 2>/dev/null; then
    log_info "aliyun_asr.py 语法正确"
else
    log_error "aliyun_asr.py 语法错误"
    exit 1
fi

if python3 -m py_compile "$SCRIPTS_DIR/asr_router.py" 2>/dev/null; then
    log_info "asr_router.py 语法正确"
else
    log_error "asr_router.py 语法错误"
    exit 1
fi

# 检查 Shell 脚本语法
if bash -n "$SCRIPTS_DIR/process_douyin.sh" 2>/dev/null; then
    log_info "process_douyin.sh 语法正确"
else
    log_error "process_douyin.sh 语法错误"
    exit 1
fi

if bash -n "$SCRIPTS_DIR/test_asr.sh" 2>/dev/null; then
    log_info "test_asr.sh 语法正确"
else
    log_error "test_asr.sh 语法错误"
    exit 1
fi

if bash -n "$SCRIPTS_DIR/video_with_feishu.sh" 2>/dev/null; then
    log_info "video_with_feishu.sh 语法正确"
else
    log_error "video_with_feishu.sh 语法错误"
    exit 1
fi

echo ""

# 7. 总结
echo "========================================"
echo -e "${GREEN}  ✅ 所有验证通过${NC}"
echo "========================================"
echo ""
echo "文件统计:"
echo "  - 新增文件: 5 个"
echo "  - 修改文件: 3 个"
echo "  - 脚本文件: 5 个"
echo ""
echo "功能列表:"
echo "  ✓ 阿里云 ASR 集成（模型: fun-asr-mtl）"
echo "  ✓ ASR 路由器（支持阿里云/Whisper）"
echo "  ✓ 抖音视频处理脚本"
echo "  ✓ ASR 测试脚本"
echo "  ✓ 完整的文档和配置指南"
echo ""
echo "下一步:"
echo "  1. 设置环境变量: export ALIYUN_ASR_API_KEY='your_aliyun_api_key'"
echo "  2. 运行测试: ./scripts/test_asr.sh"
echo "  3. 处理视频: ./scripts/video_with_feishu.sh <视频链接>"
echo ""
