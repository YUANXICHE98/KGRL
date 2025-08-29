# KGRL环境使用指南

## 🎮 当前环境状态

### 主要环境：TextWorld（带模拟后备）

我们的项目目前使用**TextWorld**作为主要环境，但包含了一个**智能模拟环境**作为后备：

#### 1. TextWorld环境
- **真实TextWorld**：如果你安装了TextWorld包
- **模拟TextWorld**：如果没有安装，自动使用模拟环境
- **完全兼容**：两种模式提供相同的接口和体验

#### 2. 环境特点
```python
# 当前配置示例
env_config = {
    "max_episode_steps": 50,
    "difficulty": "easy",      # easy/medium/hard
    "nb_objects": 5,           # 物品数量
    "nb_rooms": 3,             # 房间数量
    "quest_length": 3          # 任务复杂度
}
```

#### 3. 模拟环境详情
我们的模拟环境包含：
- **3个房间**：kitchen, living_room, bedroom
- **物品系统**：apple, key, book, pillow
- **目标任务**：找到钥匙，打开卧室的箱子
- **完整交互**：移动、拿取、查看、开启等动作

## 🏠 ALFWorld支持

ALFWorld环境框架已准备，可以通过以下方式启用：

### 安装ALFWorld
```bash
pip install alfworld
```

### 创建ALFWorld环境
```python
# 在 src/environments/alfworld_env.py 中实现
from src.environments.alfworld_env import ALFWorldEnvironment

env = ALFWorldEnvironment("alfworld_env", {
    "split": "train",
    "max_episode_steps": 50
})
```

## 🎯 环境选择建议

### Week 1-2: TextWorld（推荐）
- ✅ **即开即用**：无需额外安装
- ✅ **快速迭代**：模拟环境响应快
- ✅ **可控难度**：easy/medium/hard三档
- ✅ **完整功能**：支持所有核心功能

### Week 3+: 可选ALFWorld
- 🔄 **更真实**：基于ALFRED数据集
- 🔄 **更复杂**：家庭环境任务
- 🔄 **更标准**：学术界常用基准

## 🔧 环境配置详解

### TextWorld配置选项
```python
textworld_config = {
    # 基础设置
    "max_episode_steps": 50,        # 最大步数
    "difficulty": "easy",           # 难度等级
    
    # 游戏生成参数
    "nb_objects": 5,                # 物品数量
    "nb_rooms": 3,                  # 房间数量
    "quest_length": 3,              # 任务长度
    "quest_breadth": 2,             # 任务广度
    
    # 观测设置
    "include_description": True,     # 包含描述
    "include_inventory": True,       # 包含物品栏
    "include_objective": True,       # 包含目标
    "admissible_commands": True,     # 提供可用命令
}
```

### 难度等级说明
| 难度 | 房间数 | 物品数 | 任务长度 | 适用场景 |
|------|--------|--------|----------|----------|
| easy | 3 | 5 | 3 | 快速测试、调试 |
| medium | 5 | 10 | 5 | 正常实验 |
| hard | 8 | 15 | 8 | 挑战性评估 |

## 🎮 环境使用示例

### 基础使用
```python
from src.environments.textworld_env import TextWorldEnvironment

# 创建环境
env = TextWorldEnvironment("my_env", {
    "difficulty": "easy",
    "max_episode_steps": 30
})

# 游戏循环
observation = env.reset()
print(f"Initial: {observation}")

for step in range(30):
    # 获取可用动作
    actions = env.get_available_actions()
    print(f"Available: {actions[:3]}...")  # 显示前3个
    
    # 选择动作（这里随机选择）
    action = actions[0] if actions else "look"
    
    # 执行动作
    obs, reward, done, info = env.step(action)
    print(f"Action: {action} -> Reward: {reward}")
    print(f"Result: {obs[:100]}...")
    
    if done:
        print("Game completed!")
        break

env.close()
```

### 与Agent集成
```python
from src.agents.baseline_agent import BaselineAgent

# 创建Agent和环境
agent = BaselineAgent("test_agent", {"model_name": "gpt-4o-mini"})
env = TextWorldEnvironment("test_env", {"difficulty": "easy"})

# 运行episode
observation = env.reset()
agent.reset()

while not env.is_done():
    # Agent选择动作
    available_actions = env.get_available_actions()
    action = agent.act(observation, available_actions)
    
    # 执行并更新
    new_obs, reward, done, info = env.step(action)
    agent.update(action, new_obs, reward, done, info)
    
    observation = new_obs
    
    if done:
        success = reward > 0
        print(f"Episode finished: {'Success' if success else 'Failed'}")
        break
```

## 🔍 环境调试

### 查看环境状态
```python
# 环境信息
print(f"Environment: {env}")
print(f"Current step: {env.get_episode_step()}")
print(f"Total reward: {env.get_episode_reward()}")
print(f"Is done: {env.is_done()}")

# 动作空间
action_info = env.get_action_space_info()
print(f"Action space: {action_info}")

# 观测空间
obs_info = env.get_observation_space_info()
print(f"Observation space: {obs_info}")
```

### 环境统计
```python
# 运行多个episodes后
stats = env.get_stats()
print(f"Episodes: {stats['total_episodes']}")
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Avg steps: {stats['average_episode_length']:.1f}")
```

## 🚀 快速测试环境

运行以下命令测试环境：

```bash
# 测试TextWorld环境
python -c "
from src.environments.textworld_env import TextWorldEnvironment
env = TextWorldEnvironment('test', {'difficulty': 'easy'})
obs = env.reset()
print('Environment working!')
print(f'Initial observation: {obs[:100]}...')
env.close()
"

# 交互式测试
python main.py --demo
```

## 📈 性能对比

### TextWorld vs ALFWorld
| 特性 | TextWorld | ALFWorld |
|------|-----------|----------|
| 安装难度 | 简单 | 中等 |
| 启动速度 | 快 | 中等 |
| 任务复杂度 | 可配置 | 固定 |
| 学术认可 | 高 | 很高 |
| 调试友好 | 很好 | 好 |

### 推荐使用策略
1. **开发阶段**：使用TextWorld（快速迭代）
2. **测试阶段**：使用TextWorld（可控环境）
3. **发布阶段**：添加ALFWorld（学术对比）

## 🔧 环境扩展

### 添加新环境
1. 继承`BaseEnvironment`类
2. 实现必要的抽象方法
3. 在配置中注册新环境

### 自定义TextWorld任务
```python
# 修改环境配置
custom_config = {
    "difficulty": "custom",
    "nb_objects": 8,
    "nb_rooms": 4,
    "quest_length": 6,
    "custom_facts": [
        ("magic_key", "opens", "secret_door"),
        ("secret_door", "leads_to", "treasure_room")
    ]
}
```

这样你就有了一个完整的环境系统，既支持快速开发，又为未来扩展做好了准备！
