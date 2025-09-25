#!/usr/bin/env python3
"""
基于场景的强化学习环境
Scene-based Reinforcement Learning Environment
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.simple_config import get_config


class SceneBasedEnvironment:
    """基于场景的RL环境"""
    
    def __init__(self, config_path: str = None):
        try:
            if config_path is None:
                # 使用简化配置管理器
                config = get_config()
                self.config = config.get_environment_config()
                print(f"✅ Environment config loaded")
            else:
                self.config = self._load_config(config_path)
                print(f"✅ Environment config loaded from {config_path}")
        except Exception as e:
            print(f"⚠️ Failed to load environment config: {e}")
            self.config = self._get_default_config()
        
        # 环境设置
        self.current_scene = None
        self.current_state = {}
        self.action_history = []
        self.step_count = 0
        self.max_steps = self.config.get('environments', {}).get('alfworld', {}).get('settings', {}).get('max_steps', 50)
        
        # 加载场景数据
        self.scenes = self._load_scenes()
        self.available_actions = self._define_actions()
        
        # 奖励设置
        self.rewards = self.config.get('rewards', {
            'success': 10.0,
            'failure': -5.0,
            'step_penalty': -0.01,
            'invalid_action': -0.1
        })
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            import yaml
            return yaml.safe_load(f)

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'environments': {
                'alfworld': {
                    'settings': {
                        'max_steps': 50,
                        'timeout': 300
                    },
                    'rewards': {
                        'success': 10.0,
                        'failure': -5.0,
                        'step_penalty': -0.01,
                        'invalid_action': -0.1
                    },
                    'action_space': {
                        'actions': ['go_to', 'open', 'close', 'pick_up', 'put_down', 'examine']
                    }
                }
            }
        }
    
    def _load_scenes(self) -> Dict[str, Any]:
        """加载所有场景数据"""
        scenes = {}

        # 加载增强知识图谱场景
        kg_scenes_dir = Path("data/knowledge_graphs/enhanced_scenes")
        if kg_scenes_dir.exists():
            for scene_file in kg_scenes_dir.glob("*_enhanced_kg.json"):
                scene_name = scene_file.stem.replace('_enhanced_kg', '')
                try:
                    with open(scene_file, 'r', encoding='utf-8') as f:
                        scene_data = json.load(f)

                    # 统计KG数据
                    nodes = scene_data.get('nodes', [])
                    edges = scene_data.get('edges', [])
                    print(f"🔍 加载场景 {scene_name}: {len(nodes)} 节点, {len(edges)} 边")

                    scenes[scene_name] = {
                        'kg_data': scene_data,
                        'type': 'alfworld',
                        'source_file': str(scene_file)
                    }
                except Exception as e:
                    print(f"⚠️  加载场景失败 {scene_name}: {e}")

        print(f"📊 成功加载了 {len(scenes)} 个增强场景")
        return scenes
    
    def _define_actions(self) -> List[str]:
        """定义可用动作"""
        # 从配置中获取动作列表
        config_actions = self.config.get('actions', [])

        if config_actions:
            return config_actions
        else:
            # 默认动作列表
            return [
                "go_to",      # 移动到位置/物品
                "open",       # 打开容器
                "close",      # 关闭容器
                "pick_up",    # 拾取物品
                "put_down",   # 放下物品
                "examine",    # 检查物品/容器
                "use",        # 使用物品
                "wait"        # 等待
            ]
    
    def reset(self, scene_name: str = None) -> Dict[str, Any]:
        """重置环境到初始状态"""
        # 选择场景
        if scene_name is None:
            scene_name = random.choice(list(self.scenes.keys()))
        elif scene_name not in self.scenes:
            raise ValueError(f"场景不存在: {scene_name}")
        
        self.current_scene = scene_name
        scene_data = self.scenes[scene_name]
        
        # 初始化状态
        self.current_state = self._extract_initial_state(scene_data)
        self.action_history = []
        self.step_count = 0
        
        print(f"🎮 重置环境到场景: {scene_name}")
        return self._get_observation()
    
    def _extract_initial_state(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """从场景数据提取初始状态"""
        kg_data = scene_data.get('kg_data', {})
        nodes = kg_data.get('nodes', [])
        edges = kg_data.get('edges', [])
        
        state = {
            'entities': {},
            'states': {},
            'relations': {},
            'agent_location': None,
            'agent_inventory': [],
            'available_actions': []
        }
        
        # 提取实体
        for node in nodes:
            if node['type'] == 'entity':
                entity_name = node['name']
                state['entities'][entity_name] = {
                    'type': node['attributes'].get('entity_type', 'unknown'),
                    'properties': node['attributes']
                }
        
        # 提取状态
        for node in nodes:
            if node['type'] == 'state':
                state_name = node['name']
                state['states'][state_name] = {
                    'value': node['attributes'].get('state_value', 'unknown'),
                    'entity': node['attributes'].get('entity_name', ''),
                    'is_initial': node['attributes'].get('is_initial', False)
                }
        
        # 提取关系
        for edge in edges:
            source = edge['source']
            target = edge['target']
            relation_type = edge['type']
            
            if relation_type not in state['relations']:
                state['relations'][relation_type] = []
            
            state['relations'][relation_type].append({
                'source': source,
                'target': target,
                'attributes': edge.get('attributes', {})
            })
        
        # Set agent initial location from real KG data - NO SIMULATION
        location_entities = [name for name, data in state['entities'].items()
                           if data['type'].lower() in ['location', 'room', 'area']]

        if location_entities:
            state['agent_location'] = location_entities[0]
            print(f"🎯 Agent starting at: {state['agent_location']}")
        elif state['entities']:
            state['agent_location'] = list(state['entities'].keys())[0]
            print(f"🎯 Agent starting at: {state['agent_location']} (fallback)")
        else:
            state['agent_location'] = 'unknown_location'
            print("⚠️ No entities found in scene!")

        print(f"📊 Scene loaded: {len(state['entities'])} entities, {len(state['states'])} states")

        return state
    
    def step(self, action: str, target: str = None) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """执行一步动作"""
        self.step_count += 1
        
        # 验证动作
        if action not in self.available_actions:
            return self._get_observation(), self.rewards.get('invalid_action', -0.1), False, {'error': 'Invalid action'}
        
        # 执行动作
        reward, done, info = self._execute_action(action, target)
        
        # 检查是否超过最大步数
        if self.step_count >= self.max_steps:
            done = True
            info['timeout'] = True
        
        # 记录动作历史
        self.action_history.append({
            'step': self.step_count,
            'action': action,
            'target': target,
            'reward': reward
        })
        
        return self._get_observation(), reward, done, info
    
    def _execute_action(self, action: str, target: str = None) -> Tuple[float, bool, Dict[str, Any]]:
        """执行具体动作"""
        reward = self.rewards.get('step_penalty', -0.01)
        done = False
        info = {'action_executed': True}
        
        if action == "go_to" and target:
            reward += self._action_go_to(target)
        elif action == "open" and target:
            reward += self._action_open(target)
        elif action == "close" and target:
            reward += self._action_close(target)
        elif action == "pick_up" and target:
            reward += self._action_pick_up(target)
        elif action == "put_down" and target:
            reward += self._action_put_down(target)
        elif action == "examine" and target:
            reward += self._action_examine(target)
        elif action == "use" and target:
            reward += self._action_use(target)
        elif action == "wait":
            reward += 0  # 等待不给额外奖励
        else:
            reward = self.rewards.get('invalid_action', -0.1)
            info['error'] = 'Action requires target or invalid target'
        
        # 检查任务完成条件
        if self._check_task_completion():
            reward += self.rewards.get('success', 10.0)
            done = True
            info['task_completed'] = True
        
        return reward, done, info
    
    def _action_go_to(self, target: str) -> float:
        """执行移动动作"""
        if target in self.current_state['entities']:
            old_location = self.current_state['agent_location']
            self.current_state['agent_location'] = target
            print(f"🚶 智能体从 {old_location} 移动到 {target}")
            return 0.1  # 移动成功的小奖励
        return -0.05  # 移动失败的惩罚
    
    def _action_open(self, target: str) -> float:
        """执行打开动作"""
        if target in self.current_state['entities']:
            entity = self.current_state['entities'][target]
            if 'openable' in entity.get('properties', {}):
                # 更新状态为打开
                for state_name, state_info in self.current_state['states'].items():
                    if state_info['entity'] == target and 'closed' in state_info['value']:
                        state_info['value'] = state_info['value'].replace('closed', 'opened')
                        print(f"🔓 打开了 {target}")
                        return 0.2
        return -0.05
    
    def _action_close(self, target: str) -> float:
        """执行关闭动作"""
        if target in self.current_state['entities']:
            # 更新状态为关闭
            for state_name, state_info in self.current_state['states'].items():
                if state_info['entity'] == target and 'opened' in state_info['value']:
                    state_info['value'] = state_info['value'].replace('opened', 'closed')
                    print(f"🔒 关闭了 {target}")
                    return 0.1
        return -0.05
    
    def _action_pick_up(self, target: str) -> float:
        """执行拾取动作"""
        if target in self.current_state['entities'] and len(self.current_state['agent_inventory']) < 3:
            self.current_state['agent_inventory'].append(target)
            print(f"🤏 拾取了 {target}")
            return 0.2
        return -0.05
    
    def _action_put_down(self, target: str) -> float:
        """执行放下动作"""
        if target in self.current_state['agent_inventory']:
            self.current_state['agent_inventory'].remove(target)
            print(f"📦 放下了 {target}")
            return 0.1
        return -0.05
    
    def _action_examine(self, target: str) -> float:
        """执行检查动作"""
        if target in self.current_state['entities']:
            entity = self.current_state['entities'][target]
            print(f"🔍 检查 {target}: {entity}")
            return 0.05
        return -0.02
    
    def _action_use(self, target: str) -> float:
        """执行使用动作"""
        if target in self.current_state['agent_inventory']:
            print(f"🔧 使用了 {target}")
            return 0.1
        return -0.05
    
    def _check_task_completion(self) -> bool:
        """检查任务是否完成"""
        # 简单的完成条件：智能体拾取了某些物品
        target_items = ['key', 'treasure', 'egg']  # 示例目标物品
        
        for item in target_items:
            if any(item.lower() in inv_item.lower() for inv_item in self.current_state['agent_inventory']):
                return True
        
        return False
    
    def _get_observation(self) -> Dict[str, Any]:
        """获取当前观察"""
        return {
            'scene': self.current_scene,
            'agent_location': self.current_state['agent_location'],
            'agent_inventory': self.current_state['agent_inventory'],
            'visible_entities': self._get_visible_entities(),
            'available_actions': self._get_available_actions(),
            'step_count': self.step_count,
            'description': self._generate_description()
        }
    
    def _get_visible_entities(self) -> List[str]:
        """Get visible entities from real KG data - NO SIMULATION"""
        current_location = self.current_state['agent_location']
        visible = []

        # Add current location
        if current_location:
            visible.append(current_location)

        # Add entities based on real KG relations
        for relation_type, relations in self.current_state['relations'].items():
            if relation_type.lower() in ['contains', 'has', 'at_location', 'in']:
                for rel in relations:
                    if rel['source'] == current_location:
                        visible.append(rel['target'])
                    elif rel['target'] == current_location:
                        visible.append(rel['source'])

        # Add some random entities from the scene for interaction
        all_entities = list(self.current_state['entities'].keys())
        for entity in all_entities[:3]:  # Add first 3 entities
            if entity not in visible:
                visible.append(entity)

        print(f"👁️ Visible entities: {visible[:5]}")  # Debug info
        return visible[:8]  # Return more entities for better interaction
    
    def _get_available_actions(self) -> List[str]:
        """Get available actions from real KG data - NO SIMULATION"""
        available = ['examine', 'wait']

        visible_entities = self._get_visible_entities()

        # Add actions based on visible entities from real KG
        if visible_entities:
            available.extend(['go_to', 'open', 'close', 'pick_up'])

        if self.current_state['agent_inventory']:
            available.extend(['put_down', 'use'])

        unique_actions = list(set(available))
        print(f"⚡ Available actions: {unique_actions}")  # Debug info
        return unique_actions
    
    def _generate_description(self) -> str:
        """生成当前状态的文本描述"""
        location = self.current_state['agent_location']
        inventory = self.current_state['agent_inventory']
        visible = self._get_visible_entities()
        
        desc = f"你现在在 {location}。"
        
        if inventory:
            desc += f" 你携带着: {', '.join(inventory)}。"
        
        if visible:
            desc += f" 你可以看到: {', '.join(visible)}。"
        
        return desc
    
    def get_scene_list(self) -> List[str]:
        """获取所有可用场景列表"""
        return list(self.scenes.keys())
    
    def get_scene_info(self, scene_name: str) -> Dict[str, Any]:
        """获取场景信息"""
        if scene_name in self.scenes:
            scene_data = self.scenes[scene_name]
            kg_data = scene_data.get('kg_data', {})
            
            return {
                'name': scene_name,
                'type': scene_data.get('type', 'unknown'),
                'entities_count': len([n for n in kg_data.get('nodes', []) if n['type'] == 'entity']),
                'states_count': len([n for n in kg_data.get('nodes', []) if n['type'] == 'state']),
                'actions_count': len([n for n in kg_data.get('nodes', []) if n['type'] == 'action']),
                'source_file': scene_data.get('source_file', '')
            }
        return {}


if __name__ == "__main__":
    # 测试环境
    print("🧪 测试场景环境")
    
    env = SceneBasedEnvironment()
    
    # 显示可用场景
    scenes = env.get_scene_list()
    print(f"📊 可用场景数: {len(scenes)}")
    
    if scenes:
        # 测试第一个场景
        scene_name = scenes[0]
        print(f"🎮 测试场景: {scene_name}")
        
        # 重置环境
        obs = env.reset(scene_name)
        print(f"📋 初始观察: {obs['description']}")
        
        # 执行几个动作
        actions_to_test = [
            ("examine", obs['visible_entities'][0] if obs['visible_entities'] else None),
            ("go_to", obs['visible_entities'][1] if len(obs['visible_entities']) > 1 else None),
            ("wait", None)
        ]
        
        for action, target in actions_to_test:
            if target or action == "wait":
                obs, reward, done, info = env.step(action, target)
                print(f"🎯 动作: {action} {target or ''} | 奖励: {reward:.3f} | 完成: {done}")
                print(f"📋 新观察: {obs['description']}")
                
                if done:
                    break
    
    print("✅ 环境测试完成")
