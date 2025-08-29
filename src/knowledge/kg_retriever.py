"""
知识图谱检索器
用于从知识图谱中检索相关信息
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .kg_builder import KnowledgeGraphBuilder, KGFact
from ..utils.logger import get_logger

class KnowledgeGraphRetriever:
    """知识图谱检索器"""
    
    def __init__(self, kg_builder: KnowledgeGraphBuilder, retriever_id: str = "default"):
        self.kg_builder = kg_builder
        self.retriever_id = retriever_id
        self.logger = get_logger(f"KGRetriever_{retriever_id}")
        
        # 检索配置
        self.max_results = 10
        self.min_confidence = 0.1
        self.similarity_threshold = 0.3
        
        # TF-IDF向量化器（用于语义检索）
        self.vectorizer = None
        self.fact_vectors = None
        self._build_tfidf_index()
        
        self.logger.info(f"Initialized KnowledgeGraphRetriever: {retriever_id}")
    
    def build_index(self, facts: List[KGFact]):
        """使用外部提供的facts构建索引"""
        self.facts = facts
        self._build_tfidf_index_from_facts(facts)

    def _build_tfidf_index(self):
        """构建TF-IDF索引用于语义检索"""
        if not self.kg_builder.facts:
            self.logger.warning("No facts available for TF-IDF indexing")
            return
        self._build_tfidf_index_from_facts(self.kg_builder.facts)

    def _build_tfidf_index_from_facts(self, facts: List[KGFact]):
        """从facts列表构建TF-IDF索引"""
        if not facts:
            self.logger.warning("No facts available for TF-IDF indexing")
            return
        
        # 将事实转换为文本
        fact_texts = []
        for fact in facts:
            text = f"{fact.subject} {fact.predicate} {fact.object}"
            fact_texts.append(text)
        
        # 构建TF-IDF向量
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
        
        try:
            self.fact_vectors = self.vectorizer.fit_transform(fact_texts)
            self.logger.info(f"Built TF-IDF index for {len(fact_texts)} facts")
        except Exception as e:
            self.logger.error(f"Error building TF-IDF index: {e}")
            self.vectorizer = None
            self.fact_vectors = None
    
    def retrieve_by_keywords(self, query: str, max_results: int = None) -> List[KGFact]:
        """
        基于关键词检索相关事实
        
        Args:
            query: 查询字符串
            max_results: 最大结果数
            
        Returns:
            (事实, 相关性分数) 的列表
        """
        max_results = max_results or self.max_results
        query_lower = query.lower()
        
        # 提取查询中的关键词
        keywords = self._extract_keywords(query_lower)
        
        results = []
        for fact in self.kg_builder.facts:
            score = self._calculate_keyword_score(fact, keywords)
            if score > 0:
                results.append((fact, score))
        
        # 按分数排序并返回top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return [fact for fact, score in results[:max_results]]
    
    def retrieve_by_entity(self, entity: str, max_results: int = None) -> List[Tuple[KGFact, float]]:
        """
        检索关于特定实体的事实
        
        Args:
            entity: 实体名称
            max_results: 最大结果数
            
        Returns:
            (事实, 相关性分数) 的列表
        """
        max_results = max_results or self.max_results
        entity_normalized = self.kg_builder._normalize_entity(entity)
        
        facts = self.kg_builder.get_facts_about_entity(entity_normalized)
        
        # 为每个事实分配分数（基于置信度）
        results = [(fact, fact.confidence) for fact in facts]
        
        # 按分数排序并返回top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
    
    def retrieve_by_relation(self, relation: str, max_results: int = None) -> List[Tuple[KGFact, float]]:
        """
        检索特定关系的事实
        
        Args:
            relation: 关系名称
            max_results: 最大结果数
            
        Returns:
            (事实, 相关性分数) 的列表
        """
        max_results = max_results or self.max_results
        relation_normalized = self.kg_builder._normalize_relation(relation)
        
        facts = self.kg_builder.get_facts_by_relation(relation_normalized)
        
        # 为每个事实分配分数（基于置信度）
        results = [(fact, fact.confidence) for fact in facts]
        
        # 按分数排序并返回top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
    
    def retrieve_by_similarity(self, query: str, max_results: int = None) -> List[Tuple[KGFact, float]]:
        """
        基于语义相似度检索事实
        
        Args:
            query: 查询字符串
            max_results: 最大结果数
            
        Returns:
            (事实, 相似度分数) 的列表
        """
        max_results = max_results or self.max_results
        
        if self.vectorizer is None or self.fact_vectors is None:
            self.logger.warning("TF-IDF index not available, falling back to keyword search")
            return self.retrieve_by_keywords(query, max_results)
        
        try:
            # 将查询转换为向量
            query_vector = self.vectorizer.transform([query])
            
            # 计算相似度
            similarities = cosine_similarity(query_vector, self.fact_vectors).flatten()
            
            # 获取相似度大于阈值的结果
            results = []
            for i, similarity in enumerate(similarities):
                if similarity > self.similarity_threshold:
                    results.append((self.kg_builder.facts[i], similarity))
            
            # 按相似度排序并返回top-k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error in similarity search: {e}")
            return self.retrieve_by_keywords(query, max_results)
    
    def retrieve_hybrid(self, query: str, max_results: int = None) -> List[Tuple[KGFact, float]]:
        """
        混合检索：结合关键词和语义相似度
        
        Args:
            query: 查询字符串
            max_results: 最大结果数
            
        Returns:
            (事实, 综合分数) 的列表
        """
        max_results = max_results or self.max_results
        
        # 获取关键词检索结果
        keyword_results = self.retrieve_by_keywords(query, max_results * 2)
        keyword_scores = {str(fact): score for fact, score in keyword_results}
        
        # 获取语义检索结果
        similarity_results = self.retrieve_by_similarity(query, max_results * 2)
        similarity_scores = {str(fact): score for fact, score in similarity_results}
        
        # 合并结果
        all_facts = set()
        for fact, _ in keyword_results:
            all_facts.add(fact)
        for fact, _ in similarity_results:
            all_facts.add(fact)
        
        # 计算综合分数
        results = []
        for fact in all_facts:
            fact_str = str(fact)
            keyword_score = keyword_scores.get(fact_str, 0)
            similarity_score = similarity_scores.get(fact_str, 0)
            
            # 加权组合分数
            combined_score = 0.6 * keyword_score + 0.4 * similarity_score
            results.append((fact, combined_score))
        
        # 按综合分数排序并返回top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
    
    def retrieve_contextual(self, query: str, context: List[str] = None, max_results: int = None) -> List[Tuple[KGFact, float]]:
        """
        基于上下文的检索
        
        Args:
            query: 查询字符串
            context: 上下文信息列表
            max_results: 最大结果数
            
        Returns:
            (事实, 相关性分数) 的列表
        """
        max_results = max_results or self.max_results
        
        # 如果有上下文，将其与查询结合
        if context:
            extended_query = query + " " + " ".join(context)
        else:
            extended_query = query
        
        # 使用混合检索
        return self.retrieve_hybrid(extended_query, max_results)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取：移除停用词，提取名词性短语
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        
        # 分词并过滤
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_keyword_score(self, fact: KGFact, keywords: List[str]) -> float:
        """计算事实与关键词的匹配分数"""
        fact_text = f"{fact.subject} {fact.predicate} {fact.object}".lower()
        
        score = 0.0
        for keyword in keywords:
            if keyword in fact_text:
                # 精确匹配得分更高
                if keyword in fact.subject.lower():
                    score += 1.0
                elif keyword in fact.object.lower():
                    score += 0.8
                elif keyword in fact.predicate.lower():
                    score += 0.6
                else:
                    score += 0.3
        
        # 考虑事实的置信度
        score *= fact.confidence
        
        return score
    
    def format_results(self, results: List[Tuple[KGFact, float]], include_scores: bool = False) -> str:
        """
        格式化检索结果为文本
        
        Args:
            results: 检索结果
            include_scores: 是否包含分数
            
        Returns:
            格式化的文本
        """
        if not results:
            return "No relevant information found."
        
        formatted_lines = []
        for i, (fact, score) in enumerate(results, 1):
            if include_scores:
                line = f"{i}. {fact.subject} {fact.predicate} {fact.object} (score: {score:.3f})"
            else:
                line = f"{i}. {fact.subject} {fact.predicate} {fact.object}"
            formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    def retrieve_by_dodaf_type(self, dodaf_type: str, query: str = None, max_results: int = None) -> List[KGFact]:
        """
        按DODAF类型检索事实

        Args:
            dodaf_type: DODAF类型 (DO/DA/F)
            query: 可选的查询字符串
            max_results: 最大结果数

        Returns:
            匹配的事实列表
        """
        max_results = max_results or self.max_results

        # 筛选指定DODAF类型的事实
        filtered_facts = []
        for fact in self.kg_builder.facts:
            if hasattr(fact, 'dodaf_type') and fact.dodaf_type == dodaf_type:
                filtered_facts.append(fact)

        # 如果有查询字符串，进一步筛选
        if query:
            query_lower = query.lower()
            keywords = self._extract_keywords(query_lower)

            scored_facts = []
            for fact in filtered_facts:
                score = self._calculate_keyword_score(fact, keywords)
                if score > 0:
                    scored_facts.append((fact, score))

            # 按分数排序
            scored_facts.sort(key=lambda x: x[1], reverse=True)
            return [fact for fact, score in scored_facts[:max_results]]

        return filtered_facts[:max_results]

    def query_kg(self, query_type: str, query: str, max_results: int = 3) -> List[KGFact]:
        """
        统一的KG查询接口 - 支持ReAct框架调用

        Args:
            query_type: 查询类型 (keywords/dodaf/entity)
            query: 查询内容
            max_results: 最大结果数

        Returns:
            匹配的事实列表
        """
        if query_type == "keywords":
            return self.retrieve_by_keywords(query, max_results)
        elif query_type == "dodaf":
            # 解析DODAF查询: "DO:take key" 或 "DA:kitchen"
            if ":" in query:
                dodaf_type, content = query.split(":", 1)
                return self.retrieve_by_dodaf_type(dodaf_type.strip(), content.strip(), max_results)
            else:
                return self.retrieve_by_keywords(query, max_results)
        elif query_type == "entity":
            results = self.retrieve_by_entity(query, max_results)
            return [fact for fact, score in results]
        else:
            return self.retrieve_by_keywords(query, max_results)

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        return {
            "retriever_id": self.retriever_id,
            "total_facts": len(self.kg_builder.facts),
            "has_tfidf_index": self.vectorizer is not None,
            "max_results": self.max_results,
            "similarity_threshold": self.similarity_threshold
        }
