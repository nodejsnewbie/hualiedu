#!/bin/bash
# 清理 Hypothesis 测试生成的随机目录
#
# 这些目录是由 Hypothesis 属性测试自动生成的，用于测试路径处理功能。
# 现在已经配置 Hypothesis 使用系统临时目录，这些目录不应该再被创建。
#
# 清理的目录类型：
# 1. 单字符目录（如 0/, A/）- Hypothesis 生成的随机目录
# 2. 包含控制字符的目录（如 0ñ\x04）- 测试代码 bug 产生的目录
# 3. 特定测试课程目录（如 其他课程/, 数据结构/）
#
# 使用方法：
#   ./scripts/cleanup_test_directories.sh
#   或
#   make clean-test-dirs

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始清理测试生成的随机目录...${NC}"
echo ""

# 计数器
DELETED_COUNT=0
SKIPPED_COUNT=0

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "项目根目录: $PROJECT_ROOT"
echo ""

# 定义要保留的目录（白名单）
KEEP_DIRS=(
    ".git"
    ".github"
    ".kiro"
    ".venv"
    ".vscode"
    ".idea"
    ".pytest_cache"
    ".hypothesis"
    "__pycache__"
    "docs"
    "grading"
    "hualiEdu"
    "toolbox"
    "templates"
    "static"
    "staticfiles"
    "media"
    "logs"
    "scripts"
    "tests"
    "htmlcov"
    "node_modules"
    "testteacher_数据结构仓库"
)

# 定义要删除的目录模式
DELETE_PATTERNS=(
    # 单字符目录
    "^[0-9]$"
    "^[A-Za-z]$"
    # 特殊字符目录（非 ASCII）
    "^[^A-Za-z0-9._-]"
    # 包含控制字符的目录（如 0ñ\x04）
    "[\x00-\x1F\x7F-\x9F]"
    # 测试课程目录
    "^其他课程$"
    "^数据结构$"
    "^算法设计$"
    "^Data Structures$"
)

# 函数：检查目录是否在白名单中
is_in_whitelist() {
    local dir="$1"
    for keep in "${KEEP_DIRS[@]}"; do
        if [ "$dir" = "$keep" ]; then
            return 0
        fi
    done
    return 1
}

# 函数：检查目录是否匹配删除模式
should_delete() {
    local dir="$1"
    for pattern in "${DELETE_PATTERNS[@]}"; do
        if echo "$dir" | grep -qE "$pattern"; then
            return 0
        fi
    done
    return 1
}

# 遍历根目录下的所有目录
for dir in */; do
    # 移除尾部斜杠
    dir="${dir%/}"
    
    # 跳过隐藏目录（以 . 开头）
    if [[ "$dir" == .* ]]; then
        continue
    fi
    
    # 检查是否在白名单中
    if is_in_whitelist "$dir"; then
        continue
    fi
    
    # 检查是否应该删除
    if should_delete "$dir"; then
        echo -e "${YELLOW}删除目录: $dir${NC}"
        rm -rf "$dir"
        ((DELETED_COUNT++))
    else
        echo -e "${GREEN}保留目录: $dir${NC}"
        ((SKIPPED_COUNT++))
    fi
done

echo ""
echo -e "${GREEN}清理完成！${NC}"
echo -e "删除目录数: ${RED}$DELETED_COUNT${NC}"
echo -e "保留目录数: ${GREEN}$SKIPPED_COUNT${NC}"
echo ""

# 清理 .hypothesis 目录（如果存在）
if [ -d ".hypothesis" ]; then
    echo -e "${YELLOW}清理 .hypothesis 目录...${NC}"
    rm -rf .hypothesis
    echo -e "${GREEN}已删除 .hypothesis 目录${NC}"
    echo ""
fi

# 提示
echo -e "${YELLOW}提示：${NC}"
echo "1. 这些目录是由 Hypothesis 属性测试生成的"
echo "2. 现在已配置 Hypothesis 使用系统临时目录"
echo "3. 如果这些目录再次出现，请检查测试配置"
echo "4. 参考文档: docs/HYPOTHESIS_TESTING.md"
echo ""
