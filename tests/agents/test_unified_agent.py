"""
Unified Agent测试

测试新统一架构的Agent功能，包括：
- 配置驱动的能力启用/禁用
- 各种能力组合测试
- 模块化组件测试
- 消融实验验证
"""

import sys
import pytest
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入新框架
sys.path.append(str(Path(__file__).parent.parent.parent / "framework"))
from unified_kg_agent import UnifiedKGAgent, create_vanilla_agent, create_fully_augmented_agent
from config_manager import ConfigManager

class TestUnifiedAgent:
    """Unified Agent基础测试"""
    
    @pytest.fixture
    def config_manager(self):
        """创建配置管理器"""
        return ConfigManager("framework/configs")
    
    @pytest.fixture
    def vanilla_config(self, config_manager):
        """获取vanilla配置"""
        return config_manager.get_agent_config_dict("vanilla_llm")
    
    @pytest.fixture
    def full_config(self, config_manager):
        """获取完整配置"""
        return config_manager.get_agent_config_dict("fully_augmented")
    
    def test_vanilla_agent_creation(self, vanilla_config):
        """测试vanilla agent创建"""
        agent = UnifiedKGAgent("test_vanilla", vanilla_config)
        
        assert agent.name == "test_vanilla"
        assert not agent.use_knowledge_graph
        assert not agent.use_memory
        assert not agent.use_enhanced_reasoning
        
        # 测试便捷创建函数
        vanilla_agent = create_vanilla_agent()
        assert vanilla_agent.name == "vanilla_agent"
    
    def test_fully_augmented_creation(self, full_config):
        """测试完全增强agent创建"""
        agent = UnifiedKGAgent("test_full", full_config)
        
        assert agent.name == "test_full"
        assert agent.use_knowledge_graph
        assert agent.use_memory
        assert agent.use_enhanced_reasoning
        
        # 测试便捷创建函数
        full_agent = create_fully_augmented_agent()
        assert full_agent.name == "fully_augmented_agent"
    
    def test_capability_modules_loading(self, full_config):
        """测试能力模块加载"""
        agent = UnifiedKGAgent("test_modules", full_config)
        
        # 验证模块注册
        assert hasattr(agent, 'module_registry')
        assert 'knowledge' in agent.module_registry.modules
        assert 'memory' in agent.module_registry.modules
        assert 'reasoning' in agent.module_registry.modules
    
    def test_configuration_validation(self, config_manager):
        """测试配置验证"""
        # 测试所有标准配置
        config_names = [
            "vanilla_llm", "kg_augmented", "memory_enhanced",
            "reasoning_enhanced", "dual_augmented", "fully_augmented"
        ]
        
        for config_name in config_names:
            config = config_manager.get_agent_config_dict(config_name)
            agent = UnifiedKGAgent(f"test_{config_name}", config)
            
            # 验证基本属性
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'use_knowledge_graph')
            assert hasattr(agent, 'use_memory')
            assert hasattr(agent, 'use_enhanced_reasoning')
    
    def test_decision_making_vanilla(self, vanilla_config):
        """测试vanilla agent决策"""
        agent = UnifiedKGAgent("test_decision", vanilla_config)
        
        observation = "You are in a room. There is a key on the table."
        available_actions = ["take key", "examine room", "go north"]
        
        action = agent.act(observation, available_actions)
        
        assert action in available_actions
        assert isinstance(action, str)
    
    def test_decision_making_full(self, full_config):
        """测试完全增强agent决策"""
        agent = UnifiedKGAgent("test_full_decision", full_config)
        
        observation = "You see a chest and a key. You need treasure."
        available_actions = ["take key", "open chest", "examine chest"]
        
        action = agent.act(observation, available_actions)
        
        assert action in available_actions
        # 完全增强的agent可能会有更复杂的决策过程
    
    def test_statistics_tracking(self, vanilla_config):
        """测试统计信息跟踪"""
        agent = UnifiedKGAgent("test_stats", vanilla_config)
        
        # 执行几个动作
        for i in range(3):
            observation = f"Step {i}: You are in a room."
            available_actions = ["action1", "action2"]
            agent.act(observation, available_actions)
        
        stats = agent.get_statistics()
        
        assert stats['total_actions'] == 3
        assert 'avg_decision_time' in stats
        assert 'success_rate' in stats
    
    def test_agent_cleanup(self, full_config):
        """测试agent清理"""
        agent = UnifiedKGAgent("test_cleanup", full_config)
        
        # 执行一些操作
        agent.act("test", ["action1"])
        
        # 清理
        agent.cleanup()
        
        # 验证清理后状态
        assert hasattr(agent, 'name')  # 基本属性应该保留


class TestUnifiedAgentCapabilities:
    """Unified Agent能力测试"""
    
    def test_kg_capability_toggle(self):
        """测试KG能力开关"""
        # KG关闭的配置
        config_off = {
            'agent_name': 'test_kg_off',
            'use_knowledge_graph': False,
            'use_memory': False,
            'use_enhanced_reasoning': False
        }
        
        # KG开启的配置
        config_on = {
            'agent_name': 'test_kg_on',
            'use_knowledge_graph': True,
            'use_memory': False,
            'use_enhanced_reasoning': False,
            'knowledge_graph': {
                'enabled': True,
                'max_facts_per_query': 5
            }
        }
        
        agent_off = UnifiedKGAgent("kg_off", config_off)
        agent_on = UnifiedKGAgent("kg_on", config_on)
        
        assert not agent_off.use_knowledge_graph
        assert agent_on.use_knowledge_graph
    
    def test_memory_capability_toggle(self):
        """测试记忆能力开关"""
        config_memory = {
            'agent_name': 'test_memory',
            'use_knowledge_graph': False,
            'use_memory': True,
            'use_enhanced_reasoning': False,
            'memory': {
                'enabled': True,
                'short_term_size': 10
            }
        }
        
        agent = UnifiedKGAgent("memory_test", config_memory)
        assert agent.use_memory
    
    def test_reasoning_capability_toggle(self):
        """测试推理能力开关"""
        config_reasoning = {
            'agent_name': 'test_reasoning',
            'use_knowledge_graph': False,
            'use_memory': False,
            'use_enhanced_reasoning': True,
            'reasoning': {
                'enabled': True,
                'use_react': True
            }
        }
        
        agent = UnifiedKGAgent("reasoning_test", config_reasoning)
        assert agent.use_enhanced_reasoning
    
    def test_capability_combinations(self):
        """测试能力组合"""
        combinations = [
            {'kg': True, 'memory': False, 'reasoning': False},
            {'kg': False, 'memory': True, 'reasoning': False},
            {'kg': False, 'memory': False, 'reasoning': True},
            {'kg': True, 'memory': True, 'reasoning': False},
            {'kg': True, 'memory': False, 'reasoning': True},
            {'kg': False, 'memory': True, 'reasoning': True},
            {'kg': True, 'memory': True, 'reasoning': True},
        ]
        
        for i, combo in enumerate(combinations):
            config = {
                'agent_name': f'combo_{i}',
                'use_knowledge_graph': combo['kg'],
                'use_memory': combo['memory'],
                'use_enhanced_reasoning': combo['reasoning']
            }
            
            agent = UnifiedKGAgent(f"combo_{i}", config)
            
            assert agent.use_knowledge_graph == combo['kg']
            assert agent.use_memory == combo['memory']
            assert agent.use_enhanced_reasoning == combo['reasoning']


class TestUnifiedAgentPerformance:
    """Unified Agent性能测试"""
    
    def test_performance_comparison(self):
        """性能对比测试"""
        vanilla = create_vanilla_agent()
        full = create_fully_augmented_agent()
        
        observation = "You are in a complex room with many objects."
        actions = ["action1", "action2", "action3", "action4"]
        
        # 测试vanilla性能
        start_time = time.time()
        for _ in range(5):
            vanilla.act(observation, actions)
        vanilla_time = (time.time() - start_time) / 5
        
        # 测试full性能
        start_time = time.time()
        for _ in range(5):
            full.act(observation, actions)
        full_time = (time.time() - start_time) / 5
        
        print(f"Vanilla Agent平均时间: {vanilla_time:.3f}秒")
        print(f"Full Agent平均时间: {full_time:.3f}秒")
        
        # 清理
        vanilla.cleanup()
        full.cleanup()
        
        # 完全增强的agent可能会慢一些，但应该在合理范围内
        assert vanilla_time < 5.0
        assert full_time < 15.0
    
    def test_memory_usage(self):
        """内存使用测试"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建多个agent
        agents = []
        for i in range(5):
            agent = create_fully_augmented_agent()
            agents.append(agent)
            
            # 执行一些操作
            agent.act("test observation", ["action1", "action2"])
        
        peak_memory = process.memory_info().rss
        memory_increase = (peak_memory - initial_memory) / 1024 / 1024  # MB
        
        # 清理
        for agent in agents:
            agent.cleanup()
        
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 内存增长应该在合理范围内
        assert memory_increase < 500  # 500MB以内


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
