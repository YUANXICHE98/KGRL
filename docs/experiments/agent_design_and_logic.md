# KGRL智能体设计与代码逻辑详解

## 📋 **概述**

本文档详细描述了KGRL项目中三种智能体的设计思路、输入输出流程和代码逻辑。

## 🤖 **1. LLM基线智能体 (LLMBaselineAgent)**

### **设计思路**
- **目标**: 作为对比基线，使用纯LLM推理，不依赖任何外部知识
- **参考**: TextWorld (Côté et al., 2019), ALFWorld (Shridhar et al., 2020)
- **特点**: 简单直接，仅依赖预训练语言模型的内在知识

### **输入输出流程**

#### **输入数据结构**
```python
observation = {
    'scene': 'FloorPlan202-openable',
    'agent_location': 'FloorPlan202-openable', 
    'agent_inventory': [],
    'visible_entities': ['FloorPlan202-openable', 'ArmChair_689', 'CoffeeTable_992'],
    'available_actions': ['wait', 'close', 'pick_up', 'open', 'go_to', 'examine'],
    'step_count': 0,
    'description': '你现在在 FloorPlan202-openable。 你可以看到: FloorPlan202-openable, ArmChair_689, CoffeeTable_992。'
}
```

#### **处理步骤**

**步骤1: 信息提取**
```python
# 从观察中提取关键信息
available_actions = observation.get('available_actions', [])
visible_entities = observation.get('visible_entities', [])
inventory = observation.get('agent_inventory', [])
```

**步骤2: 构造LLM提示**
```python
prompt = f"""You are an AI agent in a household environment.

Current situation:
- Available actions: {available_actions}
- Visible entities: {visible_entities}
- Your inventory: {inventory}
- Previous actions: {self.action_history[-3:] if self.action_history else 'None'}

Your task is to explore the environment and interact with objects.

Please select ONE action and ONE target from the available options.
Respond in the format: "ACTION: <action_name> TARGET: <target_name>"

For example:
- ACTION: go_to TARGET: Cabinet_123
- ACTION: examine TARGET: Bed_456
- ACTION: pick_up TARGET: Apple_789

Choose wisely based on the current situation."""
```

**步骤3: 调用OpenAI API**
```python
from openai import OpenAI
client = OpenAI(api_key=openai.api_key)

response = client.chat.completions.create(
    model=self.model_name,  # "gpt-3.5-turbo"
    messages=[
        {"role": "system", "content": "You are an AI agent in a household environment. You need to select actions to complete tasks."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=150,
    temperature=0.7
)

raw_response = response.choices[0].message.content.strip()
```

**步骤4: 解析LLM响应**
```python
# 使用正则表达式提取ACTION和TARGET
action_match = re.search(r'ACTION:\s*(\w+)', response, re.IGNORECASE)
target_match = re.search(r'TARGET:\s*([^\s\n]+)', response, re.IGNORECASE)

if action_match and target_match:
    action = action_match.group(1).lower()
    target = target_match.group(1)
    
    # 验证动作和目标的有效性
    if action in available_actions:
        if action in ['go_to', 'examine', 'pick_up', 'open', 'close'] and target in visible_entities:
            return action, target
        elif action in ['wait']:
            return action, None
```

#### **输出数据结构**
```python
# 返回元组: (动作, 目标)
return ("go_to", "ArmChair_689")
```

#### **实际运行示例**
```
🔥 Calling real LLM (gpt-3.5-turbo)...
📝 LLM Prompt:
You are an AI agent in a household environment.
Current situation:
- Available actions: ['wait', 'close', 'pick_up', 'open', 'go_to', 'examine']
- Visible entities: ['FloorPlan202-openable', 'ArmChair_689', 'CoffeeTable_992']
- Your inventory: []
- Previous actions: None

🤖 Raw LLM Response:
ACTION: go_to TARGET: ArmChair_689

✅ Parsed action: go_to -> ArmChair_689
🎯 LLM Decision: go_to -> ArmChair_689
```

---

## 🧠 **2. ReAct智能体 (ReActAgent)**

### **设计思路**
- **目标**: 实现结构化的思考-行动-观察循环
- **参考**: ReAct (Yao et al., 2022), Reflexion (Shinn et al., 2023)
- **特点**: 显式的推理过程，包含思考、行动、观察三个阶段

### **输入输出流程**

#### **输入数据结构**
```python
# 与LLM基线相同的观察结构
observation = {
    'scene': 'FloorPlan202-openable',
    'agent_location': 'FloorPlan202-openable',
    'visible_entities': ['FloorPlan202-openable', 'ArmChair_689', 'CoffeeTable_992'],
    'available_actions': ['wait', 'close', 'pick_up', 'open', 'go_to', 'examine'],
    # ... 其他字段
}
```

#### **处理步骤**

**步骤1: THINK阶段 - 分析当前情况**
```python
def _think_phase(self, observation: Dict[str, Any]) -> str:
    """思考阶段：分析当前情况和制定策略"""
    
    # 分析当前状态
    location = observation.get('agent_location', 'unknown')
    visible_entities = observation.get('visible_entities', [])
    inventory = observation.get('agent_inventory', [])
    
    # 生成思考内容
    if not inventory and visible_entities:
        thought = f"I'm at {location} with no items. I should look for useful objects to pick up."
    elif inventory:
        thought = f"I have {inventory}. I should find a place to use these items."
    else:
        thought = f"I'm at {location}. I should explore the environment."
    
    return thought
```

**步骤2: ACT阶段 - 选择动作**
```python
def _act_phase(self, observation: Dict[str, Any], thought: str) -> Tuple[str, str]:
    """行动阶段：基于思考选择具体动作"""
    
    available_actions = observation.get('available_actions', [])
    visible_entities = observation.get('visible_entities', [])
    
    # 基于思考内容选择动作
    if "look for useful objects" in thought and 'examine' in available_actions:
        return 'examine', visible_entities[0] if visible_entities else None
    elif "explore" in thought and 'go_to' in available_actions:
        return 'go_to', visible_entities[1] if len(visible_entities) > 1 else visible_entities[0]
    else:
        return 'wait', None
```

**步骤3: OBSERVE阶段 - 处理执行结果**
```python
def _observe_phase(self, action: str, target: str, result: Dict[str, Any]) -> str:
    """观察阶段：分析动作执行结果"""
    
    reward = result.get('reward', 0)
    new_entities = result.get('visible_entities', [])
    
    if reward > 0:
        observation = f"Action {action} on {target} was successful. Reward: {reward}"
    else:
        observation = f"Action {action} on {target} had no immediate benefit."
    
    return observation
```

#### **输出数据结构**
```python
# 返回动作和推理轨迹
return ("examine", "ArmChair_689"), "I should examine this chair to understand its properties."
```

#### **实际运行示例**
```
🧠 ReAct Agent - Starting Think-Act-Observe cycle...
💭 THINK phase...
💡 Thought: I'm at FloorPlan202-openable with no items. I should look for useful objects to pick up.
🎬 ACT phase...
🎯 Action decision: examine -> ArmChair_689
📋 ReAct reasoning complete. Next: OBSERVE phase (after action execution)
```

---

## 🔍 **3. RAG智能体 (RAGAgent)**

### **设计思路**
- **目标**: 使用知识图谱检索增强决策过程
- **参考**: RAG (Lewis et al., 2020), WebGPT (Nakano et al., 2021)
- **特点**: 结合外部知识库，实现知识驱动的决策

### **输入输出流程**

#### **输入数据结构**
```python
# 相同的观察结构，但会进行知识检索
observation = {
    'scene': 'FloorPlan308-openable',
    'visible_entities': ['FloorPlan308-openable', 'Bed_937', 'Desk_335'],
    'available_actions': ['wait', 'close', 'pick_up', 'open', 'go_to', 'examine'],
    # ... 其他字段
}
```

#### **处理步骤**

**步骤1: 实体提取**
```python
def _extract_entities(self, observation: Dict[str, Any]) -> List[str]:
    """从观察中提取关键实体"""
    
    visible_entities = observation.get('visible_entities', [])
    inventory = observation.get('agent_inventory', [])
    
    # 提取实体类型（去除ID后缀）
    entities = []
    for entity in visible_entities + inventory:
        # 提取实体类型，如 "ArmChair_689" -> "ArmChair"
        entity_type = entity.split('_')[0] if '_' in entity else entity
        entities.append(entity_type)
    
    return list(set(entities))  # 去重
```

**步骤2: 知识检索**
```python
def _retrieve_knowledge(self, entities: List[str]) -> Dict[str, List[str]]:
    """从知识图谱检索相关知识"""
    
    knowledge = {}
    
    # 检索策略知识
    strategy_nodes = ['strategy_pick_up', 'strategy_open', 'strategy_go_to', 'strategy_examine']
    
    for strategy in strategy_nodes:
        if strategy in self.knowledge_base:
            knowledge[strategy] = self.knowledge_base[strategy]
    
    # 检索实体特定知识
    for entity in entities:
        if entity.lower() in self.knowledge_base:
            knowledge[entity] = self.knowledge_base[entity]
    
    return knowledge
```

**步骤3: 知识增强决策**
```python
def _generate_action_with_knowledge(self, observation: Dict[str, Any], 
                                   knowledge: Dict[str, List[str]]) -> Tuple[str, str]:
    """基于检索到的知识生成动作"""
    
    available_actions = observation.get('available_actions', [])
    visible_entities = observation.get('visible_entities', [])
    
    # 基于知识选择策略
    if 'strategy_examine' in knowledge and 'examine' in available_actions:
        # 使用检查策略
        return 'examine', visible_entities[0] if visible_entities else None
    elif 'strategy_go_to' in knowledge and 'go_to' in available_actions:
        # 使用移动策略
        return 'go_to', visible_entities[1] if len(visible_entities) > 1 else visible_entities[0]
    else:
        # 默认策略
        return 'wait', None
```

**步骤4: 收集访问的KG节点**
```python
def _collect_kg_nodes(self, knowledge: Dict[str, List[str]]) -> List[str]:
    """收集本次决策访问的所有KG节点"""
    
    accessed_nodes = []
    
    for strategy, items in knowledge.items():
        accessed_nodes.append(strategy)  # 策略节点
        accessed_nodes.extend(items)     # 策略内容节点
    
    return accessed_nodes
```

#### **输出数据结构**
```python
# 返回动作、目标和访问的KG节点
return ("go_to", "Bed_937"), ["strategy_go_to", "Explore systematically", "Visit kitchen for food items", "Check all rooms"]
```

#### **实际运行示例**
```
🔍 RAG Agent - Starting Retrieval-Augmented Generation...
🎯 Step 1: Extracting key entities...
📋 Extracted entities: []
🔍 Step 2: Retrieving knowledge from KG...
📚 Retrieved knowledge for 4 entities:
  - strategy_pick_up: 3 items
  - strategy_open: 3 items  
  - strategy_go_to: 3 items
  - strategy_examine: 3 items
🎬 Step 3: Generating action with retrieved knowledge...
🎯 Generated action: go_to -> FloorPlan308-openable
📊 Step 4: Collecting accessed KG nodes...
🔗 Total KG nodes accessed: 16
📝 KG nodes: ['strategy_pick_up', 'Pick up useful items first', 'Check inventory space', 'Prioritize keys and tools', 'strategy_open', 'Try keys on locked containers', 'Check if already open', 'Look inside after opening', 'strategy_go_to', 'Explore systematically', 'Visit kitchen for food items', 'Check all rooms', 'strategy_examine', 'Get detailed information', 'Understand object properties', 'Plan next actions']
🔗 访问了 16 个KG节点
```

---

## 📊 **4. 智能体对比总结**

| 特征 | LLM基线 | ReAct | RAG |
|------|---------|-------|-----|
| **知识来源** | 预训练模型内在知识 | 预训练模型 + 结构化推理 | 预训练模型 + 外部知识图谱 |
| **推理过程** | 直接决策 | Think-Act-Observe循环 | Retrieve-Generate流程 |
| **KG节点访问** | 0个 | 0个 | 16个 |
| **决策透明度** | 低（黑盒LLM） | 高（显式推理步骤） | 中（知识检索可见） |
| **计算复杂度** | 低 | 中 | 高 |
| **可解释性** | 低 | 高 | 中 |

## 🔧 **5. 技术实现细节**

### **配置管理**
- 使用`src/utils/simple_config.py`统一管理配置
- API密钥通过配置文件安全加载
- 支持不同模型和参数配置

### **错误处理**
- LLM调用失败时直接抛出异常，不使用模拟回退
- 响应解析失败时提供详细错误信息
- 所有实验要求使用真实LLM响应

### **日志记录**
- 详细记录每个决策步骤的输入输出
- 包含LLM原始响应和解析结果
- 支持后续分析和调试

### **性能监控**
- 记录每步决策时间
- 统计KG节点访问次数
- 追踪奖励和成功率指标

---

## 🎯 **6. 实验追踪系统**

### **路径追踪器 (AgentPathTracker)**

#### **数据结构**
```python
step_record = {
    'episode': self.current_episode,
    'step': step,
    'timestamp': datetime.now().isoformat(),
    'agent': agent_name,
    'action': action,
    'target': target,
    'reward': reward,
    'kg_nodes_accessed': kg_nodes_accessed,  # RAG智能体特有
    'reasoning_trace': reasoning_trace,      # 推理轨迹
    'scene': self.scene_name,
    'visible_entities': observation.get('visible_entities', []),
    'available_actions': observation.get('available_actions', []),
    'agent_location': observation.get('agent_location', ''),
    'agent_inventory': observation.get('agent_inventory', [])
}
```

#### **智能体路径表格格式**
```
| Round | Agent | Action | Target | KG Nodes Accessed | Num Nodes | Reward |
|-------|-------|--------|--------|-------------------|-----------|--------|
| 1     | llm_baseline | go_to | ArmChair_689 | [] | 0 | 0.090 |
| 1     | react | wait | FloorPlan202-openable | [] | 0 | -0.010 |
| 1     | rag | go_to | FloorPlan308-openable | [strategy_go_to, Explore systematically, ...] | 16 | 0.090 |
```

---

## 🏗️ **7. 系统架构设计**

### **模块依赖关系**
```
scripts/run_simple_experiment.py
├── src/agents/baseline_agents.py
│   ├── LLMBaselineAgent
│   ├── ReActAgent
│   └── RAGAgent
├── src/environments/scene_based_env.py
├── src/utils/simple_config.py
└── tools/visualization/agent_path_tracker.py
```

### **配置系统**
```yaml
# configs/simple_config.yaml
project:
  name: "KGRL"
  version: "1.0.0"

llm:
  model_name: "gpt-3.5-turbo"
  api_key: "sk-rvwMvUNbWBz9L76KB05650C7Cc464324BdC98dB3FbD4296a"
  temperature: 0.7
  max_tokens: 150

agents:
  llm_baseline:
    enabled: true
    model: "gpt-3.5-turbo"
  react:
    enabled: true
    max_reasoning_steps: 3
  rag:
    enabled: true
    knowledge_base_size: 3

environment:
  type: "alfworld"
  max_steps: 10
  scenes: ["FloorPlan202-openable", "FloorPlan308-openable"]

experiment:
  debug: true
  save_traces: true
  output_dir: "experiments/results"
```

### **知识图谱结构**
```python
knowledge_base = {
    'strategy_pick_up': [
        'Pick up useful items first',
        'Check inventory space',
        'Prioritize keys and tools'
    ],
    'strategy_examine': [
        'Get detailed information',
        'Understand object properties',
        'Plan next actions'
    ],
    'strategy_go_to': [
        'Explore systematically',
        'Visit kitchen for food items',
        'Check all rooms'
    ],
    'strategy_open': [
        'Try keys on locked containers',
        'Check if already open',
        'Look inside after opening'
    ]
}
```

---

## 🔬 **8. 实验结果分析**

### **典型行为模式**

#### **LLM基线智能体**
- **行为特征**: 在两个位置间循环移动 (ArmChair_689 ↔ FloorPlan202-openable)
- **决策依据**: 纯LLM推理，基于预训练知识
- **KG使用**: 无 (0个节点)
- **平均奖励**: 0.090 (正向探索奖励)

#### **ReAct智能体**
- **行为特征**: 重复执行wait动作
- **决策依据**: Think-Act-Observe循环，但思考过于保守
- **KG使用**: 无 (0个节点)
- **平均奖励**: -0.010 (等待惩罚)

#### **RAG智能体**
- **行为特征**: 重复执行go_to动作到同一位置
- **决策依据**: 基于检索到的策略知识
- **KG使用**: 高 (每步16个节点)
- **平均奖励**: 0.090 (探索奖励)

### **关键发现**
1. **RAG智能体确实在使用KG**: 每次决策访问16个策略节点
2. **所有智能体都存在循环行为**: 需要更好的状态记忆和避免重复机制
3. **知识检索有效**: RAG智能体能够检索到相关策略知识
4. **LLM调用成功**: 使用真实API密钥后，LLM响应正常

---

## 📈 **9. 性能指标定义**

### **基础指标**
- **步数 (Steps)**: 智能体执行的总动作数
- **奖励 (Reward)**: 累积奖励值
- **成功率 (Success Rate)**: 完成任务的比例
- **决策时间 (Decision Time)**: 每步决策耗时

### **知识图谱特定指标**
- **KG节点访问数 (KG Nodes Accessed)**: 每步访问的知识节点数量
- **知识利用率 (Knowledge Utilization)**: 检索知识的实际使用比例
- **检索精度 (Retrieval Precision)**: 检索到的相关知识比例

### **推理质量指标**
- **推理一致性 (Reasoning Consistency)**: 推理步骤的逻辑一致性
- **动作合理性 (Action Rationality)**: 选择动作的合理程度
- **探索效率 (Exploration Efficiency)**: 环境探索的效率

---

## 🛠️ **10. 调试和优化建议**

### **当前问题**
1. **循环行为**: 所有智能体都出现重复动作
2. **任务目标不明确**: 缺乏具体的任务指导
3. **状态记忆不足**: 智能体无法有效记住历史状态

### **优化方向**
1. **增强状态表示**: 包含更多环境状态信息
2. **改进奖励机制**: 设计更好的奖励函数避免循环
3. **任务导向设计**: 为智能体提供明确的任务目标
4. **记忆机制**: 实现更好的历史状态记忆

### **实验改进**
1. **多样化场景**: 测试更多不同类型的场景
2. **长期追踪**: 增加实验步数观察长期行为
3. **对比分析**: 详细分析不同智能体的决策差异
4. **知识库优化**: 改进知识图谱的内容和结构
