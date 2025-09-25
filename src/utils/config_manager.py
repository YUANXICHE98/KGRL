#!/usr/bin/env python3
"""
配置管理器
统一管理所有配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_root: str = "configs"):
        self.config_root = Path(config_root)
        self.configs = {}
        self.logger = logging.getLogger(__name__)
        
        # 加载主配置
        self.main_config = self.load_config("main_config.yaml")
        
    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """加载配置文件"""
        if isinstance(config_path, str):
            if not config_path.startswith('/') and not config_path.startswith('configs/'):
                config_path = self.config_root / config_path
            else:
                config_path = Path(config_path)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"✅ 加载配置文件: {config_path}")
            return config
            
        except FileNotFoundError:
            self.logger.error(f"❌ 配置文件不存在: {config_path}")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"❌ 配置文件格式错误: {config_path}, 错误: {e}")
            return {}
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """获取指定配置"""
        if config_name not in self.configs:
            # 根据配置名称映射到文件路径
            config_mapping = {
                'main': 'main_config.yaml',
                'kg': 'kg/kg_construction.yaml',
                'neo4j': 'neo4j/neo4j_config.yaml',
                'extraction': 'extraction/extraction_config.yaml',
                'agents': 'agents/agent_config.yaml',
                'environments': 'environments/environment_config.yaml'
            }
            
            if config_name in config_mapping:
                config_path = config_mapping[config_name]
                self.configs[config_name] = self.load_config(config_path)
            else:
                self.logger.warning(f"⚠️  未知配置名称: {config_name}")
                return {}
        
        return self.configs[config_name]
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """获取Neo4j配置"""
        return self.get_config('neo4j')
    
    def get_kg_config(self) -> Dict[str, Any]:
        """获取知识图谱配置"""
        return self.get_config('kg')
    
    def get_extraction_config(self) -> Dict[str, Any]:
        """获取数据抽取配置"""
        return self.get_config('extraction')
    
    def get_agent_config(self, agent_name: str = None) -> Dict[str, Any]:
        """获取智能体配置"""
        if agent_name:
            # 获取特定智能体配置
            agent_file_mapping = {
                'llm_baseline': 'agents/llm_baseline.yaml',
                'react': 'agents/rag_react_agent.yaml',
                'rag': 'agents/rag_react_agent.yaml',
                'kg_augmented': 'agents/kg_augmented.yaml',
                'rl_kg': 'agents/rl_kg_agent.yaml'
            }

            if agent_name in agent_file_mapping:
                return self.load_config(agent_file_mapping[agent_name])
            else:
                self.logger.warning(f"⚠️ 未知智能体类型: {agent_name}")
                return self.get_config('agents')
        else:
            return self.get_config('agents')
    
    def get_environment_config(self, env_type: str = None) -> Dict[str, Any]:
        """获取环境配置"""
        env_config = self.get_config('environments')

        if env_type and 'environments' in env_config:
            # 返回特定环境类型的配置
            if env_type in env_config['environments']:
                return env_config['environments'][env_type]
            else:
                self.logger.warning(f"⚠️ 未知环境类型: {env_type}")
                return env_config
        else:
            return env_config
    
    def get_database_connection_info(self) -> Dict[str, str]:
        """获取数据库连接信息"""
        neo4j_config = self.get_neo4j_config()
        return neo4j_config.get('database', {}).get('connection', {})
    
    def get_data_paths(self) -> Dict[str, str]:
        """获取数据路径配置"""
        main_config = self.get_config('main')
        return main_config.get('paths', {})
    
    def get_output_settings(self) -> Dict[str, Any]:
        """获取输出设置"""
        kg_config = self.get_kg_config()
        return kg_config.get('output', {})
    
    def validate_config(self, config_name: str) -> bool:
        """验证配置文件"""
        config = self.get_config(config_name)
        
        if not config:
            self.logger.error(f"❌ 配置为空: {config_name}")
            return False
        
        # 基本验证
        required_keys = {
            'neo4j': ['database'],
            'kg': ['knowledge_graph'],
            'extraction': ['data_sources'],
            'agents': ['base_agent'],
            'environments': ['environments']
        }
        
        if config_name in required_keys:
            for key in required_keys[config_name]:
                if key not in config:
                    self.logger.error(f"❌ 配置缺少必需键: {config_name}.{key}")
                    return False
        
        self.logger.info(f"✅ 配置验证通过: {config_name}")
        return True
    
    def update_config(self, config_name: str, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            config = self.get_config(config_name)
            
            # 深度更新
            def deep_update(base_dict, update_dict):
                for key, value in update_dict.items():
                    if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                        deep_update(base_dict[key], value)
                    else:
                        base_dict[key] = value
            
            deep_update(config, updates)
            self.configs[config_name] = config
            
            self.logger.info(f"✅ 配置更新成功: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置更新失败: {config_name}, 错误: {e}")
            return False
    
    def save_config(self, config_name: str, config_path: Optional[str] = None) -> bool:
        """保存配置到文件"""
        try:
            config = self.get_config(config_name)
            
            if config_path is None:
                # 使用默认路径
                config_mapping = {
                    'main': 'main_config.yaml',
                    'kg': 'kg/kg_construction.yaml',
                    'neo4j': 'neo4j/neo4j_config.yaml',
                    'extraction': 'extraction/extraction_config.yaml',
                    'agents': 'agents/agent_config.yaml',
                    'environments': 'environments/environment_config.yaml'
                }
                config_path = self.config_root / config_mapping.get(config_name, f"{config_name}.yaml")
            else:
                config_path = Path(config_path)
            
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.logger.info(f"✅ 配置保存成功: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置保存失败: {config_name}, 错误: {e}")
            return False
    
    def list_configs(self) -> Dict[str, str]:
        """列出所有可用配置"""
        config_files = {}
        
        for config_file in self.config_root.rglob("*.yaml"):
            relative_path = config_file.relative_to(self.config_root)
            config_name = str(relative_path).replace('/', '_').replace('.yaml', '')
            config_files[config_name] = str(relative_path)
        
        return config_files
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置"""
        all_configs = {}
        
        config_names = ['main', 'kg', 'neo4j', 'extraction', 'agents', 'environments']
        
        for config_name in config_names:
            all_configs[config_name] = self.get_config(config_name)
        
        return all_configs
    
    def create_runtime_config(self) -> Dict[str, Any]:
        """创建运行时配置"""
        runtime_config = {
            'project': self.main_config.get('project', {}),
            'paths': self.main_config.get('paths', {}),
            'global': self.main_config.get('global', {}),
            'neo4j_connection': self.get_database_connection_info(),
            'kg_settings': self.get_kg_config().get('knowledge_graph', {}),
            'extraction_settings': self.get_extraction_config().get('extraction_strategy', {}),
        }
        
        return runtime_config


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config(config_name: str) -> Dict[str, Any]:
    """获取配置的便捷函数"""
    return config_manager.get_config(config_name)


def get_neo4j_config() -> Dict[str, Any]:
    """获取Neo4j配置的便捷函数"""
    return config_manager.get_neo4j_config()


def get_kg_config() -> Dict[str, Any]:
    """获取知识图谱配置的便捷函数"""
    return config_manager.get_kg_config()


if __name__ == "__main__":
    # 测试配置管理器
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试配置管理器")
    
    # 测试加载配置
    configs = config_manager.get_all_configs()
    print(f"📊 加载的配置数量: {len(configs)}")
    
    # 测试Neo4j配置
    neo4j_config = config_manager.get_database_connection_info()
    print(f"🗄️  Neo4j连接: {neo4j_config.get('uri', 'N/A')}")
    
    # 测试配置验证
    for config_name in ['neo4j', 'kg', 'extraction']:
        is_valid = config_manager.validate_config(config_name)
        print(f"✅ {config_name}配置验证: {'通过' if is_valid else '失败'}")
    
    print("🎉 配置管理器测试完成")
