# KGRL科研标准架构设计

## 设计原则

1. **职责清晰**：每个模块有明确的单一职责
2. **层次分明**：LLM基线 → RAG/ReAct → RL KG智能体的清晰层次
3. **配置驱动**：所有实验参数通过配置文件控制
4. **科研标准**：符合学术界的项目组织规范
5. **可扩展性**：支持多种环境和算法的扩展

## 新架构设计

```
kgrl-research/
├── README.md                              # 项目总览
├── requirements.txt                       # 依赖管理
├── setup.py                              # 包安装配置
│
├── configs/                              # 🎛️ 配置中心
│   ├── agents/                           # Agent配置
│   │   ├── llm_baseline.yaml            # LLM基线配置
│   │   ├── rag_react.yaml               # RAG/ReAct配置
│   │   ├── rl_kg_agent.yaml             # RL KG智能体配置
│   │   └── unified_agent.yaml           # 统一智能体配置
│   ├── environments/                     # 环境配置
│   │   ├── textworld.yaml               # TextWorld环境
│   │   └── alfworld.yaml                # ALFWorld环境
│   ├── experiments/                      # 实验配置
│   │   ├── ablation_study.yaml          # 消融实验
│   │   ├── baseline_comparison.yaml     # 基线对比
│   │   └── full_evaluation.yaml         # 完整评估
│   ├── modes/                           # 运行模式配置
│   │   ├── joint_retrieve_update.yaml   # 联合检索更新
│   │   ├── decoupled_update_first.yaml  # 先更新后检索
│   │   └── decoupled_retrieve_first.yaml # 先检索后更新
│   └── kg/                              # 知识图谱配置
│       ├── schema.yaml                  # KG模式定义
│       ├── storage.yaml                 # 存储配置
│       └── indexing.yaml                # 索引配置
│
├── data/                                # 📊 数据管理
│   ├── raw/                            # 原始数据
│   ├── processed/                      # 处理后数据
│   ├── kg/                            # 知识图谱数据
│   │   ├── schemas/                   # KG模式文件
│   │   ├── triples/                   # 三元组数据
│   │   ├── indexes/                   # 索引文件
│   │   └── snapshots/                 # KG快照
│   └── benchmarks/                    # 基准数据集
│
├── src/                               # 🧠 核心源码
│   ├── __init__.py
│   │
│   ├── agents/                        # 智能体实现
│   │   ├── __init__.py
│   │   ├── base_agent.py             # 基础智能体类
│   │   ├── llm_baseline.py           # LLM基线智能体
│   │   ├── rag_react_agent.py        # RAG/ReAct智能体
│   │   ├── rl_kg_agent.py            # RL KG智能体
│   │   └── unified_agent.py          # 统一智能体
│   │
│   ├── environments/                  # 环境适配
│   │   ├── __init__.py
│   │   ├── base_env.py               # 基础环境接口
│   │   ├── textworld_adapter.py      # TextWorld适配器
│   │   ├── alfworld_adapter.py       # ALFWorld适配器
│   │   └── wrappers.py               # 环境包装器
│   │
│   ├── knowledge/                     # 知识图谱系统
│   │   ├── __init__.py
│   │   ├── graph_manager.py          # 图管理器
│   │   ├── retriever.py              # 知识检索
│   │   ├── updater.py                # 知识更新
│   │   ├── indexer.py                # 索引管理
│   │   └── schema_manager.py         # 模式管理
│   │
│   ├── reasoning/                     # 推理系统
│   │   ├── __init__.py
│   │   ├── react_planner.py          # ReAct规划器
│   │   ├── dodaf_reasoner.py         # DODAF推理器
│   │   ├── chain_of_thought.py       # 思维链推理
│   │   └── strategy_selector.py      # 策略选择器
│   │
│   ├── rl/                           # 强化学习系统
│   │   ├── __init__.py
│   │   ├── algorithms/               # RL算法
│   │   │   ├── ppo_kg.py            # PPO + KG
│   │   │   └── dqn_kg.py            # DQN + KG
│   │   ├── policies/                 # 策略网络
│   │   │   ├── action_head.py       # 动作头
│   │   │   └── value_net.py         # 价值网络
│   │   ├── replay_buffer.py          # 经验回放
│   │   └── reward_shaping.py         # 奖励塑形
│   │
│   ├── integration/                   # 系统集成
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # 系统编排器
│   │   ├── mode_controller.py        # 模式控制器
│   │   └── pipeline_manager.py       # 流水线管理
│   │
│   ├── evaluation/                    # 评估系统
│   │   ├── __init__.py
│   │   ├── metrics.py                # 评估指标
│   │   ├── benchmarks.py             # 基准测试
│   │   └── analyzers.py              # 结果分析
│   │
│   └── utils/                        # 工具模块
│       ├── __init__.py
│       ├── config_loader.py          # 配置加载
│       ├── logging_utils.py          # 日志工具
│       ├── visualization.py          # 可视化工具
│       └── data_utils.py             # 数据工具
│
├── experiments/                       # 🧪 实验管理
│   ├── logs/                         # 实验日志
│   ├── checkpoints/                  # 模型检查点
│   ├── results/                      # 实验结果
│   │   ├── metrics/                  # 指标数据
│   │   ├── plots/                    # 图表
│   │   └── traces/                   # 执行轨迹
│   └── configs/                      # 实验特定配置
│
├── scripts/                          # 🚀 执行脚本
│   ├── train/                        # 训练脚本
│   │   ├── train_llm_baseline.py     # 训练LLM基线
│   │   ├── train_rag_react.py        # 训练RAG/ReAct
│   │   └── train_rl_kg.py            # 训练RL KG智能体
│   ├── evaluate/                     # 评估脚本
│   │   ├── run_ablation.py           # 消融实验
│   │   ├── run_comparison.py         # 对比实验
│   │   └── run_full_eval.py          # 完整评估
│   ├── data/                         # 数据处理脚本
│   │   ├── preprocess_data.py        # 数据预处理
│   │   ├── build_kg.py               # 构建知识图谱
│   │   └── create_indexes.py         # 创建索引
│   └── utils/                        # 工具脚本
│       ├── setup_env.py              # 环境设置
│       ├── export_results.py         # 结果导出
│       └── visualize_traces.py       # 轨迹可视化
│
├── tests/                            # 🧪 测试套件
│   ├── unit/                         # 单元测试
│   │   ├── test_agents.py
│   │   ├── test_knowledge.py
│   │   ├── test_reasoning.py
│   │   └── test_rl.py
│   ├── integration/                  # 集成测试
│   │   ├── test_pipeline.py
│   │   └── test_experiments.py
│   ├── system/                       # 系统测试
│   │   └── test_end_to_end.py
│   └── fixtures/                     # 测试数据
│
└── docs/                            # 📚 文档
    ├── README.md                    # 文档索引
    ├── architecture/                # 架构文档
    │   ├── overview.md              # 架构概览
    │   ├── agents.md                # 智能体设计
    │   ├── knowledge_graph.md       # 知识图谱设计
    │   └── integration.md           # 集成设计
    ├── tutorials/                   # 教程
    │   ├── quickstart.md            # 快速开始
    │   ├── configuration.md         # 配置指南
    │   └── experiments.md           # 实验指南
    ├── api/                         # API文档
    └── paper/                       # 论文相关
        ├── figures/                 # 论文图表
        ├── tables/                  # 论文表格
        └── references.bib           # 参考文献
```

## 核心设计特点

### 1. 清晰的层次结构
- **LLM基线**：`src/agents/llm_baseline.py` - 任务抓取和基础决策
- **RAG/ReAct**：`src/agents/rag_react_agent.py` - 检索增强和推理
- **RL KG智能体**：`src/agents/rl_kg_agent.py` - 强化学习主导决策
- **统一智能体**：`src/agents/unified_agent.py` - 集成所有能力

### 2. 配置驱动的实验
- `configs/modes/` - 不同运行模式的配置
- `configs/experiments/` - 实验参数配置
- `configs/agents/` - 智能体配置
- `configs/environments/` - 环境配置

### 3. 模块化知识图谱系统
- `src/knowledge/graph_manager.py` - 统一图管理
- `src/knowledge/retriever.py` - 检索策略
- `src/knowledge/updater.py` - 更新策略
- `src/knowledge/indexer.py` - 索引管理

### 4. 完整的实验管理
- `experiments/` - 所有实验数据和结果
- `scripts/` - 标准化的执行脚本
- `tests/` - 完整的测试覆盖

### 5. 科研标准文档
- `docs/architecture/` - 详细的架构文档
- `docs/tutorials/` - 使用教程
- `docs/paper/` - 论文相关材料

## 与现有架构的对比

| 方面 | 现有架构 | 新架构 |
|------|----------|--------|
| 目录结构 | 混乱，重复多 | 清晰，职责明确 |
| 配置管理 | 分散在多处 | 统一在configs/ |
| 实验管理 | results/和framework/results重复 | 统一在experiments/ |
| 代码组织 | src/和framework/功能重叠 | 单一src/，模块化 |
| 测试结构 | 测试分散 | 完整测试套件 |
| 文档组织 | 文档混乱 | 科研标准文档 |

## 迁移策略

1. **保留核心功能**：将现有的核心算法和实现迁移到新架构
2. **统一配置**：合并所有配置文件到configs/
3. **整合实验**：将所有实验相关内容移到experiments/
4. **标准化测试**：重新组织测试结构
5. **完善文档**：按科研标准重写文档

这个新架构将彻底解决现有的混乱问题，提供清晰的科研项目结构。
