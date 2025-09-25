#!/usr/bin/env python3
"""
测试修复后的环境 - 验证KG数据加载和状态更新
"""

import sys
import json
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.environments.scene_based_env import SceneBasedEnvironment
from src.agents.baseline_agents import LLMBaselineAgent, ReActAgent, RAGAgent
from src.utils.llm_client import LLMClient

def test_environment_loading():
    """测试环境加载"""
    print("🔧 测试环境加载...")
    
    # 初始化环境
    env = SceneBasedEnvironment()
    
    print(f"📊 可用场景数量: {len(env.scenes)}")
    
    # 测试场景重置
    if env.scenes:
        scene_name = list(env.scenes.keys())[0]
        print(f"🎮 测试场景: {scene_name}")
        
        observation = env.reset(scene_name)
        print(f"📋 观察内容:")
        for key, value in observation.items():
            if isinstance(value, list):
                print(f"  {key}: {value[:3]}..." if len(value) > 3 else f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")
        
        return True
    else:
        print("❌ 没有找到可用场景")
        return False

def test_agent_interactions():
    """测试智能体交互"""
    print("\n🤖 测试智能体交互...")
    
    # 初始化环境和智能体
    env = SceneBasedEnvironment()
    
    # 创建智能体
    agents = {
        'llm_baseline': LLMBaselineAgent(),
        'react': ReActAgent(),
        'rag': RAGAgent()
    }
    
    if not env.scenes:
        print("❌ 没有可用场景")
        return False
    
    scene_name = list(env.scenes.keys())[0]
    print(f"🎮 使用场景: {scene_name}")
    
    # 测试每个智能体
    for agent_name, agent in agents.items():
        print(f"\n🔍 测试智能体: {agent_name}")
        
        # 重置环境
        observation = env.reset(scene_name)
        agent.reset()
        
        # 执行3步
        for step in range(3):
            print(f"  步骤 {step + 1}:")
            
            # 智能体选择动作
            action, target = agent.select_action(observation)
            print(f"    动作: {action}, 目标: {target}")
            
            # 环境执行动作
            observation, reward, done, info = env.step(action, target)
            print(f"    奖励: {reward:.3f}, 完成: {done}")
            
            if done:
                break
    
    return True

def test_kg_data_access():
    """测试KG数据访问"""
    print("\n🔍 测试KG数据访问...")
    
    env = SceneBasedEnvironment()
    
    if not env.scenes:
        print("❌ 没有可用场景")
        return False
    
    scene_name = list(env.scenes.keys())[0]
    scene_data = env.scenes[scene_name]
    
    kg_data = scene_data.get('kg_data', {})
    nodes = kg_data.get('nodes', [])
    edges = kg_data.get('edges', [])
    
    print(f"📊 场景 {scene_name} KG统计:")
    print(f"  节点数: {len(nodes)}")
    print(f"  边数: {len(edges)}")
    
    # 分析节点类型
    node_types = {}
    entity_types = {}
    
    for node in nodes:
        node_type = node.get('type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
        
        if node_type == 'entity':
            entity_type = node.get('attributes', {}).get('entity_type', 'unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    print(f"  节点类型分布: {node_types}")
    print(f"  实体类型分布: {entity_types}")
    
    # 分析边类型
    edge_types = {}
    for edge in edges:
        edge_type = edge.get('type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    print(f"  边类型分布: {edge_types}")
    
    # 显示一些示例实体
    print(f"\n📋 示例实体 (前5个):")
    entity_count = 0
    for node in nodes:
        if node.get('type') == 'entity' and entity_count < 5:
            name = node.get('name', 'unnamed')
            attrs = node.get('attributes', {})
            entity_type = attrs.get('entity_type', 'unknown')
            print(f"  {name} ({entity_type})")
            entity_count += 1
    
    return True

def test_reward_system():
    """测试奖励系统"""
    print("\n💰 测试奖励系统...")
    
    env = SceneBasedEnvironment()
    
    if not env.scenes:
        print("❌ 没有可用场景")
        return False
    
    scene_name = list(env.scenes.keys())[0]
    observation = env.reset(scene_name)
    
    # 测试不同动作的奖励
    test_actions = [
        ('examine', 'FloorPlan308-openable'),
        ('go_to', 'Bed_937'),
        ('wait', None),
        ('invalid_action', 'nonexistent_target')
    ]
    
    print(f"🎮 在场景 {scene_name} 中测试动作奖励:")
    
    for action, target in test_actions:
        # 重置环境
        observation = env.reset(scene_name)
        
        print(f"  动作: {action}, 目标: {target}")
        
        try:
            observation, reward, done, info = env.step(action, target)
            print(f"    奖励: {reward:.3f}, 完成: {done}, 信息: {info}")
        except Exception as e:
            print(f"    错误: {e}")
    
    return True

def main():
    """主函数"""
    print("🧪 开始环境修复测试")
    print("=" * 50)
    
    tests = [
        ("环境加载", test_environment_loading),
        ("KG数据访问", test_kg_data_access),
        ("奖励系统", test_reward_system),
        ("智能体交互", test_agent_interactions)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = "✅ 通过" if success else "❌ 失败"
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results[test_name] = f"❌ 异常: {str(e)[:50]}"
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print("🧪 测试结果汇总:")
    print("=" * 50)
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    # 保存测试结果
    timestamp = int(time.time())
    results_file = f"experiments/results/environment_test_{timestamp}.json"
    
    test_results = {
        'timestamp': timestamp,
        'test_results': results,
        'summary': {
            'total_tests': len(tests),
            'passed': sum(1 for r in results.values() if '✅' in r),
            'failed': sum(1 for r in results.values() if '❌' in r)
        }
    }
    
    Path(results_file).parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 测试结果已保存到: {results_file}")
    
    all_passed = all('✅' in r for r in results.values())
    if all_passed:
        print("🎉 所有测试通过！环境修复成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
    
    return all_passed

if __name__ == "__main__":
    main()
