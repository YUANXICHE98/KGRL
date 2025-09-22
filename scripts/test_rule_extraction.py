#!/usr/bin/env python3
"""
测试规则抽取功能
验证从ALFWorld和PDDL数据中抽取知识图谱的效果
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder


def test_alfworld_extraction():
    """测试ALFWorld JSON数据抽取"""
    print("🧪 测试ALFWorld数据抽取...")
    
    # 查找ALFWorld JSON文件
    alfworld_dir = project_root / "data/benchmarks/alfworld/alfworld/alfworld/gen/layouts"
    json_files = list(alfworld_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 未找到ALFWorld JSON文件")
        return None
    
    # 使用第一个JSON文件进行测试
    json_file = json_files[0]
    print(f"📁 使用文件: {json_file.name}")
    
    try:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        
        # 创建知识图谱构建器
        builder = DODAFKGBuilder()
        
        # 抽取知识图谱
        scene_name = json_file.stem  # 使用文件名作为场景名
        result = builder.extract_from_alfworld_json(json_data, scene_name)
        
        print("✅ ALFWorld抽取成功!")
        print(f"   - 抽取节点数: {result['nodes_extracted']}")
        print(f"   - 抽取边数: {result['edges_extracted']}")
        print(f"   - 处理对象数: {result['objects_processed']}")
        print(f"   - 场景名称: {result['scene_name']}")
        
        # 获取统计信息
        stats = builder.get_statistics()
        print("\n📊 知识图谱统计:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        return builder
        
    except Exception as e:
        print(f"❌ ALFWorld抽取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_pddl_extraction():
    """测试PDDL数据抽取"""
    print("\n🧪 测试PDDL数据抽取...")
    
    # 查找PDDL文件
    pddl_dir = project_root / "data/benchmarks/alfworld/alfworld/alfworld/gen/ff_planner/samples"
    pddl_files = list(pddl_dir.glob("problem_*.pddl"))
    
    if not pddl_files:
        print("❌ 未找到PDDL文件")
        return None
    
    # 使用第一个PDDL文件进行测试
    pddl_file = pddl_files[0]
    print(f"📁 使用文件: {pddl_file.name}")
    
    try:
        with open(pddl_file, 'r') as f:
            pddl_content = f.read()
        
        # 创建知识图谱构建器
        builder = DODAFKGBuilder()
        
        # 抽取知识图谱
        problem_name = pddl_file.stem
        result = builder.extract_from_pddl_problem(pddl_content, problem_name)
        
        print("✅ PDDL抽取成功!")
        print(f"   - 抽取节点数: {result['nodes_extracted']}")
        print(f"   - 抽取边数: {result['edges_extracted']}")
        print(f"   - 问题名称: {result['problem_name']}")
        
        # 获取统计信息
        stats = builder.get_statistics()
        print("\n📊 知识图谱统计:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        return builder
        
    except Exception as e:
        print(f"❌ PDDL抽取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_combined_extraction():
    """测试组合抽取"""
    print("\n🧪 测试组合抽取（ALFWorld + PDDL）...")
    
    # 创建统一的知识图谱构建器
    builder = DODAFKGBuilder()
    
    # 1. 抽取ALFWorld数据
    alfworld_dir = project_root / "data/benchmarks/alfworld/alfworld/alfworld/gen/layouts"
    json_files = list(alfworld_dir.glob("*.json"))
    
    if json_files:
        json_file = json_files[0]
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            
            scene_name = json_file.stem
            alfworld_result = builder.extract_from_alfworld_json(json_data, scene_name)
            print(f"✅ ALFWorld数据已添加: {alfworld_result['nodes_extracted']} 节点")
            
        except Exception as e:
            print(f"⚠️  ALFWorld抽取失败: {e}")
    
    # 2. 抽取PDDL数据
    pddl_dir = project_root / "data/benchmarks/alfworld/alfworld/alfworld/gen/ff_planner/samples"
    pddl_files = list(pddl_dir.glob("problem_*.pddl"))
    
    if pddl_files:
        pddl_file = pddl_files[0]
        try:
            with open(pddl_file, 'r') as f:
                pddl_content = f.read()
            
            problem_name = pddl_file.stem
            pddl_result = builder.extract_from_pddl_problem(pddl_content, problem_name)
            print(f"✅ PDDL数据已添加: {pddl_result['nodes_extracted']} 节点")
            
        except Exception as e:
            print(f"⚠️  PDDL抽取失败: {e}")
    
    # 获取最终统计信息
    stats = builder.get_statistics()
    print("\n📊 组合知识图谱统计:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    # 导出知识图谱
    output_dir = project_root / "data/knowledge_graphs/extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        builder.export_to_json(str(output_dir / "combined_kg.json"))
        builder.export_to_graphml(str(output_dir / "combined_kg.graphml"))
        print(f"\n💾 知识图谱已导出到: {output_dir}")
        
        # 显示一些示例节点
        print("\n🔍 示例节点:")
        for i, (node_id, node) in enumerate(list(builder.nodes.items())[:5]):
            print(f"   {i+1}. {node.name} ({node.type.value})")
            
    except Exception as e:
        print(f"⚠️  导出失败: {e}")
    
    return builder


def main():
    """主函数"""
    print("🚀 开始测试规则抽取功能\n")
    
    # 测试单独的ALFWorld抽取
    alfworld_builder = test_alfworld_extraction()
    
    # 测试单独的PDDL抽取
    pddl_builder = test_pddl_extraction()
    
    # 测试组合抽取
    combined_builder = test_combined_extraction()
    
    print("\n🎉 测试完成!")
    
    if combined_builder:
        stats = combined_builder.get_statistics()
        print(f"\n📈 最终结果: {stats['total_nodes']} 节点, {stats['total_edges']} 边")
        print("   节点类型分布:", stats['node_types'])
        print("   边类型分布:", stats['edge_types'])


if __name__ == "__main__":
    main()
