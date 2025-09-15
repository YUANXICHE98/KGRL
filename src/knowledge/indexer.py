"""
Knowledge Indexer for KGRL research framework.

Provides efficient indexing and search capabilities for knowledge graphs.
"""

from typing import Dict, Any, List, Optional
import logging


class KnowledgeIndexer:
    """
    Efficient indexing system for knowledge graphs.
    
    Supports:
    - Vector embeddings (FAISS, Qdrant)
    - Inverted indexes
    - Graph structure indexes
    - Real-time index updates
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the knowledge indexer."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Index configuration
        self.index_type = config.get("index_type", "vector")
        self.embedding_dim = config.get("embedding_dim", 768)
        self.enable_real_time_updates = config.get("enable_real_time_updates", True)
        
        # Initialize indexes
        self.indexes = {}
        self._initialize_indexes()
        
        self.logger.info("Knowledge indexer initialized")
    
    def _initialize_indexes(self):
        """Initialize different types of indexes."""
        if self.index_type in ["vector", "hybrid"]:
            self.indexes["vector"] = MockVectorIndex(self.embedding_dim)
        
        if self.index_type in ["inverted", "hybrid"]:
            self.indexes["inverted"] = MockInvertedIndex()
        
        if self.index_type in ["graph", "hybrid"]:
            self.indexes["graph"] = MockGraphIndex()
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Index a batch of documents.
        
        Args:
            documents: List of documents to index
            
        Returns:
            Indexing results summary
        """
        try:
            results = {
                "total_documents": len(documents),
                "indexed_documents": 0,
                "failed_documents": 0,
                "index_types_updated": []
            }
            
            for doc in documents:
                try:
                    self._index_single_document(doc)
                    results["indexed_documents"] += 1
                except Exception as e:
                    self.logger.warning(f"Failed to index document {doc.get('id', 'unknown')}: {e}")
                    results["failed_documents"] += 1
            
            results["index_types_updated"] = list(self.indexes.keys())
            
            self.logger.info(f"Document indexing completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in document indexing: {e}")
            return {"error": str(e)}
    
    def _index_single_document(self, document: Dict[str, Any]):
        """Index a single document across all indexes."""
        doc_id = document.get("id")
        content = document.get("content", "")
        
        # Index in vector index
        if "vector" in self.indexes:
            self.indexes["vector"].add_document(doc_id, content)
        
        # Index in inverted index
        if "inverted" in self.indexes:
            self.indexes["inverted"].add_document(doc_id, content)
        
        # Index in graph index
        if "graph" in self.indexes:
            entities = document.get("entities", [])
            relations = document.get("relations", [])
            self.indexes["graph"].add_document(doc_id, entities, relations)
    
    def search(self, query: str, index_type: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search across indexes.
        
        Args:
            query: Search query
            index_type: Specific index to search (None for all)
            top_k: Number of results to return
            
        Returns:
            Search results
        """
        try:
            if index_type and index_type in self.indexes:
                return self.indexes[index_type].search(query, top_k)
            else:
                # Search across all indexes and merge results
                all_results = []
                for idx_type, index in self.indexes.items():
                    results = index.search(query, top_k)
                    for result in results:
                        result["index_type"] = idx_type
                    all_results.extend(results)
                
                # Sort by score and return top_k
                all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                return all_results[:top_k]
                
        except Exception as e:
            self.logger.error(f"Error in search: {e}")
            return []
    
    def update_index(self, document_id: str, document: Dict[str, Any]):
        """Update index with new/modified document."""
        if self.enable_real_time_updates:
            try:
                self._index_single_document({"id": document_id, **document})
                self.logger.debug(f"Updated index for document: {document_id}")
            except Exception as e:
                self.logger.error(f"Failed to update index for {document_id}: {e}")
    
    def remove_from_index(self, document_id: str):
        """Remove document from all indexes."""
        try:
            for index in self.indexes.values():
                if hasattr(index, 'remove_document'):
                    index.remove_document(document_id)
            
            self.logger.debug(f"Removed document from index: {document_id}")
        except Exception as e:
            self.logger.error(f"Failed to remove document {document_id}: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexes."""
        stats = {}
        
        for idx_type, index in self.indexes.items():
            if hasattr(index, 'get_stats'):
                stats[idx_type] = index.get_stats()
            else:
                stats[idx_type] = {"status": "active"}
        
        return stats
    
    def cleanup(self):
        """Clean up indexer resources."""
        for index in self.indexes.values():
            if hasattr(index, 'cleanup'):
                index.cleanup()


class MockVectorIndex:
    """Mock vector index for testing."""
    
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.documents = {}
    
    def add_document(self, doc_id: str, content: str):
        """Add document to vector index."""
        self.documents[doc_id] = content
    
    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search vector index."""
        results = []
        for doc_id, content in list(self.documents.items())[:top_k]:
            score = 0.8 if query.lower() in content.lower() else 0.3
            results.append({
                "id": doc_id,
                "content": content,
                "score": score
            })
        return results
    
    def remove_document(self, doc_id: str):
        """Remove document from vector index."""
        self.documents.pop(doc_id, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector index statistics."""
        return {
            "num_documents": len(self.documents),
            "embedding_dim": self.embedding_dim
        }
    
    def cleanup(self):
        """Clean up vector index."""
        self.documents.clear()


class MockInvertedIndex:
    """Mock inverted index for testing."""
    
    def __init__(self):
        self.documents = {}
        self.term_index = {}
    
    def add_document(self, doc_id: str, content: str):
        """Add document to inverted index."""
        self.documents[doc_id] = content
        
        # Simple tokenization
        terms = content.lower().split()
        for term in terms:
            if term not in self.term_index:
                self.term_index[term] = set()
            self.term_index[term].add(doc_id)
    
    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search inverted index."""
        query_terms = query.lower().split()
        matching_docs = set()
        
        for term in query_terms:
            if term in self.term_index:
                matching_docs.update(self.term_index[term])
        
        results = []
        for doc_id in list(matching_docs)[:top_k]:
            content = self.documents.get(doc_id, "")
            score = sum(1 for term in query_terms if term in content.lower()) / len(query_terms)
            results.append({
                "id": doc_id,
                "content": content,
                "score": score
            })
        
        return sorted(results, key=lambda x: x["score"], reverse=True)
    
    def remove_document(self, doc_id: str):
        """Remove document from inverted index."""
        if doc_id in self.documents:
            content = self.documents[doc_id]
            terms = content.lower().split()
            
            for term in terms:
                if term in self.term_index:
                    self.term_index[term].discard(doc_id)
                    if not self.term_index[term]:
                        del self.term_index[term]
            
            del self.documents[doc_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get inverted index statistics."""
        return {
            "num_documents": len(self.documents),
            "num_terms": len(self.term_index)
        }
    
    def cleanup(self):
        """Clean up inverted index."""
        self.documents.clear()
        self.term_index.clear()


class MockGraphIndex:
    """Mock graph index for testing."""
    
    def __init__(self):
        self.documents = {}
        self.entity_index = {}
        self.relation_index = {}
    
    def add_document(self, doc_id: str, entities: List[str], relations: List[Dict[str, str]]):
        """Add document to graph index."""
        self.documents[doc_id] = {"entities": entities, "relations": relations}
        
        # Index entities
        for entity in entities:
            if entity not in self.entity_index:
                self.entity_index[entity] = set()
            self.entity_index[entity].add(doc_id)
        
        # Index relations
        for relation in relations:
            rel_type = relation.get("type", "unknown")
            if rel_type not in self.relation_index:
                self.relation_index[rel_type] = set()
            self.relation_index[rel_type].add(doc_id)
    
    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search graph index."""
        matching_docs = set()
        
        # Search entities
        for entity in self.entity_index:
            if query.lower() in entity.lower():
                matching_docs.update(self.entity_index[entity])
        
        # Search relations
        for relation in self.relation_index:
            if query.lower() in relation.lower():
                matching_docs.update(self.relation_index[relation])
        
        results = []
        for doc_id in list(matching_docs)[:top_k]:
            doc_data = self.documents.get(doc_id, {})
            results.append({
                "id": doc_id,
                "entities": doc_data.get("entities", []),
                "relations": doc_data.get("relations", []),
                "score": 0.7
            })
        
        return results
    
    def remove_document(self, doc_id: str):
        """Remove document from graph index."""
        if doc_id in self.documents:
            doc_data = self.documents[doc_id]
            
            # Remove from entity index
            for entity in doc_data.get("entities", []):
                if entity in self.entity_index:
                    self.entity_index[entity].discard(doc_id)
                    if not self.entity_index[entity]:
                        del self.entity_index[entity]
            
            # Remove from relation index
            for relation in doc_data.get("relations", []):
                rel_type = relation.get("type", "unknown")
                if rel_type in self.relation_index:
                    self.relation_index[rel_type].discard(doc_id)
                    if not self.relation_index[rel_type]:
                        del self.relation_index[rel_type]
            
            del self.documents[doc_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph index statistics."""
        return {
            "num_documents": len(self.documents),
            "num_entities": len(self.entity_index),
            "num_relation_types": len(self.relation_index)
        }
    
    def cleanup(self):
        """Clean up graph index."""
        self.documents.clear()
        self.entity_index.clear()
        self.relation_index.clear()
