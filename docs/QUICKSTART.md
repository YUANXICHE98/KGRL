# KGRL 快速开始指南

欢迎使用KGRL（Knowledge Graph Enhanced Reinforcement Learning）项目！这个指南将帮助你在5分钟内启动并运行项目。

## 🚀 快速安装

### 1. 克隆项目（如果还没有）
```bash
git clone <your-repo-url>
cd KGRL
```

### 2. 运行自动设置脚本
```bash
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

### 3. 配置API密钥
```bash
# 复制环境变量模板
cp .env.template .env

# 编辑.env文件，添加你的API密钥
nano .env  # 或使用你喜欢的编辑器
```

在`.env`文件中至少设置一个API密钥：
```bash
OPENAI_API_KEY=sk-your-openai-key-here
# 或
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

## 🧪 验证安装

运行测试脚本确保一切正常：
```bash
python test_framework.py
```

如果看到"🎉 All tests passed!"，说明安装成功！

## 🎮 立即体验

### 选项1：一键演示（推荐）
```bash
# 运行完整系统演示
python -c "
import sys; sys.path.append('.')

print('🎯 KGRL系统演示')
print('=' * 50)

# 1. 创建环境
from src.environments.textworld_env import TextWorldEnvironment
env = TextWorldEnvironment('quickstart_demo', {'difficulty': 'easy'})
print('✅ 环境创建成功')

# 2. 创建知识图谱
from src.knowledge.kg_builder import KnowledgeGraphBuilder
kg = KnowledgeGraphBuilder('quickstart_kg')
kg.add_fact('kitchen', 'contains', 'fridge')
kg.add_fact('fridge', 'contains', 'apple')
kg.add_fact('bedroom', 'contains', 'chest')
print('✅ 知识图谱构建完成')

# 3. 创建智能体
from src.agents.baseline_agent import BaselineAgent
agent = BaselineAgent('quickstart_agent', {
    'model_name': 'gpt-4o',
    'use_local_model': False,
    'temperature': 0.7
})
print('✅ 智能体创建成功')

# 4. 运行游戏循环
print('\\n🎮 开始游戏...')
obs = env.reset()
print(f'观察: {obs}')

actions = env.get_available_actions()
print(f'可用动作: {actions}')

action = agent.act(obs, actions)
print(f'AI选择: {action}')

new_obs, reward, done, info = env.step(action)
print(f'结果: 奖励={reward}, 完成={done}')
print(f'新观察: {new_obs}')

print('\\n🎉 演示完成！系统运行正常')
"
```

### 选项2：交互式演示
```bash
python main.py --demo
```
这将启动一个交互式文本游戏，你可以：
- 手动输入动作
- 让AI接管（输入`auto`）
- 重置游戏（输入`reset`）

### 选项2：运行Week 1基线实验
```bash
python main.py --week1
```
这将运行完整的基线实验，大约需要5-10分钟。

### 选项3：查看项目状态
```bash
python main.py --status
```
检查所有组件的状态和配置。

## 📊 理解输出

### 实验结果
实验完成后，你会看到类似这样的输出：
```
==================================================
WEEK 1 BASELINE EXPERIMENT RESULTS
==================================================
Episodes run: 20
Success rate: 45.00%
Average steps per episode: 12.3
Average reward per episode: 0.15
==================================================
```

### 结果文件
- 详细结果：`results/week1/baseline_results.json`
- 日志文件：`results/logs/`
- 知识图谱：`data/knowledge_graphs/`

## 🔧 自定义配置

### 修改Agent配置
编辑 `config/agent_config.py`：
```python
# 更改模型
baseline_config.model_name = "gpt-4o"  # 或 "claude-3-sonnet"

# 调整温度
baseline_config.temperature = 0.5
```

### 修改环境配置
编辑 `config/env_config.py`：
```python
# 更改难度
textworld.difficulty = "hard"

# 更改episode长度
textworld.max_episode_steps = 100
```

## 📈 下一步

### Week 2: RAG Agent
```bash
# 即将推出
python main.py --week2
```

### Week 3: 系统评估
```bash
# 即将推出
python main.py --week3
```

### 自定义实验
查看 `experiments/` 目录中的示例脚本，创建你自己的实验。

## 🐛 常见问题

### Q: 测试失败怎么办？
A: 检查以下几点：
1. Python版本是否>=3.8
2. 是否正确设置了API密钥
3. 网络连接是否正常
4. 运行 `pip install -r requirements.txt`

### Q: API调用失败
A: 
1. 确认API密钥正确
2. 检查API配额
3. 尝试使用不同的模型

### Q: TextWorld安装失败
A: 不用担心！项目会自动使用模拟环境，功能完全相同。

### Q: 如何使用本地模型？
A: 编辑配置文件：
```python
baseline_config.use_local_model = True
baseline_config.model_name = "meta-llama/Llama-3.1-8B-Instruct"
```

## 📚 深入学习

### 项目结构
```
KGRL/
├── src/agents/          # 三个核心Agent
├── src/environments/    # 环境接口
├── src/knowledge/       # 知识图谱
├── src/reasoning/       # ReAct框架
├── experiments/         # 实验脚本
├── config/             # 配置文件
└── results/            # 实验结果
```

### 核心概念
1. **Agent 1 (Baseline)**: 纯LLM，无知识图谱
2. **Agent 2 (RAG)**: LLM + 知识图谱检索
3. **Agent 3 (PPO)**: RAG + 强化学习训练

### 扩展项目
- 添加新的环境：继承 `BaseEnvironment`
- 创建新的Agent：继承 `BaseAgent`
- 自定义知识图谱：使用 `KnowledgeGraphBuilder`
- 实现新的推理方法：扩展 `ReActFramework`

## 🤝 获得帮助

1. 查看详细文档：`README.md`
2. 检查配置文件：`config/`
3. 运行测试：`python test_framework.py`
4. 查看示例：`experiments/`

## 🎯 成功指标

你的项目运行成功的标志：
- ✅ 测试全部通过
- ✅ 演示模式正常运行
- ✅ Week 1实验完成并生成结果
- ✅ 可以看到Agent的决策过程
- ✅ 知识图谱检索正常工作

恭喜！你现在已经有了一个完整的KGRL研究框架。开始探索知识图谱增强的强化学习吧！🚀
