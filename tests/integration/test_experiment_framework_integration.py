"""
实验框架集成测试

测试完整实验框架的集成功能：
- 配置管理系统集成
- 实验执行框架集成
- 结果分析系统集成
- 端到端实验流程测试
"""

import sys
import pytest
import tempfile
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入框架模块
sys.path.append(str(Path(__file__).parent.parent.parent / "framework"))
from config_manager import ConfigManager
from experiment_runner import ExperimentRunner
from result_analyzer import ResultAnalyzer
from unified_kg_agent import UnifiedKGAgent

class TestExperimentFrameworkIntegration:
    """实验框架集成测试类"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建agents配置目录
            agents_dir = temp_path / "agents"
            agents_dir.mkdir()
            
            # 创建experiments配置目录
            experiments_dir = temp_path / "experiments"
            experiments_dir.mkdir()
            
            # 创建测试Agent配置
            test_agent_config = {
                "agent_name": "test_vanilla",
                "agent_type": "UnifiedKGAgent",
                "description": "Test vanilla agent",
                "model_name": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 300,
                "use_knowledge_graph": False,
                "use_memory": False,
                "use_enhanced_reasoning": False,
                "experiment_tags": ["test", "vanilla"]
            }
            
            with open(agents_dir / "test_vanilla.yaml", 'w') as f:
                import yaml
                yaml.dump(test_agent_config, f)
            
            # 创建测试实验配置
            test_experiment_config = {
                "experiment_name": "test_experiment",
                "experiment_type": "comparison",
                "description": "Test experiment for integration",
                "settings": {
                    "num_episodes": 2,
                    "max_steps_per_episode": 5,
                    "timeout_per_episode": 30
                },
                "agents": [
                    {
                        "name": "test_vanilla",
                        "config_file": "agents/test_vanilla.yaml"
                    }
                ],
                "scenarios": ["simple_room"],
                "metrics": ["success_rate", "avg_steps", "decision_time"]
            }
            
            with open(experiments_dir / "test_experiment.yaml", 'w') as f:
                import yaml
                yaml.dump(test_experiment_config, f)
            
            yield str(temp_path)
    
    def test_config_manager_integration(self, temp_config_dir):
        """测试配置管理器集成"""
        config_manager = ConfigManager(temp_config_dir)
        
        # 测试Agent配置加载
        agent_configs = config_manager.list_agent_configs()
        assert "test_vanilla" in agent_configs
        
        agent_config = config_manager.get_agent_config_dict("test_vanilla")
        assert agent_config is not None
        assert agent_config["agent_name"] == "test_vanilla"
        assert agent_config["use_knowledge_graph"] == False
        
        # 测试实验配置加载
        experiment_configs = config_manager.list_experiment_configs()
        assert "test_experiment" in experiment_configs
        
        experiment_config = config_manager.get_experiment_config_dict("test_experiment")
        assert experiment_config is not None
        assert experiment_config["experiment_name"] == "test_experiment"
        assert len(experiment_config["agents"]) == 1
        
        print("配置管理器集成测试通过:")
        print(f"  Agent配置: {agent_configs}")
        print(f"  实验配置: {experiment_configs}")
    
    def test_agent_creation_from_config(self, temp_config_dir):
        """测试从配置创建Agent"""
        config_manager = ConfigManager(temp_config_dir)
        
        # 从配置创建Agent
        agent_config = config_manager.get_agent_config_dict("test_vanilla")
        agent = UnifiedKGAgent("integration_test_agent", agent_config)
        
        try:
            # 验证Agent属性
            assert agent.name == "integration_test_agent"
            assert agent.use_knowledge_graph == False
            assert agent.use_memory == False
            assert agent.use_enhanced_reasoning == False
            
            # 测试Agent决策
            observation = "You are in a test room."
            actions = ["test_action_1", "test_action_2"]
            
            decision = agent.act(observation, actions)
            assert decision in actions
            
            # 验证统计信息
            stats = agent.get_statistics()
            assert stats["total_actions"] == 1
            
            print("从配置创建Agent测试通过:")
            print(f"  Agent名称: {agent.name}")
            print(f"  决策结果: {decision}")
            print(f"  统计信息: {stats}")
            
        finally:
            agent.cleanup()
    
    def test_experiment_runner_integration(self, temp_config_dir):
        """测试实验执行器集成"""
        config_manager = ConfigManager(temp_config_dir)
        experiment_runner = ExperimentRunner()
        
        # 获取实验配置
        experiment_config = config_manager.get_experiment_config_dict("test_experiment")
        
        # 创建简化的实验环境
        class MockEnvironment:
            def __init__(self):
                self.step_count = 0
                self.max_steps = 5
            
            def reset(self):
                self.step_count = 0
                return "You are in a test environment."
            
            def step(self, action):
                self.step_count += 1
                observation = f"Step {self.step_count}: You performed {action}"
                reward = 1.0 if self.step_count >= 3 else 0.0
                done = self.step_count >= self.max_steps or reward > 0
                info = {"step": self.step_count}
                return observation, reward, done, info
            
            def get_available_actions(self):
                return ["action_1", "action_2", "action_3"]
        
        # 执行简化实验
        try:
            # 创建Agent
            agent_config = config_manager.get_agent_config_dict("test_vanilla")
            agent = UnifiedKGAgent("experiment_agent", agent_config)
            
            # 创建环境
            env = MockEnvironment()
            
            # 运行单个episode
            observation = env.reset()
            total_reward = 0
            steps = 0
            
            while steps < experiment_config["settings"]["max_steps_per_episode"]:
                available_actions = env.get_available_actions()
                action = agent.act(observation, available_actions)
                
                observation, reward, done, info = env.step(action)
                total_reward += reward
                steps += 1
                
                if done:
                    break
            
            # 验证实验结果
            assert steps > 0
            assert total_reward >= 0
            
            # 获取Agent统计
            agent_stats = agent.get_statistics()
            assert agent_stats["total_actions"] == steps
            
            print("实验执行器集成测试通过:")
            print(f"  执行步数: {steps}")
            print(f"  总奖励: {total_reward}")
            print(f"  Agent统计: {agent_stats}")
            
        finally:
            if 'agent' in locals():
                agent.cleanup()
    
    def test_result_analyzer_integration(self):
        """测试结果分析器集成"""
        result_analyzer = ResultAnalyzer()
        
        # 创建模拟实验结果
        mock_results = {
            "experiment_name": "integration_test",
            "timestamp": "2024-01-01T10:00:00",
            "agents": {
                "vanilla_agent": {
                    "episodes": [
                        {"steps": 5, "reward": 1.0, "success": True, "decision_time": 0.1},
                        {"steps": 7, "reward": 0.5, "success": False, "decision_time": 0.15},
                        {"steps": 4, "reward": 1.0, "success": True, "decision_time": 0.08}
                    ],
                    "config": {"type": "vanilla"}
                },
                "enhanced_agent": {
                    "episodes": [
                        {"steps": 3, "reward": 1.0, "success": True, "decision_time": 0.2},
                        {"steps": 4, "reward": 1.0, "success": True, "decision_time": 0.25},
                        {"steps": 5, "reward": 0.8, "success": True, "decision_time": 0.18}
                    ],
                    "config": {"type": "enhanced"}
                }
            }
        }
        
        # 分析结果
        analysis = result_analyzer.analyze_results(mock_results)
        
        # 验证分析结果
        assert "summary" in analysis
        assert "agent_comparison" in analysis
        assert "statistics" in analysis
        
        # 验证统计信息
        stats = analysis["statistics"]
        assert "vanilla_agent" in stats
        assert "enhanced_agent" in stats
        
        # 验证每个Agent的统计
        vanilla_stats = stats["vanilla_agent"]
        assert "avg_steps" in vanilla_stats
        assert "success_rate" in vanilla_stats
        assert "avg_decision_time" in vanilla_stats
        
        enhanced_stats = stats["enhanced_agent"]
        assert "avg_steps" in enhanced_stats
        assert "success_rate" in enhanced_stats
        assert "avg_decision_time" in enhanced_stats
        
        print("结果分析器集成测试通过:")
        print(f"  分析结果键: {list(analysis.keys())}")
        print(f"  Vanilla统计: {vanilla_stats}")
        print(f"  Enhanced统计: {enhanced_stats}")
        
        # 验证对比分析
        comparison = analysis["agent_comparison"]
        assert len(comparison) > 0
    
    def test_end_to_end_experiment_flow(self, temp_config_dir):
        """测试端到端实验流程"""
        # 1. 初始化组件
        config_manager = ConfigManager(temp_config_dir)
        experiment_runner = ExperimentRunner()
        result_analyzer = ResultAnalyzer()
        
        # 2. 加载配置
        experiment_config = config_manager.get_experiment_config_dict("test_experiment")
        agent_config = config_manager.get_agent_config_dict("test_vanilla")
        
        # 3. 创建Agent
        agent = UnifiedKGAgent("e2e_test_agent", agent_config)
        
        try:
            # 4. 执行简化实验
            experiment_results = {
                "experiment_name": experiment_config["experiment_name"],
                "timestamp": "2024-01-01T10:00:00",
                "config": experiment_config,
                "agents": {}
            }
            
            # 模拟实验执行
            agent_results = {
                "episodes": [],
                "config": agent_config
            }
            
            # 运行多个episode
            for episode in range(experiment_config["settings"]["num_episodes"]):
                # 模拟episode执行
                observation = f"Episode {episode}: Test scenario"
                actions = ["action_1", "action_2", "action_3"]
                
                episode_steps = 0
                episode_reward = 0
                episode_start_time = 0
                
                for step in range(experiment_config["settings"]["max_steps_per_episode"]):
                    import time
                    start_time = time.time()
                    
                    action = agent.act(observation, actions)
                    
                    decision_time = time.time() - start_time
                    episode_steps += 1
                    episode_reward += 0.2  # 模拟奖励
                    
                    # 模拟episode结束条件
                    if step >= 2:  # 简化的结束条件
                        break
                
                # 记录episode结果
                episode_result = {
                    "episode": episode,
                    "steps": episode_steps,
                    "reward": episode_reward,
                    "success": episode_reward > 0.5,
                    "decision_time": decision_time
                }
                
                agent_results["episodes"].append(episode_result)
            
            # 添加Agent结果到实验结果
            experiment_results["agents"]["test_vanilla"] = agent_results
            
            # 5. 分析结果
            analysis = result_analyzer.analyze_results(experiment_results)
            
            # 6. 验证端到端流程
            assert "summary" in analysis
            assert "statistics" in analysis
            assert "test_vanilla" in analysis["statistics"]
            
            # 验证Agent统计
            agent_stats = agent.get_statistics()
            expected_total_actions = experiment_config["settings"]["num_episodes"] * 3  # 每个episode 3步
            assert agent_stats["total_actions"] == expected_total_actions
            
            print("端到端实验流程测试通过:")
            print(f"  实验名称: {experiment_results['experiment_name']}")
            print(f"  执行episodes: {len(agent_results['episodes'])}")
            print(f"  Agent总动作数: {agent_stats['total_actions']}")
            print(f"  分析结果: {list(analysis.keys())}")
            
            # 验证结果一致性
            analyzed_stats = analysis["statistics"]["test_vanilla"]
            assert "avg_steps" in analyzed_stats
            assert "success_rate" in analyzed_stats
            
        finally:
            agent.cleanup()
    
    def test_configuration_validation_integration(self, temp_config_dir):
        """测试配置验证集成"""
        config_manager = ConfigManager(temp_config_dir)
        
        # 测试有效配置验证
        valid_agent_config = config_manager.get_agent_config_dict("test_vanilla")
        assert config_manager.validate_agent_config(valid_agent_config)
        
        valid_experiment_config = config_manager.get_experiment_config_dict("test_experiment")
        assert config_manager.validate_experiment_config(valid_experiment_config)
        
        # 测试无效配置检测
        invalid_agent_config = {"invalid": "config"}
        assert not config_manager.validate_agent_config(invalid_agent_config)
        
        invalid_experiment_config = {"invalid": "experiment"}
        assert not config_manager.validate_experiment_config(invalid_experiment_config)
        
        print("配置验证集成测试通过:")
        print("  有效配置验证: 通过")
        print("  无效配置检测: 通过")
    
    def test_error_handling_integration(self, temp_config_dir):
        """测试错误处理集成"""
        config_manager = ConfigManager(temp_config_dir)
        
        # 测试不存在的配置文件
        try:
            non_existent_config = config_manager.get_agent_config_dict("non_existent")
            assert non_existent_config is None
        except Exception as e:
            # 应该优雅地处理错误
            assert isinstance(e, (FileNotFoundError, KeyError))
        
        # 测试损坏的配置文件
        corrupted_config_path = Path(temp_config_dir) / "agents" / "corrupted.yaml"
        with open(corrupted_config_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        try:
            corrupted_config = config_manager.get_agent_config_dict("corrupted")
            assert corrupted_config is None
        except Exception as e:
            # 应该优雅地处理YAML解析错误
            assert "yaml" in str(e).lower() or "parse" in str(e).lower()
        
        print("错误处理集成测试通过:")
        print("  不存在配置处理: 通过")
        print("  损坏配置处理: 通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
