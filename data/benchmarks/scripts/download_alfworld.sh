#!/bin/bash

# ALFWorld数据集下载脚本
# 官方仓库: https://github.com/alfworld/alfworld

set -e

echo "🚀 开始下载ALFWorld数据集..."

# 创建目录
mkdir -p ../alfworld
cd ../alfworld

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

# 安装依赖
echo "📦 安装ALFWorld依赖..."
pip install -e .

# 下载数据
echo "💾 下载ALFWorld数据..."
python -m alfworld.agents.environment.alfred_thor_env --setup

echo "✅ ALFWorld数据集下载完成！"
echo "📍 数据位置: $(pwd)"

# 创建符号链接到processed目录
cd ../../processed
ln -sf ../alfworld/alfworld alfworld_raw
echo "🔗 创建符号链接到processed目录"

echo "🎉 ALFWorld设置完成！"
