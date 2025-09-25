#!/usr/bin/env python3
"""
真实KGRL实验脚本
使用真实LLM调用，详细输出每一步的原始响应
"""

import os
import sys
import json
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.baseline_agents import LLMBaselineAgent, ReActAgent, RAGAgent
from src.environments.scene_based_env import SceneBasedEnvironment
from tools.visualization.agent_path_tracker import AgentPathTracker

def setup_experiment_directory() -> str:
    """设置实验目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_id = f"real_experiment_{timestamp}"
    
    # 创建实验目录结构
    base_dir = project_root / "experiments" / "results" / experiment_id
    base_dir.mkdir(parents=True, exist_ok=True)
    
    (base_dir / "results").mkdir(exist_ok=True)
    (base_dir / "reports").mkdir(exist_ok=True)
    (base_dir / "logs").mkdir(exist_ok=True)
    
    print(f"🗂️ Experiment directory created: {base_dir}")
    return str(base_dir)

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = project_root / "configs" / "agents" / "llm_baseline.yaml"

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config

def setup_openai_from_config() -> bool:
    """从配置文件设置OpenAI API"""
    config = load_config()

    if not config:
        print("❌ Failed to load configuration")
        return False

    # 从配置中获取API密钥
    llm_config = config.get('llm', {})
    api_key_template = llm_config.get('api_key', '')

    # 处理环境变量模板
    if api_key_template.startswith('${') and api_key_template.endswith('}'):
        env_var = api_key_template[2:-1]  # 移除 ${ 和 }
        api_key = os.getenv(env_var)
    else:
        api_key = api_key_template

    if not api_key:
        print(f"❌ API key not found. Template: {api_key_template}")
        print("💡 Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")

        # 尝试直接从配置文件读取（如果有明文密钥）
        if 'sk-' in api_key_template:
            api_key = api_key_template
            print("🔑 Using API key from config file")
        else:
            return False

    # 设置环境变量
    os.environ['OPENAI_API_KEY'] = api_key
    print(f"✅ OpenAI API key configured: {api_key[:10]}...")

    return True

def run_agent_episode(agent, agent_name: str, env, scene_name: str, 
                     max_steps: int = 10, experiment_dir: str = None) -> Dict[str, Any]:
    """运行单个智能体的episode，记录详细信息"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting {agent_name} episode in {scene_name}")
    print(f"{'='*60}")
    
    # 重置环境和智能体
    observation = env.reset()
    agent.reset()
    
    # 创建路径追踪器
    tracker = AgentPathTracker()
    
    # 记录详细日志
    episode_log = {
        'agent': agent_name,
        'scene': scene_name,
        'start_time': datetime.now().isoformat(),
        'steps': [],
        'total_reward': 0.0,
        'success': False
    }
    
    print(f"🌍 Initial observation:")
    print(f"📍 Location: {observation.get('agent_location', 'unknown')}")
    print(f"👀 Visible entities: {observation.get('visible_entities', [])}")
    print(f"🎒 Inventory: {observation.get('agent_inventory', [])}")
    print(f"⚡ Available actions: {observation.get('available_actions', [])}")
    
    for step in range(1, max_steps + 1):
        print(f"\n🔄 STEP {step}/{max_steps}")
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
                reasoning_trace=reasoning_trace
            )
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
                reasoning_trace=f"{agent_name}: {action} -> {target}"
            )
        
        step_time = time.time() - step_start_time
        
        # 执行动作
        print(f"🎬 Executing action: {action} -> {target}")
        try:
            observation, reward, done, info = env.step(action, target)
            print(f"🏆 Reward: {reward}")
            print(f"✅ Done: {done}")
            print(f"ℹ️ Info: {info}")
            
            # 更新追踪器中的奖励
            if hasattr(tracker, 'agent_paths') and agent_name in tracker.agent_paths:
                if tracker.agent_paths[agent_name]:
                    tracker.agent_paths[agent_name][-1]['reward'] = reward
            
        except Exception as e:
            print(f"❌ Action execution failed: {e}")
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
            'observation': observation,
            'done': done,
            'info': info
        }
        
        if agent_name == 'rag':
            step_info['kg_nodes_accessed'] = kg_nodes_accessed if 'kg_nodes_accessed' in locals() else []
            step_info['reasoning_trace'] = reasoning_trace if 'reasoning_trace' in locals() else ""
        
        episode_log['steps'].append(step_info)
        episode_log['total_reward'] += reward
        
        print(f"📊 Step summary:")
        print(f"  - Action: {action} -> {target}")
        print(f"  - Reward: {reward}")
        print(f"  - Total reward: {episode_log['total_reward']:.3f}")
        print(f"  - Step time: {step_time:.3f}s")
        
        if done:
            print(f"🎉 Episode completed successfully!")
            episode_log['success'] = True
            break
    
    episode_log['end_time'] = datetime.now().isoformat()
    episode_log['total_steps'] = len(episode_log['steps'])
    
    # 保存详细日志
    if experiment_dir:
        log_file = Path(experiment_dir) / "logs" / f"{agent_name}_{scene_name}_detailed.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(episode_log, f, indent=2, ensure_ascii=False)
        print(f"💾 Detailed log saved: {log_file}")
        
        # 保存路径追踪
        tracker.save_results(Path(experiment_dir) / "results", scene_name)
    
    print(f"\n📈 {agent_name} Episode Summary:")
    print(f"  - Total steps: {episode_log['total_steps']}")
    print(f"  - Total reward: {episode_log['total_reward']:.3f}")
    print(f"  - Success: {episode_log['success']}")
    
    return episode_log

def main():
    """主实验函数"""
    print("🧪 Starting Real KGRL Experiment")
    print("=" * 60)
    
    # 设置OpenAI API
    if not setup_openai_from_config():
        print("⚠️ Running without OpenAI API - using simulated responses")
        input("Press Enter to continue or Ctrl+C to exit...")
    
    # 设置实验目录
    experiment_dir = setup_experiment_directory()
    
    # 实验配置
    config = {
        'scenes': ['FloorPlan202-openable', 'FloorPlan308-openable'],
        'agents': ['llm_baseline', 'react', 'rag'],
        'max_steps': 10,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"🔧 Experiment configuration:")
    print(f"  - Scenes: {config['scenes']}")
    print(f"  - Agents: {config['agents']}")
    print(f"  - Max steps: {config['max_steps']}")
    
    # 保存配置
    config_file = Path(experiment_dir) / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # 初始化环境
    print(f"\n🌍 Initializing Scene-based environment...")
    env = SceneBasedEnvironment()
    
    # 运行实验
    all_results = {}
    
    for scene_name in config['scenes']:
        print(f"\n🏠 Loading scene: {scene_name}")
        
        try:
            env.load_scene(scene_name)
            scene_results = {}
            
            # 初始化智能体
            agents = {
                'llm_baseline': LLMBaselineAgent(),
                'react': ReActAgent(),
                'rag': RAGAgent()
            }
            
            # 运行每个智能体
            for agent_name in config['agents']:
                agent = agents[agent_name]
                
                try:
                    episode_result = run_agent_episode(
                        agent=agent,
                        agent_name=agent_name,
                        env=env,
                        scene_name=scene_name,
                        max_steps=config['max_steps'],
                        experiment_dir=experiment_dir
                    )
                    scene_results[agent_name] = episode_result
                    
                except Exception as e:
                    print(f"❌ Error running {agent_name}: {e}")
                    scene_results[agent_name] = {
                        'error': str(e),
                        'total_reward': 0.0,
                        'total_steps': 0,
                        'success': False
                    }
            
            all_results[scene_name] = scene_results
            
        except Exception as e:
            print(f"❌ Error loading scene {scene_name}: {e}")
            all_results[scene_name] = {'error': str(e)}
    
    # 保存总结果
    results_file = Path(experiment_dir) / "results" / "experiment_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n🎉 Experiment completed!")
    print(f"📁 Results saved in: {experiment_dir}")
    print(f"📊 Check the logs/ directory for detailed step-by-step information")

if __name__ == "__main__":
    main()
