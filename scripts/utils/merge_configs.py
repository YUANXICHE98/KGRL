#!/usr/bin/env python3
"""
配置合并工具 - 合并和管理配置文件
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Union

def load_config_file(file_path: Path) -> Dict[str, Any]:
    """加载配置文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(f) or {}
        elif file_path.suffix.lower() == '.json':
            return json.load(f)
        else:
            raise ValueError(f"不支持的配置文件格式: {file_path.suffix}")

def save_config_file(data: Dict[str, Any], file_path: Path):
    """保存配置文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        elif file_path.suffix.lower() == '.json':
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的配置文件格式: {file_path.suffix}")

def deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并字典"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def merge_configs(config_files: List[Path], output_file: Path):
    """合并多个配置文件"""
    print(f"🔗 合并配置文件...")
    
    merged_config = {}
    
    for config_file in config_files:
        print(f"  📄 加载: {config_file.name}")
        try:
            config_data = load_config_file(config_file)
            merged_config = deep_merge_dicts(merged_config, config_data)
        except Exception as e:
            print(f"  ❌ 加载失败 {config_file.name}: {e}")
            continue
    
    # 保存合并结果
    save_config_file(merged_config, output_file)
    print(f"  ✅ 合并完成: {output_file}")
    
    return merged_config

def create_environment_configs():
    """创建环境特定的配置"""
    print("🌍 创建环境配置...")
    
    project_root = Path(__file__).parent.parent.parent
    configs_dir = project_root / "configs"
    
    # 基础配置
    base_config = {
        "project": {
            "name": "KGRL",
            "version": "1.0.0",
            "description": "Knowledge Graph Reinforcement Learning"
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    # 开发环境配置
    dev_config = deep_merge_dicts(base_config, {
        "environment": "development",
        "debug": True,
        "logging": {
            "level": "DEBUG"
        },
        "experiment": {
            "episodes": 3,
            "max_steps": 10
        }
    })
    
    # 生产环境配置
    prod_config = deep_merge_dicts(base_config, {
        "environment": "production",
        "debug": False,
        "experiment": {
            "episodes": 50,
            "max_steps": 20
        }
    })
    
    # 测试环境配置
    test_config = deep_merge_dicts(base_config, {
        "environment": "testing",
        "debug": True,
        "experiment": {
            "episodes": 1,
            "max_steps": 5
        }
    })
    
    # 保存配置文件
    environments_dir = configs_dir / "environments"
    environments_dir.mkdir(parents=True, exist_ok=True)
    
    configs = {
        "development.yaml": dev_config,
        "production.yaml": prod_config,
        "testing.yaml": test_config
    }
    
    for filename, config in configs.items():
        config_file = environments_dir / filename
        save_config_file(config, config_file)
        print(f"  ✅ {filename}")
    
    return configs

def create_agent_configs():
    """创建智能体配置"""
    print("\n🤖 创建智能体配置...")
    
    project_root = Path(__file__).parent.parent.parent
    configs_dir = project_root / "configs"
    
    # LLM基线配置
    llm_config = {
        "agent_type": "llm_baseline",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 150,
        "system_prompt": "You are an AI agent in a virtual environment. Choose actions wisely."
    }
    
    # ReAct配置
    react_config = {
        "agent_type": "react",
        "model": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 200,
        "reasoning_steps": 3,
        "action_space": ["go_to", "examine", "pick_up", "open", "close", "wait"]
    }
    
    # RAG配置
    rag_config = {
        "agent_type": "rag",
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 180,
        "knowledge_base": "enhanced_kg",
        "retrieval_top_k": 5,
        "similarity_threshold": 0.7
    }
    
    # 保存智能体配置
    agents_dir = configs_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    
    agent_configs = {
        "llm_baseline.yaml": llm_config,
        "react.yaml": react_config,
        "rag.yaml": rag_config
    }
    
    for filename, config in agent_configs.items():
        config_file = agents_dir / filename
        save_config_file(config, config_file)
        print(f"  ✅ {filename}")
    
    return agent_configs

def create_experiment_configs():
    """创建实验配置"""
    print("\n🧪 创建实验配置...")
    
    project_root = Path(__file__).parent.parent.parent
    configs_dir = project_root / "configs"
    
    # 基线对比实验
    baseline_experiment = {
        "experiment_name": "baseline_comparison",
        "description": "Compare LLM, ReAct, and RAG agents",
        "agents": ["llm_baseline", "react", "rag"],
        "episodes": 12,
        "max_steps": 15,
        "scenes": "random_sample",
        "metrics": ["reward", "success_rate", "steps", "actions"],
        "visualization": True,
        "save_results": True
    }
    
    # 快速测试实验
    quick_test = {
        "experiment_name": "quick_test",
        "description": "Quick functionality test",
        "agents": ["llm_baseline"],
        "episodes": 3,
        "max_steps": 10,
        "scenes": ["FloorPlan202-openable"],
        "metrics": ["reward", "steps"],
        "visualization": False,
        "save_results": True
    }
    
    # 完整评估实验
    full_evaluation = {
        "experiment_name": "full_evaluation",
        "description": "Comprehensive agent evaluation",
        "agents": ["llm_baseline", "react", "rag"],
        "episodes": 50,
        "max_steps": 20,
        "scenes": "all_available",
        "metrics": ["reward", "success_rate", "steps", "actions", "reasoning_traces"],
        "visualization": True,
        "save_results": True,
        "statistical_analysis": True
    }
    
    # 保存实验配置
    experiments_dir = configs_dir / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    
    experiment_configs = {
        "baseline_comparison.yaml": baseline_experiment,
        "quick_test.yaml": quick_test,
        "full_evaluation.yaml": full_evaluation
    }
    
    for filename, config in experiment_configs.items():
        config_file = experiments_dir / filename
        save_config_file(config, config_file)
        print(f"  ✅ {filename}")
    
    return experiment_configs

def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """验证配置文件"""
    errors = []
    
    def check_required_fields(data, schema_part, path=""):
        for key, value in schema_part.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                if "required" in value and value["required"]:
                    if key not in data:
                        errors.append(f"缺少必需字段: {current_path}")
                    elif "type" in value:
                        expected_type = value["type"]
                        actual_value = data[key]
                        
                        if expected_type == "string" and not isinstance(actual_value, str):
                            errors.append(f"字段类型错误 {current_path}: 期望string，实际{type(actual_value).__name__}")
                        elif expected_type == "number" and not isinstance(actual_value, (int, float)):
                            errors.append(f"字段类型错误 {current_path}: 期望number，实际{type(actual_value).__name__}")
                        elif expected_type == "boolean" and not isinstance(actual_value, bool):
                            errors.append(f"字段类型错误 {current_path}: 期望boolean，实际{type(actual_value).__name__}")
                
                if key in data and isinstance(data[key], dict):
                    check_required_fields(data[key], value, current_path)
    
    check_required_fields(config, schema)
    return errors

def main():
    """主配置管理函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="KGRL配置管理工具")
    parser.add_argument("--action", "-a", type=str, required=True,
                       choices=['merge', 'create', 'validate'],
                       help="操作类型")
    parser.add_argument("--files", "-f", nargs='+',
                       help="要合并的配置文件列表")
    parser.add_argument("--output", "-o", type=str,
                       help="输出文件路径")
    parser.add_argument("--type", "-t", type=str,
                       choices=['environment', 'agent', 'experiment', 'all'],
                       help="创建配置的类型")
    
    args = parser.parse_args()
    
    print("⚙️ KGRL配置管理工具")
    print("=" * 30)
    
    try:
        if args.action == 'merge':
            if not args.files or not args.output:
                print("❌ 合并操作需要指定 --files 和 --output")
                return
            
            config_files = [Path(f) for f in args.files]
            output_file = Path(args.output)
            
            merged_config = merge_configs(config_files, output_file)
            print(f"✅ 配置合并完成")
        
        elif args.action == 'create':
            if args.type == 'environment' or args.type == 'all':
                create_environment_configs()
            
            if args.type == 'agent' or args.type == 'all':
                create_agent_configs()
            
            if args.type == 'experiment' or args.type == 'all':
                create_experiment_configs()
            
            print(f"✅ 配置创建完成")
        
        elif args.action == 'validate':
            print("ℹ️ 配置验证功能待实现")
    
    except Exception as e:
        print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main()
