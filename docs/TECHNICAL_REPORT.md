# KGRL项目技术报告

## 项目概述

KGRL (Knowledge Graph Reinforcement Learning) 是一个基于知识图谱增强的强化学习智能体框架，专门用于文本冒险游戏环境中的指令跟随任务。

## 核心架构

### 1. 系统组件图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Environment   │    │  Knowledge Graph │    │     Agent       │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ TextWorld   │ │    │ │ KG Builder  │ │    │ │ Baseline    │ │
│ │ (Simulated) │ │    │ │             │ │    │ │ LLM Agent   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ │ KG Retriever│ │    │ │ RAG Agent   │ │
│ │ ALFWorld    │ │    │ │             │ │    │ │ (Future)    │ │
│ │ (Optional)  │ │    │ └─────────────┘ │    │ └─────────────┘ │
│ └─────────────┘ │    └─────────────────┘    └─────────────────┘
└─────────────────┘                           
```

### 2. 数据流向

```
观察文本 → Agent → 动作选择 → 环境执行 → 新观察 + 奖励
    ↑                ↓
知识图谱 ← 检索查询 ← ReAct推理框架
```

## 详细组件分析

### 环境层 (Environment Layer)

**核心接口**: `BaseEnvironment`
```python
class BaseEnvironment:
    def reset() -> str                    # 重置环境，返回初始观察
    def step(action: str) -> Tuple        # 执行动作，返回(obs, reward, done, info)
    def get_available_actions() -> List   # 获取当前可用动作列表
```

**实现组件**:
- `TextWorldEnvironment`: 模拟TextWorld环境
- `ALFWorldEnvironment`: 家庭任务环境（可选）

**可替换性**: 
- 真实TextWorld ↔ 模拟环境
- 不同难度级别
- 不同任务类型

### 知识图谱层 (Knowledge Graph Layer)

**核心数据结构**:
```python
@dataclass
class KGFact:
    subject: str      # 主体
    predicate: str    # 谓词
    object: str       # 客体
    confidence: float # 置信度
```

**组件功能**:

1. **KnowledgeGraphBuilder**
   - 事实存储: JSON格式持久化
   - 图构建: NetworkX图结构
   - 关系推理: 基于规则的推理

2. **KnowledgeGraphRetriever**
   - 关键词检索: 精确匹配
   - 语义检索: TF-IDF + 余弦相似度
   - 图遍历: BFS/DFS路径查找

**检索接口**:
```python
def retrieve_by_keywords(query: str) -> List[KGFact]
def retrieve_by_similarity(query: str) -> List[KGFact]  
def retrieve_paths(start: str, end: str) -> List[Path]
```

### 智能体层 (Agent Layer)

**基础接口**: `BaseAgent`
```python
class BaseAgent:
    def act(observation: str, actions: List[str]) -> str
    def reset() -> None
    def get_stats() -> Dict
```

**实现组件**:

1. **BaselineAgent**
   - LLM调用: OpenAI GPT-4o API
   - Prompt工程: 任务特定提示词
   - 动作解析: 正则表达式提取

2. **RAGAgent** (计划中)
   - 知识检索: 集成KG检索器
   - ReAct推理: 思考-行动循环
   - 上下文融合: 观察+知识→决策

### 推理框架 (Reasoning Framework)

**ReAct循环**:
```
Thought: 分析当前情况
Action: 选择执行动作
Observation: 获取环境反馈
→ 重复直到任务完成
```

**实现细节**:
- 动作提取: `extract_action_from_*()` 方法族
- 思考生成: 结构化prompt模板
- 知识融合: 检索结果注入推理过程

## 技术栈

### 核心依赖
- **LLM API**: OpenAI GPT-4o (可配置base_url)
- **知识图谱**: NetworkX + 自定义JSON存储
- **文本处理**: scikit-learn TF-IDF
- **环境模拟**: 自研TextWorld兼容层

### 配置系统
```python
# API配置
OPENAI_API_KEY: str
OPENAI_BASE_URL: str = "https://vir.vimsai.com/v1"

# 环境配置  
ENVIRONMENT_TYPE: str = "textworld"
DIFFICULTY: str = "easy"
MAX_EPISODE_STEPS: int = 50

# Agent配置
MODEL_NAME: str = "gpt-4o"
TEMPERATURE: float = 0.7
MAX_TOKENS: int = 150
```

## 消融实验设计

### 可替换组件矩阵

| 组件类型 | 基线版本 | 变体1 | 变体2 | 变体3 |
|---------|---------|-------|-------|-------|
| **环境** | 模拟TextWorld | 真实TextWorld | ALFWorld | 自定义任务 |
| **LLM** | GPT-4o | GPT-3.5 | Claude | 本地模型 |
| **知识图谱** | 手工构建 | 自动抽取 | 预训练KG | 无KG |
| **检索方法** | TF-IDF | BM25 | 语义嵌入 | 图神经网络 |
| **推理框架** | ReAct | CoT | 直接推理 | 强化学习 |

### 实验配置
```python
# 消融实验配置示例
ABLATION_CONFIGS = {
    "baseline": {
        "agent": "BaselineAgent",
        "kg_enabled": False,
        "reasoning": "direct"
    },
    "kg_only": {
        "agent": "RAGAgent", 
        "kg_enabled": True,
        "reasoning": "direct"
    },
    "react_only": {
        "agent": "BaselineAgent",
        "kg_enabled": False, 
        "reasoning": "react"
    },
    "full_system": {
        "agent": "RAGAgent",
        "kg_enabled": True,
        "reasoning": "react"
    }
}
```

## 实验结果与分析

### 实验环境基准

**模拟TextWorld环境设计**:
- **3房间固定场景**: Kitchen → Living Room → Bedroom
- **标准任务**: "Find the key and open the chest in the bedroom"
- **房间配置**:
  - Kitchen: 包含apple, key；出口north
  - Living Room: 包含book；出口south, east
  - Bedroom: 包含pillow, chest；出口west
- **约束条件**: 最大30步，超时视为失败

### 真实实验结果

**实验规模**: 12 episodes (每种Agent 6个episodes)

| Agent类型 | 成功率 | 平均步数 | 平均奖励 | KG查询命中率 | API响应时间 |
|-----------|--------|----------|----------|--------------|-------------|
| Baseline LLM | 50.0% (3/6) | 21.3步 | 0.250 | N/A | ~2.5s |
| RAG LLM | 0.0% (0/6) | 30.0步 | -0.783 | 98.89% | ~4.0s |

### 详细分析

**Baseline Agent表现**:
- Episode 1,2,6: ✅ 成功 (9,20,9步)
- Episode 3,4,5: ❌ 失败 (30步超时)
- 成功模式: 快速找到key并到达bedroom

**RAG Agent表现**:
- 所有6个episodes: ❌ 失败 (30步超时)
- KG使用: 180次查询，178次命中 (98.89%命中率)
- 问题: 推理过程过于复杂，导致决策效率低下

### 关键发现

1. **技术可行性验证**: KG检索系统完全工作，98.89%命中率
2. **复杂性悖论**: 知识增强反而降低了性能
3. **推理效率问题**: ReAct框架可能过于复杂
4. **Prompt工程需求**: 需要优化知识融合策略

## 评估指标

### 性能指标
- **成功率**: 任务完成百分比
- **平均步数**: 完成任务所需步数
- **无效指令率**: 无效动作占比
- **知识利用率**: KG检索命中率

### 实现位置
- 真实实验脚本: `experiments/complete_real_experiment.py`
- RAG实验脚本: `run_real_rag_experiment.py`
- 结果分析: `scripts/analyze_results.py`
- 可视化: `src/utils/visualization.py`

### 实验数据位置
- **真实实验数据**: `results/real_rag_vs_baseline/data/real_experiment_results_20250829_124035.json`
- **CSV格式**: `results/real_rag_vs_baseline/data/real_experiment_results_20250829_124035.csv`
- **包含字段**: episode_id, agent_type, success, total_steps, total_reward, kg_queries, kg_hits, api_response_times等

## 扩展性设计

### 新环境接入
1. 继承`BaseEnvironment`
2. 实现标准接口方法
3. 注册到环境工厂

### 新Agent开发
1. 继承`BaseAgent`
2. 实现`act()`方法
3. 可选集成KG检索器

### 新知识源集成
1. 实现`KnowledgeSource`接口
2. 提供统一的事实提取方法
3. 集成到KG构建流程

## 实际运行示例

### 完整系统演示
```bash
# 运行完整系统演示
python -c "
import sys; sys.path.append('.')
from src.environments.textworld_env import TextWorldEnvironment
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.agents.baseline_agent import BaselineAgent

# 创建组件
env = TextWorldEnvironment('demo', {'difficulty': 'easy'})
kg = KnowledgeGraphBuilder('demo_kg')
kg.add_fact('kitchen', 'contains', 'fridge')
agent = BaselineAgent('demo_agent', {'model_name': 'gpt-4o'})

# 运行游戏循环
obs = env.reset()
action = agent.act(obs, env.get_available_actions())
new_obs, reward, done, info = env.step(action)
print(f'观察: {obs}')
print(f'动作: {action}')
print(f'奖励: {reward}')
"
```

### 输出示例
```
观察: You are in a kitchen. There is a fridge here. Goal: Find the key and open the chest in the bedroom.
动作: take key
奖励: 0.1
```

## 当前状态

### ✅ 已完成 (Week 1)
- [x] 模拟TextWorld环境 - 完全兼容API
- [x] 基础知识图谱系统 - JSON存储 + NetworkX
- [x] Baseline LLM Agent - GPT-4o集成
- [x] 真实API集成 - 自定义base_url支持
- [x] 完整的游戏循环 - 观察→决策→执行→反馈
- [x] 知识检索系统 - TF-IDF + 语义检索

### 🔄 进行中 (Week 2)
- [ ] RAG Agent实现 - 知识图谱集成
- [ ] ReAct推理框架 - 思考-行动循环
- [ ] 评估系统完善 - 自动化测试

### 📋 计划中 (Week 3+)
- [ ] ALFWorld环境集成 - 家庭任务场景
- [ ] 多模型对比实验 - GPT vs Claude vs 本地模型
- [ ] 知识图谱自动构建 - 从文本中抽取事实
- [ ] 强化学习集成 - PPO训练优化

## 性能基准

### 当前基线性能
```
环境: 模拟TextWorld (easy)
Agent: BaselineAgent + GPT-4o
结果: 
- 成功率: 待测试
- 平均步数: 待测试  
- API响应时间: ~2-3秒
- 知识检索时间: <100ms
```

## 数据流向详解

### 完整数据流程图

```
用户输入/环境重置
        ↓
┌─────────────────┐
│   Environment   │
│   - reset()     │ → 初始观察文本
│   - step()      │
└─────────────────┘
        ↓
┌─────────────────┐
│     Agent       │
│ - act(obs,acts) │ ← 观察文本 + 可用动作列表
└─────────────────┘
        ↓
┌─────────────────┐
│ Knowledge Graph │
│ - retrieve()    │ ← 查询关键词/语义
│ - build_index() │ → 相关事实列表
└─────────────────┘
        ↓
┌─────────────────┐
│ ReAct Framework │
│ - think()       │ ← 观察 + 知识 + 历史
│ - act()         │ → 结构化推理过程
└─────────────────┘
        ↓
┌─────────────────┐
│   LLM API       │
│ - chat()        │ ← 完整prompt
│ - parse()       │ → 动作字符串
└─────────────────┘
        ↓
┌─────────────────┐
│   Environment   │
│ - step(action)  │ ← 解析后的动作
│ - get_reward()  │ → (新观察, 奖励, 完成状态)
└─────────────────┘
```

### 关键接口规范

#### 1. 环境接口 (Environment Interface)
```python
class BaseEnvironment:
    def reset(self) -> str:
        """重置环境，返回初始观察"""

    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """执行动作，返回(观察, 奖励, 是否完成, 额外信息)"""

    def get_available_actions(self) -> List[str]:
        """获取当前状态下的可用动作列表"""

    def render(self) -> str:
        """渲染当前环境状态（可选）"""
```

#### 2. 知识图谱接口 (Knowledge Graph Interface)
```python
class KnowledgeGraphRetriever:
    def retrieve_by_keywords(self, query: str, max_results: int = 10) -> List[KGFact]:
        """基于关键词的精确检索"""

    def retrieve_by_similarity(self, query: str, threshold: float = 0.3) -> List[KGFact]:
        """基于语义相似度的模糊检索"""

    def retrieve_paths(self, start: str, end: str, max_depth: int = 3) -> List[List[KGFact]]:
        """检索两个实体间的关系路径"""

    def build_index(self, facts: List[KGFact]) -> None:
        """构建检索索引（TF-IDF + 图结构）"""
```

#### 3. Agent接口 (Agent Interface)
```python
class BaseAgent:
    def act(self, observation: str, available_actions: List[str]) -> str:
        """根据观察和可用动作选择最佳动作"""

    def reset(self) -> None:
        """重置Agent内部状态"""

    def get_stats(self) -> Dict[str, Any]:
        """获取Agent性能统计信息"""

    def update_knowledge(self, facts: List[KGFact]) -> None:
        """更新Agent的知识库（可选）"""
```

## 实验配置详解

### 消融实验配置矩阵

```python
EXPERIMENT_CONFIGS = {
    # 基线实验：纯LLM，无任何增强
    "baseline": {
        "agent_class": "BaselineAgent",
        "model_name": "gpt-4o",
        "use_knowledge_graph": False,
        "use_react_reasoning": False,
        "temperature": 0.7,
        "max_tokens": 100
    },

    # 知识图谱增强：LLM + KG检索
    "kg_enhanced": {
        "agent_class": "RAGAgent",
        "model_name": "gpt-4o",
        "use_knowledge_graph": True,
        "use_react_reasoning": False,
        "kg_retrieval_method": "tfidf",
        "max_kg_facts": 5
    },

    # ReAct推理增强：LLM + 结构化推理
    "react_enhanced": {
        "agent_class": "BaselineAgent",
        "model_name": "gpt-4o",
        "use_knowledge_graph": False,
        "use_react_reasoning": True,
        "max_reasoning_steps": 3
    },

    # 完整系统：LLM + KG + ReAct
    "full_system": {
        "agent_class": "RAGAgent",
        "model_name": "gpt-4o",
        "use_knowledge_graph": True,
        "use_react_reasoning": True,
        "kg_retrieval_method": "semantic",
        "max_kg_facts": 5,
        "max_reasoning_steps": 3
    }
}
```

### 环境配置变体

```python
ENVIRONMENT_CONFIGS = {
    "easy": {
        "difficulty": "easy",
        "max_episode_steps": 20,
        "num_rooms": 3,
        "num_objects": 5
    },
    "medium": {
        "difficulty": "medium",
        "max_episode_steps": 35,
        "num_rooms": 5,
        "num_objects": 8
    },
    "hard": {
        "difficulty": "hard",
        "max_episode_steps": 50,
        "num_rooms": 8,
        "num_objects": 12
    }
}
```

## 性能监控和调试

### 日志系统
```python
# 日志级别配置
LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/kgrl.log",
            "level": "INFO"
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "Agent": {"level": "INFO"},
        "Environment": {"level": "INFO"},
        "KnowledgeGraph": {"level": "DEBUG"}
    }
}
```

### 性能指标收集
```python
class MetricsCollector:
    def __init__(self):
        self.episode_rewards = []
        self.episode_lengths = []
        self.success_rate = 0.0
        self.invalid_action_rate = 0.0
        self.kg_retrieval_hits = 0
        self.api_call_times = []

    def log_episode(self, reward: float, length: int, success: bool):
        """记录单个episode的结果"""

    def log_action(self, action: str, is_valid: bool, kg_used: bool):
        """记录单个动作的执行情况"""

    def get_summary(self) -> Dict[str, float]:
        """获取性能摘要统计"""
```

这个技术报告为后续的实验设计和系统优化提供了清晰的架构指导。
