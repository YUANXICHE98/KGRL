"""
规则知识图谱构建器

专门用于构建基于规则的知识图谱，支持：
1. 条件-动作规则
2. 约束规则
3. 推理规则
4. 优先级规则
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from .dodaf_kg_builder import DODAFKGBuilder, NodeType, EdgeType, KGNode, KGEdge


class RuleType(Enum):
    """规则类型枚举"""
    CONDITION_ACTION = "condition_action"     # 条件-动作规则
    CONSTRAINT = "constraint"                 # 约束规则
    INFERENCE = "inference"                   # 推理规则
    PRIORITY = "priority"                     # 优先级规则
    TEMPORAL = "temporal"                     # 时序规则
    CAUSAL = "causal"                        # 因果规则


class ConditionType(Enum):
    """条件类型枚举"""
    PRECONDITION = "precondition"            # 前置条件
    POSTCONDITION = "postcondition"          # 后置条件
    INVARIANT = "invariant"                  # 不变条件
    TRIGGER = "trigger"                      # 触发条件


@dataclass
class Rule:
    """规则定义"""
    id: str
    name: str
    rule_type: RuleType
    conditions: List[str]
    actions: List[str]
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RuleKGBuilder(DODAFKGBuilder):
    """规则知识图谱构建器"""
    
    def __init__(self):
        super().__init__()
        self.rules: Dict[str, Rule] = {}
        self.rule_counter = 0
    
    def add_rule(self, name: str, rule_type: RuleType, 
                conditions: List[str], actions: List[str],
                priority: int = 0, enabled: bool = True,
                metadata: Dict[str, Any] = None) -> str:
        """添加规则"""
        rule_id = self._generate_node_id("rule")
        
        rule = Rule(
            id=rule_id,
            name=name,
            rule_type=rule_type,
            conditions=conditions,
            actions=actions,
            priority=priority,
            enabled=enabled,
            metadata=metadata or {}
        )
        
        self.rules[rule_id] = rule
        
        # 创建规则节点
        rule_node_id = self.add_rule_node(
            name, rule_type.value, conditions, actions,
            {
                "priority": priority,
                "enabled": enabled,
                **rule.metadata
            }
        )
        
        return rule_node_id
    
    def add_condition_action_rule(self, name: str, 
                                 conditions: List[str], 
                                 actions: List[str],
                                 priority: int = 0) -> str:
        """添加条件-动作规则
        
        示例: IF (有钥匙 AND 宝箱锁定) THEN 打开宝箱
        """
        rule_id = self.add_rule(
            name, RuleType.CONDITION_ACTION, 
            conditions, actions, priority
        )
        
        # 为每个条件创建条件节点
        condition_nodes = []
        for i, condition in enumerate(conditions):
            cond_id = self._generate_node_id("condition")
            cond_node = KGNode(
                id=cond_id,
                type=NodeType.CONDITION,
                name=f"{name}_条件_{i+1}",
                attributes={
                    "condition_text": condition,
                    "condition_type": ConditionType.PRECONDITION.value
                }
            )
            self.nodes[cond_id] = cond_node
            self.graph.add_node(cond_id, **cond_node.to_dict())
            condition_nodes.append(cond_id)
            
            # 条件指向规则
            self.add_edge(cond_id, rule_id, EdgeType.ENABLES)
        
        # 为每个动作创建动作节点
        action_nodes = []
        for i, action in enumerate(actions):
            action_id = self.add_action_node(
                action, 
                {"rule_action": True, "action_index": i}
            )
            action_nodes.append(action_id)
            
            # 规则指向动作
            self.add_edge(rule_id, action_id, EdgeType.PRODUCES)
        
        return rule_id
    
    def add_constraint_rule(self, name: str, 
                           constraint_conditions: List[str],
                           violation_actions: List[str] = None) -> str:
        """添加约束规则
        
        示例: 约束：不能同时拿取两个重物
        """
        rule_id = self.add_rule(
            name, RuleType.CONSTRAINT,
            constraint_conditions, 
            violation_actions or ["违反约束"],
            priority=100  # 约束规则通常有高优先级
        )
        
        # 创建约束节点
        for i, constraint in enumerate(constraint_conditions):
            constraint_id = self._generate_node_id("constraint")
            constraint_node = KGNode(
                id=constraint_id,
                type=NodeType.CONDITION,
                name=f"{name}_约束_{i+1}",
                attributes={
                    "constraint_text": constraint,
                    "constraint_type": "hard_constraint"
                }
            )
            self.nodes[constraint_id] = constraint_node
            self.graph.add_node(constraint_id, **constraint_node.to_dict())
            
            # 约束阻止规则执行
            self.add_edge(constraint_id, rule_id, EdgeType.PREVENTS)
        
        return rule_id
    
    def add_inference_rule(self, name: str,
                          premises: List[str],
                          conclusions: List[str]) -> str:
        """添加推理规则
        
        示例: IF (A是B的父亲 AND B是C的父亲) THEN A是C的祖父
        """
        rule_id = self.add_rule(
            name, RuleType.INFERENCE,
            premises, conclusions
        )
        
        # 创建前提节点
        premise_nodes = []
        for i, premise in enumerate(premises):
            premise_id = self._generate_node_id("premise")
            premise_node = KGNode(
                id=premise_id,
                type=NodeType.CONDITION,
                name=f"{name}_前提_{i+1}",
                attributes={
                    "premise_text": premise,
                    "logical_type": "premise"
                }
            )
            self.nodes[premise_id] = premise_node
            self.graph.add_node(premise_id, **premise_node.to_dict())
            premise_nodes.append(premise_id)
            
            self.add_edge(premise_id, rule_id, EdgeType.ENABLES)
        
        # 创建结论节点
        for i, conclusion in enumerate(conclusions):
            conclusion_id = self._generate_node_id("conclusion")
            conclusion_node = KGNode(
                id=conclusion_id,
                type=NodeType.RESULT,
                name=f"{name}_结论_{i+1}",
                attributes={
                    "conclusion_text": conclusion,
                    "logical_type": "conclusion"
                }
            )
            self.nodes[conclusion_id] = conclusion_node
            self.graph.add_node(conclusion_id, **conclusion_node.to_dict())
            
            self.add_edge(rule_id, conclusion_id, EdgeType.PRODUCES)
        
        return rule_id
    
    def add_priority_rule(self, name: str,
                         high_priority_rule: str,
                         low_priority_rule: str,
                         conflict_resolution: str = "override") -> str:
        """添加优先级规则
        
        定义规则之间的优先级关系
        """
        rule_id = self.add_rule(
            name, RuleType.PRIORITY,
            [f"规则冲突: {high_priority_rule} vs {low_priority_rule}"],
            [f"执行: {high_priority_rule}"],
            metadata={
                "high_priority_rule": high_priority_rule,
                "low_priority_rule": low_priority_rule,
                "resolution_strategy": conflict_resolution
            }
        )
        
        return rule_id
    
    def add_temporal_rule(self, name: str,
                         temporal_conditions: List[str],
                         temporal_actions: List[str],
                         time_constraints: Dict[str, Any] = None) -> str:
        """添加时序规则
        
        示例: 在T1时刻执行动作A，在T2时刻执行动作B
        """
        rule_id = self.add_rule(
            name, RuleType.TEMPORAL,
            temporal_conditions, temporal_actions,
            metadata={
                "time_constraints": time_constraints or {},
                "temporal_type": "sequence"
            }
        )
        
        return rule_id
    
    def build_game_rules_kg(self, game_rules: Dict[str, Any]) -> None:
        """从游戏规则构建知识图谱"""
        
        # 基本动作规则
        if "basic_actions" in game_rules:
            for action_name, action_info in game_rules["basic_actions"].items():
                self.add_condition_action_rule(
                    f"执行_{action_name}",
                    action_info.get("preconditions", []),
                    [action_name],
                    priority=1
                )
        
        # 约束规则
        if "constraints" in game_rules:
            for constraint_name, constraint_info in game_rules["constraints"].items():
                self.add_constraint_rule(
                    constraint_name,
                    constraint_info.get("conditions", []),
                    constraint_info.get("violations", [])
                )
        
        # 推理规则
        if "inference_rules" in game_rules:
            for rule_name, rule_info in game_rules["inference_rules"].items():
                self.add_inference_rule(
                    rule_name,
                    rule_info.get("premises", []),
                    rule_info.get("conclusions", [])
                )
    
    def export_rules_to_json(self, filepath: str) -> None:
        """导出规则到JSON文件"""
        rules_data = {
            "rules": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "type": rule.rule_type.value,
                    "conditions": rule.conditions,
                    "actions": rule.actions,
                    "priority": rule.priority,
                    "enabled": rule.enabled,
                    "metadata": rule.metadata
                }
                for rule in self.rules.values()
            ],
            "graph": {
                "nodes": [node.to_dict() for node in self.nodes.values()],
                "edges": [edge.to_dict() for edge in self.edges]
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False)


def create_example_rule_kg() -> RuleKGBuilder:
    """创建示例规则知识图谱"""
    builder = RuleKGBuilder()
    
    # 示例1: 开门规则
    builder.add_condition_action_rule(
        "开门规则",
        ["有钥匙", "门是锁定的", "钥匙匹配门"],
        ["打开门", "门状态变为打开"],
        priority=5
    )
    
    # 示例2: 约束规则
    builder.add_constraint_rule(
        "负重约束",
        ["背包重量 > 最大负重"],
        ["无法拿取物品", "显示负重警告"]
    )
    
    # 示例3: 推理规则
    builder.add_inference_rule(
        "传递性推理",
        ["A在B里面", "B在C里面"],
        ["A在C里面"]
    )
    
    return builder


if __name__ == "__main__":
    # 创建示例规则知识图谱
    kg = create_example_rule_kg()
    
    # 输出统计信息
    stats = kg.get_statistics()
    print("规则知识图谱统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 导出文件
    output_dir = Path("data/knowledge_graphs/rules")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    kg.export_rules_to_json(output_dir / "example_rules_kg.json")
    kg.export_to_graphml(output_dir / "example_rules_kg.graphml")
    
    print(f"\n规则知识图谱已导出到: {output_dir}")
