#!/usr/bin/env python3
"""
场景级别知识图谱构建器
Scene-level Knowledge Graph Builder
完整覆盖benchmark信息：动作定义、目标、状态等
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder, NodeType, EdgeType


class SceneKGBuilder:
    """场景级别KG构建器"""
    
    def __init__(self):
        self.kg_builder = DODAFKGBuilder()
        
        # ALFWorld动作定义 (从PDDL domain提取)
        self.alfworld_actions = {
            'GotoLocation': {
                'parameters': ['agent', 'start_location', 'end_location'],
                'preconditions': ['atLocation(agent, start_location)'],
                'effects': ['atLocation(agent, end_location)', 'not atLocation(agent, start_location)'],
                'cost': 'distance(start_location, end_location)'
            },
            'OpenObject': {
                'parameters': ['agent', 'location', 'receptacle'],
                'preconditions': ['atLocation(agent, location)', 'receptacleAtLocation(receptacle, location)', 
                                'openable(receptacle)', 'forall receptacle: not opened(receptacle)'],
                'effects': ['opened(receptacle)', 'checked(receptacle)'],
                'cost': 1
            },
            'CloseObject': {
                'parameters': ['agent', 'location', 'receptacle'],
                'preconditions': ['atLocation(agent, location)', 'receptacleAtLocation(receptacle, location)',
                                'openable(receptacle)', 'opened(receptacle)'],
                'effects': ['not opened(receptacle)'],
                'cost': 1
            },
            'PickupObject': {
                'parameters': ['agent', 'location', 'object', 'receptacle'],
                'preconditions': ['atLocation(agent, location)', 'objectAtLocation(object, location)',
                                'inReceptacle(object, receptacle)', 'not holdsAny(agent)',
                                'or(not openable(receptacle), opened(receptacle))'],
                'effects': ['not inReceptacle(object, receptacle)', 'holds(agent, object)', 'holdsAny(agent)'],
                'cost': 1
            },
            'PutObject': {
                'parameters': ['agent', 'location', 'object_type', 'object', 'receptacle'],
                'preconditions': ['atLocation(agent, location)', 'receptacleAtLocation(receptacle, location)',
                                'not full(receptacle)', 'objectType(object, object_type)', 'holds(agent, object)',
                                'or(not openable(receptacle), opened(receptacle))'],
                'effects': ['inReceptacle(object, receptacle)', 'full(receptacle)', 
                          'not holds(agent, object)', 'not holdsAny(agent)'],
                'cost': 1
            }
        }
        
        # 状态类型定义
        self.state_types = {
            'location_states': ['atLocation', 'objectAtLocation', 'receptacleAtLocation'],
            'container_states': ['opened', 'closed', 'full', 'empty'],
            'possession_states': ['holds', 'holdsAny', 'inReceptacle'],
            'property_states': ['openable', 'checked', 'objectType', 'receptacleType']
        }
    
    def build_scene_kg_from_alfworld(self, layout_data: Dict[str, Any], pddl_data: Dict[str, Any], 
                                   scene_name: str) -> Dict[str, Any]:
        """从ALFWorld数据构建完整的场景KG"""
        print(f"🏗️ 构建场景KG: {scene_name}")
        
        # 重置构建器
        self.kg_builder = DODAFKGBuilder()
        
        # 1. 创建场景根节点
        scene_id = self.kg_builder.add_entity_node(
            scene_name, "scene", 
            {"scene_type": "alfworld", "layout_file": str(layout_data.get('source_file', ''))}
        )
        
        # 2. 从布局数据提取实体和位置
        entities = self._extract_entities_from_layout(layout_data)
        
        # 3. 从PDDL数据提取完整信息
        if pddl_data:
            objects, initial_states, goal_states = self._extract_pddl_information(pddl_data)
            entities.update(objects)
        else:
            initial_states, goal_states = {}, {}
        
        # 4. 添加实体节点
        entity_nodes = {}
        for entity_name, entity_info in entities.items():
            entity_id = self.kg_builder.add_entity_node(
                entity_name, entity_info['type'], entity_info['properties']
            )
            entity_nodes[entity_name] = entity_id
            
            # 连接到场景
            self.kg_builder.add_edge(scene_id, entity_id, EdgeType.CONTAINS, 
                                   {"relationship": "scene_contains_entity"})
        
        # 5. 添加动作定义
        action_nodes = self._add_action_definitions(scene_id)
        
        # 6. 添加状态节点和关系
        state_nodes = self._add_state_information(entity_nodes, initial_states, scene_id)
        
        # 7. 添加目标信息
        goal_nodes = self._add_goal_information(goal_states, scene_id, entity_nodes)
        
        # 8. 建立动作-状态-实体关系
        self._connect_actions_states_entities(action_nodes, state_nodes, entity_nodes)
        
        # 9. 导出场景KG
        scene_kg = self._export_scene_kg(scene_name, len(entities), len(action_nodes), len(state_nodes))
        
        print(f"✅ 场景KG构建完成: {len(entity_nodes)} 实体, {len(action_nodes)} 动作, {len(state_nodes)} 状态")
        return scene_kg
    
    def _extract_entities_from_layout(self, layout_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """从布局数据提取实体"""
        entities = {}
        
        # 处理布局中的对象
        for object_key, position_data in layout_data.items():
            if isinstance(position_data, list) and len(position_data) >= 4:
                # 解析对象键: "ObjectType|x|y|z"
                parts = object_key.split('|')
                if len(parts) >= 4:
                    object_type = parts[0]
                    x, y, z = parts[1], parts[2], parts[3]
                    
                    # 创建实体信息
                    entity_name = f"{object_type}_{abs(hash(object_key)) % 1000}"
                    entities[entity_name] = {
                        'type': 'furniture' if object_type in ['Cabinet', 'Drawer', 'Table'] else 'object',
                        'properties': {
                            'object_type': object_type,
                            'position_x': float(x),
                            'position_y': float(y), 
                            'position_z': float(z),
                            'layout_data': position_data,
                            'original_key': object_key,
                            'openable': object_type in ['Cabinet', 'Drawer', 'Fridge', 'Microwave', 'Safe'],
                            'receptacle': object_type in ['Cabinet', 'Drawer', 'Fridge', 'Microwave', 'TableTop', 'CounterTop']
                        }
                    }
        
        return entities
    
    def _extract_pddl_information(self, pddl_data: Dict[str, Any]) -> Tuple[Dict, Dict, Dict]:
        """从PDDL数据提取对象、初始状态和目标"""
        objects = {}
        initial_states = {}
        goal_states = {}
        
        if 'problem_content' in pddl_data:
            content = pddl_data['problem_content']
            
            # 提取对象定义
            objects_match = re.search(r'\(:objects\s+(.*?)\)', content, re.DOTALL)
            if objects_match:
                objects_text = objects_match.group(1)
                # 解析对象定义
                for line in objects_text.split('\n'):
                    line = line.strip()
                    if ' - ' in line:
                        obj_name, obj_type = line.split(' - ')
                        obj_name = obj_name.strip()
                        obj_type = obj_type.strip()
                        
                        objects[obj_name] = {
                            'type': 'object' if 'object' in obj_type else 'receptacle',
                            'properties': {
                                'pddl_type': obj_type,
                                'source': 'pddl_objects'
                            }
                        }
            
            # 提取初始状态
            init_match = re.search(r'\(:init\s+(.*?)\)\s*\(:goal', content, re.DOTALL)
            if init_match:
                init_text = init_match.group(1)
                initial_states = self._parse_pddl_predicates(init_text)
            
            # 提取目标状态
            goal_match = re.search(r'\(:goal\s+(.*?)\)', content, re.DOTALL)
            if goal_match:
                goal_text = goal_match.group(1)
                goal_states = self._parse_pddl_predicates(goal_text)
        
        return objects, initial_states, goal_states
    
    def _parse_pddl_predicates(self, text: str) -> Dict[str, List]:
        """解析PDDL谓词"""
        predicates = {}
        
        # 查找所有谓词
        predicate_pattern = r'\(([^)]+)\)'
        matches = re.findall(predicate_pattern, text)
        
        for match in matches:
            parts = match.split()
            if parts:
                predicate_name = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                if predicate_name not in predicates:
                    predicates[predicate_name] = []
                predicates[predicate_name].append(args)
        
        return predicates
    
    def _add_action_definitions(self, scene_id: str) -> Dict[str, str]:
        """添加动作定义节点"""
        action_nodes = {}
        
        for action_name, action_def in self.alfworld_actions.items():
            action_id = self.kg_builder.add_action_node(
                action_name,
                {
                    'description': f"ALFWorld action: {action_name}",
                    'parameters': action_def['parameters'],
                    'preconditions': action_def['preconditions'],
                    'effects': action_def['effects'],
                    'cost': action_def['cost'],
                    'source': 'alfworld_domain'
                }
            )
            action_nodes[action_name] = action_id
            
            # 连接到场景
            self.kg_builder.add_edge(scene_id, action_id, EdgeType.CONTAINS,
                                   {"relationship": "scene_contains_action"})
        
        return action_nodes
    
    def _add_state_information(self, entity_nodes: Dict[str, str], 
                             initial_states: Dict[str, List], scene_id: str) -> Dict[str, str]:
        """添加状态信息"""
        state_nodes = {}
        
        # 为每个实体添加可能的状态
        for entity_name, entity_id in entity_nodes.items():
            # 基于实体类型推断可能状态
            entity_info = self.kg_builder.graph.nodes[entity_id]
            object_type = entity_info['attributes'].get('object_type', '')
            
            possible_states = self._get_possible_states(object_type)
            
            for state_name in possible_states:
                state_id = self.kg_builder.add_state_node(
                    f"{entity_name}_{state_name}",
                    state_name,
                    {
                        'entity_name': entity_name,
                        'state_category': self._get_state_category(state_name),
                        'is_initial': self._is_initial_state(entity_name, state_name, initial_states),
                        'source': 'inferred_from_type'
                    }
                )
                state_nodes[f"{entity_name}_{state_name}"] = state_id
                
                # 连接实体和状态
                self.kg_builder.add_edge(entity_id, state_id, EdgeType.HAS_STATE,
                                       {"state_type": state_name})
                
                # 连接到场景
                self.kg_builder.add_edge(scene_id, state_id, EdgeType.CONTAINS,
                                       {"relationship": "scene_contains_state"})
        
        # 添加从PDDL初始状态提取的状态
        for predicate, args_list in initial_states.items():
            for args in args_list:
                if len(args) >= 1:
                    state_key = f"{predicate}_{args[0]}" if args else predicate
                    if state_key not in state_nodes:
                        state_id = self.kg_builder.add_state_node(
                            state_key,
                            predicate,
                            {
                                'arguments': args,
                                'source': 'pddl_initial_state',
                                'is_initial': True
                            }
                        )
                        state_nodes[state_key] = state_id
                        
                        # 连接到场景
                        self.kg_builder.add_edge(scene_id, state_id, EdgeType.CONTAINS,
                                               {"relationship": "scene_contains_state"})
        
        return state_nodes
    
    def _add_goal_information(self, goal_states: Dict[str, List], scene_id: str, 
                            entity_nodes: Dict[str, str]) -> Dict[str, str]:
        """添加目标信息"""
        goal_nodes = {}
        
        for predicate, args_list in goal_states.items():
            for i, args in enumerate(args_list):
                goal_name = f"goal_{predicate}_{i}"
                goal_id = self.kg_builder.add_result_node(
                    goal_name,
                    "task_goal",
                    {
                        'goal_predicate': predicate,
                        'goal_arguments': args,
                        'description': f"Goal: {predicate}({', '.join(args)})",
                        'source': 'pddl_goal'
                    }
                )
                goal_nodes[goal_name] = goal_id
                
                # 连接到场景
                self.kg_builder.add_edge(scene_id, goal_id, EdgeType.CONTAINS,
                                       {"relationship": "scene_contains_goal"})
        
        return goal_nodes
    
    def _connect_actions_states_entities(self, action_nodes: Dict[str, str], 
                                       state_nodes: Dict[str, str], entity_nodes: Dict[str, str]):
        """建立动作-状态-实体之间的关系"""
        
        # 为每个动作建立与相关状态的连接
        for action_name, action_id in action_nodes.items():
            action_def = self.alfworld_actions[action_name]
            
            # 连接前置条件状态
            for precond in action_def['preconditions']:
                matching_states = [s_id for s_name, s_id in state_nodes.items() 
                                 if any(pred in precond for pred in ['atLocation', 'opened', 'holds'])]
                for state_id in matching_states[:3]:  # 限制连接数量
                    self.kg_builder.add_edge(state_id, action_id, EdgeType.ENABLES,
                                           {"relationship": "state_enables_action"})
            
            # 连接效果状态
            for effect in action_def['effects']:
                matching_states = [s_id for s_name, s_id in state_nodes.items()
                                 if any(pred in effect for pred in ['atLocation', 'opened', 'holds', 'inReceptacle'])]
                for state_id in matching_states[:3]:  # 限制连接数量
                    self.kg_builder.add_edge(action_id, state_id, EdgeType.PRODUCES,
                                           {"relationship": "action_produces_state"})
    
    def _get_possible_states(self, object_type: str) -> List[str]:
        """根据对象类型获取可能的状态"""
        base_states = ['available', 'visible']
        
        type_specific_states = {
            'Cabinet': ['opened', 'closed', 'locked', 'unlocked', 'full', 'empty'],
            'Drawer': ['opened', 'closed', 'locked', 'unlocked', 'full', 'empty'],
            'Fridge': ['opened', 'closed', 'full', 'empty'],
            'Microwave': ['opened', 'closed', 'on', 'off'],
            'TableTop': ['full', 'empty', 'clean', 'dirty'],
            'CounterTop': ['full', 'empty', 'clean', 'dirty'],
            'Sink': ['full', 'empty', 'clean', 'dirty'],
            'StoveBurner': ['on', 'off', 'hot', 'cold']
        }
        
        return base_states + type_specific_states.get(object_type, [])
    
    def _get_state_category(self, state_name: str) -> str:
        """获取状态类别"""
        categories = {
            'opened': 'container_state',
            'closed': 'container_state', 
            'locked': 'container_state',
            'unlocked': 'container_state',
            'full': 'content_state',
            'empty': 'content_state',
            'available': 'accessibility_state',
            'visible': 'visibility_state',
            'clean': 'condition_state',
            'dirty': 'condition_state',
            'on': 'power_state',
            'off': 'power_state'
        }
        return categories.get(state_name, 'general_state')
    
    def _is_initial_state(self, entity_name: str, state_name: str, initial_states: Dict) -> bool:
        """判断是否为初始状态"""
        # 简化实现：某些状态默认为初始状态
        default_initial = {
            'available': True,
            'visible': True,
            'closed': True,
            'empty': True,
            'off': True,
            'clean': True
        }
        return default_initial.get(state_name, False)
    
    def _export_scene_kg(self, scene_name: str, num_entities: int, 
                        num_actions: int, num_states: int) -> Dict[str, Any]:
        """导出场景KG"""
        kg_data = self.kg_builder.export_to_dict()
        
        # 添加场景元信息
        kg_data['scene_metadata'] = {
            'scene_name': scene_name,
            'scene_type': 'alfworld',
            'statistics': {
                'entities': num_entities,
                'actions': num_actions,
                'states': num_states,
                'total_nodes': len(kg_data['nodes']),
                'total_edges': len(kg_data['edges'])
            },
            'coverage': {
                'has_actions': num_actions > 0,
                'has_goals': any(n['type'] == 'result' for n in kg_data['nodes']),
                'has_states': num_states > 0,
                'has_entities': num_entities > 0
            }
        }
        
        return kg_data
    
    def build_all_scene_kgs(self, max_scenes: int = 20) -> Dict[str, Dict[str, Any]]:
        """构建所有场景的KG"""
        print(f"🏗️ 开始构建所有场景KG (最多 {max_scenes} 个)")
        
        # 查找ALFWorld数据
        alfworld_dir = Path("data/benchmarks/alfworld/alfworld/alfworld/gen/layouts")
        pddl_dir = Path("data/benchmarks/alfworld/alfworld/alfworld/gen/ff_planner/samples")
        
        if not alfworld_dir.exists():
            print("❌ ALFWorld数据目录不存在")
            return {}
        
        # 加载PDDL数据
        pddl_data = {}
        if pddl_dir.exists():
            for pddl_file in pddl_dir.glob("*.pddl"):
                if 'problem' in pddl_file.name:
                    with open(pddl_file, 'r') as f:
                        pddl_data[pddl_file.stem] = {
                            'problem_content': f.read(),
                            'source_file': str(pddl_file)
                        }
        
        # 处理布局文件
        layout_files = list(alfworld_dir.glob("*-openable.json"))[:max_scenes]
        if not layout_files:
            layout_files = list(alfworld_dir.glob("*.json"))[:max_scenes]
        
        scene_kgs = {}
        
        for layout_file in layout_files:
            try:
                with open(layout_file, 'r') as f:
                    layout_data = json.load(f)
                
                scene_name = layout_file.stem
                
                # 选择匹配的PDDL数据
                matching_pddl = next((pddl for pddl in pddl_data.values()), {})
                
                # 构建场景KG
                scene_kg = self.build_scene_kg_from_alfworld(layout_data, matching_pddl, scene_name)
                scene_kgs[scene_name] = scene_kg
                
                print(f"✅ 完成场景: {scene_name}")
                
            except Exception as e:
                print(f"❌ 处理场景失败 {layout_file.name}: {e}")
                continue
        
        print(f"🎉 完成所有场景KG构建: {len(scene_kgs)} 个场景")
        return scene_kgs


if __name__ == "__main__":
    # 测试场景KG构建器
    print("🧪 测试场景KG构建器")
    
    builder = SceneKGBuilder()
    
    # 构建所有场景KG
    scene_kgs = builder.build_all_scene_kgs(max_scenes=5)
    
    if scene_kgs:
        # 保存场景KG
        output_dir = Path("data/knowledge_graphs/enhanced_scenes")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for scene_name, scene_kg in scene_kgs.items():
            # 保存JSON格式
            json_file = output_dir / f"{scene_name}_enhanced_kg.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(scene_kg, f, indent=2, ensure_ascii=False)
            
            print(f"💾 保存场景KG: {json_file}")
        
        # 创建汇总信息
        summary = {
            'total_scenes': len(scene_kgs),
            'scenes': {name: kg['scene_metadata']['statistics'] for name, kg in scene_kgs.items()}
        }
        
        summary_file = output_dir / "enhanced_scenes_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📊 保存汇总信息: {summary_file}")
    
    print("✅ 测试完成")
