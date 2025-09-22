#!/usr/bin/env python3
"""
按场景分割的知识图谱构建器
为每个场景创建独立的知识图谱文件
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from state_kg_builder import StateKGBuilder, GameEntity, GameAction, StateTransition


def build_separated_alfworld_kgs(max_scenes: int = 10) -> Dict[str, Any]:
    """构建按场景分割的ALFWorld知识图谱"""
    print(f"🏗️ 构建按场景分割的ALFWorld知识图谱 (最多 {max_scenes} 个场景)...")
    
    data_dir = Path(__file__).parent.parent
    alfworld_dir = data_dir / "benchmarks/alfworld/alfworld/alfworld/gen/layouts"
    
    if not alfworld_dir.exists():
        print("❌ ALFWorld目录不存在")
        return {}
    
    # 获取布局文件
    json_files = list(alfworld_dir.glob("*-openable.json"))  # 优先处理可打开的场景
    if not json_files:
        json_files = list(alfworld_dir.glob("*.json"))
    
    json_files = json_files[:max_scenes]
    print(f"📁 找到 {len(json_files)} 个场景文件")
    
    # 创建输出目录
    output_dir = data_dir / "knowledge_graphs/scenes"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scene_results = {}
    processed_scenes = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                scene_data = json.load(f)
            
            # 跳过格式不正确的文件
            if not isinstance(scene_data, dict):
                continue
            
            scene_name = json_file.stem
            print(f"   处理场景: {scene_name}")
            
            # 为每个场景创建独立的知识图谱构建器
            kg_builder = StateKGBuilder()
            
            # 创建场景知识图谱
            result = kg_builder.create_alfworld_scene_kg(scene_data, scene_name)
            
            # 导出单个场景的知识图谱
            scene_json_file = output_dir / f"{scene_name}_kg.json"
            scene_graphml_file = output_dir / f"{scene_name}_kg.graphml"
            
            builder = kg_builder.get_builder()
            builder.export_to_json(str(scene_json_file))
            builder.export_to_graphml(str(scene_graphml_file))
            
            # 获取统计信息
            stats = builder.get_statistics()
            
            scene_results[scene_name] = {
                'file_path': str(scene_json_file),
                'entities': result['entities'],
                'actions': result['actions'],
                'transitions': result['transitions'],
                'total_nodes': stats['total_nodes'],
                'total_edges': stats['total_edges'],
                'node_types': stats['node_types'],
                'edge_types': stats['edge_types']
            }
            
            print(f"     ✅ 节点: {stats['total_nodes']}, 边: {stats['total_edges']}")
            print(f"     💾 保存到: {scene_json_file.name}")
            
            processed_scenes += 1
            
        except Exception as e:
            print(f"     ❌ 处理 {json_file.name} 失败: {e}")
            continue
    
    print(f"✅ 成功处理 {processed_scenes} 个场景")
    print(f"📁 场景文件保存在: {output_dir}")
    
    # 保存场景汇总信息
    summary_file = output_dir / "scenes_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_scenes': processed_scenes,
            'output_directory': str(output_dir),
            'scenes': scene_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📊 场景汇总保存到: {summary_file}")
    
    return scene_results


def create_scene_index():
    """创建场景索引文件"""
    print("📋 创建场景索引...")
    
    data_dir = Path(__file__).parent.parent
    scenes_dir = data_dir / "knowledge_graphs/scenes"
    
    if not scenes_dir.exists():
        print("❌ 场景目录不存在")
        return
    
    # 查找所有场景文件
    scene_files = list(scenes_dir.glob("*_kg.json"))
    
    index_data = {
        'total_scenes': len(scene_files),
        'created_at': str(Path(__file__).stat().st_mtime),
        'scenes': []
    }
    
    for scene_file in scene_files:
        scene_name = scene_file.stem.replace('_kg', '')
        
        try:
            with open(scene_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            
            # 分析场景内容
            entities = [n for n in nodes if n['type'] == 'entity' and n['attributes'].get('entity_type') != 'scene']
            actions = [n for n in nodes if n['type'] == 'action']
            states = [n for n in nodes if n['type'] == 'state']
            
            scene_info = {
                'name': scene_name,
                'file': scene_file.name,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'entities': len(entities),
                    'actions': len(actions),
                    'states': len(states)
                },
                'entity_types': list(set(e['attributes'].get('entity_type', 'unknown') for e in entities))
            }
            
            index_data['scenes'].append(scene_info)
            
        except Exception as e:
            print(f"   ⚠️  分析 {scene_file.name} 失败: {e}")
    
    # 按场景名排序
    index_data['scenes'].sort(key=lambda x: x['name'])
    
    # 保存索引
    index_file = scenes_dir / "scene_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 场景索引保存到: {index_file}")
    
    # 显示统计信息
    print(f"\n📊 场景统计:")
    print(f"   - 总场景数: {index_data['total_scenes']}")
    
    if index_data['scenes']:
        total_nodes = sum(s['stats']['total_nodes'] for s in index_data['scenes'])
        total_edges = sum(s['stats']['total_edges'] for s in index_data['scenes'])
        total_entities = sum(s['stats']['entities'] for s in index_data['scenes'])
        
        print(f"   - 总节点数: {total_nodes}")
        print(f"   - 总边数: {total_edges}")
        print(f"   - 总实体数: {total_entities}")
        
        # 显示前5个场景
        print(f"\n🎯 场景示例 (前5个):")
        for i, scene in enumerate(index_data['scenes'][:5]):
            print(f"   {i+1}. {scene['name']}: {scene['stats']['entities']} 实体, {scene['stats']['actions']} 动作")
    
    return index_data


def main():
    """主函数"""
    print("🚀 开始构建按场景分割的知识图谱\n")
    
    # 构建分割的知识图谱
    scene_results = build_separated_alfworld_kgs(max_scenes=10)
    
    if scene_results:
        # 创建场景索引
        index_data = create_scene_index()
        
        print(f"\n🎉 按场景分割的知识图谱构建完成!")
        print(f"   - 处理场景数: {len(scene_results)}")
        print(f"   - 输出目录: data/knowledge_graphs/scenes/")
        print(f"   - 索引文件: scene_index.json")
        
        print(f"\n📁 文件结构:")
        print(f"   data/knowledge_graphs/")
        print(f"   ├── scenes/")
        print(f"   │   ├── scene_index.json          # 场景索引")
        print(f"   │   ├── scenes_summary.json       # 场景汇总")
        print(f"   │   ├── FloorPlan228-openable_kg.json")
        print(f"   │   ├── FloorPlan228-openable_kg.graphml")
        print(f"   │   └── ... (其他场景文件)")
        print(f"   └── extracted/")
        print(f"       └── ... (合并的知识图谱文件)")
    
    else:
        print("❌ 未能构建任何场景知识图谱")


if __name__ == "__main__":
    main()
