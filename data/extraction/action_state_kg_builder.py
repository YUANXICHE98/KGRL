#!/usr/bin/env python3
"""
基于PDDL动作定义的动作-状态-结果知识图谱构建器
从ALFWorld的PDDL文件和场景数据构建正确的KG结构
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from dataclasses import dataclass

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class ActionDefinition:
    """动作定义"""
    name: str
    parameters: List[str]
    preconditions: List[str]
    effects: List[str]
    description: str = ""


@dataclass
class EntityState:
    """实体状态"""
    entity_name: str
    state_type: str
    state_value: str
    is_initial: bool = False


@dataclass
class ActionRule:
    """动作规则"""
    action_name: str
    required_entities: List[str]
    required_states: Dict[str, str]
    effects: Dict[str, str]
    result: str
    reward: float = 0.0


class ActionStateKGBuilder:
    """动作-状态-结果知识图谱构建器"""
    
    def __init__(self):
        self.actions = {}  # action_name -> ActionDefinition
        self.entities = {}  # entity_name -> entity_info
        self.states = {}   # (entity, state_type) -> EntityState
        self.action_rules = {}  # action_name -> ActionRule
        
        # 节点和边计数器
        self.node_id_counter = 1
        self.edge_id_counter = 1
        
        print("🏗️ 初始化动作-状态-结果KG构建器")
    
    def parse_pddl_actions(self, pddl_file: str) -> Dict[str, ActionDefinition]:
        """解析PDDL文件中的动作定义"""
        print(f"📖 解析PDDL动作定义: {pddl_file}")
        
        with open(pddl_file, 'r') as f:
            content = f.read()
        
        # 提取动作定义
        action_pattern = r'\(:action\s+(\w+).*?:parameters\s*\((.*?)\).*?:precondition\s*(.*?):effect\s*(.*?)\)'
        actions = {}
        
        for match in re.finditer(action_pattern, content, re.DOTALL):
            name = match.group(1)
            params = self._parse_parameters(match.group(2))
            precond = self._parse_conditions(match.group(3))
            effects = self._parse_effects(match.group(4))
            
            actions[name] = ActionDefinition(
                name=name,
                parameters=params,
                preconditions=precond,
                effects=effects,
                description=f"ALFWorld action: {name}"
            )
        
        print(f"✅ 解析到 {len(actions)} 个动作定义")
        return actions
    
    def _parse_parameters(self, param_str: str) -> List[str]:
        """解析参数列表"""
        # 简化处理：提取变量名
        params = []
        for match in re.finditer(r'\?(\w+)', param_str):
            params.append(match.group(1))
        return params
    
    def _parse_conditions(self, cond_str: str) -> List[str]:
        """解析前置条件"""
        conditions = []
        # 提取谓词
        for match in re.finditer(r'\((\w+)[^)]*\)', cond_str):
            conditions.append(match.group(1))
        return conditions
    
    def _parse_effects(self, effect_str: str) -> List[str]:
        """解析效果"""
        effects = []
        # 提取谓词
        for match in re.finditer(r'\((\w+)[^)]*\)', effect_str):
            effects.append(match.group(1))
        return effects
    
    def build_scene_action_rules(self, scene_data: Dict[str, Any], scene_name: str) -> Dict[str, ActionRule]:
        """基于场景数据构建动作规则"""
        print(f"🎯 为场景 {scene_name} 构建动作规则")
        
        # 提取场景中的实体
        entities = self._extract_scene_entities(scene_data)
        
        # 构建核心动作规则
        action_rules = {}
        
        # 1. pick_up 动作规则
        action_rules['pick_up'] = ActionRule(
            action_name='pick_up',
            required_entities=['agent', 'object'],
            required_states={
                'agent': 'empty_handed',
                'object': 'available'
            },
            effects={
                'agent': 'holding_object',
                'object': 'picked_up'
            },
            result='pickup_success',
            reward=0.19
        )
        
        # 2. go_to 动作规则
        action_rules['go_to'] = ActionRule(
            action_name='go_to',
            required_entities=['agent', 'location'],
            required_states={
                'agent': 'at_current_location'
            },
            effects={
                'agent': 'at_target_location'
            },
            result='movement_success',
            reward=0.09
        )
        
        # 3. examine 动作规则
        action_rules['examine'] = ActionRule(
            action_name='examine',
            required_entities=['agent', 'object'],
            required_states={
                'agent': 'at_object_location',
                'object': 'visible'
            },
            effects={
                'object': 'examined'
            },
            result='examine_success',
            reward=0.04
        )
        
        # 4. open 动作规则
        action_rules['open'] = ActionRule(
            action_name='open',
            required_entities=['agent', 'receptacle'],
            required_states={
                'agent': 'at_receptacle_location',
                'receptacle': 'closed'
            },
            effects={
                'receptacle': 'opened'
            },
            result='open_success',
            reward=0.1
        )
        
        print(f"✅ 构建了 {len(action_rules)} 个动作规则")
        return action_rules
    
    def _extract_scene_entities(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """从场景数据中提取实体"""
        entities = {}
        
        # 添加智能体
        entities['agent'] = {
            'type': 'agent',
            'name': 'agent',
            'initial_states': {
                'location': 'start_location',
                'inventory': 'empty_handed'
            }
        }
        
        # 从场景数据中提取物体
        if 'objects' in scene_data:
            for obj_data in scene_data['objects']:
                obj_name = obj_data.get('name', 'unknown_object')
                entities[obj_name] = {
                    'type': 'object',
                    'name': obj_name,
                    'initial_states': {
                        'availability': 'available',
                        'visibility': 'visible'
                    }
                }
        
        return entities
    
    def build_kg_from_scene(self, scene_file: str) -> Dict[str, Any]:
        """从场景文件构建知识图谱"""
        scene_name = Path(scene_file).stem
        print(f"🏗️ 为场景 {scene_name} 构建动作-状态KG")
        
        # 加载场景数据
        with open(scene_file, 'r') as f:
            scene_data = json.load(f)
        
        # 构建动作规则
        action_rules = self.build_scene_action_rules(scene_data, scene_name)
        
        # 构建KG结构
        kg = {
            'kg_id': f"{scene_name}_action_state_kg",
            'description': f"Action-State Knowledge Graph for {scene_name}",
            'nodes': [],
            'edges': [],
            'metadata': {
                'scene_name': scene_name,
                'kg_type': 'action_state_result',
                'creation_time': str(Path(scene_file).stat().st_mtime)
            }
        }
        
        # 添加场景节点
        scene_node = self._create_scene_node(scene_name)
        kg['nodes'].append(scene_node)
        
        # 添加动作、状态、结果节点
        for rule in action_rules.values():
            # 添加动作节点
            action_node = self._create_action_node(rule)
            kg['nodes'].append(action_node)
            
            # 添加状态节点
            for entity, state in rule.required_states.items():
                state_node = self._create_state_node(entity, state, True)
                kg['nodes'].append(state_node)
            
            for entity, state in rule.effects.items():
                state_node = self._create_state_node(entity, state, False)
                kg['nodes'].append(state_node)
            
            # 添加结果节点
            result_node = self._create_result_node(rule)
            kg['nodes'].append(result_node)
            
            # 添加关系边
            kg['edges'].extend(self._create_action_edges(rule))
        
        # 添加统计信息
        kg['metadata']['statistics'] = {
            'total_nodes': len(kg['nodes']),
            'total_edges': len(kg['edges']),
            'actions': len(action_rules),
            'states': len([n for n in kg['nodes'] if n['type'] == 'state']),
            'results': len([n for n in kg['nodes'] if n['type'] == 'result'])
        }
        
        print(f"✅ 构建完成: {kg['metadata']['statistics']}")
        return kg

    def _create_scene_node(self, scene_name: str) -> Dict[str, Any]:
        """创建场景节点"""
        return {
            'id': f'scene_{self.node_id_counter}',
            'type': 'entity',
            'name': scene_name,
            'attributes': {
                'entity_type': 'scene',
                'description': f'ALFWorld scene: {scene_name}'
            }
        }

    def _create_action_node(self, rule: ActionRule) -> Dict[str, Any]:
        """创建动作节点"""
        self.node_id_counter += 1
        return {
            'id': f'action_{self.node_id_counter}',
            'type': 'action',
            'name': rule.action_name,
            'attributes': {
                'description': f'Action: {rule.action_name}',
                'required_entities': rule.required_entities,
                'required_states': rule.required_states,
                'effects': rule.effects,
                'result': rule.result,
                'reward': rule.reward
            }
        }

    def _create_state_node(self, entity: str, state: str, is_initial: bool) -> Dict[str, Any]:
        """创建状态节点"""
        self.node_id_counter += 1
        return {
            'id': f'state_{self.node_id_counter}',
            'type': 'state',
            'name': f'{entity}_{state}',
            'attributes': {
                'entity_name': entity,
                'state_value': state,
                'is_initial': is_initial,
                'state_type': 'entity_state'
            }
        }

    def _create_result_node(self, rule: ActionRule) -> Dict[str, Any]:
        """创建结果节点"""
        self.node_id_counter += 1
        return {
            'id': f'result_{self.node_id_counter}',
            'type': 'result',
            'name': rule.result,
            'attributes': {
                'action_name': rule.action_name,
                'result_value': rule.result,
                'reward': rule.reward
            }
        }

    def _create_action_edges(self, rule: ActionRule) -> List[Dict[str, Any]]:
        """创建动作相关的边"""
        edges = []

        # 动作 -> 前置状态 (REQUIRES)
        for entity, state in rule.required_states.items():
            edges.append({
                'id': f'edge_{self.edge_id_counter}',
                'source': f'action_{self.node_id_counter}',
                'target': f'state_{entity}_{state}',
                'type': 'requires',
                'attributes': {
                    'relation_type': 'precondition'
                }
            })
            self.edge_id_counter += 1

        # 动作 -> 效果状态 (PRODUCES)
        for entity, state in rule.effects.items():
            edges.append({
                'id': f'edge_{self.edge_id_counter}',
                'source': f'action_{self.node_id_counter}',
                'target': f'state_{entity}_{state}',
                'type': 'produces',
                'attributes': {
                    'relation_type': 'effect'
                }
            })
            self.edge_id_counter += 1

        # 动作 -> 结果 (PRODUCES)
        edges.append({
            'id': f'edge_{self.edge_id_counter}',
            'source': f'action_{self.node_id_counter}',
            'target': f'result_{self.node_id_counter}',
            'type': 'produces',
            'attributes': {
                'relation_type': 'result'
            }
        })
        self.edge_id_counter += 1

        return edges


def build_action_state_kgs_for_scenes(scene_names: List[str] = None) -> Dict[str, str]:
    """为指定场景构建动作-状态KG"""
    if scene_names is None:
        scene_names = ['FloorPlan202-openable', 'FloorPlan308-openable']

    print(f"🚀 开始构建 {len(scene_names)} 个场景的动作-状态KG")

    builder = ActionStateKGBuilder()

    # 解析PDDL动作定义
    pddl_file = project_root / "data/benchmarks/alfworld/alfworld/alfworld/data/alfred.pddl"
    if pddl_file.exists():
        builder.actions = builder.parse_pddl_actions(str(pddl_file))

    # 创建输出目录
    output_dir = project_root / "data/knowledge_graphs/action_state_scenes"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for scene_name in scene_names:
        # 查找场景文件
        scene_file = project_root / f"data/benchmarks/alfworld/alfworld/alfworld/gen/layouts/{scene_name}.json"

        if not scene_file.exists():
            print(f"⚠️  场景文件不存在: {scene_file}")
            continue

        try:
            # 构建KG
            kg = builder.build_kg_from_scene(str(scene_file))

            # 保存KG文件
            output_file = output_dir / f"{scene_name}_action_state_kg.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(kg, f, indent=2, ensure_ascii=False)

            results[scene_name] = str(output_file)
            print(f"✅ {scene_name} KG已保存到: {output_file}")

        except Exception as e:
            print(f"❌ 构建 {scene_name} KG失败: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n🎉 完成! 成功构建 {len(results)} 个动作-状态KG")
    return results


if __name__ == "__main__":
    # 构建两个实验场景的动作-状态KG
    results = build_action_state_kgs_for_scenes()

    print("\n📊 构建结果:")
    for scene, file_path in results.items():
        print(f"   - {scene}: {file_path}")
