# KGRL详细使用指南

## 🤖 LLM选择和比较详解

### 当前支持的LLM

我们的框架支持多种LLM，你可以根据需要选择：

#### 1. OpenAI模型（推荐用于快速开始）
```python
# 在.env文件中设置
OPENAI_API_KEY=sk-your-key-here

# 可用模型
- gpt-4o: 最强性能，成本较高 ($0.03/1K tokens)
- gpt-4o-mini: 性价比最高 ($0.0015/1K tokens) ⭐推荐
- gpt-3.5-turbo: 经济选择 ($0.002/1K tokens)
```

#### 2. Anthropic模型（推荐用于研究）
```python
# 在.env文件中设置
ANTHROPIC_API_KEY=sk-ant-your-key-here

# 可用模型
- claude-3-5-sonnet: 最新最强 ($0.015/1K tokens)
- claude-3-haiku: 快速经济 ($0.0025/1K tokens) ⭐推荐
```

#### 3. 本地模型（推荐用于大量实验）
```python
# 免费使用，需要GPU
- llama-3.1-8b: Meta开源模型
- gemma-2-9b: Google开源模型
```

### LLM比较实验

运行多个LLM的性能对比：

```bash
# 比较推荐的LLM组合
python experiments/llm_comparison.py --episodes 20

# 比较特定模型
python experiments/llm_comparison.py --models gpt-4o-mini claude-3-haiku --episodes 30

# 快速测试
python experiments/llm_comparison.py --episodes 5 --max-steps 20
```

### 选择建议

| 场景 | 推荐LLM | 原因 |
|------|---------|------|
| 快速原型 | gpt-4o-mini | 便宜、快速、效果好 |
| 研究实验 | claude-3-haiku | 性价比高、推理能力强 |
| 大量测试 | llama-3.1-8b | 免费、本地运行 |
| 最佳性能 | gpt-4o | 最强能力（成本较高） |

## 🎮 环境详解：TextWorld vs ALFWorld

### 当前环境：智能TextWorld

我们使用了一个**智能TextWorld系统**：

#### 真实TextWorld模式
```bash
# 如果安装了TextWorld
pip install textworld
# 自动使用真实TextWorld环境
```

#### 模拟TextWorld模式（默认）
```python
# 无需安装，自动启用模拟环境
# 提供完全相同的接口和体验
```

### 模拟环境详情

我们的模拟环境包含：

```
🏠 房间布局:
kitchen ←→ living_room ←→ bedroom
                ↓
            bathroom

📦 物品分布:
- kitchen: apple (in fridge), key (on table)
- living_room: book (on sofa)  
- bedroom: pillow (on bed), chest (locked)

🎯 任务目标:
找到钥匙 → 去卧室 → 打开箱子 → 获得宝藏
```

### 环境配置示例

```python
# 简单配置
easy_config = {
    "difficulty": "easy",
    "max_episode_steps": 30
}

# 详细配置
detailed_config = {
    "max_episode_steps": 50,
    "difficulty": "medium",
    "nb_objects": 8,        # 物品数量
    "nb_rooms": 4,          # 房间数量
    "quest_length": 5,      # 任务复杂度
    "include_description": True,
    "include_inventory": True,
    "admissible_commands": True
}
```

### ALFWorld支持

ALFWorld环境已准备就绪，可以这样启用：

```bash
# 安装ALFWorld
pip install alfworld

# 使用ALFWorld
python -c "
from src.environments.alfworld_env import ALFWorldEnvironment
env = ALFWorldEnvironment('test', {'split': 'train'})
print('ALFWorld ready!')
"
```

## 🧠 知识图谱详解

### 当前KG结构

我们的基础知识图谱包含：

#### 实体类型（28个实体）
- **房间** (4个): kitchen, living_room, bedroom, bathroom
- **家具** (6个): fridge, table, sofa, tv, bed, chest, mirror  
- **物品** (4个): apple, key, book, pillow, treasure
- **动作** (3个): take_item, open_container, go_direction
- **属性** (4个): opened, taken, free_hands, location
- **目标** (7个): player, find_treasure, open_chest, have_key, take_key

#### 关系类型（8种关系）
- **connected_to**: 房间连接关系
- **located_in**: 物品位置关系  
- **can_be**: 物品属性关系
- **opens**: 钥匙开启关系
- **requires**: 需求关系
- **changes**: 状态变化关系
- **hidden_in**: 隐藏关系
- **goal**: 目标关系

### KG可视化

运行独立的可视化脚本：

```bash
# 可视化默认KG
python scripts/visualize_kg.py

# 可视化自定义KG
python scripts/visualize_kg.py --kg-file data/knowledge_graphs/my_kg.json

# 指定输出目录
python scripts/visualize_kg.py --output-dir results/my_visualizations
```

生成的可视化包括：
1. **完整图谱**: 显示所有实体和关系
2. **按关系分类**: 每种关系单独显示
3. **统计图表**: 实体分布、关系分布、置信度等

### 自定义KG

创建你自己的知识图谱：

```python
from src.knowledge.kg_builder import KnowledgeGraphBuilder

# 创建KG构建器
kg = KnowledgeGraphBuilder("my_custom_kg")

# 添加事实
kg.add_fact("wizard_tower", "connected_to", "magic_forest")
kg.add_fact("magic_sword", "located_in", "wizard_tower")
kg.add_fact("magic_sword", "can_defeat", "dragon")

# 从文本提取事实
text = "The dragon is in the cave. The cave contains treasure."
kg.add_facts_from_text(text)

# 保存KG
kg.save_to_file("data/knowledge_graphs/my_custom_kg.json")

# 可视化
python scripts/visualize_kg.py --kg-file data/knowledge_graphs/my_custom_kg.json
```

## 🚀 完整使用流程

### 1. 环境设置
```bash
# 克隆项目
git clone <your-repo>
cd KGRL

# 自动设置
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh

# 配置API密钥
cp .env.template .env
# 编辑.env文件添加API密钥
```

### 2. 验证安装
```bash
# 运行测试
python test_framework.py

# 检查项目状态
python main.py --status
```

### 3. 体验项目
```bash
# 交互式演示
python main.py --demo

# 运行基线实验
python main.py --week1

# LLM比较实验
python experiments/llm_comparison.py
```

### 4. 可视化分析
```bash
# 可视化知识图谱
python scripts/visualize_kg.py

# 查看实验结果
ls results/week1/
ls results/llm_comparison/
```

## 📊 实验结果解读

### Week 1基线结果
```json
{
  "success_rate": 0.45,        // 45%的episode成功
  "average_steps": 12.3,       // 平均12.3步完成
  "average_reward": 0.15,      // 平均奖励0.15
  "invalid_action_rate": 0.08  // 8%的动作无效
}
```

### LLM比较结果
```
GPT-4o Mini (openai):
  Success Rate: 65.00%
  Avg Steps: 10.2
  Cost: $0.0234

Claude 3 Haiku (anthropic):  
  Success Rate: 58.00%
  Avg Steps: 11.5
  Cost: $0.0156

Llama 3.1 8B (local):
  Success Rate: 42.00%
  Avg Steps: 14.8
  Cost: $0.0000
```

## 🔧 高级配置

### 自定义Agent配置
```python
# 修改 config/agent_config.py
baseline_config.model_name = "claude-3-haiku"
baseline_config.temperature = 0.5
baseline_config.max_tokens = 256
```

### 自定义环境配置
```python
# 修改 config/env_config.py
textworld.difficulty = "hard"
textworld.max_episode_steps = 100
textworld.nb_rooms = 6
```

### 自定义实验
```python
# 创建 experiments/my_experiment.py
from experiments.week1_baseline import Week1Experiment

class MyExperiment(Week1Experiment):
    def __init__(self):
        super().__init__()
        self.num_episodes = 50  # 更多episodes
        
    def setup_agent(self):
        # 自定义Agent设置
        pass
```

## 🐛 常见问题解决

### Q: API调用失败
```bash
# 检查API密钥
python -c "import os; print('OpenAI:', bool(os.getenv('OPENAI_API_KEY')))"

# 测试API连接
python -c "
from config.llm_config import get_available_llms
print('Available LLMs:', list(get_available_llms().keys()))
"
```

### Q: 环境运行错误
```bash
# 使用模拟环境
python -c "
from src.environments.textworld_env import TextWorldEnvironment
env = TextWorldEnvironment('test', {'difficulty': 'easy'})
print('Environment OK')
"
```

### Q: 可视化失败
```bash
# 安装可视化依赖
pip install matplotlib seaborn networkx

# 测试可视化
python scripts/visualize_kg.py --kg-file data/knowledge_graphs/example_basic_kg.json
```

## 📈 性能优化建议

### 1. 快速实验
- 使用`difficulty="easy"`
- 设置`max_episode_steps=20`
- 使用`gpt-4o-mini`或本地模型

### 2. 准确实验  
- 使用`difficulty="medium"`
- 设置`num_episodes=50`
- 使用`claude-3-haiku`

### 3. 大规模实验
- 使用本地模型（llama-3.1-8b）
- 批量运行多个配置
- 使用GPU加速

这样你就有了一个完整的使用指南！你可以根据自己的需求选择合适的LLM、环境配置和实验设置。
