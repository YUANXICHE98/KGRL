#!/bin/bash

# TextWorld数据集下载脚本
# 官方仓库: https://github.com/microsoft/TextWorld

set -e

echo "🚀 开始下载TextWorld数据集..."

# 创建目录
mkdir -p ../textworld
cd ../textworld

# 检查是否已经下载
if [ -d "TextWorld" ]; then
    echo "⚠️  TextWorld已存在，跳过下载"
    exit 0
fi

# 克隆仓库
echo "📥 克隆TextWorld仓库..."
git clone https://github.com/microsoft/TextWorld.git

# 进入目录
cd TextWorld

# 安装依赖
echo "📦 安装TextWorld依赖..."
pip install -e .

# 下载预构建的游戏
echo "💾 下载TextWorld游戏数据..."
mkdir -p games
cd games

# 下载一些示例游戏
echo "📥 下载示例游戏..."
wget -q https://github.com/microsoft/TextWorld/releases/download/v1.0.0/tw-simple-games.zip
unzip -q tw-simple-games.zip
rm tw-simple-games.zip

# 下载更复杂的游戏
wget -q https://github.com/microsoft/TextWorld/releases/download/v1.0.0/tw-cooking-games.zip
unzip -q tw-cooking-games.zip
rm tw-cooking-games.zip

echo "✅ TextWorld数据集下载完成！"
echo "📍 数据位置: $(pwd)"

# 创建符号链接到processed目录
cd ../../../processed
ln -sf ../textworld/TextWorld textworld_raw
echo "🔗 创建符号链接到processed目录"

echo "🎉 TextWorld设置完成！"
