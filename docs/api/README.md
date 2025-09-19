# KGRL API 参考文档

欢迎使用KGRL框架的API参考文档。本文档提供了所有模块、类和函数的详细说明。

## 📚 API 模块结构

### 智能体模块 (`src.agents`)
- [**BaseAgent**](agents/base_agent.md) - 所有智能体的抽象基类
- [**LLMBaselineAgent**](agents/llm_baseline_agent.md) - 纯LLM基线智能体
- [**RAGReActAgent**](agents/rag_react_agent.md) - RAG/ReAct增强智能体
- [**RLKGAgent**](agents/rl_kg_agent.md) - 强化学习知识图谱智能体
- [**UnifiedAgent**](agents/unified_agent.md) - 统一智能体系统

### 知识模块 (`src.knowledge`)
- [**GraphManager**](knowledge/graph_manager.md) - 知识图谱管理器
- [**KnowledgeRetriever**](knowledge/knowledge_retriever.md) - 知识检索器
- [**KnowledgeUpdater**](knowledge/knowledge_updater.md) - 知识更新器
- [**KnowledgeIndexer**](knowledge/knowledge_indexer.md) - 知识索引器
- [**SchemaManager**](knowledge/schema_manager.md) - 模式管理器

### 推理模块 (`src.reasoning`)
- [**ReActPlanner**](reasoning/react_planner.md) - ReAct推理规划器
- [**DODAFReasoner**](reasoning/dodaf_reasoner.md) - DODAF框架推理器
- [**StrategySelector**](reasoning/strategy_selector.md) - 推理策略选择器

### 强化学习模块 (`src.rl`)
- [**算法**](rl/algorithms.md) - PPO、DQN等RL算法
- [**策略**](rl/policies.md) - 各种策略实现
- [**环境**](rl/environments.md) - RL环境接口

### 环境模块 (`src.environments`)
- [**BaseEnvironment**](environments/base_environment.md) - 环境基类
- [**TextWorldAdapter**](environments/textworld_adapter.md) - TextWorld适配器
- [**ALFWorldAdapter**](environments/alfworld_adapter.md) - ALFWorld适配器

### 集成模块 (`src.integration`)
- [**SystemOrchestrator**](integration/system_orchestrator.md) - 系统编排器
- [**ModeController**](integration/mode_controller.md) - 模式控制器
- [**PipelineManager**](integration/pipeline_manager.md) - 管道管理器
- [**ExperimentRunner**](integration/experiment_runner.md) - 实验运行器

### 评估模块 (`src.evaluation`)
- [**AgentEvaluator**](evaluation/agent_evaluator.md) - 智能体评估器
- [**MetricsCalculator**](evaluation/metrics_calculator.md) - 指标计算器
- [**BenchmarkRunner**](evaluation/benchmark_runner.md) - 基准测试运行器

### 工具模块 (`src.utils`)
- [**日志工具**](utils/logging_utils.md) - 日志配置和管理
- [**指标工具**](utils/metrics.md) - 性能指标计算
- [**可视化工具**](utils/visualization.md) - 结果可视化
- [**配置工具**](utils/config_utils.md) - 配置文件处理

## 🚀 快速导航

### 按使用场景

#### 创建新智能体
1. 继承 [BaseAgent](agents/base_agent.md)
2. 实现必需的抽象方法
3. 配置能力模块
4. 添加到训练脚本

#### 扩展知识系统
1. 使用 [GraphManager](knowledge/graph_manager.md) 管理图数据
2. 通过 [KnowledgeRetriever](knowledge/knowledge_retriever.md) 检索信息
3. 使用 [KnowledgeUpdater](knowledge/knowledge_updater.md) 更新知识
4. 配置 [SchemaManager](knowledge/schema_manager.md) 管理模式

#### 添加推理能力
1. 实现 [ReActPlanner](reasoning/react_planner.md) 接口
2. 配置 [StrategySelector](reasoning/strategy_selector.md)
3. 集成到智能体决策流程

#### 运行实验
1. 配置 [ExperimentRunner](integration/experiment_runner.md)
2. 使用 [AgentEvaluator](evaluation/agent_evaluator.md) 评估性能
3. 通过 [MetricsCalculator](evaluation/metrics_calculator.md) 计算指标

### 按开发阶段

#### 开发阶段
- [BaseAgent](agents/base_agent.md) - 智能体开发基础
- [GraphManager](knowledge/graph_manager.md) - 知识图谱操作
- [日志工具](utils/logging_utils.md) - 调试和监控

#### 测试阶段
- [AgentEvaluator](evaluation/agent_evaluator.md) - 性能评估
- [BenchmarkRunner](evaluation/benchmark_runner.md) - 基准测试
- [MetricsCalculator](evaluation/metrics_calculator.md) - 指标分析

#### 部署阶段
- [SystemOrchestrator](integration/system_orchestrator.md) - 系统管理
- [ModeController](integration/mode_controller.md) - 运行模式控制
- [ExperimentRunner](integration/experiment_runner.md) - 实验执行

## 📖 使用示例

### 基本智能体创建
```python
from src.agents import UnifiedAgent
from src.knowledge import GraphManager

# 创建知识图谱管理器
kg_manager = GraphManager(backend="networkx")

# 创建统一智能体
agent = UnifiedAgent(
    name="my_agent",
    config={
        "capabilities": {
            "use_knowledge_graph": True,
            "use_memory": True,
            "use_enhanced_reasoning": False,
            "use_rl": False
        }
    },
    kg_manager=kg_manager
)
```

### 知识检索和更新
```python
from src.knowledge import KnowledgeRetriever, KnowledgeUpdater

# 检索相关知识
retriever = KnowledgeRetriever(kg_manager)
relevant_facts = retriever.retrieve_by_keywords(["door", "key"])

# 更新知识图谱
updater = KnowledgeUpdater(kg_manager)
updater.add_fact("player", "has", "key", confidence=0.9)
```

### 运行实验
```python
from src.integration import ExperimentRunner
from src.evaluation import AgentEvaluator

# 创建实验运行器
runner = ExperimentRunner("my_experiment")

# 运行评估
evaluator = AgentEvaluator()
results = evaluator.evaluate_agent(agent, num_episodes=10)
```

## 🔧 配置参考

### 智能体配置
```yaml
agent_name: "example_agent"
agent_type: "UnifiedAgent"
capabilities:
  use_knowledge_graph: true
  use_memory: true
  use_enhanced_reasoning: false
  use_rl: false
```

### 知识图谱配置
```yaml
knowledge_graph:
  backend: "networkx"
  max_retrieved_docs: 5
  similarity_threshold: 0.7
  update_strategy: "evidence_based"
```

### 实验配置
```yaml
experiment:
  name: "ablation_study"
  num_episodes: 50
  max_steps_per_episode: 30
  evaluation_metrics: ["success_rate", "avg_steps", "decision_time"]
```

## 📝 开发指南

### 代码风格
- 遵循PEP 8 Python代码风格
- 使用类型提示
- 编写详细的文档字符串
- 添加单元测试

### 错误处理
- 使用适当的异常类型
- 提供有意义的错误消息
- 实现优雅的降级处理
- 记录错误和警告

### 性能优化
- 使用缓存减少重复计算
- 实现延迟加载
- 优化数据结构选择
- 监控内存使用

## 🆘 常见问题

### 导入错误
确保正确设置PYTHONPATH：
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### 配置错误
验证YAML配置文件语法和必需字段。

### 性能问题
检查日志输出，监控系统资源使用。

## 🔗 相关资源

- [架构概览](../architecture/overview.md) - 系统整体设计
- [快速开始](../tutorials/quickstart.md) - 10分钟上手指南
- [配置指南](../tutorials/configuration.md) - 详细配置说明
- [实验指南](../tutorials/experiments.md) - 实验设计和执行

---

**最后更新：** 2024-01-01  
**版本：** 1.0.0  
**维护者：** KGRL研究团队
