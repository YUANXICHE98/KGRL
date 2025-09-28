#!/usr/bin/env python3
"""
TextWorld数据目录提取器
从所有真实TextWorld游戏文件中提取完整的数据目录，生成CSV文件
严格遵循不使用模拟数据的原则
"""

import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import textworld
    TEXTWORLD_AVAILABLE = True
except ImportError:
    TEXTWORLD_AVAILABLE = False
    raise RuntimeError("❌ TextWorld未安装，请运行: pip install textworld")


class TextWorldDataCatalogExtractor:
    """TextWorld真实数据目录提取器"""
    
    def __init__(self):
        if not TEXTWORLD_AVAILABLE:
            raise RuntimeError("❌ TextWorld未安装")
        
        # 数据收集器
        self.all_type_codes = set()
        self.all_entity_names = set()
        self.all_object_names = set()
        self.all_verbs = set()
        self.all_directions = set()
        self.all_commands = set()
        self.all_objectives = []
        self.all_walkthroughs = []
        
        # 详细统计
        self.type_code_stats = defaultdict(int)
        self.entity_name_stats = defaultdict(int)
        self.verb_stats = defaultdict(int)
        self.direction_stats = defaultdict(int)
        
        # 游戏文件统计
        self.processed_files = []
        self.failed_files = []
    
    def extract_from_all_games(self, max_games: int = None) -> Dict[str, Any]:
        """从所有TextWorld游戏文件中提取数据"""
        
        # 查找所有TextWorld游戏文件
        textworld_dir = project_root / "data/benchmarks/textworld"
        game_files = []
        
        for pattern in ["**/*.z8", "**/*.ulx"]:
            game_files.extend(textworld_dir.glob(pattern))
        
        if not game_files:
            raise FileNotFoundError(f"❌ 未找到TextWorld游戏文件，搜索目录: {textworld_dir}")
        
        print(f"📁 找到 {len(game_files)} 个TextWorld游戏文件")
        
        # 限制处理数量（如果指定）
        if max_games:
            game_files = game_files[:max_games]
            print(f"🎯 将处理前 {max_games} 个文件")
        
        # 处理每个游戏文件
        for i, game_file in enumerate(game_files):
            print(f"\n🎮 处理游戏 {i+1}/{len(game_files)}: {game_file.name}")
            try:
                self._extract_from_single_game(str(game_file))
                self.processed_files.append(str(game_file))
            except Exception as e:
                print(f"❌ 处理失败: {e}")
                self.failed_files.append((str(game_file), str(e)))
                continue
        
        # 生成统计报告
        return self._generate_catalog_report()
    
    def _extract_from_single_game(self, game_file_path: str):
        """从单个游戏文件提取数据 - 修复版本"""

        env = None
        try:
            print(f"   🔄 启动游戏环境...")
            env = textworld.start(game_file_path)
            game_state = env.reset()

            print(f"   📋 游戏状态类型: {type(game_state)}")
            print(f"   📋 游戏状态属性: {list(game_state.keys()) if hasattr(game_state, 'keys') else 'N/A'}")

            # 检查game_state结构
            if hasattr(game_state, 'game') and game_state.game is not None:
                game_info = game_state.game
                print(f"   ✅ 获取到game_info")
            else:
                print(f"   ⚠️ game_state没有game属性或为None，尝试直接使用game_state")
                # 有些TextWorld版本可能直接在game_state中包含信息
                game_info = game_state

            # 1. 提取类型编码 - 更安全的方式
            print(f"   🔍 提取类型编码...")
            if hasattr(game_info, 'world') and game_info.world is not None:
                world = game_info.world
                if hasattr(world, 'objects') and world.objects is not None:
                    print(f"      发现 {len(world.objects)} 个objects")
                    for obj in world.objects:
                        if hasattr(obj, 'type') and obj.type is not None:
                            type_code = str(obj.type)
                            self.all_type_codes.add(type_code)
                            self.type_code_stats[type_code] += 1
                            print(f"         类型: {type_code}")
                else:
                    print(f"      ⚠️ world没有objects属性")
            else:
                print(f"      ⚠️ game_info没有world属性")

            # 2. 提取实体名称
            print(f"   🔍 提取实体名称...")
            if hasattr(game_info, 'entity_names') and game_info.entity_names is not None:
                print(f"      发现 {len(game_info.entity_names)} 个entity_names")
                for name in game_info.entity_names:
                    if name is not None:
                        name_str = str(name)
                        self.all_entity_names.add(name_str)
                        self.entity_name_stats[name_str] += 1
            else:
                print(f"      ⚠️ 没有entity_names属性")

            # 3. 提取物品名称
            print(f"   🔍 提取物品名称...")
            if hasattr(game_info, 'objects_names') and game_info.objects_names is not None:
                print(f"      发现 {len(game_info.objects_names)} 个objects_names")
                for name in game_info.objects_names:
                    if name is not None:
                        name_str = str(name)
                        self.all_object_names.add(name_str)
            else:
                print(f"      ⚠️ 没有objects_names属性")

            # 4. 提取动词
            print(f"   🔍 提取动词...")
            if hasattr(game_info, 'verbs') and game_info.verbs is not None:
                print(f"      发现 {len(game_info.verbs)} 个verbs")
                for verb in game_info.verbs:
                    if verb is not None:
                        verb_str = str(verb)
                        self.all_verbs.add(verb_str)
                        self.verb_stats[verb_str] += 1
            else:
                print(f"      ⚠️ 没有verbs属性")

            # 5. 提取方向
            print(f"   🔍 提取方向...")
            if hasattr(game_info, 'directions_names') and game_info.directions_names is not None:
                print(f"      发现 {len(game_info.directions_names)} 个directions")
                for direction in game_info.directions_names:
                    if direction is not None:
                        direction_str = str(direction)
                        self.all_directions.add(direction_str)
                        self.direction_stats[direction_str] += 1
            else:
                print(f"      ⚠️ 没有directions_names属性")

            # 6. 提取可执行命令样本
            print(f"   🔍 提取可执行命令...")
            if hasattr(game_state, 'admissible_commands') and game_state.admissible_commands is not None:
                commands = game_state.admissible_commands[:10]  # 只取前10个作为样本
                print(f"      发现 {len(commands)} 个commands (样本)")
                for cmd in commands:
                    if cmd is not None:
                        self.all_commands.add(str(cmd))
            else:
                print(f"      ⚠️ 没有admissible_commands属性")

            # 7. 提取游戏目标
            print(f"   🔍 提取游戏目标...")
            if hasattr(game_info, 'objective') and game_info.objective is not None:
                objective_str = str(game_info.objective)
                self.all_objectives.append(objective_str)
                print(f"      目标长度: {len(objective_str)} 字符")
            else:
                print(f"      ⚠️ 没有objective属性")

            # 8. 提取通关步骤
            print(f"   🔍 提取通关步骤...")
            if hasattr(game_info, 'walkthrough') and game_info.walkthrough is not None:
                walkthrough_steps = [str(step) for step in game_info.walkthrough if step is not None]
                self.all_walkthroughs.append(walkthrough_steps)
                print(f"      通关步骤: {len(walkthrough_steps)} 步")
            else:
                print(f"      ⚠️ 没有walkthrough属性")

            print(f"   ✅ 成功提取数据")

        except Exception as e:
            print(f"   ❌ 提取过程中出错: {e}")
            import traceback
            traceback.print_exc()
            raise e

        finally:
            if env is not None:
                try:
                    env.close()
                except:
                    pass
    
    def _generate_catalog_report(self) -> Dict[str, Any]:
        """生成数据目录报告"""
        
        report = {
            "summary": {
                "total_games_found": len(self.processed_files) + len(self.failed_files),
                "successfully_processed": len(self.processed_files),
                "failed_to_process": len(self.failed_files),
                "unique_type_codes": len(self.all_type_codes),
                "unique_entity_names": len(self.all_entity_names),
                "unique_object_names": len(self.all_object_names),
                "unique_verbs": len(self.all_verbs),
                "unique_directions": len(self.all_directions),
                "total_command_samples": len(self.all_commands),
                "total_objectives": len(self.all_objectives),
                "total_walkthroughs": len(self.all_walkthroughs)
            },
            "data_catalogs": {
                "type_codes": sorted(list(self.all_type_codes)),
                "entity_names": sorted(list(self.all_entity_names)),
                "object_names": sorted(list(self.all_object_names)),
                "verbs": sorted(list(self.all_verbs)),
                "directions": sorted(list(self.all_directions)),
                "command_samples": sorted(list(self.all_commands))[:50],  # 前50个命令样本
                "objectives_sample": self.all_objectives[:5],  # 前5个目标样本
                "walkthrough_sample": self.all_walkthroughs[:3]  # 前3个通关样本
            },
            "statistics": {
                "type_code_frequency": dict(self.type_code_stats),
                "entity_name_frequency": dict(sorted(self.entity_name_stats.items(), key=lambda x: x[1], reverse=True)[:20]),
                "verb_frequency": dict(self.verb_stats),
                "direction_frequency": dict(self.direction_stats)
            },
            "processed_files": self.processed_files,
            "failed_files": self.failed_files
        }
        
        return report
    
    def save_catalogs_to_csv(self, report: Dict[str, Any], output_dir: str):
        """将数据目录保存为CSV文件"""
        
        output_path = project_root / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 类型编码目录
        type_codes_file = output_path / "textworld_type_codes.csv"
        with open(type_codes_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["type_code", "frequency", "description"])
            for type_code in sorted(report["data_catalogs"]["type_codes"]):
                freq = report["statistics"]["type_code_frequency"].get(type_code, 0)
                writer.writerow([type_code, freq, f"TextWorld类型编码: {type_code}"])
        
        # 2. 实体名称目录
        entity_names_file = output_path / "textworld_entity_names.csv"
        with open(entity_names_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["entity_name", "frequency"])
            for name, freq in report["statistics"]["entity_name_frequency"].items():
                writer.writerow([name, freq])
        
        # 3. 动词目录
        verbs_file = output_path / "textworld_verbs.csv"
        with open(verbs_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["verb", "frequency"])
            for verb in sorted(report["data_catalogs"]["verbs"]):
                freq = report["statistics"]["verb_frequency"].get(verb, 0)
                writer.writerow([verb, freq])
        
        # 4. 方向目录
        directions_file = output_path / "textworld_directions.csv"
        with open(directions_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["direction", "frequency"])
            for direction in sorted(report["data_catalogs"]["directions"]):
                freq = report["statistics"]["direction_frequency"].get(direction, 0)
                writer.writerow([direction, freq])
        
        # 5. 物品名称目录
        objects_file = output_path / "textworld_object_names.csv"
        with open(objects_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["object_name"])
            for obj_name in sorted(report["data_catalogs"]["object_names"]):
                writer.writerow([obj_name])
        
        print(f"\n💾 数据目录已保存到:")
        print(f"   - 类型编码: {type_codes_file}")
        print(f"   - 实体名称: {entity_names_file}")
        print(f"   - 动词列表: {verbs_file}")
        print(f"   - 方向列表: {directions_file}")
        print(f"   - 物品名称: {objects_file}")


def main():
    """主函数"""
    print("📊 TextWorld真实数据目录提取器")
    print("=" * 50)

    extractor = TextWorldDataCatalogExtractor()

    # 提取所有游戏的数据目录 - 处理所有文件
    report = extractor.extract_from_all_games(max_games=None)  # 处理所有文件
    
    # 保存完整报告
    report_file = project_root / "data/extraction/textworld_data_catalog.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 保存CSV目录
    extractor.save_catalogs_to_csv(report, "data/extraction/textworld_catalogs")
    
    # 打印摘要
    print(f"\n📋 数据提取摘要:")
    for key, value in report["summary"].items():
        print(f"   - {key}: {value}")
    
    print(f"\n🔍 发现的类型编码: {report['data_catalogs']['type_codes']}")
    print(f"🔍 发现的动词: {report['data_catalogs']['verbs']}")
    print(f"🔍 发现的方向: {report['data_catalogs']['directions']}")
    
    print(f"\n💾 完整报告已保存: {report_file}")


if __name__ == "__main__":
    main()
