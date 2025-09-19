"""
ReAct Agent测试

测试ReAct推理Agent的功能，包括：
- 思考-行动-观察循环
- KG查询能力
- 推理链生成
- 动态决策
"""

import sys
import pytest
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.react_agent import ReactAgent
from src.knowledge.kg_builder import KnowledgeGraphBuilder
from src.knowledge.kg_retriever import KnowledgeGraphRetriever
from src.environments.textworld_env import TextWorldEnvironment

class TestReactAgent:
    """ReAct Agent测试类"""
    
    @pytest.fixture
    def knowledge_graph(self):
        """创建测试用知识图谱"""
        kg = KnowledgeGraphBuilder('test_react_kg')
        
        # 添加基础知识
        kg.add_fact('key', 'type', 'object')
        kg.add_fact('chest', 'type', 'container')
        kg.add_fact('key', 'opens', 'chest')
        kg.add_fact('chest', 'contains', 'treasure')
        kg.add_fact('room', 'type', 'location')
        kg.add_fact('kitchen', 'type', 'room')
        kg.add_fact('bedroom', 'type', 'room')
        kg.add_fact('kitchen', 'connects_to', 'bedroom')
        
        return kg
    
    @pytest.fixture
    def kg_retriever(self, knowledge_graph):
        """创建KG检索器"""
        return KnowledgeGraphRetriever(knowledge_graph, 'test_react_retriever')
    
    @pytest.fixture
    def react_agent(self, kg_retriever):
        """创建测试用ReAct Agent"""
        config = {
            'model_name': 'gpt-4o',
            'temperature': 0.7,
            'max_tokens': 500,
            'max_react_iterations': 3
        }
        return ReactAgent('test_react', config, kg_retriever)
    
    def test_agent_initialization(self, react_agent):
        """测试Agent初始化"""
        assert react_agent.name == 'test_react'
        assert react_agent.model_name == 'gpt-4o'
        assert react_agent.max_react_iterations == 3
        assert react_agent.kg_retriever is not None
    
    def test_kg_query_action(self, react_agent):
        """测试KG查询动作"""
        observation = "You see a key on the table."
        available_actions = ["take key", "examine key", "query_kg"]
        
        # 模拟ReAct循环中的KG查询
        kg_results = react_agent.kg_retriever.query_keywords(['key'])
        
        assert len(kg_results) > 0
        assert any('key' in str(fact).lower() for fact in kg_results)
    
    def test_react_reasoning_loop(self, react_agent):
        """测试ReAct推理循环"""
        observation = "You are in a room with a key and a chest."
        available_actions = ["take key", "open chest", "examine room", "query_kg"]
        
        action = react_agent.decide_action(observation, available_actions)
        
        # ReAct Agent应该能做出合理决策
        assert action in available_actions
        
        # 检查是否生成了推理链
        if hasattr(react_agent, 'last_reasoning_chain'):
            assert len(react_agent.last_reasoning_chain) > 0
    
    def test_knowledge_integration(self, react_agent):
        """测试知识整合能力"""
        observation = "You see a locked chest."
        available_actions = ["examine chest", "query_kg", "look around"]
        
        # 执行决策，应该会查询KG获取相关知识
        action = react_agent.decide_action(observation, available_actions)
        
        assert action in available_actions
        
        # 如果选择query_kg，验证查询结果
        if action == "query_kg":
            kg_results = react_agent.kg_retriever.query_keywords(['chest', 'key'])
            assert len(kg_results) > 0
    
    def test_multi_step_reasoning(self, react_agent):
        """测试多步推理"""
        scenarios = [
            {
                'observation': "You see a key on the floor.",
                'actions': ["take key", "examine key", "query_kg"]
            },
            {
                'observation': "You have a key. You see a chest.",
                'actions': ["open chest", "examine chest", "use key"]
            }
        ]
        
        for scenario in scenarios:
            action = react_agent.decide_action(
                scenario['observation'], 
                scenario['actions']
            )
            assert action in scenario['actions']
    
    def test_reasoning_chain_quality(self, react_agent):
        """测试推理链质量"""
        observation = "You need to find treasure. You see a key and a chest."
        available_actions = ["take key", "open chest", "examine key", "query_kg"]
        
        action = react_agent.decide_action(observation, available_actions)
        
        # 验证推理链包含思考过程
        if hasattr(react_agent, 'last_reasoning_chain'):
            reasoning = react_agent.last_reasoning_chain
            # 应该包含Thought和Action
            assert any('thought' in step.lower() or 'think' in step.lower() 
                      for step in reasoning)
    
    def test_performance_with_kg(self, react_agent):
        """测试带KG的性能"""
        start_time = time.time()
        
        observation = "Complex scenario with multiple objects and rooms."
        available_actions = ["action1", "action2", "query_kg", "examine"]
        
        # 执行多次决策
        for _ in range(3):
            action = react_agent.decide_action(observation, available_actions)
            assert action in available_actions
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 3
        
        # ReAct Agent可能比Baseline慢，但应该在合理范围内
        assert avg_time < 10.0  # 10秒内
        
        print(f"ReAct Agent平均决策时间: {avg_time:.3f}秒")


class TestReactAgentAdvanced:
    """ReAct Agent高级测试"""
    
    def test_dodaf_integration(self):
        """测试DODAF框架集成"""
        # 创建包含DODAF知识的KG
        kg = KnowledgeGraphBuilder('dodaf_test_kg')
        kg.add_fact('take_key', 'DO', 'acquire_key')
        kg.add_fact('acquire_key', 'DA', 'key_in_inventory')
        kg.add_fact('key_in_inventory', 'F', 'can_open_chest')
        
        retriever = KnowledgeGraphRetriever(kg, 'dodaf_retriever')
        
        config = {
            'model_name': 'gpt-4o',
            'temperature': 0.7,
            'use_dodaf': True
        }
        
        agent = ReactAgent('dodaf_react', config, retriever)
        
        observation = "You need to open a chest. You see a key."
        available_actions = ["take key", "examine chest", "query_kg"]
        
        action = agent.decide_action(observation, available_actions)
        assert action in available_actions
    
    def test_memory_integration(self):
        """测试记忆系统集成"""
        kg = KnowledgeGraphBuilder('memory_test_kg')
        kg.add_fact('previous_action', 'result', 'success')
        
        retriever = KnowledgeGraphRetriever(kg, 'memory_retriever')
        
        config = {
            'model_name': 'gpt-4o',
            'use_memory': True,
            'memory_size': 5
        }
        
        agent = ReactAgent('memory_react', config, retriever)
        
        # 执行一系列动作，测试记忆
        observations = [
            "You take the key.",
            "You approach the chest.",
            "You use the key on the chest."
        ]
        
        actions = ["examine chest", "open chest", "take treasure"]
        
        for obs, act in zip(observations, actions):
            result = agent.decide_action(obs, [act, "other_action"])
            assert result in [act, "other_action"]
    
    def test_error_recovery(self):
        """测试错误恢复能力"""
        kg = KnowledgeGraphBuilder('error_test_kg')
        retriever = KnowledgeGraphRetriever(kg, 'error_retriever')
        
        config = {'model_name': 'gpt-4o'}
        agent = ReactAgent('error_react', config, retriever)
        
        # 测试各种错误情况
        error_cases = [
            {"observation": None, "actions": ["test"]},
            {"observation": "", "actions": []},
            {"observation": "test", "actions": None}
        ]
        
        for case in error_cases:
            try:
                result = agent.decide_action(case["observation"], case["actions"])
                # 应该返回None或合理的默认值
                assert result is None or isinstance(result, str)
            except Exception as e:
                # 或者抛出合适的异常
                assert isinstance(e, (ValueError, TypeError))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
