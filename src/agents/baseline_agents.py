#!/usr/bin/env python3
"""
基线智能体实现
包含LLM基线、ReAct Agent、RAG Agent三条对比线
"""

import json
import random
import re
import os
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入简化配置管理器
from src.utils.simple_config import get_config

# 尝试导入OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True

    # 从简化配置获取API密钥和base_url
    try:
        config = get_config()
        api_key = config.get_api_key()
        base_url = config.get_base_url()

        if api_key and api_key.startswith('sk-'):
            openai.api_key = api_key
            print(f"✅ OpenAI API key loaded: {api_key[:10]}...")
            print(f"✅ API base URL: {base_url}")
        else:
            print("⚠️ API key not found or invalid, using simulated responses")
            OPENAI_AVAILABLE = False

    except Exception as e:
        print(f"⚠️ Failed to load config: {e}, using simulated responses")
        OPENAI_AVAILABLE = False

except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available, using simulated responses")


class LLMBaselineAgent:
    """
    LLM基线智能体
    参考: TextWorld (Côté et al., 2019), ALFWorld (Shridhar et al., 2020)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        self.model_name = config.get('model', 'claude-3-5-sonnet-20241022')
        self.action_history = []
        self.observation_history = []
        self.max_history = 10

        print(f"🤖 初始化LLM基线智能体 (模型: {self.model_name})")
    
    def reset(self, scene_info: Dict[str, Any] = None):
        """重置智能体"""
        self.action_history = []
        self.observation_history = []
    
    def select_action(self, observation: Dict[str, Any]) -> Tuple[str, str]:
        """选择动作 - 使用真实LLM或模拟实现"""
        print(f"\n🤖 LLM Baseline Agent - Processing observation...")
        print(f"📥 Raw observation: {observation}")

        # 记录观察
        self.observation_history.append(observation)
        if len(self.observation_history) > self.max_history:
            self.observation_history.pop(0)

        # 简单的LLM基线策略
        available_actions = observation.get('available_actions', [])
        visible_entities = observation.get('visible_entities', [])
        inventory = observation.get('agent_inventory', [])

        print(f"🔍 Extracted info:")
        print(f"  - Available actions: {available_actions}")
        print(f"  - Visible entities: {visible_entities}")
        print(f"  - Inventory: {inventory}")

        # 使用真实LLM或模拟推理
        if OPENAI_AVAILABLE and openai.api_key:
            action, target = self._call_real_llm(observation, available_actions, visible_entities, inventory)
        else:
            action, target = self._simulate_llm_reasoning(observation, available_actions, visible_entities, inventory)

        # 记录动作
        self.action_history.append((action, target))
        if len(self.action_history) > self.max_history:
            self.action_history.pop(0)

        print(f"🎯 LLM Decision: {action} -> {target}")
        return action, target

    def _call_real_llm(self, observation: Dict[str, Any], available_actions: List[str],
                      visible_entities: List[str], inventory: List[str]) -> Tuple[str, str]:
        """调用真实的LLM进行推理"""
        print(f"🔥 Calling real LLM ({self.model_name})...")

        # 构建提示
        prompt = self._build_llm_prompt(observation, available_actions, visible_entities, inventory)
        print(f"📝 LLM Prompt:")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")

        try:
            # 调用OpenAI API (新版本)
            from openai import OpenAI

            # 获取配置
            config = get_config()
            base_url = config.get_base_url()

            # 初始化客户端，支持自定义base_url
            client = OpenAI(
                api_key=openai.api_key,
                base_url=base_url
            )

            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an AI agent in a household environment. You need to select actions to complete tasks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3  # 降低随机性
            )

            raw_response = response.choices[0].message.content.strip()
            print(f"🤖 Raw LLM Response:")
            print(f"{'='*60}")
            print(raw_response)
            print(f"{'='*60}")

            # 解析响应
            action, target = self._parse_llm_response(raw_response, available_actions, visible_entities)
            print(f"✅ Parsed action: {action} -> {target}")

            return action, target

        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            print("🚫 No fallback - experiment requires real LLM responses")
            raise e  # 直接抛出异常，不使用模拟

    def _build_llm_prompt(self, observation: Dict[str, Any], available_actions: List[str],
                         visible_entities: List[str], inventory: List[str]) -> str:
        """构建LLM提示"""
        prompt = f"""You are an AI agent in a household environment.

Current situation:
- Available actions: {available_actions}
- Visible entities: {visible_entities}
- Your inventory: {inventory}
- Previous actions: {self.action_history[-3:] if self.action_history else 'None'}

TASK OBJECTIVES:
1. PRIMARY: Find and collect useful items (keys, tools, food items)
2. SECONDARY: Explore systematically to discover new areas and objects
3. TERTIARY: Interact with containers (cabinets, drawers) to find hidden items

STRATEGY:
- Examine objects before picking them up to understand their properties
- Prioritize keys and tools as they enable access to more areas
- Use go_to to move between different areas for exploration
- Open containers when you have appropriate keys

Please select ONE action and ONE target from the available options.
Respond in the format: "ACTION: <action_name> TARGET: <target_name>"

For example:
- ACTION: go_to TARGET: Cabinet_123
- ACTION: examine TARGET: Bed_456
- ACTION: pick_up TARGET: Apple_789

Choose wisely based on the current situation and task objectives."""

        return prompt

    def _parse_llm_response(self, response: str, available_actions: List[str],
                           visible_entities: List[str]) -> Tuple[str, str]:
        """解析LLM响应"""
        # 尝试提取ACTION和TARGET
        action_match = re.search(r'ACTION:\s*(\w+)', response, re.IGNORECASE)
        target_match = re.search(r'TARGET:\s*([^\s\n]+)', response, re.IGNORECASE)

        if action_match and target_match:
            action = action_match.group(1).lower()
            target = target_match.group(1)

            # 验证动作是否可用
            if action in available_actions:
                # 验证目标是否可见（对于需要目标的动作）
                if action in ['go_to', 'examine', 'pick_up', 'open', 'close'] and target in visible_entities:
                    return action, target
                elif action in ['wait']:
                    return action, None

        # 如果解析失败，抛出异常
        print(f"⚠️ Failed to parse LLM response")
        raise ValueError(f"Cannot parse LLM response: {response}")


    
    def update(self, observation: Dict[str, Any], action: str, target: str, 
               reward: float, next_observation: Dict[str, Any], done: bool):
        """更新智能体（基线不学习）"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'agent_type': 'llm_baseline',
            'model_name': self.model_name,
            'total_actions': len(self.action_history),
            'history_length': len(self.observation_history)
        }


class ReActAgent:
    """
    ReAct智能体 - 使用真实LLM进行Think-Act-Observe推理
    参考: ReAct (Yao et al., 2022), Reflexion (Shinn et al., 2023)
    """

    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        self.thought_history = []
        self.action_history = []
        self.observation_history = []
        self.reasoning_steps = []
        self.max_reasoning_steps = config.get('max_reasoning_steps', 5)
        self.model_name = config.get('model', 'claude-3-5-sonnet-20241022')

        print(f"🧠 初始化ReAct智能体 (模型: {self.model_name})")

    def reset(self, scene_info: Dict[str, Any] = None):
        """重置智能体"""
        self.thought_history = []
        self.action_history = []
        self.observation_history = []
        self.reasoning_steps = []
    
    def select_action(self, observation: Dict[str, Any]) -> Tuple[str, str]:
        """ReAct: Reasoning + Acting - 使用真实LLM"""
        print(f"\n🧠 ReAct Agent - Starting Think-Act-Observe cycle...")
        print(f"📥 Raw observation: {observation}")

        # 记录观察
        self.observation_history.append(observation)

        # 提取观察信息
        available_actions = observation.get('available_actions', [])
        visible_entities = observation.get('visible_entities', [])
        inventory = observation.get('agent_inventory', [])

        # 使用LLM进行ReAct推理
        action, target = self._llm_react_reasoning(observation, available_actions, visible_entities, inventory)

        # 记录动作历史
        self.action_history.append((action, target))

        print(f"📋 ReAct reasoning complete. Next: OBSERVE phase (after action execution)")
        return action, target

    def _llm_react_reasoning(self, observation: Dict[str, Any], available_actions: List[str],
                           visible_entities: List[str], inventory: List[str]) -> Tuple[str, str]:
        """使用真实LLM进行ReAct推理"""
        print(f"🔥 Calling real LLM for ReAct reasoning ({self.model_name})...")

        # 构建ReAct提示
        prompt = self._build_react_prompt(observation, available_actions, visible_entities, inventory)
        print(f"📝 ReAct LLM Prompt:")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")

        try:
            # 调用OpenAI API
            from openai import OpenAI
            from src.utils.simple_config import SimpleConfig

            config = SimpleConfig()
            api_key = config.get_api_key()
            base_url = config.get_base_url()

            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )

            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an AI agent using ReAct (Reasoning + Acting) methodology. Think step by step, then act."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3  # 降低随机性
            )

            raw_response = response.choices[0].message.content.strip()
            print(f"🤖 Raw ReAct LLM Response:")
            print(f"{'='*60}")
            print(raw_response)
            print(f"{'='*60}")

            # 解析ReAct响应
            action, target = self._parse_react_response(raw_response, available_actions, visible_entities)
            print(f"✅ Parsed ReAct action: {action} -> {target}")

            return action, target

        except Exception as e:
            print(f"❌ ReAct LLM call failed: {e}")
            print("🚫 No fallback - experiment requires real LLM responses")
            raise e

    def _build_react_prompt(self, observation: Dict[str, Any], available_actions: List[str],
                          visible_entities: List[str], inventory: List[str]) -> str:
        """构建ReAct提示"""
        # 获取历史推理步骤
        recent_history = ""
        if self.reasoning_steps:
            recent_history = "\nRecent reasoning history:\n"
            for i, step in enumerate(self.reasoning_steps[-3:]):
                recent_history += f"Step {i+1}: Thought: {step.get('thought', 'N/A')} -> Action: {step.get('action', 'N/A')} {step.get('target', 'N/A')}\n"

        prompt = f"""You are using ReAct (Reasoning + Acting) methodology in a household environment.

Current situation:
- Available actions: {available_actions}
- Visible entities: {visible_entities}
- Your inventory: {inventory}
- Previous actions: {self.action_history[-3:] if self.action_history else 'None'}{recent_history}

TASK OBJECTIVES:
1. PRIMARY: Find and collect useful items (keys, tools, food items)
2. SECONDARY: Explore systematically to discover new areas and objects
3. TERTIARY: Interact with containers (cabinets, drawers) to find hidden items

ReAct Process:
1. THINK: Analyze the current situation, consider task objectives, and reason about what to do next
2. ACT: Choose one specific action based on your reasoning that advances the task objectives

Please follow this format:
THINK: [Your reasoning about the current situation, task progress, and what you should do next]
ACT: ACTION: <action_name> TARGET: <target_name>

For example:
THINK: I can see a coffee table and an armchair. Since my primary objective is to find useful items, I should examine the coffee table first to see if there are any keys or tools on it before exploring other areas.
ACT: ACTION: examine TARGET: CoffeeTable_992

Now, think and act based on the current situation and task objectives:"""

        return prompt

    def _parse_react_response(self, response: str, available_actions: List[str],
                            visible_entities: List[str]) -> Tuple[str, str]:
        """解析ReAct响应"""
        # 提取THINK部分
        think_match = re.search(r'THINK:\s*(.+?)(?=ACT:|$)', response, re.DOTALL | re.IGNORECASE)
        if think_match:
            thought = think_match.group(1).strip()
            print(f"💭 LLM Thought: {thought}")
            self.thought_history.append(thought)

        # 提取ACTION和TARGET
        action_match = re.search(r'ACTION:\s*(\w+)', response, re.IGNORECASE)
        target_match = re.search(r'TARGET:\s*([^\s\n]+)', response, re.IGNORECASE)

        if action_match and target_match:
            action = action_match.group(1).lower()
            target = target_match.group(1)

            # 验证动作和目标
            if action in available_actions and target in visible_entities:
                return action, target
            else:
                print(f"⚠️ Invalid action/target, using fallback")

        # 回退策略
        if available_actions and visible_entities:
            return available_actions[0], visible_entities[0]

        raise ValueError(f"Cannot parse ReAct response: {response}")

    def _generate_thought(self, observation: Dict[str, Any]) -> str:
        """生成思考"""
        current_location = observation.get('agent_location', 'unknown')
        inventory = observation.get('agent_inventory', [])
        visible_entities = observation.get('visible_entities', [])
        
        # 模拟ReAct的思考过程
        if not inventory:
            thought = f"I'm at {current_location} with no items. I should look for useful objects to pick up."
        elif inventory and any('key' in item.lower() for item in inventory):
            thought = f"I have a key: {inventory}. I should look for something to unlock."
        elif visible_entities:
            thought = f"I can see: {visible_entities}. I should examine or interact with them."
        else:
            thought = "I need to explore more to find useful items or locations."
        
        return thought
    
    def _reason_and_act(self, observation: Dict[str, Any], thought: str) -> Tuple[str, str]:
        """基于思考进行推理和行动"""
        available_actions = observation.get('available_actions', [])
        visible_entities = observation.get('visible_entities', [])
        inventory = observation.get('agent_inventory', [])
        
        # ReAct推理链
        if "look for useful objects" in thought and 'pick_up' in available_actions:
            useful_items = [e for e in visible_entities if any(keyword in e.lower() 
                           for keyword in ['key', 'treasure', 'egg', 'apple'])]
            if useful_items:
                return "pick_up", useful_items[0]
        
        elif "look for something to unlock" in thought and 'open' in available_actions:
            lockable_items = [e for e in visible_entities if any(keyword in e.lower() 
                             for keyword in ['cabinet', 'drawer', 'chest', 'safe'])]
            if lockable_items:
                return "open", lockable_items[0]
        
        elif "examine or interact" in thought and 'examine' in available_actions:
            return "examine", visible_entities[0] if visible_entities else None
        
        elif "explore more" in thought and 'go_to' in available_actions:
            current_location = observation.get('agent_location', '')
            new_locations = [e for e in visible_entities if e != current_location]
            if new_locations:
                return "go_to", new_locations[0]
        
        # 默认行为
        if available_actions:
            return available_actions[0], visible_entities[0] if visible_entities else None
        
        return "wait", None
    
    def update(self, observation: Dict[str, Any], action: str, target: str, 
               reward: float, next_observation: Dict[str, Any], done: bool):
        """更新智能体 - ReAct可以进行反思"""
        # 简单的反思机制
        if reward < -0.1:  # 负奖励
            reflection = f"Action {action} on {target} resulted in negative reward {reward}. Should avoid similar actions."
            self.thought_history.append(f"Reflection: {reflection}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'agent_type': 'react',
            'total_thoughts': len(self.thought_history),
            'total_actions': len(self.action_history),
            'reasoning_steps': len(self.reasoning_steps),
            'recent_reasoning': self.reasoning_steps[-3:] if self.reasoning_steps else []
        }


class RAGAgent:
    """
    RAG (Retrieval-Augmented Generation) 智能体 - 使用真实LLM进行检索增强生成
    参考: RAG (Lewis et al., 2020), WebGPT (Nakano et al., 2021)
    """

    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        self.knowledge_base = {}
        self.scene_kg = {}  # 存储场景特定的KG
        self.retrieval_history = []
        self.action_history = []
        self.max_retrievals = config.get('max_retrievals', 5)
        self.model_name = config.get('model', 'gpt-3.5-turbo')
        self.knowledge_base_path = config.get('knowledge_base_path')
        self.current_scene = None

        # 加载知识库
        if self.knowledge_base_path:
            self._load_knowledge_base(self.knowledge_base_path)
        else:
            self._create_default_knowledge_base()

        print(f"🔍 初始化RAG智能体 (模型: {self.model_name}, 知识库路径: {self.knowledge_base_path})")
        print(f"📚 默认知识库条目: {len(self.knowledge_base)}")
    
    def _load_knowledge_base(self, kb_path: str):
        """加载外部知识库"""
        try:
            # 如果是目录，先创建默认知识库
            if os.path.isdir(kb_path):
                print(f"📁 知识库路径是目录: {kb_path}")
                self._create_default_knowledge_base()
                return

            # 如果是文件，直接加载
            with open(kb_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
                print(f"✅ 成功加载知识库文件: {kb_path}")
        except Exception as e:
            print(f"⚠️  加载知识库失败: {e}")
            self._create_default_knowledge_base()
    
    def _create_default_knowledge_base(self):
        """创建默认知识库"""
        self.knowledge_base = {
            'object_interactions': {
                'key': ['Can unlock doors, cabinets, drawers', 'Usually found on tables or in containers'],
                'cabinet': ['Can be opened with keys', 'May contain useful items', 'Check if locked first'],
                'drawer': ['Can be opened', 'Often contains small items', 'May require key'],
                'apple': ['Food item', 'Can be eaten', 'Often found in kitchen areas'],
                'egg': ['Fragile food item', 'Can be cooked', 'Handle carefully'],
                'microwave': ['Cooking appliance', 'Can heat food', 'Need to open first']
            },
            'action_strategies': {
                'pick_up': ['Pick up useful items first', 'Check inventory space', 'Prioritize keys and tools'],
                'open': ['Try keys on locked containers', 'Check if already open', 'Look inside after opening'],
                'go_to': ['Explore systematically', 'Visit kitchen for food items', 'Check all rooms'],
                'examine': ['Get detailed information', 'Understand object properties', 'Plan next actions']
            },
            'task_patterns': {
                'cooking_task': ['Find ingredients', 'Use cooking appliances', 'Follow recipe steps'],
                'cleaning_task': ['Find cleaning supplies', 'Clean systematically', 'Put items away'],
                'retrieval_task': ['Locate target item', 'Navigate efficiently', 'Handle carefully']
            }
        }
    
    def reset(self, scene_info: Dict[str, Any] = None):
        """重置智能体"""
        self.retrieval_history = []
        self.action_history = []

        # 加载场景特定的KG
        if scene_info and 'scene_name' in scene_info:
            self.current_scene = scene_info['scene_name']
            self._load_scene_kg(self.current_scene)

    def _load_scene_kg(self, scene_name: str):
        """加载场景特定的知识图谱"""
        if not self.knowledge_base_path or not os.path.isdir(self.knowledge_base_path):
            print(f"⚠️  无法加载场景KG: 知识库路径无效")
            return

        # 尝试加载动作-状态场景KG
        kg_file = os.path.join(self.knowledge_base_path, f"{scene_name}_action_state_kg.json")
        if not os.path.exists(kg_file):
            print(f"⚠️  场景KG文件不存在: {kg_file}")
            return

        try:
            with open(kg_file, 'r', encoding='utf-8') as f:
                self.scene_kg = json.load(f)
                print(f"✅ 成功加载场景KG: {kg_file}")
                print(f"📊 KG节点数: {len(self.scene_kg.get('nodes', []))}")
                print(f"📊 KG边数: {len(self.scene_kg.get('edges', []))}")
        except Exception as e:
            print(f"⚠️  加载场景KG失败: {e}")
            self.scene_kg = {}
    
    def select_action(self, observation: Dict[str, Any]) -> Tuple[str, str]:
        """RAG: 检索相关知识 + 使用LLM生成动作"""
        # 1. 从观察中提取关键信息
        key_entities = self._extract_key_entities(observation)

        # 2. 检索相关知识
        retrieved_knowledge = self._retrieve_knowledge(key_entities, observation)

        # 3. 使用LLM基于检索的知识生成动作
        available_actions = observation.get('available_actions', [])
        visible_entities = observation.get('visible_entities', [])
        inventory = observation.get('agent_inventory', [])

        action, target = self._llm_rag_generation(observation, retrieved_knowledge,
                                                available_actions, visible_entities, inventory)

        # 记录检索历史
        self.retrieval_history.append({
            'entities': key_entities,
            'knowledge': retrieved_knowledge,
            'action': action,
            'target': target
        })

        if len(self.retrieval_history) > self.max_retrievals:
            self.retrieval_history.pop(0)

        return action, target

    def select_action_with_tracking(self, observation: Dict[str, Any]) -> Tuple[str, str, List[str], str]:
        """RAG: 检索相关知识 + 生成动作，返回追踪信息"""
        print(f"\n🔍 RAG Agent - Starting Retrieval-Augmented Generation...")
        print(f"📥 Raw observation: {observation}")

        # 1. 从观察中提取关键信息
        print(f"🎯 Step 1: Extracting key entities...")
        key_entities = self._extract_key_entities(observation)
        print(f"📋 Extracted entities: {key_entities}")

        # 2. 检索相关知识
        print(f"🔍 Step 2: Retrieving knowledge from KG...")
        retrieved_knowledge = self._retrieve_knowledge(key_entities, observation)
        print(f"📚 Retrieved knowledge for {len(retrieved_knowledge)} entities:")
        for entity, knowledge in retrieved_knowledge.items():
            print(f"  - {entity}: {len(knowledge) if isinstance(knowledge, list) else 1} items")

        # 3. 使用真实LLM基于检索的知识生成动作
        print(f"🎬 Step 3: Generating action with retrieved knowledge using real LLM...")
        available_actions = observation.get('available_actions', [])
        visible_entities = observation.get('visible_entities', [])
        inventory = observation.get('agent_inventory', [])
        action, target = self._llm_rag_generation(observation, retrieved_knowledge,
                                                available_actions, visible_entities, inventory)
        print(f"🎯 Generated action: {action} -> {target}")

        # 4. 收集访问的KG节点
        print(f"📊 Step 4: Collecting accessed KG nodes...")
        kg_nodes_accessed = []
        kg_nodes_accessed.extend(key_entities)  # 提取的实体
        for entity, knowledge_list in retrieved_knowledge.items():
            kg_nodes_accessed.append(entity)
            if isinstance(knowledge_list, list):
                kg_nodes_accessed.extend([k for k in knowledge_list if isinstance(k, str)])

        print(f"🔗 Total KG nodes accessed: {len(kg_nodes_accessed)}")
        print(f"📝 KG nodes: {kg_nodes_accessed}")

        # 5. 生成推理轨迹
        reasoning_trace = f"RAG: Extracted {len(key_entities)} entities: {key_entities[:3]}..., "
        reasoning_trace += f"Retrieved knowledge for {len(retrieved_knowledge)} entities, "
        reasoning_trace += f"Selected action: {action} -> {target}"

        # 6. 记录历史
        self.retrieval_history.append({
            'entities': key_entities,
            'knowledge': retrieved_knowledge,
            'action': action,
            'target': target,
            'kg_nodes_accessed': kg_nodes_accessed,
            'reasoning_trace': reasoning_trace
        })

        if len(self.retrieval_history) > self.max_retrievals:
            self.retrieval_history.pop(0)

        return action, target, kg_nodes_accessed, reasoning_trace

    def _extract_key_entities(self, observation: Dict[str, Any]) -> List[str]:
        """从观察中提取关键实体 - 改进版本"""
        key_entities = []

        # 1. 直接使用可见实体名称
        visible_entities = observation.get('visible_entities', [])
        key_entities.extend(visible_entities)

        # 2. 从库存中提取
        inventory = observation.get('agent_inventory', [])
        key_entities.extend(inventory)

        # 3. 如果有场景KG，提取实体类型信息
        if self.scene_kg and 'nodes' in self.scene_kg:
            for entity_name in visible_entities + inventory:
                # 在KG中查找匹配的节点
                for node in self.scene_kg['nodes']:
                    if (node.get('name') == entity_name or
                        entity_name in node.get('name', '') or
                        node.get('name', '') in entity_name):

                        # 添加实体类型信息
                        attrs = node.get('attributes', {})
                        if 'object_type' in attrs:
                            key_entities.append(attrs['object_type'].lower())
                        if 'entity_type' in attrs:
                            key_entities.append(attrs['entity_type'].lower())

        # 4. 添加通用策略实体（保持向后兼容）
        key_entities.extend(['examine', 'pick_up', 'open', 'go_to'])

        return list(set(key_entities))  # 去重
    
    def _retrieve_knowledge(self, key_entities: List[str], observation: Dict[str, Any]) -> Dict[str, List[str]]:
        """检索相关知识 - 改进版本"""
        retrieved = {}

        # 1. 从场景KG中检索实体特定知识
        if self.scene_kg and 'nodes' in self.scene_kg:
            for entity in key_entities:
                entity_info = self._get_entity_info_from_kg(entity)
                if entity_info:
                    retrieved[f"kg_{entity}"] = entity_info

        # 2. 检索对象交互知识（默认知识库）
        for entity in key_entities:
            if entity in self.knowledge_base.get('object_interactions', {}):
                retrieved[f"about_{entity}"] = self.knowledge_base['object_interactions'][entity]

        # 3. 检索动作策略知识
        available_actions = observation.get('available_actions', [])
        for action in available_actions:
            if action in self.knowledge_base.get('action_strategies', {}):
                retrieved[f"strategy_{action}"] = self.knowledge_base['action_strategies'][action]

        # 4. 检索任务模式知识（基于上下文推断）
        context = observation.get('description', '').lower()
        for task_type, strategies in self.knowledge_base.get('task_patterns', {}).items():
            if any(keyword in context for keyword in ['cook', 'kitchen', 'food']) and 'cooking' in task_type:
                retrieved[f"pattern_{task_type}"] = strategies
            elif any(keyword in context for keyword in ['clean', 'dirty']) and 'cleaning' in task_type:
                retrieved[f"pattern_{task_type}"] = strategies

        return retrieved

    def _get_entity_info_from_kg(self, entity_name: str) -> List[str]:
        """从KG中获取实体信息"""
        info = []

        if not self.scene_kg or 'nodes' not in self.scene_kg:
            return info

        # 查找匹配的节点
        for node in self.scene_kg['nodes']:
            node_name = node.get('name', '')
            if (node_name == entity_name or
                entity_name in node_name or
                node_name in entity_name):

                attrs = node.get('attributes', {})

                # 提取有用的属性信息
                if 'object_type' in attrs:
                    info.append(f"Type: {attrs['object_type']}")

                if 'openable' in attrs:
                    info.append(f"Openable: {attrs['openable']}")

                if 'receptacle' in attrs:
                    info.append(f"Can contain items: {attrs['receptacle']}")

                if 'position_x' in attrs:
                    info.append(f"Located at position ({attrs.get('position_x', 0):.1f}, {attrs.get('position_z', 0):.1f})")

                # 添加状态信息
                if node.get('type') == 'state':
                    state_value = attrs.get('state_value', '')
                    if state_value:
                        info.append(f"Current state: {state_value}")

        return info
    
    def _generate_action_with_knowledge(self, observation: Dict[str, Any], 
                                      knowledge: Dict[str, List[str]]) -> Tuple[str, str]:
        """基于检索的知识生成动作"""
        available_actions = observation.get('available_actions', [])
        visible_entities = observation.get('visible_entities', [])
        inventory = observation.get('agent_inventory', [])
        
        # 基于知识的决策
        # 1. 如果知识建议优先拾取钥匙
        if any('keys' in str(k) for k in knowledge.values()) and 'pick_up' in available_actions:
            key_items = [e for e in visible_entities if 'key' in e.lower()]
            if key_items:
                return "pick_up", key_items[0]
        
        # 2. 如果有钥匙且知识建议解锁
        if any('key' in item.lower() for item in inventory) and 'open' in available_actions:
            lockable_items = [e for e in visible_entities if any(keyword in e.lower() 
                             for keyword in ['cabinet', 'drawer', 'safe'])]
            if lockable_items:
                return "open", lockable_items[0]
        
        # 3. 基于任务模式知识
        if 'pattern_cooking_task' in knowledge and visible_entities:
            cooking_items = [e for e in visible_entities if any(keyword in e.lower() 
                            for keyword in ['microwave', 'stove', 'oven'])]
            if cooking_items and 'use' in available_actions:
                return "use", cooking_items[0]
        
        # 4. 基于动作策略知识
        for action in available_actions:
            strategy_key = f"strategy_{action}"
            if strategy_key in knowledge:
                if action == 'examine' and visible_entities:
                    return "examine", visible_entities[0]
                elif action == 'go_to' and visible_entities:
                    return "go_to", visible_entities[0]
        
        # 默认行为
        if 'pick_up' in available_actions and visible_entities and not inventory:
            return "pick_up", visible_entities[0]
        elif 'examine' in available_actions and visible_entities:
            return "examine", visible_entities[0]
        
        return "wait", None

    def _llm_rag_generation(self, observation: Dict[str, Any], retrieved_knowledge: Dict[str, Any],
                          available_actions: List[str], visible_entities: List[str],
                          inventory: List[str]) -> Tuple[str, str]:
        """使用真实LLM进行RAG生成"""
        print(f"🔥 Calling real LLM for RAG generation ({self.model_name})...")

        # 构建RAG提示
        prompt = self._build_rag_prompt(observation, retrieved_knowledge, available_actions,
                                      visible_entities, inventory)
        print(f"📝 RAG LLM Prompt:")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")

        try:
            # 调用OpenAI API
            from openai import OpenAI
            from src.utils.simple_config import SimpleConfig

            config = SimpleConfig()
            api_key = config.get_api_key()
            base_url = config.get_base_url()

            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )

            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an AI agent using RAG (Retrieval-Augmented Generation). Use the retrieved knowledge to make informed decisions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3  # 降低随机性
            )

            raw_response = response.choices[0].message.content.strip()
            print(f"🤖 Raw RAG LLM Response:")
            print(f"{'='*60}")
            print(raw_response)
            print(f"{'='*60}")

            # 解析RAG响应
            action, target = self._parse_rag_response(raw_response, available_actions, visible_entities)
            print(f"✅ Parsed RAG action: {action} -> {target}")

            return action, target

        except Exception as e:
            print(f"❌ RAG LLM call failed: {e}")
            print("🚫 No fallback - experiment requires real LLM responses")
            raise e

    def _build_rag_prompt(self, observation: Dict[str, Any], retrieved_knowledge: Dict[str, Any],
                        available_actions: List[str], visible_entities: List[str],
                        inventory: List[str]) -> str:
        """构建RAG提示"""
        # 格式化检索到的知识
        knowledge_text = ""
        if retrieved_knowledge:
            knowledge_text = "\nRetrieved Knowledge:\n"
            for entity, knowledge in retrieved_knowledge.items():
                if isinstance(knowledge, list):
                    knowledge_text += f"- {entity}: {', '.join(knowledge)}\n"
                else:
                    knowledge_text += f"- {entity}: {knowledge}\n"

        # 获取历史动作
        recent_actions = ""
        if self.action_history:
            recent_actions = f"\nRecent actions: {self.action_history[-3:]}"

        prompt = f"""You are using RAG (Retrieval-Augmented Generation) in a household environment.

Current situation:
- Available actions: {available_actions}
- Visible entities: {visible_entities}
- Your inventory: {inventory}{recent_actions}{knowledge_text}

TASK OBJECTIVES:
1. PRIMARY: Find and collect useful items (keys, tools, food items) - USE PICK_UP ACTION!
2. SECONDARY: Explore systematically to discover new areas and objects
3. TERTIARY: Interact with containers (cabinets, drawers) to find hidden items

CRITICAL INSTRUCTIONS:
1. **PRIORITIZE PICK_UP**: If you see any objects and have pick_up available, strongly consider picking them up
2. Use the retrieved knowledge to inform your decision and advance task objectives
3. The knowledge says "Pick up useful items first" - follow this guidance!
4. After examining objects, try to pick them up if possible
5. Collecting items gives higher rewards than just examining

Please select ONE action and ONE target from the available options.
Respond in the format: "ACTION: <action_name> TARGET: <target_name>"

For example:
- ACTION: examine TARGET: CoffeeTable_992 (to check for useful items)
- ACTION: pick_up TARGET: Key_123 (keys are high priority items)
- ACTION: go_to TARGET: Kitchen_456 (to explore new areas)

Choose wisely based on the current situation, retrieved knowledge, and task objectives:"""

        return prompt

    def _parse_rag_response(self, response: str, available_actions: List[str],
                          visible_entities: List[str]) -> Tuple[str, str]:
        """解析RAG响应 - 改进版本，包含动作兼容性检查"""
        # 提取ACTION和TARGET
        action_match = re.search(r'ACTION:\s*(\w+)', response, re.IGNORECASE)
        target_match = re.search(r'TARGET:\s*([^\s\n]+)', response, re.IGNORECASE)

        if action_match and target_match:
            action = action_match.group(1).lower()
            target = target_match.group(1)

            # 验证动作和目标的基本有效性
            if action in available_actions and target in visible_entities:
                # 进一步检查动作-目标兼容性
                if self._is_action_compatible(action, target):
                    return action, target
                else:
                    print(f"⚠️ Action {action} not compatible with {target}, finding alternative")

        # 智能回退策略 - 找到兼容的动作-目标组合
        print(f"🔄 Using intelligent fallback strategy...")
        return self._find_compatible_action(available_actions, visible_entities)

    def _is_action_compatible(self, action: str, target: str) -> bool:
        """检查动作和目标是否兼容"""
        # 检查是否是之前失败的组合
        failed_key = f"{action}_{target}"
        if hasattr(self, 'failed_actions') and failed_key in self.failed_actions:
            failure_count = self.failed_actions[failed_key]
            if failure_count >= 3:  # 如果失败超过3次，避免重复
                print(f"⚠️ Avoiding repeated failure: {failed_key} (failed {failure_count} times)")
                return False

        # 从KG获取目标对象的属性
        entity_info = self._get_entity_info_from_kg(target)

        # 基于对象属性检查动作兼容性
        if action == "pick_up":
            # 检查对象是否可以拾取
            for info in entity_info:
                if "Type:" in info:
                    object_type = info.split("Type: ")[1]
                    # 大型家具不能拾取
                    if object_type in ["ArmChair", "CoffeeTable", "Bed", "Desk", "Sofa", "Dresser"]:
                        print(f"⚠️ Cannot pick up furniture: {object_type}")
                        return False
                    # 固定装置不能拾取
                    if object_type in ["Sink", "Toilet", "Bathtub", "Stove", "Fridge"]:
                        print(f"⚠️ Cannot pick up fixture: {object_type}")
                        return False

        elif action == "open":
            # 检查对象是否可以打开
            is_openable = False
            for info in entity_info:
                if "Openable: True" in info:
                    is_openable = True
                    break
            if not is_openable:
                print(f"⚠️ Object {target} is not openable")
                return False

        return True

    def _find_compatible_action(self, available_actions: List[str],
                              visible_entities: List[str]) -> Tuple[str, str]:
        """找到兼容的动作-目标组合"""
        # 优先级策略：examine > go_to > pick_up > open > others
        action_priority = ["examine", "go_to", "pick_up", "open", "close", "put_down", "wait"]

        for action in action_priority:
            if action not in available_actions:
                continue

            for entity in visible_entities:
                if self._is_action_compatible(action, entity):
                    print(f"✅ Found compatible action: {action} -> {entity}")
                    return action, entity

        # 如果没有找到兼容的组合，使用最安全的选择
        if "examine" in available_actions and visible_entities:
            print(f"🔒 Using safe fallback: examine -> {visible_entities[0]}")
            return "examine", visible_entities[0]
        elif "wait" in available_actions:
            print(f"🔒 Using wait action as last resort")
            return "wait", ""

        raise ValueError(f"Cannot find any compatible action-target combination")

    def update(self, observation: Dict[str, Any], action: str, target: str,
               reward: float, next_observation: Dict[str, Any], done: bool):
        """更新智能体 - RAG可以更新知识库"""
        # 基于经验更新知识库
        if reward > 0.1:  # 正奖励
            # 强化成功的动作模式
            success_pattern = f"{action}_{target}" if target else action
            if 'successful_patterns' not in self.knowledge_base:
                self.knowledge_base['successful_patterns'] = {}
            
            self.knowledge_base['successful_patterns'][success_pattern] = \
                self.knowledge_base['successful_patterns'].get(success_pattern, 0) + reward
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'agent_type': 'rag',
            'knowledge_base_size': len(self.knowledge_base),
            'total_retrievals': len(self.retrieval_history),
            'recent_retrievals': self.retrieval_history[-3:] if self.retrieval_history else [],
            'successful_patterns': self.knowledge_base.get('successful_patterns', {})
        }


if __name__ == "__main__":
    # 测试三个智能体
    print("🧪 测试基线智能体")
    
    # 模拟观察
    mock_observation = {
        'scene': 'FloorPlan228-openable',
        'agent_location': 'Kitchen',
        'agent_inventory': [],
        'visible_entities': ['Cabinet', 'Drawer', 'Apple', 'Key'],
        'available_actions': ['go_to', 'open', 'pick_up', 'examine', 'wait'],
        'step_count': 1,
        'description': '你在厨房里，可以看到柜子、抽屉、苹果和钥匙。'
    }
    
    # 测试LLM基线
    llm_agent = LLMBaselineAgent()
    llm_action, llm_target = llm_agent.select_action(mock_observation)
    print(f"🤖 LLM基线: {llm_action} {llm_target or ''}")
    
    # 测试ReAct
    react_agent = ReActAgent()
    react_action, react_target = react_agent.select_action(mock_observation)
    print(f"🧠 ReAct: {react_action} {react_target or ''}")
    
    # 测试RAG
    rag_agent = RAGAgent()
    rag_action, rag_target = rag_agent.select_action(mock_observation)
    print(f"🔍 RAG: {rag_action} {rag_target or ''}")
    
    # 显示统计信息
    print(f"\n📊 统计信息:")
    print(f"LLM: {llm_agent.get_statistics()}")
    print(f"ReAct: {react_agent.get_statistics()}")
    print(f"RAG: {rag_agent.get_statistics()}")
    
    print("✅ 测试完成")
