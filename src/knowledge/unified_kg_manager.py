"""
统一知识图谱管理器

整合不同类型的知识图谱：
1. DODAF状态知识图谱
2. 规则知识图谱
3. 领域特定知识图谱
4. 动态知识图谱更新
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Union
from pathlib import Path
import json
import networkx as nx
from datetime import datetime

from .dodaf_kg_builder import DODAFKGBuilder, NodeType, EdgeType
from .rule_kg_builder import RuleKGBuilder, RuleType


class UnifiedKGManager:
    """统一知识图谱管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.kg_instances: Dict[str, DODAFKGBuilder] = {}
        self.kg_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 主图谱用于整合所有子图谱
        self.unified_graph = nx.MultiDiGraph()
        
        # 知识图谱类型注册
        self.kg_types = {
            "dodaf": DODAFKGBuilder,
            "rule": RuleKGBuilder
        }
    
    def create_kg(self, kg_id: str, kg_type: str, 
                  metadata: Dict[str, Any] = None) -> DODAFKGBuilder:
        """创建新的知识图谱实例"""
        if kg_type not in self.kg_types:
            raise ValueError(f"不支持的知识图谱类型: {kg_type}")
        
        kg_class = self.kg_types[kg_type]
        kg_instance = kg_class()
        
        self.kg_instances[kg_id] = kg_instance
        self.kg_metadata[kg_id] = {
            "type": kg_type,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        return kg_instance
    
    def get_kg(self, kg_id: str) -> Optional[DODAFKGBuilder]:
        """获取知识图谱实例"""
        return self.kg_instances.get(kg_id)
    
    def list_kgs(self) -> List[Dict[str, Any]]:
        """列出所有知识图谱"""
        return [
            {
                "id": kg_id,
                "metadata": metadata,
                "stats": self.kg_instances[kg_id].get_statistics()
            }
            for kg_id, metadata in self.kg_metadata.items()
        ]
    
    def merge_kgs(self, source_kg_ids: List[str], 
                  target_kg_id: str, 
                  merge_strategy: str = "union") -> DODAFKGBuilder:
        """合并多个知识图谱"""
        if merge_strategy == "union":
            return self._merge_union(source_kg_ids, target_kg_id)
        elif merge_strategy == "intersection":
            return self._merge_intersection(source_kg_ids, target_kg_id)
        else:
            raise ValueError(f"不支持的合并策略: {merge_strategy}")
    
    def _merge_union(self, source_kg_ids: List[str], 
                    target_kg_id: str) -> DODAFKGBuilder:
        """联合合并策略"""
        target_kg = DODAFKGBuilder()
        
        # 合并所有节点和边
        for kg_id in source_kg_ids:
            if kg_id not in self.kg_instances:
                continue
                
            source_kg = self.kg_instances[kg_id]
            
            # 复制节点
            for node_id, node in source_kg.nodes.items():
                new_node_id = f"{kg_id}_{node_id}"
                target_kg.nodes[new_node_id] = node
                target_kg.graph.add_node(new_node_id, **node.to_dict())
            
            # 复制边
            for edge in source_kg.edges:
                new_source = f"{kg_id}_{edge.source}"
                new_target = f"{kg_id}_{edge.target}"
                target_kg.add_edge(new_source, new_target, edge.type, edge.attributes)
        
        # 注册合并后的图谱
        self.kg_instances[target_kg_id] = target_kg
        self.kg_metadata[target_kg_id] = {
            "type": "merged",
            "source_kgs": source_kg_ids,
            "merge_strategy": "union",
            "created_at": datetime.now().isoformat()
        }
        
        return target_kg
    
    def _merge_intersection(self, source_kg_ids: List[str], 
                           target_kg_id: str) -> DODAFKGBuilder:
        """交集合并策略"""
        # 实现交集合并逻辑
        # 这里简化实现，实际应该找到共同的节点和边
        target_kg = DODAFKGBuilder()
        
        if len(source_kg_ids) < 2:
            return target_kg
        
        # 找到第一个图谱作为基准
        base_kg = self.kg_instances.get(source_kg_ids[0])
        if not base_kg:
            return target_kg
        
        # 找到所有图谱中共同的节点
        common_nodes = set(base_kg.nodes.keys())
        for kg_id in source_kg_ids[1:]:
            if kg_id in self.kg_instances:
                kg = self.kg_instances[kg_id]
                common_nodes &= set(kg.nodes.keys())
        
        # 添加共同节点到目标图谱
        for node_id in common_nodes:
            node = base_kg.nodes[node_id]
            target_kg.nodes[node_id] = node
            target_kg.graph.add_node(node_id, **node.to_dict())
        
        # 注册合并后的图谱
        self.kg_instances[target_kg_id] = target_kg
        self.kg_metadata[target_kg_id] = {
            "type": "merged",
            "source_kgs": source_kg_ids,
            "merge_strategy": "intersection",
            "created_at": datetime.now().isoformat()
        }
        
        return target_kg
    
    def query_kg(self, kg_id: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询知识图谱"""
        kg = self.kg_instances.get(kg_id)
        if not kg:
            return []
        
        results = []
        
        # 节点查询
        if "node_type" in query:
            node_type = query["node_type"]
            for node_id, node in kg.nodes.items():
                if node.type.value == node_type:
                    results.append({
                        "type": "node",
                        "id": node_id,
                        "data": node.to_dict()
                    })
        
        # 边查询
        if "edge_type" in query:
            edge_type = query["edge_type"]
            for edge in kg.edges:
                if edge.type.value == edge_type:
                    results.append({
                        "type": "edge",
                        "data": edge.to_dict()
                    })
        
        # 路径查询
        if "path_query" in query:
            path_query = query["path_query"]
            source = path_query.get("source")
            target = path_query.get("target")
            
            if source and target and source in kg.nodes and target in kg.nodes:
                try:
                    paths = list(nx.all_simple_paths(
                        kg.graph, source, target, 
                        cutoff=path_query.get("max_length", 5)
                    ))
                    results.extend([
                        {"type": "path", "data": path} 
                        for path in paths
                    ])
                except nx.NetworkXNoPath:
                    pass
        
        return results
    
    def update_kg_from_experience(self, kg_id: str, 
                                 experience: Dict[str, Any]) -> None:
        """从经验中更新知识图谱"""
        kg = self.kg_instances.get(kg_id)
        if not kg:
            return
        
        # 从经验中提取新的状态转换
        if "state_transitions" in experience:
            for transition in experience["state_transitions"]:
                self._add_state_transition(kg, transition)
        
        # 从经验中提取新的动作效果
        if "action_effects" in experience:
            for effect in experience["action_effects"]:
                self._add_action_effect(kg, effect)
        
        # 更新元数据
        self.kg_metadata[kg_id]["last_updated"] = datetime.now().isoformat()
    
    def _add_state_transition(self, kg: DODAFKGBuilder, 
                             transition: Dict[str, Any]) -> None:
        """添加状态转换"""
        entity_name = transition.get("entity")
        pre_state = transition.get("pre_state")
        post_state = transition.get("post_state")
        action = transition.get("action")
        
        if all([entity_name, pre_state, post_state, action]):
            kg.build_action_state_pattern(
                action, entity_name, "实体",
                pre_state, post_state
            )
    
    def _add_action_effect(self, kg: DODAFKGBuilder, 
                          effect: Dict[str, Any]) -> None:
        """添加动作效果"""
        action_name = effect.get("action")
        effects = effect.get("effects", [])
        
        if action_name and effects:
            action_id = kg.add_action_node(action_name)
            
            for effect_desc in effects:
                result_id = kg._generate_node_id("result")
                result_node = kg.KGNode(
                    id=result_id,
                    type=NodeType.RESULT,
                    name=effect_desc,
                    attributes={"effect_type": "learned"}
                )
                kg.nodes[result_id] = result_node
                kg.graph.add_node(result_id, **result_node.to_dict())
                kg.add_edge(action_id, result_id, EdgeType.PRODUCES)
    
    def export_all_kgs(self, output_dir: str) -> None:
        """导出所有知识图谱"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for kg_id, kg in self.kg_instances.items():
            # 导出JSON格式
            json_file = output_path / f"{kg_id}.json"
            kg.export_to_json(str(json_file))
            
            # 导出GraphML格式
            graphml_file = output_path / f"{kg_id}.graphml"
            kg.export_to_graphml(str(graphml_file))
        
        # 导出元数据
        metadata_file = output_path / "kg_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.kg_metadata, f, indent=2, ensure_ascii=False)
    
    def load_kgs_from_directory(self, input_dir: str) -> None:
        """从目录加载知识图谱"""
        input_path = Path(input_dir)
        
        # 加载元数据
        metadata_file = input_path / "kg_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.kg_metadata = json.load(f)
        
        # 加载各个知识图谱
        for json_file in input_path.glob("*.json"):
            if json_file.name == "kg_metadata.json":
                continue
                
            kg_id = json_file.stem
            
            # 根据元数据确定类型
            kg_type = self.kg_metadata.get(kg_id, {}).get("type", "dodaf")
            kg = self.create_kg(kg_id, kg_type)
            
            # 加载图谱数据（这里需要实现加载逻辑）
            # 简化实现，实际需要根据JSON结构重建图谱
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # TODO: 实现从JSON重建图谱的逻辑


def create_example_unified_kg() -> UnifiedKGManager:
    """创建示例统一知识图谱"""
    manager = UnifiedKGManager()
    
    # 创建DODAF状态图谱
    dodaf_kg = manager.create_kg("game_states", "dodaf", {
        "domain": "textworld",
        "description": "游戏状态知识图谱"
    })
    
    # 添加示例状态模式
    dodaf_kg.build_action_state_pattern(
        "打开", "宝箱", "容器", "锁定", "打开", "成功打开"
    )
    
    # 创建规则图谱
    rule_kg = manager.create_kg("game_rules", "rule", {
        "domain": "textworld",
        "description": "游戏规则知识图谱"
    })
    
    # 添加示例规则
    rule_kg.add_condition_action_rule(
        "开箱规则",
        ["有钥匙", "宝箱锁定"],
        ["打开宝箱"]
    )
    
    return manager


if __name__ == "__main__":
    # 创建示例统一知识图谱
    manager = create_example_unified_kg()
    
    # 列出所有图谱
    kgs = manager.list_kgs()
    print("知识图谱列表:")
    for kg_info in kgs:
        print(f"  {kg_info['id']}: {kg_info['metadata']['description']}")
        print(f"    统计: {kg_info['stats']}")
    
    # 导出所有图谱
    output_dir = Path("data/knowledge_graphs/unified")
    manager.export_all_kgs(str(output_dir))
    
    print(f"\n统一知识图谱已导出到: {output_dir}")
