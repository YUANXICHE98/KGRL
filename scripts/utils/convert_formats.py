#!/usr/bin/env python3
"""
格式转换工具 - 转换各种数据格式
"""

import json
import yaml
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

def json_to_yaml(input_file: Path, output_file: Path = None):
    """JSON转YAML"""
    print(f"🔄 转换 {input_file.name} (JSON → YAML)")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if output_file is None:
        output_file = input_file.with_suffix('.yaml')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    print(f"  ✅ 输出: {output_file}")
    return output_file

def yaml_to_json(input_file: Path, output_file: Path = None):
    """YAML转JSON"""
    print(f"🔄 转换 {input_file.name} (YAML → JSON)")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if output_file is None:
        output_file = input_file.with_suffix('.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 输出: {output_file}")
    return output_file

def results_to_csv(input_file: Path, output_file: Path = None):
    """实验结果JSON转CSV"""
    print(f"📊 转换实验结果 {input_file.name} (JSON → CSV)")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if output_file is None:
        output_file = input_file.with_suffix('.csv')
    
    # 提取实验结果数据
    if 'results' in data:
        results_data = []
        
        for agent_name, agent_results in data['results'].items():
            if 'episode_details' in agent_results:
                for episode in agent_results['episode_details']:
                    row = {
                        'agent': agent_name,
                        'episode': episode.get('episode', 0),
                        'scene': episode.get('scene', ''),
                        'total_reward': episode.get('total_reward', 0),
                        'steps': episode.get('steps', 0),
                        'success': episode.get('success', False)
                    }
                    results_data.append(row)
        
        df = pd.DataFrame(results_data)
        df.to_csv(output_file, index=False)
        
        print(f"  ✅ 输出: {output_file} ({len(results_data)} 行)")
    else:
        print(f"  ⚠️ 文件格式不支持转换")
    
    return output_file

def kg_to_graphml(input_file: Path, output_file: Path = None):
    """知识图谱JSON转GraphML"""
    print(f"🕸️ 转换知识图谱 {input_file.name} (JSON → GraphML)")
    
    try:
        import networkx as nx
    except ImportError:
        print("  ❌ 需要安装networkx: pip install networkx")
        return None
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if output_file is None:
        output_file = input_file.with_suffix('.graphml')
    
    # 创建NetworkX图
    G = nx.Graph()
    
    # 添加节点
    if 'nodes' in data:
        for node in data['nodes']:
            node_id = node.get('id', '')
            G.add_node(node_id, **{k: v for k, v in node.items() if k != 'id'})
    
    # 添加边
    if 'edges' in data:
        for edge in data['edges']:
            source = edge.get('source', '')
            target = edge.get('target', '')
            if source and target:
                G.add_edge(source, target, **{k: v for k, v in edge.items() 
                                            if k not in ['source', 'target']})
    
    # 保存为GraphML
    nx.write_graphml(G, output_file)
    
    print(f"  ✅ 输出: {output_file} ({G.number_of_nodes()} 节点, {G.number_of_edges()} 边)")
    return output_file

def batch_convert_directory(input_dir: Path, conversion_type: str):
    """批量转换目录中的文件"""
    print(f"📁 批量转换目录: {input_dir}")
    print(f"🔄 转换类型: {conversion_type}")
    
    conversion_map = {
        'json_to_yaml': (json_to_yaml, '*.json'),
        'yaml_to_json': (yaml_to_json, '*.yaml'),
        'results_to_csv': (results_to_csv, '*experiment*.json'),
        'kg_to_graphml': (kg_to_graphml, '*kg*.json')
    }
    
    if conversion_type not in conversion_map:
        print(f"  ❌ 不支持的转换类型: {conversion_type}")
        return []
    
    convert_func, pattern = conversion_map[conversion_type]
    
    input_files = list(input_dir.glob(pattern))
    converted_files = []
    
    for input_file in input_files:
        try:
            output_file = convert_func(input_file)
            if output_file:
                converted_files.append(output_file)
        except Exception as e:
            print(f"  ❌ 转换失败 {input_file.name}: {e}")
    
    print(f"  ✅ 成功转换 {len(converted_files)} 个文件")
    return converted_files

def create_conversion_report(converted_files: List[Path], output_dir: Path):
    """创建转换报告"""
    print(f"\n📋 创建转换报告...")
    
    report = {
        "conversion_time": __import__('datetime').datetime.now().isoformat(),
        "total_files": len(converted_files),
        "files": []
    }
    
    for file_path in converted_files:
        file_info = {
            "name": file_path.name,
            "size": file_path.stat().st_size,
            "path": str(file_path.relative_to(output_dir.parent))
        }
        report["files"].append(file_info)
    
    report_file = output_dir / "conversion_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 转换报告: {report_file}")
    return report_file

def main():
    """主转换函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="KGRL格式转换工具")
    parser.add_argument("--input", "-i", type=str, required=True,
                       help="输入文件或目录路径")
    parser.add_argument("--output", "-o", type=str,
                       help="输出文件路径（可选）")
    parser.add_argument("--type", "-t", type=str, required=True,
                       choices=['json_to_yaml', 'yaml_to_json', 'results_to_csv', 
                               'kg_to_graphml', 'batch'],
                       help="转换类型")
    parser.add_argument("--batch-type", type=str,
                       choices=['json_to_yaml', 'yaml_to_json', 'results_to_csv', 
                               'kg_to_graphml'],
                       help="批量转换时的具体类型")
    
    args = parser.parse_args()
    
    print("🔄 KGRL格式转换工具")
    print("=" * 30)
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"❌ 输入路径不存在: {input_path}")
        return
    
    output_path = Path(args.output) if args.output else None
    
    try:
        if args.type == 'batch':
            if not args.batch_type:
                print("❌ 批量转换需要指定 --batch-type")
                return
            
            if input_path.is_dir():
                converted_files = batch_convert_directory(input_path, args.batch_type)
                create_conversion_report(converted_files, input_path)
            else:
                print("❌ 批量转换需要输入目录")
        else:
            # 单文件转换
            conversion_map = {
                'json_to_yaml': json_to_yaml,
                'yaml_to_json': yaml_to_json,
                'results_to_csv': results_to_csv,
                'kg_to_graphml': kg_to_graphml
            }
            
            convert_func = conversion_map[args.type]
            result = convert_func(input_path, output_path)
            
            if result:
                print(f"\n✅ 转换完成: {result}")
            else:
                print(f"\n❌ 转换失败")
    
    except Exception as e:
        print(f"❌ 转换过程出错: {e}")

if __name__ == "__main__":
    main()
