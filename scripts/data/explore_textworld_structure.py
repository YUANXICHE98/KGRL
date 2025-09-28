#!/usr/bin/env python3
"""
TextWorld游戏文件结构探索脚本
深入分析真实TextWorld游戏文件的内部结构，不做任何假设
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import textworld
    TEXTWORLD_AVAILABLE = True
except ImportError:
    TEXTWORLD_AVAILABLE = False
    print("❌ TextWorld未安装，请运行: pip install textworld")
    sys.exit(1)


class TextWorldExplorer:
    """TextWorld游戏文件结构探索器"""
    
    def __init__(self):
        self.exploration_results = []
    
    def explore_game_file(self, game_file_path: str) -> Dict[str, Any]:
        """深度探索单个游戏文件"""
        
        print(f"\n🔍 探索游戏文件: {Path(game_file_path).name}")
        print("=" * 60)
        
        result = {
            "file_path": game_file_path,
            "file_name": Path(game_file_path).name,
            "exploration_success": False,
            "error": None,
            "game_state_structure": {},
            "game_info_structure": {},
            "admissible_commands": [],
            "world_structure": {},
            "objects_found": [],
            "rooms_found": [],
            "other_attributes": {}
        }
        
        try:
            # 启动游戏环境
            env = textworld.start(game_file_path)
            game_state = env.reset()
            
            print("✅ 成功启动游戏环境")
            
            # 1. 探索game_state结构
            print("\n📋 探索 game_state 结构:")
            result["game_state_structure"] = self._explore_object_structure(game_state, "game_state")
            
            # 2. 探索game_info结构
            if hasattr(game_state, 'game') and game_state.game is not None:
                print("\n📋 探索 game_info 结构:")
                game_info = game_state.game
                result["game_info_structure"] = self._explore_object_structure(game_info, "game_info")
                
                # 3. 探索world结构
                if hasattr(game_info, 'world'):
                    print("\n🌍 探索 world 结构:")
                    world = game_info.world
                    result["world_structure"] = self._explore_object_structure(world, "world")
                    
                    # 4. 详细探索objects
                    if hasattr(world, 'objects'):
                        print(f"\n📦 发现 {len(world.objects)} 个objects:")
                        for i, obj in enumerate(world.objects):
                            obj_info = self._explore_object_structure(obj, f"object_{i}")
                            result["objects_found"].append(obj_info)
                            print(f"   Object {i}: {obj_info.get('summary', 'Unknown')}")
                    
                    # 5. 详细探索rooms
                    if hasattr(world, 'rooms'):
                        print(f"\n🏠 发现 {len(world.rooms)} 个rooms:")
                        for i, room in enumerate(world.rooms):
                            room_info = self._explore_object_structure(room, f"room_{i}")
                            result["rooms_found"].append(room_info)
                            print(f"   Room {i}: {room_info.get('summary', 'Unknown')}")
            else:
                print("⚠️ 无法获取game_info")
            
            # 6. 获取可执行命令
            if hasattr(game_state, 'admissible_commands'):
                commands = game_state.admissible_commands
                result["admissible_commands"] = commands
                print(f"\n🎮 发现 {len(commands)} 个可执行命令:")
                for cmd in commands[:10]:  # 只显示前10个
                    print(f"   - {cmd}")
                if len(commands) > 10:
                    print(f"   ... 还有 {len(commands) - 10} 个命令")
            
            # 7. 探索其他属性
            print("\n🔍 探索其他属性:")
            other_attrs = {}
            for attr_name in dir(game_state):
                if not attr_name.startswith('_') and attr_name not in ['game', 'admissible_commands']:
                    try:
                        attr_value = getattr(game_state, attr_name)
                        if not callable(attr_value):
                            other_attrs[attr_name] = {
                                "type": str(type(attr_value).__name__),
                                "value": str(attr_value)[:100] + "..." if len(str(attr_value)) > 100 else str(attr_value)
                            }
                            print(f"   - {attr_name}: {type(attr_value).__name__} = {str(attr_value)[:50]}...")
                    except Exception as e:
                        other_attrs[attr_name] = {"error": str(e)}
            
            result["other_attributes"] = other_attrs
            result["exploration_success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 探索失败: {e}")
        
        finally:
            try:
                env.close()
            except:
                pass
        
        return result
    
    def _explore_object_structure(self, obj, obj_name: str) -> Dict[str, Any]:
        """深度探索对象结构"""
        
        structure = {
            "object_name": obj_name,
            "type": str(type(obj).__name__),
            "attributes": {},
            "methods": [],
            "summary": ""
        }
        
        # 获取所有属性
        for attr_name in dir(obj):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(obj, attr_name)
                    
                    if callable(attr_value):
                        structure["methods"].append(attr_name)
                    else:
                        attr_info = {
                            "type": str(type(attr_value).__name__),
                            "value": None
                        }
                        
                        # 根据类型处理值
                        if isinstance(attr_value, (str, int, float, bool)):
                            attr_info["value"] = attr_value
                        elif isinstance(attr_value, (list, tuple)):
                            attr_info["length"] = len(attr_value)
                            attr_info["value"] = f"[{len(attr_value)} items]"
                            if len(attr_value) > 0:
                                attr_info["first_item_type"] = str(type(attr_value[0]).__name__)
                        elif isinstance(attr_value, dict):
                            attr_info["length"] = len(attr_value)
                            attr_info["value"] = f"{{{len(attr_value)} keys}}"
                            attr_info["keys"] = list(attr_value.keys())[:5]  # 前5个key
                        else:
                            attr_info["value"] = str(attr_value)[:100] + "..." if len(str(attr_value)) > 100 else str(attr_value)
                        
                        structure["attributes"][attr_name] = attr_info
                        
                except Exception as e:
                    structure["attributes"][attr_name] = {"error": str(e)}
        
        # 生成摘要
        key_attrs = []
        for attr_name, attr_info in structure["attributes"].items():
            if attr_name in ['name', 'id', 'type', 'desc', 'description']:
                key_attrs.append(f"{attr_name}={attr_info.get('value', 'N/A')}")
        
        structure["summary"] = f"{structure['type']}({', '.join(key_attrs)})" if key_attrs else structure['type']
        
        return structure
    
    def explore_all_games(self, max_games: int = 3) -> List[Dict[str, Any]]:
        """探索多个游戏文件"""
        
        print("🚀 TextWorld游戏文件结构探索器")
        print("=" * 60)
        
        # 查找游戏文件
        textworld_dir = project_root / "data/benchmarks/textworld"
        game_files = []
        
        for pattern in ["**/*.z8", "**/*.ulx"]:
            game_files.extend(textworld_dir.glob(pattern))
        
        if not game_files:
            print("❌ 未找到TextWorld游戏文件")
            print(f"📁 搜索目录: {textworld_dir}")
            return []
        
        print(f"📁 找到 {len(game_files)} 个TextWorld游戏文件")
        print(f"🎯 将探索前 {min(max_games, len(game_files))} 个文件")
        
        results = []
        for i, game_file in enumerate(game_files[:max_games]):
            result = self.explore_game_file(str(game_file))
            results.append(result)
            self.exploration_results.append(result)
        
        return results
    
    def save_exploration_report(self, output_file: str):
        """保存探索报告"""
        
        report = {
            "exploration_summary": {
                "total_files_explored": len(self.exploration_results),
                "successful_explorations": len([r for r in self.exploration_results if r["exploration_success"]]),
                "failed_explorations": len([r for r in self.exploration_results if not r["exploration_success"]])
            },
            "detailed_results": self.exploration_results,
            "common_patterns": self._analyze_common_patterns()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 探索报告已保存: {output_file}")
    
    def _analyze_common_patterns(self) -> Dict[str, Any]:
        """分析共同模式"""
        
        patterns = {
            "common_game_state_attributes": {},
            "common_world_attributes": {},
            "common_object_types": {},
            "common_room_attributes": {},
            "command_patterns": {}
        }
        
        successful_results = [r for r in self.exploration_results if r["exploration_success"]]
        
        if not successful_results:
            return patterns
        
        # 分析game_state共同属性
        for result in successful_results:
            for attr_name in result["game_state_structure"].get("attributes", {}):
                patterns["common_game_state_attributes"][attr_name] = patterns["common_game_state_attributes"].get(attr_name, 0) + 1
        
        # 分析world共同属性
        for result in successful_results:
            for attr_name in result["world_structure"].get("attributes", {}):
                patterns["common_world_attributes"][attr_name] = patterns["common_world_attributes"].get(attr_name, 0) + 1
        
        # 分析object类型
        for result in successful_results:
            for obj_info in result["objects_found"]:
                obj_type = obj_info.get("type", "Unknown")
                patterns["common_object_types"][obj_type] = patterns["common_object_types"].get(obj_type, 0) + 1
        
        return patterns


def main():
    """主函数"""
    
    explorer = TextWorldExplorer()
    
    # 探索游戏文件
    results = explorer.explore_all_games(max_games=2)  # 先探索2个文件
    
    if results:
        print(f"\n📊 探索完成! 成功探索 {len([r for r in results if r['exploration_success']])} 个文件")
        
        # 保存详细报告
        report_file = project_root / "data/extraction/textworld_structure_exploration.json"
        explorer.save_exploration_report(str(report_file))
        
        # 显示关键发现
        print("\n🔍 关键发现:")
        successful_results = [r for r in results if r["exploration_success"]]
        
        if successful_results:
            # 显示第一个成功的结果摘要
            first_result = successful_results[0]
            print(f"\n📋 示例游戏结构 ({first_result['file_name']}):")
            
            if first_result["objects_found"]:
                print(f"   - Objects: {len(first_result['objects_found'])} 个")
                for obj in first_result["objects_found"][:3]:
                    print(f"     * {obj.get('summary', 'Unknown')}")
            
            if first_result["rooms_found"]:
                print(f"   - Rooms: {len(first_result['rooms_found'])} 个")
                for room in first_result["rooms_found"][:3]:
                    print(f"     * {room.get('summary', 'Unknown')}")
            
            if first_result["admissible_commands"]:
                print(f"   - Commands: {len(first_result['admissible_commands'])} 个")
                for cmd in first_result["admissible_commands"][:5]:
                    print(f"     * {cmd}")
    else:
        print("❌ 没有成功探索任何文件")


if __name__ == "__main__":
    main()
