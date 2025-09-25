#!/usr/bin/env python3
"""
知识图谱构建主脚本

统一构建和管理各种类型的知识图谱：
1. 下载benchmark数据
2. 预处理数据
3. 构建DODAF状态知识图谱
4. 构建规则知识图谱
5. 生成统一知识图谱
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.knowledge.unified_kg_manager import UnifiedKGManager
from src.knowledge.dodaf_kg_builder import create_example_kg
from src.knowledge.rule_kg_builder import create_example_rule_kg


class KGBuildPipeline:
    """知识图谱构建流水线"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.benchmarks_dir = self.data_dir / "benchmarks"
        self.kg_dir = self.data_dir / "knowledge_graphs"
        
        # 确保目录存在
        self.benchmarks_dir.mkdir(parents=True, exist_ok=True)
        self.kg_dir.mkdir(parents=True, exist_ok=True)
    
    def download_benchmarks(self, datasets: List[str] = None) -> None:
        """下载benchmark数据集"""
        if datasets is None:
            datasets = ["alfworld", "textworld"]
        
        scripts_dir = self.benchmarks_dir / "scripts"
        
        for dataset in datasets:
            script_name = f"download_{dataset}.sh"
            script_path = scripts_dir / script_name
            
            if script_path.exists():
                print(f"🚀 下载 {dataset} 数据集...")
                try:
                    # 使脚本可执行
                    os.chmod(script_path, 0o755)
                    
                    # 执行下载脚本
                    result = subprocess.run(
                        [str(script_path)],
                        cwd=str(scripts_dir),
                        capture_output=True,
                        text=True,
                        timeout=3600  # 1小时超时
                    )
                    
                    if result.returncode == 0:
                        print(f"✅ {dataset} 数据集下载成功")
                    else:
                        print(f"❌ {dataset} 数据集下载失败:")
                        print(result.stderr)
                        
                except subprocess.TimeoutExpired:
                    print(f"⏰ {dataset} 数据集下载超时")
                except Exception as e:
                    print(f"⚠️  下载 {dataset} 时出错: {e}")
            else:
                print(f"⚠️  未找到 {dataset} 下载脚本: {script_path}")
    
    def preprocess_data(self, datasets: List[str] = None) -> None:
        """预处理数据"""
        if datasets is None:
            datasets = ["alfworld", "textworld"]
        
        scripts_dir = self.benchmarks_dir / "scripts"
        
        for dataset in datasets:
            script_name = f"preprocess_{dataset}.py"
            script_path = scripts_dir / script_name
            
            if script_path.exists():
                print(f"🔄 预处理 {dataset} 数据...")
                try:
                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        cwd=str(self.project_root),
                        capture_output=True,
                        text=True,
                        timeout=1800  # 30分钟超时
                    )
                    
                    if result.returncode == 0:
                        print(f"✅ {dataset} 数据预处理成功")
                        if result.stdout:
                            print(result.stdout)
                    else:
                        print(f"❌ {dataset} 数据预处理失败:")
                        print(result.stderr)
                        
                except subprocess.TimeoutExpired:
                    print(f"⏰ {dataset} 数据预处理超时")
                except Exception as e:
                    print(f"⚠️  预处理 {dataset} 时出错: {e}")
            else:
                print(f"⚠️  未找到 {dataset} 预处理脚本: {script_path}")
    
    def build_dodaf_kgs(self) -> List[str]:
        """构建DODAF状态知识图谱"""
        print("🏗️  构建DODAF状态知识图谱...")
        
        kg_ids = []
        
        # 创建示例DODAF知识图谱
        example_kg = create_example_kg()
        
        # 保存示例图谱
        dodaf_dir = self.kg_dir / "dodaf"
        dodaf_dir.mkdir(exist_ok=True)
        
        example_kg.export_to_json(str(dodaf_dir / "example_dodaf_kg.json"))
        example_kg.export_to_graphml(str(dodaf_dir / "example_dodaf_kg.graphml"))
        
        kg_ids.append("example_dodaf")
        
        # 从预处理的数据构建更多图谱
        for dataset in ["alfworld", "textworld"]:
            dataset_kg_dir = self.kg_dir / dataset
            if dataset_kg_dir.exists():
                kg_files = list(dataset_kg_dir.glob("*_kg_*.json"))
                print(f"📊 找到 {len(kg_files)} 个 {dataset} 知识图谱文件")
                kg_ids.extend([f.stem for f in kg_files])
        
        print(f"✅ 构建了 {len(kg_ids)} 个DODAF知识图谱")
        return kg_ids
    
    def build_rule_kgs(self) -> List[str]:
        """构建规则知识图谱"""
        print("📋 构建规则知识图谱...")
        
        kg_ids = []
        
        # 创建示例规则知识图谱
        example_rule_kg = create_example_rule_kg()
        
        # 保存示例规则图谱
        rules_dir = self.kg_dir / "rules"
        rules_dir.mkdir(exist_ok=True)
        
        example_rule_kg.export_rules_to_json(str(rules_dir / "example_rules_kg.json"))
        example_rule_kg.export_to_graphml(str(rules_dir / "example_rules_kg.graphml"))
        
        kg_ids.append("example_rules")
        
        # 构建游戏特定的规则图谱
        game_rules = {
            "textworld_rules": {
                "basic_actions": {
                    "take": {"preconditions": ["物品可见", "物品可拿取"]},
                    "drop": {"preconditions": ["物品在背包中"]},
                    "open": {"preconditions": ["容器可开启", "容器未打开"]},
                    "go": {"preconditions": ["方向可通行"]}
                },
                "constraints": {
                    "负重限制": {
                        "conditions": ["背包重量 > 最大负重"],
                        "violations": ["无法拿取更多物品"]
                    },
                    "空间限制": {
                        "conditions": ["背包空间已满"],
                        "violations": ["无法放入更多物品"]
                    }
                },
                "inference_rules": {
                    "位置推理": {
                        "premises": ["玩家在房间A", "物品在房间A"],
                        "conclusions": ["玩家可以看到物品"]
                    }
                }
            }
        }
        
        for rule_set_name, rules in game_rules.items():
            rule_kg = create_example_rule_kg()
            rule_kg.build_game_rules_kg(rules)
            
            rule_file = rules_dir / f"{rule_set_name}.json"
            rule_kg.export_rules_to_json(str(rule_file))
            kg_ids.append(rule_set_name)
        
        print(f"✅ 构建了 {len(kg_ids)} 个规则知识图谱")
        return kg_ids
    
    def build_unified_kg(self, dodaf_kg_ids: List[str], 
                        rule_kg_ids: List[str]) -> None:
        """构建统一知识图谱"""
        print("🔗 构建统一知识图谱...")
        
        manager = UnifiedKGManager()
        
        # 创建示例统一图谱
        example_manager = create_example_unified_kg()
        
        # 导出统一图谱
        unified_dir = self.kg_dir / "unified"
        unified_dir.mkdir(exist_ok=True)
        
        example_manager.export_all_kgs(str(unified_dir))
        
        # 生成统计报告
        self._generate_unified_report(unified_dir, dodaf_kg_ids, rule_kg_ids)
        
        print("✅ 统一知识图谱构建完成")
    
    def _generate_unified_report(self, output_dir: Path, 
                               dodaf_kg_ids: List[str],
                               rule_kg_ids: List[str]) -> None:
        """生成统一报告"""
        report = {
            "build_timestamp": str(Path(__file__).stat().st_mtime),
            "dodaf_kgs": {
                "count": len(dodaf_kg_ids),
                "ids": dodaf_kg_ids
            },
            "rule_kgs": {
                "count": len(rule_kg_ids),
                "ids": rule_kg_ids
            },
            "total_kgs": len(dodaf_kg_ids) + len(rule_kg_ids),
            "output_directories": {
                "dodaf": str(self.kg_dir / "dodaf"),
                "rules": str(self.kg_dir / "rules"),
                "unified": str(output_dir)
            }
        }
        
        report_file = output_dir / "build_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 构建报告已保存到: {report_file}")
    
    def run_full_pipeline(self, download: bool = True, 
                         preprocess: bool = True,
                         datasets: List[str] = None) -> None:
        """运行完整的构建流水线"""
        print("🚀 开始知识图谱构建流水线...")
        
        if datasets is None:
            datasets = ["alfworld", "textworld"]
        
        try:
            # 1. 下载数据
            if download:
                self.download_benchmarks(datasets)
            
            # 2. 预处理数据
            if preprocess:
                self.preprocess_data(datasets)
            
            # 3. 构建DODAF知识图谱
            dodaf_kg_ids = self.build_dodaf_kgs()
            
            # 4. 构建规则知识图谱
            rule_kg_ids = self.build_rule_kgs()
            
            # 5. 构建统一知识图谱
            self.build_unified_kg(dodaf_kg_ids, rule_kg_ids)
            
            print("🎉 知识图谱构建流水线完成！")
            
        except Exception as e:
            print(f"❌ 构建流水线出错: {e}")
            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="知识图谱构建工具")
    parser.add_argument("--no-download", action="store_true", 
                       help="跳过数据下载")
    parser.add_argument("--no-preprocess", action="store_true",
                       help="跳过数据预处理")
    parser.add_argument("--datasets", nargs="+", 
                       default=["alfworld", "textworld"],
                       help="要处理的数据集")
    
    args = parser.parse_args()
    
    # 创建构建流水线
    pipeline = KGBuildPipeline()
    
    # 运行流水线
    pipeline.run_full_pipeline(
        download=not args.no_download,
        preprocess=not args.no_preprocess,
        datasets=args.datasets
    )


if __name__ == "__main__":
    main()
