#!/usr/bin/env python3
"""
Simple architecture validation script for KGRL research framework.

Validates the new architecture without external dependencies.
"""

import sys
import tempfile
import yaml
import json
from pathlib import Path


def test_directory_structure():
    """Test that the new directory structure exists."""
    print("🔍 Testing directory structure...")
    
    base_path = Path(__file__).parent
    
    # Check main directories
    required_dirs = [
        "src", "configs", "experiments", "scripts", "tests", "docs"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            raise AssertionError(f"Missing directory: {dir_name}")
        print(f"  ✅ {dir_name}/")
    
    # Check src subdirectories
    src_subdirs = [
        "agents", "knowledge", "reasoning", "rl", "integration", "evaluation", "utils"
    ]
    
    for subdir in src_subdirs:
        subdir_path = base_path / "src" / subdir
        if not subdir_path.exists():
            raise AssertionError(f"Missing src subdirectory: {subdir}")
        print(f"  ✅ src/{subdir}/")
    
    # Check config subdirectories
    config_subdirs = ["agents", "environments", "experiments", "modes"]
    
    for subdir in config_subdirs:
        subdir_path = base_path / "configs" / subdir
        if not subdir_path.exists():
            raise AssertionError(f"Missing config subdirectory: {subdir}")
        print(f"  ✅ configs/{subdir}/")
    
    print("✅ Directory structure validation passed")


def test_configuration_files():
    """Test that configuration files are valid."""
    print("🔍 Testing configuration files...")
    
    base_path = Path(__file__).parent
    config_path = base_path / "configs"
    
    # Test agent configurations
    agent_configs = list((config_path / "agents").glob("*.yaml"))
    if len(agent_configs) == 0:
        raise AssertionError("No agent configuration files found")
    
    for config_file in agent_configs:
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ["agent_name", "agent_type", "capabilities"]
            for field in required_fields:
                if field not in config:
                    raise AssertionError(f"Missing field '{field}' in {config_file.name}")
            
            print(f"  ✅ {config_file.name}")
        except Exception as e:
            raise AssertionError(f"Invalid config file {config_file.name}: {e}")
    
    # Test experiment configurations
    exp_configs = list((config_path / "experiments").glob("*.yaml"))
    if len(exp_configs) == 0:
        raise AssertionError("No experiment configuration files found")
    
    for config_file in exp_configs:
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ["experiment_name", "experiment_type"]
            for field in required_fields:
                if field not in config:
                    raise AssertionError(f"Missing field '{field}' in {config_file.name}")
            
            print(f"  ✅ {config_file.name}")
        except Exception as e:
            raise AssertionError(f"Invalid config file {config_file.name}: {e}")
    
    print("✅ Configuration files validation passed")


def test_package_structure():
    """Test that the package can be imported correctly."""
    print("🔍 Testing package structure...")

    base_path = Path(__file__).parent
    src_path = base_path / "src"

    # Check __init__.py files exist
    init_files = [
        src_path / "__init__.py",
        src_path / "agents" / "__init__.py",
        src_path / "knowledge" / "__init__.py",
        src_path / "integration" / "__init__.py"
    ]

    for init_file in init_files:
        if not init_file.exists():
            raise AssertionError(f"Missing __init__.py: {init_file}")
        print(f"  ✅ {init_file.relative_to(base_path)}")

    # Test basic imports with proper path setup
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        # Test individual module files exist and can be imported
        from agents.base_agent import BaseAgent
        print("  ✅ BaseAgent imported")

        from knowledge.graph_manager import GraphManager
        print("  ✅ GraphManager imported")

        print("  ✅ Core modules imported successfully")
    except ImportError as e:
        raise AssertionError(f"Failed to import core modules: {e}")

    print("✅ Package structure validation passed")


def test_agent_creation():
    """Test that agents can be created."""
    print("🔍 Testing agent creation...")

    base_path = Path(__file__).parent
    src_path = base_path / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from agents.unified_agent import UnifiedAgent
        from agents.base_agent import AgentStatistics
        
        # Create test configuration
        config = {
            "agent_name": "test_agent",
            "agent_type": "UnifiedAgent",
            "llm": {
                "model_name": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 512
            },
            "capabilities": {
                "use_knowledge_graph": False,
                "use_memory": False,
                "use_enhanced_reasoning": False,
                "use_rl": False
            }
        }
        
        # Create agent
        agent = UnifiedAgent("test_agent", config)
        print("  ✅ UnifiedAgent created")
        
        # Validate agent properties
        assert agent.name == "test_agent"
        assert hasattr(agent, 'enabled_capabilities')
        assert hasattr(agent, 'stats')
        assert isinstance(agent.stats, AgentStatistics)
        print("  ✅ Agent properties validated")
        
        # Test basic functionality
        observation = "You are in a test room."
        actions = ["examine room", "go north", "take item"]
        
        # This should not crash
        action = agent.act(observation, actions)
        assert action in actions
        print(f"  ✅ Agent action: {action}")
        
        # Test statistics
        stats = agent.get_statistics()
        assert isinstance(stats, dict)
        assert "total_actions" in stats
        assert stats["total_actions"] == 1
        print("  ✅ Agent statistics working")
        
        # Cleanup
        agent.cleanup()
        print("  ✅ Agent cleanup completed")
        
    except Exception as e:
        raise AssertionError(f"Agent creation failed: {e}")
    
    print("✅ Agent creation validation passed")


def test_knowledge_graph():
    """Test knowledge graph components."""
    print("🔍 Testing knowledge graph...")

    base_path = Path(__file__).parent
    src_path = base_path / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from knowledge.graph_manager import GraphManager, GraphNode, GraphEdge
        
        # Create graph manager
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "backend": "networkx",
                "storage_path": temp_dir,
                "enable_versioning": False
            }
            
            graph_manager = GraphManager(config)
            print("  ✅ GraphManager created")
            
            # Test adding nodes and edges
            node1 = GraphNode("entity1", "item", {"name": "key"})
            node2 = GraphNode("entity2", "location", {"name": "room"})
            
            assert graph_manager.backend.add_node(node1)
            assert graph_manager.backend.add_node(node2)
            print("  ✅ Nodes added")
            
            edge = GraphEdge("entity1", "entity2", "located_in", {"confidence": 0.9})
            assert graph_manager.backend.add_edge(edge)
            print("  ✅ Edge added")
            
            # Test retrieval
            retrieved_node = graph_manager.backend.get_node("entity1")
            assert retrieved_node is not None
            assert retrieved_node.id == "entity1"
            print("  ✅ Node retrieval working")
            
            # Test neighbors
            neighbors = graph_manager.backend.get_neighbors("entity1")
            assert "entity2" in neighbors
            print("  ✅ Neighbor retrieval working")
            
            # Test statistics
            stats = graph_manager.get_statistics()
            assert isinstance(stats, dict)
            assert "num_nodes" in stats
            assert stats["num_nodes"] >= 2
            print("  ✅ Graph statistics working")
            
            # Cleanup
            graph_manager.cleanup()
            print("  ✅ Graph cleanup completed")
        
    except Exception as e:
        raise AssertionError(f"Knowledge graph test failed: {e}")
    
    print("✅ Knowledge graph validation passed")


def test_end_to_end_workflow():
    """Test a complete end-to-end workflow."""
    print("🔍 Testing end-to-end workflow...")

    base_path = Path(__file__).parent
    src_path = base_path / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from agents.unified_agent import UnifiedAgent
        
        # Create agent configuration
        config = {
            "agent_name": "e2e_test",
            "agent_type": "UnifiedAgent",
            "llm": {
                "model_name": "gpt-4o",
                "temperature": 0.7
            },
            "capabilities": {
                "use_knowledge_graph": False,
                "use_memory": False,
                "use_enhanced_reasoning": False,
                "use_rl": False
            }
        }
        
        # Create agent
        agent = UnifiedAgent("e2e_test", config)
        print("  ✅ Agent created for E2E test")
        
        # Simulate a simple episode
        observations = [
            "You are in a room with a key on the table.",
            "You picked up the key. There is a locked door.",
            "You used the key on the door. The door is now open."
        ]
        
        actions_list = [
            ["examine room", "take key", "look around"],
            ["examine door", "use key on door", "go through door"],
            ["go through door", "examine new room", "celebrate"]
        ]
        
        episode_actions = []
        
        for i, (obs, available_actions) in enumerate(zip(observations, actions_list)):
            action = agent.act(obs, available_actions)
            episode_actions.append(action)
            
            # Simulate reward
            agent.update_reward(1.0 if i == len(observations) - 1 else 0.1)
            print(f"  ✅ Step {i+1}: {action}")
        
        # Check episode completed
        assert len(episode_actions) == 3
        print("  ✅ Episode completed")
        
        # Check statistics
        stats = agent.get_statistics()
        print(f"  📊 Stats: {stats}")
        assert stats["total_actions"] == 3, f"Expected 3 actions, got {stats['total_actions']}"
        assert stats["total_reward"] > 0, f"Expected positive reward, got {stats['total_reward']}"
        print("  ✅ Statistics updated correctly")

        # Reset for new episode
        agent.reset()

        # Check reset worked
        new_stats = agent.get_statistics()
        print(f"  📊 New stats after reset: {new_stats}")
        # After reset, episodes should be incremented
        assert new_stats["total_episodes"] >= 1, f"Expected episodes >= 1, got {new_stats['total_episodes']}"
        print("  ✅ Agent reset working")
        
        # Cleanup
        agent.cleanup()
        print("  ✅ E2E cleanup completed")
        
    except Exception as e:
        raise AssertionError(f"End-to-end workflow failed: {e}")
    
    print("✅ End-to-end workflow validation passed")


def test_file_existence():
    """Test that required files exist."""
    print("🔍 Testing file existence...")
    
    base_path = Path(__file__).parent
    
    required_files = [
        "README.md",
        "requirements.txt", 
        "setup.py",
        "docs/README.md",
        "docs/architecture/overview.md",
        "docs/tutorials/quickstart.md",
        "scripts/train/train_unified.py"
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            raise AssertionError(f"Missing required file: {file_path}")
        print(f"  ✅ {file_path}")
    
    print("✅ File existence validation passed")


def main():
    """Run all validation tests."""
    print("🧪 KGRL Architecture Validation")
    print("=" * 50)
    
    tests = [
        test_directory_structure,
        test_file_existence,
        test_configuration_files,
        test_package_structure,
        test_agent_creation,
        test_knowledge_graph,
        test_end_to_end_workflow,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All architecture validation tests passed!")
        print("✅ New KGRL architecture is ready for use")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
