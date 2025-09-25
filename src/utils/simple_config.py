#!/usr/bin/env python3
"""
简化配置管理器
统一管理所有配置，去除复杂性
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class SimpleConfig:
    """简化配置管理器"""
    
    def __init__(self, config_file: str = "configs/simple_config.yaml"):
        self.config_file = Path(config_file)
        self.config = {}
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if not self.config_file.exists():
                self.logger.error(f"❌ 配置文件不存在: {self.config_file}")
                self.config = self._get_default_config()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            self.logger.info(f"✅ 配置加载成功: {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"❌ 配置加载失败: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'project': {
                'name': 'KGRL',
                'version': '1.0.0'
            },
            'llm': {
                'model': 'gpt-4o',
                'api_key': '',
                'temperature': 0.7,
                'max_tokens': 512
            },
            'environment': {
                'type': 'alfworld',
                'max_steps': 50,
                'actions': ['go_to', 'examine', 'pick_up', 'open', 'close'],
                'rewards': {
                    'success': 10.0,
                    'failure': -5.0,
                    'step_penalty': -0.01,
                    'invalid_action': -0.1
                }
            },
            'experiment': {
                'scenes': ['FloorPlan202-openable'],
                'max_episodes': 1,
                'max_steps_per_episode': 10
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.get('llm', {})
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """获取智能体配置"""
        agents = self.get('agents', {})
        return agents.get(agent_name, {})
    
    def get_environment_config(self) -> Dict[str, Any]:
        """获取环境配置"""
        return self.get('environment', {})
    
    def get_experiment_config(self) -> Dict[str, Any]:
        """获取实验配置"""
        return self.get('experiment', {})
    
    def get_kg_config(self) -> Dict[str, Any]:
        """获取知识图谱配置"""
        return self.get('knowledge_graph', {})
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """获取Neo4j配置"""
        kg_config = self.get_kg_config()
        return kg_config.get('neo4j', {})
    
    def get_paths(self) -> Dict[str, str]:
        """获取路径配置"""
        return self.get('paths', {})
    
    def is_debug_enabled(self) -> bool:
        """检查是否启用调试模式"""
        return self.get('debug.enabled', False)
    
    def should_save_detailed_logs(self) -> bool:
        """检查是否保存详细日志"""
        return self.get('experiment.output.save_detailed_logs', True)
    
    def should_track_kg_nodes(self) -> bool:
        """检查是否追踪KG节点"""
        return self.get('debug.track_kg_nodes', True)
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        api_key = self.get('llm.api_key', '')

        # 处理环境变量
        if api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]
            return os.getenv(env_var, '')

        return api_key

    def get_base_url(self) -> str:
        """获取API基础URL"""
        return self.get('llm.base_url', 'https://api.openai.com/v1')
    
    def validate(self) -> bool:
        """验证配置"""
        required_keys = [
            'project.name',
            'llm.model',
            'environment.type',
            'experiment.scenes'
        ]
        
        missing_keys = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            self.logger.error(f"❌ 配置缺少必需键: {missing_keys}")
            return False
        
        self.logger.info("✅ 配置验证通过")
        return True
    
    def save(self, file_path: Optional[str] = None) -> bool:
        """保存配置到文件"""
        try:
            save_path = Path(file_path) if file_path else self.config_file
            
            # 确保目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            self.logger.info(f"✅ 配置保存成功: {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 配置保存失败: {e}")
            return False
    
    def print_summary(self) -> None:
        """打印配置摘要"""
        print("📊 配置摘要:")
        print("=" * 40)
        print(f"项目: {self.get('project.name')} v{self.get('project.version')}")
        print(f"LLM模型: {self.get('llm.model')}")
        print(f"环境类型: {self.get('environment.type')}")
        print(f"实验场景: {len(self.get('experiment.scenes', []))} 个")
        print(f"调试模式: {'开启' if self.is_debug_enabled() else '关闭'}")
        
        # API密钥状态
        api_key = self.get_api_key()
        if api_key and api_key.startswith('sk-'):
            print(f"API密钥: 已配置 ({api_key[:10]}...)")
        else:
            print("API密钥: 未配置")


# 全局配置实例
config = SimpleConfig()

# 便捷函数
def get_config() -> SimpleConfig:
    """获取全局配置实例"""
    return config

def get(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return config.get(key, default)


if __name__ == "__main__":
    # 测试配置管理器
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 测试简化配置管理器")
    
    # 验证配置
    if config.validate():
        config.print_summary()
    else:
        print("❌ 配置验证失败")
