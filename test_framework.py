#!/usr/bin/env python3
"""
KGRL框架快速测试脚本
验证项目框架的基本功能是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试核心模块导入"""
    print("🧪 Testing core module imports...")
    
    try:
        # 测试配置模块
        from config.base_config import config
        from config.agent_config import agent_configs
        from config.env_config import env_config
        print("  ✅ Configuration modules imported successfully")
        
        # 测试Agent模块
        from src.agents.base_agent import BaseAgent
        from src.agents.baseline_agent import BaselineAgent
        print("  ✅ Agent modules imported successfully")
        
        # 测试环境模块
        from src.environments.base_env import BaseEnvironment
        from src.environments.textworld_env import TextWorldEnvironment
        print("  ✅ Environment modules imported successfully")
        
        # 测试知识图谱模块
        from src.knowledge.kg_builder import KnowledgeGraphBuilder
        from src.knowledge.kg_retriever import KnowledgeGraphRetriever
        print("  ✅ Knowledge graph modules imported successfully")
        
        # 测试推理模块
        from src.reasoning.react_framework import ReActFramework
        print("  ✅ Reasoning modules imported successfully")
        
        # 测试工具模块
        from src.utils.logger import get_logger, setup_logging
        print("  ✅ Utility modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_configuration():
    """测试配置系统"""
    print("\n🔧 Testing configuration system...")
    
    try:
        from config.base_config import config
        from config.agent_config import agent_configs
        from config.env_config import env_config
        
        # 测试基础配置
        assert config.PROJECT_ROOT.exists(), "Project root should exist"
        print(f"  ✅ Project root: {config.PROJECT_ROOT}")
        
        # 测试Agent配置
        baseline_config = agent_configs.get_agent_config("baseline")
        assert baseline_config is not None, "Baseline config should exist"
        print(f"  ✅ Baseline agent config: {baseline_config.model_name}")
        
        # 测试环境配置
        env_cfg = env_config.get_env_config("textworld")
        assert env_cfg is not None, "TextWorld config should exist"
        print(f"  ✅ TextWorld config: {env_cfg.env_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def test_knowledge_graph():
    """测试知识图谱功能"""
    print("\n🧠 Testing knowledge graph functionality...")
    
    try:
        from src.knowledge.kg_builder import KnowledgeGraphBuilder
        from src.knowledge.kg_retriever import KnowledgeGraphRetriever
        
        # 创建知识图谱构建器
        kg_builder = KnowledgeGraphBuilder("test_kg")
        
        # 添加一些测试事实
        test_facts = [
            ("kitchen", "connected_to", "living_room"),
            ("fridge", "located_in", "kitchen"),
            ("apple", "located_in", "fridge"),
            ("key", "opens", "chest")
        ]
        
        for subject, predicate, obj in test_facts:
            kg_builder.add_fact(subject, predicate, obj)
        
        print(f"  ✅ Added {len(test_facts)} facts to knowledge graph")
        
        # 测试检索器
        retriever = KnowledgeGraphRetriever(kg_builder, "test_retriever")
        
        # 测试关键词检索
        results = retriever.retrieve_by_keywords("kitchen")
        assert len(results) > 0, "Should find facts about kitchen"
        print(f"  ✅ Keyword retrieval found {len(results)} results")
        
        # 测试实体检索
        results = retriever.retrieve_by_entity("kitchen")
        assert len(results) > 0, "Should find facts about kitchen entity"
        print(f"  ✅ Entity retrieval found {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Knowledge graph error: {e}")
        return False

def test_react_framework():
    """测试ReAct推理框架"""
    print("\n🤔 Testing ReAct reasoning framework...")
    
    try:
        from src.reasoning.react_framework import ReActFramework, ActionType
        
        # 创建ReAct框架
        react = ReActFramework("test_react")
        
        # 测试响应解析
        test_response = """
        Thought: I need to find the key to open the chest.
        Action: query_kg("where is the key located")
        Observation: The key is in the kitchen.
        Thought: Now I should go to the kitchen to get the key.
        Action: execute_action("go kitchen")
        """
        
        steps = react.parse_response(test_response)
        assert len(steps) > 0, "Should parse at least one step"
        print(f"  ✅ Parsed {len(steps)} ReAct steps")
        
        # 检查动作分类
        for step in steps:
            if step.action_content:
                action_type = react._classify_action(step.action_content)
                print(f"    - Action: {step.action_content[:30]}... -> {action_type.value}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ ReAct framework error: {e}")
        return False

def test_environment():
    """测试环境功能"""
    print("\n🎮 Testing environment functionality...")
    
    try:
        from src.environments.textworld_env import TextWorldEnvironment
        
        # 创建测试环境
        env_config = {
            "max_episode_steps": 10,
            "difficulty": "easy"
        }
        
        env = TextWorldEnvironment("test_env", env_config)
        
        # 测试重置
        observation = env.reset()
        assert observation is not None, "Reset should return observation"
        print(f"  ✅ Environment reset: {observation[:50]}...")
        
        # 测试可用动作
        actions = env.get_available_actions()
        assert len(actions) > 0, "Should have available actions"
        print(f"  ✅ Available actions: {len(actions)} actions")
        
        # 测试步骤执行
        test_action = actions[0] if actions else "look"
        obs, reward, done, info = env.step(test_action)
        print(f"  ✅ Step execution: action='{test_action}', reward={reward}")
        
        env.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Environment error: {e}")
        return False

def test_baseline_agent():
    """测试基线Agent"""
    print("\n🤖 Testing baseline agent...")
    
    try:
        from src.agents.baseline_agent import BaselineAgent
        
        # 创建测试Agent（使用模拟模式避免API调用）
        agent_config = {
            "model_name": "mock_model",
            "use_local_model": False,
            "temperature": 0.7,
            "max_retries": 1
        }
        
        agent = BaselineAgent("test_agent", agent_config)
        print(f"  ✅ Created baseline agent: {agent.agent_id}")
        
        # 测试重置
        agent.reset()
        print("  ✅ Agent reset successful")
        
        # 测试统计信息
        stats = agent.get_stats()
        assert isinstance(stats, dict), "Stats should be a dictionary"
        print(f"  ✅ Agent stats: {len(stats)} metrics")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Baseline agent error: {e}")
        return False

def test_directory_structure():
    """测试目录结构"""
    print("\n📁 Testing directory structure...")
    
    try:
        from config.base_config import config
        
        # 检查关键目录
        required_dirs = [
            config.DATA_DIR,
            config.RESULTS_DIR,
            config.KG_DIR,
            config.LOGS_DIR,
            config.MODELS_DIR,
            config.PLOTS_DIR
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {dir_path.name}: {dir_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Directory structure error: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 KGRL Framework Test Suite")
    print("="*50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration System", test_configuration),
        ("Directory Structure", test_directory_structure),
        ("Knowledge Graph", test_knowledge_graph),
        ("ReAct Framework", test_react_framework),
        ("Environment", test_environment),
        ("Baseline Agent", test_baseline_agent),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Framework is ready to use.")
        print("\n📋 Next steps:")
        print("1. Set up your API keys in .env file")
        print("2. Run: python main.py --demo")
        print("3. Or run: python main.py --week1")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
