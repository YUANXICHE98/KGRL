#!/usr/bin/env python3
"""
基础抽取测试
验证DODAF知识图谱构建器的基本功能
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder, EdgeType, NodeType


def test_basic_kg_construction():
    """测试基本知识图谱构建功能"""
    print("🧪 测试基本知识图谱构建...")
    
    builder = DODAFKGBuilder()
    
    # 创建一个简单的"打开宝箱"场景
    print("   创建'打开宝箱'场景...")
    
    # 1. 创建实体节点
    key_id = builder.add_entity_node("bronze_key", "key", {
        'material': 'bronze',
        'description': '一把青铜钥匙'
    })
    
    chest_id = builder.add_entity_node("wooden_chest", "chest", {
        'material': 'wood',
        'description': '一个木制宝箱'
    })
    
    player_id = builder.add_entity_node("player", "agent", {
        'description': '玩家角色'
    })
    
    # 2. 创建状态节点
    key_available_id = builder.add_state_node("key_available", "true", {
        'description': '钥匙可获取'
    })
    
    chest_locked_id = builder.add_state_node("chest_locked", "true", {
        'description': '宝箱被锁定'
    })
    
    chest_opened_id = builder.add_state_node("chest_opened", "false", {
        'description': '宝箱已打开'
    })
    
    # 3. 创建动作节点
    take_key_id = builder.add_action_node("take_key", {
        'description': '拿取钥匙'
    })
    
    open_chest_id = builder.add_action_node("open_chest", {
        'description': '打开宝箱'
    })
    
    # 4. 创建关系
    # 钥匙的状态
    builder.add_edge(key_id, key_available_id, EdgeType.HAS_STATE, {
        'description': '钥匙具有可获取状态'
    })
    
    # 宝箱的状态
    builder.add_edge(chest_id, chest_locked_id, EdgeType.HAS_STATE, {
        'description': '宝箱具有锁定状态'
    })
    
    builder.add_edge(chest_id, chest_opened_id, EdgeType.HAS_STATE, {
        'description': '宝箱具有打开状态'
    })
    
    # 动作需求
    builder.add_edge(take_key_id, key_available_id, EdgeType.REQUIRES, {
        'description': '拿取钥匙需要钥匙可获取'
    })
    
    builder.add_edge(open_chest_id, key_id, EdgeType.REQUIRES, {
        'description': '打开宝箱需要钥匙'
    })
    
    # 动作效果
    builder.add_edge(take_key_id, key_available_id, EdgeType.MODIFIES, {
        'description': '拿取钥匙改变钥匙状态',
        'new_value': 'false'
    })
    
    builder.add_edge(open_chest_id, chest_opened_id, EdgeType.MODIFIES, {
        'description': '打开宝箱改变宝箱状态',
        'new_value': 'true'
    })
    
    # 获取统计信息
    stats = builder.get_statistics()
    print("✅ 基本知识图谱构建成功!")
    print(f"   - 节点数: {stats['total_nodes']}")
    print(f"   - 边数: {stats['total_edges']}")
    print(f"   - 节点类型: {stats['node_types']}")
    print(f"   - 边类型: {stats['edge_types']}")
    
    return builder


def test_alfworld_single_file():
    """测试单个ALFWorld文件抽取"""
    print("\n🧪 测试单个ALFWorld文件抽取...")
    
    data_dir = Path(__file__).parent.parent
    layout_dir = data_dir / "benchmarks/alfworld/alfworld/alfworld/gen/layouts"
    
    if not layout_dir.exists():
        print("❌ ALFWorld布局目录不存在")
        return None
    
    json_files = list(layout_dir.glob("*.json"))
    if not json_files:
        print("❌ 未找到JSON文件")
        return None
    
    # 使用第一个文件
    json_file = json_files[0]
    print(f"   使用文件: {json_file.name}")
    
    try:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        
        print(f"   - 原始数据对象数: {len(json_data)}")
        
        # 显示数据结构
        print("   - 数据示例:")
        for i, (key, value) in enumerate(list(json_data.items())[:3]):
            print(f"     {i+1}. {key} -> {value}")
        
        # 创建知识图谱构建器
        builder = DODAFKGBuilder()
        
        # 手动抽取数据
        scene_name = json_file.stem
        scene_id = builder.add_entity_node(scene_name, "scene", {
            'description': f'ALFWorld场景: {scene_name}',
            'source': 'alfworld'
        })
        
        extracted_objects = 0
        for object_key, position_data in json_data.items():
            parts = object_key.split('|')
            if len(parts) >= 4:
                object_type = parts[0]
                x_pos, y_pos, z_pos = parts[1], parts[2], parts[3]
                
                # 创建对象节点
                obj_id = builder.add_entity_node(f"{object_type}_{extracted_objects}", object_type, {
                    'position_x': float(x_pos),
                    'position_y': float(y_pos),
                    'position_z': float(z_pos),
                    'layout_data': str(position_data),
                    'source': 'alfworld'
                })
                
                # 与场景建立关系
                builder.add_edge(scene_id, obj_id, EdgeType.CONTAINS, {
                    'relationship': 'scene_contains_object'
                })
                
                # 创建对象状态
                state_id = builder.add_state_node(f"{object_type}_{extracted_objects}_available", "true", {
                    'description': f'{object_type} 可访问'
                })
                
                builder.add_edge(obj_id, state_id, EdgeType.HAS_STATE, {
                    'state_type': 'availability'
                })
                
                extracted_objects += 1
        
        stats = builder.get_statistics()
        print("✅ ALFWorld文件抽取成功!")
        print(f"   - 抽取对象数: {extracted_objects}")
        print(f"   - 总节点数: {stats['total_nodes']}")
        print(f"   - 总边数: {stats['total_edges']}")
        print(f"   - 节点类型: {stats['node_types']}")
        print(f"   - 边类型: {stats['edge_types']}")
        
        return builder
        
    except Exception as e:
        print(f"❌ 抽取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_export_functionality():
    """测试导出功能"""
    print("\n🧪 测试导出功能...")
    
    # 创建一个简单的知识图谱
    builder = DODAFKGBuilder()
    
    # 添加一些测试数据
    obj1 = builder.add_entity_node("test_object", "object", {'test': 'value'})
    state1 = builder.add_state_node("test_state", "active", {'test': 'state'})
    builder.add_edge(obj1, state1, EdgeType.HAS_STATE, {'test': 'edge'})
    
    # 测试导出
    output_dir = Path(__file__).parent.parent / "knowledge_graphs/extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 导出JSON
        json_file = output_dir / "test_kg.json"
        builder.export_to_json(str(json_file))
        print(f"✅ JSON导出成功: {json_file}")
        
        # 验证JSON文件
        with open(json_file, 'r') as f:
            data = json.load(f)
        print(f"   - JSON节点数: {len(data['nodes'])}")
        print(f"   - JSON边数: {len(data['edges'])}")
        
        # 导出GraphML
        graphml_file = output_dir / "test_kg.graphml"
        builder.export_to_graphml(str(graphml_file))
        print(f"✅ GraphML导出成功: {graphml_file}")
        
        # 检查文件大小
        json_size = json_file.stat().st_size
        graphml_size = graphml_file.stat().st_size
        print(f"   - JSON文件大小: {json_size} bytes")
        print(f"   - GraphML文件大小: {graphml_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 开始基础抽取测试\n")
    
    # 测试基本知识图谱构建
    basic_builder = test_basic_kg_construction()
    
    # 测试ALFWorld单文件抽取
    alfworld_builder = test_alfworld_single_file()
    
    # 测试导出功能
    export_success = test_export_functionality()
    
    print("\n📊 测试总结:")
    print(f"   - 基本构建: {'✅' if basic_builder else '❌'}")
    print(f"   - ALFWorld抽取: {'✅' if alfworld_builder else '❌'}")
    print(f"   - 导出功能: {'✅' if export_success else '❌'}")
    
    if basic_builder:
        stats = basic_builder.get_statistics()
        print(f"\n🎯 基本场景统计: {stats['total_nodes']} 节点, {stats['total_edges']} 边")
    
    if alfworld_builder:
        stats = alfworld_builder.get_statistics()
        print(f"🎯 ALFWorld场景统计: {stats['total_nodes']} 节点, {stats['total_edges']} 边")
    
    print("\n🎉 基础测试完成!")


if __name__ == "__main__":
    main()
