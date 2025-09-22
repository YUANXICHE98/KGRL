#!/usr/bin/env python3
"""
状态知识图谱构建器
构建符合用户要求的场景固定、状态更新的flowchart知识图谱

用户要求的结构:
flowchart TD
  A["动作: 打开"]:::act
  K["道具: 钥匙<br/>名称: 青铜钥匙<br/>状态: 未获取"]:::ent
  K2["道具: 钥匙<br/>状态: 已获取"]:::ent
  C["容器: 宝箱<br/>材质: 木制<br/>状态: 锁定"]:::ent
  S1["状态: 未获取"]:::state
  S2["状态: 锁定"]:::state
  R["结果: 打开成功"]:::result

  A --> C
  A --> K
  K --> S1
  C --> S2
  K --> C
  K -.-> K2
  K2 --> A
  A --> R
  R -.-> C
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder, EdgeType, NodeType


@dataclass
class StateTransition:
    """状态转换"""
    from_state: str
    to_state: str
    action: str
    conditions: List[str]
    effects: List[str]


@dataclass
class GameEntity:
    """游戏实体"""
    name: str
    type: str  # 道具、容器、角色等
    properties: Dict[str, Any]  # 材质、名称等属性
    initial_state: str
    possible_states: List[str]


@dataclass
class GameAction:
    """游戏动作"""
    name: str
    description: str
    required_entities: List[str]
    required_states: Dict[str, str]  # 实体名 -> 需要的状态
    effects: Dict[str, str]  # 实体名 -> 产生的状态
    result: str


class StateKGBuilder:
    """状态知识图谱构建器"""
    
    def __init__(self):
        self.builder = DODAFKGBuilder()
        self.entities = {}  # 实体ID映射
        self.states = {}    # 状态ID映射
        self.actions = {}   # 动作ID映射
        self.results = {}   # 结果ID映射
        
    def create_scene_kg(self, scene_name: str, entities: List[GameEntity], 
                       actions: List[GameAction], transitions: List[StateTransition]) -> Dict[str, Any]:
        """创建场景知识图谱"""
        
        # 1. 创建场景节点
        scene_id = self.builder.add_entity_node(scene_name, "scene", {
            'description': f'游戏场景: {scene_name}',
            'type': 'game_scene'
        })
        
        # 2. 创建实体节点和状态节点
        for entity in entities:
            # 创建实体节点
            entity_id = self.builder.add_entity_node(entity.name, entity.type, {
                'properties': entity.properties,
                'initial_state': entity.initial_state,
                'possible_states': entity.possible_states
            })
            self.entities[entity.name] = entity_id
            
            # 场景包含实体
            self.builder.add_edge(scene_id, entity_id, EdgeType.CONTAINS, {
                'relationship': 'scene_contains_entity'
            })
            
            # 为每个可能状态创建状态节点
            for state_value in entity.possible_states:
                state_name = f"{entity.name}_{state_value}"
                state_id = self.builder.add_state_node(state_name, state_value, {
                    'entity_name': entity.name,
                    'state_type': 'entity_state',
                    'is_initial': (state_value == entity.initial_state)
                })
                self.states[state_name] = state_id
                
                # 实体具有状态
                self.builder.add_edge(entity_id, state_id, EdgeType.HAS_STATE, {
                    'state_value': state_value,
                    'is_initial': (state_value == entity.initial_state)
                })
        
        # 3. 创建动作节点
        for action in actions:
            action_id = self.builder.add_action_node(action.name, {
                'description': action.description,
                'required_entities': action.required_entities,
                'required_states': action.required_states,
                'effects': action.effects,
                'result': action.result
            })
            self.actions[action.name] = action_id
            
            # 创建结果节点
            result_id = self.builder.add_result_node(f"{action.name}_result", action.result, {
                'action_name': action.name,
                'description': f'动作 {action.name} 的结果'
            })
            self.results[f"{action.name}_result"] = result_id
            
            # 动作产生结果
            self.builder.add_edge(action_id, result_id, EdgeType.PRODUCES, {
                'relationship': 'action_produces_result'
            })
        
        # 4. 创建动作-实体-状态关系
        for action in actions:
            action_id = self.actions[action.name]
            
            # 动作需要的实体和状态
            for entity_name in action.required_entities:
                if entity_name in self.entities:
                    entity_id = self.entities[entity_name]
                    # 动作需要实体
                    self.builder.add_edge(action_id, entity_id, EdgeType.REQUIRES, {
                        'relationship': 'action_requires_entity'
                    })
            
            # 动作需要的状态
            for entity_name, required_state in action.required_states.items():
                state_name = f"{entity_name}_{required_state}"
                if state_name in self.states:
                    state_id = self.states[state_name]
                    # 动作需要状态
                    self.builder.add_edge(action_id, state_id, EdgeType.REQUIRES, {
                        'relationship': 'action_requires_state',
                        'required_value': required_state
                    })
            
            # 动作的效果
            for entity_name, new_state in action.effects.items():
                state_name = f"{entity_name}_{new_state}"
                if state_name in self.states:
                    state_id = self.states[state_name]
                    # 动作修改状态
                    self.builder.add_edge(action_id, state_id, EdgeType.MODIFIES, {
                        'relationship': 'action_modifies_state',
                        'new_value': new_state
                    })
        
        # 5. 创建状态转换关系
        for transition in transitions:
            from_state_id = self.states.get(transition.from_state)
            to_state_id = self.states.get(transition.to_state)
            action_id = self.actions.get(transition.action)
            
            if from_state_id and to_state_id and action_id:
                # 状态转换
                self.builder.add_edge(from_state_id, to_state_id, EdgeType.TRANSITIONS, {
                    'action': transition.action,
                    'conditions': transition.conditions,
                    'effects': transition.effects
                })
        
        return {
            'scene_id': scene_id,
            'entities': len(entities),
            'actions': len(actions),
            'transitions': len(transitions),
            'total_nodes': len(self.builder.nodes),
            'total_edges': len(self.builder.edges)
        }
    
    def create_alfworld_scene_kg(self, scene_data: Dict[str, Any], scene_name: str) -> Dict[str, Any]:
        """从ALFWorld数据创建场景知识图谱"""
        
        # 解析ALFWorld数据，创建实体
        entities = []
        for object_key, position_data in scene_data.items():
            parts = object_key.split('|')
            if len(parts) >= 4:
                object_type = parts[0]
                x_pos, y_pos, z_pos = parts[1], parts[2], parts[3]
                
                # 创建游戏实体
                entity = GameEntity(
                    name=f"{object_type}_{len(entities)}",
                    type=object_type.lower(),
                    properties={
                        'position_x': float(x_pos),
                        'position_y': float(y_pos),
                        'position_z': float(z_pos),
                        'layout_data': position_data,
                        'object_type': object_type
                    },
                    initial_state='available',
                    possible_states=['available', 'unavailable', 'in_use']
                )
                entities.append(entity)
        
        # 创建基本动作
        actions = []
        
        # 如果有可打开的容器，创建打开动作
        openable_entities = [e for e in entities if 'drawer' in e.type.lower() or 'cabinet' in e.type.lower()]
        if openable_entities:
            for entity in openable_entities[:1]:  # 只处理第一个
                # 添加锁定状态
                entity.possible_states.extend(['locked', 'unlocked', 'opened'])
                entity.initial_state = 'locked'
                
                # 创建打开动作
                open_action = GameAction(
                    name=f"open_{entity.name}",
                    description=f"打开 {entity.name}",
                    required_entities=[entity.name],
                    required_states={entity.name: 'unlocked'},
                    effects={entity.name: 'opened'},
                    result="打开成功"
                )
                actions.append(open_action)
        
        # 创建状态转换
        transitions = []
        for action in actions:
            for entity_name, from_state in action.required_states.items():
                to_state = action.effects.get(entity_name)
                if to_state:
                    transition = StateTransition(
                        from_state=f"{entity_name}_{from_state}",
                        to_state=f"{entity_name}_{to_state}",
                        action=action.name,
                        conditions=[f"{entity_name} must be {from_state}"],
                        effects=[f"{entity_name} becomes {to_state}"]
                    )
                    transitions.append(transition)
        
        # 创建知识图谱
        return self.create_scene_kg(scene_name, entities, actions, transitions)
    
    def get_builder(self) -> DODAFKGBuilder:
        """获取底层构建器"""
        return self.builder


def create_example_state_kg():
    """创建示例状态知识图谱 - 符合用户要求的"打开宝箱"场景"""
    
    builder = StateKGBuilder()
    
    # 定义实体
    entities = [
        GameEntity(
            name="青铜钥匙",
            type="道具",
            properties={'材质': '青铜', '名称': '青铜钥匙'},
            initial_state='未获取',
            possible_states=['未获取', '已获取']
        ),
        GameEntity(
            name="木制宝箱",
            type="容器", 
            properties={'材质': '木制'},
            initial_state='锁定',
            possible_states=['锁定', '解锁', '打开']
        )
    ]
    
    # 定义动作
    actions = [
        GameAction(
            name="打开",
            description="打开宝箱",
            required_entities=["青铜钥匙", "木制宝箱"],
            required_states={"青铜钥匙": "已获取", "木制宝箱": "解锁"},
            effects={"木制宝箱": "打开"},
            result="打开成功"
        )
    ]
    
    # 定义状态转换
    transitions = [
        StateTransition(
            from_state="青铜钥匙_未获取",
            to_state="青铜钥匙_已获取", 
            action="获取钥匙",
            conditions=["钥匙可见", "玩家在场"],
            effects=["钥匙在玩家手中"]
        ),
        StateTransition(
            from_state="木制宝箱_锁定",
            to_state="木制宝箱_解锁",
            action="使用钥匙",
            conditions=["有正确的钥匙"],
            effects=["宝箱解锁"]
        ),
        StateTransition(
            from_state="木制宝箱_解锁", 
            to_state="木制宝箱_打开",
            action="打开",
            conditions=["宝箱已解锁"],
            effects=["宝箱内容可见"]
        )
    ]
    
    # 创建知识图谱
    result = builder.create_scene_kg("打开宝箱场景", entities, actions, transitions)
    
    print("✅ 创建示例状态知识图谱成功!")
    print(f"   - 实体数: {result['entities']}")
    print(f"   - 动作数: {result['actions']}")
    print(f"   - 转换数: {result['transitions']}")
    print(f"   - 总节点数: {result['total_nodes']}")
    print(f"   - 总边数: {result['total_edges']}")
    
    return builder


def main():
    """主函数"""
    print("🚀 开始创建状态知识图谱\n")
    
    # 创建示例知识图谱
    example_builder = create_example_state_kg()
    
    # 获取统计信息
    stats = example_builder.get_builder().get_statistics()
    print("\n📊 知识图谱统计:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    print("\n🎉 状态知识图谱创建完成!")
    
    return example_builder


if __name__ == "__main__":
    main()
