#!/usr/bin/env python3
"""
TextWorld Real Knowledge Graph Builder - Task-Scene Based
严格基于真实TextWorld游戏文件构建知识图谱，不使用任何模拟数据

设计理念：
- 按任务场景分：每个游戏文件生成一个独立的KG
- 只从真实TextWorld游戏文件提取数据
- 完整的状态机设计
- 动作的前置条件和效果
- 状态转换逻辑
- 支持推理和规划

场景分化策略：
- 物理场景：所有游戏共享相同的6个房间布局
- 任务场景：每个游戏有不同的目标、奖励结构、物品配置
- KG构建：为每个任务场景生成独立的KG文件
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import textworld
    TEXTWORLD_AVAILABLE = True
except ImportError:
    TEXTWORLD_AVAILABLE = False
    raise RuntimeError("❌ TextWorld未安装，请运行: pip install textworld")


@dataclass
class GameEntity:
    """游戏实体"""
    id: str
    name: str
    entity_type: str  # 房间、物品、容器、角色
    properties: Dict[str, Any]
    initial_state: str
    possible_states: List[str]
    description: str = ""


@dataclass
class GameState:
    """游戏状态"""
    id: str
    name: str
    entity_name: str
    state_value: str
    is_initial: bool
    description: str = ""


@dataclass
class GameAction:
    """游戏动作"""
    id: str
    name: str
    description: str
    required_entities: List[str]
    required_states: Dict[str, str]  # 实体名 -> 需要的状态值
    effects: Dict[str, str]  # 实体名 -> 产生的状态值
    result: str


@dataclass
class StateTransition:
    """状态转换"""
    from_state: str
    to_state: str
    action: str
    conditions: List[str]
    effects: List[str]


class RealTextWorldKGBuilder:
    """真实TextWorld知识图谱构建器 - 只使用真实数据"""
    
    def __init__(self):
        if not TEXTWORLD_AVAILABLE:
            raise RuntimeError("❌ TextWorld未安装，请运行: pip install textworld")
        
        self.entities = []
        self.states = []
        self.actions = []
        self.transitions = []
        self.results = []
        self.edges = []
        
        # ID计数器
        self.entity_counter = 1
        self.state_counter = 1
        self.action_counter = 1
        self.result_counter = 1
    
    def build_kg_from_real_game_file(self, game_file_path: str) -> Dict[str, Any]:
        """从真实TextWorld游戏文件构建KG"""
        
        if not Path(game_file_path).exists():
            raise FileNotFoundError(f"❌ 游戏文件不存在: {game_file_path}")
        
        print(f"🎮 处理真实游戏文件: {Path(game_file_path).name}")
        
        try:
            # 启动游戏环境
            env = textworld.start(game_file_path)
            game_state = env.reset()
            
            # 必须获取游戏信息
            if not hasattr(game_state, 'game') or game_state.game is None:
                raise RuntimeError(f"❌ 无法从游戏文件获取内部游戏信息")
            
            game_info = game_state.game
            scenario_name = f"TextWorld_{Path(game_file_path).stem}"
            
            # 重置计数器
            self._reset_counters()
            
            # 从真实游戏信息提取数据
            self._extract_real_entities(scenario_name, game_info, game_state)
            self._extract_real_actions(game_info, game_state)

            # 构建KG结构
            self._create_states_for_entities()
            self._create_state_transitions()
            self._create_relationships()

            kg_data = self._build_final_kg_data(scenario_name, game_info)

            print(f"✅ 成功构建KG: {len(self.entities)} 实体, {len(self.actions)} 动作, {len(self.states)} 状态")

            return kg_data
            
        except Exception as e:
            raise RuntimeError(f"❌ 处理游戏文件失败: {e}")
        finally:
            try:
                env.close()
            except:
                pass
    
    def _reset_counters(self):
        """重置计数器"""
        self.entity_counter = 1
        self.state_counter = 1
        self.action_counter = 1
        self.result_counter = 1
        self.entities = []
        self.states = []
        self.actions = []
        self.results = []
        self.edges = []
        self.transitions = []
    
    def _extract_real_entities(self, scenario_name: str, game_info, game_state):
        """从真实游戏信息提取实体 - 基于探索发现的真实结构"""

        # 1. 创建场景实体
        scene_entity = GameEntity(
            id=f"entity_{self.entity_counter}",
            name=scenario_name,
            entity_type="场景",
            properties={
                "描述": f"TextWorld游戏场景: {scenario_name}",
                "类型": "文本冒险游戏",
                "游戏目标": game_info.objective if hasattr(game_info, 'objective') else "",
                "最大分数": str(game_info.max_score) if hasattr(game_info, 'max_score') else "0",
                "通关步骤数": str(len(game_info.walkthrough)) if hasattr(game_info, 'walkthrough') else "0"
            },
            initial_state="活跃",
            possible_states=["活跃", "完成", "失败"],
            description=f"TextWorld游戏场景: {scenario_name}"
        )
        self.entities.append(scene_entity)
        self.entity_counter += 1

        # 2. 从world对象提取真实实体
        if not hasattr(game_info, 'world'):
            raise RuntimeError("❌ 游戏信息中没有world对象")

        world = game_info.world

        # 3. 提取玩家实体
        if hasattr(world, 'player'):
            player_obj = world.player
            player_entity = GameEntity(
                id=f"entity_{self.entity_counter}",
                name="玩家",
                entity_type="角色",
                properties={
                    "描述": "游戏玩家",
                    "玩家ID": str(player_obj.id) if hasattr(player_obj, 'id') else "P",
                    "玩家类型": str(player_obj.type) if hasattr(player_obj, 'type') else "P",
                    "当前房间": str(world.player_room.id) if hasattr(world, 'player_room') else ""
                },
                initial_state="探索中",
                possible_states=["探索中", "任务完成", "游戏结束"],
                description="游戏的主角玩家"
            )
            self.entities.append(player_entity)
            self.entity_counter += 1

        # 4. 提取房间实体 - 基于真实发现
        if hasattr(world, 'rooms') and world.rooms:
            print(f"🏠 提取 {len(world.rooms)} 个房间")
            for room in world.rooms:
                room_entity = GameEntity(
                    id=f"entity_{self.entity_counter}",
                    name=self._get_readable_name(room.id, "房间", game_info) if hasattr(room, 'id') else f"房间_{self.entity_counter}",
                    entity_type="房间",
                    properties={
                        "房间ID": str(room.id) if hasattr(room, 'id') else "",
                        "房间类型": str(room.type) if hasattr(room, 'type') else "r",
                        "原始名称": str(room.name) if hasattr(room, 'name') else ""
                    },
                    initial_state="可访问",
                    possible_states=["可访问", "不可访问", "已访问"],
                    description=f"游戏中的房间"
                )
                self.entities.append(room_entity)
                self.entity_counter += 1

        # 5. 提取物品实体 - 基于真实类型编码
        if hasattr(world, 'objects') and world.objects:
            print(f"📦 提取 {len(world.objects)} 个物品")
            for obj in world.objects:
                if hasattr(obj, 'type') and obj.type:
                    obj_type_code = str(obj.type)

                    # 基于真实发现的类型映射
                    entity_type, initial_state, possible_states = self._map_textworld_type(obj_type_code)

                    # 跳过玩家和库存对象（已单独处理）
                    if obj_type_code in ['P', 'I']:
                        continue

                    obj_entity = GameEntity(
                        id=f"entity_{self.entity_counter}",
                        name=self._get_readable_name(obj.id, entity_type, game_info) if hasattr(obj, 'id') else f"{entity_type}_{self.entity_counter}",
                        entity_type=entity_type,
                        properties={
                            "物品ID": str(obj.id) if hasattr(obj, 'id') else "",
                            "类型编码": obj_type_code,
                            "原始名称": str(obj.name) if hasattr(obj, 'name') else "",
                            "原始类型": str(type(obj).__name__)
                        },
                        initial_state=initial_state,
                        possible_states=possible_states,
                        description=f"游戏中的{entity_type}"
                    )
                    self.entities.append(obj_entity)
                    self.entity_counter += 1

    def _map_textworld_type(self, type_code: str) -> tuple:
        """基于100%真实数据映射TextWorld类型编码"""
        # 基于从8个真实TextWorld文件中提取的完整类型编码集合
        # 类型编码: ['I', 'P', 'c', 'd', 'f', 'k', 'o', 's']
        type_mapping = {
            'I': ("库存", "空", ["空", "有物品"]),
            'P': ("玩家", "探索中", ["探索中", "任务完成", "游戏结束"]),
            'c': ("容器", "关闭", ["关闭", "打开", "锁定", "解锁"]),
            'd': ("门", "关闭", ["关闭", "打开", "锁定", "解锁"]),
            'f': ("食物", "可获取", ["可获取", "已获取", "已消耗"]),
            'k': ("钥匙", "可获取", ["可获取", "已获取", "已使用"]),
            'o': ("物品", "可获取", ["可获取", "已获取", "已使用"]),
            's': ("支撑面", "可用", ["可用", "不可用", "已占用"])
        }

        if type_code not in type_mapping:
            raise ValueError(f"❌ 发现未知类型编码: {type_code}，不在真实数据集中: {list(type_mapping.keys())}")

        return type_mapping[type_code]

    def _get_readable_name(self, obj_id: str, entity_type: str, game_info=None) -> str:
        """从真实游戏数据中获取可读名称 - 修复版，基于100%真实数据"""

        # 1. 首先尝试从infos字典获取真实名称（最可靠的来源）
        if game_info and hasattr(game_info, 'infos'):
            # infos可能是字典或列表，统一处理
            if isinstance(game_info.infos, dict):
                infos_dict = game_info.infos
            elif isinstance(game_info.infos, list):
                infos_dict = dict(game_info.infos)
            else:
                infos_dict = {}

            if obj_id in infos_dict:
                obj_info = infos_dict[obj_id]

                # obj_info可能是EntityInfo对象或字典
                if hasattr(obj_info, 'name'):
                    # EntityInfo对象，直接访问name属性
                    name = obj_info.name
                    if name and name is not None:
                        return str(name)
                elif isinstance(obj_info, dict):
                    # 字典，使用get方法
                    name = obj_info.get('name')
                    if name and name is not None:
                        return str(name)
                else:
                    # 尝试直接转换为字符串（EntityInfo的__str__方法返回名称）
                    name_str = str(obj_info)
                    if name_str and name_str != obj_id:
                        return name_str

        # 2. 尝试从游戏世界对象中获取真实名称
        if game_info and hasattr(game_info, 'world') and game_info.world:
            world = game_info.world

            # 2.1 检查rooms
            if hasattr(world, 'rooms') and world.rooms:
                for room in world.rooms:
                    if hasattr(room, 'id') and str(room.id) == obj_id:
                        if hasattr(room, 'name') and room.name:
                            return str(room.name)

            # 2.2 检查objects
            if hasattr(world, 'objects') and world.objects:
                for obj in world.objects:
                    if hasattr(obj, 'id') and str(obj.id) == obj_id:
                        if hasattr(obj, 'name') and obj.name:
                            return str(obj.name)

        # 3. 尝试从entity_names获取真实名称
        if game_info and hasattr(game_info, 'entity_names') and game_info.entity_names:
            for entity_name in game_info.entity_names:
                entity_str = str(entity_name)
                # 检查ID是否在实体名称中
                if obj_id in entity_str or entity_str.replace(' ', '_').lower() == obj_id.lower():
                    return entity_str

        # 4. 尝试从objects_names获取真实名称
        if game_info and hasattr(game_info, 'objects_names') and game_info.objects_names:
            for obj_name in game_info.objects_names:
                obj_str = str(obj_name)
                if obj_id in obj_str or obj_str.replace(' ', '_').lower() == obj_id.lower():
                    return obj_str

        # 5. 如果都找不到真实名称，直接使用原始ID
        # 严格遵循不使用模拟数据的原则
        return obj_id
    
    def _extract_real_actions(self, game_info, game_state):
        """从真实游戏信息提取动作 - 基于真实可执行命令和通关步骤"""

        # 1. 从通关步骤提取核心动作
        if hasattr(game_info, 'walkthrough') and game_info.walkthrough:
            print(f"📋 从通关步骤提取动作 ({len(game_info.walkthrough)} 步)")
            self._create_actions_from_walkthrough(game_info.walkthrough)

        # 2. 从可执行命令补充动作
        if hasattr(game_state, 'admissible_commands') and game_state.admissible_commands:
            print(f"📋 从可执行命令补充动作 ({len(game_state.admissible_commands)} 个)")
            self._create_actions_from_commands(game_state.admissible_commands[:20])  # 限制数量避免过多
        else:
            print("⚠️ 无法获取可执行命令")

    def _create_actions_from_walkthrough(self, walkthrough: List[str]):
        """从通关步骤创建核心动作"""
        player = next((e for e in self.entities if e.entity_type == "角色"), None)
        if not player:
            return

        print("🎯 通关步骤动作:")
        for i, command in enumerate(walkthrough):
            print(f"   {i+1}. {command}")
            self._parse_and_create_action(command, f"核心动作{i+1}", is_core_action=True)

    def _create_actions_from_commands(self, commands: List[str]):
        """从可执行命令创建补充动作"""
        processed_actions = set()

        for command in commands:
            if command not in processed_actions:
                self._parse_and_create_action(command, f"补充动作", is_core_action=False)
                processed_actions.add(command)

    def _parse_and_create_action(self, command: str, action_prefix: str, is_core_action: bool = False):
        """解析命令并创建动作 - 增强版，支持复杂命令格式"""
        words = command.lower().split()
        if not words:
            return

        action_verb = words[0]
        player = next((e for e in self.entities if e.entity_type == "角色"), None)
        if not player:
            return

        # 基于从真实TextWorld数据提取的13个动词
        # 真实动词: ['close', 'drop', 'eat', 'examine', 'go', 'insert', 'inventory', 'lock', 'look', 'open', 'put', 'take', 'unlock']

        # === 1. TAKE 动作 ===
        # 支持格式: "take X" 或 "take X from Y"
        if action_verb == 'take' and len(words) > 1:
            # 检查是否有 "from" 关键词
            if 'from' in words:
                from_index = words.index('from')
                target_name = ' '.join(words[1:from_index])
                container_name = ' '.join(words[from_index+1:])

                target_entity = self._find_entity_by_partial_name(target_name)
                container_entity = self._find_entity_by_partial_name(container_name)

                if target_entity and container_entity:
                    action = GameAction(
                        id=f"action_{self.action_counter}",
                        name=f"从{container_entity.name}获取{target_entity.name}",
                        description=f"从{container_entity.name}中拿取{target_entity.name}",
                        required_entities=[player.name, target_entity.name, container_entity.name],
                        required_states={
                            target_entity.name: "可获取",
                            container_entity.name: "打开"
                        },
                        effects={target_entity.name: "已获取"},
                        result="获取成功"
                    )
                    self.actions.append(action)
                    self.action_counter += 1
                    return

            # 简单的 "take X" 格式
            target_name = ' '.join(words[1:])
            target_name = ' '.join(words[1:])
            target_entity = self._find_entity_by_partial_name(target_name)

            if target_entity and target_entity.entity_type in ["食物", "钥匙", "物品"]:
                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"获取{target_entity.name}",
                    description=f"从环境中拿取{target_entity.name}",
                    required_entities=[player.name, target_entity.name],
                    required_states={target_entity.name: "可获取"},
                    effects={target_entity.name: "已获取"},
                    result="获取成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        elif action_verb == 'open' and len(words) > 1:
            target_name = ' '.join(words[1:])
            target_entity = self._find_entity_by_partial_name(target_name)

            if target_entity and target_entity.entity_type in ["容器", "门"]:
                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"打开{target_entity.name}",
                    description=f"打开{target_entity.name}",
                    required_entities=[player.name, target_entity.name],
                    required_states={target_entity.name: "关闭"},
                    effects={target_entity.name: "打开"},
                    result="打开成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        elif action_verb == 'close' and len(words) > 1:
            target_name = ' '.join(words[1:])
            target_entity = self._find_entity_by_partial_name(target_name)

            if target_entity and target_entity.entity_type in ["容器", "门"]:
                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"关闭{target_entity.name}",
                    description=f"关闭{target_entity.name}",
                    required_entities=[player.name, target_entity.name],
                    required_states={target_entity.name: "打开"},
                    effects={target_entity.name: "关闭"},
                    result="关闭成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        # === 4. UNLOCK 动作 ===
        # 支持格式: "unlock X" 或 "unlock X with Y"
        elif action_verb == 'unlock' and len(words) > 1:
            # 检查是否有 "with" 关键词
            if 'with' in words:
                with_index = words.index('with')
                target_name = ' '.join(words[1:with_index])
                key_name = ' '.join(words[with_index+1:])

                target_entity = self._find_entity_by_partial_name(target_name)
                key_entity = self._find_entity_by_partial_name(key_name)

                if target_entity and target_entity.entity_type in ["容器", "门"]:
                    required_states = {target_entity.name: "锁定"}
                    required_entities = [player.name, target_entity.name]

                    if key_entity:
                        required_states[key_entity.name] = "已获取"
                        required_entities.append(key_entity.name)

                    action = GameAction(
                        id=f"action_{self.action_counter}",
                        name=f"用{key_entity.name if key_entity else '钥匙'}解锁{target_entity.name}",
                        description=f"使用{key_entity.name if key_entity else '钥匙'}解锁{target_entity.name}",
                        required_entities=required_entities,
                        required_states=required_states,
                        effects={target_entity.name: "解锁"},
                        result="解锁成功"
                    )
                    self.actions.append(action)
                    self.action_counter += 1
                    return

            # 简单的 "unlock X" 格式
            target_name = ' '.join(words[1:])
            target_entity = self._find_entity_by_partial_name(target_name)

            if target_entity and target_entity.entity_type in ["容器", "门"]:
                key_entity = next((e for e in self.entities if e.entity_type == "钥匙"), None)
                required_states = {target_entity.name: "锁定"}
                if key_entity:
                    required_states[key_entity.name] = "已获取"

                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"解锁{target_entity.name}",
                    description=f"使用钥匙解锁{target_entity.name}",
                    required_entities=[player.name, target_entity.name] + ([key_entity.name] if key_entity else []),
                    required_states=required_states,
                    effects={target_entity.name: "解锁"},
                    result="解锁成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        # === 5. LOCK 动作 ===
        # 支持格式: "lock X" 或 "lock X with Y"
        elif action_verb == 'lock' and len(words) > 1:
            # 检查是否有 "with" 关键词
            if 'with' in words:
                with_index = words.index('with')
                target_name = ' '.join(words[1:with_index])
                key_name = ' '.join(words[with_index+1:])

                target_entity = self._find_entity_by_partial_name(target_name)
                key_entity = self._find_entity_by_partial_name(key_name)

                if target_entity and target_entity.entity_type in ["容器", "门"]:
                    required_states = {target_entity.name: "解锁"}
                    required_entities = [player.name, target_entity.name]

                    if key_entity:
                        required_states[key_entity.name] = "已获取"
                        required_entities.append(key_entity.name)

                    action = GameAction(
                        id=f"action_{self.action_counter}",
                        name=f"用{key_entity.name if key_entity else '钥匙'}锁定{target_entity.name}",
                        description=f"使用{key_entity.name if key_entity else '钥匙'}锁定{target_entity.name}",
                        required_entities=required_entities,
                        required_states=required_states,
                        effects={target_entity.name: "锁定"},
                        result="锁定成功"
                    )
                    self.actions.append(action)
                    self.action_counter += 1
                    return

            # 简单的 "lock X" 格式
            target_name = ' '.join(words[1:])
            target_entity = self._find_entity_by_partial_name(target_name)

            if target_entity and target_entity.entity_type in ["容器", "门"]:
                key_entity = next((e for e in self.entities if e.entity_type == "钥匙"), None)
                required_states = {target_entity.name: "解锁"}
                if key_entity:
                    required_states[key_entity.name] = "已获取"

                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"锁定{target_entity.name}",
                    description=f"使用钥匙锁定{target_entity.name}",
                    required_entities=[player.name, target_entity.name] + ([key_entity.name] if key_entity else []),
                    required_states=required_states,
                    effects={target_entity.name: "锁定"},
                    result="锁定成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        elif action_verb == 'go' and len(words) > 1:
            # 基于真实方向: ['east', 'north', 'south', 'west']
            direction = words[1]
            if direction in ['east', 'north', 'south', 'west']:
                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"向{direction}移动",
                    description=f"向{direction}方向移动",
                    required_entities=[player.name],
                    required_states={player.name: "探索中"},
                    effects={player.name: "探索中"},
                    result=f"移动到{direction}方向"
                )
                self.actions.append(action)
                self.action_counter += 1

        # === 7. PUT 动作 ===
        # 支持格式: "put X on Y" 或 "put X in Y"
        elif action_verb == 'put' and len(words) > 3:
            if 'on' in words:
                on_index = words.index('on')
                item_name = ' '.join(words[1:on_index])
                surface_name = ' '.join(words[on_index+1:])

                item_entity = self._find_entity_by_partial_name(item_name)
                surface_entity = self._find_entity_by_partial_name(surface_name)

                if item_entity and surface_entity:
                    action = GameAction(
                        id=f"action_{self.action_counter}",
                        name=f"放置{item_entity.name}到{surface_entity.name}",
                        description=f"将{item_entity.name}放置到{surface_entity.name}上",
                        required_entities=[player.name, item_entity.name, surface_entity.name],
                        required_states={item_entity.name: "已获取"},
                        effects={item_entity.name: "已放置"},
                        result="放置成功"
                    )
                    self.actions.append(action)
                    self.action_counter += 1
                    return

            elif 'in' in words:
                in_index = words.index('in')
                item_name = ' '.join(words[1:in_index])
                container_name = ' '.join(words[in_index+1:])

                item_entity = self._find_entity_by_partial_name(item_name)
                container_entity = self._find_entity_by_partial_name(container_name)

                if item_entity and container_entity and container_entity.entity_type == "容器":
                    action = GameAction(
                        id=f"action_{self.action_counter}",
                        name=f"放入{item_entity.name}到{container_entity.name}",
                        description=f"将{item_entity.name}放入{container_entity.name}中",
                        required_entities=[player.name, item_entity.name, container_entity.name],
                        required_states={
                            item_entity.name: "已获取",
                            container_entity.name: "打开"
                        },
                        effects={item_entity.name: "已放置"},
                        result="放入成功"
                    )
                    self.actions.append(action)
                    self.action_counter += 1
                    return

        elif action_verb == 'drop' and len(words) > 1:
            target_name = ' '.join(words[1:])
            target_entity = self._find_entity_by_partial_name(target_name)

            if target_entity:
                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"丢弃{target_entity.name}",
                    description=f"丢弃{target_entity.name}",
                    required_entities=[player.name, target_entity.name],
                    required_states={target_entity.name: "已获取"},
                    effects={target_entity.name: "可获取"},
                    result="丢弃成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        # === 9. EAT 动作 ===
        elif action_verb == 'eat' and len(words) > 1:
            target_name = ' '.join(words[1:])
            target_entity = self._find_entity_by_partial_name(target_name)

            if target_entity and target_entity.entity_type == "食物":
                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"食用{target_entity.name}",
                    description=f"食用{target_entity.name}",
                    required_entities=[player.name, target_entity.name],
                    required_states={target_entity.name: "已获取"},
                    effects={target_entity.name: "已消耗"},
                    result="食用成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        # === 10. INSERT 动作 ===
        # 支持格式: "insert X into Y"
        elif action_verb == 'insert' and len(words) > 3 and 'into' in words:
            into_index = words.index('into')
            item_name = ' '.join(words[1:into_index])
            container_name = ' '.join(words[into_index+1:])

            item_entity = self._find_entity_by_partial_name(item_name)
            container_entity = self._find_entity_by_partial_name(container_name)

            if item_entity and container_entity and container_entity.entity_type == "容器":
                action = GameAction(
                    id=f"action_{self.action_counter}",
                    name=f"插入{item_entity.name}到{container_entity.name}",
                    description=f"将{item_entity.name}插入{container_entity.name}中",
                    required_entities=[player.name, item_entity.name, container_entity.name],
                    required_states={
                        item_entity.name: "已获取",
                        container_entity.name: "打开"
                    },
                    effects={item_entity.name: "已放置"},
                    result="插入成功"
                )
                self.actions.append(action)
                self.action_counter += 1

        # 为每个动作创建结果节点
        if hasattr(self, 'actions') and self.actions:
            last_action = self.actions[-1]
            result = {
                "id": f"result_{self.result_counter}",
                "type": "result",
                "name": f"{last_action.name}_结果",
                "attributes": {
                    "action_name": last_action.name,
                    "description": f"执行{last_action.name}的结果",
                    "result_value": last_action.result,
                    "is_core_action": is_core_action
                }
            }
            self.results.append(result)
            self.result_counter += 1
    
    def _find_entity_by_name(self, name: str) -> Optional[GameEntity]:
        """根据名称查找实体"""
        name_lower = name.lower()
        for entity in self.entities:
            if name_lower in entity.name.lower() or name_lower == entity.name.lower():
                return entity
        return None

    def _find_entity_by_partial_name(self, partial_name: str) -> Optional[GameEntity]:
        """根据部分名称查找实体（支持模糊匹配）"""
        partial_lower = partial_name.lower().strip()

        # 首先尝试精确匹配
        for entity in self.entities:
            if partial_lower == entity.name.lower():
                return entity

        # 然后尝试包含匹配
        for entity in self.entities:
            if partial_lower in entity.name.lower() or entity.name.lower() in partial_lower:
                return entity

        # 最后尝试基于属性匹配
        for entity in self.entities:
            if hasattr(entity, 'properties') and entity.properties:
                # 检查原始名称
                if 'original_name' in entity.properties:
                    orig_name = str(entity.properties['original_name']).lower()
                    if partial_lower in orig_name or orig_name in partial_lower:
                        return entity

                # 检查物品ID
                if '物品ID' in entity.properties:
                    obj_id = str(entity.properties['物品ID']).lower()
                    if partial_lower in obj_id:
                        return entity

        return None

    def _create_states_for_entities(self):
        """为所有实体创建状态节点"""
        for entity in self.entities:
            for state_value in entity.possible_states:
                state = GameState(
                    id=f"state_{self.state_counter}",
                    name=f"{entity.name}_{state_value}",
                    entity_name=entity.name,
                    state_value=state_value,
                    is_initial=(state_value == entity.initial_state),
                    description=f"{entity.name}的状态: {state_value}"
                )
                self.states.append(state)
                self.state_counter += 1

    def _create_state_transitions(self):
        """创建状态转换"""
        for action in self.actions:
            # 为每个动作的效果创建状态转换
            for entity_name, to_state in action.effects.items():
                from_state = action.required_states.get(entity_name)
                if from_state:
                    transition = StateTransition(
                        from_state=f"{entity_name}_{from_state}",
                        to_state=f"{entity_name}_{to_state}",
                        action=action.name,
                        conditions=[f"{entity_name}必须处于{from_state}状态"],
                        effects=[f"{entity_name}变为{to_state}状态"]
                    )
                    self.transitions.append(transition)

    def _create_relationships(self):
        """创建边关系"""
        # 动作需要实体
        for action in self.actions:
            for entity_name in action.required_entities:
                entity = next((e for e in self.entities if e.name == entity_name), None)
                if entity:
                    self.edges.append({
                        "source": action.id,
                        "target": entity.id,
                        "type": "requires",
                        "attributes": {
                            "relationship": "action_requires_entity"
                        }
                    })

        # 动作需要状态
        for action in self.actions:
            for entity_name, state_value in action.required_states.items():
                state = next((s for s in self.states
                            if s.entity_name == entity_name and s.state_value == state_value), None)
                if state:
                    self.edges.append({
                        "source": action.id,
                        "target": state.id,
                        "type": "requires",
                        "attributes": {
                            "relationship": "action_requires_state",
                            "required_value": state_value
                        }
                    })

        # 动作修改状态
        for action in self.actions:
            for entity_name, state_value in action.effects.items():
                state = next((s for s in self.states
                            if s.entity_name == entity_name and s.state_value == state_value), None)
                if state:
                    self.edges.append({
                        "source": action.id,
                        "target": state.id,
                        "type": "modifies",
                        "attributes": {
                            "relationship": "action_modifies_state",
                            "new_value": state_value
                        }
                    })

        # 动作产生结果
        for i, action in enumerate(self.actions):
            if i < len(self.results):
                self.edges.append({
                    "source": action.id,
                    "target": self.results[i]["id"],
                    "type": "produces",
                    "attributes": {
                        "relationship": "action_produces_result"
                    }
                })

        # 状态转换
        for transition in self.transitions:
            from_state = next((s for s in self.states if s.name == transition.from_state), None)
            to_state = next((s for s in self.states if s.name == transition.to_state), None)

            if from_state and to_state:
                self.edges.append({
                    "source": from_state.id,
                    "target": to_state.id,
                    "type": "transitions",
                    "attributes": {
                        "action": transition.action,
                        "conditions": transition.conditions,
                        "effects": transition.effects
                    }
                })

    def _build_final_kg_data(self, scenario_name: str, game_info=None) -> Dict[str, Any]:
        """构建最终的KG数据 - 包含任务场景信息"""
        nodes = []

        # 添加实体节点
        for entity in self.entities:
            nodes.append({
                "id": entity.id,
                "type": "entity",
                "name": entity.name,
                "attributes": {
                    "entity_type": entity.entity_type,
                    "properties": entity.properties,
                    "initial_state": entity.initial_state,
                    "possible_states": entity.possible_states,
                    "description": entity.description
                }
            })

        # 添加状态节点
        for state in self.states:
            nodes.append({
                "id": state.id,
                "type": "state",
                "name": state.name,
                "attributes": {
                    "entity_name": state.entity_name,
                    "state_type": "entity_state",
                    "is_initial": state.is_initial,
                    "state_value": state.state_value,
                    "description": state.description
                }
            })

        # 添加动作节点
        for action in self.actions:
            nodes.append({
                "id": action.id,
                "type": "action",
                "name": action.name,
                "attributes": {
                    "description": action.description,
                    "required_entities": action.required_entities,
                    "required_states": action.required_states,
                    "effects": action.effects,
                    "result": action.result
                }
            })

        # 添加结果节点
        for result in self.results:
            nodes.append(result)

        # 提取任务场景信息
        task_info = {}
        if game_info:
            if hasattr(game_info, 'objective'):
                task_info['objective'] = game_info.objective
            if hasattr(game_info, 'max_score'):
                task_info['max_score'] = game_info.max_score
            if hasattr(game_info, 'walkthrough'):
                task_info['walkthrough'] = game_info.walkthrough
                task_info['walkthrough_length'] = len(game_info.walkthrough)

        return {
            "nodes": nodes,
            "edges": self.edges,
            "metadata": {
                "node_count": len(nodes),
                "edge_count": len(self.edges),
                "node_types": ["entity", "state", "action", "result"],
                "scene_name": scenario_name,
                "scene_type": "task_scene",  # 标记为任务场景
                "game_type": "textworld",
                "schema_version": "2.0",  # 更新版本号
                "data_source": "real_textworld_game",
                "task_info": task_info  # 添加任务信息
            }
        }


def main():
    """主函数 - 按任务场景批量处理所有TextWorld游戏文件"""
    print("🚀 TextWorld Knowledge Graph Builder - Task-Scene Based")
    print("=" * 80)
    print("📋 策略: 为每个任务场景生成独立的知识图谱")
    print("=" * 80)

    builder = RealTextWorldKGBuilder()

    # 查找真实的TextWorld游戏文件
    textworld_dir = project_root / "data/benchmarks/textworld"
    game_files = []

    # 查找.z8和.ulx文件
    for pattern in ["**/*.z8", "**/*.ulx"]:
        game_files.extend(textworld_dir.glob(pattern))

    if not game_files:
        print("❌ 未找到TextWorld游戏文件")
        print(f"📁 搜索目录: {textworld_dir}")
        return

    # 排序确保处理顺序一致
    game_files = sorted(game_files)

    print(f"\n📁 找到 {len(game_files)} 个TextWorld任务场景文件:")
    for i, gf in enumerate(game_files, 1):
        print(f"   {i}. {gf.name}")

    print(f"\n{'=' * 80}")
    print(f"🎯 开始批量处理...")
    print(f"{'=' * 80}\n")

    # 统计信息
    success_count = 0
    failed_count = 0
    failed_files = []
    kg_summary = []

    # 批量处理所有游戏文件
    for i, game_file in enumerate(game_files, 1):
        print(f"\n{'=' * 80}")
        print(f"� 处理任务场景 {i}/{len(game_files)}: {game_file.name}")
        print(f"{'=' * 80}")

        try:
            # 构建KG
            kg_data = builder.build_kg_from_real_game_file(str(game_file))

            # 保存KG文件
            scenario_name = kg_data["metadata"]["scene_name"]
            output_file = project_root / f"data/kg/task_scenes/{scenario_name}_task_kg.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(kg_data, f, indent=2, ensure_ascii=False)

            # 统计节点类型分布
            node_types = {}
            for node in kg_data['nodes']:
                node_type = node['type']
                node_types[node_type] = node_types.get(node_type, 0) + 1

            print(f"\n✅ KG保存成功: {output_file.name}")
            print(f"📊 统计: {kg_data['metadata']['node_count']} 节点, {kg_data['metadata']['edge_count']} 边")
            print(f"📋 节点类型分布: {node_types}")

            # 记录成功
            success_count += 1
            kg_summary.append({
                "file": game_file.name,
                "scenario": scenario_name,
                "output": output_file.name,
                "nodes": kg_data['metadata']['node_count'],
                "edges": kg_data['metadata']['edge_count'],
                "node_types": node_types,
                "status": "success"
            })

        except Exception as e:
            print(f"\n❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()

            failed_count += 1
            failed_files.append(game_file.name)
            kg_summary.append({
                "file": game_file.name,
                "status": "failed",
                "error": str(e)
            })

    # 打印最终汇总
    print(f"\n{'=' * 80}")
    print(f"🎉 批量处理完成！")
    print(f"{'=' * 80}")
    print(f"✅ 成功: {success_count}/{len(game_files)}")
    print(f"❌ 失败: {failed_count}/{len(game_files)}")

    if failed_files:
        print(f"\n❌ 失败的文件:")
        for ff in failed_files:
            print(f"   - {ff}")

    # 保存汇总报告
    summary_file = project_root / "data/kg/task_scenes/task_scenes_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_files": len(game_files),
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_files": failed_files,
            "kg_details": kg_summary
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📄 汇总报告已保存: {summary_file.name}")
    print(f"📁 所有KG文件保存在: data/kg/task_scenes/")
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()
