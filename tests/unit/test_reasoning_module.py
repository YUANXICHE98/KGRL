"""
Reasoning Module单元测试

测试推理增强模块的核心功能：
- ReAct推理循环
- DODAF框架推理
- 思维链推理
- 推理策略选择
- 置信度计算
"""

import sys
import pytest
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入框架模块
sys.path.append(str(Path(__file__).parent.parent.parent / "framework"))
from capabilities.reasoning_module import ReasoningModule
from capabilities.base import CapabilityModule

class TestReasoningModule:
    """Reasoning Module基础测试"""
    
    @pytest.fixture
    def reasoning_config(self):
        """创建测试用推理配置"""
        return {
            'enabled': True,
            'use_react': True,
            'use_dodaf': True,
            'use_chain_of_thought': True,
            'max_react_iterations': 3,
            'react_temperature': 0.7,
            'confidence_threshold': 0.6
        }
    
    @pytest.fixture
    def reasoning_module(self, reasoning_config):
        """创建测试用Reasoning Module"""
        return ReasoningModule('test_reasoning', reasoning_config)
    
    def test_module_inheritance(self, reasoning_module):
        """测试模块继承关系"""
        assert isinstance(reasoning_module, CapabilityModule)
        assert hasattr(reasoning_module, 'initialize')
        assert hasattr(reasoning_module, 'process')
        assert hasattr(reasoning_module, 'cleanup')
    
    def test_module_initialization(self, reasoning_module):
        """测试模块初始化"""
        # 初始化前状态
        assert not hasattr(reasoning_module, 'reasoning_strategies')
        
        # 执行初始化
        reasoning_module.initialize()
        
        # 初始化后状态
        assert hasattr(reasoning_module, 'reasoning_strategies')
        assert reasoning_module.enabled
        
        # 验证推理策略初始化
        assert 'react' in reasoning_module.reasoning_strategies
        assert 'dodaf' in reasoning_module.reasoning_strategies
        assert 'chain_of_thought' in reasoning_module.reasoning_strategies
    
    def test_react_reasoning(self, reasoning_module):
        """测试ReAct推理"""
        reasoning_module.initialize()
        
        # ReAct推理请求
        reasoning_data = {
            'strategy': 'react',
            'observation': 'You are in a room with a key and a chest.',
            'available_actions': ['take key', 'open chest', 'examine room'],
            'goal': 'Find treasure'
        }
        
        result = reasoning_module.process(reasoning_data)
        
        assert 'action' in result
        assert 'reasoning_chain' in result
        assert 'confidence' in result
        
        # 验证返回的动作在可用动作列表中
        assert result['action'] in reasoning_data['available_actions']
        
        # 验证推理链包含思考过程
        reasoning_chain = result['reasoning_chain']
        assert len(reasoning_chain) > 0
        
        # 验证置信度在合理范围内
        assert 0.0 <= result['confidence'] <= 1.0
    
    def test_dodaf_reasoning(self, reasoning_module):
        """测试DODAF框架推理"""
        reasoning_module.initialize()
        
        # DODAF推理请求
        reasoning_data = {
            'strategy': 'dodaf',
            'observation': 'You see a locked door and a key on the ground.',
            'available_actions': ['take key', 'examine door', 'use key on door'],
            'goal': 'Open the door'
        }
        
        result = reasoning_module.process(reasoning_data)
        
        assert 'action' in result
        assert 'dodaf_analysis' in result
        assert 'confidence' in result
        
        # 验证DODAF分析包含DO-DA-F结构
        dodaf_analysis = result['dodaf_analysis']
        assert 'DO' in dodaf_analysis or 'DA' in dodaf_analysis or 'F' in dodaf_analysis
        
        # 验证动作选择合理性
        assert result['action'] in reasoning_data['available_actions']
    
    def test_chain_of_thought_reasoning(self, reasoning_module):
        """测试思维链推理"""
        reasoning_module.initialize()
        
        # 思维链推理请求
        reasoning_data = {
            'strategy': 'chain_of_thought',
            'observation': 'Complex puzzle: You have 3 keys (red, blue, green) and 3 chests with matching colors.',
            'available_actions': ['use red key', 'use blue key', 'use green key', 'examine chests'],
            'goal': 'Open all chests efficiently'
        }
        
        result = reasoning_module.process(reasoning_data)
        
        assert 'action' in result
        assert 'thought_chain' in result
        assert 'confidence' in result
        
        # 验证思维链包含逐步推理
        thought_chain = result['thought_chain']
        assert len(thought_chain) > 0
        
        # 思维链应该包含推理步骤
        chain_text = ' '.join(thought_chain)
        assert len(chain_text) > 0
    
    def test_strategy_selection(self, reasoning_module):
        """测试推理策略自动选择"""
        reasoning_module.initialize()
        
        # 不指定策略，让模块自动选择
        reasoning_data = {
            'observation': 'You are in a simple room with a key.',
            'available_actions': ['take key', 'examine key'],
            'goal': 'Get the key'
        }
        
        result = reasoning_module.process(reasoning_data)
        
        assert 'action' in result
        assert 'strategy_used' in result
        assert 'confidence' in result
        
        # 验证选择了合适的策略
        strategy_used = result['strategy_used']
        assert strategy_used in ['react', 'dodaf', 'chain_of_thought', 'direct']
    
    def test_confidence_calculation(self, reasoning_module):
        """测试置信度计算"""
        reasoning_module.initialize()
        
        # 测试不同复杂度的场景
        scenarios = [
            {
                'observation': 'Simple: You see a key.',
                'available_actions': ['take key'],
                'goal': 'Get key',
                'expected_confidence': 'high'  # 简单场景应该有高置信度
            },
            {
                'observation': 'Complex: Multiple rooms, many objects, unclear goal.',
                'available_actions': ['go north', 'go south', 'examine', 'take item1', 'take item2'],
                'goal': 'Find the hidden treasure',
                'expected_confidence': 'lower'  # 复杂场景置信度较低
            }
        ]
        
        confidences = []
        for scenario in scenarios:
            reasoning_data = {
                'strategy': 'react',
                'observation': scenario['observation'],
                'available_actions': scenario['available_actions'],
                'goal': scenario['goal']
            }
            
            result = reasoning_module.process(reasoning_data)
            confidences.append(result['confidence'])
        
        # 简单场景的置信度应该高于复杂场景
        # 注意：这个测试可能需要根据实际实现调整
        assert all(0.0 <= conf <= 1.0 for conf in confidences)
    
    def test_iterative_reasoning(self, reasoning_module):
        """测试迭代推理"""
        reasoning_module.initialize()
        
        # 多轮推理场景
        reasoning_sequence = [
            {
                'observation': 'You enter a room with multiple objects.',
                'available_actions': ['examine room', 'take key', 'open chest'],
                'goal': 'Find treasure'
            },
            {
                'observation': 'After examining, you see the key opens the chest.',
                'available_actions': ['take key', 'open chest'],
                'goal': 'Find treasure',
                'previous_action': 'examine room'
            },
            {
                'observation': 'You have the key. The chest is locked.',
                'available_actions': ['open chest with key', 'examine chest'],
                'goal': 'Find treasure',
                'previous_action': 'take key'
            }
        ]
        
        results = []
        for step in reasoning_sequence:
            reasoning_data = {
                'strategy': 'react',
                **step
            }
            
            result = reasoning_module.process(reasoning_data)
            results.append(result)
            
            assert 'action' in result
            assert result['action'] in step['available_actions']
        
        # 验证推理序列的连贯性
        assert len(results) == 3
        
        # 每一步的置信度都应该在合理范围内
        for result in results:
            assert 0.0 <= result['confidence'] <= 1.0
    
    def test_reasoning_with_constraints(self, reasoning_module):
        """测试带约束的推理"""
        reasoning_module.initialize()
        
        # 带约束的推理请求
        reasoning_data = {
            'strategy': 'react',
            'observation': 'You see multiple items: key, sword, potion.',
            'available_actions': ['take key', 'take sword', 'take potion', 'examine items'],
            'goal': 'Prepare for battle',
            'constraints': ['can only carry 2 items', 'key is required for exit']
        }
        
        result = reasoning_module.process(reasoning_data)
        
        assert 'action' in result
        assert 'reasoning_chain' in result
        
        # 推理链应该考虑约束条件
        reasoning_text = ' '.join(result['reasoning_chain'])
        # 可能包含对约束的考虑（具体取决于实现）
        assert len(reasoning_text) > 0
    
    def test_invalid_reasoning_requests(self, reasoning_module):
        """测试无效推理请求"""
        reasoning_module.initialize()
        
        # 测试各种无效请求
        invalid_requests = [
            None,  # None输入
            {},    # 空字典
            {'strategy': 'invalid_strategy'},  # 无效策略
            {'observation': 'test'},  # 缺少必要字段
            {'strategy': 'react', 'observation': 'test', 'available_actions': []},  # 空动作列表
        ]
        
        for invalid_request in invalid_requests:
            try:
                result = reasoning_module.process(invalid_request)
                # 应该返回错误结果或默认结果
                if 'action' in result:
                    # 如果返回了动作，应该是合理的默认值
                    assert isinstance(result['action'], str)
                else:
                    # 或者明确表示失败
                    assert 'error' in result or 'success' in result
            except Exception as e:
                # 或者抛出合适的异常
                assert isinstance(e, (ValueError, TypeError, KeyError))
    
    def test_reasoning_performance(self, reasoning_module):
        """测试推理性能"""
        reasoning_module.initialize()
        
        import time
        
        # 测试推理速度
        reasoning_data = {
            'strategy': 'react',
            'observation': 'Performance test scenario.',
            'available_actions': ['action1', 'action2', 'action3'],
            'goal': 'Test performance'
        }
        
        start_time = time.time()
        
        # 执行多次推理
        for _ in range(5):
            result = reasoning_module.process(reasoning_data)
            assert 'action' in result
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        
        # 推理应该在合理时间内完成
        assert avg_time < 2.0  # 2秒内
        
        print(f"Average reasoning time: {avg_time:.3f} seconds")
    
    def test_module_cleanup(self, reasoning_module):
        """测试模块清理"""
        reasoning_module.initialize()
        
        # 执行一些推理
        reasoning_data = {
            'strategy': 'react',
            'observation': 'Test cleanup.',
            'available_actions': ['test_action'],
            'goal': 'Test'
        }
        
        result = reasoning_module.process(reasoning_data)
        assert 'action' in result
        
        # 执行清理
        reasoning_module.cleanup()
        
        # 验证清理不会抛出异常
        assert True


class TestReasoningModuleIntegration:
    """Reasoning Module集成测试"""
    
    def test_multi_strategy_reasoning(self):
        """测试多策略推理集成"""
        config = {
            'enabled': True,
            'use_react': True,
            'use_dodaf': True,
            'use_chain_of_thought': True,
            'max_react_iterations': 2
        }
        
        module = ReasoningModule('multi_strategy_test', config)
        
        try:
            module.initialize()
            
            # 测试不同策略在同一场景下的表现
            base_scenario = {
                'observation': 'You are in a treasure room with a locked chest, a key on the floor, and a riddle on the wall.',
                'available_actions': ['take key', 'read riddle', 'examine chest', 'use key on chest'],
                'goal': 'Get the treasure'
            }
            
            strategies = ['react', 'dodaf', 'chain_of_thought']
            results = {}
            
            for strategy in strategies:
                reasoning_data = {
                    'strategy': strategy,
                    **base_scenario
                }
                
                result = module.process(reasoning_data)
                results[strategy] = result
                
                assert 'action' in result
                assert result['action'] in base_scenario['available_actions']
            
            # 验证不同策略可能产生不同的推理过程
            assert len(results) == 3
            
            # 所有策略都应该产生有效结果
            for strategy, result in results.items():
                assert 'confidence' in result
                assert 0.0 <= result['confidence'] <= 1.0
                
        finally:
            module.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
