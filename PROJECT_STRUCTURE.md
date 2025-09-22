# KGRL项目结构文档

## 📁 项目总体结构

```
KGRL/
├── 📂 src/                          # 核心源代码
├── 📂 data/                         # 数据管理
├── 📂 scripts/                      # 脚本工具
├── 📂 docs/                         # 文档
├── 📂 tests/                        # 测试文件
├── 📄 requirements.txt              # Python依赖
├── 📄 README.md                     # 项目说明
└── 📄 PROJECT_STRUCTURE.md          # 本文件
```

## 🏗️ 核心模块 (src/)

### 知识图谱模块 (src/knowledge/)
```
src/knowledge/
├── 📄 __init__.py
├── 📄 dodaf_kg_builder.py          # DODAF知识图谱构建器 (核心)
├── 📄 rule_kg_builder.py           # 规则知识图谱构建器
└── 📄 unified_kg_manager.py        # 统一知识图谱管理器
```

**核心功能**:
- `DODAFKGBuilder`: DODAF架构知识图谱构建
- `RuleKGBuilder`: 规则知识图谱构建  
- `UnifiedKGManager`: 多类型知识图谱统一管理

### 智能体模块 (src/agents/)
```
src/agents/
├── 📄 __init__.py
├── 📄 base_agent.py               # 基础智能体
├── 📄 kg_enhanced_agent.py        # 知识图谱增强智能体
└── 📄 rl_agent.py                 # 强化学习智能体
```

### 环境模块 (src/environments/)
```
src/environments/
├── 📄 __init__.py
├── 📄 alfworld_env.py             # ALFWorld环境包装
├── 📄 textworld_env.py            # TextWorld环境包装
└── 📄 kg_enhanced_env.py          # 知识图谱增强环境
```

## 📊 数据管理 (data/)

### 基准数据 (data/benchmarks/)
```
data/benchmarks/
├── 📄 README.md                   # 基准数据说明
├── 📂 alfworld/                   # ALFWorld数据 (240个场景)
│   └── alfworld/alfworld/gen/
│       ├── layouts/               # 布局文件 (*.json)
│       └── ff_planner/samples/    # PDDL文件
├── 📂 textworld/                  # TextWorld数据
│   └── TextWorld/
│       ├── benchmark/games.json   # 64个benchmark游戏
│       └── ...
└── 📂 scripts/                    # 下载脚本
    ├── 📄 download_alfworld.sh
    └── 📄 download_textworld.sh
```

### 知识图谱数据 (data/knowledge_graphs/)
```
data/knowledge_graphs/
├── 📂 extracted/                  # 合并的知识图谱
│   ├── 📄 alfworld_kg.json       # ALFWorld合并KG (111KB, 225节点)
│   ├── 📄 alfworld_kg.graphml
│   ├── 📄 textworld_kg.json      # TextWorld KG (4.4KB, 10节点)
│   ├── 📄 textworld_kg.graphml
│   └── 📄 enhanced_example_kg.json # 示例KG (12KB, 17节点)
├── 📂 scenes/                     # 按场景分割的KG
│   ├── 📄 scene_index.json       # 场景索引
│   ├── 📄 scenes_summary.json    # 场景汇总
│   ├── 📄 FloorPlan228-openable_kg.json
│   ├── 📄 FloorPlan211-openable_kg.json
│   └── ... (10个场景文件)
├── 📂 schemas/                    # 知识图谱模式
│   └── 📄 kg_schema.json
├── 📂 domains/                    # 领域知识图谱
│   └── 📂 textworld/
└── 📂 templates/                  # 知识图谱模板
```

### 数据抽取工具 (data/extraction/)
```
data/extraction/
├── 📄 extraction_config.yaml      # 抽取配置 (包含Neo4j配置)
├── 📄 rule_extractors.py         # 规则抽取器
├── 📄 state_kg_builder.py        # 状态知识图谱构建器
├── 📄 scene_separated_kg_builder.py # 场景分割构建器
├── 📄 neo4j_importer.py          # Neo4j导入器
├── 📄 build_and_import_kg.py     # 完整构建和导入流程
├── 📄 analyze_benchmark_data.py  # 数据分析工具
├── 📄 analyze_dataset_scale.py   # 数据集规模分析
├── 📄 test_basic_extraction.py   # 基础抽取测试
├── 📄 visualize_kg.py            # 知识图谱可视化
├── 📄 kg_mermaid_diagram.md      # 知识图谱文档和改造方法
├── 📄 dataset_scale_report.json  # 数据集规模报告
└── 📄 data_summary.json          # 数据摘要
```

### 处理数据 (data/processed/)
```
data/processed/
├── 📂 alfworld/                  # 处理后的ALFWorld数据
├── 📂 textworld/                 # 处理后的TextWorld数据
└── 📂 features/                  # 特征数据
```

### 原始数据 (data/raw/)
```
data/raw/
├── 📂 experiments/               # 实验原始数据
└── 📂 logs/                      # 日志文件
```

## 🔧 脚本工具 (scripts/)

### 构建脚本
```
scripts/
├── 📄 build_kg.py               # 知识图谱构建脚本
├── 📄 train_agent.py            # 智能体训练脚本
├── 📄 evaluate_model.py         # 模型评估脚本
└── 📄 run_experiments.py        # 实验运行脚本
```

## 📚 文档 (docs/)

### 研究文档 (docs/research/)
```
docs/research/
├── 📄 少样本LLMbaseline.md      # KG-Agent论文分析
├── 📄 图在AI多代理发挥的作用.md  # 图在AI中的作用研究
├── 📄 RL插件位置.md             # RL插件位置研究 (已修复Mermaid)
└── 📄 README_KG_CONSTRUCTION.md  # 知识图谱构建文档
```

### API文档 (docs/api/)
```
docs/api/
├── 📄 knowledge_graph_api.md    # 知识图谱API文档
├── 📄 agent_api.md              # 智能体API文档
└── 📄 environment_api.md        # 环境API文档
```

## ⚙️ 配置文件系统

### 配置文件结构
```
configs/
├── 📂 kg/                          # 知识图谱配置
│   └── 📄 kg_construction.yaml     # KG构建配置 (完整DODAF设置)
├── 📂 neo4j/                       # Neo4j数据库配置
│   ├── 📄 neo4j_config.yaml        # 数据库连接和导入配置
│   └── 📄 import_to_neo4j.py       # 专用导入脚本
├── 📂 extraction/                  # 数据抽取配置
│   └── 📄 extraction_config.yaml   # 多数据源抽取配置
├── 📂 agents/                      # 智能体配置
│   └── 📄 agent_config.yaml        # KG增强智能体配置
├── 📂 environments/                # 环境配置
│   └── 📄 environment_config.yaml  # 多环境配置
├── 📄 requirements.txt             # Python依赖
└── 📄 .gitignore                   # Git忽略文件
```

### 核心配置文件说明

#### 1. KG构建配置 (`configs/kg/kg_construction.yaml`)
```yaml
# DODAF架构设置
dodaf:
  views: ["OV-1", "SV-1", "SV-4", "SV-10c"]
  state_modeling:
    state_types: ["initial", "intermediate", "final", "error"]
    transition_types: ["deterministic", "probabilistic", "conditional"]

# 知识图谱设置
knowledge_graph:
  node_types: [ACTION, ENTITY, STATE, RESULT, CONDITION, RULE]
  edge_types: [REQUIRES, PRODUCES, MODIFIES, ENABLES, PREVENTS, TRANSITIONS, CONTAINS, HAS_STATE]
  validation: {check_consistency: true, max_nodes: 10000}
```

#### 2. Neo4j配置 (`configs/neo4j/neo4j_config.yaml`)
```yaml
# 数据库连接
database:
  connection:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    password: "yuanxi98"

# 导入设置
import:
  batch: {enabled: true, batch_size: 1000}
  database_management: {clear_before_import: true, create_indexes: true}

# 索引和约束
indexes:
  nodes: [{label: "Action", properties: ["id", "name"]}]
constraints:
  unique: [{label: "Action", property: "id"}]
```

#### 3. 数据抽取配置 (`configs/extraction/extraction_config.yaml`)
```yaml
# 多数据源配置
data_sources:
  alfworld:
    enabled: true
    data_types: {layouts: {max_files: 50}, pddl_problems: {max_files: 10}}
    extraction_rules: {objects: {infer_states: true, infer_actions: true}}

  textworld:
    enabled: true
    extraction_rules: {rooms: {create_scene_nodes: true}}

# 抽取策略
extraction_strategy:
  mode: "rule_based"  # 100%准确的规则抽取
  validation: true
```

## 🧪 测试文件 (tests/)

```
tests/
├── 📄 test_kg_builder.py         # 知识图谱构建器测试
├── 📄 test_agents.py             # 智能体测试
├── 📄 test_environments.py       # 环境测试
└── 📄 test_extraction.py         # 数据抽取测试
```

## 📊 数据统计

### 数据集规模
- **ALFWorld**: 240个场景，5,358个对象，25种对象类型
- **TextWorld**: 64个benchmark游戏，22个游戏文件
- **知识图谱**: 585个节点，596条边 (10个场景)

### 文件大小统计
- **合并KG**: alfworld_kg.json (111KB), textworld_kg.json (4.4KB)
- **分割KG**: 平均每场景 ~3-8KB
- **配置文件**: extraction_config.yaml (~5KB)

## 🚀 使用流程

### 1. 数据准备
```bash
# 下载benchmark数据
cd data/benchmarks/scripts
./download_alfworld.sh
./download_textworld.sh
```

### 2. 知识图谱构建
```bash
# 构建合并的知识图谱
python data/extraction/rule_extractors.py

# 构建按场景分割的知识图谱
python data/extraction/scene_separated_kg_builder.py

# 构建示例知识图谱并导入Neo4j
python data/extraction/build_and_import_kg.py
```

### 3. 数据分析
```bash
# 分析数据集规模
python data/extraction/analyze_dataset_scale.py

# 可视化知识图谱
python data/extraction/visualize_kg.py
```

### 4. Neo4j导入
```bash
# 导入到Neo4j数据库
python data/extraction/neo4j_importer.py
```

## 🎯 核心特性

- ✅ **规则抽取**: 100%准确的确定性抽取
- ✅ **场景分割**: 支持合并和分割两种模式
- ✅ **多格式支持**: JSON, GraphML, Neo4j
- ✅ **完整文档**: 包含改造方法和使用说明
- ✅ **可视化**: Mermaid图表展示结构
- ✅ **配置化**: 灵活的配置管理
