# KGRL 实验指南

本指南详细介绍如何使用KGRL框架设计、运行和分析实验。

## 🧪 实验类型

### 1. 基线对比实验
比较不同智能体的性能：

```bash
# 运行基线对比
python scripts/evaluate/run_comparison.py \
    --config configs/experiments/baseline_comparison.yaml \
    --output experiments/results/baseline_comparison
```

### 2. 消融研究
系统性地分析各组件的贡献：

```bash
# 运行消融研究
python scripts/evaluate/run_ablation.py \
    --config configs/experiments/ablation_study.yaml \
    --output experiments/results/ablation_study
```

### 3. 超参数调优
优化模型超参数：

```bash
# 运行超参数搜索
python scripts/optimize/hyperparameter_search.py \
    --config configs/experiments/hyperparameter_tuning.yaml \
    --method grid_search  # grid_search, random_search, bayesian
```

### 4. 可扩展性测试
测试系统在不同规模下的性能：

```bash
# 运行可扩展性测试
python scripts/evaluate/scalability_test.py \
    --config configs/experiments/scalability_test.yaml \
    --scales small,medium,large,xlarge
```

## 📊 实验设计

### 基本实验配置
```yaml
# configs/experiments/my_experiment.yaml
experiment_name: "my_experiment"
experiment_type: "comparison"
description: "我的自定义实验"

# 实验参数
parameters:
  num_episodes: 100
  num_runs: 5
  max_steps_per_episode: 30
  random_seed: 42

# 智能体配置
agents:
  - name: "baseline"
    config: "configs/agents/llm_baseline.yaml"
  - name: "enhanced"
    config: "configs/agents/unified_agent.yaml"

# 环境配置
environments:
  - "configs/environments/textworld_easy.yaml"
  - "configs/environments/textworld_medium.yaml"

# 评估指标
metrics:
  - "success_rate"
  - "avg_steps"
  - "decision_time"
  - "knowledge_utilization"
  - "memory_efficiency"

# 统计分析
statistical_analysis:
  significance_tests: ["t_test", "mann_whitney"]
  effect_size: ["cohen_d", "cliff_delta"]
  confidence_level: 0.95
  multiple_comparison_correction: "bonferroni"
```

### 消融研究设计
```yaml
# configs/experiments/detailed_ablation.yaml
experiment_name: "detailed_ablation"
experiment_type: "ablation"

# 基础配置
base_config: "configs/agents/unified_agent.yaml"

# 消融变量（全因子设计）
ablation_variables:
  - name: "knowledge_graph"
    values: [true, false]
    config_path: "capabilities.use_knowledge_graph"
    
  - name: "memory_system"
    values: [true, false]
    config_path: "capabilities.use_memory"
    
  - name: "reasoning_type"
    values: ["none", "react", "chain_of_thought"]
    config_path: "reasoning.strategy"
    
  - name: "kg_retrieval_method"
    values: ["keyword", "semantic", "hybrid"]
    config_path: "knowledge_graph.retrieval_method"
    condition: "knowledge_graph == true"  # 条件消融

# 实验设置
training:
  num_episodes: 50
  num_runs: 3
  early_stopping:
    enabled: true
    patience: 10
    min_improvement: 0.01

# 分析设置
analysis:
  component_importance: true
  interaction_effects: true
  learning_curves: true
  statistical_power: 0.8
```

## 🚀 运行实验

### 单个实验
```bash
# 基本运行
python scripts/train/train_unified.py \
    --config configs/agents/my_agent.yaml \
    --num-episodes 100 \
    --output experiments/results/single_run

# 带详细日志
python scripts/train/train_unified.py \
    --config configs/agents/my_agent.yaml \
    --num-episodes 100 \
    --log-level DEBUG \
    --save-checkpoints \
    --output experiments/results/detailed_run
```

### 批量实验
```bash
# 运行多个配置
python scripts/evaluate/batch_experiments.py \
    --configs configs/agents/llm_baseline.yaml configs/agents/unified_agent.yaml \
    --num-runs 5 \
    --parallel 2 \
    --output experiments/results/batch_run

# 使用实验配置文件
python scripts/evaluate/run_experiment.py \
    --experiment-config configs/experiments/my_experiment.yaml \
    --parallel 4 \
    --resume-from experiments/results/my_experiment  # 断点续跑
```

### 分布式实验
```bash
# 使用多GPU
python scripts/train/distributed_training.py \
    --config configs/agents/rl_kg_agent.yaml \
    --gpus 0,1,2,3 \
    --strategy ddp

# 使用集群
python scripts/train/cluster_training.py \
    --config configs/experiments/large_scale_experiment.yaml \
    --nodes 4 \
    --tasks-per-node 8
```

## 📈 实验监控

### 实时监控
```bash
# 启动监控服务
python scripts/monitoring/start_monitor.py \
    --experiment-dir experiments/results/my_experiment \
    --port 8080

# 查看实时指标
python scripts/monitoring/live_metrics.py \
    --experiment my_experiment \
    --refresh-interval 10
```

### Weights & Biases集成
```yaml
# 在配置中启用W&B
logging:
  wandb:
    enabled: true
    project: "kgrl_experiments"
    entity: "research_team"
    tags: ["ablation", "textworld"]
    
    # 记录的指标
    metrics:
      - "episode_reward"
      - "success_rate"
      - "knowledge_queries"
      - "decision_time"
    
    # 记录的媒体
    media:
      - "learning_curves"
      - "attention_maps"
      - "knowledge_graph_evolution"
```

### TensorBoard集成
```bash
# 启动TensorBoard
tensorboard --logdir experiments/results/my_experiment/tensorboard

# 记录自定义指标
python scripts/utils/log_to_tensorboard.py \
    --experiment-dir experiments/results/my_experiment \
    --metrics success_rate,avg_steps,decision_time
```

## 📊 结果分析

### 基本统计分析
```bash
# 生成统计报告
python scripts/analysis/statistical_analysis.py \
    --results experiments/results/baseline_comparison \
    --output experiments/analysis/statistical_report.html

# 计算效应大小
python scripts/analysis/effect_size_analysis.py \
    --baseline experiments/results/llm_baseline \
    --treatment experiments/results/unified_agent \
    --metrics success_rate,avg_steps
```

### 可视化分析
```bash
# 生成性能对比图
python scripts/visualization/performance_plots.py \
    --results experiments/results/baseline_comparison \
    --output experiments/plots/performance_comparison.png

# 生成学习曲线
python scripts/visualization/learning_curves.py \
    --results experiments/results/training_logs \
    --smooth-window 10 \
    --output experiments/plots/learning_curves.png

# 生成消融研究热力图
python scripts/visualization/ablation_heatmap.py \
    --results experiments/results/ablation_study \
    --metric success_rate \
    --output experiments/plots/ablation_heatmap.png
```

### 高级分析
```python
# 自定义分析脚本示例
from src.analysis import ExperimentAnalyzer, StatisticalTester

# 加载实验结果
analyzer = ExperimentAnalyzer("experiments/results/my_experiment")

# 基本统计
stats = analyzer.compute_basic_statistics()
print(f"平均成功率: {stats['success_rate']['mean']:.3f} ± {stats['success_rate']['std']:.3f}")

# 显著性测试
tester = StatisticalTester()
p_value = tester.compare_groups(
    group1=analyzer.get_metric("baseline", "success_rate"),
    group2=analyzer.get_metric("enhanced", "success_rate"),
    test="mann_whitney"
)
print(f"显著性检验 p-value: {p_value:.4f}")

# 效应大小
effect_size = tester.compute_effect_size(
    group1=analyzer.get_metric("baseline", "success_rate"),
    group2=analyzer.get_metric("enhanced", "success_rate"),
    method="cohen_d"
)
print(f"Cohen's d: {effect_size:.3f}")
```

## 🔍 实验调试

### 调试模式
```bash
# 启用调试模式
python scripts/train/train_unified.py \
    --config configs/agents/my_agent.yaml \
    --debug \
    --save-states \
    --num-episodes 5

# 详细跟踪
python scripts/train/train_unified.py \
    --config configs/agents/my_agent.yaml \
    --trace-execution \
    --profile-performance \
    --output experiments/debug/trace_run
```

### 错误诊断
```bash
# 验证配置
python scripts/utils/validate_experiment.py \
    --config configs/experiments/my_experiment.yaml

# 检查数据完整性
python scripts/utils/check_results.py \
    --results-dir experiments/results/my_experiment \
    --fix-missing-data

# 性能分析
python scripts/utils/performance_analysis.py \
    --results experiments/results/my_experiment \
    --identify-bottlenecks
```

## 📋 实验最佳实践

### 1. 实验设计原则
- **控制变量**: 每次只改变一个变量
- **随机化**: 使用不同的随机种子
- **重复实验**: 多次运行确保结果可靠
- **统计功效**: 确保样本量足够

### 2. 结果记录
```yaml
# 完整的实验记录
experiment_metadata:
  date: "2024-01-01"
  researcher: "研究员姓名"
  hypothesis: "统一智能体比基线智能体性能更好"
  
  environment:
    python_version: "3.9.7"
    pytorch_version: "1.12.0"
    cuda_version: "11.6"
    hardware: "NVIDIA RTX 3080"
    
  data_sources:
    training_data: "data/textworld_games_v1.2"
    knowledge_base: "data/kg/cooking_domain.json"
    
  preprocessing:
    text_normalization: true
    knowledge_filtering: "confidence > 0.5"
```

### 3. 可重现性检查清单
- [ ] 固定随机种子
- [ ] 记录所有依赖版本
- [ ] 保存完整配置文件
- [ ] 记录数据预处理步骤
- [ ] 保存模型检查点
- [ ] 记录硬件环境信息

### 4. 结果验证
```bash
# 重现性测试
python scripts/validation/reproduce_results.py \
    --original-results experiments/results/published_results \
    --config configs/experiments/reproduction_test.yaml \
    --tolerance 0.05

# 交叉验证
python scripts/validation/cross_validation.py \
    --config configs/agents/my_agent.yaml \
    --folds 5 \
    --stratified
```

## 📊 实验报告生成

### 自动报告生成
```bash
# 生成完整实验报告
python scripts/reporting/generate_report.py \
    --experiment experiments/results/my_experiment \
    --template templates/experiment_report.html \
    --output experiments/reports/my_experiment_report.html

# 生成LaTeX表格
python scripts/reporting/generate_latex_tables.py \
    --results experiments/results/baseline_comparison \
    --output experiments/reports/tables.tex

# 生成论文图表
python scripts/reporting/generate_paper_figures.py \
    --results experiments/results/ablation_study \
    --style ieee \
    --output experiments/reports/figures/
```

### 报告模板
```html
<!-- templates/experiment_report.html -->
<!DOCTYPE html>
<html>
<head>
    <title>KGRL实验报告: {{experiment_name}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .metric { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        .significant { color: #d32f2f; font-weight: bold; }
    </style>
</head>
<body>
    <h1>实验报告: {{experiment_name}}</h1>
    
    <h2>实验概述</h2>
    <p>实验日期: {{date}}</p>
    <p>实验描述: {{description}}</p>
    
    <h2>主要结果</h2>
    {% for agent in agents %}
    <div class="metric">
        <h3>{{agent.name}}</h3>
        <p>成功率: {{agent.success_rate}} ± {{agent.success_rate_std}}</p>
        <p>平均步数: {{agent.avg_steps}} ± {{agent.avg_steps_std}}</p>
    </div>
    {% endfor %}
    
    <h2>统计分析</h2>
    {% for comparison in statistical_comparisons %}
    <p class="{% if comparison.significant %}significant{% endif %}">
        {{comparison.name}}: p = {{comparison.p_value}}
        {% if comparison.significant %}(显著){% endif %}
    </p>
    {% endfor %}
    
    <h2>可视化结果</h2>
    <img src="{{performance_plot}}" alt="性能对比图">
    <img src="{{learning_curves}}" alt="学习曲线">
</body>
</html>
```

## 🎯 高级实验技巧

### 1. 自适应实验
```python
# 基于中间结果调整实验参数
from src.experiments import AdaptiveExperiment

experiment = AdaptiveExperiment("adaptive_tuning")

# 定义适应策略
experiment.add_adaptation_rule(
    condition="success_rate < 0.3 after 20 episodes",
    action="increase learning_rate by 50%"
)

experiment.add_adaptation_rule(
    condition="decision_time > 1.0 seconds",
    action="reduce max_retrieved_docs to 3"
)

# 运行自适应实验
results = experiment.run()
```

### 2. 多目标优化
```yaml
# 多目标优化配置
optimization:
  objectives:
    - name: "success_rate"
      direction: "maximize"
      weight: 0.6
      
    - name: "decision_time"
      direction: "minimize"
      weight: 0.3
      
    - name: "knowledge_utilization"
      direction: "maximize"
      weight: 0.1
      
  method: "nsga2"  # 非支配排序遗传算法
  population_size: 50
  generations: 100
```

### 3. 在线学习实验
```bash
# 在线学习模式
python scripts/train/online_learning.py \
    --config configs/agents/online_agent.yaml \
    --stream-data data/streaming_episodes.jsonl \
    --adaptation-rate 0.01 \
    --evaluation-interval 100
```

---

**提示：** 实验设计是科学研究的核心。花时间仔细设计实验比匆忙运行大量实验更有价值。

**最后更新：** 2024-01-01  
**版本：** 1.0.0  
**维护者：** KGRL研究团队
