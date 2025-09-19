"""
ALFWorld数据预处理脚本

从ALFWorld数据中提取状态信息，构建DODAF知识图谱
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder, NodeType, EdgeType


class ALFWorldPreprocessor:
    """ALFWorld数据预处理器"""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 动作映射
        self.action_mapping = {
            "go to": "移动到",
            "take": "拿取",
            "put": "放置",
            "open": "打开",
            "close": "关闭",
            "toggle": "切换",
            "clean": "清洁",
            "heat": "加热",
            "cool": "冷却",
            "use": "使用"
        }
        
        # 实体类型映射
        self.entity_types = {
            "receptacle": "容器",
            "object": "物品",
            "appliance": "设备",
            "furniture": "家具"
        }
    
    def extract_actions_from_trajectory(self, trajectory: List[str]) -> List[Dict[str, Any]]:
        """从轨迹中提取动作序列"""
        actions = []
        
        for step in trajectory:
            # 解析动作
            action_match = re.match(r'^(\w+(?:\s+\w+)*)\s+(.+)$', step.strip())
            if action_match:
                action_verb = action_match.group(1).lower()
                action_object = action_match.group(2)
                
                # 映射动作名称
                mapped_action = self.action_mapping.get(action_verb, action_verb)
                
                actions.append({
                    "action": mapped_action,
                    "object": action_object,
                    "original": step.strip()
                })
        
        return actions
    
    def extract_entities_from_observation(self, observation: str) -> List[Dict[str, Any]]:
        """从观察中提取实体信息"""
        entities = []
        
        # 简单的实体提取（可以改进）
        # 查找常见的物品和容器
        patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:is|are)\s+(open|closed|clean|dirty|hot|cold)',
            r'(?:a|an|the)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:on|in|under)\s+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, observation.lower())
            for match in matches:
                if isinstance(match, tuple):
                    entity_name = match[0]
                    state = match[1] if len(match) > 1 else None
                else:
                    entity_name = match
                    state = None
                
                entities.append({
                    "name": entity_name,
                    "state": state,
                    "type": self._infer_entity_type(entity_name)
                })
        
        return entities
    
    def _infer_entity_type(self, entity_name: str) -> str:
        """推断实体类型"""
        # 简单的类型推断规则
        containers = ["drawer", "cabinet", "fridge", "microwave", "sink", "toilet"]
        objects = ["apple", "bread", "egg", "lettuce", "tomato", "potato", "knife"]
        appliances = ["stove", "microwave", "fridge", "toaster"]
        
        entity_lower = entity_name.lower()
        
        if any(container in entity_lower for container in containers):
            return "容器"
        elif any(obj in entity_lower for obj in objects):
            return "物品"
        elif any(app in entity_lower for app in appliances):
            return "设备"
        else:
            return "物品"  # 默认类型
    
    def build_kg_from_episode(self, episode_data: Dict[str, Any]) -> DODAFKGBuilder:
        """从单个episode构建知识图谱"""
        kg_builder = DODAFKGBuilder()
        
        # 提取轨迹信息
        if "trajectory" in episode_data:
            actions = self.extract_actions_from_trajectory(episode_data["trajectory"])
            
            # 为每个动作创建节点和关系
            prev_state_nodes = {}
            
            for i, action_info in enumerate(actions):
                # 创建动作节点
                action_id = kg_builder.add_action_node(
                    action_info["action"],
                    {"step": i, "original_command": action_info["original"]}
                )
                
                # 创建或获取实体节点
                entity_name = action_info["object"]
                entity_type = self._infer_entity_type(entity_name)
                entity_id = kg_builder.add_entity_node(entity_name, entity_type)
                
                # 创建状态转换
                pre_state_id = kg_builder.add_state_node(
                    f"{entity_name}_pre_{i}", "unknown"
                )
                post_state_id = kg_builder.add_state_node(
                    f"{entity_name}_post_{i}", "modified"
                )
                
                # 添加关系
                kg_builder.add_edge(action_id, entity_id, EdgeType.MODIFIES)
                kg_builder.add_edge(entity_id, pre_state_id, EdgeType.REQUIRES)
                kg_builder.add_edge(action_id, post_state_id, EdgeType.PRODUCES)
                kg_builder.add_edge(pre_state_id, post_state_id, EdgeType.TRANSITIONS)
                
                # 如果有前一个状态，建立连接
                if entity_name in prev_state_nodes:
                    kg_builder.add_edge(
                        prev_state_nodes[entity_name], 
                        pre_state_id, 
                        EdgeType.TRANSITIONS
                    )
                
                prev_state_nodes[entity_name] = post_state_id
        
        return kg_builder
    
    def process_alfworld_data(self) -> None:
        """处理ALFWorld数据"""
        print("🚀 开始处理ALFWorld数据...")
        
        # 查找数据文件
        data_files = list(self.data_dir.rglob("*.json"))
        
        if not data_files:
            print("❌ 未找到ALFWorld数据文件")
            return
        
        print(f"📁 找到 {len(data_files)} 个数据文件")
        
        all_kgs = []
        
        for i, data_file in enumerate(data_files[:10]):  # 处理前10个文件作为示例
            print(f"📄 处理文件 {i+1}/{min(10, len(data_files))}: {data_file.name}")
            
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 如果是episode列表
                if isinstance(data, list):
                    for j, episode in enumerate(data[:5]):  # 每个文件处理前5个episode
                        kg = self.build_kg_from_episode(episode)
                        
                        # 保存单个KG
                        output_file = self.output_dir / f"alfworld_kg_{i}_{j}.json"
                        kg.export_to_json(str(output_file))
                        all_kgs.append(kg)
                
                # 如果是单个episode
                elif isinstance(data, dict):
                    kg = self.build_kg_from_episode(data)
                    output_file = self.output_dir / f"alfworld_kg_{i}.json"
                    kg.export_to_json(str(output_file))
                    all_kgs.append(kg)
                    
            except Exception as e:
                print(f"⚠️  处理文件 {data_file} 时出错: {e}")
                continue
        
        print(f"✅ 成功处理 {len(all_kgs)} 个知识图谱")
        
        # 生成统计报告
        self._generate_statistics_report(all_kgs)
    
    def _generate_statistics_report(self, kgs: List[DODAFKGBuilder]) -> None:
        """生成统计报告"""
        if not kgs:
            return
        
        total_stats = {
            "total_graphs": len(kgs),
            "total_nodes": 0,
            "total_edges": 0,
            "node_types": {},
            "edge_types": {}
        }
        
        for kg in kgs:
            stats = kg.get_statistics()
            total_stats["total_nodes"] += stats["total_nodes"]
            total_stats["total_edges"] += stats["total_edges"]
            
            # 合并节点类型统计
            for node_type, count in stats["node_types"].items():
                total_stats["node_types"][node_type] = \
                    total_stats["node_types"].get(node_type, 0) + count
            
            # 合并边类型统计
            for edge_type, count in stats["edge_types"].items():
                total_stats["edge_types"][edge_type] = \
                    total_stats["edge_types"].get(edge_type, 0) + count
        
        # 保存统计报告
        report_file = self.output_dir / "alfworld_statistics.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(total_stats, f, indent=2, ensure_ascii=False)
        
        print(f"📊 统计报告已保存到: {report_file}")
        print("📈 ALFWorld数据统计:")
        for key, value in total_stats.items():
            print(f"  {key}: {value}")


def main():
    """主函数"""
    # 设置路径
    alfworld_data_dir = "data/benchmarks/alfworld"
    output_dir = "data/knowledge_graphs/alfworld"
    
    # 创建预处理器
    preprocessor = ALFWorldPreprocessor(alfworld_data_dir, output_dir)
    
    # 处理数据
    preprocessor.process_alfworld_data()


if __name__ == "__main__":
    main()
