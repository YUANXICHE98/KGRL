#!/usr/bin/env python3
"""
交互式知识图谱导入脚本
让用户选择数字导入对应的KG文件到Neo4j
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("❌ Neo4j driver未安装，请运行: pip install neo4j")
    sys.exit(1)


class SimpleNeo4jImporter:
    """简单的Neo4j导入器"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="yuanxi98"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            print(f"✅ 连接Neo4j成功: {self.uri}")
            return True
        except Exception as e:
            print(f"❌ 连接Neo4j失败: {e}")
            return False
    
    def clear_database(self):
        """清空数据库"""
        try:
            with self.driver.session() as session:
                # 删除所有节点和关系
                session.run("MATCH (n) DETACH DELETE n")

                # 删除所有约束
                constraints_result = session.run("SHOW CONSTRAINTS")
                for record in constraints_result:
                    constraint_name = record.get("name")
                    if constraint_name:
                        try:
                            session.run(f"DROP CONSTRAINT {constraint_name}")
                        except:
                            pass  # 忽略删除约束的错误

                # 删除所有索引
                indexes_result = session.run("SHOW INDEXES")
                for record in indexes_result:
                    index_name = record.get("name")
                    if index_name and not index_name.startswith("system"):
                        try:
                            session.run(f"DROP INDEX {index_name}")
                        except:
                            pass  # 忽略删除索引的错误

            print("🧹 数据库已完全清空 (包括约束和索引)")
            return True
        except Exception as e:
            print(f"❌ 清空数据库失败: {e}")
            return False
    
    def import_kg_simple(self, json_file):
        """简单导入KG文件"""
        try:
            print(f"📁 加载文件: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            
            print(f"📊 统计: {len(nodes)} 节点, {len(edges)} 边")
            
            with self.driver.session() as session:
                # 导入节点
                print("🔄 导入节点...")
                for i, node in enumerate(nodes):
                    if i % 50 == 0:
                        print(f"   进度: {i}/{len(nodes)}")
                    
                    label = self._get_label(node['type'])
                    props = {
                        'id': node['id'],
                        'name': node['name'],
                        'type': node['type']
                    }
                    
                    # 添加属性
                    attrs = node.get('attributes', {})
                    for key, value in attrs.items():
                        if isinstance(value, (str, int, float, bool)):
                            props[key] = value
                        else:
                            props[key] = str(value)
                    
                    # 使用MERGE避免重复节点
                    query = f"MERGE (n:{label} {{id: $id}}) SET n = $props"
                    session.run(query, id=props['id'], props=props)
                
                print(f"✅ 导入了 {len(nodes)} 个节点")
                
                # 导入边
                print("🔄 导入边...")
                for i, edge in enumerate(edges):
                    if i % 50 == 0:
                        print(f"   进度: {i}/{len(edges)}")
                    
                    rel_type = edge['type'].upper()
                    # 使用MERGE避免重复关系
                    query = f"""
                    MATCH (a {{id: $source}})
                    MATCH (b {{id: $target}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    """
                    session.run(query, source=edge['source'], target=edge['target'])
                
                print(f"✅ 导入了 {len(edges)} 条边")
            
            return True
            
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False
    
    def _get_label(self, node_type):
        """获取节点标签"""
        mapping = {
            'action': 'Action',
            'entity': 'Entity',
            'state': 'State',
            'result': 'Result',
            'condition': 'Condition',
            'rule': 'Rule'
        }
        return mapping.get(node_type, node_type.capitalize())
    
    def get_stats(self):
        """获取统计信息"""
        try:
            with self.driver.session() as session:
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()['count']
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()['count']
                
                return {'nodes': node_count, 'relationships': rel_count}
        except:
            return {'nodes': 0, 'relationships': 0}
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


def main():
    """主函数"""
    
    # KG文件映射 - 更新为包含新的TextWorld KG
    kg_files = {
        # 1. 真实TextWorld KG文件 (新生成的基于100%真实数据)
        1: "data/kg/enhanced_scenes/TextWorld_tw-another_game_enhanced_kg.json",

        # 2. 增强示例KG (原来的4号，作为对比)
        2: "data/kg/extracted/enhanced_example_kg.json",

        # 3-8. 其他可用的KG文件 (如果存在)
        3: "data/kg/extracted/alfworld_kg.json",
        4: "data/kg/extracted/test_kg.json",
        5: "data/kg/extracted/textworld_kg.json",
        6: "data/kg/domains/textworld/basic_game.json",
        7: "data/kg/schemas/kg_schema.json",
        8: "data/kg/enhanced_scenes/enhanced_scenes_summary.json"
    }
    
    print("🚀 交互式知识图谱导入器")
    print("=" * 50)
    
    # 显示文件列表
    print("📋 可用的KG文件:")
    print("  1. 🎮 真实TextWorld KG (基于100%真实数据)")
    print("  2. 📦 增强示例KG (原设计模板)")
    print("  3. 📦 ALFWorld KG")
    print("  4. 📦 测试KG")
    print("  5. 📦 TextWorld KG (旧版)")
    print("  6. 📄 基础游戏KG")
    print("  7. 📄 KG模式定义")
    print("  8. 📄 场景汇总")
    
    print("\n" + "=" * 50)
    
    # 创建导入器
    importer = SimpleNeo4jImporter()
    
    if not importer.connect():
        return
    
    try:
        while True:
            print("\n🎯 请选择要导入的KG文件 (输入数字 1-8，或 'q' 退出):")
            choice = input(">>> ").strip()

            if choice.lower() == 'q':
                print("👋 退出程序")
                break

            try:
                num = int(choice)
                if num not in kg_files:
                    print("❌ 无效的数字，请输入 1-8")
                    continue

                selected = kg_files[num]

                # 确认清空数据库
                confirm = input("🧹 是否先清空数据库? (y/n): ").strip().lower()
                if confirm == 'y':
                    importer.clear_database()

                # 处理单个文件或文件组
                if isinstance(selected, list):
                    # 文件组 (选项1和7)
                    print(f"\n📁 选择的文件组包含 {len(selected)} 个文件:")
                    for i, file_path in enumerate(selected, 1):
                        filename = Path(file_path).name
                        print(f"  {i}. {filename}")

                    sub_choice = input(f"\n请选择具体文件 (1-{len(selected)}) 或 'a' 导入全部: ").strip()

                    if sub_choice.lower() == 'a':
                        # 导入全部
                        success_count = 0
                        for file_path in selected:
                            kg_file = project_root / file_path
                            if kg_file.exists():
                                print(f"\n� 导入: {kg_file.name}")
                                if importer.import_kg_simple(str(kg_file)):
                                    success_count += 1

                        stats = importer.get_stats()
                        print(f"\n✅ 成功导入 {success_count}/{len(selected)} 个文件")
                        print(f"📊 数据库统计: {stats['nodes']} 节点, {stats['relationships']} 关系")
                    else:
                        # 导入单个
                        try:
                            sub_num = int(sub_choice) - 1
                            if 0 <= sub_num < len(selected):
                                kg_file = project_root / selected[sub_num]
                                if kg_file.exists():
                                    print(f"\n🚀 导入: {kg_file.name}")
                                    success = importer.import_kg_simple(str(kg_file))
                                    if success:
                                        stats = importer.get_stats()
                                        print(f"\n✅ 导入成功!")
                                        print(f"📊 数据库统计: {stats['nodes']} 节点, {stats['relationships']} 关系")
                            else:
                                print("❌ 无效的文件编号")
                        except ValueError:
                            print("❌ 请输入有效的数字")
                else:
                    # 单个文件
                    kg_file = project_root / selected

                    if not kg_file.exists():
                        print(f"❌ 文件不存在: {kg_file}")
                        continue

                    print(f"\n📁 选择的文件: {kg_file.name}")

                    # 导入文件
                    print(f"\n🚀 开始导入...")
                    success = importer.import_kg_simple(str(kg_file))

                    if success:
                        stats = importer.get_stats()
                        print(f"\n✅ 导入成功!")
                        print(f"📊 数据库统计: {stats['nodes']} 节点, {stats['relationships']} 关系")
                    else:
                        print(f"\n❌ 导入失败!")

                print(f"🌐 查看地址: http://localhost:7474")

            except ValueError:
                print("❌ 请输入有效的数字")
                continue
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，退出程序")
                break
    
    finally:
        importer.close()


if __name__ == "__main__":
    main()
