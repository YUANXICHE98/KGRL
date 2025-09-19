#!/usr/bin/env python3
"""
知识图谱可视化脚本
独立的KG可视化工具，可以单独运行
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import FancyBboxPatch
import seaborn as sns

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

class KnowledgeGraphVisualizer:
    """知识图谱可视化器"""
    
    def __init__(self, output_dir: str = "results/kg_visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 可视化配置
        self.figsize = (14, 10)
        self.dpi = 300
        
        # 颜色配置
        self.colors = {
            'rooms': '#FF6B6B',      # 红色 - 房间
            'objects': '#4ECDC4',    # 青色 - 物品
            'actions': '#45B7D1',    # 蓝色 - 动作
            'properties': '#96CEB4', # 绿色 - 属性
            'goals': '#FFEAA7',      # 黄色 - 目标
            'default': '#DDA0DD'     # 紫色 - 默认
        }
        
        # 关系样式配置
        self.edge_styles = {
            'connected_to': {'style': '-', 'width': 2, 'color': '#2C3E50'},
            'located_in': {'style': '-', 'width': 1.5, 'color': '#E74C3C'},
            'can_be': {'style': '--', 'width': 1, 'color': '#3498DB'},
            'opens': {'style': '->', 'width': 2, 'color': '#F39C12'},
            'requires': {'style': '-.', 'width': 1.5, 'color': '#9B59B6'},
            'changes': {'style': ':', 'width': 1, 'color': '#1ABC9C'},
            'hidden_in': {'style': '-', 'width': 1.5, 'color': '#E67E22'},
            'goal': {'style': '->', 'width': 2.5, 'color': '#C0392B'}
        }
    
    def load_kg_from_json(self, kg_file: str) -> Dict[str, Any]:
        """从JSON文件加载知识图谱"""
        with open(kg_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_kg_from_builder(self, kg_builder) -> Dict[str, Any]:
        """从KG构建器加载知识图谱"""
        return {
            "facts": [fact.to_dict() for fact in kg_builder.facts],
            "entities": list(kg_builder.entities),
            "relations": list(kg_builder.relations),
            "stats": kg_builder.get_stats()
        }
    
    def classify_entity(self, entity: str) -> str:
        """分类实体类型"""
        rooms = ['kitchen', 'living_room', 'bedroom', 'bathroom', 'room']
        objects = ['fridge', 'table', 'sofa', 'tv', 'bed', 'chest', 'mirror', 
                  'apple', 'key', 'book', 'pillow', 'treasure']
        actions = ['take_item', 'open_container', 'go_direction']
        properties = ['opened', 'taken', 'free_hands', 'location']
        goals = ['find_treasure', 'open_chest', 'have_key', 'take_key', 'player']
        
        entity_lower = entity.lower()
        
        if any(room in entity_lower for room in rooms):
            return 'rooms'
        elif any(obj in entity_lower for obj in objects):
            return 'objects'
        elif any(action in entity_lower for action in actions):
            return 'actions'
        elif any(prop in entity_lower for prop in properties):
            return 'properties'
        elif any(goal in entity_lower for goal in goals):
            return 'goals'
        else:
            return 'default'
    
    def create_networkx_graph(self, kg_data: Dict[str, Any]) -> nx.MultiDiGraph:
        """创建NetworkX图"""
        G = nx.MultiDiGraph()
        
        # 添加节点和边
        for fact in kg_data.get("facts", []):
            subject = fact["subject"]
            predicate = fact["predicate"]
            obj = fact["object"]
            confidence = fact.get("confidence", 1.0)
            
            # 添加节点
            G.add_node(subject, entity_type=self.classify_entity(subject))
            G.add_node(obj, entity_type=self.classify_entity(obj))
            
            # 添加边
            G.add_edge(subject, obj, 
                      relation=predicate, 
                      confidence=confidence,
                      source=fact.get("source", "unknown"))
        
        return G
    
    def visualize_full_graph(self, kg_data: Dict[str, Any], 
                           title: str = "Knowledge Graph Visualization",
                           save_name: str = "kg_full_graph.png") -> str:
        """可视化完整知识图谱"""
        
        G = self.create_networkx_graph(kg_data)
        
        plt.figure(figsize=self.figsize)
        
        # 使用spring布局
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
        
        # 绘制节点
        for entity_type, color in self.colors.items():
            nodes = [node for node, data in G.nodes(data=True) 
                    if data.get('entity_type') == entity_type]
            if nodes:
                nx.draw_networkx_nodes(G, pos, nodelist=nodes, 
                                     node_color=color, node_size=1000, 
                                     alpha=0.8, edgecolors='black', linewidths=1)
        
        # 绘制边
        for relation, style_config in self.edge_styles.items():
            edges = [(u, v) for u, v, data in G.edges(data=True) 
                    if data.get('relation') == relation]
            if edges:
                nx.draw_networkx_edges(G, pos, edgelist=edges,
                                     edge_color=style_config['color'],
                                     width=style_config['width'],
                                     alpha=0.7, arrows=True, arrowsize=20,
                                     arrowstyle='->')
        
        # 添加节点标签
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
        
        # 添加边标签
        edge_labels = {}
        for u, v, data in G.edges(data=True):
            relation = data.get('relation', '')
            confidence = data.get('confidence', 1.0)
            edge_labels[(u, v)] = f"{relation}\n({confidence:.1f})"
        
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)
        
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        
        # 添加图例
        legend_elements = []
        for entity_type, color in self.colors.items():
            if any(data.get('entity_type') == entity_type for _, data in G.nodes(data=True)):
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                                markerfacecolor=color, markersize=10, 
                                                label=entity_type.title()))
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.axis('off')
        plt.tight_layout()
        
        # 保存图片
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def visualize_by_relation_type(self, kg_data: Dict[str, Any],
                                  save_name: str = "kg_by_relations.png") -> str:
        """按关系类型分别可视化"""
        
        G = self.create_networkx_graph(kg_data)
        relations = list(set(data.get('relation') for _, _, data in G.edges(data=True)))
        
        # 计算子图布局
        n_relations = len(relations)
        cols = min(3, n_relations)
        rows = (n_relations + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_relations == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes.reshape(1, -1)
        
        axes_flat = axes.flatten() if n_relations > 1 else axes
        
        for i, relation in enumerate(relations):
            ax = axes_flat[i]
            
            # 创建子图
            subgraph_edges = [(u, v) for u, v, data in G.edges(data=True) 
                             if data.get('relation') == relation]
            subgraph_nodes = set()
            for u, v in subgraph_edges:
                subgraph_nodes.add(u)
                subgraph_nodes.add(v)
            
            if not subgraph_nodes:
                ax.set_title(f"No edges for {relation}")
                ax.axis('off')
                continue
            
            subG = G.subgraph(subgraph_nodes)
            pos = nx.spring_layout(subG, k=2, iterations=30)
            
            # 绘制节点
            for entity_type, color in self.colors.items():
                nodes = [node for node, data in subG.nodes(data=True) 
                        if data.get('entity_type') == entity_type]
                if nodes:
                    nx.draw_networkx_nodes(subG, pos, nodelist=nodes, 
                                         node_color=color, node_size=500, 
                                         alpha=0.8, ax=ax)
            
            # 绘制边
            style_config = self.edge_styles.get(relation, 
                                              {'color': '#666666', 'width': 1})
            nx.draw_networkx_edges(subG, pos, edgelist=subgraph_edges,
                                 edge_color=style_config['color'],
                                 width=style_config['width'],
                                 alpha=0.7, arrows=True, ax=ax)
            
            # 添加标签
            nx.draw_networkx_labels(subG, pos, font_size=8, ax=ax)
            
            ax.set_title(f"Relation: {relation}", fontweight='bold')
            ax.axis('off')
        
        # 隐藏多余的子图
        for i in range(n_relations, len(axes_flat)):
            axes_flat[i].axis('off')
        
        plt.suptitle("Knowledge Graph by Relation Types", fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # 保存图片
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def create_statistics_plot(self, kg_data: Dict[str, Any],
                              save_name: str = "kg_statistics.png") -> str:
        """创建KG统计图表"""
        
        stats = kg_data.get("stats", {})
        facts = kg_data.get("facts", [])
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. 基础统计
        basic_stats = [
            stats.get("num_facts", 0),
            stats.get("num_entities", 0), 
            stats.get("num_relations", 0)
        ]
        ax1.bar(['Facts', 'Entities', 'Relations'], basic_stats, 
                color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_title('Basic Statistics', fontweight='bold')
        ax1.set_ylabel('Count')
        
        # 2. 关系类型分布
        relation_counts = {}
        for fact in facts:
            rel = fact.get("predicate", "unknown")
            relation_counts[rel] = relation_counts.get(rel, 0) + 1
        
        if relation_counts:
            relations = list(relation_counts.keys())
            counts = list(relation_counts.values())
            ax2.pie(counts, labels=relations, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Relation Distribution', fontweight='bold')
        
        # 3. 置信度分布
        confidences = [fact.get("confidence", 1.0) for fact in facts]
        if confidences:
            ax3.hist(confidences, bins=10, alpha=0.7, color='#96CEB4', edgecolor='black')
            ax3.set_title('Confidence Distribution', fontweight='bold')
            ax3.set_xlabel('Confidence')
            ax3.set_ylabel('Frequency')
        
        # 4. 实体类型分布
        entity_types = {}
        for fact in facts:
            for entity in [fact.get("subject"), fact.get("object")]:
                if entity:
                    entity_type = self.classify_entity(entity)
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        if entity_types:
            types = list(entity_types.keys())
            type_counts = list(entity_types.values())
            colors = [self.colors.get(t, self.colors['default']) for t in types]
            ax4.bar(types, type_counts, color=colors)
            ax4.set_title('Entity Type Distribution', fontweight='bold')
            ax4.set_ylabel('Count')
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # 保存图片
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def generate_full_report(self, kg_file: str) -> List[str]:
        """生成完整的KG可视化报告"""
        
        print(f"Loading knowledge graph from: {kg_file}")
        kg_data = self.load_kg_from_json(kg_file)
        
        kg_name = kg_data.get("kg_id", "unknown")
        print(f"Visualizing knowledge graph: {kg_name}")
        
        generated_plots = []
        
        # 1. 完整图谱
        print("Creating full graph visualization...")
        full_graph = self.visualize_full_graph(
            kg_data, 
            title=f"Knowledge Graph: {kg_name}",
            save_name=f"{kg_name}_full_graph.png"
        )
        generated_plots.append(full_graph)
        
        # 2. 按关系分类
        print("Creating relation-based visualizations...")
        relation_plots = self.visualize_by_relation_type(
            kg_data,
            save_name=f"{kg_name}_by_relations.png"
        )
        generated_plots.append(relation_plots)
        
        # 3. 统计图表
        print("Creating statistics plots...")
        stats_plot = self.create_statistics_plot(
            kg_data,
            save_name=f"{kg_name}_statistics.png"
        )
        generated_plots.append(stats_plot)
        
        print(f"Generated {len(generated_plots)} visualizations:")
        for plot in generated_plots:
            print(f"  - {plot}")
        
        return generated_plots

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Knowledge Graph Visualizer")
    parser.add_argument("--kg-file", 
                       default="data/knowledge_graphs/example_basic_kg.json",
                       help="Path to knowledge graph JSON file")
    parser.add_argument("--output-dir", 
                       default="results/kg_visualizations",
                       help="Output directory for visualizations")
    parser.add_argument("--format", choices=["png", "pdf", "svg"], 
                       default="png", help="Output format")
    
    args = parser.parse_args()
    
    # 检查输入文件
    kg_file = Path(args.kg_file)
    if not kg_file.exists():
        print(f"Error: Knowledge graph file not found: {kg_file}")
        return 1
    
    # 创建可视化器
    visualizer = KnowledgeGraphVisualizer(args.output_dir)
    
    try:
        # 生成可视化
        plots = visualizer.generate_full_report(str(kg_file))
        
        print("\n" + "="*50)
        print("KNOWLEDGE GRAPH VISUALIZATION COMPLETED")
        print("="*50)
        print(f"Input file: {kg_file}")
        print(f"Output directory: {args.output_dir}")
        print(f"Generated plots: {len(plots)}")
        print("="*50)
        
        return 0
        
    except Exception as e:
        print(f"Error during visualization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
