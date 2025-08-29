# KGRL: Knowledge Graph Enhanced Reinforcement Learning

一个基于知识图谱增强的强化学习智能体框架，专门用于文本冒险游戏中的指令跟随任务。

## 🎯 项目概述

KGRL通过集成知识图谱和大语言模型，构建能够在复杂文本环境中进行推理和决策的智能体。项目包含完整的消融实验设计，用于验证知识图谱对性能的提升效果。

### 核心特性
- 🤖 **多种Agent**: Baseline LLM、RAG增强、ReAct推理
- 🧠 **知识图谱**: 自动构建、语义检索、关系推理
- 🎮 **环境支持**: TextWorld、ALFWorld兼容
- 🔬 **实验框架**: 完整的消融实验和性能评估
- 🚀 **真实API**: 支持GPT-4o、Claude等主流模型

## 🚀 快速开始

### 1. 安装
```bash
# 克隆项目
git clone <your-repo-url>
cd KGRL

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.template .env
# 编辑 .env 文件，添加你的 OpenAI API 密钥
```

### 2. 快速体验
```bash
# 运行完整系统演示
python -c "
import sys; sys.path.append('.')
from src.environments.textworld_env import TextWorldEnvironment
from src.agents.baseline_agent import BaselineAgent

env = TextWorldEnvironment('demo', {'difficulty': 'easy'})
agent = BaselineAgent('demo_agent', {'model_name': 'gpt-4o'})

obs = env.reset()
action = agent.act(obs, env.get_available_actions())
print(f'观察: {obs}')
print(f'AI选择: {action}')
"
```

### 3. 详细文档
- 📖 **[完整文档](docs/README.md)** - 文档中心导航
- 🚀 **[快速开始](docs/QUICKSTART.md)** - 5分钟快速上手
- 🔧 **[安装指南](docs/INSTALL_GUIDE.md)** - 详细安装步骤
- 🔬 **[技术报告](docs/TECHNICAL_REPORT.md)** - 系统架构和实验设计

## 📁 项目结构

```
KGRL/
├── src/                        # 核心源代码
│   ├── agents/                 # 智能体实现
│   ├── environments/           # 环境接口 (TextWorld/ALFWorld)
│   ├── knowledge/              # 知识图谱系统
│   ├── reasoning/              # ReAct推理框架
│   └── utils/                  # 工具函数
├── docs/                       # 📖 完整文档
├── experiments/                # 🧪 实验脚本
├── config/                     # ⚙️ 配置文件
└── data/                       # 💾 数据存储
└── results/                    # 结果输出
    ├── logs/                   # 日志文件
    ├── models/                 # 保存的模型
    └── plots/                  # 图表结果
```

## 快速开始

### 1. 环境设置
```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境
bash scripts/setup_environment.sh
```

### 2. 运行基线Agent (Week 1)
```bash
python experiments/week1_baseline.py
```

### 3. 运行RAG Agent (Week 2)
```bash
python experiments/week2_rag.py
```

### 4. 进行系统评估 (Week 3)
```bash
python experiments/week3_evaluation.py
```

## 开发计划

- **Week 1**: 环境搭建与基线确立
- **Week 2**: 构建RAG核心管道
- **Week 3**: 系统评估与结果分析
- **Week 4**: 强化学习理论与工具准备
- **Week 5**: PPO训练与调试
- **Week 6**: 最终整合与优化

## 接口说明

### Agent接口
所有Agent都继承自`BaseAgent`，提供统一的接口：
- `act(observation, state)`: 根据观测和状态选择动作
- `reset()`: 重置Agent状态
- `update(experience)`: 更新Agent参数

### 环境接口
所有环境都继承自`BaseEnvironment`，提供统一的接口：
- `reset()`: 重置环境
- `step(action)`: 执行动作
- `get_observation()`: 获取当前观测

### 知识图谱接口
- `build_kg(data)`: 构建知识图谱
- `retrieve(query)`: 检索相关知识
- `update_kg(new_knowledge)`: 更新知识图谱

## 贡献指南

1. 每个模块都有清晰的接口定义
2. 所有代码都有详细的文档字符串
3. 提供完整的测试覆盖
4. 遵循PEP 8代码规范

## 📊 当前状态

### ✅ 已完成 (Week 1)
- [x] 模拟TextWorld环境 - 完全兼容API
- [x] 知识图谱系统 - 构建、检索、语义搜索
- [x] Baseline LLM Agent - GPT-4o集成
- [x] 完整游戏循环 - 观察→决策→执行→反馈

### 🔄 进行中 (Week 2)
- [ ] RAG Agent - 知识图谱增强决策
- [ ] ReAct推理 - 思考-行动循环
- [ ] 消融实验 - 性能对比分析

## 🤝 贡献

欢迎贡献代码、报告问题或提出改进建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

MIT License

---

**💡 提示**: 查看 [docs/README.md](docs/README.md) 获取完整的文档导航和使用指南。
