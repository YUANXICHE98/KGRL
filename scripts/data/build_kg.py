#!/usr/bin/env python3
"""
标准化知识图谱构建脚本
按照项目结构规范实现知识图谱构建功能

功能：
1. 构建DODAF状态知识图谱
2. 构建规则知识图谱  
3. 构建场景特定知识图谱
4. 导出到标准格式
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.knowledge.dodaf_kg_builder import DODAFKGBuilder, create_example_kg
from src.utils.config_loader import ConfigLoader
from src.utils.logging_utils import setup_logging

class StandardKGBuilder:
    """标准化知识图谱构建器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化构建器"""
        self.project_root = project_root
        self.data_dir = self.project_root / "data"
        self.kg_dir = self.data_dir / "kg"
        
        # 加载配置
        if config_path:
            self.config = ConfigLoader.load_config(config_path)
        else:
            self.config = self._load_default_config()
        
        # 设置日志
        self.logger = setup_logging("KGBuilder", level=logging.INFO)
        
        # 确保目录存在
        self._ensure_directories()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "kg_construction": {
                "max_scenes": 5,
                "output_formats": ["json", "graphml"],
                "enable_dodaf": True,
                "enable_rules": True,
                "enable_enhanced_scenes": True
            },
            "output": {
                "base_dir": "data/kg",
                "schemas_dir": "schemas",
                "triples_dir": "triples", 
                "snapshots_dir": "snapshots"
            }
        }
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs = [
            self.kg_dir / "schemas",
            self.kg_dir / "triples",
            self.kg_dir / "indexes", 
            self.kg_dir / "snapshots",
            self.kg_dir / "extracted",
            self.kg_dir / "enhanced_scenes"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def build_dodaf_kg(self, scene_name: Optional[str] = None) -> bool:
        """构建DODAF状态知识图谱"""
        self.logger.info("🏗️ 构建DODAF状态知识图谱...")
        
        try:
            if scene_name:
                # 构建特定场景的DODAF KG
                kg_builder = self._build_scene_dodaf_kg(scene_name)
                output_file = self.kg_dir / "snapshots" / f"{scene_name}_dodaf_kg"
            else:
                # 构建示例DODAF KG
                kg_builder = create_example_kg()
                output_file = self.kg_dir / "snapshots" / "example_dodaf_kg"
            
            # 导出到多种格式
            success = self._export_kg(kg_builder, output_file)
            
            if success:
                self.logger.info("✅ DODAF知识图谱构建成功")
                return True
            else:
                self.logger.error("❌ DODAF知识图谱构建失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ DODAF知识图谱构建出错: {e}")
            return False
    
    def build_enhanced_scene_kgs(self, max_scenes: int = 5) -> bool:
        """构建增强场景知识图谱"""
        self.logger.info(f"🏗️ 构建增强场景知识图谱 (最多 {max_scenes} 个场景)...")
        
        try:
            # 查找ALFWorld场景数据
            alfworld_dir = self.data_dir / "benchmarks/alfworld/alfworld/alfworld/gen/layouts"
            
            if not alfworld_dir.exists():
                self.logger.warning("⚠️ ALFWorld数据目录不存在，跳过场景KG构建")
                return False
            
            # 获取场景文件
            scene_files = list(alfworld_dir.glob("*-openable.json"))[:max_scenes]
            
            if not scene_files:
                self.logger.warning("⚠️ 未找到ALFWorld场景文件")
                return False
            
            self.logger.info(f"📁 找到 {len(scene_files)} 个场景文件")
            
            success_count = 0
            for scene_file in scene_files:
                scene_name = scene_file.stem
                if self._build_single_enhanced_scene_kg(scene_file, scene_name):
                    success_count += 1
            
            self.logger.info(f"✅ 成功构建 {success_count}/{len(scene_files)} 个增强场景KG")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ 增强场景KG构建出错: {e}")
            return False
    
    def _build_single_enhanced_scene_kg(self, scene_file: Path, scene_name: str) -> bool:
        """构建单个增强场景知识图谱"""
        try:
            self.logger.info(f"🔨 构建场景: {scene_name}")
            
            # 加载场景数据
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            
            # 使用现有的场景KG构建器
            from data.extraction.tools.scene_kg_builder import SceneKGBuilder
            
            builder = SceneKGBuilder()
            kg_data = builder.build_enhanced_scene_kg(scene_data, scene_name)
            
            if kg_data:
                # 保存到标准位置
                output_file = self.kg_dir / "enhanced_scenes" / f"{scene_name}_enhanced_kg.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(kg_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"   ✅ {scene_name}: {kg_data['metadata']['node_count']} 节点, {kg_data['metadata']['edge_count']} 边")
                return True
            else:
                self.logger.warning(f"   ⚠️ {scene_name}: 构建失败")
                return False
                
        except Exception as e:
            self.logger.error(f"   ❌ {scene_name}: 构建出错 - {e}")
            return False
    
    def _build_scene_dodaf_kg(self, scene_name: str) -> DODAFKGBuilder:
        """构建特定场景的DODAF知识图谱"""
        # 这里可以根据场景数据构建DODAF KG
        # 暂时返回示例KG
        return create_example_kg()
    
    def _export_kg(self, kg_builder: DODAFKGBuilder, output_file: Path) -> bool:
        """导出知识图谱到多种格式"""
        try:
            formats = self.config.get("kg_construction", {}).get("output_formats", ["json"])
            
            for fmt in formats:
                if fmt == "json":
                    kg_builder.export_to_json(f"{output_file}.json")
                elif fmt == "graphml":
                    kg_builder.export_to_graphml(f"{output_file}.graphml")
            
            return True
            
        except Exception as e:
            self.logger.error(f"导出KG失败: {e}")
            return False
    
    def build_all(self, max_scenes: int = 5) -> Dict[str, bool]:
        """构建所有类型的知识图谱"""
        self.logger.info("🚀 开始构建所有知识图谱...")
        
        results = {}
        
        # 1. 构建DODAF知识图谱
        results["dodaf"] = self.build_dodaf_kg()
        
        # 2. 构建增强场景知识图谱
        results["enhanced_scenes"] = self.build_enhanced_scene_kgs(max_scenes)
        
        # 生成构建报告
        self._generate_build_report(results)
        
        return results
    
    def _generate_build_report(self, results: Dict[str, bool]):
        """生成构建报告"""
        report = {
            "timestamp": str(Path().resolve()),
            "results": results,
            "kg_directory": str(self.kg_dir),
            "summary": {
                "total_tasks": len(results),
                "successful_tasks": sum(results.values()),
                "failed_tasks": len(results) - sum(results.values())
            }
        }
        
        report_file = self.kg_dir / "snapshots" / "build_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📊 构建报告已保存: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="标准化知识图谱构建脚本")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--max-scenes", type=int, default=5, help="最大场景数量")
    parser.add_argument("--type", choices=["dodaf", "scenes", "all"], default="all", help="构建类型")
    parser.add_argument("--scene", type=str, help="特定场景名称")
    
    args = parser.parse_args()
    
    # 创建构建器
    builder = StandardKGBuilder(args.config)
    
    print("🚀 标准化知识图谱构建器")
    print(f"📁 数据目录: {builder.kg_dir}")
    print(f"🎯 构建类型: {args.type}")
    
    # 根据类型执行构建
    if args.type == "dodaf":
        success = builder.build_dodaf_kg(args.scene)
    elif args.type == "scenes":
        success = builder.build_enhanced_scene_kgs(args.max_scenes)
    else:  # all
        results = builder.build_all(args.max_scenes)
        success = any(results.values())
    
    if success:
        print("🎉 知识图谱构建完成!")
        print(f"📂 输出目录: {builder.kg_dir}")
    else:
        print("❌ 知识图谱构建失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
