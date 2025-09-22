#!/bin/bash

# TextWorld数据集下载脚本
# 官方仓库: https://github.com/microsoft/TextWorld

set -e

echo "🚀 开始下载TextWorld数据集..."

# 设置目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARKS_DIR="$(dirname "$SCRIPT_DIR")"
TEXTWORLD_DIR="$BENCHMARKS_DIR/textworld"

# 创建目录
mkdir -p "$TEXTWORLD_DIR"
cd "$TEXTWORLD_DIR"

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

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
echo "🐍 检测到Python版本: $python_version"

# 检查系统依赖
echo "🔧 检查系统依赖..."
if command -v apt-get >/dev/null 2>&1; then
    echo "📦 Ubuntu/Debian系统，检查依赖..."
    sudo apt-get update && sudo apt-get install -y build-essential libffi-dev python3-dev curl git || echo "⚠️  请手动安装系统依赖"
elif command -v brew >/dev/null 2>&1; then
    echo "🍺 macOS系统，检查依赖..."
    brew install libffi curl git || echo "⚠️  请手动安装系统依赖"
fi

# 安装依赖
echo "📦 安装TextWorld依赖..."
pip install -e . || pip install textworld

# 创建游戏目录
mkdir -p "$TEXTWORLD_DIR/games"
cd "$TEXTWORLD_DIR/games"

# 生成示例游戏
echo "🎮 生成示例游戏..."
python3 -c "
import textworld
import os

# 生成不同复杂度的示例游戏
configs = [
    {'world_size': 3, 'nb_objects': 5, 'quest_length': 3, 'name': 'simple_game'},
    {'world_size': 5, 'nb_objects': 10, 'quest_length': 5, 'name': 'medium_game'},
    {'world_size': 7, 'nb_objects': 15, 'quest_length': 8, 'name': 'complex_game'}
]

for config in configs:
    try:
        game = textworld.generator.make_game(
            world_size=config['world_size'],
            nb_objects=config['nb_objects'],
            quest_length=config['quest_length']
        )
        game_file = f\"{config['name']}.z8\"
        textworld.generator.compile_game(game, game_file)
        print(f'✅ 生成游戏: {game_file}')
    except Exception as e:
        print(f'⚠️  生成 {config[\"name\"]} 失败: {e}')
" || echo "⚠️  游戏生成失败，可能需要手动创建"

# 尝试下载预构建游戏（如果可用）
echo "📥 尝试下载预构建游戏..."
if command -v wget >/dev/null 2>&1; then
    wget -q --timeout=30 "https://github.com/microsoft/TextWorld/releases/download/v1.0.0/tw-simple-games.zip" 2>/dev/null && {
        unzip -q tw-simple-games.zip 2>/dev/null || true
        rm -f tw-simple-games.zip
        echo "✅ 下载了预构建简单游戏"
    } || echo "⚠️  预构建游戏下载失败，使用生成的游戏"
elif command -v curl >/dev/null 2>&1; then
    curl -L --max-time 30 -s "https://github.com/microsoft/TextWorld/releases/download/v1.0.0/tw-simple-games.zip" -o tw-simple-games.zip 2>/dev/null && {
        unzip -q tw-simple-games.zip 2>/dev/null || true
        rm -f tw-simple-games.zip
        echo "✅ 下载了预构建简单游戏"
    } || echo "⚠️  预构建游戏下载失败，使用生成的游戏"
fi

# 创建符号链接便于访问
cd "$BENCHMARKS_DIR"
ln -sf textworld/TextWorld textworld_repo 2>/dev/null || true
ln -sf textworld/games textworld_games 2>/dev/null || true

echo "✅ TextWorld数据集下载完成！"
echo "📁 仓库位置: $TEXTWORLD_DIR/TextWorld"
echo "📁 游戏位置: $TEXTWORLD_DIR/games"
echo "🎮 测试命令: tw-play $TEXTWORLD_DIR/games/simple_game.z8"
echo "🎉 TextWorld设置完成！"
