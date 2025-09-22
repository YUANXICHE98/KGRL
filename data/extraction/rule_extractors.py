#!/usr/bin/env python3
"""
规则抽取器
从ALFWorld和TextWorld benchmark数据中抽取知识图谱
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder, EdgeType, NodeType


class ALFWorldExtractor:
    """ALFWorld数据抽取器"""
    
    def __init__(self):
        self.builder = DODAFKGBuilder()
        
    def extract_from_layout_json(self, json_file: Path) -> Dict[str, Any]:
        """从ALFWorld布局JSON文件抽取知识图谱"""
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            scene_name = json_file.stem
            result = self.builder.extract_from_alfworld_json(json_data, scene_name)
            
            return {
                'success': True,
                'file': str(json_file),
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'file': str(json_file),
                'error': str(e)
            }
    
    def extract_from_pddl_problem(self, pddl_file: Path) -> Dict[str, Any]:
        """从PDDL问题文件抽取知识图谱"""
        try:
            with open(pddl_file, 'r') as f:
                pddl_content = f.read()
            
            problem_name = pddl_file.stem
            result = self.builder.extract_from_pddl_problem(pddl_content, problem_name)
            
            return {
                'success': True,
                'file': str(pddl_file),
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'file': str(pddl_file),
                'error': str(e)
            }
    
    def batch_extract_alfworld(self, alfworld_dir: Path) -> Dict[str, Any]:
        """批量抽取ALFWorld数据"""
        results = {
            'layouts': [],
            'pddl_problems': [],
            'total_nodes': 0,
            'total_edges': 0,
            'errors': []
        }
        
        # 抽取布局文件
        layout_dir = alfworld_dir / "alfworld/alfworld/gen/layouts"
        if layout_dir.exists():
            json_files = list(layout_dir.glob("*.json"))
            print(f"📁 找到 {len(json_files)} 个布局文件")
            
            for json_file in json_files[:5]:  # 限制处理前5个文件
                result = self.extract_from_layout_json(json_file)
                results['layouts'].append(result)
                
                if result['success']:
                    results['total_nodes'] += result['result']['nodes_extracted']
                    results['total_edges'] += result['result']['edges_extracted']
                else:
                    results['errors'].append(result)
        
        # 抽取PDDL问题文件
        pddl_dir = alfworld_dir / "alfworld/alfworld/gen/ff_planner/samples"
        if pddl_dir.exists():
            pddl_files = list(pddl_dir.glob("problem_*.pddl"))
            print(f"📁 找到 {len(pddl_files)} 个PDDL问题文件")
            
            for pddl_file in pddl_files[:3]:  # 限制处理前3个文件
                result = self.extract_from_pddl_problem(pddl_file)
                results['pddl_problems'].append(result)
                
                if result['success']:
                    results['total_nodes'] += result['result']['nodes_extracted']
                    results['total_edges'] += result['result']['edges_extracted']
                else:
                    results['errors'].append(result)
        
        return results


class TextWorldExtractor:
    """TextWorld数据抽取器"""
    
    def __init__(self):
        self.builder = DODAFKGBuilder()
    
    def extract_from_textworld_game(self, game_data: Dict[str, Any], game_name: str = "textworld_game") -> Dict[str, Any]:
        """从TextWorld游戏数据抽取知识图谱"""
        try:
            extracted_nodes = 0
            extracted_edges = 0
            
            # 创建游戏节点
            game_id = self.builder.add_entity_node(game_name, "game", {
                'category': 'textworld_game',
                'description': f'TextWorld game: {game_name}',
                'source': 'textworld'
            })
            extracted_nodes += 1
            
            # 处理房间信息（如果存在）
            if 'rooms' in game_data:
                for room_name, room_info in game_data['rooms'].items():
                    room_id = self.builder.add_entity_node(room_name, "room", {
                        'category': 'location',
                        'description': room_info.get('description', ''),
                        'source': 'textworld'
                    })
                    extracted_nodes += 1
                    
                    # 与游戏建立关系
                    self.builder.add_edge(game_id, room_id, EdgeType.CONTAINS, {
                        'relationship': 'game_contains_room'
                    })
                    extracted_edges += 1
            
            # 处理物品信息（如果存在）
            if 'objects' in game_data:
                for obj_name, obj_info in game_data['objects'].items():
                    obj_id = self.builder.add_entity_node(obj_name, obj_info.get('type', 'object'), {
                        'category': 'game_object',
                        'description': obj_info.get('description', ''),
                        'properties': obj_info.get('properties', {}),
                        'source': 'textworld'
                    })
                    extracted_nodes += 1
                    
                    # 与游戏建立关系
                    self.builder.add_edge(game_id, obj_id, EdgeType.CONTAINS, {
                        'relationship': 'game_contains_object'
                    })
                    extracted_edges += 1
                    
                    # 创建物品状态
                    state_id = self.builder.add_state_node(f"{obj_name}_state", 
                                                         obj_info.get('state', 'available'), {
                        'state_type': 'object_state',
                        'object_name': obj_name
                    })
                    
                    self.builder.add_edge(obj_id, state_id, EdgeType.HAS_STATE, {
                        'state_category': 'object_state'
                    })
                    extracted_nodes += 1
                    extracted_edges += 1
            
            return {
                'success': True,
                'nodes_extracted': extracted_nodes,
                'edges_extracted': extracted_edges,
                'game_name': game_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'game_name': game_name
            }
    
    def create_sample_textworld_game(self) -> Dict[str, Any]:
        """创建示例TextWorld游戏数据用于测试"""
        return {
            'rooms': {
                'kitchen': {
                    'description': 'A modern kitchen with appliances',
                    'exits': ['living_room']
                },
                'living_room': {
                    'description': 'A cozy living room with furniture',
                    'exits': ['kitchen', 'bedroom']
                },
                'bedroom': {
                    'description': 'A quiet bedroom',
                    'exits': ['living_room']
                }
            },
            'objects': {
                'apple': {
                    'type': 'food',
                    'description': 'A red apple',
                    'state': 'fresh',
                    'location': 'kitchen',
                    'properties': {'edible': True, 'color': 'red'}
                },
                'key': {
                    'type': 'tool',
                    'description': 'A brass key',
                    'state': 'available',
                    'location': 'living_room',
                    'properties': {'material': 'brass', 'opens': 'chest'}
                },
                'chest': {
                    'type': 'container',
                    'description': 'A wooden chest',
                    'state': 'locked',
                    'location': 'bedroom',
                    'properties': {'material': 'wood', 'locked': True}
                }
            },
            'actions': [
                {'name': 'take', 'objects': ['apple', 'key']},
                {'name': 'open', 'objects': ['chest'], 'requires': ['key']},
                {'name': 'eat', 'objects': ['apple']}
            ]
        }


def main():
    """主函数 - 测试规则抽取功能"""
    print("🚀 开始测试规则抽取功能\n")
    
    # 设置路径
    data_dir = Path(__file__).parent.parent
    alfworld_dir = data_dir / "benchmarks/alfworld"
    textworld_dir = data_dir / "benchmarks/textworld"
    
    # 测试ALFWorld抽取
    print("🧪 测试ALFWorld数据抽取...")
    alfworld_extractor = ALFWorldExtractor()
    
    if alfworld_dir.exists():
        alfworld_results = alfworld_extractor.batch_extract_alfworld(alfworld_dir)
        
        print("✅ ALFWorld抽取完成!")
        print(f"   - 处理布局文件: {len(alfworld_results['layouts'])}")
        print(f"   - 处理PDDL文件: {len(alfworld_results['pddl_problems'])}")
        print(f"   - 总节点数: {alfworld_results['total_nodes']}")
        print(f"   - 总边数: {alfworld_results['total_edges']}")
        print(f"   - 错误数: {len(alfworld_results['errors'])}")
        
        # 显示统计信息
        stats = alfworld_extractor.builder.get_statistics()
        print("\n📊 ALFWorld知识图谱统计:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
    else:
        print("❌ ALFWorld目录不存在")
    
    # 测试TextWorld抽取
    print("\n🧪 测试TextWorld数据抽取...")
    textworld_extractor = TextWorldExtractor()
    
    # 使用示例数据测试
    sample_game = textworld_extractor.create_sample_textworld_game()
    textworld_result = textworld_extractor.extract_from_textworld_game(sample_game, "sample_game")
    
    if textworld_result['success']:
        print("✅ TextWorld抽取成功!")
        print(f"   - 抽取节点数: {textworld_result['nodes_extracted']}")
        print(f"   - 抽取边数: {textworld_result['edges_extracted']}")
        
        # 显示统计信息
        stats = textworld_extractor.builder.get_statistics()
        print("\n📊 TextWorld知识图谱统计:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
    else:
        print(f"❌ TextWorld抽取失败: {textworld_result['error']}")
    
    # 导出结果
    output_dir = data_dir / "knowledge_graphs/extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 导出ALFWorld知识图谱
        if alfworld_dir.exists():
            alfworld_extractor.builder.export_to_json(str(output_dir / "alfworld_kg.json"))
            alfworld_extractor.builder.export_to_graphml(str(output_dir / "alfworld_kg.graphml"))
        
        # 导出TextWorld知识图谱
        textworld_extractor.builder.export_to_json(str(output_dir / "textworld_kg.json"))
        textworld_extractor.builder.export_to_graphml(str(output_dir / "textworld_kg.graphml"))
        
        print(f"\n💾 知识图谱已导出到: {output_dir}")
        
    except Exception as e:
        print(f"⚠️  导出失败: {e}")
    
    print("\n🎉 测试完成!")


if __name__ == "__main__":
    main()
