# KGRL Experiments

本目录包含KGRL项目的所有实验代码，按功能分类组织。

## 📁 目录结构

### baseline/ - 基线实验
基准性能测试和对比实验
- `week1_baseline.py` - Week1基线实验，建立性能基准
- `baseline_comparison.py` - 基线对比实验，测试不同配置

### agent_comparison/ - Agent对比实验  
不同智能体之间的性能对比
- `comprehensive_comparison.py` - 全面对比实验（Baseline vs React）
- `baseline_vs_react.py` - Baseline vs React Agent对比
- `react_vs_dodaf.py` - React vs DODAF Agent对比
- `memory_vs_basic.py` - Memory vs Basic Agent对比

### llm_evaluation/ - LLM评估实验
大语言模型性能评估和对比
- `model_comparison.py` - 不同LLM模型对比
- `performance_analysis.py` - LLM性能分析

### knowledge_graph/ - 知识图谱实验
知识图谱相关功能测试
- `kg_effectiveness.py` - KG有效性测试
- `dodaf_evaluation.py` - DODAF框架评估
- `query_strategy_test.py` - 查询策略测试

### integration/ - 集成测试实验
完整系统集成测试
- `full_pipeline_test.py` - 完整pipeline测试
- `stress_test.py` - 系统压力测试

## 🚀 运行实验

### 单个实验
```bash
# 运行基线实验
python experiments/baseline/week1_baseline.py

# 运行Agent对比实验
python experiments/agent_comparison/comprehensive_comparison.py

# 运行LLM评估实验
python experiments/llm_evaluation/model_comparison.py
```

### 批量运行
```bash
# 运行所有基线实验
python -m experiments.baseline.week1_baseline
python -m experiments.baseline.baseline_comparison

# 运行所有Agent对比实验
python -m experiments.agent_comparison.comprehensive_comparison
```

## 📊 实验结果

实验结果保存在 `results/` 目录下，按实验类型分类：
- `results/baseline/` - 基线实验结果
- `results/agent_comparison/` - Agent对比实验结果
- `results/llm_evaluation/` - LLM评估实验结果
- `results/knowledge_graph/` - 知识图谱实验结果
- `results/integration/` - 集成测试实验结果

## 🎯 实验标准

### 统一配置
所有实验使用统一的配置格式：
```python
experiment_config = {
    "experiment_name": "baseline_vs_react",
    "num_episodes": 10,
    "max_steps_per_episode": 30,
    "environment": {
        "type": "TextWorld",
        "difficulty": "easy"
    },
    "agents": [
        {
            "type": "BaselineAgent",
            "config": {...}
        },
        {
            "type": "ReactAgent", 
            "config": {...}
        }
    ]
}
```

### 统一结果格式
```python
experiment_results = {
    "experiment_name": "baseline_vs_react",
    "timestamp": "2024-01-01T00:00:00",
    "config": {...},
    "agents": [
        {
            "agent_type": "BaselineAgent",
            "episodes": 10,
            "success_rate": 0.6,
            "avg_steps": 15.2,
            "avg_response_time": 1.5
        }
    ],
    "comparison": {
        "success_rate_improvement": 0.2,
        "statistical_significance": 0.05
    }
}
```

## 🔧 添加新实验

1. 选择合适的分类目录
2. 创建实验文件，继承 `BaseExperiment` 类
3. 实现必要的方法：`setup()`, `run()`, `analyze()`, `save_results()`
4. 添加到相应的 `__init__.py` 文件中
5. 更新本README文档

## 📈 实验分析

使用 `scripts/analyze_results.py` 脚本分析实验结果：
```bash
python scripts/analyze_results.py --experiment baseline_vs_react
python scripts/analyze_results.py --compare baseline_vs_react react_vs_dodaf
```

## ⚠️ 注意事项

1. **API调用**: 实验涉及真实API调用，注意成本控制
2. **随机种子**: 设置固定随机种子确保结果可复现
3. **资源管理**: 长时间实验注意内存和存储管理
4. **错误处理**: 实现完善的错误处理和恢复机制
5. **日志记录**: 详细记录实验过程和异常情况

## 📝 实验报告

每个实验完成后会自动生成：
- JSON格式的详细结果数据
- CSV格式的统计摘要
- 可视化图表（PNG/PDF）
- Markdown格式的分析报告

查看实验报告：
```bash
# 查看最新实验结果
python scripts/show_latest_results.py

# 生成综合报告
python scripts/generate_report.py --experiments baseline_vs_react react_vs_dodaf
```
