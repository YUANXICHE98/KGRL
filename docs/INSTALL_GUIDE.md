# KGRL 安装指南

本指南将帮助你在不同操作系统上安装和配置KGRL项目。

## 📋 系统要求

- **Python**: 3.8+ (推荐3.11)
- **内存**: 至少4GB RAM
- **存储**: 至少1GB可用空间
- **网络**: 需要访问OpenAI/Anthropic API

## 🚨 Python版本检查

首先检查你的Python版本：
```bash
python --version
# 或
python3 --version
```

如果版本低于3.8，需要升级。以下是几种解决方案：

## 方案1：使用Homebrew（最推荐）

### 1. 安装Homebrew
```bash
# 如果没有Homebrew，先安装
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. 安装Python
```bash
# 安装Python 3.11
brew install python@3.11

# 验证安装
python3 --version
# 应该显示: Python 3.11.x
```

### 3. 设置项目环境
```bash
# 进入项目目录
cd KGRL

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证Python版本
python --version
# 应该显示: Python 3.11.x

# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

## 方案2：使用Miniconda（推荐用于数据科学）

### 1. 下载并安装Miniconda
```bash
# 下载Miniconda
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# 安装（按提示操作）
bash Miniconda3-latest-MacOSX-x86_64.sh

# 重启终端或运行
source ~/.zshrc
```

### 2. 创建KGRL环境
```bash
# 创建Python 3.11环境
conda create -n kgrl python=3.11

# 激活环境
conda activate kgrl

# 验证版本
python --version
# 应该显示: Python 3.11.x

# 进入项目目录并安装依赖
cd KGRL
pip install -r requirements.txt
```

## 方案3：使用pyenv（高级用户）

### 1. 安装pyenv
```bash
# 使用Homebrew安装pyenv
brew install pyenv

# 添加到shell配置
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# 重启终端或运行
source ~/.zshrc
```

### 2. 安装和设置Python
```bash
# 安装Python 3.11
pyenv install 3.11.7

# 在项目目录中设置本地版本
cd KGRL
pyenv local 3.11.7

# 验证版本
python --version
# 应该显示: Python 3.11.7

# 创建虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🚀 安装完成后的验证

无论使用哪种方案，完成后运行以下命令验证：

```bash
# 1. 检查Python版本
python --version
# 应该显示 3.8+ 版本

# 2. 运行项目测试
python test_framework.py
# 应该显示所有测试通过

# 3. 检查项目状态
python main.py --status
# 显示项目配置信息

# 4. 体验交互式演示
python main.py --demo
# 启动文本游戏演示
```

## 📋 最小化安装（如果上述方案都有问题）

如果以上方案都遇到问题，可以尝试最小化安装：

### 1. 只安装核心依赖
```bash
# 激活你的Python环境后
pip install openai anthropic requests numpy pandas matplotlib

# 测试核心功能
python -c "
import sys
print(f'Python version: {sys.version}')
try:
    import openai
    print('✅ OpenAI available')
except:
    print('❌ OpenAI not available')
"
```

### 2. 使用模拟模式
```bash
# 设置环境变量使用模拟模式
export USE_MOCK_MODELS=true

# 运行测试
python test_framework.py
```

## 🔧 常见问题解决

### Q: 权限问题
```bash
# 如果遇到权限问题，使用--user安装
pip install --user -r requirements.txt
```

### Q: 网络问题
```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### Q: M1 Mac兼容性问题
```bash
# 对于M1 Mac，使用conda更稳定
conda create -n kgrl python=3.11
conda activate kgrl
conda install pytorch torchvision torchaudio -c pytorch
pip install -r requirements.txt
```

## 📞 获取帮助

如果仍然遇到问题，请：

1. **检查错误信息**：仔细阅读错误提示
2. **验证Python版本**：确保使用3.8+版本
3. **检查网络连接**：确保能访问PyPI
4. **尝试简化安装**：先安装核心包，再逐步添加

## 🎯 推荐安装路径

对于你的情况，我推荐：

1. **首选**：方案1（Homebrew） - 最简单直接
2. **备选**：方案2（Miniconda） - 更好的环境管理
3. **高级**：方案3（pyenv） - 最灵活的版本管理

选择一个方案，按步骤执行即可！
