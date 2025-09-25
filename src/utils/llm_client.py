#!/usr/bin/env python3
"""
LLM客户端
支持多种LLM API调用
"""

import json
import requests
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class LLMClient:
    """LLM客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://vir.vimsai.com", model: str = "gpt-4o"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"🤖 初始化LLM客户端 (模型: {model})")
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.7, max_tokens: int = 512) -> str:
        """聊天完成"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"❌ LLM API错误: {response.status_code} - {response.text}")
                return self._fallback_response(messages)
                
        except Exception as e:
            print(f"❌ LLM调用异常: {e}")
            return self._fallback_response(messages)
    
    def _fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """备用响应"""
        last_message = messages[-1]['content'] if messages else ""
        
        # 简单的规则备用
        if "pick up" in last_message.lower():
            return "pick_up"
        elif "open" in last_message.lower():
            return "open"
        elif "go to" in last_message.lower():
            return "go_to"
        elif "examine" in last_message.lower():
            return "examine"
        else:
            return "wait"


class LLMBaselineAgent:
    """真正的LLM基线智能体"""
    
    def __init__(self, api_key: str):
        self.llm_client = LLMClient(api_key)
        self.conversation_history = []
        self.max_history = 5
        
        print("🤖 初始化真正的LLM基线智能体")
    
    def reset(self, scene_info: Dict[str, Any] = None):
        """重置智能体"""
        self.conversation_history = []
        if scene_info:
            self.conversation_history.append({
                "role": "system",
                "content": f"你是一个在{scene_info.get('scene', '未知场景')}中的智能体。你的目标是完成任务。"
            })
    
    def select_action(self, observation: Dict[str, Any]) -> tuple[str, str]:
        """选择动作"""
        # 构建提示
        prompt = self._build_prompt(observation)
        
        # 添加到对话历史
        self.conversation_history.append({
            "role": "user", 
            "content": prompt
        })
        
        # 限制历史长度
        if len(self.conversation_history) > self.max_history * 2:
            # 保留系统消息和最近的对话
            system_msg = self.conversation_history[0] if self.conversation_history[0]["role"] == "system" else None
            recent_msgs = self.conversation_history[-(self.max_history * 2 - 1):]
            self.conversation_history = ([system_msg] if system_msg else []) + recent_msgs
        
        # 调用LLM
        response = self.llm_client.chat_completion(self.conversation_history)
        
        # 解析响应
        action, target = self._parse_response(response, observation)
        
        # 添加助手响应到历史
        self.conversation_history.append({
            "role": "assistant",
            "content": f"我选择: {action} {target or ''}"
        })
        
        return action, target
    
    def _build_prompt(self, observation: Dict[str, Any]) -> str:
        """构建提示"""
        location = observation.get('agent_location', '未知位置')
        inventory = observation.get('agent_inventory', [])
        visible_entities = observation.get('visible_entities', [])
        available_actions = observation.get('available_actions', [])
        description = observation.get('description', '没有描述')
        
        prompt = f"""
当前状态:
- 位置: {location}
- 库存: {inventory if inventory else '空'}
- 可见物品: {visible_entities if visible_entities else '无'}
- 可用动作: {available_actions if available_actions else '无'}
- 环境描述: {description}

请选择一个动作。回复格式: "动作 目标" (如果不需要目标则只回复动作)
例如: "pick_up Apple" 或 "examine Cabinet" 或 "wait"

你的选择:"""
        
        return prompt
    
    def _parse_response(self, response: str, observation: Dict[str, Any]) -> tuple[str, str]:
        """解析LLM响应"""
        response = response.strip().lower()
        available_actions = observation.get('available_actions', [])
        visible_entities = observation.get('visible_entities', [])
        
        # 尝试解析 "动作 目标" 格式
        parts = response.split()
        if len(parts) >= 2:
            action = parts[0]
            target = ' '.join(parts[1:])
            
            # 验证动作是否可用
            if action in available_actions:
                # 验证目标是否存在
                if any(target.lower() in entity.lower() for entity in visible_entities):
                    return action, target
        
        # 尝试单个动作
        if len(parts) >= 1:
            action = parts[0]
            if action in available_actions:
                if action in ['wait', 'look']:
                    return action, None
                elif visible_entities:
                    return action, visible_entities[0]
        
        # 备用策略
        if available_actions:
            if 'pick_up' in available_actions and visible_entities:
                return 'pick_up', visible_entities[0]
            elif 'examine' in available_actions and visible_entities:
                return 'examine', visible_entities[0]
            else:
                return available_actions[0], visible_entities[0] if visible_entities else None
        
        return 'wait', None
    
    def update(self, observation: Dict[str, Any], action: str, target: str, 
               reward: float, next_observation: Dict[str, Any], done: bool):
        """更新智能体"""
        # 添加结果反馈到对话历史
        feedback = f"执行 {action} {target or ''} 后，获得奖励 {reward:.2f}"
        if done:
            feedback += "，任务完成！" if reward > 0 else "，任务失败。"
        
        self.conversation_history.append({
            "role": "user",
            "content": f"反馈: {feedback}"
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'agent_type': 'real_llm_baseline',
            'model': self.llm_client.model,
            'conversation_length': len(self.conversation_history),
            'api_calls': len([msg for msg in self.conversation_history if msg['role'] == 'assistant'])
        }


if __name__ == "__main__":
    # 测试LLM客户端
    print("🧪 测试LLM客户端")
    
    api_key = "sk-rvwMvUNbWBz9L76KB05650C7Cc464324BdC98dB3FbD4296a"
    
    # 测试LLM客户端
    client = LLMClient(api_key)
    
    test_messages = [
        {"role": "user", "content": "你好，请简单介绍一下你自己。"}
    ]
    
    response = client.chat_completion(test_messages)
    print(f"LLM响应: {response}")
    
    # 测试LLM智能体
    agent = LLMBaselineAgent(api_key)
    
    mock_observation = {
        'scene': 'FloorPlan228-openable',
        'agent_location': 'Kitchen',
        'agent_inventory': [],
        'visible_entities': ['Cabinet', 'Drawer', 'Apple', 'Key'],
        'available_actions': ['go_to', 'open', 'pick_up', 'examine', 'wait'],
        'description': '你在厨房里，可以看到柜子、抽屉、苹果和钥匙。'
    }
    
    action, target = agent.select_action(mock_observation)
    print(f"智能体选择: {action} {target or ''}")
    
    print("✅ 测试完成")
