#!/usr/bin/env python3
"""
简化的KGRL实验脚本
使用简化配置，清晰的逻辑，详细的输出
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.simple_config import get_config
from src.agents.baseline_agents import LLMBaselineAgent, ReActAgent, RAGAgent
from src.environments.scene_based_env import SceneBasedEnvironment
from src.utils.agent_path_tracker import AgentPathTracker

def setup_experiment() -> Tuple[str, Dict[str, Any]]:
    """设置实验"""
    print("🔧 设置实验环境...")
    
    # 加载配置
    config = get_config()
    
    # 验证配置
    if not config.validate():
        raise ValueError("配置验证失败")
    
    # 打印配置摘要
    config.print_summary()
    
    # 创建实验目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_id = f"simple_experiment_{timestamp}"
    
    experiment_dir = project_root / "experiments" / "results" / experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建子目录
    (experiment_dir / "logs").mkdir(exist_ok=True)
    (experiment_dir / "results").mkdir(exist_ok=True)
    
    print(f"📁 实验目录: {experiment_dir}")
    
    # 保存配置到实验目录
    config.save(experiment_dir / "config.yaml")
    
    return str(experiment_dir), config.config

def run_agent_episode(agent, agent_name: str, env, scene_name: str,
                     config: Dict[str, Any], experiment_dir: str) -> Dict[str, Any]:
    """运行单个智能体的episode"""
    agent_emoji = {'llm_baseline': '🤖', 'react': '🧠', 'rag': '🔍'}
    agent_desc = {
        'llm_baseline': 'LLM基线智能体 (纯LLM推理)',
        'react': 'ReAct智能体 (思考-行动-观察)',
        'rag': 'RAG智能体 (检索增强生成)'
    }

    print(f"\n{'🚀' * 25}")
    print(f"{agent_emoji.get(agent_name, '🤖')} 【{agent_name.upper()}】 {agent_desc.get(agent_name, agent_name)}")
    print(f"🏠 场景: {scene_name}")
    print(f"{'🚀' * 25}")
    print()
    
    # 重置环境和智能体到指定场景
    observation = env.reset(scene_name)
    agent.reset({'scene_name': scene_name})
    
    # 创建路径追踪器
    tracker = AgentPathTracker(scene_name)
    
    # 实验配置
    max_steps = config.get('experiment', {}).get('max_steps_per_episode', 10)
    
    # 记录episode信息
    episode_data = {
        'agent': agent_name,
        'scene': scene_name,
        'start_time': datetime.now().isoformat(),
        'steps': [],
        'total_reward': 0.0,
        'success': False
    }
    
    print(f"🌍 初始观察:")
    print(f"  位置: {observation.get('agent_location', 'unknown')}")
    print(f"  可见实体: {observation.get('visible_entities', [])[:5]}...")
    print(f"  库存: {observation.get('agent_inventory', [])}")
    print(f"  可用动作: {observation.get('available_actions', [])}")
    
    for step in range(1, max_steps + 1):
        print(f"\n🔄 步骤 {step}/{max_steps}")
        print(f"{'─'*40}")
        
        step_start_time = time.time()
        
        # 智能体选择动作
        if agent_name == 'rag' and hasattr(agent, 'select_action_with_tracking'):
            # RAG智能体使用追踪版本
            action, target, kg_nodes_accessed, reasoning_trace = agent.select_action_with_tracking(observation)
            
            # 记录KG节点访问
            tracker.record_step(
                agent_name=agent_name,
                step=step,
                action=action,
                target=target,
                reward=0.0,  # 将在执行后更新
                kg_nodes_accessed=kg_nodes_accessed,
                reasoning_trace=reasoning_trace,
                observation=observation
            )
            
            print(f"🔗 访问了 {len(kg_nodes_accessed)} 个KG节点")
            
        else:
            # 其他智能体使用标准版本
            action, target = agent.select_action(observation)
            
            # 记录步骤（无KG节点访问）
            tracker.record_step(
                agent_name=agent_name,
                step=step,
                action=action,
                target=target,
                reward=0.0,  # 将在执行后更新
                kg_nodes_accessed=[],
                reasoning_trace=f"{agent_name}: {action} -> {target}",
                observation=observation
            )
        
        step_time = time.time() - step_start_time
        
        # 执行动作
        print(f"🎬 执行动作: {action} -> {target}")
        try:
            observation, reward, done, info = env.step(action, target)
            print(f"🏆 奖励: {reward}")
            print(f"✅ 完成: {done}")
            if info:
                print(f"ℹ️ 信息: {info}")
            
            # 更新追踪器中的奖励
            if tracker.paths:
                tracker.paths[-1]['reward'] = reward
            
        except Exception as e:
            print(f"❌ 动作执行失败: {e}")
            reward = -0.1
            done = False
            info = {'error': str(e)}
        
        # 记录步骤详情
        step_info = {
            'step': step,
            'action': action,
            'target': target,
            'reward': reward,
            'step_time': step_time,
            'done': done,
            'info': info
        }
        
        if agent_name == 'rag':
            step_info['kg_nodes_accessed'] = kg_nodes_accessed if 'kg_nodes_accessed' in locals() else []
            step_info['reasoning_trace'] = reasoning_trace if 'reasoning_trace' in locals() else ""
        
        episode_data['steps'].append(step_info)
        episode_data['total_reward'] += reward
        
        print(f"📊 步骤总结:")
        print(f"  - 动作: {action} -> {target}")
        print(f"  - 奖励: {reward}")
        print(f"  - 累计奖励: {episode_data['total_reward']:.3f}")
        print(f"  - 用时: {step_time:.3f}s")
        
        if done:
            print(f"🎉 Episode成功完成!")
            episode_data['success'] = True
            break
    
    episode_data['end_time'] = datetime.now().isoformat()
    episode_data['total_steps'] = len(episode_data['steps'])
    
    # 保存详细日志
    log_file = Path(experiment_dir) / "logs" / f"{agent_name}_{scene_name}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(episode_data, f, indent=2, ensure_ascii=False)
    
    # 保存路径追踪
    tracker.save_results(str(Path(experiment_dir) / "results"))
    
    print(f"\n📈 {agent_name} Episode总结:")
    print(f"  - 总步数: {episode_data['total_steps']}")
    print(f"  - 总奖励: {episode_data['total_reward']:.3f}")
    print(f"  - 成功: {episode_data['success']}")

    # 添加智能体完成标识
    print(f"\n{'🔚' * 20} {agent_name.upper()} 完成 {'🔚' * 20}")
    print(f"⏱️  等待下一个智能体...")
    time.sleep(1)  # 短暂暂停以便观察

    return episode_data

def main():
    """主实验函数"""
    print("🧪 KGRL 简化实验")
    print("=" * 60)
    
    try:
        # 设置实验
        experiment_dir, config = setup_experiment()
        
        # 初始化环境
        print(f"\n🌍 初始化环境...")
        env = SceneBasedEnvironment()
        
        # 获取实验配置
        experiment_config = config.get('experiment', {})
        scenes = experiment_config.get('scenes', ['FloorPlan202-openable'])
        
        # 初始化智能体 - 传入配置
        llm_config = config.get('llm', {})
        agents_config = config.get('agents', {})

        agents = {
            'llm_baseline': LLMBaselineAgent(llm_config),
            'react': ReActAgent(llm_config),
            'rag': RAGAgent({**llm_config, **agents_config.get('rag', {})})
        }
        
        # 运行实验
        all_results = {}
        
        for scene_name in scenes:
            print(f"\n🏠 加载场景: {scene_name}")
            
            try:
                # 重置环境到指定场景
                env.reset(scene_name)
                scene_results = {}
                
                # 运行每个智能体
                for agent_name, agent in agents.items():
                    try:
                        episode_result = run_agent_episode(
                            agent=agent,
                            agent_name=agent_name,
                            env=env,
                            scene_name=scene_name,
                            config=config,
                            experiment_dir=experiment_dir
                        )
                        scene_results[agent_name] = episode_result
                        
                    except Exception as e:
                        print(f"❌ 运行 {agent_name} 时出错: {e}")
                        scene_results[agent_name] = {
                            'error': str(e),
                            'total_reward': 0.0,
                            'total_steps': 0,
                            'success': False
                        }
                
                all_results[scene_name] = scene_results
                
            except Exception as e:
                print(f"❌ 加载场景 {scene_name} 时出错: {e}")
                all_results[scene_name] = {'error': str(e)}
        
        # 保存总结果
        results_file = Path(experiment_dir) / "results" / "experiment_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n🎉 实验完成!")
        print(f"📁 结果保存在: {experiment_dir}")
        print(f"📊 详细日志在: {experiment_dir}/logs/")
        
    except Exception as e:
        print(f"❌ 实验失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
