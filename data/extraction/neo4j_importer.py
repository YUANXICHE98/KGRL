#!/usr/bin/env python3
"""
Neo4j知识图谱导入器
将构建的知识图谱导入到Neo4j数据库中
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️  Neo4j driver未安装，请运行: pip install neo4j")

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder


class Neo4jImporter:
    """Neo4j导入器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.driver = None
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "extraction_config.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('neo4j', {})
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            return {
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': 'yuanxi98',
                'database': 'neo4j'
            }
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('neo4j_importer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def connect(self) -> bool:
        """连接到Neo4j数据库"""
        if not NEO4J_AVAILABLE:
            self.logger.error("Neo4j driver未安装")
            return False
        
        try:
            self.driver = GraphDatabase.driver(
                self.config['uri'],
                auth=(self.config['user'], self.config['password'])
            )
            
            # 测试连接
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()['test']
                
            self.logger.info(f"✅ 成功连接到Neo4j: {self.config['uri']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 连接Neo4j失败: {e}")
            return False
    
    def clear_database(self) -> bool:
        """清空数据库"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # 删除所有节点和关系
                session.run("MATCH (n) DETACH DELETE n")
                
            self.logger.info("✅ 数据库已清空")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 清空数据库失败: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """创建索引"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # 为不同类型的节点创建索引
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
                
            self.logger.info("✅ 索引创建完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建索引失败: {e}")
            return False
    
    def import_kg_from_builder(self, builder: DODAFKGBuilder) -> bool:
        """从DODAFKGBuilder导入知识图谱"""
        if not self.driver:
            self.logger.error("未连接到数据库")
            return False
        
        try:
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # 导入节点
                node_count = 0
                for node_id, node in builder.nodes.items():
                    # 获取节点标签
                    label = self._get_node_label(node.type.value)
                    
                    # 准备节点属性
                    properties = {
                        'id': node.id,
                        'name': node.name,
                        'type': node.type.value,
                        **self._serialize_attributes(node.attributes)
                    }
                    
                    # 创建节点
                    query = f"CREATE (n:{label} $props)"
                    session.run(query, props=properties)
                    node_count += 1
                
                self.logger.info(f"✅ 导入 {node_count} 个节点")
                
                # 导入边
                edge_count = 0
                for edge in builder.edges:
                    # 获取关系类型
                    rel_type = self._get_relationship_type(edge.type.value)
                    
                    # 准备关系属性
                    properties = self._serialize_attributes(edge.attributes)
                    
                    # 创建关系
                    query = f"""
                    MATCH (a {{id: $source_id}})
                    MATCH (b {{id: $target_id}})
                    CREATE (a)-[r:{rel_type} $props]->(b)
                    """
                    
                    session.run(query, 
                               source_id=edge.source,
                               target_id=edge.target,
                               props=properties)
                    edge_count += 1
                
                self.logger.info(f"✅ 导入 {edge_count} 条关系")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 导入知识图谱失败: {e}")
            return False
    
    def import_kg_from_json(self, json_file: str) -> bool:
        """从JSON文件导入知识图谱"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not self.driver:
                self.logger.error("未连接到数据库")
                return False
            
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # 导入节点
                node_count = 0
                for node in data.get('nodes', []):
                    label = self._get_node_label(node['type'])
                    
                    properties = {
                        'id': node['id'],
                        'name': node['name'],
                        'type': node['type'],
                        **self._serialize_attributes(node.get('attributes', {}))
                    }
                    
                    query = f"CREATE (n:{label} $props)"
                    session.run(query, props=properties)
                    node_count += 1
                
                # 导入边
                edge_count = 0
                for edge in data.get('edges', []):
                    rel_type = self._get_relationship_type(edge['type'])
                    
                    properties = self._serialize_attributes(edge.get('attributes', {}))
                    
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
                
                self.logger.info(f"✅ 从JSON导入 {node_count} 个节点, {edge_count} 条关系")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 从JSON导入失败: {e}")
            return False
    
    def _get_node_label(self, node_type: str) -> str:
        """获取节点标签"""
        label_mapping = self.config.get('node_labels', {})
        return label_mapping.get(node_type, node_type.capitalize())
    
    def _get_relationship_type(self, edge_type: str) -> str:
        """获取关系类型"""
        rel_mapping = self.config.get('relationship_types', {})
        return rel_mapping.get(edge_type, edge_type.upper())
    
    def _serialize_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """序列化属性，确保Neo4j兼容"""
        serialized = {}
        for key, value in attributes.items():
            if isinstance(value, (str, int, float, bool)):
                serialized[key] = value
            elif isinstance(value, (list, dict)):
                serialized[key] = json.dumps(value, ensure_ascii=False)
            else:
                serialized[key] = str(value)
        return serialized
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session(database=self.config.get('database', 'neo4j')) as session:
                # 节点统计
                node_result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                node_stats = {}
                total_nodes = 0
                for record in node_result:
                    labels = record['labels']
                    count = record['count']
                    label = labels[0] if labels else 'Unknown'
                    node_stats[label] = count
                    total_nodes += count
                
                # 关系统计
                rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                rel_stats = {}
                total_rels = 0
                for record in rel_result:
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
            self.logger.error(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.logger.info("✅ Neo4j连接已关闭")


def main():
    """主函数 - 测试Neo4j导入功能"""
    print("🚀 开始测试Neo4j导入功能\n")
    
    # 创建导入器
    importer = Neo4jImporter()
    
    # 连接数据库
    if not importer.connect():
        print("❌ 无法连接到Neo4j数据库")
        return
    
    # 清空数据库（如果配置允许）
    if importer.config.get('import_settings', {}).get('clear_database', False):
        importer.clear_database()
    
    # 创建索引
    if importer.config.get('import_settings', {}).get('create_indexes', True):
        importer.create_indexes()
    
    # 导入现有的知识图谱文件
    data_dir = Path(__file__).parent.parent
    kg_files = list((data_dir / "knowledge_graphs/extracted").glob("*.json"))
    
    if kg_files:
        # 导入第一个JSON文件
        json_file = kg_files[0]
        print(f"📁 导入文件: {json_file.name}")
        
        if importer.import_kg_from_json(str(json_file)):
            # 获取统计信息
            stats = importer.get_statistics()
            print("\n📊 Neo4j数据库统计:")
            for key, value in stats.items():
                print(f"   - {key}: {value}")
        else:
            print("❌ 导入失败")
    else:
        print("❌ 未找到知识图谱文件")
    
    # 关闭连接
    importer.close()
    
    print("\n🎉 Neo4j导入测试完成!")


if __name__ == "__main__":
    main()
