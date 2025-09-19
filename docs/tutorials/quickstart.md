# KGRL 快速开始指南

10分钟快速上手KGRL研究框架！

## 前置要求

- Python 3.8 或更高版本
- Git
- 推荐8GB+内存
- CUDA兼容GPU（可选，用于RL训练）

## 安装

### 1. 克隆仓库
```bash
git clone <repository-url>
cd kgrl-research
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate     # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 安装包
```bash
pip install -e .
```

### 5. 验证安装
```bash
python -c "import src.agents; print('KGRL安装成功！')"
```

## 你的第一个实验

### 1. 运行LLM基线
让我们从最简单的智能体开始 - 纯LLM基线：

```bash
python scripts/train/train_unified.py \
    --config configs/agents/llm_baseline.yaml \
    --num-episodes 10 \
    --max-steps 20
```

这将：
- 创建一个LLM基线智能体
- 运行10个训练回合
- 限制每个回合最多20步
- 将结果保存到`experiments/results/`

### 2. 检查结果
```bash
ls experiments/results/
# 你应该看到：
# - checkpoints/    (保存的智能体状态)
# - metrics/        (性能数据)
```

### 3. 查看训练指标
```bash
python -c "
import json
with open('experiments/results/metrics/training_metrics.json') as f:
    metrics = json.load(f)
print(f'成功率: {metrics[\"success_rate\"]:.2f}')
print(f'平均步数: {metrics[\"avg_steps\"]:.1f}')
"
```

## 理解配置

让我们看看LLM基线配置：

```yaml
# configs/agents/llm_baseline.yaml
agent_name: "llm_baseline"
agent_type: "LLMBaselineAgent"

# LLM设置
llm:
  model_name: "gpt-4o"
  temperature: 0.7
  max_tokens: 512

# 能力（基线全部禁用）
capabilities:
  use_knowledge_graph: false
  use_memory: false
  use_enhanced_reasoning: false
  use_rl: false
```

## 运行不同类型的智能体

### 2. RAG/ReAct智能体
添加知识图谱和推理能力：

```bash
python scripts/train/train_unified.py \
    --config configs/agents/rag_react_agent.yaml \
    --num-episodes 10
```

### 3. RL KG智能体
使用强化学习与知识图谱：

```bash
python scripts/train/train_unified.py \
    --config configs/agents/rl_kg_agent.yaml \
    --num-episodes 50  # RL需要更多回合
```

### 4. 完整系统
运行完整的KGRL系统：

```bash
python scripts/train/train_unified.py \
    --config configs/agents/unified_agent.yaml \
    --mode-config configs/modes/joint_retrieve_update.yaml \
    --num-episodes 20
```

## 运行消融研究

系统性地比较不同智能体配置：

```bash
python scripts/evaluate/run_ablation.py \
    --config configs/experiments/ablation_study.yaml
```

这将：
- 运行所有智能体配置
- 比较它们的性能
- 生成统计分析
- 创建可视化图表

## 可视化结果

### 1. 生成图表
```bash
python scripts/utils/visualize_traces.py \
    --results experiments/results/ablation_study \
    --output experiments/results/plots/
```

### 2. 查看性能比较
```bash
# 打开生成的HTML报告
open experiments/results/plots/performance_comparison.html
```

## 自定义你的实验

### 1. 创建自定义智能体配置
```yaml
# configs/agents/my_agent.yaml
agent_name: "my_custom_agent"
agent_type: "UnifiedAgent"

llm:
  model_name: "gpt-4o"
  temperature: 0.5

capabilities:
  use_knowledge_graph: true   # 启用KG
  use_memory: true           # 启用记忆
  use_enhanced_reasoning: false  # 禁用推理
  use_rl: false             # 禁用RL

knowledge_graph:
  max_retrieved_docs: 3
  similarity_threshold: 0.8

memory:
  short_term_size: 10
  medium_term_size: 50
```

### 2. 运行你的自定义智能体
```bash
python scripts/train/train_unified.py \
    --config configs/agents/my_agent.yaml \
    --num-episodes 15
```

## 理解输出

### 训练日志
```
INFO:train:开始KGRL训练
INFO:train:智能体已创建: UnifiedAgent(name=my_custom_agent, capabilities=['use_knowledge_graph', 'use_memory'])
INFO:train:回合 10/15: reward=1.50, steps=12, success=True
INFO:train:训练成功完成！
```

### 指标文件
- `training_metrics.json` - 逐回合性能
- `agent_statistics.json` - 整体智能体统计
- `checkpoints/` - 保存的智能体状态用于恢复

### 关键指标
- **成功率** - 成功回合的百分比
- **平均步数** - 完成任务的平均步数
- **决策时间** - 每次动作选择的时间
- **知识利用率** - KG查询频率

## 下一步

### 1. 探索不同环境
```bash
# 尝试不同的TextWorld场景
python scripts/train/train_unified.py \
    --config configs/agents/rag_react_agent.yaml \
    --env-config configs/environments/textworld.yaml
```

### 2. 运行综合评估
```bash
python scripts/evaluate/run_comparison.py \
    --config configs/experiments/baseline_comparison.yaml
```

### 3. 分析组件贡献
```bash
python scripts/evaluate/run_ablation.py \
    --config configs/experiments/ablation_study.yaml \
    --analysis-type component_contribution
```

## 常见问题和解决方案

### 问题：导入错误
```bash
# 解决方案：检查Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### 问题：CUDA内存不足
```yaml
# 解决方案：在配置中减少批大小
rl_algorithm:
  ppo:
    batch_size: 32  # 从64减少
```

### 问题：训练缓慢
```yaml
# 解决方案：减少回合长度
training:
  max_steps_per_episode: 25  # 从50减少
```

## 获取帮助

- **文档**: 查看`docs/`获取详细指南
- **示例**: 查看`scripts/`获取工作示例
- **问题**: 在GitHub上报告错误
- **配置**: 查看`configs/`获取所有选项

## 接下来做什么？

现在你已经运行了KGRL，可以探索：

1. **[配置指南](configuration.md)** - 详细配置选项
2. **[实验指南](experiments.md)** - 高级实验设置
3. **[架构概览](../architecture/overview.md)** - 系统设计细节
4. **[API参考](../api/)** - 完整API文档

祝你使用KGRL研究愉快！🚀
