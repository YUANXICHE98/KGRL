# 🧠 KGRL知识图谱构建分支

本分支专门用于构建和管理KGRL项目的知识图谱系统，支持多种类型的知识图谱构建和管理。

## 🎯 功能特性

### 📊 支持的知识图谱类型

1. **DODAF状态知识图谱**
   - 动作-状态关系建模
   - 实体属性跟踪
   - 状态转换逻辑
   - 结果预测

2. **规则知识图谱**
   - 条件-动作规则
   - 约束规则
   - 推理规则
   - 优先级规则
   - 时序规则

3. **统一知识图谱**
   - 多图谱整合
   - 动态更新
   - 查询接口
   - 经验学习

### 🗂️ 目录结构

```
KGRL/
├── data/
│   ├── benchmarks/           # Benchmark数据集
│   │   ├── alfworld/        # ALFWorld数据
│   │   ├── textworld/       # TextWorld数据
│   │   └── scripts/         # 下载和预处理脚本
│   └── knowledge_graphs/    # 知识图谱输出
│       ├── dodaf/          # DODAF状态图谱
│       ├── rules/          # 规则图谱
│       ├── alfworld/       # ALFWorld图谱
│       ├── textworld/      # TextWorld图谱
│       └── unified/        # 统一图谱
├── src/knowledge/           # 知识图谱构建模块
│   ├── dodaf_kg_builder.py # DODAF图谱构建器
│   ├── rule_kg_builder.py  # 规则图谱构建器
│   └── unified_kg_manager.py # 统一图谱管理器
└── scripts/
    └── build_knowledge_graphs.py # 主构建脚本
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install networkx textworld alfworld

# 切换到知识图谱构建分支
git checkout feature/knowledge-graph-construction
```

### 2. 运行完整构建流水线

```bash
# 运行完整流水线（下载数据 + 预处理 + 构建图谱）
python scripts/build_knowledge_graphs.py

# 跳过数据下载
python scripts/build_knowledge_graphs.py --no-download

# 只处理特定数据集
python scripts/build_knowledge_graphs.py --datasets textworld
```

### 3. 单独运行各个步骤

```bash
# 1. 下载benchmark数据
cd data/benchmarks/scripts
./download_alfworld.sh
./download_textworld.sh

# 2. 预处理数据
python preprocess_alfworld.py
python preprocess_textworld.py

# 3. 构建示例图谱
cd ../../../
python -c "from src.knowledge.dodaf_kg_builder import create_example_kg; kg = create_example_kg(); print(kg.get_statistics())"
```

## 📋 知识图谱类型详解

### DODAF状态知识图谱

基于DODAF架构框架的状态建模：

```python
from src.knowledge.dodaf_kg_builder import DODAFKGBuilder

# 创建构建器
builder = DODAFKGBuilder()

# 构建动作-状态模式
pattern = builder.build_action_state_pattern(
    action_name="打开",
    entity_name="宝箱", 
    entity_type="容器",
    pre_state="锁定",
    post_state="打开",
    result_name="打开成功"
)
```

**节点类型**:
- `ACTION`: 动作节点（如：打开、拿取）
- `ENTITY`: 实体节点（如：宝箱、钥匙）
- `STATE`: 状态节点（如：锁定、打开）
- `RESULT`: 结果节点（如：成功、失败）

**边类型**:
- `REQUIRES`: 需要关系
- `PRODUCES`: 产生关系
- `MODIFIES`: 修改关系
- `TRANSITIONS`: 状态转换

### 规则知识图谱

支持多种规则类型：

```python
from src.knowledge.rule_kg_builder import RuleKGBuilder

builder = RuleKGBuilder()

# 条件-动作规则
builder.add_condition_action_rule(
    "开门规则",
    conditions=["有钥匙", "门是锁定的"],
    actions=["打开门"],
    priority=5
)

# 约束规则
builder.add_constraint_rule(
    "负重约束",
    constraint_conditions=["背包重量 > 最大负重"],
    violation_actions=["无法拿取物品"]
)

# 推理规则
builder.add_inference_rule(
    "传递性推理",
    premises=["A在B里面", "B在C里面"],
    conclusions=["A在C里面"]
)
```

### 统一知识图谱管理

整合多种图谱类型：

```python
from src.knowledge.unified_kg_manager import UnifiedKGManager

manager = UnifiedKGManager()

# 创建不同类型的图谱
dodaf_kg = manager.create_kg("game_states", "dodaf")
rule_kg = manager.create_kg("game_rules", "rule")

# 合并图谱
merged_kg = manager.merge_kgs(
    ["game_states", "game_rules"], 
    "unified_game_kg"
)

# 查询图谱
results = manager.query_kg("unified_game_kg", {
    "node_type": "action",
    "path_query": {"source": "action_1", "target": "result_1"}
})
```

## 🔧 配置选项

### 构建配置

在`scripts/build_knowledge_graphs.py`中可以配置：

- **数据集选择**: ALFWorld, TextWorld
- **图谱类型**: DODAF, Rules, Unified
- **输出格式**: JSON, GraphML
- **合并策略**: Union, Intersection

### 图谱参数

- **节点属性**: 自定义属性字典
- **边权重**: 关系强度
- **优先级**: 规则优先级
- **时间戳**: 创建和更新时间

## 📊 输出格式

### JSON格式
```json
{
  "nodes": [
    {
      "id": "action_1",
      "type": "action", 
      "name": "打开",
      "attributes": {"priority": 1}
    }
  ],
  "edges": [
    {
      "source": "action_1",
      "target": "entity_1", 
      "type": "modifies",
      "attributes": {"strength": 0.8}
    }
  ]
}
```

### GraphML格式
标准的图形交换格式，可用于：
- Gephi可视化
- NetworkX分析
- 其他图分析工具

## 🧪 示例用法

### 创建游戏场景图谱

```python
# 示例：TextWorld开箱场景
builder = DODAFKGBuilder()

# 1. 创建实体
key_id = builder.add_entity_node("青铜钥匙", "道具")
chest_id = builder.add_entity_node("宝箱", "容器")

# 2. 创建状态
locked_state = builder.add_state_node("宝箱状态", "锁定")
open_state = builder.add_state_node("宝箱状态", "打开")

# 3. 创建动作
open_action = builder.add_action_node("打开")

# 4. 建立关系
builder.add_edge(key_id, open_action, EdgeType.ENABLES)
builder.add_edge(open_action, chest_id, EdgeType.MODIFIES)
builder.add_edge(locked_state, open_state, EdgeType.TRANSITIONS)
```

### 可视化图谱

```python
import matplotlib.pyplot as plt
import networkx as nx

# 加载图谱
kg = DODAFKGBuilder()
# ... 构建图谱 ...

# 可视化
pos = nx.spring_layout(kg.graph)
nx.draw(kg.graph, pos, with_labels=True, 
        node_color='lightblue', 
        node_size=1000,
        font_size=8)
plt.show()
```

## 🔍 故障排除

### 常见问题

1. **数据下载失败**
   - 检查网络连接
   - 确认GitHub访问权限
   - 手动下载数据集

2. **依赖包缺失**
   ```bash
   pip install networkx textworld alfworld
   ```

3. **权限问题**
   ```bash
   chmod +x data/benchmarks/scripts/*.sh
   ```

4. **内存不足**
   - 减少处理的数据量
   - 分批处理大型数据集

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查图谱统计
stats = kg.get_statistics()
print(f"节点数: {stats['total_nodes']}")
print(f"边数: {stats['total_edges']}")
```

## 🤝 贡献指南

1. 创建新的图谱类型时，继承`DODAFKGBuilder`
2. 添加新的节点/边类型到相应的枚举
3. 实现相应的导入/导出方法
4. 添加单元测试
5. 更新文档

## 📈 性能优化

- 使用NetworkX的高效图算法
- 批量操作减少I/O
- 内存映射大型数据集
- 并行处理多个图谱

---

🎯 **目标**: 为KGRL项目构建完整、高效、可扩展的知识图谱系统，支持复杂的推理和决策任务。
