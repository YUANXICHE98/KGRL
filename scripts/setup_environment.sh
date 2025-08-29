#!/bin/bash

# KGRL项目环境设置脚本
# 用于快速设置项目依赖和环境

echo "🚀 Setting up KGRL project environment..."

# 检查Python版本
check_python() {
    local python_cmd=$1
    if command -v $python_cmd &> /dev/null; then
        local version=$($python_cmd --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)

        if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 8 ]); then
            echo "✅ Found compatible Python: $python_cmd version $version"
            return 0
        else
            echo "⚠️  Found $python_cmd version $version (need 3.8+)"
            return 1
        fi
    else
        echo "❌ $python_cmd not found"
        return 1
    fi
}

# 尝试找到合适的Python版本
PYTHON_CMD=""
for cmd in python3.11 python3.10 python3.9 python3.8 python3 python; do
    if check_python $cmd; then
        PYTHON_CMD=$cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "❌ No compatible Python version found!"
    echo ""
    echo "📋 Please install Python 3.8+ using one of these methods:"
    echo ""
    echo "Method 1 - Homebrew (Recommended):"
    echo "  brew install python@3.11"
    echo ""
    echo "Method 2 - Miniconda:"
    echo "  curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
    echo "  bash Miniconda3-latest-MacOSX-x86_64.sh"
    echo "  conda create -n kgrl python=3.11"
    echo "  conda activate kgrl"
    echo ""
    echo "Method 3 - pyenv:"
    echo "  brew install pyenv"
    echo "  pyenv install 3.11.7"
    echo "  pyenv global 3.11.7"
    echo ""
    echo "Then run this script again!"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "💡 Try: $PYTHON_CMD -m pip install --user virtualenv"
        exit 1
    fi
fi

# 激活虚拟环境
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 验证虚拟环境中的Python版本
echo "🔍 Verifying virtual environment..."
python --version

# 升级pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# 安装基础依赖
echo "📚 Installing basic dependencies..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装其他依赖
echo "📦 Installing project dependencies..."
pip install -r requirements.txt

# 创建必要的目录结构
echo "📁 Creating directory structure..."
mkdir -p data/knowledge_graphs
mkdir -p data/training_data
mkdir -p data/evaluation_data
mkdir -p results/logs
mkdir -p results/models
mkdir -p results/plots

# 设置环境变量文件
if [ ! -f ".env" ]; then
    echo "🔑 Creating .env file template..."
    cat > .env << EOL
# API Keys (请填入你的API密钥)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
WANDB_API_KEY=your_wandb_api_key_here

# 项目配置
PROJECT_ROOT=$(pwd)
PYTHONPATH=$(pwd)
EOL
    echo "⚠️  Please edit .env file and add your API keys"
fi

# 尝试安装TextWorld（可选）
echo "🎮 Attempting to install TextWorld (optional)..."
pip install textworld || echo "⚠️  TextWorld installation failed, will use mock environment"

# 尝试安装ALFWorld（可选）
echo "🏠 Attempting to install ALFWorld (optional)..."
pip install alfworld || echo "⚠️  ALFWorld installation failed, will use TextWorld only"

# 运行简单测试
echo "🧪 Running basic tests..."
python3 -c "
import sys
sys.path.append('.')
try:
    from src.agents.baseline_agent import BaselineAgent
    from src.environments.textworld_env import TextWorldEnvironment
    from src.knowledge.kg_builder import KnowledgeGraphBuilder
    print('✅ All core modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run Week 1 experiment: python experiments/week1_baseline.py"
echo ""
echo "📖 Quick start commands:"
echo "  - Run baseline experiment: python experiments/week1_baseline.py"
echo "  - Check project structure: tree -I 'venv|__pycache__|*.pyc'"
echo "  - View logs: ls -la results/logs/"
echo ""
echo "🔗 Useful resources:"
echo "  - Project README: cat README.md"
echo "  - Configuration files: ls config/"
echo "  - Example scripts: ls experiments/"
