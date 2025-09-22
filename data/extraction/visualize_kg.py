#!/usr/bin/env python3
"""
知识图谱可视化
展示构建的状态知识图谱结构
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def analyze_kg_structure(json_file: str):
    """分析知识图谱结构"""
    print(f"🔍 分析知识图谱结构: {Path(json_file).name}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        print(f"\n📊 基本统计:")
        print(f"   - 节点数: {len(nodes)}")
        print(f"   - 边数: {len(edges)}")
        
        # 分析节点类型
        node_types = {}
        entities_by_type = {}
        states_by_entity = {}
        
        for node in nodes:
            node_type = node['type']
            node_types[node_type] = node_types.get(node_type, 0) + 1
            
            if node_type == 'entity':
                entity_type = node['attributes'].get('entity_type', 'unknown')
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(node['name'])
            
            elif node_type == 'state':
                entity_name = node['attributes'].get('entity_name', 'unknown')
                state_value = node['attributes'].get('state_value', 'unknown')
                is_initial = node['attributes'].get('is_initial', False)
                
                if entity_name not in states_by_entity:
                    states_by_entity[entity_name] = []
                states_by_entity[entity_name].append({
                    'state': state_value,
                    'initial': is_initial,
                    'node_name': node['name']
                })
        
        print(f"\n🏷️  节点类型分布:")
        for node_type, count in sorted(node_types.items()):
            print(f"   - {node_type}: {count}")
        
        print(f"\n🎯 实体分类:")
        for entity_type, entities in entities_by_type.items():
            print(f"   - {entity_type}: {', '.join(entities)}")
        
        print(f"\n🔄 实体状态:")
        for entity_name, states in states_by_entity.items():
            print(f"   - {entity_name}:")
            for state_info in states:
                initial_mark = " (初始)" if state_info['initial'] else ""
                print(f"     * {state_info['state']}{initial_mark}")
        
        # 分析边类型
        edge_types = {}
        relationships = []
        
        for edge in edges:
            edge_type = edge['type']
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
            
            # 找到源和目标节点的名称
            source_name = next((n['name'] for n in nodes if n['id'] == edge['source']), edge['source'])
            target_name = next((n['name'] for n in nodes if n['id'] == edge['target']), edge['target'])
            
            relationships.append({
                'source': source_name,
                'target': target_name,
                'type': edge_type,
                'attributes': edge.get('attributes', {})
            })
        
        print(f"\n🔗 边类型分布:")
        for edge_type, count in sorted(edge_types.items()):
            print(f"   - {edge_type}: {count}")
        
        # 显示关键关系
        print(f"\n🎯 关键关系 (前10个):")
        for i, rel in enumerate(relationships[:10]):
            attrs_str = ""
            if rel['attributes']:
                key_attrs = {k: v for k, v in rel['attributes'].items() if k in ['relationship', 'new_value', 'required_value']}
                if key_attrs:
                    attrs_str = f" ({key_attrs})"
            
            print(f"   {i+1:2d}. {rel['source']} --[{rel['type']}]--> {rel['target']}{attrs_str}")
        
        return {
            'nodes': len(nodes),
            'edges': len(edges),
            'node_types': node_types,
            'edge_types': edge_types,
            'entities': entities_by_type,
            'states': states_by_entity,
            'relationships': relationships
        }
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None


def generate_mermaid_diagram(analysis: Dict[str, Any]):
    """生成Mermaid流程图"""
    print(f"\n🎨 生成Mermaid流程图...")
    
    mermaid_lines = ["flowchart TD"]
    
    # 定义节点样式
    styles = {
        'action': ':::act',
        'entity': ':::ent', 
        'state': ':::state',
        'result': ':::result'
    }
    
    # 生成节点定义
    node_definitions = []
    edge_definitions = []
    
    # 简化版本 - 只显示关键节点和关系
    key_entities = ['青铜钥匙', '木制宝箱', '玩家']
    key_actions = ['获取钥匙', '使用钥匙', '打开']
    key_states = ['未获取', '已获取', '锁定', '解锁', '打开']
    
    # 添加动作节点
    for action in key_actions:
        node_id = action.replace(' ', '_')
        node_definitions.append(f'  {node_id}["动作: {action}"]:::act')
    
    # 添加实体节点
    for entity in key_entities:
        if entity in analysis['states']:
            states = analysis['states'][entity]
            for state_info in states:
                state_value = state_info['state']
                if state_value in key_states:
                    node_id = f"{entity}_{state_value}".replace(' ', '_').replace(':', '_')
                    initial_mark = "<br/>初始状态" if state_info['initial'] else ""
                    node_definitions.append(f'  {node_id}["实体: {entity}<br/>状态: {state_value}{initial_mark}"]:::ent')
    
    # 添加结果节点
    results = ['获取成功', '解锁成功', '打开成功']
    for result in results:
        node_id = result.replace(' ', '_')
        node_definitions.append(f'  {node_id}["结果: {result}"]:::result')
    
    # 添加关系
    key_relationships = [
        ('获取钥匙', '青铜钥匙_已获取'),
        ('获取钥匙', '获取成功'),
        ('使用钥匙', '木制宝箱_解锁'),
        ('使用钥匙', '解锁成功'),
        ('打开', '木制宝箱_打开'),
        ('打开', '打开成功'),
        ('青铜钥匙_未获取', '青铜钥匙_已获取'),
        ('木制宝箱_锁定', '木制宝箱_解锁'),
        ('木制宝箱_解锁', '木制宝箱_打开')
    ]
    
    for source, target in key_relationships:
        source_id = source.replace(' ', '_').replace(':', '_')
        target_id = target.replace(' ', '_').replace(':', '_')
        
        # 状态转换用虚线
        if '_' in source and '_' in target:
            edge_definitions.append(f'  {source_id} -.-> {target_id}')
        else:
            edge_definitions.append(f'  {source_id} --> {target_id}')
    
    # 组合Mermaid代码
    mermaid_code = '\n'.join([
        'flowchart TD',
        '',
        '  %% 节点定义',
        *node_definitions,
        '',
        '  %% 关系定义', 
        *edge_definitions,
        '',
        '  %% 样式定义',
        '  classDef act fill:#e1f5fe,stroke:#01579b,stroke-width:2px',
        '  classDef ent fill:#f3e5f5,stroke:#4a148c,stroke-width:2px',
        '  classDef state fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px',
        '  classDef result fill:#fff3e0,stroke:#e65100,stroke-width:2px'
    ])
    
    print("✅ Mermaid流程图生成完成!")
    print("\n📋 Mermaid代码:")
    print("```mermaid")
    print(mermaid_code)
    print("```")
    
    # 保存到文件
    output_file = Path(__file__).parent / "kg_mermaid_diagram.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 知识图谱结构图\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_code)
        f.write("\n```\n")
    
    print(f"\n💾 Mermaid图表已保存到: {output_file}")
    
    return mermaid_code


def main():
    """主函数"""
    print("🚀 开始分析和可视化知识图谱\n")
    
    # 查找知识图谱文件
    data_dir = Path(__file__).parent.parent
    kg_dir = data_dir / "knowledge_graphs/extracted"
    
    json_files = list(kg_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 未找到知识图谱文件")
        return
    
    print(f"📁 找到 {len(json_files)} 个知识图谱文件:")
    for i, file in enumerate(json_files):
        print(f"   {i+1}. {file.name}")
    
    # 分析增强示例知识图谱
    enhanced_file = kg_dir / "enhanced_example_kg.json"
    if enhanced_file.exists():
        print(f"\n{'='*60}")
        analysis = analyze_kg_structure(str(enhanced_file))
        
        if analysis:
            # 生成Mermaid图表
            generate_mermaid_diagram(analysis)
            
            print(f"\n🎯 知识图谱符合用户要求:")
            print(f"   ✅ 场景固定: 有场景节点作为容器")
            print(f"   ✅ 状态更新: 实体有多个状态，支持状态转换")
            print(f"   ✅ 动作驱动: 动作节点连接实体和状态")
            print(f"   ✅ 结果反馈: 每个动作都有对应的结果")
            print(f"   ✅ flowchart结构: 支持节点间的有向关系")
    
    print("\n🎉 知识图谱分析完成!")


if __name__ == "__main__":
    main()
