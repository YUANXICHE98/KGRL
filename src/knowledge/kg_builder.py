"""
知识图谱构建器
用于构建和管理微型知识图谱
"""

import json
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
import re
from dataclasses import dataclass

from ..utils.logger import get_logger

@dataclass
class KGFact:
    """知识图谱事实"""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: str = "manual"
    dodaf_type: str = "DA"  # DO (Action), DA (Condition), F (Outcome)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "source": self.source,
            "dodaf_type": self.dodaf_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KGFact':
        return cls(**data)
    
    def __str__(self) -> str:
        return f"({self.subject}, {self.predicate}, {self.object})"

class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self, kg_id: str = "default"):
        self.kg_id = kg_id
        self.logger = get_logger(f"KGBuilder_{kg_id}")
        
        # 使用NetworkX图存储知识
        self.graph = nx.MultiDiGraph()
        
        # 事实存储
        self.facts: List[KGFact] = []
        self.fact_index: Dict[str, List[int]] = {}  # 用于快速检索
        
        # 实体和关系统计
        self.entities: Set[str] = set()
        self.relations: Set[str] = set()
        
        self.logger.info(f"Initialized KnowledgeGraphBuilder: {kg_id}")
    
    def add_fact(self, subject: str, predicate: str, obj: str,
                 confidence: float = 1.0, source: str = "manual", dodaf_type: str = None) -> bool:
        """
        添加一个事实到知识图谱
        
        Args:
            subject: 主语
            predicate: 谓语/关系
            obj: 宾语
            confidence: 置信度
            source: 来源
            
        Returns:
            是否成功添加
        """
        try:
            # 标准化实体名称
            subject = self._normalize_entity(subject)
            obj = self._normalize_entity(obj)
            predicate = self._normalize_relation(predicate)
            
            # 自动推断DODAF类型
            if dodaf_type is None:
                dodaf_type = self._infer_dodaf_type(subject, predicate, obj)

            # 创建事实
            fact = KGFact(subject, predicate, obj, confidence, source, dodaf_type)
            
            # 检查是否已存在
            if self._fact_exists(fact):
                self.logger.debug(f"Fact already exists: {fact}")
                return False
            
            # 添加到图中
            self.graph.add_edge(subject, obj, relation=predicate, 
                              confidence=confidence, source=source)
            
            # 添加到事实列表
            fact_id = len(self.facts)
            self.facts.append(fact)
            
            # 更新索引
            self._update_fact_index(fact, fact_id)
            
            # 更新实体和关系集合
            self.entities.add(subject)
            self.entities.add(obj)
            self.relations.add(predicate)
            
            self.logger.debug(f"Added fact: {fact}")
            return fact
            
        except Exception as e:
            self.logger.error(f"Error adding fact: {e}")
            return None
    
    def add_facts_from_text(self, text: str, source: str = "text_extraction") -> int:
        """
        从文本中提取并添加事实
        
        Args:
            text: 输入文本
            source: 来源标识
            
        Returns:
            添加的事实数量
        """
        facts_added = 0
        
        # 简单的规则提取（可以扩展为更复杂的NLP方法）
        patterns = [
            # "X is in Y" -> (X, located_in, Y)
            (r'(\w+(?:\s+\w+)*)\s+is\s+in\s+(?:the\s+)?(\w+(?:\s+\w+)*)', 'located_in'),
            # "X has Y" -> (X, has, Y)
            (r'(\w+(?:\s+\w+)*)\s+has\s+(?:a\s+|an\s+)?(\w+(?:\s+\w+)*)', 'has'),
            # "X contains Y" -> (X, contains, Y)
            (r'(\w+(?:\s+\w+)*)\s+contains?\s+(?:a\s+|an\s+)?(\w+(?:\s+\w+)*)', 'contains'),
            # "You need X to Y" -> (Y, requires, X)
            (r'you\s+need\s+(?:a\s+|an\s+)?(\w+(?:\s+\w+)*)\s+to\s+(\w+(?:\s+\w+)*)', 'requires'),
        ]
        
        for pattern, relation in patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                if relation == 'requires':
                    # 特殊处理：需要关系的主宾语顺序
                    subject = match.group(2)
                    obj = match.group(1)
                else:
                    subject = match.group(1)
                    obj = match.group(2)
                
                if self.add_fact(subject, relation, obj, source=source):
                    facts_added += 1
        
        self.logger.info(f"Extracted {facts_added} facts from text")
        return facts_added
    
    def add_facts_from_dict(self, facts_dict: Dict[str, Any]) -> int:
        """
        从字典添加事实
        
        Args:
            facts_dict: 包含事实的字典
            
        Returns:
            添加的事实数量
        """
        facts_added = 0
        
        if "facts" in facts_dict:
            for fact_data in facts_dict["facts"]:
                if isinstance(fact_data, dict):
                    if self.add_fact(
                        fact_data.get("subject", ""),
                        fact_data.get("predicate", ""),
                        fact_data.get("object", ""),
                        fact_data.get("confidence", 1.0),
                        fact_data.get("source", "dict")
                    ):
                        facts_added += 1
        
        return facts_added
    
    def _normalize_entity(self, entity: str) -> str:
        """标准化实体名称"""
        return entity.strip().lower().replace("_", " ")
    
    def _normalize_relation(self, relation: str) -> str:
        """标准化关系名称"""
        return relation.strip().lower().replace(" ", "_")

    def _infer_dodaf_type(self, subject: str, predicate: str, obj: str) -> str:
        """
        自动推断DODAF类型

        Args:
            subject: 主语
            predicate: 谓语
            obj: 宾语

        Returns:
            DODAF类型: DO (Action), DA (Condition), F (Outcome)
        """
        # DO (Action) - 动作相关
        action_predicates = ['opens', 'leads_to', 'enables', 'triggers', 'executes']
        action_subjects = ['take', 'go', 'open', 'use', 'move']

        if any(pred in predicate for pred in action_predicates):
            return "DO"
        if any(act in subject.lower() for act in action_subjects):
            return "DO"

        # F (Outcome) - 结果相关
        outcome_predicates = ['results_in', 'causes', 'achieves', 'completes']
        outcome_subjects = ['goal', 'target', 'success', 'failure', 'reward']

        if any(pred in predicate for pred in outcome_predicates):
            return "F"
        if any(out in subject.lower() for out in outcome_subjects):
            return "F"

        # DA (Condition) - 默认为条件/状态
        return "DA"
    
    def _fact_exists(self, fact: KGFact) -> bool:
        """检查事实是否已存在"""
        for existing_fact in self.facts:
            if (existing_fact.subject == fact.subject and
                existing_fact.predicate == fact.predicate and
                existing_fact.object == fact.object):
                return True
        return False
    
    def _update_fact_index(self, fact: KGFact, fact_id: int):
        """更新事实索引"""
        # 为主语建立索引
        if fact.subject not in self.fact_index:
            self.fact_index[fact.subject] = []
        self.fact_index[fact.subject].append(fact_id)
        
        # 为宾语建立索引
        if fact.object not in self.fact_index:
            self.fact_index[fact.object] = []
        self.fact_index[fact.object].append(fact_id)
        
        # 为关系建立索引
        if fact.predicate not in self.fact_index:
            self.fact_index[fact.predicate] = []
        self.fact_index[fact.predicate].append(fact_id)
    
    def get_facts_about_entity(self, entity: str) -> List[KGFact]:
        """获取关于特定实体的所有事实"""
        entity = self._normalize_entity(entity)
        fact_ids = self.fact_index.get(entity, [])
        return [self.facts[i] for i in fact_ids]
    
    def get_facts_by_relation(self, relation: str) -> List[KGFact]:
        """获取特定关系的所有事实"""
        relation = self._normalize_relation(relation)
        fact_ids = self.fact_index.get(relation, [])
        return [self.facts[i] for i in fact_ids]
    
    def get_neighbors(self, entity: str, relation: str = None) -> List[str]:
        """获取实体的邻居"""
        entity = self._normalize_entity(entity)
        neighbors = []
        
        if entity in self.graph:
            for neighbor in self.graph.neighbors(entity):
                if relation is None:
                    neighbors.append(neighbor)
                else:
                    # 检查是否有指定关系
                    edge_data = self.graph.get_edge_data(entity, neighbor)
                    if edge_data:
                        for edge in edge_data.values():
                            if edge.get('relation') == self._normalize_relation(relation):
                                neighbors.append(neighbor)
                                break
        
        return neighbors
    
    def save_to_file(self, filepath: str):
        """保存知识图谱到文件"""
        kg_data = {
            "kg_id": self.kg_id,
            "facts": [fact.to_dict() for fact in self.facts],
            "entities": list(self.entities),
            "relations": list(self.relations),
            "stats": {
                "num_facts": len(self.facts),
                "num_entities": len(self.entities),
                "num_relations": len(self.relations)
            }
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved knowledge graph to {filepath}")
    
    def load_from_file(self, filepath: str):
        """从文件加载知识图谱"""
        with open(filepath, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)
        
        # 清空现有数据
        self.graph.clear()
        self.facts.clear()
        self.fact_index.clear()
        self.entities.clear()
        self.relations.clear()
        
        # 加载事实
        for fact_data in kg_data.get("facts", []):
            fact = KGFact.from_dict(fact_data)
            self.add_fact(fact.subject, fact.predicate, fact.object, 
                         fact.confidence, fact.source)
        
        self.logger.info(f"Loaded knowledge graph from {filepath}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        return {
            "kg_id": self.kg_id,
            "num_facts": len(self.facts),
            "num_entities": len(self.entities),
            "num_relations": len(self.relations),
            "entities": list(self.entities),
            "relations": list(self.relations)
        }
