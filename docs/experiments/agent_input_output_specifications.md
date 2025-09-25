# 智能体输入输出规格说明

## 🤖 **1. LLM基线智能体**

### **输入格式**
```python
observation = {
    'scene': 'FloorPlan308-openable',
    'agent_location': 'Kitchen',
    'agent_inventory': ['Key_1'],
    'visible_entities': ['Cabinet_0', 'Drawer_1', 'Apple_2'],
    'available_actions': ['go_to', 'pick_up', 'open', 'examine', 'wait'],
    'description': '你在厨房里，可以看到柜子、抽屉和苹果。'
}
```

### **内部处理流程**
```python
def select_action(self, observation):
    # 1. 构建上下文提示
    prompt = f"""
    当前状态:
    - 位置: {observation['agent_location']}
    - 库存: {observation['agent_inventory']}
    - 可见物品: {observation['visible_entities']}
    - 可用动作: {observation['available_actions']}
    - 环境描述: {observation['description']}
    
    请选择一个动作。回复格式: "动作 目标"
    你的选择:
    """
    
    # 2. 调用真实GPT-4o API
    messages = [
        {"role": "system", "content": "你是一个智能体，需要完成任务。"},
        {"role": "user", "content": prompt}
    ]
    
    response = self.llm_client.chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=512
    )
    
    # 3. 解析响应
    action, target = self._parse_response(response, observation)
    
    return action, target
```

### **输出格式**
```python
# 返回值
action = "pick_up"
target = "Apple_2"

# API调用示例
{
    "model": "gpt-4o",
    "messages": [...],
    "temperature": 0.7,
    "max_tokens": 512
}

# API响应示例
{
    "choices": [{
        "message": {
            "content": "pick_up Apple_2"
        }
    }]
}
```

### **实际问题**
- **输入**: 只收到场景名称，没有真实实体
- **处理**: GPT-4o无法理解空洞的观察
- **输出**: 回退到examine动作
- **结果**: 陷入examine循环，获得微小正奖励

---

## 🧠 **2. ReAct智能体**

### **输入格式**
```python
observation = {
    'scene': 'FloorPlan308-openable',
    'agent_location': 'Kitchen', 
    'visible_entities': ['Cabinet_0', 'Drawer_1'],
    'available_actions': ['go_to', 'open', 'examine'],
    'description': '厨房环境，有柜子和抽屉'
}
```

### **每轮处理流程**
```python
def select_action(self, observation):
    # 第1步：生成思考
    thought = self._generate_thought(observation)
    # 示例思考: "我看到柜子和抽屉，应该检查它们是否包含有用物品"
    
    # 第2步：基于思考推理动作
    action, target = self._reason_and_act(observation, thought)
    
    # 第3步：记录推理步骤
    reasoning_step = {
        'thought': thought,
        'action': action,
        'target': target,
        'observation': observation['description']
    }
    self.reasoning_steps.append(reasoning_step)
    
    return action, target

def _generate_thought(self, observation):
    """生成推理思考"""
    visible = observation.get('visible_entities', [])
    actions = observation.get('available_actions', [])
    
    # 基于当前状态生成思考
    if visible and 'examine' in actions:
        return f"我看到 {visible[:2]}，应该检查这些物品获取更多信息"
    elif 'go_to' in actions:
        return "我需要探索环境，寻找可交互的对象"
    else:
        return "我需要等待或重新评估情况"

def _reason_and_act(self, observation, thought):
    """基于思考选择动作"""
    available_actions = observation.get('available_actions', [])
    visible_entities = observation.get('visible_entities', [])
    
    # 基于思考内容选择动作
    if "检查" in thought and 'examine' in available_actions:
        if visible_entities:
            return "examine", visible_entities[0]
    elif "探索" in thought and 'go_to' in available_actions:
        if visible_entities:
            return "go_to", visible_entities[0]
    
    # 默认动作
    return "wait", None
```

### **输出格式**
```python
# 每轮输出
{
    'thought': "我看到 ['Cabinet_0', 'Drawer_1']，应该检查这些物品获取更多信息",
    'action': "examine",
    'target': "Cabinet_0"
}

# 推理历史
reasoning_steps = [
    {
        'thought': "我需要探索环境",
        'action': "examine", 
        'target': "Cabinet_0",
        'observation': "厨房环境"
    },
    {
        'thought': "柜子可能包含有用物品",
        'action': "open",
        'target': "Cabinet_0", 
        'observation': "柜子是关闭的"
    }
]
```

### **实际表现**
- **思考生成**: 基于有限观察生成合理思考
- **动作选择**: 比LLM更结构化，选择examine
- **循环问题**: 同样陷入examine循环
- **奖励获得**: 每次examine获得0.75奖励（比其他智能体高）

---

## 🔍 **3. RAG智能体**

### **输入格式**
```python
observation = {
    'scene': 'FloorPlan308-openable',
    'visible_entities': ['Cabinet_0', 'Drawer_1'],
    'available_actions': ['examine', 'open', 'go_to'],
    'agent_inventory': [],
    'description': '厨房场景'
}
```

### **检索和生成流程**
```python
def select_action(self, observation):
    # 第1步：提取关键实体
    key_entities = self._extract_key_entities(observation)
    # 示例: ['cabinet', 'drawer', 'kitchen']
    
    # 第2步：检索相关知识
    retrieved_knowledge = self._retrieve_knowledge(key_entities, observation)
    
    # 第3步：基于知识生成动作
    action, target = self._generate_action_with_knowledge(observation, retrieved_knowledge)
    
    return action, target

def _extract_key_entities(self, observation):
    """从观察中提取关键实体"""
    entities = []
    
    # 从可见实体中提取
    for entity in observation.get('visible_entities', []):
        # 提取实体类型（去掉编号）
        entity_type = entity.split('_')[0].lower()
        entities.append(entity_type)
    
    # 从描述中提取关键词
    description = observation.get('description', '').lower()
    keywords = ['kitchen', 'bedroom', 'bathroom', 'living']
    for keyword in keywords:
        if keyword in description:
            entities.append(keyword)
    
    return list(set(entities))  # 去重

def _retrieve_knowledge(self, entities, observation):
    """检索相关知识"""
    retrieved = {}
    
    # 1. 检索对象交互知识
    for entity in entities:
        if entity in self.knowledge_base['object_interactions']:
            retrieved[f"object_{entity}"] = self.knowledge_base['object_interactions'][entity]
    
    # 2. 检索动作策略知识
    available_actions = observation.get('available_actions', [])
    for action in available_actions:
        if action in self.knowledge_base['action_strategies']:
            retrieved[f"strategy_{action}"] = self.knowledge_base['action_strategies'][action]
    
    # 3. 检索任务模式知识
    context = observation.get('description', '').lower()
    for task_type, strategies in self.knowledge_base['task_patterns'].items():
        if any(keyword in context for keyword in ['cook', 'food']) and 'cooking' in task_type:
            retrieved[f"pattern_{task_type}"] = strategies
    
    return retrieved

def _generate_action_with_knowledge(self, observation, knowledge):
    """基于检索知识生成动作"""
    available_actions = observation.get('available_actions', [])
    visible_entities = observation.get('visible_entities', [])
    
    # 知识驱动的决策逻辑
    
    # 1. 如果知识建议检查容器
    if any('cabinet' in str(k) for k in knowledge.values()):
        cabinet_items = [e for e in visible_entities if 'cabinet' in e.lower()]
        if cabinet_items and 'examine' in available_actions:
            return "examine", cabinet_items[0]
    
    # 2. 如果知识建议打开容器
    if any('open' in str(k) for k in knowledge.values()):
        openable_items = [e for e in visible_entities if any(keyword in e.lower() 
                         for keyword in ['cabinet', 'drawer'])]
        if openable_items and 'open' in available_actions:
            return "open", openable_items[0]
    
    # 3. 默认策略：检查第一个可见实体
    if visible_entities and 'examine' in available_actions:
        return "examine", visible_entities[0]
    
    # 4. 最后备选：等待
    return "wait", None
```

### **知识库结构**
```python
knowledge_base = {
    'object_interactions': {
        'cabinet': [
            'Can be opened with keys',
            'May contain useful items', 
            'Check if locked first'
        ],
        'drawer': [
            'Can be opened',
            'Often contains small items',
            'May require key'
        ],
        'key': [
            'Can unlock doors, cabinets, drawers',
            'Usually found on tables or in containers'
        ]
    },
    'action_strategies': {
        'examine': [
            'Get detailed information',
            'Understand object properties',
            'Plan next actions'
        ],
        'open': [
            'Try keys on locked containers',
            'Check if already open',
            'Look inside after opening'
        ]
    },
    'task_patterns': {
        'cooking_task': [
            'Find ingredients',
            'Use cooking appliances',
            'Follow recipe steps'
        ]
    }
}
```

### **输出格式**
```python
# 检索结果示例
retrieved_knowledge = {
    'object_cabinet': ['Can be opened with keys', 'May contain useful items'],
    'strategy_examine': ['Get detailed information', 'Plan next actions'],
    'strategy_open': ['Try keys on locked containers', 'Look inside after opening']
}

# 最终动作
action = "examine"
target = "Cabinet_0"

# 检索历史
retrieval_history = [
    {
        'entities': ['cabinet', 'drawer'],
        'knowledge': {
            'object_cabinet': ['Can be opened with keys', 'May contain useful items'],
            'strategy_examine': ['Get detailed information']
        },
        'action': 'examine',
        'target': 'Cabinet_0'
    }
]
```

### **实际表现**
- **实体提取**: 成功提取cabinet, drawer等
- **知识检索**: 找到相关的对象交互知识
- **动作生成**: 基于知识选择examine动作
- **循环问题**: 同样陷入examine循环
- **奖励获得**: 每次examine获得0.6奖励

---

## 🚨 **共同问题分析**

### **环境问题**
1. **观察不完整**: 只提供场景名称，缺少真实KG实体
2. **状态更新失败**: 环境没有正确加载KG数据
3. **奖励机制**: examine给予小额正奖励，导致智能体陷入循环

### **智能体问题**
1. **缺乏探索**: 所有智能体都选择安全的examine动作
2. **没有状态记忆**: 不记住已经检查过的对象
3. **缺乏任务目标**: 没有明确的完成条件

### **解决方案**
1. **修复环境**: 确保正确加载KG实体和关系
2. **改进奖励**: 惩罚重复动作，奖励探索
3. **增加记忆**: 让智能体记住历史状态
4. **明确目标**: 提供清晰的任务完成条件
