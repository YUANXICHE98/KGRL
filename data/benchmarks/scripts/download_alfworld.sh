#!/bin/bash

# ALFWorld数据集下载脚本
# 官方仓库: https://github.com/alfworld/alfworld

set -e

echo "🚀 开始下载ALFWorld数据集..."

# 设置目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARKS_DIR="$(dirname "$SCRIPT_DIR")"
ALFWORLD_DIR="$BENCHMARKS_DIR/alfworld"

# 创建目录
mkdir -p "$ALFWORLD_DIR"
cd "$ALFWORLD_DIR"

# 检查是否已经下载
if [ -d "alfworld" ]; then
    echo "⚠️  ALFWorld已存在，跳过下载"
    exit 0
fi

# 克隆仓库
echo "📥 克隆ALFWorld仓库..."
git clone https://github.com/alfworld/alfworld.git

# 进入目录
cd alfworld

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
echo "🐍 检测到Python版本: $python_version"

if [[ "$python_version" != "unknown" && "$python_version" < "3.9" ]]; then
    echo "❌ ALFWorld需要Python 3.9+，当前版本: $python_version"
    exit 1
fi

# 安装依赖
echo "📦 安装ALFWorld依赖..."
pip install -e .[full] || pip install -e .

# 设置数据目录
export ALFWORLD_DATA="$ALFWORLD_DIR/data"
mkdir -p "$ALFWORLD_DATA"

# 下载数据文件
echo "📊 下载ALFWorld数据文件..."
alfworld-download || python scripts/alfworld-download || echo "⚠️  数据下载可能需要手动执行"

# 创建符号链接便于访问
cd "$BENCHMARKS_DIR"
ln -sf alfworld/data processed_alfworld 2>/dev/null || true

echo "✅ ALFWorld数据集下载完成！"
echo "📁 仓库位置: $ALFWORLD_DIR/alfworld"
echo "📁 数据位置: $ALFWORLD_DATA"
echo "🎮 测试命令: alfworld-play-tw"
echo "🎉 ALFWorld设置完成！"
