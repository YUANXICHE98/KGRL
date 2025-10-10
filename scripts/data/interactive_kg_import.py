#!/usr/bin/env python3
"""
TextWorld任务场景知识图谱导入器
专门用于导入TextWorld任务场景KG到Neo4j
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from neo4j import GraphDatabase
except ImportError:
    print("❌ Neo4j driver未安装，请运行: pip install neo4j")
    sys.exit(1)


class TextWorldKGImporter:
    """TextWorld任务场景KG导入器"""

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
            print(f"   请确保Neo4j正在运行，地址: {self.uri}")
            return False

    def clear_database(self):
        """清空数据库"""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            print("🧹 数据库已清空")
            return True
        except Exception as e:
            print(f"❌ 清空数据库失败: {e}")
            return False

    def create_indexes_and_constraints(self):
        """创建索引和约束以改善可视化性能"""
        try:
            with self.driver.session() as session:
                # 为每种节点类型创建唯一约束
                node_types = ['Entity', 'Action', 'State', 'Result']

                for node_type in node_types:
                    try:
                        # 创建唯一约束（如果不存在）
                        constraint_query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_type}) REQUIRE n.id IS UNIQUE"
                        session.run(constraint_query)

                        # 创建name索引以改善搜索性能
                        index_query = f"CREATE INDEX IF NOT EXISTS FOR (n:{node_type}) ON (n.name)"
                        session.run(index_query)

                    except Exception as e:
                        # 忽略已存在的约束/索引错误
                        pass

                print("📊 已创建索引和约束")
                return True
        except Exception as e:
            print(f"⚠️ 创建索引失败: {e}")
            return False
    
    def import_textworld_kg(self, json_file):
        """导入TextWorld任务场景KG"""
        try:
            print(f"📁 加载文件: {Path(json_file).name}")

            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            metadata = data.get('metadata', {})

            print(f"📊 统计: {len(nodes)} 节点, {len(edges)} 边")

            # 显示任务信息
            task_info = metadata.get('task_info', {})
            if task_info:
                print(f"🎯 任务: {task_info.get('objective', 'N/A')[:60]}...")
                print(f"📈 最大分数: {task_info.get('max_score', 'N/A')}")
                print(f"🎮 通关步骤: {task_info.get('walkthrough_length', 'N/A')}步")

            # 创建索引和约束
            self.create_indexes_and_constraints()

            with self.driver.session() as session:
                # 导入节点
                print("🔄 导入节点...")
                for i, node in enumerate(nodes):
                    if i % 50 == 0 and i > 0:
                        print(f"   进度: {i}/{len(nodes)}")

                    # 根据节点类型设置标签
                    node_type = node['type']
                    label = node_type.capitalize()

                    # 准备基础属性
                    props = {
                        'id': node['id'],
                        'name': node['name'],
                        'type': node_type,
                        'display_name': node['name']  # 专门用于显示的属性
                    }

                    # 添加attributes中的属性
                    attrs = node.get('attributes', {})
                    for key, value in attrs.items():
                        # 跳过复杂的嵌套属性，避免显示混乱
                        if key in ['properties', 'required_entities', 'required_states', 'effects']:
                            if isinstance(value, dict):
                                # 将字典转换为易读的字符串
                                props[key] = json.dumps(value, ensure_ascii=False, indent=2)
                            elif isinstance(value, list):
                                props[key] = ', '.join(str(v) for v in value)
                            else:
                                props[key] = str(value)
                        elif isinstance(value, (str, int, float, bool)):
                            props[key] = value
                        elif isinstance(value, (list, dict)):
                            props[key] = json.dumps(value, ensure_ascii=False)
                        else:
                            props[key] = str(value)

                    # 为不同类型的节点添加特殊属性以改善可视化
                    if node_type == 'entity':
                        entity_type = attrs.get('entity_type', 'unknown')
                        props['entity_type'] = entity_type
                        props['label_display'] = f"{node['name']} ({entity_type})"
                    elif node_type == 'action':
                        props['label_display'] = f"⚡ {node['name']}"
                    elif node_type == 'state':
                        props['label_display'] = f"🔄 {node['name']}"
                    elif node_type == 'result':
                        props['label_display'] = f"✅ {node['name']}"
                    else:
                        props['label_display'] = node['name']

                    # 创建节点，使用MERGE避免重复
                    query = f"MERGE (n:{label} {{id: $id}}) SET n = $props"
                    session.run(query, id=props['id'], props=props)

                print(f"✅ 导入了 {len(nodes)} 个节点")

                # 导入关系
                print("🔄 导入关系...")
                for i, edge in enumerate(edges):
                    if i % 50 == 0 and i > 0:
                        print(f"   进度: {i}/{len(edges)}")

                    rel_type = edge['type'].upper()

                    # 准备关系属性
                    rel_props = {
                        'type': edge['type']
                    }

                    # 添加其他边属性（如果有）
                    for key, value in edge.items():
                        if key not in ['source', 'target', 'type']:
                            if isinstance(value, (str, int, float, bool)):
                                rel_props[key] = value
                            else:
                                rel_props[key] = str(value)

                    # 创建关系
                    if rel_props:
                        query = f"""
                        MATCH (a {{id: $source}})
                        MATCH (b {{id: $target}})
                        MERGE (a)-[r:{rel_type}]->(b)
                        SET r = $props
                        """
                        session.run(query, source=edge['source'], target=edge['target'], props=rel_props)
                    else:
                        query = f"""
                        MATCH (a {{id: $source}})
                        MATCH (b {{id: $target}})
                        MERGE (a)-[r:{rel_type}]->(b)
                        """
                        session.run(query, source=edge['source'], target=edge['target'])

                print(f"✅ 导入了 {len(edges)} 条关系")

                # 设置Neo4j浏览器的节点显示属性
                print("🎨 配置节点显示...")
                display_configs = [
                    "CALL db.createLabel('Entity')",
                    "CALL db.createLabel('Action')",
                    "CALL db.createLabel('State')",
                    "CALL db.createLabel('Result')"
                ]

                # 这些命令可能在某些Neo4j版本中不可用，所以忽略错误
                for config in display_configs:
                    try:
                        session.run(config)
                    except:
                        pass

                print("💡 提示: 在Neo4j浏览器中，点击节点类型图标，选择'name'作为Caption属性")

            return True

        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False

    def get_stats(self):
        """获取数据库统计信息"""
        try:
            with self.driver.session() as session:
                # 节点统计
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()['count']

                # 关系统计
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()['count']

                # 节点类型统计
                type_result = session.run("MATCH (n) RETURN n.type as type, count(n) as count")
                type_stats = {record['type']: record['count'] for record in type_result}

                return {
                    'nodes': node_count,
                    'relationships': rel_count,
                    'node_types': type_stats
                }
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {'nodes': 0, 'relationships': 0, 'node_types': {}}

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


def get_available_kg_files():
    """获取可用的KG文件列表"""
    kg_dir = Path("data/kg/task_scenes")
    kg_files = []

    if kg_dir.exists():
        for kg_file in sorted(kg_dir.glob("TextWorld_*_task_kg.json")):
            kg_files.append(str(kg_file))

    return kg_files


def main():
    """主函数"""

    print("🚀 TextWorld任务场景KG导入器")
    print("=" * 60)
    print("📋 专门用于导入TextWorld任务场景知识图谱到Neo4j")
    print("=" * 60)

    # 获取可用的KG文件
    kg_files = get_available_kg_files()

    if not kg_files:
        print("❌ 未找到任务场景KG文件")
        print("   请确保 data/kg/task_scenes/ 目录下有KG文件")
        return

    print(f"\n📁 找到 {len(kg_files)} 个任务场景KG文件:")
    for i, kg_file in enumerate(kg_files, 1):
        filename = Path(kg_file).name
        scenario_name = filename.replace("TextWorld_", "").replace("_task_kg.json", "")
        print(f"  {i}. {scenario_name}")

    print(f"\n  {len(kg_files)+1}. 🎯 导入全部文件")
    print(f"  {len(kg_files)+2}. 📄 查看汇总报告")

    # 创建导入器
    importer = TextWorldKGImporter()

    if not importer.connect():
        return

    try:
        while True:
            max_choice = len(kg_files) + 2
            print(f"\n🎯 请选择操作 (输入数字 1-{max_choice}，或 'q' 退出):")
            choice = input(">>> ").strip()

            if choice.lower() == 'q':
                print("👋 退出程序")
                break

            try:
                num = int(choice)

                if 1 <= num <= len(kg_files):
                    # 导入单个KG文件
                    selected_file = kg_files[num - 1]

                    # 确认清空数据库
                    confirm = input("🧹 是否先清空数据库? (y/n): ").strip().lower()
                    if confirm == 'y':
                        importer.clear_database()

                    print(f"\n🚀 开始导入: {Path(selected_file).name}")
                    success = importer.import_textworld_kg(selected_file)

                    if success:
                        stats = importer.get_stats()
                        print(f"\n✅ 导入成功!")
                        print(f"📊 数据库统计:")
                        print(f"   总节点: {stats['nodes']}")
                        print(f"   总关系: {stats['relationships']}")
                        print(f"   节点类型: {stats['node_types']}")
                        print(f"🌐 Neo4j浏览器: http://localhost:7474")

                elif num == len(kg_files) + 1:
                    # 导入全部文件
                    confirm = input("🧹 是否先清空数据库? (y/n): ").strip().lower()
                    if confirm == 'y':
                        importer.clear_database()

                    print(f"\n🚀 开始批量导入 {len(kg_files)} 个文件...")
                    success_count = 0

                    for i, kg_file in enumerate(kg_files, 1):
                        print(f"\n📦 [{i}/{len(kg_files)}] 导入: {Path(kg_file).name}")
                        if importer.import_textworld_kg(kg_file):
                            success_count += 1

                    stats = importer.get_stats()
                    print(f"\n✅ 批量导入完成: {success_count}/{len(kg_files)} 成功")
                    print(f"📊 最终数据库统计:")
                    print(f"   总节点: {stats['nodes']}")
                    print(f"   总关系: {stats['relationships']}")
                    print(f"   节点类型: {stats['node_types']}")
                    print(f"🌐 Neo4j浏览器: http://localhost:7474")

                elif num == len(kg_files) + 2:
                    # 查看汇总报告
                    summary_file = "data/kg/task_scenes/task_scenes_summary.json"
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary = json.load(f)

                        print(f"\n📊 任务场景KG汇总报告:")
                        print(f"   总文件数: {summary['total_files']}")
                        print(f"   成功处理: {summary['success_count']}")
                        print(f"   失败数: {summary['failed_count']}")

                        print(f"\n📋 详细统计:")
                        for detail in summary['kg_details']:
                            scenario = detail['scenario'].replace('TextWorld_', '')
                            print(f"   {scenario}:")
                            print(f"     节点: {detail['nodes']}, 边: {detail['edges']}")
                            print(f"     动作: {detail['node_types']['action']}")
                    except Exception as e:
                        print(f"❌ 读取汇总报告失败: {e}")

                else:
                    print(f"❌ 无效的数字，请输入 1-{max_choice}")

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
