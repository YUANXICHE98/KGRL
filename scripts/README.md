# KGRL Scripts 使用指南

这个目录包含了KGRL项目的所有脚本工具，按功能分类组织。

## 📁 目录结构

```
scripts/
├── setup/                  # 环境设置脚本
│   ├── install_dependencies.sh    # 安装依赖
│   ├── setup_environment.sh       # 环境配置
│   └── download_datasets.sh       # 数据下载
├── maintenance/            # 维护脚本
│   ├── check_health.py            # 健康检查
│   ├── clean_cache.py             # 清理缓存
│   └── backup_results.py          # 备份结果
├── utils/                  # 实用工具
│   ├── convert_formats.py         # 格式转换
│   ├── merge_configs.py           # 配置合并
│   └── generate_docs.py           # 文档生成
├── run_quick_test.py       # 快速测试
├── run_baseline_comparison.py     # 基线对比实验
├── run_full_experiment.py         # 完整实验
└── run_kg_analysis.py             # 知识图谱分析
```

## 🚀 快速开始

### 1. 初始设置

```bash
# 安装依赖
bash scripts/setup/install_dependencies.sh

# 配置环境
bash scripts/setup/setup_environment.sh

# 下载数据集
bash scripts/setup/download_datasets.sh
```

### 2. 健康检查

```bash
# 全面健康检查
python scripts/maintenance/check_health.py
```

### 3. 运行实验

```bash
# 快速功能测试
python scripts/run_quick_test.py

# 基线对比实验
python scripts/run_baseline_comparison.py

# 完整实验评估
python scripts/run_full_experiment.py
```

## 📋 脚本详细说明

### Setup 脚本

#### `install_dependencies.sh`
安装项目所需的Python依赖包。

```bash
bash scripts/setup/install_dependencies.sh
```

**功能**:
- 检查Python版本
- 升级pip
- 安装核心依赖 (openai, networkx, matplotlib等)
- 安装可选依赖 (jupyter, seaborn等)
- 验证安装

#### `setup_environment.sh`
配置项目环境和目录结构。

```bash
bash scripts/setup/setup_environment.sh
```

**功能**:
- 创建必要的目录结构
- 检查API密钥
- 创建环境变量模板
- 设置脚本权限
- 创建快速启动别名

#### `download_datasets.sh`
下载和准备实验数据。

```bash
bash scripts/setup/download_datasets.sh
```

**功能**:
- 检查现有数据
- 创建示例配置
- 验证数据格式

### Maintenance 脚本

#### `check_health.py`
全面的项目健康检查。

```bash
python scripts/maintenance/check_health.py
```

**检查项目**:
- 项目结构完整性
- 数据文件完整性
- Python依赖
- API连接
- 实验就绪状态
- Git状态

#### `clean_cache.py`
清理各种缓存和临时文件。

```bash
python scripts/maintenance/clean_cache.py
```

**清理内容**:
- Python缓存 (__pycache__, *.pyc)
- 系统缓存 (.DS_Store, Thumbs.db)
- 日志文件 (超过1MB或7天)
- 实验临时文件
- IDE缓存

#### `backup_results.py`
备份实验结果和重要数据。

```bash
python scripts/maintenance/backup_results.py
```

**备份内容**:
- 实验结果文件
- 配置文件
- 重要脚本
- 最近日志文件

### Utils 工具

#### `convert_formats.py`
格式转换工具。

```bash
# 单文件转换
python scripts/utils/convert_formats.py -i config.json -t json_to_yaml

# 批量转换
python scripts/utils/convert_formats.py -i configs/ -t batch --batch-type json_to_yaml
```

**支持转换**:
- JSON ↔ YAML
- 实验结果 → CSV
- 知识图谱 → GraphML

#### `merge_configs.py`
配置文件管理工具。

```bash
# 合并配置
python scripts/utils/merge_configs.py -a merge -f config1.yaml config2.yaml -o merged.yaml

# 创建配置模板
python scripts/utils/merge_configs.py -a create -t all
```

#### `generate_docs.py`
自动生成项目文档。

```bash
python scripts/utils/generate_docs.py
```

**生成文档**:
- API参考文档
- 实验文档
- 配置文档
- 项目README

### 实验脚本

#### `run_quick_test.py`
快速功能测试，验证系统基本功能。

```bash
python scripts/run_quick_test.py
```

**测试内容**:
- 环境加载
- 智能体初始化
- 知识图谱数据
- API连接
- 迷你实验

#### `run_baseline_comparison.py`
运行基线对比实验。

```bash
python scripts/run_baseline_comparison.py
```

**实验内容**:
- LLM基线 vs ReAct vs RAG
- 12个回合，每回合最多15步
- 自动生成结果和可视化

#### `run_full_experiment.py`
完整的实验评估流程。

```bash
python scripts/run_full_experiment.py
```

**实验流程**:
- 前提条件检查
- 运行基线实验
- 结果分析
- 生成报告
- 清理临时文件

#### `run_kg_analysis.py`
知识图谱数据分析。

```bash
python scripts/run_kg_analysis.py
```

**分析内容**:
- 图结构统计
- 实体关系分析
- 连通性分析
- 可视化生成

## 🔧 高级用法

### 环境变量

创建 `.env` 文件设置环境变量：

```bash
# 复制模板
cp .env.template .env

# 编辑配置
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_MODEL="gpt-3.5-turbo"
export MAX_EPISODES=12
export MAX_STEPS=15
```

### 快速别名

加载项目别名：

```bash
source kgrl_aliases.sh
```

然后可以使用：
- `kgrl-check` - 健康检查
- `kgrl-clean` - 清理缓存
- `kgrl-experiment` - 运行实验
- `kgrl-test` - 快速测试

### 批量操作

```bash
# 批量转换配置文件
find configs -name "*.json" -exec python scripts/utils/convert_formats.py -i {} -t json_to_yaml \;

# 批量备份结果
python scripts/maintenance/backup_results.py && python scripts/maintenance/clean_cache.py
```

## 🐛 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip
   
   # 使用国内镜像
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ package_name
   ```

2. **API密钥问题**
   ```bash
   # 检查环境变量
   echo $OPENAI_API_KEY
   
   # 设置环境变量
   export OPENAI_API_KEY="your-key-here"
   ```

3. **权限问题**
   ```bash
   # 设置脚本权限
   chmod +x scripts/setup/*.sh
   find scripts -name "*.py" -exec chmod +x {} \;
   ```

4. **数据文件缺失**
   ```bash
   # 重新下载数据
   bash scripts/setup/download_datasets.sh
   
   # 检查数据完整性
   python scripts/maintenance/check_health.py
   ```

### 日志查看

```bash
# 查看最新日志
tail -f logs/kgrl.log

# 查看错误日志
grep ERROR logs/kgrl.log
```

## 📞 获取帮助

- 运行健康检查: `python scripts/maintenance/check_health.py`
- 查看脚本帮助: `python script_name.py --help`
- 检查项目状态: `python scripts/run_quick_test.py`

## 🔄 更新和维护

```bash
# 定期清理
python scripts/maintenance/clean_cache.py

# 备份重要结果
python scripts/maintenance/backup_results.py

# 更新文档
python scripts/utils/generate_docs.py

# 健康检查
python scripts/maintenance/check_health.py
```
