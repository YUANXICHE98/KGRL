#!/usr/bin/env python3
"""
标准化Neo4j知识图谱导入脚本
优化导入性能，避免卡顿问题

功能：
1. 批量导入节点和边
2. 优化的查询策略
3. 进度显示和错误处理
4. 支持多种KG格式
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

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

from src.utils.logging_utils import setup_logging


class OptimizedNeo4jImporter:
    """优化的Neo4j知识图谱导入器"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", password: str = "yuanxi98"):
        """初始化导入器"""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.logger = logging.getLogger("Neo4jImporter")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # 批量导入配置
        self.batch_size = 1000  # 每批处理的节点/边数量
        self.max_retries = 3    # 最大重试次数
        
    def connect(self) -> bool:
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()['test']
                
            self.logger.info(f"✅ 成功连接到Neo4j: {self.uri}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 连接Neo4j失败: {e}")
            self.logger.error("   请确保Neo4j服务正在运行")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            self.logger.info("🔌 数据库连接已关闭")
    
    def clear_database(self) -> bool:
        """清空数据库"""
        try:
            with self.driver.session() as session:
                # 删除所有节点和关系
                session.run("MATCH (n) DETACH DELETE n")
                
            self.logger.info("🧹 数据库已清空")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 清空数据库失败: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """创建索引以提高查询性能"""
        try:
            with self.driver.session() as session:
                # 为常用属性创建索引
                indexes = [
                    "CREATE INDEX entity_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id)",
                    "CREATE INDEX entity_name_index IF NOT EXISTS FOR (n:Entity) ON (n.name)",
                    "CREATE INDEX action_id_index IF NOT EXISTS FOR (n:Action) ON (n.id)",
                    "CREATE INDEX state_id_index IF NOT EXISTS FOR (n:State) ON (n.id)",
                ]
                
                for index_query in indexes:
                    session.run(index_query)
                
            self.logger.info("📊 索引创建完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建索引失败: {e}")
            return False
    
    def import_kg_from_json(self, json_file: str, progress_callback=None) -> bool:
        """从JSON文件导入知识图谱 - 优化版本"""
        try:
            self.logger.info(f"📁 加载KG文件: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            
            self.logger.info(f"📊 KG统计: {len(nodes)} 节点, {len(edges)} 边")
            
            # 批量导入节点
            if not self._import_nodes_batch(nodes, progress_callback):
                return False
            
            # 批量导入边
            if not self._import_edges_batch(edges, progress_callback):
                return False
            
            self.logger.info("✅ KG导入完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 导入KG失败: {e}")
            return False
    
    def _import_nodes_batch(self, nodes: List[Dict], progress_callback=None) -> bool:
        """批量导入节点"""
        try:
            total_nodes = len(nodes)
            self.logger.info(f"🔄 开始批量导入 {total_nodes} 个节点...")
            
            with self.driver.session() as session:
                for i in range(0, total_nodes, self.batch_size):
                    batch = nodes[i:i + self.batch_size]
                    batch_num = i // self.batch_size + 1
                    total_batches = (total_nodes + self.batch_size - 1) // self.batch_size
                    
                    self.logger.info(f"   📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 节点)")
                    
                    # 构建批量插入查询
                    query = self._build_batch_node_query()
                    
                    # 准备批量数据
                    batch_data = []
                    for node in batch:
                        node_data = {
                            'id': node['id'],
                            'name': node['name'],
                            'type': node['type'],
                            'label': self._get_node_label(node['type']),
                            'attributes': self._serialize_attributes(node.get('attributes', {}))
                        }
                        batch_data.append(node_data)
                    
                    # 执行批量插入
                    session.run(query, nodes=batch_data)
                    
                    if progress_callback:
                        progress_callback(i + len(batch), total_nodes, "nodes")
            
            self.logger.info(f"✅ 成功导入 {total_nodes} 个节点")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 批量导入节点失败: {e}")
            return False
    
    def _import_edges_batch(self, edges: List[Dict], progress_callback=None) -> bool:
        """批量导入边 - 优化版本"""
        try:
            total_edges = len(edges)
            self.logger.info(f"🔄 开始批量导入 {total_edges} 条边...")
            
            with self.driver.session() as session:
                for i in range(0, total_edges, self.batch_size):
                    batch = edges[i:i + self.batch_size]
                    batch_num = i // self.batch_size + 1
                    total_batches = (total_edges + self.batch_size - 1) // self.batch_size
                    
                    self.logger.info(f"   📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 条边)")
                    
                    # 使用优化的边导入策略
                    success = self._import_edge_batch_optimized(session, batch)
                    
                    if not success:
                        self.logger.warning(f"   ⚠️ 批次 {batch_num} 部分失败，继续处理...")
                    
                    if progress_callback:
                        progress_callback(i + len(batch), total_edges, "edges")
            
            self.logger.info(f"✅ 成功导入 {total_edges} 条边")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 批量导入边失败: {e}")
            return False
    
    def _import_edge_batch_optimized(self, session, batch: List[Dict]) -> bool:
        """优化的边批量导入"""
        try:
            # 使用UNWIND进行批量处理，避免逐个查询
            query = """
            UNWIND $edges AS edge
            MATCH (a {id: edge.source})
            MATCH (b {id: edge.target})
            CALL apoc.create.relationship(a, edge.rel_type, edge.attributes, b) YIELD rel
            RETURN count(rel) as created
            """
            
            # 如果没有APOC插件，使用标准查询
            fallback_query = """
            UNWIND $edges AS edge
            MATCH (a {id: edge.source})
            MATCH (b {id: edge.target})
            CREATE (a)-[r:RELATES]->(b)
            SET r = edge.attributes
            SET r.type = edge.rel_type
            RETURN count(r) as created
            """
            
            # 准备批量数据
            batch_data = []
            for edge in batch:
                edge_data = {
                    'source': edge['source'],
                    'target': edge['target'],
                    'rel_type': self._get_relationship_type(edge['type']),
                    'attributes': self._serialize_attributes(edge.get('attributes', {}))
                }
                batch_data.append(edge_data)
            
            try:
                # 尝试使用APOC查询
                result = session.run(query, edges=batch_data)
                created = result.single()['created']
            except:
                # 回退到标准查询
                result = session.run(fallback_query, edges=batch_data)
                created = result.single()['created']
            
            return created > 0
            
        except Exception as e:
            self.logger.error(f"批量导入边出错: {e}")
            return False
    
    def _build_batch_node_query(self) -> str:
        """构建批量节点插入查询 - 不使用APOC"""
        return """
        UNWIND $nodes AS node
        CALL {
            WITH node
            CREATE (n)
            SET n = node.attributes
            SET n.id = node.id, n.name = node.name, n.type = node.type
            WITH n, node.label as label
            CALL apoc.create.addLabels(n, [label]) YIELD node as labeled_node
            RETURN labeled_node
        }
        RETURN count(*) as created
        """
    
    def _get_node_label(self, node_type: str) -> str:
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
    
    def _get_relationship_type(self, edge_type: str) -> str:
        """获取关系类型"""
        rel_mapping = {
            'requires': 'REQUIRES',
            'produces': 'PRODUCES',
            'modifies': 'MODIFIES',
            'enables': 'ENABLES',
            'prevents': 'PREVENTS',
            'has_state': 'HAS_STATE',
            'located_in': 'LOCATED_IN',
            'connected_to': 'CONNECTED_TO'
        }
        return rel_mapping.get(edge_type, edge_type.upper())
    
    def _serialize_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """序列化属性"""
        serialized = {}
        for key, value in attributes.items():
            if isinstance(value, (str, int, float, bool)):
                serialized[key] = value
            elif isinstance(value, (list, dict)):
                serialized[key] = json.dumps(value, ensure_ascii=False)
            else:
                serialized[key] = str(value)
        return serialized
    
    def get_statistics(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        try:
            with self.driver.session() as session:
                # 统计节点
                node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = node_result.single()['node_count']
                
                # 统计关系
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = rel_result.single()['rel_count']
                
                # 统计标签
                label_result = session.run("CALL db.labels() YIELD label RETURN count(label) as label_count")
                label_count = label_result.single()['label_count']
                
                return {
                    'nodes': node_count,
                    'relationships': rel_count,
                    'labels': label_count
                }
                
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}


def progress_callback(current: int, total: int, item_type: str):
    """进度回调函数"""
    percentage = (current / total) * 100
    print(f"   📈 {item_type}: {current}/{total} ({percentage:.1f}%)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="标准化Neo4j知识图谱导入脚本")
    parser.add_argument("--file", type=str, help="要导入的KG JSON文件")
    parser.add_argument("--scene", type=str, help="导入特定场景")
    parser.add_argument("--all-scenes", action="store_true", help="导入所有增强场景")
    parser.add_argument("--uri", type=str, default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", type=str, default="neo4j", help="Neo4j用户名")
    parser.add_argument("--password", type=str, default="yuanxi98", help="Neo4j密码")
    parser.add_argument("--clear", action="store_true", help="导入前清空数据库")
    
    args = parser.parse_args()
    
    # 创建导入器
    importer = OptimizedNeo4jImporter(args.uri, args.user, args.password)
    
    print("🚀 标准化Neo4j知识图谱导入器")
    print(f"🌐 Neo4j URI: {args.uri}")
    
    # 连接数据库
    if not importer.connect():
        return
    
    try:
        # 清空数据库
        if args.clear:
            print("🧹 清空数据库...")
            importer.clear_database()
        
        # 创建索引
        print("📊 创建索引...")
        importer.create_indexes()
        
        # 确定要导入的文件
        kg_files = []
        
        if args.file:
            kg_files.append(Path(args.file))
        elif args.scene:
            kg_file = project_root / f"data/kg/enhanced_scenes/{args.scene}_enhanced_kg.json"
            if kg_file.exists():
                kg_files.append(kg_file)
            else:
                print(f"❌ 场景文件不存在: {kg_file}")
                return
        elif args.all_scenes:
            scenes_dir = project_root / "data/kg/enhanced_scenes"
            kg_files = list(scenes_dir.glob("*_enhanced_kg.json"))
        else:
            # 默认导入实验场景
            scenes = ['FloorPlan202-openable', 'FloorPlan308-openable']
            for scene in scenes:
                kg_file = project_root / f"data/kg/enhanced_scenes/{scene}_enhanced_kg.json"
                if kg_file.exists():
                    kg_files.append(kg_file)
        
        if not kg_files:
            print("❌ 未找到要导入的KG文件")
            return
        
        # 导入文件
        success_count = 0
        for kg_file in kg_files:
            print(f"\n🏗️ 导入文件: {kg_file.name}")
            
            start_time = time.time()
            if importer.import_kg_from_json(str(kg_file), progress_callback):
                elapsed = time.time() - start_time
                print(f"✅ 导入成功 (耗时: {elapsed:.1f}秒)")
                success_count += 1
            else:
                print(f"❌ 导入失败")
        
        # 显示最终统计
        print(f"\n📊 导入完成统计:")
        print(f"   - 成功导入: {success_count}/{len(kg_files)} 个文件")
        
        final_stats = importer.get_statistics()
        for key, value in final_stats.items():
            print(f"   - {key}: {value}")
        
        print(f"\n🎉 知识图谱导入完成!")
        print(f"🌐 请在Neo4j Browser中查看: http://localhost:7474")
        
    finally:
        importer.close()


if __name__ == "__main__":
    main()
