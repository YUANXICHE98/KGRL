# KGRL 研究框架文档

欢迎使用 KGRL（知识图谱增强强化学习）研究框架文档。

## 📚 文档结构

### 架构文档
- [**架构概览**](architecture/overview.md) - 系统高层架构设计
- [**智能体设计**](architecture/agents.md) - 详细的智能体架构和能力
- [**知识图谱设计**](architecture/knowledge_graph.md) - 知识图谱系统设计与实现
- [**集成设计**](architecture/integration.md) - 系统集成和编排

### 教程指南
- [**快速开始指南**](tutorials/quickstart.md) - 10分钟快速上手KGRL
- [**配置指南**](tutorials/configuration.md) - 完整的配置参考
- [**实验指南**](tutorials/experiments.md) - 运行实验和消融研究

### API文档
- [**API参考**](api/) - 所有模块的完整API文档

### 论文材料
- [**图表**](paper/figures/) - 研究论文中使用的所有图表
- [**数据表**](paper/tables/) - 数据表格和实验结果
- [**参考文献**](paper/references.bib) - 参考书目和引用

## 🚀 快速导航

### 研究人员
- **初次使用KGRL？** 从[快速开始指南](tutorials/quickstart.md)开始
- **运行实验？** 查看[实验指南](tutorials/experiments.md)
- **理解系统？** 阅读[架构概览](architecture/overview.md)

### 开发人员
- **贡献代码？** 参考[API文档](api/)
- **添加新智能体？** 阅读[智能体设计](architecture/agents.md)
- **扩展知识图谱功能？** 查看[知识图谱设计](architecture/knowledge_graph.md)

### 论文写作
- **需要图表？** 浏览[论文图表](paper/figures/)
- **查找结果？** 检查[论文数据表](paper/tables/)
- **编写引用？** 使用[参考文献](paper/references.bib)

## 📖 核心概念

### 智能体层次结构
KGRL框架实现了清晰的智能体层次结构：

1. **LLM基线** - 纯语言模型，用于任务提取和基本决策
2. **RAG/ReAct智能体** - 增强了检索和推理能力
3. **RL KG智能体** - 强化学习与知识图谱集成
4. **统一智能体** - 集成所有能力的完整系统

### 配置驱动设计
所有实验都通过YAML配置文件控制：

- `configs/agents/` - 智能体特定配置
- `configs/environments/` - 环境设置
- `configs/experiments/` - 实验参数
- `configs/modes/` - 操作模式设置

### 模块化架构
系统采用模块化组件构建：

- **知识模块** - 图存储、检索和更新
- **推理模块** - ReAct、DODAF和思维链推理
- **强化学习模块** - 强化学习算法和策略
- **集成模块** - 系统编排和模式控制

## 🔧 常见任务

### 运行基础实验
```bash
# 训练LLM基线
python scripts/train/train_unified.py --config configs/agents/llm_baseline.yaml

# 运行消融研究
python scripts/evaluate/run_ablation.py --config configs/experiments/ablation_study.yaml
```

### 创建自定义配置
```yaml
# 智能体配置示例
agent_name: "my_custom_agent"
agent_type: "UnifiedAgent"
capabilities:
  use_knowledge_graph: true
  use_memory: true
  use_enhanced_reasoning: false
  use_rl: false
```

### 分析结果
```bash
# 生成图表
python scripts/utils/visualize_traces.py --results experiments/results/my_experiment

# 导出论文格式
python scripts/utils/export_results.py --format latex --output paper/tables/
```

## 🆘 获取帮助

### 常见问题
- **导入错误？** 检查Python路径和虚拟环境
- **配置错误？** 验证YAML语法和必需字段
- **性能问题？** 查看日志输出和系统资源

### 支持渠道
- **GitHub Issues** - 错误报告和功能请求
- **文档** - 全面的指南和API参考
- **示例** - `scripts/`目录中的工作示例

## 📝 贡献指南

我们欢迎贡献！请：

1. 阅读[架构概览](architecture/overview.md)以理解系统
2. 查看现有的[API文档](api/)了解接口
3. 遵循`configs/`中的配置模式
4. 为新功能添加测试
5. 根据需要更新文档

## 📊 研究影响

该框架已用于多个研究项目：

- **知识图谱增强强化学习** - 核心KGRL方法论
- **多模态决策制定** - 视觉和语言集成
- **消融研究** - 系统化组件分析
- **基准评估** - 标准任务性能评估

## 🔗 相关资源

### 外部链接
- [TextWorld环境](https://github.com/microsoft/TextWorld)
- [ALFWorld环境](https://github.com/alfworld/alfworld)
- [Stable Baselines3](https://github.com/DLR-RM/stable-baselines3)
- [NetworkX](https://networkx.org/)

### 学术论文
- 完整参考书目请参见[参考文献](paper/references.bib)
- 关键论文在各个文档部分中引用

---

**最后更新：** 2024-01-01
**版本：** 1.0.0
**维护者：** KGRL研究团队
