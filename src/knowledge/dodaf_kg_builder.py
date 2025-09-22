"""
DODAF状态知识图谱构建器

基于DODAF架构框架构建状态知识图谱，支持：
1. 动作-状态关系建模
2. 实体属性跟踪
3. 规则约束表示
4. 状态转换逻辑
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import networkx as nx
import json
from pathlib import Path


class NodeType(Enum):
    """节点类型枚举"""
    ACTION = "action"           # 动作节点
    ENTITY = "entity"           # 实体节点
    STATE = "state"             # 状态节点
    RULE = "rule"               # 规则节点
    RESULT = "result"           # 结果节点
    CONDITION = "condition"     # 条件节点


class EdgeType(Enum):
    """边类型枚举"""
    REQUIRES = "requires"       # 需要关系
    PRODUCES = "produces"       # 产生关系
    MODIFIES = "modifies"       # 修改关系
    ENABLES = "enables"         # 启用关系
    PREVENTS = "prevents"       # 阻止关系
    TRANSITIONS = "transitions" # 状态转换
    CONTAINS = "contains"       # 包含关系
    HAS_STATE = "has_state"     # 具有状态关系


@dataclass
class KGNode:
    """知识图谱节点"""
    id: str
    type: NodeType
    name: str
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "attributes": self.attributes
        }


@dataclass
class KGEdge:
    """知识图谱边"""
    source: str
    target: str
    type: EdgeType
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "attributes": self.attributes
        }


class DODAFKGBuilder:
    """DODAF状态知识图谱构建器"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.nodes: Dict[str, KGNode] = {}
        self.edges: List[KGEdge] = []
        self.node_counter = 0
        
    def _generate_node_id(self, prefix: str = "node") -> str:
        """生成唯一节点ID"""
        self.node_counter += 1
        return f"{prefix}_{self.node_counter}"
    
    def add_action_node(self, name: str, attributes: Dict[str, Any] = None) -> str:
        """添加动作节点"""
        node_id = self._generate_node_id("action")
        node = KGNode(
            id=node_id,
            type=NodeType.ACTION,
            name=name,
            attributes=attributes or {}
        )
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        return node_id
    
    def add_entity_node(self, name: str, entity_type: str, 
                       attributes: Dict[str, Any] = None) -> str:
        """添加实体节点"""
        node_id = self._generate_node_id("entity")
        attrs = attributes or {}
        attrs["entity_type"] = entity_type
        
        node = KGNode(
            id=node_id,
            type=NodeType.ENTITY,
            name=name,
            attributes=attrs
        )
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        return node_id
    
    def add_state_node(self, name: str, state_value: str,
                      attributes: Dict[str, Any] = None) -> str:
        """添加状态节点"""
        node_id = self._generate_node_id("state")
        attrs = attributes or {}
        attrs["state_value"] = state_value
        
        node = KGNode(
            id=node_id,
            type=NodeType.STATE,
            name=name,
            attributes=attrs
        )
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        return node_id
    
    def add_rule_node(self, name: str, rule_type: str,
                     conditions: List[str], actions: List[str],
                     attributes: Dict[str, Any] = None) -> str:
        """添加规则节点"""
        node_id = self._generate_node_id("rule")
        attrs = attributes or {}
        attrs.update({
            "rule_type": rule_type,
            "conditions": conditions,
            "actions": actions
        })
        
        node = KGNode(
            id=node_id,
            type=NodeType.RULE,
            name=name,
            attributes=attrs
        )
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        return node_id

    def add_result_node(self, name: str, result_value: str,
                       attributes: Dict[str, Any] = None) -> str:
        """添加结果节点"""
        node_id = self._generate_node_id("result")
        attrs = attributes or {}
        attrs["result_value"] = result_value

        node = KGNode(
            id=node_id,
            type=NodeType.RESULT,
            name=name,
            attributes=attrs
        )
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        return node_id

    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType,
                attributes: Dict[str, Any] = None) -> None:
        """添加边"""
        edge = KGEdge(
            source=source_id,
            target=target_id,
            type=edge_type,
            attributes=attributes or {}
        )
        self.edges.append(edge)
        self.graph.add_edge(source_id, target_id, **edge.to_dict())
    
    def build_action_state_pattern(self, action_name: str, 
                                  entity_name: str, entity_type: str,
                                  pre_state: str, post_state: str,
                                  result_name: str = None) -> Dict[str, str]:
        """构建动作-状态模式
        
        示例: 打开(钥匙) -> 宝箱[锁定] -> 宝箱[打开]
        """
        # 创建节点
        action_id = self.add_action_node(action_name)
        entity_id = self.add_entity_node(entity_name, entity_type)
        pre_state_id = self.add_state_node(f"{entity_name}_pre", pre_state)
        post_state_id = self.add_state_node(f"{entity_name}_post", post_state)
        
        # 添加结果节点（如果指定）
        result_id = None
        if result_name:
            result_id = self._generate_node_id("result")
            result_node = KGNode(
                id=result_id,
                type=NodeType.RESULT,
                name=result_name,
                attributes={"result_type": "action_outcome"}
            )
            self.nodes[result_id] = result_node
            self.graph.add_node(result_id, **result_node.to_dict())
        
        # 创建边关系
        self.add_edge(action_id, entity_id, EdgeType.MODIFIES)
        self.add_edge(entity_id, pre_state_id, EdgeType.REQUIRES)
        self.add_edge(action_id, post_state_id, EdgeType.PRODUCES)
        self.add_edge(pre_state_id, post_state_id, EdgeType.TRANSITIONS)
        
        if result_id:
            self.add_edge(action_id, result_id, EdgeType.PRODUCES)
        
        return {
            "action": action_id,
            "entity": entity_id,
            "pre_state": pre_state_id,
            "post_state": post_state_id,
            "result": result_id
        }
    
    def export_to_json(self, filepath: str) -> None:
        """导出为JSON格式"""
        data = {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "node_types": list(set(node.type.value for node in self.nodes.values()))
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export_to_graphml(self, filepath: str) -> None:
        """导出为GraphML格式"""
        # 创建一个简化的图，只包含基本属性
        simple_graph = nx.DiGraph()

        # 添加节点，只保留字符串和数字属性
        for node_id, node_data in self.graph.nodes(data=True):
            simple_attrs = {}
            for key, value in node_data.items():
                if isinstance(value, (str, int, float, bool)):
                    simple_attrs[key] = str(value)
                elif isinstance(value, dict):
                    # 将字典转换为字符串
                    simple_attrs[f"{key}_json"] = str(value)
            simple_graph.add_node(node_id, **simple_attrs)

        # 添加边，只保留字符串和数字属性
        for source, target, edge_data in self.graph.edges(data=True):
            simple_attrs = {}
            for key, value in edge_data.items():
                if isinstance(value, (str, int, float, bool)):
                    simple_attrs[key] = str(value)
                elif isinstance(value, dict):
                    simple_attrs[f"{key}_json"] = str(value)
            simple_graph.add_edge(source, target, **simple_attrs)

        nx.write_graphml(simple_graph, filepath)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        node_types = {}
        for node in self.nodes.values():
            node_type = node.type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        edge_types = {}
        for edge in self.edges:
            edge_type = edge.type.value
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph)
        }

    def extract_from_alfworld_json(self, json_data: Dict[str, Any], scene_name: str = "unknown") -> Dict[str, Any]:
        """从ALFWorld JSON布局数据中抽取知识图谱

        Args:
            json_data: ALFWorld布局JSON数据
            scene_name: 场景名称

        Returns:
            dict: 抽取统计信息
        """
        extracted_nodes = 0
        extracted_edges = 0

        # 创建场景节点
        scene_id = self.add_entity_node(scene_name, "scene", {
            'category': 'environment',
            'description': f'ALFWorld scene: {scene_name}'
        })
        extracted_nodes += 1

        # 处理布局中的每个对象
        for object_key, position_data in json_data.items():
            # 解析对象信息 格式: "ObjectType|x|y|z"
            parts = object_key.split('|')
            if len(parts) >= 4:
                object_type = parts[0]
                x_pos = parts[1]
                y_pos = parts[2]
                z_pos = parts[3]

                # 创建对象实体节点
                object_id = self.add_entity_node(object_type, "furniture", {
                    'category': 'physical_object',
                    'position_x': float(x_pos),
                    'position_y': float(y_pos),
                    'position_z': float(z_pos),
                    'layout_data': str(position_data),  # 转换为字符串避免GraphML问题
                    'source': 'alfworld'
                })
                extracted_nodes += 1

                # 创建与场景的空间关系
                self.add_edge(scene_id, object_id, EdgeType.CONTAINS, {
                    'relationship': 'spatial_containment',
                    'position_info': str(position_data)
                })
                extracted_edges += 1

                # 创建对象的默认状态
                state_id = self.add_state_node(f"{object_type}_available", "accessible", {
                    'state_type': 'availability',
                    'object_name': object_type,
                    'description': f'{object_type} is accessible in the environment'
                })

                self.add_edge(object_id, state_id, EdgeType.HAS_STATE, {
                    'state_category': 'availability'
                })
                extracted_nodes += 1
                extracted_edges += 1

        return {
            'nodes_extracted': extracted_nodes,
            'edges_extracted': extracted_edges,
            'scene_name': scene_name,
            'objects_processed': len(json_data)
        }

    def extract_from_pddl_problem(self, pddl_content: str, problem_name: str = "unknown") -> Dict[str, Any]:
        """从PDDL问题文件中抽取知识图谱

        Args:
            pddl_content: PDDL文件内容
            problem_name: 问题名称

        Returns:
            dict: 抽取统计信息
        """
        import re

        extracted_nodes = 0
        extracted_edges = 0

        # 创建问题节点
        problem_id = self.add_entity_node(problem_name, "problem", {
            'category': 'planning_problem',
            'description': f'PDDL planning problem: {problem_name}',
            'source': 'pddl'
        })
        extracted_nodes += 1

        # 解析对象定义
        objects_match = re.search(r'\(:objects\s+(.*?)\)', pddl_content, re.DOTALL)
        if objects_match:
            objects_text = objects_match.group(1)
            # 解析对象和类型 格式: "object1 object2 - type"
            object_lines = [line.strip() for line in objects_text.split('\n') if line.strip()]

            for line in object_lines:
                if ' - ' in line:
                    objects_part, type_part = line.split(' - ')
                    object_names = objects_part.strip().split()
                    object_type = type_part.strip()

                    for obj_name in object_names:
                        if obj_name:  # 跳过空字符串
                            # 创建对象实体节点
                            obj_id = self.add_entity_node(obj_name, object_type, {
                                'category': 'pddl_object',
                                'object_type': object_type,
                                'source': 'pddl'
                            })
                            extracted_nodes += 1

                            # 与问题建立关系
                            self.add_edge(problem_id, obj_id, EdgeType.CONTAINS, {
                                'relationship': 'problem_contains_object'
                            })
                            extracted_edges += 1

                            # 创建对象的初始状态
                            initial_state_id = self.add_state_node(f"{obj_name}_initial", "available", {
                                'state_type': 'initial',
                                'object_name': obj_name,
                                'object_type': object_type
                            })

                            self.add_edge(obj_id, initial_state_id, EdgeType.HAS_STATE, {
                                'state_category': 'initial'
                            })
                            extracted_nodes += 1
                            extracted_edges += 1

        # 解析初始状态（如果存在）
        init_match = re.search(r'\(:init\s+(.*?)\)', pddl_content, re.DOTALL)
        if init_match:
            init_text = init_match.group(1)
            # 简单解析谓词，可以根据需要扩展
            predicates = re.findall(r'\([^)]+\)', init_text)

            for predicate in predicates:
                # 创建初始条件状态
                pred_clean = predicate.strip('()')
                if pred_clean:
                    condition_id = self.add_state_node(f"init_{pred_clean}", "true", {
                        'state_type': 'initial_condition',
                        'predicate': pred_clean,
                        'source': 'pddl'
                    })

                    self.add_edge(problem_id, condition_id, EdgeType.HAS_STATE, {
                        'state_category': 'initial_condition'
                    })
                    extracted_nodes += 1
                    extracted_edges += 1

        # 解析目标状态（如果存在）
        goal_match = re.search(r'\(:goal\s+(.*?)\)', pddl_content, re.DOTALL)
        if goal_match:
            goal_text = goal_match.group(1)
            # 创建目标状态
            goal_id = self.add_state_node(f"goal_{problem_name}", "target", {
                'state_type': 'goal',
                'goal_description': goal_text.strip(),
                'source': 'pddl'
            })

            self.add_edge(problem_id, goal_id, EdgeType.REQUIRES, {
                'relationship': 'problem_requires_goal'
            })
            extracted_nodes += 1
            extracted_edges += 1

        return {
            'nodes_extracted': extracted_nodes,
            'edges_extracted': extracted_edges,
            'problem_name': problem_name,
            'source': 'pddl'
        }


def create_example_kg() -> DODAFKGBuilder:
    """创建示例知识图谱"""
    builder = DODAFKGBuilder()
    
    # 示例：打开宝箱的动作序列
    pattern = builder.build_action_state_pattern(
        action_name="打开",
        entity_name="宝箱",
        entity_type="容器",
        pre_state="锁定",
        post_state="打开",
        result_name="打开成功"
    )
    
    # 添加钥匙实体和相关状态
    key_id = builder.add_entity_node("青铜钥匙", "道具", {"material": "青铜"})
    key_state_ungot = builder.add_state_node("钥匙状态", "未获取")
    key_state_got = builder.add_state_node("钥匙状态", "已获取")
    
    # 添加获取钥匙的动作
    get_action_id = builder.add_action_node("获取")
    
    # 建立关系
    builder.add_edge(key_id, key_state_ungot, EdgeType.REQUIRES)
    builder.add_edge(get_action_id, key_id, EdgeType.MODIFIES)
    builder.add_edge(get_action_id, key_state_got, EdgeType.PRODUCES)
    builder.add_edge(key_state_got, pattern["action"], EdgeType.ENABLES)
    
    return builder


if __name__ == "__main__":
    # 创建示例知识图谱
    kg = create_example_kg()
    
    # 输出统计信息
    stats = kg.get_statistics()
    print("知识图谱统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 导出文件
    output_dir = Path("data/knowledge_graphs/dodaf")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    kg.export_to_json(output_dir / "example_dodaf_kg.json")
    kg.export_to_graphml(output_dir / "example_dodaf_kg.graphml")
    
    print(f"\n知识图谱已导出到: {output_dir}")
