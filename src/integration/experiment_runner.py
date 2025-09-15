"""
Experiment Runner for KGRL research framework.

Provides unified experiment execution and management.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml

from ..agents.unified_agent import UnifiedAgent
from ..environments.textworld_adapter import TextWorldAdapter
from ..evaluation.evaluator import AgentEvaluator
from ..utils.logging_utils import ExperimentLogger
from ..utils.metrics import MetricsCalculator


class ExperimentRunner:
    """Unified experiment runner for KGRL research."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Experiment configuration
        self.experiment_name = self.config.get("experiment_name", "default_experiment")
        self.output_dir = Path(self.config.get("output_dir", "experiments/results"))
        self.save_checkpoints = self.config.get("save_checkpoints", True)
        self.checkpoint_interval = self.config.get("checkpoint_interval", 10)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize experiment logger
        self.exp_logger = ExperimentLogger(
            self.experiment_name,
            str(self.output_dir.parent / "logs")
        )
        
        self.logger.info(f"Initialized experiment runner: {self.experiment_name}")
    
    def run_single_experiment(
        self,
        agent_config: Dict[str, Any],
        env_config: Dict[str, Any],
        eval_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a single experiment with given configurations.
        
        Args:
            agent_config: Agent configuration
            env_config: Environment configuration
            eval_config: Evaluation configuration
            
        Returns:
            Experiment results
        """
        self.logger.info("Starting single experiment")
        
        # Log configurations
        self.exp_logger.log_config({
            "agent_config": agent_config,
            "env_config": env_config,
            "eval_config": eval_config
        })
        
        try:
            # Create agent
            agent = UnifiedAgent(agent_config)
            
            # Create environment
            environment = TextWorldAdapter(env_config)
            
            # Create evaluator
            evaluator = AgentEvaluator(eval_config)
            
            # Run evaluation
            results = evaluator.evaluate_agent(agent, environment)
            
            # Log results
            self.exp_logger.log_results(results)
            
            # Save results
            results_file = self.output_dir / f"{self.experiment_name}_results.json"
            evaluator.save_results(results, str(results_file))
            
            # Cleanup
            agent.cleanup()
            environment.cleanup()
            
            self.logger.info("Single experiment completed successfully")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Experiment failed: {e}")
            raise
    
    def run_ablation_study(self, ablation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run ablation study with multiple agent configurations.
        
        Args:
            ablation_config: Ablation study configuration
            
        Returns:
            Ablation study results
        """
        self.logger.info("Starting ablation study")
        
        # Extract configurations
        agent_configs = ablation_config.get("agent_configs", [])
        env_config = ablation_config.get("environment", {})
        eval_config = ablation_config.get("evaluation", {})
        
        if not agent_configs:
            raise ValueError("No agent configurations provided for ablation study")
        
        # Log ablation configuration
        self.exp_logger.log_config(ablation_config)
        
        # Results storage
        ablation_results = {}
        
        # Run each configuration
        for i, agent_config in enumerate(agent_configs):
            config_name = agent_config.get("name", f"config_{i}")
            
            self.logger.info(f"Running ablation configuration: {config_name}")
            
            try:
                # Create agent
                agent = UnifiedAgent(agent_config)
                
                # Create environment
                environment = TextWorldAdapter(env_config)
                
                # Create evaluator
                evaluator = AgentEvaluator(eval_config)
                
                # Run evaluation
                results = evaluator.evaluate_agent(agent, environment)
                
                # Store results
                ablation_results[config_name] = results
                
                # Log configuration results
                self.exp_logger.log_step(i, {
                    "config": config_name,
                    "success_rate": results.get("success_rate", 0),
                    "avg_reward": results.get("avg_reward", 0)
                })
                
                # Save checkpoint
                if self.save_checkpoints and (i + 1) % self.checkpoint_interval == 0:
                    checkpoint_file = self.output_dir / f"ablation_checkpoint_{i+1}.json"
                    evaluator.save_results(ablation_results, str(checkpoint_file))
                
                # Cleanup
                agent.cleanup()
                environment.cleanup()
                
            except Exception as e:
                self.logger.error(f"Failed to run configuration {config_name}: {e}")
                ablation_results[config_name] = {"error": str(e)}
        
        # Create comparison analysis
        comparison = self._analyze_ablation_results(ablation_results)
        
        # Final results
        final_results = {
            "ablation_config": ablation_config,
            "individual_results": ablation_results,
            "comparison_analysis": comparison
        }
        
        # Log final results
        self.exp_logger.log_results(final_results)
        
        # Save final results
        results_file = self.output_dir / f"{self.experiment_name}_ablation_results.json"
        self._save_results(final_results, str(results_file))
        
        self.logger.info("Ablation study completed")
        
        return final_results
    
    def run_comparison_study(
        self,
        agent_configs: List[Dict[str, Any]],
        env_config: Dict[str, Any],
        eval_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run comparison study between different agents.
        
        Args:
            agent_configs: List of agent configurations
            env_config: Environment configuration
            eval_config: Evaluation configuration
            
        Returns:
            Comparison results
        """
        self.logger.info(f"Starting comparison study with {len(agent_configs)} agents")
        
        # Create agents
        agents = []
        for config in agent_configs:
            agent_name = config.get("name", f"agent_{len(agents)}")
            agent = UnifiedAgent(config)
            agents.append((agent_name, agent))
        
        # Create environment
        environment = TextWorldAdapter(env_config)
        
        # Create evaluator
        evaluator = AgentEvaluator(eval_config)
        
        # Run comparison
        results = evaluator.compare_agents(agents, environment)
        
        # Log results
        self.exp_logger.log_results(results)
        
        # Save results
        results_file = self.output_dir / f"{self.experiment_name}_comparison_results.json"
        evaluator.save_results(results, str(results_file))
        
        # Cleanup
        for _, agent in agents:
            agent.cleanup()
        environment.cleanup()
        
        self.logger.info("Comparison study completed")
        
        return results
    
    def _analyze_ablation_results(self, ablation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ablation study results."""
        if not ablation_results:
            return {}
        
        # Extract key metrics
        metrics = ["success_rate", "avg_reward", "avg_steps"]
        analysis = {}
        
        for metric in metrics:
            metric_values = {}
            
            for config_name, results in ablation_results.items():
                if isinstance(results, dict) and metric in results:
                    metric_values[config_name] = results[metric]
            
            if metric_values:
                best_config = max(metric_values, key=metric_values.get)
                worst_config = min(metric_values, key=metric_values.get)
                
                analysis[metric] = {
                    "values": metric_values,
                    "best_config": best_config,
                    "best_value": metric_values[best_config],
                    "worst_config": worst_config,
                    "worst_value": metric_values[worst_config],
                    "improvement": metric_values[best_config] - metric_values[worst_config]
                }
        
        return analysis
    
    def _save_results(self, results: Dict[str, Any], filepath: str):
        """Save results to JSON file."""
        try:
            import json
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Saved results to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def load_config_from_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate experiment report."""
        if not results:
            return "No results available"
        
        report = f"""
=== Experiment Report: {self.experiment_name} ===

Experiment Type: {results.get('experiment_type', 'Unknown')}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        # Add specific report sections based on result type
        if "individual_results" in results:
            report += self._generate_ablation_report(results)
        elif "comparison" in results:
            report += self._generate_comparison_report(results)
        else:
            report += self._generate_single_experiment_report(results)
        
        report += "\n" + "=" * 50 + "\n"
        
        return report
    
    def _generate_ablation_report(self, results: Dict[str, Any]) -> str:
        """Generate ablation study report."""
        report = "Ablation Study Results:\n\n"
        
        individual_results = results.get("individual_results", {})
        comparison = results.get("comparison_analysis", {})
        
        for config_name, config_results in individual_results.items():
            if isinstance(config_results, dict) and "success_rate" in config_results:
                report += f"{config_name}:\n"
                report += f"  Success Rate: {config_results.get('success_rate', 0):.2%}\n"
                report += f"  Avg Reward: {config_results.get('avg_reward', 0):.3f}\n"
                report += f"  Avg Steps: {config_results.get('avg_steps', 0):.1f}\n\n"
        
        # Add comparison analysis
        if comparison:
            report += "Best Configurations:\n"
            for metric, analysis in comparison.items():
                report += f"  {metric}: {analysis.get('best_config', 'N/A')} "
                report += f"({analysis.get('best_value', 0):.3f})\n"
        
        return report
    
    def _generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """Generate comparison study report."""
        report = "Agent Comparison Results:\n\n"
        
        individual_results = results.get("individual_results", {})
        comparison = results.get("comparison", {})
        
        for agent_name, agent_results in individual_results.items():
            report += f"{agent_name}:\n"
            report += f"  Success Rate: {agent_results.get('success_rate', 0):.2%}\n"
            report += f"  Avg Reward: {agent_results.get('avg_reward', 0):.3f}\n"
            report += f"  Avg Steps: {agent_results.get('avg_steps', 0):.1f}\n\n"
        
        return report
    
    def _generate_single_experiment_report(self, results: Dict[str, Any]) -> str:
        """Generate single experiment report."""
        report = "Single Experiment Results:\n\n"
        report += f"Success Rate: {results.get('success_rate', 0):.2%}\n"
        report += f"Average Reward: {results.get('avg_reward', 0):.3f}\n"
        report += f"Average Steps: {results.get('avg_steps', 0):.1f}\n"
        report += f"Total Episodes: {results.get('total_episodes', 0)}\n"
        
        return report
    
    def cleanup(self):
        """Clean up experiment runner resources."""
        if hasattr(self, 'exp_logger'):
            self.exp_logger.cleanup()
        
        self.logger.info("Experiment runner cleanup completed")
