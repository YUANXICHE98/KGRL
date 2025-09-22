#!/usr/bin/env python3
"""
分析数据集规模
统计ALFWorld和TextWorld的完整数据集规模
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def analyze_alfworld_scale():
    """分析ALFWorld数据集规模"""
    print("🔍 分析ALFWorld数据集规模...")
    
    data_dir = Path(__file__).parent.parent
    alfworld_dir = data_dir / "benchmarks/alfworld"
    
    if not alfworld_dir.exists():
        print("❌ ALFWorld目录不存在")
        return {}
    
    stats = {
        'layout_files': 0,
        'pddl_files': 0,
        'domain_files': 0,
        'total_objects': 0,
        'unique_object_types': set(),
        'scenes': [],
        'sample_scenes': []
    }
    
    # 分析布局文件
    layout_dir = alfworld_dir / "alfworld/alfworld/gen/layouts"
    if layout_dir.exists():
        json_files = list(layout_dir.glob("*.json"))
        stats['layout_files'] = len(json_files)
        
        print(f"📁 找到 {len(json_files)} 个布局文件")
        
        # 分析所有布局文件
        for i, json_file in enumerate(json_files):
            scene_name = json_file.stem
            stats['scenes'].append(scene_name)
            
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                scene_objects = len(data)
                stats['total_objects'] += scene_objects
                
                # 统计对象类型
                for key in data.keys():
                    obj_type = key.split('|')[0]
                    stats['unique_object_types'].add(obj_type)
                
                # 保存前10个场景作为样本
                if i < 10:
                    stats['sample_scenes'].append({
                        'name': scene_name,
                        'objects': scene_objects,
                        'object_types': list(set(key.split('|')[0] for key in data.keys()))
                    })
                    
            except Exception as e:
                print(f"   ⚠️  读取 {json_file.name} 失败: {e}")
    
    # 分析PDDL问题文件
    pddl_dir = alfworld_dir / "alfworld/alfworld/gen/ff_planner/samples"
    if pddl_dir.exists():
        pddl_files = list(pddl_dir.glob("problem_*.pddl"))
        stats['pddl_files'] = len(pddl_files)
        print(f"📁 找到 {len(pddl_files)} 个PDDL问题文件")
    
    # 分析PDDL域文件
    domain_dir = alfworld_dir / "alfworld/alfworld/gen/planner/domains"
    if domain_dir.exists():
        domain_files = list(domain_dir.glob("*_domain.pddl"))
        stats['domain_files'] = len(domain_files)
        print(f"📁 找到 {len(domain_files)} 个PDDL域文件")
    
    # 转换set为list以便JSON序列化
    stats['unique_object_types'] = list(stats['unique_object_types'])
    
    return stats


def analyze_textworld_scale():
    """分析TextWorld数据集规模"""
    print("\n🔍 分析TextWorld数据集规模...")
    
    data_dir = Path(__file__).parent.parent
    textworld_dir = data_dir / "benchmarks/textworld"
    
    stats = {
        'available': False,
        'game_files': 0,
        'benchmark_games': 0,
        'sample_games': []
    }
    
    if not textworld_dir.exists():
        print("❌ TextWorld目录不存在")
        return stats
    
    stats['available'] = True
    
    # 查找游戏文件
    game_files = []
    for ext in ['*.json', '*.z8', '*.ulx']:
        game_files.extend(textworld_dir.rglob(ext))
    
    stats['game_files'] = len(game_files)
    print(f"📁 找到 {len(game_files)} 个游戏文件")
    
    # 查找benchmark文件
    benchmark_file = textworld_dir / "TextWorld/benchmark/games.json"
    if benchmark_file.exists():
        try:
            with open(benchmark_file, 'r') as f:
                benchmark_data = json.load(f)
            
            if isinstance(benchmark_data, list):
                stats['benchmark_games'] = len(benchmark_data)
                stats['sample_games'] = benchmark_data[:5]  # 前5个作为样本
            elif isinstance(benchmark_data, dict):
                stats['benchmark_games'] = len(benchmark_data)
                stats['sample_games'] = list(benchmark_data.items())[:5]
                
            print(f"📁 找到 {stats['benchmark_games']} 个benchmark游戏")
            
        except Exception as e:
            print(f"   ⚠️  读取benchmark文件失败: {e}")
    
    return stats


def generate_scale_report():
    """生成规模报告"""
    print("\n📊 生成数据集规模报告...")
    
    alfworld_stats = analyze_alfworld_scale()
    textworld_stats = analyze_textworld_scale()
    
    report = {
        'alfworld': alfworld_stats,
        'textworld': textworld_stats,
        'summary': {
            'total_scenes': alfworld_stats.get('layout_files', 0),
            'total_objects': alfworld_stats.get('total_objects', 0),
            'unique_object_types': len(alfworld_stats.get('unique_object_types', [])),
            'textworld_games': textworld_stats.get('benchmark_games', 0)
        }
    }
    
    # 输出报告
    print("\n📋 数据集规模总结:")
    print(f"   ALFWorld:")
    print(f"     - 场景数量: {report['summary']['total_scenes']}")
    print(f"     - 总对象数: {report['summary']['total_objects']}")
    print(f"     - 对象类型: {report['summary']['unique_object_types']}")
    print(f"     - PDDL问题: {alfworld_stats.get('pddl_files', 0)}")
    print(f"     - PDDL域: {alfworld_stats.get('domain_files', 0)}")
    
    print(f"   TextWorld:")
    print(f"     - 可用: {textworld_stats['available']}")
    print(f"     - 游戏文件: {textworld_stats['game_files']}")
    print(f"     - Benchmark游戏: {textworld_stats['benchmark_games']}")
    
    # 显示样本场景
    if alfworld_stats.get('sample_scenes'):
        print(f"\n🎯 ALFWorld样本场景 (前10个):")
        for i, scene in enumerate(alfworld_stats['sample_scenes']):
            print(f"     {i+1:2d}. {scene['name']}: {scene['objects']} 对象")
            print(f"         类型: {', '.join(scene['object_types'])}")
    
    # 显示对象类型统计
    if alfworld_stats.get('unique_object_types'):
        print(f"\n🏷️  ALFWorld对象类型统计:")
        for obj_type in sorted(alfworld_stats['unique_object_types']):
            print(f"     - {obj_type}")
    
    # 保存报告
    report_file = Path(__file__).parent / "dataset_scale_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 规模报告已保存到: {report_file}")
    
    return report


def main():
    """主函数"""
    print("🚀 开始分析数据集规模\n")
    
    report = generate_scale_report()
    
    print("\n🎉 数据集规模分析完成!")
    
    return report


if __name__ == "__main__":
    main()
