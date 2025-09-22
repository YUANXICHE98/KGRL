#!/usr/bin/env python3
"""
专门的Neo4j导入脚本
清空数据库并导入最新的知识图谱
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

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


class Neo4jKGImporter:
    """Neo4j知识图谱导入器"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="yuanxi98"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
    def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()['test']
                
            print(f"✅ 成功连接到Neo4j: {self.uri}")
            return True
            
        except Exception as e:
            print(f"❌ 连接Neo4j失败: {e}")
            print("   请确保Neo4j服务正在运行")
            return False
    
    def clear_database(self):
        """清空数据库"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # 删除所有节点和关系
                session.run("MATCH (n) DETACH DELETE n")
                
            print("✅ 数据库已清空")
            return True
            
        except Exception as e:
            print(f"❌ 清空数据库失败: {e}")
            return False
    
    def create_indexes(self):
        """创建索引"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                indexes = [
                    "CREATE INDEX IF NOT EXISTS FOR (n:Action) ON (n.name)",
                    "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.name)",
                    "CREATE INDEX IF NOT EXISTS FOR (n:State) ON (n.name)",
                    "CREATE INDEX IF NOT EXISTS FOR (n:Result) ON (n.name)",
                    "CREATE INDEX IF NOT EXISTS FOR (n:Scene) ON (n.name)",
                    "CREATE INDEX IF NOT EXISTS FOR (n:Action) ON (n.id)",
                    "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.id)",
                    "CREATE INDEX IF NOT EXISTS FOR (n:State) ON (n.id)",
                ]
                
                for index_query in indexes:
                    session.run(index_query)
                
            print("✅ 索引创建完成")
            return True
            
        except Exception as e:
            print(f"❌ 创建索引失败: {e}")
            return False
    
    def import_json_kg(self, json_file: str):
        """从JSON文件导入知识图谱"""
        if not self.driver:
            return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            
            print(f"📁 导入文件: {Path(json_file).name}")
            print(f"   - 节点数: {len(nodes)}")
            print(f"   - 边数: {len(edges)}")
            
            with self.driver.session() as session:
                # 导入节点
                node_count = 0
                for node in nodes:
                    label = self.get_node_label(node['type'])
                    
                    # 准备属性
                    properties = {
                        'id': node['id'],
                        'name': node['name'],
                        'type': node['type']
                    }
                    
                    # 处理attributes
                    for key, value in node.get('attributes', {}).items():
                        if isinstance(value, (str, int, float, bool)):
                            properties[key] = value
                        elif isinstance(value, (list, dict)):
                            properties[key] = json.dumps(value, ensure_ascii=False)
                        else:
                            properties[key] = str(value)
                    
                    # 创建节点
                    query = f"CREATE (n:{label} $props)"
                    session.run(query, props=properties)
                    node_count += 1
                
                print(f"   ✅ 导入 {node_count} 个节点")
                
                # 导入边
                edge_count = 0
                for edge in edges:
                    rel_type = self.get_relationship_type(edge['type'])
                    
                    # 准备关系属性
                    properties = {}
                    for key, value in edge.get('attributes', {}).items():
                        if isinstance(value, (str, int, float, bool)):
                            properties[key] = value
                        elif isinstance(value, (list, dict)):
                            properties[key] = json.dumps(value, ensure_ascii=False)
                        else:
                            properties[key] = str(value)
                    
                    # 创建关系
                    query = f"""
                    MATCH (a {{id: $source_id}})
                    MATCH (b {{id: $target_id}})
                    CREATE (a)-[r:{rel_type} $props]->(b)
                    """
                    
                    session.run(query,
                               source_id=edge['source'],
                               target_id=edge['target'],
                               props=properties)
                    edge_count += 1
                
                print(f"   ✅ 导入 {edge_count} 条关系")
                
            return True
            
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_node_label(self, node_type: str) -> str:
        """获取节点标签"""
        label_mapping = {
            'action': 'Action',
            'entity': 'Entity',
            'state': 'State',
            'result': 'Result',
            'condition': 'Condition',
            'rule': 'Rule'
        }
        return label_mapping.get(node_type, node_type.capitalize())
    
    def get_relationship_type(self, edge_type: str) -> str:
        """获取关系类型"""
        rel_mapping = {
            'requires': 'REQUIRES',
            'produces': 'PRODUCES',
            'modifies': 'MODIFIES',
            'enables': 'ENABLES',
            'prevents': 'PREVENTS',
            'transitions': 'TRANSITIONS',
            'contains': 'CONTAINS',
            'has_state': 'HAS_STATE'
        }
        return rel_mapping.get(edge_type, edge_type.upper())
    
    def get_statistics(self):
        """获取数据库统计信息"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # 节点统计
                result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                node_stats = {}
                total_nodes = 0
                for record in result:
                    labels = record['labels']
                    count = record['count']
                    label = labels[0] if labels else 'Unknown'
                    node_stats[label] = count
                    total_nodes += count
                
                # 关系统计
                result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                rel_stats = {}
                total_rels = 0
                for record in result:
                    rel_type = record['type']
                    count = record['count']
                    rel_stats[rel_type] = count
                    total_rels += count
                
                return {
                    'total_nodes': total_nodes,
                    'total_relationships': total_rels,
                    'node_types': node_stats,
                    'relationship_types': rel_stats
                }
                
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j连接已关闭")


def main():
    """主函数"""
    print("🚀 开始导入知识图谱到Neo4j\n")
    
    # 创建导入器
    importer = Neo4jKGImporter()
    
    # 连接数据库
    if not importer.connect():
        return
    
    # 显示当前数据库状态
    print("📊 当前数据库状态:")
    current_stats = importer.get_statistics()
    for key, value in current_stats.items():
        print(f"   - {key}: {value}")
    
    # 询问是否清空数据库
    if current_stats.get('total_nodes', 0) > 0:
        clear_db = input(f"\n数据库中有 {current_stats['total_nodes']} 个节点，是否清空? (y/n): ").strip().lower()
        if clear_db == 'y':
            importer.clear_database()
        else:
            print("⚠️  将在现有数据基础上添加新数据")
    
    # 创建索引
    importer.create_indexes()
    
    # 选择要导入的知识图谱
    data_dir = Path(__file__).parent.parent
    kg_files = []
    
    # 查找可用的知识图谱文件
    extracted_dir = data_dir / "knowledge_graphs/extracted"
    scenes_dir = data_dir / "knowledge_graphs/scenes"
    
    print(f"\n📁 可用的知识图谱文件:")
    
    # 合并的知识图谱
    if extracted_dir.exists():
        for json_file in extracted_dir.glob("*.json"):
            kg_files.append(json_file)
            print(f"   {len(kg_files)}. {json_file.name} (合并模式)")
    
    # 场景分割的知识图谱
    if scenes_dir.exists():
        scene_files = list(scenes_dir.glob("*_kg.json"))
        if scene_files:
            print(f"   {len(kg_files)+1}. 所有场景文件 ({len(scene_files)} 个场景)")
            kg_files.append("ALL_SCENES")
    
    if not kg_files:
        print("❌ 未找到知识图谱文件")
        importer.close()
        return
    
    # 用户选择
    choice = input(f"\n请选择要导入的知识图谱 (1-{len(kg_files)}): ").strip()
    
    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(kg_files):
            raise ValueError("选择超出范围")
        
        selected = kg_files[choice_idx]
        
        if selected == "ALL_SCENES":
            # 导入所有场景
            scene_files = list(scenes_dir.glob("*_kg.json"))
            print(f"\n🏗️ 导入 {len(scene_files)} 个场景...")
            
            success_count = 0
            for scene_file in scene_files:
                if importer.import_json_kg(str(scene_file)):
                    success_count += 1
            
            print(f"\n✅ 成功导入 {success_count}/{len(scene_files)} 个场景")
            
        else:
            # 导入单个文件
            print(f"\n🏗️ 导入知识图谱...")
            if importer.import_json_kg(str(selected)):
                print("✅ 导入成功!")
            else:
                print("❌ 导入失败!")
        
        # 显示最终统计
        print(f"\n📊 导入后数据库统计:")
        final_stats = importer.get_statistics()
        for key, value in final_stats.items():
            print(f"   - {key}: {value}")
        
        print(f"\n🎯 Neo4j查询示例:")
        print(f"   - 查看所有节点: MATCH (n) RETURN n LIMIT 25")
        print(f"   - 查看动作节点: MATCH (n:Action) RETURN n")
        print(f"   - 查看关系: MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10")
        print(f"   - 查看场景: MATCH (s:Entity {{entity_type: 'scene'}}) RETURN s")
        
    except (ValueError, IndexError):
        print("❌ 无效选择")
    
    # 关闭连接
    importer.close()
    
    print(f"\n🎉 导入完成! 请在Neo4j Browser中查看: http://localhost:7474")


if __name__ == "__main__":
    main()
