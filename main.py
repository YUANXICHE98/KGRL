#!/usr/bin/env python3
"""
KGRL项目主入口脚本
提供统一的命令行接口来运行不同的实验和任务
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logging
from config.base_config import config

def run_week1_baseline():
    """运行Week 1基线实验"""
    print("🚀 Running Week 1 Baseline Experiment...")
    from experiments.week1_baseline import main as week1_main
    week1_main()

def run_week2_rag():
    """运行Week 2 RAG实验"""
    print("🚀 Running Week 2 RAG Experiment...")
    print("⚠️  Week 2 experiment not yet implemented")
    # from experiments.week2_rag import main as week2_main
    # week2_main()

def run_week3_evaluation():
    """运行Week 3评估实验"""
    print("🚀 Running Week 3 Evaluation Experiment...")
    print("⚠️  Week 3 experiment not yet implemented")
    # from experiments.week3_evaluation import main as week3_main
    # week3_main()

def run_interactive_demo():
    """运行交互式演示"""
    print("🎮 Starting Interactive Demo...")
    
    from src.agents.baseline_agent import BaselineAgent
    from src.environments.textworld_env import TextWorldEnvironment
    from config.agent_config import agent_configs
    
    # 创建环境和Agent
    env_config = {"max_episode_steps": 20, "difficulty": "easy"}
    environment = TextWorldEnvironment("demo_env", env_config)
    
    agent_config = {
        "model_name": "gpt-4o-mini",
        "use_local_model": False,
        "temperature": 0.7
    }
    agent = BaselineAgent("demo_agent", agent_config)
    
    print("\n" + "="*50)
    print("INTERACTIVE KGRL DEMO")
    print("="*50)
    print("Commands:")
    print("  - Type actions directly (e.g., 'look', 'go north', 'take key')")
    print("  - Type 'auto' to let the AI agent take over")
    print("  - Type 'reset' to restart the game")
    print("  - Type 'quit' to exit")
    print("="*50)
    
    # 重置环境
    observation = environment.reset()
    agent.reset()
    
    print(f"\n📍 {observation}")
    
    while True:
        try:
            # 显示可用动作
            available_actions = environment.get_available_actions()
            if available_actions:
                print(f"\n💡 Available actions: {', '.join(available_actions[:5])}{'...' if len(available_actions) > 5 else ''}")
            
            # 获取用户输入
            user_input = input("\n🎯 Your action (or 'auto'/'reset'/'quit'): ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'reset':
                observation = environment.reset()
                agent.reset()
                print(f"\n🔄 Game reset!\n📍 {observation}")
                continue
            elif user_input.lower() == 'auto':
                # AI接管
                action = agent.act(observation, available_actions)
                print(f"\n🤖 AI chooses: {action}")
            else:
                # 用户动作
                action = user_input
            
            # 执行动作
            new_observation, reward, done, info = environment.step(action)
            agent.update(action, new_observation, reward, done, info)
            
            print(f"\n📍 {new_observation}")
            if reward != 0:
                print(f"🎁 Reward: {reward}")
            
            if done:
                if reward > 0:
                    print("🎉 Congratulations! You completed the task!")
                else:
                    print("😔 Game over. Better luck next time!")
                
                restart = input("\n🔄 Start a new game? (y/n): ").strip().lower()
                if restart == 'y':
                    observation = environment.reset()
                    agent.reset()
                    print(f"\n🔄 New game started!\n📍 {observation}")
                else:
                    break
            else:
                observation = new_observation
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue
    
    environment.close()
    print("\n👋 Thanks for trying the KGRL demo!")

def show_project_status():
    """显示项目状态"""
    print("📊 KGRL Project Status")
    print("="*50)
    
    # 检查配置
    print("📋 Configuration:")
    print(f"  - Project root: {config.PROJECT_ROOT}")
    print(f"  - Data directory: {config.DATA_DIR}")
    print(f"  - Results directory: {config.RESULTS_DIR}")
    
    # 检查依赖
    print("\n📦 Dependencies:")
    try:
        import torch
        print(f"  ✅ PyTorch: {torch.__version__}")
    except ImportError:
        print("  ❌ PyTorch: Not installed")
    
    try:
        import transformers
        print(f"  ✅ Transformers: {transformers.__version__}")
    except ImportError:
        print("  ❌ Transformers: Not installed")
    
    try:
        import textworld
        print(f"  ✅ TextWorld: Available")
    except ImportError:
        print("  ⚠️  TextWorld: Not installed (will use mock environment)")
    
    try:
        import openai
        print(f"  ✅ OpenAI: {openai.__version__}")
    except ImportError:
        print("  ❌ OpenAI: Not installed")
    
    # 检查API密钥
    print("\n🔑 API Keys:")
    print(f"  - OpenAI: {'✅ Set' if config.OPENAI_API_KEY else '❌ Not set'}")
    print(f"  - Anthropic: {'✅ Set' if config.ANTHROPIC_API_KEY else '❌ Not set'}")
    print(f"  - WandB: {'✅ Set' if config.WANDB_API_KEY else '❌ Not set'}")
    
    # 检查目录结构
    print("\n📁 Directory Structure:")
    important_dirs = [
        config.DATA_DIR,
        config.RESULTS_DIR,
        config.KG_DIR,
        config.LOGS_DIR
    ]
    
    for dir_path in important_dirs:
        if dir_path.exists():
            print(f"  ✅ {dir_path.name}: {dir_path}")
        else:
            print(f"  ❌ {dir_path.name}: Missing")
    
    # 检查实验结果
    print("\n📈 Experiment Results:")
    results_files = list(config.RESULTS_DIR.glob("**/*/results.json"))
    if results_files:
        for result_file in results_files:
            print(f"  📄 {result_file.parent.name}: {result_file}")
    else:
        print("  📭 No experiment results found")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="KGRL: Knowledge Graph Enhanced Reinforcement Learning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --week1          # Run Week 1 baseline experiment
  python main.py --demo           # Run interactive demo
  python main.py --status         # Show project status
  python main.py --week2          # Run Week 2 RAG experiment (coming soon)
        """
    )
    
    # 实验选项
    parser.add_argument("--week1", action="store_true", help="Run Week 1 baseline experiment")
    parser.add_argument("--week2", action="store_true", help="Run Week 2 RAG experiment")
    parser.add_argument("--week3", action="store_true", help="Run Week 3 evaluation experiment")
    
    # 工具选项
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")
    parser.add_argument("--status", action="store_true", help="Show project status")
    
    # 配置选项
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    parser.add_argument("--config", help="Path to custom config file")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(log_level=args.log_level)
    
    # 如果没有指定任何选项，显示帮助
    if not any([args.week1, args.week2, args.week3, args.demo, args.status]):
        parser.print_help()
        return
    
    try:
        # 执行相应的功能
        if args.status:
            show_project_status()
        
        if args.demo:
            run_interactive_demo()
        
        if args.week1:
            run_week1_baseline()
        
        if args.week2:
            run_week2_rag()
        
        if args.week3:
            run_week3_evaluation()
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
