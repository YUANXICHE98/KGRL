#!/usr/bin/env python3
"""
Unified training script for KGRL research framework.

This script provides a unified interface for training different agent configurations
and running experiments with various capability combinations.
"""

import argparse
import logging
import sys
from pathlib import Path
import yaml
import time
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents import UnifiedAgent
from environments import TextWorldAdapter
from utils import ConfigLoader, setup_logging
from evaluation import MetricsCollector


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train KGRL agents")
    
    parser.add_argument(
        "--config", 
        type=str, 
        required=True,
        help="Path to agent configuration file"
    )
    
    parser.add_argument(
        "--env-config",
        type=str,
        default="configs/environments/textworld.yaml",
        help="Path to environment configuration file"
    )
    
    parser.add_argument(
        "--mode-config",
        type=str,
        default=None,
        help="Path to mode configuration file"
    )
    
    parser.add_argument(
        "--num-episodes",
        type=int,
        default=100,
        help="Number of training episodes"
    )
    
    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="Maximum steps per episode"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/results",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    
    parser.add_argument(
        "--save-freq",
        type=int,
        default=10,
        help="Save checkpoint every N episodes"
    )
    
    parser.add_argument(
        "--eval-freq",
        type=int,
        default=20,
        help="Evaluate every N episodes"
    )
    
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_agent(config: Dict[str, Any], mode_config: Dict[str, Any] = None) -> UnifiedAgent:
    """Create agent from configuration."""
    # Merge mode configuration if provided
    if mode_config:
        # Update agent config with mode-specific settings
        config = {**config, **mode_config}
    
    agent_name = config.get("agent_name", "unified_agent")
    return UnifiedAgent(agent_name, config)


def create_environment(config: Dict[str, Any]):
    """Create environment from configuration."""
    env_type = config.get("environment_type", "textworld")
    
    if env_type == "textworld":
        return TextWorldAdapter(config)
    else:
        raise ValueError(f"Unsupported environment type: {env_type}")


def run_training_episode(agent: UnifiedAgent, env, max_steps: int, metrics: MetricsCollector) -> Dict[str, Any]:
    """Run a single training episode."""
    episode_start_time = time.time()
    
    # Reset environment and agent
    observation = env.reset()
    agent.reset()
    
    episode_reward = 0.0
    episode_steps = 0
    done = False
    
    episode_metrics = {
        "actions": [],
        "rewards": [],
        "observations": [],
        "decision_times": [],
    }
    
    while not done and episode_steps < max_steps:
        # Get available actions
        available_actions = env.get_available_actions()
        
        # Agent selects action
        action_start_time = time.time()
        action = agent.act(observation, available_actions)
        decision_time = time.time() - action_start_time
        
        # Execute action in environment
        next_observation, reward, done, info = env.step(action)
        
        # Update agent
        agent.update_reward(reward)
        
        # Record metrics
        episode_reward += reward
        episode_steps += 1
        
        episode_metrics["actions"].append(action)
        episode_metrics["rewards"].append(reward)
        episode_metrics["observations"].append(observation)
        episode_metrics["decision_times"].append(decision_time)
        
        # Update for next step
        observation = next_observation
    
    episode_time = time.time() - episode_start_time
    
    # Episode summary
    episode_summary = {
        "episode_reward": episode_reward,
        "episode_steps": episode_steps,
        "episode_time": episode_time,
        "success": info.get("success", episode_reward > 0),
        "metrics": episode_metrics
    }
    
    # Update metrics collector
    metrics.record_episode(episode_summary)
    
    return episode_summary


def run_evaluation(agent: UnifiedAgent, env, num_eval_episodes: int = 10, max_steps: int = 50) -> Dict[str, Any]:
    """Run evaluation episodes."""
    eval_metrics = MetricsCollector()
    
    for episode in range(num_eval_episodes):
        episode_summary = run_training_episode(agent, env, max_steps, eval_metrics)
        logging.info(f"Eval Episode {episode + 1}: reward={episode_summary['episode_reward']:.2f}, "
                    f"steps={episode_summary['episode_steps']}, success={episode_summary['success']}")
    
    return eval_metrics.get_summary()


def save_checkpoint(agent: UnifiedAgent, episode: int, output_dir: Path):
    """Save agent checkpoint."""
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_path = checkpoint_dir / f"agent_episode_{episode}.pkl"
    agent.save_checkpoint(str(checkpoint_path))
    
    logging.info(f"Checkpoint saved: {checkpoint_path}")


def save_results(metrics: MetricsCollector, agent_stats: Dict[str, Any], output_dir: Path):
    """Save training results."""
    results_dir = output_dir / "metrics"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metrics
    metrics_path = results_dir / "training_metrics.json"
    metrics.save_to_file(str(metrics_path))
    
    # Save agent statistics
    stats_path = results_dir / "agent_statistics.json"
    import json
    with open(stats_path, 'w') as f:
        json.dump(agent_stats, f, indent=2)
    
    logging.info(f"Results saved to {results_dir}")


def main():
    """Main training function."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger("train")
    
    # Set random seed
    import random
    import numpy as np
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    logger.info("Starting KGRL training")
    logger.info(f"Configuration: {args.config}")
    
    try:
        # Load configurations
        agent_config = load_config(args.config)
        env_config = load_config(args.env_config)
        
        mode_config = None
        if args.mode_config:
            mode_config = load_config(args.mode_config)
            logger.info(f"Mode configuration: {args.mode_config}")
        
        # Create agent and environment
        agent = create_agent(agent_config, mode_config)
        env = create_environment(env_config)
        
        logger.info(f"Agent created: {agent}")
        logger.info(f"Environment created: {type(env).__name__}")
        
        # Initialize metrics collector
        metrics = MetricsCollector()
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Training loop
        logger.info(f"Starting training for {args.num_episodes} episodes")
        
        for episode in range(1, args.num_episodes + 1):
            # Run training episode
            episode_summary = run_training_episode(agent, env, args.max_steps, metrics)
            
            # Log progress
            if episode % 10 == 0:
                logger.info(
                    f"Episode {episode}/{args.num_episodes}: "
                    f"reward={episode_summary['episode_reward']:.2f}, "
                    f"steps={episode_summary['episode_steps']}, "
                    f"success={episode_summary['success']}"
                )
            
            # Save checkpoint
            if episode % args.save_freq == 0:
                save_checkpoint(agent, episode, output_dir)
            
            # Run evaluation
            if episode % args.eval_freq == 0:
                logger.info(f"Running evaluation at episode {episode}")
                eval_results = run_evaluation(agent, env)
                logger.info(f"Evaluation results: {eval_results}")
        
        # Final evaluation
        logger.info("Running final evaluation")
        final_eval = run_evaluation(agent, env, num_eval_episodes=20)
        
        # Get final agent statistics
        agent_stats = agent.get_statistics()
        
        # Save results
        save_results(metrics, agent_stats, output_dir)
        
        # Print summary
        logger.info("Training completed successfully!")
        logger.info(f"Final agent statistics: {agent_stats}")
        logger.info(f"Final evaluation: {final_eval}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    
    finally:
        # Cleanup
        if 'agent' in locals():
            agent.cleanup()
        if 'env' in locals():
            env.cleanup()


if __name__ == "__main__":
    main()
