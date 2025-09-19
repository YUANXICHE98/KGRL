"""
TextWorld数据预处理脚本

从TextWorld游戏中提取状态信息，构建DODAF知识图谱
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re
import textworld

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder, NodeType, EdgeType


class TextWorldPreprocessor:
    """TextWorld数据预处理器"""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 动作映射
        self.action_mapping = {
            "go": "移动",
            "take": "拿取",
            "drop": "放下",
            "put": "放置",
            "open": "打开",
            "close": "关闭",
            "lock": "锁定",
            "unlock": "解锁",
            "eat": "吃",
            "cook": "烹饪",
            "examine": "检查",
            "look": "观察"
        }
    
    def extract_game_info(self, game_file: str) -> Dict[str, Any]:
        """从游戏文件中提取信息"""
        try:
            # 加载TextWorld游戏
            env = textworld.start(game_file)
            game_state = env.reset()
            
            # 提取初始状态信息
            game_info = {
                "description": game_state.description,
                "inventory": game_state.inventory,
                "score": game_state.score,
                "max_score": game_state.max_score,
                "won": game_state.won,
                "lost": game_state.lost
            }
            
            # 尝试获取游戏的内部结构
            if hasattr(env, 'game'):
                game = env.game
                game_info.update({
                    "rooms": self._extract_rooms(game),
                    "objects": self._extract_objects(game),
                    "rules": self._extract_rules(game)
                })
            
            env.close()
            return game_info
            
        except Exception as e:
            print(f"⚠️  加载游戏文件 {game_file} 时出错: {e}")
            return {}
    
    def _extract_rooms(self, game) -> List[Dict[str, Any]]:
        """提取房间信息"""
        rooms = []
        
        if hasattr(game, 'world') and hasattr(game.world, 'rooms'):
            for room in game.world.rooms:
                room_info = {
                    "id": room.id,
                    "name": getattr(room, 'name', 'Unknown Room'),
                    "description": getattr(room, 'description', ''),
                    "exits": []
                }
                
                # 提取出口信息
                if hasattr(room, 'exits'):
                    for direction, connected_room in room.exits.items():
                        room_info["exits"].append({
                            "direction": direction,
                            "target": connected_room.id if connected_room else None
                        })
                
                rooms.append(room_info)
        
        return rooms
    
    def _extract_objects(self, game) -> List[Dict[str, Any]]:
        """提取物品信息"""
        objects = []
        
        if hasattr(game, 'world') and hasattr(game.world, 'objects'):
            for obj in game.world.objects:
                obj_info = {
                    "id": obj.id,
                    "name": getattr(obj, 'name', 'Unknown Object'),
                    "type": obj.__class__.__name__,
                    "properties": {}
                }
                
                # 提取属性
                for attr in ['portable', 'openable', 'open', 'locked', 'edible']:
                    if hasattr(obj, attr):
                        obj_info["properties"][attr] = getattr(obj, attr)
                
                objects.append(obj_info)
        
        return objects
    
    def _extract_rules(self, game) -> List[Dict[str, Any]]:
        """提取规则信息"""
        rules = []
        
        if hasattr(game, 'rules'):
            for rule in game.rules:
                rule_info = {
                    "name": getattr(rule, 'name', 'Unknown Rule'),
                    "conditions": str(getattr(rule, 'preconditions', [])),
                    "effects": str(getattr(rule, 'postconditions', []))
                }
                rules.append(rule_info)
        
        return rules
    
    def build_kg_from_game_info(self, game_info: Dict[str, Any], game_name: str) -> DODAFKGBuilder:
        """从游戏信息构建知识图谱"""
        kg_builder = DODAFKGBuilder()
        
        # 添加房间节点
        room_nodes = {}
        if "rooms" in game_info:
            for room in game_info["rooms"]:
                room_id = kg_builder.add_entity_node(
                    room["name"], 
                    "房间",
                    {"description": room["description"], "game_id": room["id"]}
                )
                room_nodes[room["id"]] = room_id
                
                # 为房间添加状态
                state_id = kg_builder.add_state_node(
                    f"{room['name']}_状态", 
                    "可访问"
                )
                kg_builder.add_edge(room_id, state_id, EdgeType.REQUIRES)
        
        # 添加物品节点
        object_nodes = {}
        if "objects" in game_info:
            for obj in game_info["objects"]:
                obj_id = kg_builder.add_entity_node(
                    obj["name"],
                    "物品",
                    {"type": obj["type"], "properties": obj["properties"]}
                )
                object_nodes[obj["id"]] = obj_id
                
                # 根据属性添加状态
                for prop, value in obj["properties"].items():
                    if isinstance(value, bool):
                        state_value = "是" if value else "否"
                        state_id = kg_builder.add_state_node(
                            f"{obj['name']}_{prop}",
                            state_value
                        )
                        kg_builder.add_edge(obj_id, state_id, EdgeType.REQUIRES)
        
        # 添加规则节点
        if "rules" in game_info:
            for rule in game_info["rules"]:
                rule_id = kg_builder.add_rule_node(
                    rule["name"],
                    "游戏规则",
                    [rule["conditions"]],
                    [rule["effects"]]
                )
        
        # 添加房间连接关系
        if "rooms" in game_info:
            for room in game_info["rooms"]:
                if room["id"] in room_nodes:
                    source_id = room_nodes[room["id"]]
                    
                    for exit_info in room["exits"]:
                        if exit_info["target"] and exit_info["target"] in room_nodes:
                            target_id = room_nodes[exit_info["target"]]
                            
                            # 创建移动动作
                            move_action_id = kg_builder.add_action_node(
                                f"移动_{exit_info['direction']}",
                                {"direction": exit_info["direction"]}
                            )
                            
                            kg_builder.add_edge(source_id, move_action_id, EdgeType.ENABLES)
                            kg_builder.add_edge(move_action_id, target_id, EdgeType.PRODUCES)
        
        return kg_builder
    
    def process_textworld_games(self) -> None:
        """处理TextWorld游戏文件"""
        print("🚀 开始处理TextWorld游戏...")
        
        # 查找游戏文件
        game_files = list(self.data_dir.rglob("*.ulx")) + list(self.data_dir.rglob("*.z8"))
        
        if not game_files:
            print("❌ 未找到TextWorld游戏文件")
            return
        
        print(f"🎮 找到 {len(game_files)} 个游戏文件")
        
        all_kgs = []
        
        for i, game_file in enumerate(game_files[:10]):  # 处理前10个游戏
            print(f"🎯 处理游戏 {i+1}/{min(10, len(game_files))}: {game_file.name}")
            
            try:
                # 提取游戏信息
                game_info = self.extract_game_info(str(game_file))
                
                if game_info:
                    # 构建知识图谱
                    kg = self.build_kg_from_game_info(game_info, game_file.stem)
                    
                    # 保存知识图谱
                    output_file = self.output_dir / f"textworld_kg_{game_file.stem}.json"
                    kg.export_to_json(str(output_file))
                    all_kgs.append(kg)
                    
                    # 保存游戏信息
                    info_file = self.output_dir / f"textworld_info_{game_file.stem}.json"
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump(game_info, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                print(f"⚠️  处理游戏 {game_file} 时出错: {e}")
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
        report_file = self.output_dir / "textworld_statistics.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(total_stats, f, indent=2, ensure_ascii=False)
        
        print(f"📊 统计报告已保存到: {report_file}")
        print("📈 TextWorld数据统计:")
        for key, value in total_stats.items():
            print(f"  {key}: {value}")


def main():
    """主函数"""
    # 设置路径
    textworld_data_dir = "data/benchmarks/textworld"
    output_dir = "data/knowledge_graphs/textworld"
    
    # 创建预处理器
    preprocessor = TextWorldPreprocessor(textworld_data_dir, output_dir)
    
    # 处理数据
    preprocessor.process_textworld_games()


if __name__ == "__main__":
    main()
