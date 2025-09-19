# KGRL 配置指南

本指南详细介绍KGRL框架的所有配置选项，帮助您自定义实验设置。

## 📋 配置文件结构

KGRL使用YAML格式的配置文件，按功能分类存储在不同目录中：

```
configs/
├── agents/          # 智能体配置
├── environments/    # 环境配置  
├── experiments/     # 实验配置
├── modes/          # 运行模式配置
└── kg/             # 知识图谱配置
```

## 🤖 智能体配置

### 基本配置结构
```yaml
# configs/agents/example_agent.yaml
agent_name: "example_agent"
agent_type: "UnifiedAgent"
description: "示例智能体配置"

# LLM基础设置
llm:
  model_name: "gpt-4o"
  temperature: 0.7
  max_tokens: 512
  api_key: "${OPENAI_API_KEY}"  # 环境变量

# 能力开关
capabilities:
  use_knowledge_graph: true
  use_memory: true
  use_enhanced_reasoning: false
  use_rl: false

# 组件特定配置
knowledge_graph:
  backend: "networkx"
  max_retrieved_docs: 5
  similarity_threshold: 0.7
  update_strategy: "evidence_based"

memory:
  short_term_size: 10
  medium_term_size: 50
  long_term_size: 100
  similarity_threshold: 0.6

reasoning:
  strategy: "react"
  max_iterations: 5
  confidence_threshold: 0.8

rl:
  algorithm: "ppo"
  learning_rate: 0.0003
  batch_size: 64
  gamma: 0.99
```

### 智能体类型

#### 1. LLM基线智能体
```yaml
agent_name: "llm_baseline"
agent_type: "LLMBaselineAgent"

llm:
  model_name: "gpt-4o"
  temperature: 0.7
  max_tokens: 300

capabilities:
  use_knowledge_graph: false
  use_memory: false
  use_enhanced_reasoning: false
  use_rl: false
```

#### 2. RAG/ReAct智能体
```yaml
agent_name: "rag_react_agent"
agent_type: "RAGReActAgent"

capabilities:
  use_knowledge_graph: true
  use_memory: true
  use_enhanced_reasoning: true
  use_rl: false

knowledge_graph:
  retrieval_method: "hybrid"  # keyword, semantic, hybrid
  max_retrieved_docs: 3
  rerank_results: true

reasoning:
  use_react: true
  use_chain_of_thought: true
  max_react_iterations: 3
```

#### 3. RL KG智能体
```yaml
agent_name: "rl_kg_agent"
agent_type: "RLKGAgent"

capabilities:
  use_knowledge_graph: true
  use_memory: false
  use_enhanced_reasoning: false
  use_rl: true

rl:
  algorithm: "ppo"
  policy_network:
    hidden_sizes: [256, 256]
    activation: "relu"
  value_network:
    hidden_sizes: [256, 256]
    activation: "relu"
  learning_rate: 0.0003
  clip_epsilon: 0.2
  entropy_coefficient: 0.01
```

#### 4. 统一智能体
```yaml
agent_name: "unified_agent"
agent_type: "UnifiedAgent"

capabilities:
  use_knowledge_graph: true
  use_memory: true
  use_enhanced_reasoning: true
  use_rl: true

# 所有组件的详细配置
knowledge_graph:
  backend: "networkx"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  vector_store: "faiss"
  
memory:
  use_short_term: true
  use_medium_term: true
  use_long_term: true
  
reasoning:
  primary_strategy: "react"
  fallback_strategy: "direct"
  
rl:
  algorithm: "ppo"
  use_curiosity: true
  intrinsic_reward_weight: 0.1
```

## 🌍 环境配置

### TextWorld环境
```yaml
# configs/environments/textworld.yaml
environment_type: "textworld"
environment_name: "cooking_game"

textworld:
  game_file: "data/games/cooking_simple.z8"
  max_episode_steps: 50
  observation_format: "text"
  action_space: "text"
  
  # 奖励设置
  reward_shaping:
    step_penalty: -0.01
    completion_reward: 1.0
    progress_reward: 0.1
    
  # 预处理设置
  preprocessing:
    lowercase: true
    remove_punctuation: false
    max_text_length: 500
```

### 自定义环境
```yaml
# configs/environments/custom_env.yaml
environment_type: "custom"
environment_name: "my_environment"

custom:
  class_path: "src.environments.my_custom_env.MyEnvironment"
  init_params:
    difficulty: "medium"
    seed: 42
    
  observation_space:
    type: "text"
    max_length: 1000
    
  action_space:
    type: "discrete"
    actions: ["north", "south", "east", "west", "take", "drop"]
```

## 🧪 实验配置

### 消融研究配置
```yaml
# configs/experiments/ablation_study.yaml
experiment_name: "ablation_study"
experiment_type: "ablation"
description: "系统性消融研究"

# 基础配置
base_config: "configs/agents/unified_agent.yaml"

# 消融变量
ablation_variables:
  - name: "knowledge_graph"
    values: [true, false]
    config_path: "capabilities.use_knowledge_graph"
    
  - name: "memory"
    values: [true, false]
    config_path: "capabilities.use_memory"
    
  - name: "reasoning"
    values: [true, false]
    config_path: "capabilities.use_enhanced_reasoning"
    
  - name: "rl"
    values: [true, false]
    config_path: "capabilities.use_rl"

# 实验设置
training:
  num_episodes: 100
  num_runs: 5  # 每个配置运行5次
  max_steps_per_episode: 30
  
evaluation:
  metrics: ["success_rate", "avg_steps", "decision_time", "knowledge_utilization"]
  statistical_tests: ["t_test", "mann_whitney"]
  significance_level: 0.05
```

### 基线对比配置
```yaml
# configs/experiments/baseline_comparison.yaml
experiment_name: "baseline_comparison"
experiment_type: "comparison"

# 对比的智能体配置
agents:
  - name: "llm_baseline"
    config: "configs/agents/llm_baseline.yaml"
    
  - name: "rag_react"
    config: "configs/agents/rag_react_agent.yaml"
    
  - name: "rl_kg"
    config: "configs/agents/rl_kg_agent.yaml"
    
  - name: "unified"
    config: "configs/agents/unified_agent.yaml"

# 实验设置
training:
  num_episodes: 200
  num_runs: 10
  
environments:
  - "configs/environments/textworld_easy.yaml"
  - "configs/environments/textworld_medium.yaml"
  - "configs/environments/textworld_hard.yaml"
```

## 🔄 运行模式配置

### 联合模式
```yaml
# configs/modes/joint_retrieve_update.yaml
mode_name: "joint_retrieve_update"
mode_type: "joint"
description: "知识检索和更新同时进行"

coordination:
  retrieve_and_update: "simultaneous"
  conflict_resolution: "confidence_based"
  
performance:
  cache_retrievals: true
  batch_updates: true
  max_concurrent_operations: 4
  
thresholds:
  update_confidence: 0.7
  retrieval_similarity: 0.6
  max_update_frequency: 10  # 每10步最多更新一次
```

### 解耦模式
```yaml
# configs/modes/decoupled_retrieve_first.yaml
mode_name: "decoupled_retrieve_first"
mode_type: "decoupled"
description: "先检索后更新的解耦模式"

sequence:
  primary_operation: "retrieve"
  secondary_operation: "update"
  switch_condition: "episode_end"
  
retrieve_phase:
  duration: "first_half"  # 前半段回合
  aggressive_retrieval: true
  cache_results: true
  
update_phase:
  duration: "second_half"  # 后半段回合
  batch_updates: true
  validate_updates: true
```

## 📊 知识图谱配置

### 图存储配置
```yaml
# configs/kg/graph_storage.yaml
backend: "networkx"  # networkx, neo4j, custom

networkx:
  graph_type: "MultiDiGraph"
  node_attributes: ["type", "confidence", "timestamp"]
  edge_attributes: ["relation", "confidence", "source"]
  
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "${NEO4J_PASSWORD}"
  database: "kgrl"
  
indexing:
  vector_store: "faiss"  # faiss, qdrant, chroma
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  index_refresh_interval: 100  # 每100次更新刷新索引
```

### 知识更新策略
```yaml
# configs/kg/update_strategy.yaml
update_strategy: "evidence_based"

evidence_based:
  confidence_threshold: 0.6
  evidence_aggregation: "weighted_average"
  conflict_resolution: "highest_confidence"
  
temporal:
  decay_factor: 0.95
  max_age_days: 30
  
validation:
  consistency_check: true
  schema_validation: true
  duplicate_detection: true
```

## ⚙️ 高级配置选项

### 性能优化
```yaml
performance:
  # 并行处理
  parallel_processing:
    enabled: true
    max_workers: 4
    
  # 缓存设置
  caching:
    llm_responses: true
    kg_retrievals: true
    cache_size_mb: 512
    
  # 内存管理
  memory_management:
    max_memory_mb: 2048
    gc_frequency: 100
    
  # GPU设置
  gpu:
    enabled: true
    device_id: 0
    mixed_precision: true
```

### 日志和监控
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  handlers:
    console:
      enabled: true
      level: "INFO"
      
    file:
      enabled: true
      level: "DEBUG"
      filename: "logs/kgrl_{timestamp}.log"
      max_size_mb: 100
      backup_count: 5
      
    wandb:
      enabled: false
      project: "kgrl_experiments"
      entity: "research_team"

monitoring:
  metrics_collection: true
  performance_profiling: false
  memory_tracking: true
  
  alerts:
    memory_threshold_mb: 1500
    error_rate_threshold: 0.1
    response_time_threshold_ms: 1000
```

## 🔧 配置验证和调试

### 配置验证
```bash
# 验证配置文件语法
python scripts/utils/validate_config.py \
    --config configs/agents/my_agent.yaml

# 验证配置完整性
python scripts/utils/validate_config.py \
    --config configs/agents/my_agent.yaml \
    --check-completeness

# 验证配置兼容性
python scripts/utils/validate_config.py \
    --agent-config configs/agents/my_agent.yaml \
    --env-config configs/environments/textworld.yaml \
    --check-compatibility
```

### 配置调试
```yaml
# 调试模式配置
debug:
  enabled: true
  verbose_logging: true
  save_intermediate_states: true
  
  breakpoints:
    - "before_action_selection"
    - "after_kg_retrieval"
    - "before_kg_update"
    
  profiling:
    enabled: true
    output_dir: "debug/profiles"
```

## 📝 配置最佳实践

### 1. 模块化配置
将复杂配置分解为多个文件：
```yaml
# 主配置文件
agent_name: "complex_agent"
imports:
  - "configs/components/llm_config.yaml"
  - "configs/components/kg_config.yaml"
  - "configs/components/rl_config.yaml"
```

### 2. 环境变量使用
敏感信息使用环境变量：
```yaml
llm:
  api_key: "${OPENAI_API_KEY}"
  
database:
  password: "${DB_PASSWORD}"
  
wandb:
  api_key: "${WANDB_API_KEY}"
```

### 3. 配置继承
基于基础配置创建变体：
```yaml
# 继承基础配置
base_config: "configs/agents/base_unified.yaml"

# 覆盖特定设置
overrides:
  capabilities.use_rl: false
  llm.temperature: 0.5
  memory.short_term_size: 20
```

### 4. 配置模板
为常见场景创建模板：
```yaml
# 快速实验模板
template: "quick_experiment"
num_episodes: 10
max_steps: 20
logging_level: "WARNING"

# 完整评估模板  
template: "full_evaluation"
num_episodes: 200
num_runs: 10
statistical_analysis: true
```

---

**提示：** 配置文件支持YAML的所有特性，包括锚点、引用和多行字符串。合理使用这些特性可以让配置更加简洁和可维护。

**最后更新：** 2024-01-01  
**版本：** 1.0.0  
**维护者：** KGRL研究团队
