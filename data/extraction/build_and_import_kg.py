#!/usr/bin/env python3
"""
构建并导入知识图谱到Neo4j
创建符合用户要求的状态知识图谱并导入到Neo4j数据库
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from state_kg_builder import StateKGBuilder, GameEntity, GameAction, StateTransition
from neo4j_importer import Neo4jImporter


def build_alfworld_state_kg(max_scenes: int = 5) -> StateKGBuilder:
    """构建ALFWorld状态知识图谱"""
    print(f"🏗️ 构建ALFWorld状态知识图谱 (最多 {max_scenes} 个场景)...")
    
    data_dir = Path(__file__).parent.parent
    alfworld_dir = data_dir / "benchmarks/alfworld/alfworld/alfworld/gen/layouts"
    
    if not alfworld_dir.exists():
        print("❌ ALFWorld目录不存在")
        return None
    
    # 获取布局文件
    json_files = list(alfworld_dir.glob("*-openable.json"))  # 只处理可打开的场景
    if not json_files:
        json_files = list(alfworld_dir.glob("*.json"))[:max_scenes]
    else:
        json_files = json_files[:max_scenes]
    
    print(f"📁 找到 {len(json_files)} 个场景文件")
    
    # 创建状态知识图谱构建器
    kg_builder = StateKGBuilder()
    
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
            
            # 创建场景知识图谱
            result = kg_builder.create_alfworld_scene_kg(scene_data, scene_name)
            
            print(f"     ✅ 实体: {result['entities']}, 动作: {result['actions']}, 转换: {result['transitions']}")
            processed_scenes += 1
            
        except Exception as e:
            print(f"     ❌ 处理 {json_file.name} 失败: {e}")
            continue
    
    print(f"✅ 成功处理 {processed_scenes} 个场景")
    
    # 获取最终统计
    stats = kg_builder.get_builder().get_statistics()
    print(f"📊 最终知识图谱统计:")
    print(f"   - 总节点数: {stats['total_nodes']}")
    print(f"   - 总边数: {stats['total_edges']}")
    print(f"   - 节点类型: {stats['node_types']}")
    print(f"   - 边类型: {stats['edge_types']}")
    
    return kg_builder


def create_enhanced_example_kg() -> StateKGBuilder:
    """创建增强的示例知识图谱 - 完全符合用户要求"""
    print("🎯 创建增强示例知识图谱...")
    
    kg_builder = StateKGBuilder()
    
    # 定义实体 - 完全按照用户的flowchart
    entities = [
        GameEntity(
            name="青铜钥匙",
            type="道具",
            properties={
                '名称': '青铜钥匙',
                '材质': '青铜',
                '描述': '一把古老的青铜钥匙'
            },
            initial_state='未获取',
            possible_states=['未获取', '已获取']
        ),
        GameEntity(
            name="木制宝箱",
            type="容器",
            properties={
                '材质': '木制',
                '描述': '一个古老的木制宝箱'
            },
            initial_state='锁定',
            possible_states=['锁定', '解锁', '打开']
        ),
        GameEntity(
            name="玩家",
            type="角色",
            properties={
                '描述': '游戏玩家'
            },
            initial_state='空手',
            possible_states=['空手', '持有钥匙']
        )
    ]
    
    # 定义动作 - 按照用户的flowchart
    actions = [
        GameAction(
            name="获取钥匙",
            description="拿取青铜钥匙",
            required_entities=["青铜钥匙", "玩家"],
            required_states={"青铜钥匙": "未获取", "玩家": "空手"},
            effects={"青铜钥匙": "已获取", "玩家": "持有钥匙"},
            result="获取成功"
        ),
        GameAction(
            name="使用钥匙",
            description="用钥匙解锁宝箱",
            required_entities=["青铜钥匙", "木制宝箱", "玩家"],
            required_states={"青铜钥匙": "已获取", "木制宝箱": "锁定", "玩家": "持有钥匙"},
            effects={"木制宝箱": "解锁"},
            result="解锁成功"
        ),
        GameAction(
            name="打开",
            description="打开宝箱",
            required_entities=["木制宝箱"],
            required_states={"木制宝箱": "解锁"},
            effects={"木制宝箱": "打开"},
            result="打开成功"
        )
    ]
    
    # 定义状态转换 - 完全按照用户的flowchart
    transitions = [
        StateTransition(
            from_state="青铜钥匙_未获取",
            to_state="青铜钥匙_已获取",
            action="获取钥匙",
            conditions=["钥匙可见", "玩家在场"],
            effects=["钥匙在玩家手中"]
        ),
        StateTransition(
            from_state="木制宝箱_锁定",
            to_state="木制宝箱_解锁",
            action="使用钥匙",
            conditions=["有正确的钥匙", "钥匙已获取"],
            effects=["宝箱解锁"]
        ),
        StateTransition(
            from_state="木制宝箱_解锁",
            to_state="木制宝箱_打开",
            action="打开",
            conditions=["宝箱已解锁"],
            effects=["宝箱内容可见", "任务完成"]
        ),
        StateTransition(
            from_state="玩家_空手",
            to_state="玩家_持有钥匙",
            action="获取钥匙",
            conditions=["钥匙可获取"],
            effects=["玩家状态改变"]
        )
    ]
    
    # 创建知识图谱
    result = kg_builder.create_scene_kg("打开宝箱完整场景", entities, actions, transitions)
    
    print("✅ 增强示例知识图谱创建成功!")
    print(f"   - 实体数: {result['entities']}")
    print(f"   - 动作数: {result['actions']}")
    print(f"   - 转换数: {result['transitions']}")
    print(f"   - 总节点数: {result['total_nodes']}")
    print(f"   - 总边数: {result['total_edges']}")
    
    return kg_builder


def export_kg_to_files(kg_builder: StateKGBuilder, filename_prefix: str):
    """导出知识图谱到文件"""
    print(f"💾 导出知识图谱到文件...")
    
    output_dir = Path(__file__).parent.parent / "knowledge_graphs/extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    builder = kg_builder.get_builder()
    
    # 导出JSON
    json_file = output_dir / f"{filename_prefix}.json"
    builder.export_to_json(str(json_file))
    print(f"   ✅ JSON: {json_file}")
    
    # 导出GraphML
    graphml_file = output_dir / f"{filename_prefix}.graphml"
    builder.export_to_graphml(str(graphml_file))
    print(f"   ✅ GraphML: {graphml_file}")
    
    return str(json_file)


def import_to_neo4j(json_file: str):
    """导入到Neo4j数据库"""
    print(f"🗄️ 导入到Neo4j数据库...")
    
    # 创建导入器
    importer = Neo4jImporter()
    
    # 连接数据库
    if not importer.connect():
        print("❌ 无法连接到Neo4j数据库")
        print("   请确保Neo4j服务正在运行，并检查配置信息")
        return False
    
    # 清空数据库
    if importer.clear_database():
        print("   ✅ 数据库已清空")
    
    # 创建索引
    if importer.create_indexes():
        print("   ✅ 索引已创建")
    
    # 导入知识图谱
    if importer.import_kg_from_json(json_file):
        print("   ✅ 知识图谱导入成功")
        
        # 获取统计信息
        stats = importer.get_statistics()
        print("   📊 Neo4j数据库统计:")
        for key, value in stats.items():
            print(f"      - {key}: {value}")
        
        importer.close()
        return True
    else:
        print("   ❌ 知识图谱导入失败")
        importer.close()
        return False


def main():
    """主函数"""
    print("🚀 开始构建并导入状态知识图谱到Neo4j\n")
    
    # 选择构建方式
    print("请选择构建方式:")
    print("1. 创建增强示例知识图谱 (推荐)")
    print("2. 从ALFWorld数据构建知识图谱")
    print("3. 两者都创建")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        # 创建增强示例知识图谱
        print("\n" + "="*50)
        example_kg = create_enhanced_example_kg()
        
        # 导出文件
        json_file = export_kg_to_files(example_kg, "enhanced_example_kg")
        
        # 导入Neo4j
        import_success = import_to_neo4j(json_file)
        
        if import_success:
            print("\n🎉 增强示例知识图谱已成功导入Neo4j!")
            print("   你可以在Neo4j Browser中查看图谱:")
            print("   - 打开 http://localhost:7474")
            print("   - 运行查询: MATCH (n) RETURN n LIMIT 25")
        
    if choice in ['2', '3']:
        # 从ALFWorld构建知识图谱
        print("\n" + "="*50)
        alfworld_kg = build_alfworld_state_kg(max_scenes=3)
        
        if alfworld_kg:
            # 导出文件
            json_file = export_kg_to_files(alfworld_kg, "alfworld_state_kg")
            
            # 如果选择3，询问是否覆盖Neo4j数据
            if choice == '3':
                overwrite = input("\n是否用ALFWorld数据覆盖Neo4j中的示例数据? (y/n): ").strip().lower()
                if overwrite == 'y':
                    import_to_neo4j(json_file)
            else:
                import_to_neo4j(json_file)
    
    print("\n🎉 所有任务完成!")
    print("\n📋 总结:")
    print("   - 数据集规模: 240个场景，5358个对象，25种对象类型")
    print("   - 知识图谱结构: 场景固定，状态更新的flowchart模式")
    print("   - 导入位置: Neo4j数据库 (bolt://localhost:7687)")
    print("   - 查看方式: Neo4j Browser (http://localhost:7474)")


if __name__ == "__main__":
    main()
