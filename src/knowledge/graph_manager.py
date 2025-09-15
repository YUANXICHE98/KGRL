"""
Graph Manager for KGRL research framework.

Provides core knowledge graph storage, management, and operations.
Supports multiple backends (Neo4j, NetworkX, etc.) and handles
graph persistence, versioning, and basic CRUD operations.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import logging
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import networkx as nx


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    id: str
    type: str
    properties: Dict[str, Any]
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph."""
    source: str
    target: str
    relation: str
    properties: Dict[str, Any]
    confidence: float = 1.0
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class GraphTriple:
    """Represents a knowledge triple (subject, predicate, object)."""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: str = "unknown"
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class GraphBackend(ABC):
    """Abstract base class for graph storage backends."""
    
    @abstractmethod
    def add_node(self, node: GraphNode) -> bool:
        """Add a node to the graph."""
        pass
    
    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> bool:
        """Add an edge to the graph."""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str, relation: Optional[str] = None) -> List[str]:
        """Get neighboring nodes."""
        pass
    
    @abstractmethod
    def query_nodes(self, filters: Dict[str, Any]) -> List[GraphNode]:
        """Query nodes with filters."""
        pass
    
    @abstractmethod
    def query_edges(self, filters: Dict[str, Any]) -> List[GraphEdge]:
        """Query edges with filters."""
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """Delete a node."""
        pass
    
    @abstractmethod
    def delete_edge(self, source: str, target: str, relation: str) -> bool:
        """Delete an edge."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        pass


class NetworkXBackend(GraphBackend):
    """NetworkX-based graph backend for in-memory operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.graph = nx.MultiDiGraph()
        self.logger = logging.getLogger("graph.networkx")
        
        # Node and edge storage
        self.nodes = {}  # node_id -> GraphNode
        self.edges = {}  # (source, target, relation) -> GraphEdge
    
    def add_node(self, node: GraphNode) -> bool:
        """Add a node to the graph."""
        try:
            self.graph.add_node(node.id, **node.properties)
            self.nodes[node.id] = node
            return True
        except Exception as e:
            self.logger.error(f"Failed to add node {node.id}: {e}")
            return False
    
    def add_edge(self, edge: GraphEdge) -> bool:
        """Add an edge to the graph."""
        try:
            # Prepare edge attributes, avoiding conflicts with NetworkX parameters
            edge_attrs = {
                "relation": edge.relation,
                "edge_confidence": edge.confidence,  # Rename to avoid conflict
                **edge.properties
            }

            self.graph.add_edge(
                edge.source,
                edge.target,
                key=edge.relation,
                **edge_attrs
            )
            self.edges[(edge.source, edge.target, edge.relation)] = edge
            return True
        except Exception as e:
            self.logger.error(f"Failed to add edge {edge.source}->{edge.target}: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, relation: Optional[str] = None) -> List[str]:
        """Get neighboring nodes."""
        if node_id not in self.graph:
            return []
        
        neighbors = []
        
        # Outgoing edges
        for target in self.graph.successors(node_id):
            if relation is None:
                neighbors.append(target)
            else:
                edge_data = self.graph.get_edge_data(node_id, target)
                if edge_data and any(data.get('relation') == relation for data in edge_data.values()):
                    neighbors.append(target)
        
        # Incoming edges
        for source in self.graph.predecessors(node_id):
            if relation is None:
                neighbors.append(source)
            else:
                edge_data = self.graph.get_edge_data(source, node_id)
                if edge_data and any(data.get('relation') == relation for data in edge_data.values()):
                    neighbors.append(source)
        
        return list(set(neighbors))  # Remove duplicates
    
    def query_nodes(self, filters: Dict[str, Any]) -> List[GraphNode]:
        """Query nodes with filters."""
        results = []
        
        for node_id, node in self.nodes.items():
            match = True
            
            for key, value in filters.items():
                if key == "type" and node.type != value:
                    match = False
                    break
                elif key in node.properties and node.properties[key] != value:
                    match = False
                    break
            
            if match:
                results.append(node)
        
        return results
    
    def query_edges(self, filters: Dict[str, Any]) -> List[GraphEdge]:
        """Query edges with filters."""
        results = []
        
        for edge_key, edge in self.edges.items():
            match = True
            
            for key, value in filters.items():
                if key == "relation" and edge.relation != value:
                    match = False
                    break
                elif key == "source" and edge.source != value:
                    match = False
                    break
                elif key == "target" and edge.target != value:
                    match = False
                    break
                elif key in edge.properties and edge.properties[key] != value:
                    match = False
                    break
            
            if match:
                results.append(edge)
        
        return results
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node."""
        try:
            if node_id in self.graph:
                self.graph.remove_node(node_id)
            if node_id in self.nodes:
                del self.nodes[node_id]
            
            # Remove related edges
            edges_to_remove = []
            for edge_key in self.edges:
                if edge_key[0] == node_id or edge_key[1] == node_id:
                    edges_to_remove.append(edge_key)
            
            for edge_key in edges_to_remove:
                del self.edges[edge_key]
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete node {node_id}: {e}")
            return False
    
    def delete_edge(self, source: str, target: str, relation: str) -> bool:
        """Delete an edge."""
        try:
            if self.graph.has_edge(source, target):
                edge_data = self.graph.get_edge_data(source, target)
                for key, data in edge_data.items():
                    if data.get('relation') == relation:
                        self.graph.remove_edge(source, target, key)
                        break
            
            edge_key = (source, target, relation)
            if edge_key in self.edges:
                del self.edges[edge_key]
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete edge {source}->{target}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph),
            "num_components": nx.number_weakly_connected_components(self.graph),
        }


class GraphManager:
    """
    Main graph manager that provides high-level graph operations.
    
    Handles graph persistence, versioning, and provides a unified
    interface for different graph backends.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the graph manager.
        
        Args:
            config: Configuration dictionary with backend and storage settings
        """
        self.config = config
        self.logger = logging.getLogger("graph.manager")
        
        # Initialize backend
        backend_type = config.get("backend", "networkx")
        if backend_type == "networkx":
            self.backend = NetworkXBackend(config)
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
        
        # Storage configuration
        self.storage_path = Path(config.get("storage_path", "data/kg"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Versioning
        self.enable_versioning = config.get("enable_versioning", True)
        self.current_version = 0
        
        # Load existing graph if available
        self._load_graph()
        
        self.logger.info(f"Graph manager initialized with {backend_type} backend")
    
    def add_triple(self, triple: GraphTriple) -> bool:
        """Add a knowledge triple to the graph."""
        # Create nodes if they don't exist
        subject_node = self.backend.get_node(triple.subject)
        if not subject_node:
            subject_node = GraphNode(
                id=triple.subject,
                type="entity",
                properties={"name": triple.subject}
            )
            self.backend.add_node(subject_node)
        
        object_node = self.backend.get_node(triple.object)
        if not object_node:
            object_node = GraphNode(
                id=triple.object,
                type="entity",
                properties={"name": triple.object}
            )
            self.backend.add_node(object_node)
        
        # Create edge
        edge = GraphEdge(
            source=triple.subject,
            target=triple.object,
            relation=triple.predicate,
            properties={
                "source": triple.source,
                "timestamp": triple.timestamp
            },
            confidence=triple.confidence
        )
        
        return self.backend.add_edge(edge)
    
    def get_related_entities(self, entity: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Get entities related to the given entity within max_depth."""
        visited = set()
        queue = [(entity, 0)]
        related = []
        
        while queue:
            current_entity, depth = queue.pop(0)
            
            if current_entity in visited or depth > max_depth:
                continue
            
            visited.add(current_entity)
            
            if depth > 0:  # Don't include the query entity itself
                node = self.backend.get_node(current_entity)
                if node:
                    related.append({
                        "entity": current_entity,
                        "type": node.type,
                        "properties": node.properties,
                        "depth": depth
                    })
            
            # Add neighbors to queue
            neighbors = self.backend.get_neighbors(current_entity)
            for neighbor in neighbors:
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
        
        return related
    
    def find_path(self, source: str, target: str, max_length: int = 5) -> List[List[str]]:
        """Find paths between two entities."""
        try:
            if hasattr(self.backend, 'graph'):
                # Use NetworkX path finding
                paths = list(nx.all_simple_paths(
                    self.backend.graph, 
                    source, 
                    target, 
                    cutoff=max_length
                ))
                return paths[:10]  # Limit to 10 paths
            else:
                # Implement basic BFS path finding
                return self._bfs_paths(source, target, max_length)
        except Exception as e:
            self.logger.error(f"Path finding failed: {e}")
            return []
    
    def _bfs_paths(self, source: str, target: str, max_length: int) -> List[List[str]]:
        """BFS-based path finding."""
        queue = [(source, [source])]
        paths = []
        
        while queue and len(paths) < 10:
            current, path = queue.pop(0)
            
            if len(path) > max_length:
                continue
            
            if current == target and len(path) > 1:
                paths.append(path)
                continue
            
            neighbors = self.backend.get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in path:  # Avoid cycles
                    queue.append((neighbor, path + [neighbor]))
        
        return paths
    
    def save_graph(self, version: Optional[int] = None) -> bool:
        """Save the current graph to storage."""
        try:
            if version is None:
                version = self.current_version + 1
            
            # Create snapshot
            snapshot = {
                "version": version,
                "timestamp": time.time(),
                "nodes": {node_id: {
                    "id": node.id,
                    "type": node.type,
                    "properties": node.properties,
                    "created_at": node.created_at,
                    "updated_at": node.updated_at
                } for node_id, node in self.backend.nodes.items()},
                "edges": {f"{edge.source}-{edge.target}-{edge.relation}": {
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation,
                    "properties": edge.properties,
                    "confidence": edge.confidence,
                    "created_at": edge.created_at,
                    "updated_at": edge.updated_at
                } for edge in self.backend.edges.values()},
                "statistics": self.backend.get_statistics()
            }
            
            # Save to file
            snapshot_file = self.storage_path / f"graph_v{version}.json"
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
            
            self.current_version = version
            self.logger.info(f"Graph saved as version {version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save graph: {e}")
            return False
    
    def _load_graph(self) -> bool:
        """Load the latest graph from storage."""
        try:
            # Find latest version
            snapshot_files = list(self.storage_path.glob("graph_v*.json"))
            if not snapshot_files:
                self.logger.info("No existing graph found, starting fresh")
                return True
            
            latest_file = max(snapshot_files, key=lambda f: int(f.stem.split('_v')[1]))
            
            with open(latest_file, 'r') as f:
                snapshot = json.load(f)
            
            # Restore nodes
            for node_data in snapshot["nodes"].values():
                node = GraphNode(**node_data)
                self.backend.add_node(node)
            
            # Restore edges
            for edge_data in snapshot["edges"].values():
                edge = GraphEdge(**edge_data)
                self.backend.add_edge(edge)
            
            self.current_version = snapshot["version"]
            self.logger.info(f"Graph loaded from version {self.current_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load graph: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        backend_stats = self.backend.get_statistics()
        
        return {
            **backend_stats,
            "current_version": self.current_version,
            "storage_path": str(self.storage_path),
            "backend_type": type(self.backend).__name__,
        }
    
    def cleanup(self):
        """Clean up resources."""
        if self.enable_versioning:
            self.save_graph()
        self.logger.info("Graph manager cleanup completed")
