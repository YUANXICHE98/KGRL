#!/usr/bin/env python3
"""
智能体路径追踪器 - 追踪和可视化智能体在知识图谱中的路径
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class AgentPathTracker:
    """智能体路径追踪器"""

    def __init__(self, scene_name: str):
        self.scene_name = scene_name
        self.paths = []
        self.current_episode = 0
        self.current_step = 0

    def start_episode(self, episode_num: int):
        """开始新回合"""
        self.current_episode = episode_num
        self.current_step = 0

    def record_step(self, agent_name: str, step: int, action: str, target: str,
                   reward: float, kg_nodes_accessed: List[str] = None,
                   reasoning_trace: str = "", observation: Dict[str, Any] = None):
        """记录一步"""
        if kg_nodes_accessed is None:
            kg_nodes_accessed = []

        step_record = {
            'episode': self.current_episode,
            'step': step,
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'action': action,
            'target': target,
            'reward': reward,
            'kg_nodes_accessed': kg_nodes_accessed,
            'reasoning_trace': reasoning_trace,
            'scene': self.scene_name
        }

        # 添加观察信息（如果提供）
        if observation:
            step_record.update({
                'visible_entities': observation.get('visible_entities', []),
                'available_actions': observation.get('available_actions', []),
                'agent_location': observation.get('agent_location', ''),
                'agent_inventory': observation.get('agent_inventory', [])
            })

        self.paths.append(step_record)

    def get_episode_path(self, episode_num: int) -> List[Dict]:
        """获取特定回合的路径"""
        return [step for step in self.paths if step['episode'] == episode_num]

    def get_agent_paths(self, agent_name: str) -> List[Dict]:
        """获取特定智能体的所有路径"""
        return [step for step in self.paths if step['agent'] == agent_name]

    def save_paths(self, output_dir: Path):
        """保存路径数据"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存JSON格式
        json_file = output_dir / f"agent_paths_{self.scene_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.paths, f, indent=2, ensure_ascii=False)

        # 保存CSV格式
        if self.paths:
            df = pd.DataFrame(self.paths)
            csv_file = output_dir / f"agent_paths_{self.scene_name}.csv"
            df.to_csv(csv_file, index=False)

        return json_file, csv_file

    def save_results(self, base_path: str):
        """保存所有结果"""
        from pathlib import Path
        output_dir = Path(base_path)
        json_file, csv_file = self.save_paths(output_dir)

        return {
            'csv_path': str(csv_file),
            'json_path': str(json_file),
            'total_steps': len(self.paths)
        }

    def generate_path_table(self, output_dir: Path):
        """生成路径表格报告"""
        if not self.paths:
            return None

        output_dir.mkdir(parents=True, exist_ok=True)

        # 按回合分组
        episodes = {}
        for step in self.paths:
            ep = step['episode']
            if ep not in episodes:
                episodes[ep] = []
            episodes[ep].append(step)

        # 生成Markdown报告
        md_file = output_dir / f"path_analysis_{self.scene_name}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# 智能体路径分析: {self.scene_name}\n\n")

            for episode_num, steps in episodes.items():
                f.write(f"## 回合 {episode_num}\n\n")
                f.write("| 步骤 | 智能体 | 动作 | 目标 | 可见实体 | 奖励 |\n")
                f.write("|------|--------|------|------|----------|------|\n")

                for step in steps:
                    visible = ", ".join(step['visible_entities'][:3])  # 只显示前3个
                    if len(step['visible_entities']) > 3:
                        visible += "..."

                    f.write(f"| {step['step']} | {step['agent']} | {step['action']} | "
                           f"{step['target']} | {visible} | {step['reward']:.3f} |\n")

                f.write("\n")

            # 添加统计信息
            f.write("## 路径统计\n\n")

            agents = set(step['agent'] for step in self.paths)
            for agent in agents:
                agent_steps = [s for s in self.paths if s['agent'] == agent]
                total_reward = sum(s['reward'] for s in agent_steps)
                unique_entities = set()
                for s in agent_steps:
                    unique_entities.update(s['visible_entities'])

                f.write(f"### {agent}\n")
                f.write(f"- 总步数: {len(agent_steps)}\n")
                f.write(f"- 总奖励: {total_reward:.3f}\n")
                f.write(f"- 访问实体数: {len(unique_entities)}\n")
                f.write(f"- 平均奖励: {total_reward/len(agent_steps):.3f}\n\n")

        return md_file

# 使用示例
if __name__ == "__main__":
    # 创建追踪器
    tracker = AgentPathTracker("FloorPlan202-openable")

    # 模拟记录路径
    tracker.start_episode(1)
    tracker.record_step("llm_baseline", "go_to", "ArmChair_689",
                       {"visible_entities": ["ArmChair_689", "CoffeeTable_992"],
                        "available_actions": ["go_to", "examine"]}, 0.1)

    # 保存路径
    output_dir = Path("reports/agent_paths")
    tracker.save_paths(output_dir)
    tracker.generate_path_table(output_dir)
