"""
Architecture validation tests for KGRL research framework.

Tests the complete new architecture to ensure all components work together
and the system functions as expected.
"""

import sys
import pytest
import tempfile
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents import UnifiedAgent
from knowledge import GraphManager
from utils import ConfigLoader


class TestArchitectureValidation:
    """Test suite for validating the new KGRL architecture."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            
            # Create basic agent config
            agent_config = {
                "agent_name": "test_agent",
                "agent_type": "UnifiedAgent",
                "llm": {
                    "model_name": "gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 512
                },
                "capabilities": {
                    "use_knowledge_graph": True,
                    "use_memory": True,
                    "use_enhanced_reasoning": False,
                    "use_rl": False
                },
                "knowledge_graph": {
                    "storage": {
                        "backend": "networkx",
                        "storage_path": str(config_path / "kg_data")
                    }
                }
            }
            
            config_file = config_path / "test_agent.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(agent_config, f)
            
            yield str(config_file)
    
    def test_directory_structure(self):
        """Test that the new directory structure exists."""
        base_path = Path(__file__).parent.parent.parent
        
        # Check main directories
        assert (base_path / "src").exists()
        assert (base_path / "configs").exists()
        assert (base_path / "experiments").exists()
        assert (base_path / "scripts").exists()
        assert (base_path / "tests").exists()
        assert (base_path / "docs").exists()
        
        # Check src subdirectories
        src_path = base_path / "src"
        assert (src_path / "agents").exists()
        assert (src_path / "knowledge").exists()
        assert (src_path / "reasoning").exists()
        assert (src_path / "rl").exists()
        assert (src_path / "integration").exists()
        assert (src_path / "evaluation").exists()
        assert (src_path / "utils").exists()
        
        # Check config subdirectories
        config_path = base_path / "configs"
        assert (config_path / "agents").exists()
        assert (config_path / "environments").exists()
        assert (config_path / "experiments").exists()
        assert (config_path / "modes").exists()
        
        print("✅ Directory structure validation passed")
    
    def test_configuration_files(self):
        """Test that configuration files are valid."""
        base_path = Path(__file__).parent.parent.parent
        config_path = base_path / "configs"
        
        # Test agent configurations
        agent_configs = list((config_path / "agents").glob("*.yaml"))
        assert len(agent_configs) > 0, "No agent configuration files found"
        
        for config_file in agent_configs:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required fields
            assert "agent_name" in config
            assert "agent_type" in config
            assert "capabilities" in config
            
            print(f"✅ Agent config validated: {config_file.name}")
        
        # Test experiment configurations
        exp_configs = list((config_path / "experiments").glob("*.yaml"))
        assert len(exp_configs) > 0, "No experiment configuration files found"
        
        for config_file in exp_configs:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required fields
            assert "experiment_name" in config
            assert "experiment_type" in config
            
            print(f"✅ Experiment config validated: {config_file.name}")
    
    def test_agent_import_and_creation(self, temp_config_dir):
        """Test that agents can be imported and created."""
        # Test imports
        from agents import BaseAgent, UnifiedAgent
        from agents.base_agent import AgentStatistics
        
        # Load configuration
        with open(temp_config_dir, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create agent
        agent = UnifiedAgent("test_agent", config)
        
        # Validate agent properties
        assert agent.name == "test_agent"
        assert hasattr(agent, 'enabled_capabilities')
        assert hasattr(agent, 'stats')
        assert isinstance(agent.stats, AgentStatistics)
        
        # Test basic functionality
        observation = "You are in a test room."
        actions = ["examine room", "go north", "take item"]
        
        # This should not crash
        action = agent.act(observation, actions)
        assert action in actions
        
        # Test statistics
        stats = agent.get_statistics()
        assert isinstance(stats, dict)
        assert "total_actions" in stats
        assert stats["total_actions"] == 1
        
        # Cleanup
        agent.cleanup()
        
        print("✅ Agent creation and basic functionality validated")
    
    def test_knowledge_graph_integration(self):
        """Test knowledge graph components."""
        from knowledge import GraphManager
        from knowledge.graph_manager import GraphNode, GraphEdge, GraphTriple
        
        # Create graph manager
        config = {
            "backend": "networkx",
            "storage_path": "/tmp/test_kg",
            "enable_versioning": False
        }
        
        graph_manager = GraphManager(config)
        
        # Test adding nodes and edges
        node1 = GraphNode("entity1", "item", {"name": "key"})
        node2 = GraphNode("entity2", "location", {"name": "room"})
        
        assert graph_manager.backend.add_node(node1)
        assert graph_manager.backend.add_node(node2)
        
        edge = GraphEdge("entity1", "entity2", "located_in", {"confidence": 0.9})
        assert graph_manager.backend.add_edge(edge)
        
        # Test retrieval
        retrieved_node = graph_manager.backend.get_node("entity1")
        assert retrieved_node is not None
        assert retrieved_node.id == "entity1"
        
        # Test neighbors
        neighbors = graph_manager.backend.get_neighbors("entity1")
        assert "entity2" in neighbors
        
        # Test statistics
        stats = graph_manager.get_statistics()
        assert isinstance(stats, dict)
        assert "num_nodes" in stats
        assert stats["num_nodes"] >= 2
        
        # Cleanup
        graph_manager.cleanup()
        
        print("✅ Knowledge graph integration validated")
    
    def test_configuration_loading(self):
        """Test configuration loading utilities."""
        base_path = Path(__file__).parent.parent.parent
        
        # Test loading agent configuration
        agent_config_path = base_path / "configs" / "agents" / "llm_baseline.yaml"
        if agent_config_path.exists():
            with open(agent_config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            assert isinstance(config, dict)
            assert "agent_name" in config
            assert "capabilities" in config
            
            print("✅ Configuration loading validated")
        else:
            print("⚠️  Agent configuration file not found, skipping test")
    
    def test_script_executability(self):
        """Test that main scripts are executable."""
        base_path = Path(__file__).parent.parent.parent
        scripts_path = base_path / "scripts"
        
        # Check training scripts
        train_script = scripts_path / "train" / "train_unified.py"
        if train_script.exists():
            assert train_script.is_file()
            # Check if it's executable (has shebang or can be run with python)
            with open(train_script, 'r') as f:
                first_line = f.readline()
            assert first_line.startswith('#!/usr/bin/env python') or 'python' in first_line.lower()
            
            print("✅ Training script validated")
        
        # Check that scripts directory structure exists
        assert (scripts_path / "train").exists()
        assert (scripts_path / "evaluate").exists()
        assert (scripts_path / "data").exists()
        assert (scripts_path / "utils").exists()
        
        print("✅ Scripts structure validated")
    
    def test_documentation_completeness(self):
        """Test that documentation files exist."""
        base_path = Path(__file__).parent.parent.parent
        docs_path = base_path / "docs"
        
        # Check main documentation files
        assert (docs_path / "README.md").exists()
        
        # Check architecture documentation
        arch_path = docs_path / "architecture"
        if arch_path.exists():
            assert (arch_path / "overview.md").exists()
            print("✅ Architecture documentation validated")
        
        # Check tutorials
        tutorial_path = docs_path / "tutorials"
        if tutorial_path.exists():
            assert (tutorial_path / "quickstart.md").exists()
            print("✅ Tutorial documentation validated")
        
        print("✅ Documentation structure validated")
    
    def test_package_structure(self):
        """Test that the package can be imported correctly."""
        base_path = Path(__file__).parent.parent.parent
        src_path = base_path / "src"
        
        # Check __init__.py files exist
        assert (src_path / "__init__.py").exists()
        assert (src_path / "agents" / "__init__.py").exists()
        assert (src_path / "knowledge" / "__init__.py").exists()
        
        # Test imports work
        try:
            import agents
            import knowledge
            print("✅ Package imports validated")
        except ImportError as e:
            pytest.fail(f"Package import failed: {e}")
    
    def test_requirements_and_setup(self):
        """Test that requirements and setup files exist."""
        base_path = Path(__file__).parent.parent.parent
        
        # Check requirements file
        assert (base_path / "requirements.txt").exists()
        
        # Check setup file
        assert (base_path / "setup.py").exists()
        
        # Check README
        assert (base_path / "README.md").exists()
        
        print("✅ Package setup files validated")
    
    def test_end_to_end_workflow(self, temp_config_dir):
        """Test a complete end-to-end workflow."""
        # Load configuration
        with open(temp_config_dir, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create agent
        agent = UnifiedAgent("e2e_test", config)
        
        try:
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
            
            # Check episode completed
            assert len(episode_actions) == 3
            
            # Check statistics
            stats = agent.get_statistics()
            assert stats["total_actions"] == 3
            assert stats["total_reward"] > 0
            
            # Reset for new episode
            agent.reset()
            
            # Check reset worked
            new_stats = agent.get_statistics()
            assert new_stats["total_episodes"] == 1
            
            print("✅ End-to-end workflow validated")
            
        finally:
            agent.cleanup()


class TestSystemIntegration:
    """Test system-level integration."""
    
    def test_mock_training_run(self):
        """Test a mock training run without external dependencies."""
        # This would test the training loop without actually training
        # Mock environment and agent interaction
        
        class MockEnvironment:
            def __init__(self):
                self.step_count = 0
            
            def reset(self):
                self.step_count = 0
                return "Mock observation"
            
            def step(self, action):
                self.step_count += 1
                obs = f"Mock observation {self.step_count}"
                reward = 1.0 if self.step_count >= 3 else 0.0
                done = self.step_count >= 5
                info = {"success": reward > 0}
                return obs, reward, done, info
            
            def get_available_actions(self):
                return ["action1", "action2", "action3"]
        
        # Create mock agent config
        config = {
            "agent_name": "mock_agent",
            "agent_type": "UnifiedAgent",
            "llm": {"model_name": "mock", "temperature": 0.7},
            "capabilities": {
                "use_knowledge_graph": False,
                "use_memory": False,
                "use_enhanced_reasoning": False,
                "use_rl": False
            }
        }
        
        # Create components
        agent = UnifiedAgent("mock_test", config)
        env = MockEnvironment()
        
        try:
            # Run mock episode
            obs = env.reset()
            agent.reset()
            
            total_reward = 0
            steps = 0
            
            while steps < 5:
                actions = env.get_available_actions()
                action = agent.act(obs, actions)
                
                obs, reward, done, info = env.step(action)
                agent.update_reward(reward)
                
                total_reward += reward
                steps += 1
                
                if done:
                    break
            
            # Validate results
            assert steps > 0
            assert total_reward >= 0
            
            stats = agent.get_statistics()
            assert stats["total_actions"] == steps
            
            print("✅ Mock training run validated")
            
        finally:
            agent.cleanup()


if __name__ == "__main__":
    # Run tests directly
    test_suite = TestArchitectureValidation()
    
    print("🧪 Running KGRL Architecture Validation Tests")
    print("=" * 50)
    
    try:
        test_suite.test_directory_structure()
        test_suite.test_configuration_files()
        test_suite.test_package_structure()
        test_suite.test_requirements_and_setup()
        test_suite.test_script_executability()
        test_suite.test_documentation_completeness()
        
        # Tests requiring fixtures
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            agent_config = {
                "agent_name": "test_agent",
                "agent_type": "UnifiedAgent",
                "llm": {"model_name": "gpt-4o", "temperature": 0.7},
                "capabilities": {
                    "use_knowledge_graph": True,
                    "use_memory": True,
                    "use_enhanced_reasoning": False,
                    "use_rl": False
                },
                "knowledge_graph": {
                    "storage": {
                        "backend": "networkx",
                        "storage_path": str(config_path / "kg_data")
                    }
                }
            }
            
            config_file = config_path / "test_agent.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(agent_config, f)
            
            test_suite.test_agent_import_and_creation(str(config_file))
            test_suite.test_end_to_end_workflow(str(config_file))
        
        test_suite.test_knowledge_graph_integration()
        test_suite.test_configuration_loading()
        
        # Integration tests
        integration_suite = TestSystemIntegration()
        integration_suite.test_mock_training_run()
        
        print("=" * 50)
        print("🎉 All architecture validation tests passed!")
        print("✅ New KGRL architecture is ready for use")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
