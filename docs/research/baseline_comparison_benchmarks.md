# 基线对比基准文献

## 📚 文献分类与对比基准

### 1. LLM 基线智能体

#### 核心文献
- **TextWorld**: Côté et al., 2019 - "TextWorld: A Learning Environment for Text-based Games"
- **ALFWorld**: Shridhar et al., 2020 - "ALFWorld: Aligning Text and Embodied Environments for Interactive Learning"

#### 常见对比对象
- **Random Agent** - 随机动作基线
- **Bag-of-Words DQN** - 基于词袋模型的深度Q网络
- **LSTM-DQN** - 基于LSTM的深度Q网络
- **GPT/Seq2Seq微调** - 在ALFWorld上微调的语言模型

#### 发现的问题/局限
- ❌ **容易幻觉**: 生成不存在的动作或对象
- ❌ **动作效率低**: 缺乏长期规划能力
- ❌ **缺少长期记忆**: 策略不稳定，重复错误
- ❌ **多步推理失败率高**: 复杂任务完成率低

#### 增强动机
➡️ **引入ReAct框架**: 增加推理-行动交替，减少幻觉，提高复杂任务完成率

---

### 2. ReAct Agent

#### 核心文献
- **ReAct**: Yao et al., 2022 - "ReAct: Synergizing Reasoning and Acting in Language Models"
- **Reflexion**: Shinn et al., 2023 - "Reflexion: Language Agents with Verbal Reinforcement Learning"

#### 常见对比对象
- **BUTLER** (Shridhar et al., 2021) - ALFWorld transfer baseline
- **KG-DQN** - 知识图谱增强的深度Q网络 (TextWorld)
- **常识知识RL agent** - 基于常识知识库的强化学习智能体

#### 发现的问题/局限
- ✅ **多步推理更好**: 相比基线有显著提升
- ❌ **依赖LLM内部知识**: 缺少外部信息补充
- ❌ **动作规划局限**: 可能陷入循环或局部最优
- ❌ **知识更新不足**: 环境适应能力弱

#### 增强动机
➡️ **引入RAG检索增强**: 在推理过程中动态检索外部知识，提升鲁棒性

---

### 3. RAG / 检索增强智能体

#### 核心文献
- **RAG**: Lewis et al., 2020 - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- **WebGPT**: Nakano et al., 2021 - "WebGPT: Browser-assisted question-answering with human feedback"
- **Toolformer**: Schick et al., 2023 - "Toolformer: Language Models Can Teach Themselves to Use Tools"

#### 常见对比对象
- **TWC (TextWorld Commonsense)** - 引入外部知识库 (ConceptNet)
- **BUTLER+演示学习** - ALFWorld上的演示学习方法
- **REALM/FiD** - 基于检索的问答模型

#### 发现的问题/局限
- ✅ **缓解知识盲点**: 能够获取外部信息
- ❌ **检索噪声大**: 影响推理质量
- ❌ **缺乏结构化表达**: 难以进行参数空间推理
- ❌ **长期交互效率低**: 检索开销影响实时性

#### 增强动机
➡️ **引入知识图谱 (KG)**: 提供结构化状态建模
➡️ **结合RL优化**: 优化检索-推理策略

---

## 🎯 我们的KG增强方法定位

### 核心创新点
1. **场景级别KG**: 每个场景独立的知识图谱，避免信息混淆
2. **完整信息覆盖**: 包含benchmark原有的动作定义、目标、状态等
3. **结构化推理**: 基于图结构的状态-动作关系推理
4. **多智能体对比**: 同时对比LLM基线、ReAct、RAG三条线

### 预期优势
- ✅ **减少幻觉**: 基于真实的场景结构化信息
- ✅ **提高效率**: 图结构指导的动作选择
- ✅ **增强泛化**: 场景间的知识迁移能力
- ✅ **可解释性**: 基于图路径的决策解释

---

## 📊 实验设计对比

### 评估指标
1. **成功率** (Success Rate) - 任务完成百分比
2. **平均奖励** (Average Reward) - 累积奖励均值
3. **步数效率** (Step Efficiency) - 完成任务所需步数
4. **泛化能力** (Generalization) - 跨场景性能

### 基准数据集
- **ALFWorld**: 240个场景，5358个对象，25种对象类型
- **TextWorld**: 64个benchmark游戏，22个游戏文件

### 对比方法
1. **LLM Baseline** - 简单的语言模型智能体
2. **ReAct** - 推理-行动交替智能体
3. **RAG** - 检索增强生成智能体
4. **KG-Enhanced** (我们的方法) - 知识图谱增强智能体

---

## 📈 预期实验结果

### 假设验证
1. **H1**: KG增强智能体在复杂场景中表现优于基线方法
2. **H2**: 结构化知识能够减少动作选择的随机性
3. **H3**: 场景级别KG提供更好的局部优化能力
4. **H4**: 多模态信息融合提升整体性能

### 成功标准
- **成功率提升**: 相比最佳基线提升 > 10%
- **效率提升**: 平均步数减少 > 15%
- **稳定性**: 方差减少，性能更稳定
- **可扩展性**: 在新场景上快速适应

---

## 🔬 实验执行计划

### Phase 1: 基线复现 (1-2天)
- [ ] 实现LLM基线智能体
- [ ] 实现ReAct智能体
- [ ] 实现RAG智能体
- [ ] 验证基线性能

### Phase 2: KG构建 (2-3天)
- [ ] 构建场景级别知识图谱
- [ ] 验证KG完整性和正确性
- [ ] 优化KG结构和连接

### Phase 3: KG智能体 (3-4天)
- [ ] 实现KG增强智能体
- [ ] 集成图推理算法
- [ ] 优化动作选择策略

### Phase 4: 对比实验 (2-3天)
- [ ] 运行大规模对比实验
- [ ] 收集性能数据
- [ ] 分析结果和可视化

### Phase 5: 分析报告 (1-2天)
- [ ] 撰写实验报告
- [ ] 总结创新点和贡献
- [ ] 准备论文材料

---

## 📝 相关工作引用

```bibtex
@article{cote2019textworld,
  title={TextWorld: A Learning Environment for Text-based Games},
  author={Côté, Marc-Alexandre and others},
  journal={arXiv preprint arXiv:1806.11532},
  year={2019}
}

@article{shridhar2020alfworld,
  title={ALFWorld: Aligning Text and Embodied Environments for Interactive Learning},
  author={Shridhar, Mohit and others},
  journal={arXiv preprint arXiv:2010.03768},
  year={2020}
}

@article{yao2022react,
  title={ReAct: Synergizing Reasoning and Acting in Language Models},
  author={Yao, Shunyu and others},
  journal={arXiv preprint arXiv:2210.03629},
  year={2022}
}

@article{shinn2023reflexion,
  title={Reflexion: Language Agents with Verbal Reinforcement Learning},
  author={Shinn, Noah and others},
  journal={arXiv preprint arXiv:2303.11366},
  year={2023}
}

@article{lewis2020rag,
  title={Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks},
  author={Lewis, Patrick and others},
  journal={Advances in Neural Information Processing Systems},
  year={2020}
}

@article{nakano2021webgpt,
  title={WebGPT: Browser-assisted question-answering with human feedback},
  author={Nakano, Reiichiro and others},
  journal={arXiv preprint arXiv:2112.09332},
  year={2021}
}
```

---

## 🎯 总结

通过系统性的文献调研和基准设计，我们建立了完整的对比实验框架。这个框架不仅能够验证KG增强方法的有效性，还能为后续研究提供可靠的基准和参考。

关键创新在于**场景级别的知识图谱构建**和**多智能体系统性对比**，这将为文本环境中的智能体研究提供新的视角和方法。
