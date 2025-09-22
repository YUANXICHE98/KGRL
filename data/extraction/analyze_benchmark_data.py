#!/usr/bin/env python3
"""
分析benchmark数据结构
了解ALFWorld和TextWorld的真实数据格式，为规则抽取做准备
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def analyze_alfworld_data():
    """分析ALFWorld数据结构"""
    print("🔍 分析ALFWorld数据结构...")
    
    data_dir = Path(__file__).parent.parent
    alfworld_dir = data_dir / "benchmarks/alfworld"
    
    if not alfworld_dir.exists():
        print("❌ ALFWorld目录不存在")
        return
    
    # 分析布局文件
    layout_dir = alfworld_dir / "alfworld/alfworld/gen/layouts"
    if layout_dir.exists():
        json_files = list(layout_dir.glob("*.json"))
        print(f"📁 找到 {len(json_files)} 个布局文件")
        
        if json_files:
            # 分析第一个文件
            sample_file = json_files[0]
            print(f"📄 分析文件: {sample_file.name}")
            
            try:
                with open(sample_file, 'r') as f:
                    data = json.load(f)
                
                print(f"   - 对象数量: {len(data)}")
                print("   - 对象类型:")
                
                object_types = {}
                for key in data.keys():
                    obj_type = key.split('|')[0]
                    object_types[obj_type] = object_types.get(obj_type, 0) + 1
                
                for obj_type, count in sorted(object_types.items()):
                    print(f"     * {obj_type}: {count}")
                
                # 显示几个示例
                print("   - 示例对象:")
                for i, (key, value) in enumerate(list(data.items())[:3]):
                    print(f"     * {key}: {value}")
                
            except Exception as e:
                print(f"   ❌ 读取失败: {e}")
    
    # 分析PDDL文件
    pddl_dir = alfworld_dir / "alfworld/alfworld/gen/ff_planner/samples"
    if pddl_dir.exists():
        pddl_files = list(pddl_dir.glob("*.pddl"))
        print(f"\n📁 找到 {len(pddl_files)} 个PDDL文件")
        
        if pddl_files:
            sample_file = pddl_files[0]
            print(f"📄 分析文件: {sample_file.name}")
            
            try:
                with open(sample_file, 'r') as f:
                    content = f.read()
                
                print(f"   - 文件大小: {len(content)} 字符")
                
                # 分析对象定义
                import re
                objects_match = re.search(r'\(:objects\s+(.*?)\)', content, re.DOTALL)
                if objects_match:
                    objects_text = objects_match.group(1)
                    lines = [line.strip() for line in objects_text.split('\n') if line.strip()]
                    print(f"   - 对象定义行数: {len(lines)}")
                    
                    # 统计对象类型
                    object_types = {}
                    for line in lines:
                        if ' - ' in line:
                            _, type_part = line.split(' - ')
                            obj_type = type_part.strip()
                            object_types[obj_type] = object_types.get(obj_type, 0) + 1
                    
                    print("   - 对象类型:")
                    for obj_type, count in sorted(object_types.items()):
                        print(f"     * {obj_type}: {count}")
                
                # 显示文件开头
                print("   - 文件开头:")
                for i, line in enumerate(content.split('\n')[:10]):
                    print(f"     {i+1:2d}: {line}")
                
            except Exception as e:
                print(f"   ❌ 读取失败: {e}")


def analyze_textworld_data():
    """分析TextWorld数据结构"""
    print("\n🔍 分析TextWorld数据结构...")
    
    data_dir = Path(__file__).parent.parent
    textworld_dir = data_dir / "benchmarks/textworld"
    
    if not textworld_dir.exists():
        print("❌ TextWorld目录不存在")
        return
    
    # 查找TextWorld文件
    print(f"📁 TextWorld目录内容:")
    for item in textworld_dir.rglob("*"):
        if item.is_file() and item.suffix in ['.json', '.txt', '.py']:
            rel_path = item.relative_to(textworld_dir)
            print(f"   - {rel_path}")
    
    # 尝试使用TextWorld API创建示例游戏
    try:
        import textworld
        print("\n🎮 使用TextWorld API创建示例游戏...")
        
        from textworld import GameMaker
        maker = GameMaker()
        
        # 创建一个简单的游戏
        print("   - 创建GameMaker实例成功")
        print(f"   - 可用方法: {[m for m in dir(maker) if not m.startswith('_')][:10]}...")
        
        # 尝试创建房间和物品
        try:
            # 创建房间
            kitchen = maker.new_room("kitchen")
            living_room = maker.new_room("living_room")
            
            # 连接房间
            path = maker.connect(kitchen.east, living_room.west)
            
            # 创建物品
            apple = maker.new(type='food', name='apple')
            kitchen.add(apple)
            
            print("   - 成功创建示例游戏结构")
            print(f"     * 房间: kitchen, living_room")
            print(f"     * 物品: apple")
            print(f"     * 连接: kitchen <-> living_room")
            
        except Exception as e:
            print(f"   ⚠️  游戏创建失败: {e}")
            
    except ImportError:
        print("   ⚠️  TextWorld未安装或导入失败")
    except Exception as e:
        print(f"   ❌ TextWorld API测试失败: {e}")


def analyze_existing_kg_data():
    """分析已有的知识图谱数据"""
    print("\n🔍 分析已有的知识图谱数据...")
    
    data_dir = Path(__file__).parent.parent
    kg_dir = data_dir / "knowledge_graphs"
    
    if not kg_dir.exists():
        print("❌ 知识图谱目录不存在")
        return
    
    # 查找现有的知识图谱文件
    kg_files = []
    for ext in ['*.json', '*.graphml', '*.pickle']:
        kg_files.extend(kg_dir.rglob(ext))
    
    print(f"📁 找到 {len(kg_files)} 个知识图谱文件:")
    for kg_file in kg_files:
        rel_path = kg_file.relative_to(kg_dir)
        size = kg_file.stat().st_size
        print(f"   - {rel_path} ({size} bytes)")
        
        # 如果是JSON文件，尝试分析内容
        if kg_file.suffix == '.json':
            try:
                with open(kg_file, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    print(f"     * 键: {list(data.keys())}")
                    if 'nodes' in data:
                        print(f"     * 节点数: {len(data['nodes'])}")
                    if 'edges' in data:
                        print(f"     * 边数: {len(data['edges'])}")
                        
            except Exception as e:
                print(f"     ❌ 读取失败: {e}")


def generate_data_summary():
    """生成数据摘要报告"""
    print("\n📊 生成数据摘要报告...")
    
    data_dir = Path(__file__).parent.parent
    
    summary = {
        'alfworld': {
            'layout_files': 0,
            'pddl_files': 0,
            'total_objects': 0,
            'object_types': set()
        },
        'textworld': {
            'available': False,
            'api_working': False
        },
        'knowledge_graphs': {
            'existing_files': 0,
            'total_size_bytes': 0
        }
    }
    
    # 统计ALFWorld数据
    alfworld_dir = data_dir / "benchmarks/alfworld"
    if alfworld_dir.exists():
        layout_dir = alfworld_dir / "alfworld/alfworld/gen/layouts"
        if layout_dir.exists():
            json_files = list(layout_dir.glob("*.json"))
            summary['alfworld']['layout_files'] = len(json_files)
            
            # 统计对象
            for json_file in json_files[:5]:  # 只分析前5个文件
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    summary['alfworld']['total_objects'] += len(data)
                    
                    for key in data.keys():
                        obj_type = key.split('|')[0]
                        summary['alfworld']['object_types'].add(obj_type)
                except:
                    pass
        
        pddl_dir = alfworld_dir / "alfworld/alfworld/gen/ff_planner/samples"
        if pddl_dir.exists():
            pddl_files = list(pddl_dir.glob("*.pddl"))
            summary['alfworld']['pddl_files'] = len(pddl_files)
    
    # 检查TextWorld
    try:
        import textworld
        summary['textworld']['available'] = True
        
        from textworld import GameMaker
        maker = GameMaker()
        summary['textworld']['api_working'] = True
    except:
        pass
    
    # 统计知识图谱文件
    kg_dir = data_dir / "knowledge_graphs"
    if kg_dir.exists():
        kg_files = []
        for ext in ['*.json', '*.graphml', '*.pickle']:
            kg_files.extend(kg_dir.rglob(ext))
        
        summary['knowledge_graphs']['existing_files'] = len(kg_files)
        summary['knowledge_graphs']['total_size_bytes'] = sum(f.stat().st_size for f in kg_files)
    
    # 输出摘要
    print("📋 数据摘要:")
    print(f"   ALFWorld:")
    print(f"     - 布局文件: {summary['alfworld']['layout_files']}")
    print(f"     - PDDL文件: {summary['alfworld']['pddl_files']}")
    print(f"     - 总对象数: {summary['alfworld']['total_objects']}")
    print(f"     - 对象类型: {len(summary['alfworld']['object_types'])}")
    
    print(f"   TextWorld:")
    print(f"     - 可用: {summary['textworld']['available']}")
    print(f"     - API工作: {summary['textworld']['api_working']}")
    
    print(f"   知识图谱:")
    print(f"     - 现有文件: {summary['knowledge_graphs']['existing_files']}")
    print(f"     - 总大小: {summary['knowledge_graphs']['total_size_bytes']} bytes")
    
    # 保存摘要到文件
    summary_file = data_dir / "extraction/data_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 转换set为list以便JSON序列化
    summary['alfworld']['object_types'] = list(summary['alfworld']['object_types'])
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 摘要已保存到: {summary_file}")


def main():
    """主函数"""
    print("🚀 开始分析benchmark数据结构\n")
    
    # 分析ALFWorld数据
    analyze_alfworld_data()
    
    # 分析TextWorld数据
    analyze_textworld_data()
    
    # 分析已有知识图谱数据
    analyze_existing_kg_data()
    
    # 生成数据摘要
    generate_data_summary()
    
    print("\n🎉 数据分析完成!")


if __name__ == "__main__":
    main()
