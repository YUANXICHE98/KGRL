#!/usr/bin/env python3
"""
配置文件验证脚本
检查配置文件的一致性和完整性
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_manager import config_manager

def validate_agent_configs() -> Dict[str, bool]:
    """验证智能体配置"""
    print("🤖 验证智能体配置...")
    
    results = {}
    agent_types = ['llm_baseline', 'react', 'rag']
    
    for agent_type in agent_types:
        try:
            config = config_manager.get_agent_config(agent_type)
            
            # 检查必需字段
            required_fields = ['agent_name', 'agent_type']
            missing_fields = []
            
            for field in required_fields:
                if field not in config:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ {agent_type}: 缺少字段 {missing_fields}")
                results[agent_type] = False
            else:
                print(f"✅ {agent_type}: 配置有效")
                results[agent_type] = True
                
        except Exception as e:
            print(f"❌ {agent_type}: 配置加载失败 - {e}")
            results[agent_type] = False
    
    return results

def validate_environment_configs() -> Dict[str, bool]:
    """验证环境配置"""
    print("\n🌍 验证环境配置...")
    
    results = {}
    env_types = ['alfworld', 'textworld']
    
    for env_type in env_types:
        try:
            config = config_manager.get_environment_config(env_type)
            
            # 检查必需字段
            required_fields = ['settings', 'rewards', 'action_space']
            missing_fields = []
            
            for field in required_fields:
                if field not in config:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ {env_type}: 缺少字段 {missing_fields}")
                results[env_type] = False
            else:
                print(f"✅ {env_type}: 配置有效")
                results[env_type] = True
                
        except Exception as e:
            print(f"❌ {env_type}: 配置加载失败 - {e}")
            results[env_type] = False
    
    return results

def check_config_consistency() -> bool:
    """检查配置一致性"""
    print("\n🔍 检查配置一致性...")
    
    try:
        # 检查智能体配置中的环境引用
        agent_config = config_manager.get_config('agents')
        env_config = config_manager.get_config('environments')
        
        # 检查环境类型一致性
        agent_env_type = agent_config.get('environment', {}).get('default_type', 'alfworld')
        available_envs = list(env_config.get('environments', {}).keys())
        
        if agent_env_type not in available_envs:
            print(f"❌ 智能体默认环境类型 '{agent_env_type}' 在环境配置中不存在")
            return False
        
        # 检查奖励设置一致性
        for env_type in available_envs:
            env_rewards = env_config['environments'][env_type].get('rewards', {})
            required_rewards = ['success', 'failure', 'step_penalty', 'invalid_action']
            
            missing_rewards = [r for r in required_rewards if r not in env_rewards]
            if missing_rewards:
                print(f"❌ {env_type} 环境缺少奖励设置: {missing_rewards}")
                return False
        
        print("✅ 配置一致性检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置一致性检查失败: {e}")
        return False

def check_api_keys() -> bool:
    """检查API密钥配置"""
    print("\n🔑 检查API密钥配置...")
    
    try:
        llm_config = config_manager.get_agent_config('llm_baseline')
        api_key = llm_config.get('llm', {}).get('api_key', '')
        
        if not api_key:
            print("❌ 未找到API密钥配置")
            return False
        
        if api_key.startswith('sk-'):
            print("✅ 找到有效的API密钥")
            return True
        elif api_key.startswith('${') and api_key.endswith('}'):
            import os
            env_var = api_key[2:-1]
            actual_key = os.getenv(env_var)
            if actual_key and actual_key.startswith('sk-'):
                print(f"✅ 环境变量 {env_var} 中找到有效的API密钥")
                return True
            else:
                print(f"❌ 环境变量 {env_var} 未设置或无效")
                return False
        else:
            print("❌ API密钥格式无效")
            return False
            
    except Exception as e:
        print(f"❌ API密钥检查失败: {e}")
        return False

def generate_config_summary() -> None:
    """生成配置摘要"""
    print("\n📊 配置摘要:")
    print("=" * 50)
    
    try:
        # 主配置
        main_config = config_manager.get_config('main')
        project_info = main_config.get('project', {})
        print(f"项目: {project_info.get('name', 'N/A')} v{project_info.get('version', 'N/A')}")
        
        # 智能体配置
        agent_configs = config_manager.list_configs()
        agent_files = [f for f in agent_configs.keys() if f.startswith('agents_')]
        print(f"智能体配置文件: {len(agent_files)} 个")
        
        # 环境配置
        env_config = config_manager.get_config('environments')
        env_types = list(env_config.get('environments', {}).keys())
        print(f"支持的环境类型: {', '.join(env_types)}")
        
        # 知识图谱配置
        kg_config = config_manager.get_config('kg')
        if kg_config:
            print("知识图谱: 已配置")
        else:
            print("知识图谱: 未配置")
        
        # Neo4j配置
        neo4j_config = config_manager.get_config('neo4j')
        if neo4j_config:
            connection = neo4j_config.get('database', {}).get('connection', {})
            uri = connection.get('uri', 'N/A')
            print(f"Neo4j: {uri}")
        else:
            print("Neo4j: 未配置")
            
    except Exception as e:
        print(f"❌ 生成配置摘要失败: {e}")

def main():
    """主验证函数"""
    print("🔧 KGRL 配置验证工具")
    print("=" * 50)
    
    # 验证各类配置
    agent_results = validate_agent_configs()
    env_results = validate_environment_configs()
    consistency_ok = check_config_consistency()
    api_key_ok = check_api_keys()
    
    # 生成摘要
    generate_config_summary()
    
    # 总结结果
    print("\n🎯 验证结果:")
    print("=" * 50)
    
    total_checks = len(agent_results) + len(env_results) + 2  # +2 for consistency and api key
    passed_checks = sum(agent_results.values()) + sum(env_results.values())
    if consistency_ok:
        passed_checks += 1
    if api_key_ok:
        passed_checks += 1
    
    print(f"通过检查: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("🎉 所有配置验证通过！")
        return True
    else:
        print("⚠️ 部分配置需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
