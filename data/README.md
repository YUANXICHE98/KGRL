# KGRL 数据管理

本目录包含KGRL项目的所有数据文件，按功能和类型分类组织。

## 📁 数据结构

```
data/
├── README.md                           # 数据说明文档
├── knowledge_graphs/                   # 知识图谱数据
│   ├── README.md                      # KG数据说明
│   ├── domains/                       # 按领域分类的KG
│   │   ├── textworld/                 # TextWorld领域KG
│   │   │   └── basic_game.json       # 基础游戏KG
│   │   ├── dodaf/                     # DODAF框架KG
│   │   └── general/                   # 通用领域KG
│   ├── templates/                     # KG模板
│   └── schemas/                       # KG模式定义
│       └── kg_schema.json            # KG数据模式
├── environments/                       # 环境数据
│   ├── README.md                      # 环境数据说明
│   ├── textworld/                     # TextWorld环境
│   │   ├── scenarios/                 # 场景定义
│   │   └── configs/                   # 环境配置
│   └── custom/                        # 自定义环境
├── agents/                            # Agent配置和数据
│   ├── README.md                      # Agent数据说明
│   ├── configs/                       # Agent配置
│   │   ├── baseline_agent.yaml       # 基线Agent配置
│   │   └── react_agent.yaml          # React Agent配置
│   ├── prompts/                       # 提示词模板
│   └── memory/                        # 记忆数据
│       ├── short_term/               # 短期记忆
│       ├── medium_term/              # 中期记忆
│       └── long_term/                # 长期记忆
├── experiments/                       # 实验数据
│   ├── README.md                      # 实验数据说明
│   ├── datasets/                      # 实验数据集
│   ├── benchmarks/                    # 基准测试
│   └── evaluation/                    # 评估数据
└── pipeline/                          # Pipeline数据
    ├── README.md                      # Pipeline数据说明
    ├── flows/                         # 数据流定义
    └── transformations/               # 数据转换
```

## 📚 知识图谱数据

### 数据格式
所有KG数据使用统一的JSON格式，符合 `schemas/kg_schema.json` 定义：

```json
{
  "kg_id": "unique_identifier",
  "domain": "textworld|dodaf|general",
  "version": "1.0",
  "description": "KG description",
  "facts": [
    {
      "subject": "entity1",
      "predicate": "relation",
      "object": "entity2",
      "confidence": 0.9,
      "source": "manual|auto|learned",
      "dodaf_type": "DO|DA|F"
    }
  ],
  "entities": [...],
  "relations": [...],
  "stats": {...},
  "metadata": {...}
}
```

### 领域分类
- **textworld/**: TextWorld游戏环境相关的知识
- **dodaf/**: DODAF决策框架相关的知识
- **general/**: 通用常识和导航知识

### 使用示例
```python
from data.tools.kg_loader import load_kg

# 加载特定领域的KG
textworld_kg = load_kg("data/knowledge_graphs/domains/textworld/basic_game.json")
```

## ⚙️ Agent配置

### 配置格式
Agent配置使用YAML格式，支持以下结构：

```yaml
agent_type: "ReactAgent"
version: "1.0"
description: "ReAct agent configuration"

model:
  name: "gpt-4o"
  temperature: 0.7
  max_tokens: 300

knowledge_graph:
  enabled: true
  max_facts: 5
  query_types: ["keywords", "dodaf", "entity"]

memory:
  enabled: false
  short_term_size: 10

reasoning:
  type: "react"
  max_iterations: 5

prompts:
  system_prompt: "You are an AI assistant..."
```

### 可用配置
- **baseline_agent.yaml**: 基线Agent配置
- **react_agent.yaml**: ReAct Agent配置
- **dodaf_agent.yaml**: DODAF Agent配置
- **memory_agent.yaml**: Memory Agent配置

### 使用示例
```python
from data.tools.config_loader import load_agent_config

config = load_agent_config("data/agents/configs/react_agent.yaml")
agent = ReactAgent("my_agent", config)
```

## 🎮 环境配置

### TextWorld环境
- **scenarios/**: 游戏场景定义文件
- **configs/**: 难度和参数配置

### 配置示例
```yaml
environment_type: "TextWorld"
difficulty: "easy"
max_episode_steps: 30
random_seed: 42

game_settings:
  nb_objects: 5
  nb_rooms: 3
  quest_length: 3
```

## 🧪 实验数据

### 数据集格式
```json
{
  "dataset_id": "baseline_test",
  "version": "1.0",
  "description": "Baseline agent test dataset",
  "scenarios": [
    {
      "scenario_id": "treasure_hunt_001",
      "environment": "textworld",
      "difficulty": "easy",
      "initial_state": "...",
      "goal": "find treasure",
      "optimal_actions": ["take key", "go north", "open chest"],
      "expected_reward": 1.0
    }
  ],
  "evaluation_metrics": ["success_rate", "avg_steps", "efficiency"]
}
```

### 基准测试
- **textworld_benchmark.json**: TextWorld环境基准
- **dodaf_benchmark.json**: DODAF框架基准

## 🔧 数据管理工具

### 数据验证
```python
# 验证KG数据格式
from data.tools.validate import validate_kg_format
is_valid = validate_kg_format("path/to/kg.json")

# 验证Agent配置
from data.tools.validate import validate_agent_config
is_valid = validate_agent_config("path/to/config.yaml")
```

### 数据转换
```python
# TextWorld数据转KG
from data.tools.convert import textworld_to_kg
kg_data = textworld_to_kg(textworld_data)

# KG转DODAF格式
from data.tools.convert import kg_to_dodaf
dodaf_kg = kg_to_dodaf(kg_data)
```

### 数据统计
```python
# 分析KG统计信息
from data.tools.analyze import analyze_kg_stats
stats = analyze_kg_stats("path/to/kg.json")

# 生成数据报告
from data.tools.analyze import generate_data_report
report = generate_data_report()
```

## 📊 数据质量

### 质量标准
- **完整性**: 所有必需字段都存在
- **一致性**: 数据格式符合模式定义
- **准确性**: 事实和关系正确无误
- **时效性**: 数据保持最新状态

### 质量检查
```bash
# 运行数据质量检查
python data/tools/quality_check.py

# 检查特定文件
python data/tools/quality_check.py --file data/knowledge_graphs/domains/textworld/basic_game.json
```

## 🔄 数据更新

### 版本控制
- 每次重大更新增加版本号
- 保留历史版本以便回滚
- 记录更新日志

### 更新流程
1. 备份当前数据
2. 应用更新
3. 验证数据质量
4. 更新版本信息
5. 提交变更

### 自动更新
```python
# 从经验中学习更新KG
from data.tools.update import update_kg_from_experience
update_kg_from_experience(observation, action, result)

# 更新Agent配置
from data.tools.update import update_agent_config
update_agent_config(agent_id, new_config)
```

## 📈 数据监控

### 监控指标
- 数据文件大小和数量
- KG事实数量和质量
- 配置文件使用频率
- 数据访问模式

### 监控工具
```python
# 数据使用统计
from data.tools.monitor import get_usage_stats
stats = get_usage_stats()

# 性能监控
from data.tools.monitor import monitor_performance
monitor_performance()
```

## 🔒 数据安全

### 访问控制
- 只读数据：公开访问
- 配置文件：受限访问
- 实验数据：版本控制

### 备份策略
- 定期自动备份
- 多地点存储
- 增量备份机制

## 💡 使用建议

1. **遵循命名规范**: 使用描述性的文件名
2. **保持数据整洁**: 定期清理过时数据
3. **文档化变更**: 记录重要的数据变更
4. **测试数据质量**: 使用验证工具检查数据
5. **版本管理**: 对重要数据进行版本控制

这个数据管理系统为KGRL项目提供了完整的数据组织和管理框架。
