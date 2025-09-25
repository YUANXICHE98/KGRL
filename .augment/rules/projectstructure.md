---
type: "always_apply"
---

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


我希望你能够根据这个架构生成每一个文件，而不是乱放文件