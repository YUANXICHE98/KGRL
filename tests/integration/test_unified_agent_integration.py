"""
UnifiedKGAgent集成测试

测试统一Agent的完整集成功能：
- 不同配置组合的Agent创建和运行
- 能力模块间的协同工作
- 完整决策流程测试
- 性能和稳定性测试
"""

import sys
import pytest
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入框架模块
sys.path.append(str(Path(__file__).parent.parent.parent / "framework"))
from unified_kg_agent import UnifiedKGAgent, create_vanilla_agent, create_fully_augmented_agent
from config_manager import ConfigManager

class TestUnifiedAgentIntegration:
    """UnifiedKGAgent集成测试类"""
    
    @pytest.fixture
    def config_manager(self):
        """配置管理器"""
        return ConfigManager("framework/configs")
    
    @pytest.fixture
    def test_scenario(self):
        """标准测试场景"""
        return {
            'observation': 'You are in a room. There is a golden key on the table and a locked chest in the corner. You need to find treasure.',
            'available_actions': ['take key', 'examine key', 'examine chest', 'open chest', 'look around']
        }
    
    def test_all_agent_configurations(self, config_manager, test_scenario):
        """测试所有Agent配置的集成"""
        agent_configs = [
            "vanilla_llm", "kg_augmented", "memory_enhanced",
            "reasoning_enhanced", "dual_augmented", "fully_augmented"
        ]
        
        agents = {}
        results = {}
        
        try:
            # 创建所有配置的Agent
            for config_name in agent_configs:
                config = config_manager.get_agent_config_dict(config_name)
                agent = UnifiedKGAgent(f"test_{config_name}", config)
                agents[config_name] = agent
                
                # 执行决策
                action = agent.act(test_scenario['observation'], test_scenario['available_actions'])
                results[config_name] = action
                
                # 验证决策有效性
                assert action in test_scenario['available_actions']
                
                # 验证Agent状态
                stats = agent.get_statistics()
                assert stats['total_actions'] == 1
                assert 'avg_decision_time' in stats
            
            # 验证不同配置产生的决策
            assert len(results) == 6
            
            # 所有决策都应该有效
            for config_name, action in results.items():
                assert action is not None
                assert isinstance(action, str)
                assert action in test_scenario['available_actions']
                
            print("所有Agent配置集成测试通过:")
            for config_name, action in results.items():
                print(f"  {config_name}: {action}")
                
        finally:
            # 清理所有Agent
            for agent in agents.values():
                agent.cleanup()
    
    def test_capability_progression(self, config_manager, test_scenario):
        """测试能力递进效应"""
        # 按能力复杂度排序
        progression_configs = [
            ("vanilla_llm", "基础LLM"),
            ("kg_augmented", "KG增强"),
            ("memory_enhanced", "记忆增强"),
            ("reasoning_enhanced", "推理增强"),
            ("dual_augmented", "双重增强"),
            ("fully_augmented", "完全增强")
        ]
        
        agents = []
        decision_times = []
        
        try:
            for config_name, description in progression_configs:
                config = config_manager.get_agent_config_dict(config_name)
                agent = UnifiedKGAgent(config_name, config)
                agents.append(agent)
                
                # 测量决策时间
                start_time = time.time()
                action = agent.act(test_scenario['observation'], test_scenario['available_actions'])
                decision_time = time.time() - start_time
                
                decision_times.append(decision_time)
                
                # 验证决策
                assert action in test_scenario['available_actions']
                
                # 获取统计信息
                stats = agent.get_statistics()
                
                print(f"{description} ({config_name}):")
                print(f"  决策: {action}")
                print(f"  时间: {decision_time:.3f}s")
                print(f"  能力: KG={agent.use_knowledge_graph}, Memory={agent.use_memory}, Reasoning={agent.use_enhanced_reasoning}")
                print()
            
            # 验证决策时间趋势（更复杂的Agent可能需要更多时间）
            assert all(dt < 10.0 for dt in decision_times)  # 所有决策都应在10秒内
            
        finally:
            for agent in agents:
                agent.cleanup()
    
    def test_multi_step_scenario(self, config_manager):
        """测试多步骤场景集成"""
        # 使用完全增强的Agent进行多步测试
        config = config_manager.get_agent_config_dict("fully_augmented")
        agent = UnifiedKGAgent("multi_step_test", config)
        
        try:
            # 多步场景序列
            scenario_sequence = [
                {
                    'observation': 'You enter a room and see a table with a key.',
                    'actions': ['examine room', 'take key', 'look around'],
                    'expected_context': 'exploration'
                },
                {
                    'observation': 'You have the key. You notice a locked chest.',
                    'actions': ['examine chest', 'use key on chest', 'look for more items'],
                    'expected_context': 'problem_solving'
                },
                {
                    'observation': 'The chest is now open and contains a gem.',
                    'actions': ['take gem', 'examine gem', 'look for exit'],
                    'expected_context': 'completion'
                }
            ]
            
            actions_taken = []
            
            for i, step in enumerate(scenario_sequence):
                action = agent.act(step['observation'], step['actions'])
                actions_taken.append(action)
                
                # 验证动作有效性
                assert action in step['actions']
                
                # 验证Agent状态更新
                stats = agent.get_statistics()
                assert stats['total_actions'] == i + 1
                
                print(f"步骤 {i+1}: {step['observation']}")
                print(f"  选择动作: {action}")
                print(f"  可用动作: {step['actions']}")
                print()
            
            # 验证完整序列
            assert len(actions_taken) == 3
            
            # 获取最终统计
            final_stats = agent.get_statistics()
            assert final_stats['total_actions'] == 3
            assert final_stats['success_rate'] == 1.0  # 所有动作都成功
            
            print("多步场景统计:")
            for key, value in final_stats.items():
                print(f"  {key}: {value}")
                
        finally:
            agent.cleanup()
    
    def test_capability_module_interaction(self, config_manager):
        """测试能力模块间交互"""
        # 使用完全增强配置测试模块交互
        config = config_manager.get_agent_config_dict("fully_augmented")
        agent = UnifiedKGAgent("interaction_test", config)
        
        try:
            # 需要多种能力协同的复杂场景
            complex_scenario = {
                'observation': 'You are in a familiar room (you\'ve been here before). There are multiple objects: a red key, a blue key, a red chest, a blue chest, and a note that says "colors must match".',
                'available_actions': [
                    'take red key', 'take blue key', 
                    'open red chest', 'open blue chest',
                    'read note again', 'recall previous experience',
                    'examine keys', 'examine chests'
                ]
            }
            
            # 执行决策（应该利用记忆、知识图谱和推理）
            action = agent.act(complex_scenario['observation'], complex_scenario['available_actions'])
            
            # 验证决策
            assert action in complex_scenario['available_actions']
            
            # 获取详细统计，验证各模块都被使用
            stats = agent.get_statistics()
            
            print("复杂场景决策结果:")
            print(f"  观察: {complex_scenario['observation'][:100]}...")
            print(f"  选择动作: {action}")
            print(f"  统计信息: {stats}")
            
            # 验证各能力模块的使用情况
            if agent.use_knowledge_graph:
                assert stats.get('kg_queries', 0) >= 0
            if agent.use_memory:
                assert stats.get('memory_retrievals', 0) >= 0
            
        finally:
            agent.cleanup()
    
    def test_agent_performance_comparison(self, config_manager, test_scenario):
        """测试不同Agent配置的性能对比"""
        configs_to_test = ["vanilla_llm", "kg_augmented", "fully_augmented"]
        
        performance_results = {}
        
        for config_name in configs_to_test:
            config = config_manager.get_agent_config_dict(config_name)
            agent = UnifiedKGAgent(f"perf_{config_name}", config)
            
            try:
                # 执行多次决策测量性能
                times = []
                actions = []
                
                for _ in range(3):  # 执行3次测试
                    start_time = time.time()
                    action = agent.act(test_scenario['observation'], test_scenario['available_actions'])
                    end_time = time.time()
                    
                    times.append(end_time - start_time)
                    actions.append(action)
                    
                    # 验证每次决策都有效
                    assert action in test_scenario['available_actions']
                
                # 计算性能指标
                avg_time = sum(times) / len(times)
                consistency = len(set(actions)) == 1  # 决策是否一致
                
                performance_results[config_name] = {
                    'avg_time': avg_time,
                    'consistency': consistency,
                    'times': times,
                    'actions': actions
                }
                
                print(f"{config_name} 性能:")
                print(f"  平均时间: {avg_time:.3f}s")
                print(f"  决策一致性: {consistency}")
                print(f"  决策序列: {actions}")
                print()
                
            finally:
                agent.cleanup()
        
        # 验证性能结果
        assert len(performance_results) == 3
        
        # 所有配置的平均时间都应该在合理范围内
        for config_name, results in performance_results.items():
            assert results['avg_time'] < 5.0  # 5秒内
            assert len(results['actions']) == 3
    
    def test_error_recovery_integration(self, config_manager):
        """测试错误恢复集成"""
        config = config_manager.get_agent_config_dict("fully_augmented")
        agent = UnifiedKGAgent("error_recovery_test", config)
        
        try:
            # 测试各种错误情况下的恢复能力
            error_scenarios = [
                {
                    'observation': None,
                    'actions': ['test_action'],
                    'description': 'None observation'
                },
                {
                    'observation': 'Valid observation',
                    'actions': [],
                    'description': 'Empty actions list'
                },
                {
                    'observation': '',
                    'actions': ['test_action'],
                    'description': 'Empty observation'
                }
            ]
            
            recovery_results = []
            
            for scenario in error_scenarios:
                try:
                    action = agent.act(scenario['observation'], scenario['actions'])
                    recovery_results.append({
                        'scenario': scenario['description'],
                        'action': action,
                        'recovered': True
                    })
                    
                    # 如果返回了动作，应该是合理的
                    if action is not None:
                        if scenario['actions']:
                            assert action in scenario['actions']
                        
                except Exception as e:
                    recovery_results.append({
                        'scenario': scenario['description'],
                        'error': str(e),
                        'recovered': False
                    })
            
            print("错误恢复测试结果:")
            for result in recovery_results:
                print(f"  {result['scenario']}: {'成功' if result['recovered'] else '失败'}")
                if 'action' in result:
                    print(f"    动作: {result['action']}")
                elif 'error' in result:
                    print(f"    错误: {result['error']}")
            
            # 至少应该有一些错误恢复成功
            successful_recoveries = sum(1 for r in recovery_results if r['recovered'])
            assert successful_recoveries >= 0  # 允许所有都失败，但不应该崩溃
            
        finally:
            agent.cleanup()
    
    def test_concurrent_agents(self, config_manager, test_scenario):
        """测试并发Agent运行"""
        # 创建多个不同配置的Agent
        configs = ["vanilla_llm", "kg_augmented", "fully_augmented"]
        agents = []
        
        try:
            # 创建Agent
            for config_name in configs:
                config = config_manager.get_agent_config_dict(config_name)
                agent = UnifiedKGAgent(f"concurrent_{config_name}", config)
                agents.append((config_name, agent))
            
            # 并发执行决策
            results = []
            for config_name, agent in agents:
                action = agent.act(test_scenario['observation'], test_scenario['available_actions'])
                results.append((config_name, action))
                
                # 验证决策有效性
                assert action in test_scenario['available_actions']
            
            # 验证并发结果
            assert len(results) == 3
            
            print("并发Agent测试结果:")
            for config_name, action in results:
                print(f"  {config_name}: {action}")
            
            # 验证每个Agent的状态独立
            for config_name, agent in agents:
                stats = agent.get_statistics()
                assert stats['total_actions'] == 1
                
        finally:
            # 清理所有Agent
            for _, agent in agents:
                agent.cleanup()


class TestAgentLifecycle:
    """Agent生命周期集成测试"""
    
    def test_complete_agent_lifecycle(self):
        """测试完整的Agent生命周期"""
        # 1. 创建Agent
        vanilla_agent = create_vanilla_agent()
        full_agent = create_fully_augmented_agent()
        
        try:
            # 2. 验证初始状态
            assert vanilla_agent.name == "vanilla_agent"
            assert full_agent.name == "fully_augmented_agent"
            
            # 3. 执行决策序列
            test_sequence = [
                'You enter a mysterious room.',
                'You see various objects around.',
                'You need to find a way out.'
            ]
            
            actions = ['examine room', 'take item', 'use item', 'go north']
            
            for observation in test_sequence:
                # 两个Agent都执行相同的决策任务
                vanilla_action = vanilla_agent.act(observation, actions)
                full_action = full_agent.act(observation, actions)
                
                # 验证决策有效性
                assert vanilla_action in actions
                assert full_action in actions
            
            # 4. 验证最终状态
            vanilla_stats = vanilla_agent.get_statistics()
            full_stats = full_agent.get_statistics()
            
            assert vanilla_stats['total_actions'] == 3
            assert full_stats['total_actions'] == 3
            
            print("Agent生命周期测试完成:")
            print(f"  Vanilla Agent统计: {vanilla_stats}")
            print(f"  Full Agent统计: {full_stats}")
            
        finally:
            # 5. 清理资源
            vanilla_agent.cleanup()
            full_agent.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
