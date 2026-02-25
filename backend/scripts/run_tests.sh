#!/bin/bash
# 后端测试执行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

PYTEST="./venv/bin/pytest"

show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all         运行所有测试 (默认)"
    echo "  quick       快速测试 (跳过慢测试)"
    echo "  slow        只运行慢测试"
    echo "  timing      显示每个文件的执行时间"
    echo "  file <name> 运行指定文件的测试"
    echo "  cov         运行测试并生成覆盖率报告"
    echo "  help        显示帮助信息"
    echo ""
    echo "Examples:"
    echo "  $0              # 运行所有测试"
    echo "  $0 quick        # 快速测试"
    echo "  $0 timing       # 显示每个文件执行时间"
    echo "  $0 file auth    # 运行 test_auth.py"
}

run_all() {
    echo "🧪 运行所有测试..."
    $PYTEST tests/ -q --tb=short
}

run_quick() {
    echo "⚡ 快速测试 (跳过慢测试)..."
    $PYTEST tests/ -m "not slow" -q --tb=short
}

run_slow() {
    echo "🐢 运行慢测试..."
    $PYTEST tests/ -m "slow" -q --tb=short
}

run_timing() {
    echo "⏱️  每个测试文件执行时间:"
    echo "----------------------------------------"
    for f in tests/test_*.py; do
        filename=$(basename "$f")
        result=$($PYTEST "$f" -q --tb=no 2>&1 | grep -E "passed|skipped|failed" | head -1)
        printf "%-30s %s\n" "$filename:" "$result"
    done
    echo "----------------------------------------"
}

run_file() {
    if [ -z "$1" ]; then
        echo "❌ 请指定测试文件名"
        echo "用法: $0 file <name>"
        echo "示例: $0 file auth  # 运行 test_auth.py"
        exit 1
    fi
    file="tests/test_$1.py"
    if [ ! -f "$file" ]; then
        echo "❌ 文件不存在: $file"
        echo "可用的测试文件:"
        ls tests/test_*.py | xargs -n1 basename | sed 's/test_/  /; s/.py//'
        exit 1
    fi
    echo "🧪 运行 $file..."
    $PYTEST "$file" -v --tb=short
}

run_coverage() {
    echo "📊 运行测试并生成覆盖率报告..."
    $PYTEST tests/ --cov=app --cov-report=html --cov-report=term-missing -q
    echo ""
    echo "覆盖率报告已生成: htmlcov/index.html"
}

case "${1:-all}" in
    all)
        run_all
        ;;
    quick)
        run_quick
        ;;
    slow)
        run_slow
        ;;
    timing)
        run_timing
        ;;
    file)
        run_file "$2"
        ;;
    cov|coverage)
        run_coverage
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $1"
        show_help
        exit 1
        ;;
esac
