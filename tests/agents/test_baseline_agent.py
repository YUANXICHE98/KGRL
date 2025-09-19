"""
Baseline Agent测试

测试纯LLM Agent的基础功能，包括：
- 基本决策能力
- API调用
- 错误处理
- 性能基准
"""

import sys
import pytest
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.baseline_agent import BaselineAgent
from src.environments.textworld_env import TextWorldEnvironment

class TestBaselineAgent:
    """Baseline Agent测试类"""
    
    @pytest.fixture
    def baseline_agent(self):
        """创建测试用的Baseline Agent"""
        config = {
            'model_name': 'gpt-4o',
            'temperature': 0.7,
            'max_tokens': 300
        }
        return BaselineAgent('test_baseline', config)
    
    @pytest.fixture
    def test_environment(self):
        """创建测试环境"""
        return TextWorldEnvironment({
            'nb_objects': 3,
            'nb_rooms': 2,
            'quest_length': 2
        })
    
    def test_agent_initialization(self, baseline_agent):
        """测试Agent初始化"""
        assert baseline_agent.name == 'test_baseline'
        assert baseline_agent.model_name == 'gpt-4o'
        assert baseline_agent.temperature == 0.7
    
    def test_basic_decision_making(self, baseline_agent):
        """测试基本决策能力"""
        observation = "You are in a room. There is a key on the table."
        available_actions = ["take key", "examine room", "go north"]
        
        action = baseline_agent.decide_action(observation, available_actions)
        
        assert action in available_actions
        assert isinstance(action, str)
    
    def test_action_validation(self, baseline_agent):
        """测试动作验证"""
        observation = "You see a chest."
        available_actions = ["open chest", "examine chest"]
        
        action = baseline_agent.decide_action(observation, available_actions)
        
        # 确保返回的动作在可用动作列表中
        assert action in available_actions
    
    def test_empty_actions_handling(self, baseline_agent):
        """测试空动作列表处理"""
        observation = "You are stuck."
        available_actions = []
        
        action = baseline_agent.decide_action(observation, available_actions)
        
        # 应该返回None或默认动作
        assert action is None or isinstance(action, str)
    
    def test_performance_benchmark(self, baseline_agent, test_environment):
        """性能基准测试"""
        start_time = time.time()
        
        # 运行5个决策步骤
        for _ in range(5):
            observation = test_environment.get_observation()
            available_actions = test_environment.get_available_actions()
            
            if available_actions:
                action = baseline_agent.decide_action(observation, available_actions)
                if action:
                    test_environment.step(action)
        
        end_time = time.time()
        avg_decision_time = (end_time - start_time) / 5
        
        # 基线Agent应该在合理时间内做出决策
        assert avg_decision_time < 5.0  # 5秒内
        
        print(f"Baseline Agent平均决策时间: {avg_decision_time:.3f}秒")
    
    def test_consistency(self, baseline_agent):
        """测试决策一致性"""
        observation = "You are in a kitchen. There is a key on the counter."
        available_actions = ["take key", "examine counter", "go east"]
        
        # 多次决策，检查一致性
        decisions = []
        for _ in range(3):
            action = baseline_agent.decide_action(observation, available_actions)
            decisions.append(action)
        
        # 所有决策都应该有效
        for decision in decisions:
            assert decision in available_actions
    
    def test_error_handling(self, baseline_agent):
        """测试错误处理"""
        # 测试无效输入
        try:
            action = baseline_agent.decide_action(None, ["test"])
            # 应该能处理None输入
            assert action is None or isinstance(action, str)
        except Exception as e:
            # 或者抛出合适的异常
            assert isinstance(e, (ValueError, TypeError))
    
    def test_agent_reset(self, baseline_agent):
        """测试Agent重置功能"""
        # 先进行一些决策
        baseline_agent.decide_action("test", ["action1"])
        
        # 重置Agent
        baseline_agent.reset()
        
        # 验证重置后状态
        assert hasattr(baseline_agent, 'name')
        assert baseline_agent.name == 'test_baseline'


class TestBaselineAgentIntegration:
    """Baseline Agent集成测试"""
    
    def test_full_episode(self):
        """完整episode测试"""
        agent = BaselineAgent('integration_test', {
            'model_name': 'gpt-4o',
            'temperature': 0.7
        })
        
        env = TextWorldEnvironment({
            'nb_objects': 2,
            'nb_rooms': 2,
            'quest_length': 2
        })
        
        observation = env.reset()
        total_reward = 0
        steps = 0
        max_steps = 10
        
        while steps < max_steps:
            available_actions = env.get_available_actions()
            if not available_actions:
                break
                
            action = agent.decide_action(observation, available_actions)
            if not action:
                break
                
            observation, reward, done, info = env.step(action)
            total_reward += reward
            steps += 1
            
            if done:
                break
        
        # 验证episode完成
        assert steps > 0
        assert isinstance(total_reward, (int, float))
        
        print(f"Episode完成: {steps}步, 总奖励: {total_reward}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
