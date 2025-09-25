#!/usr/bin/env python3
"""
文档生成工具 - 自动生成项目文档
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def extract_docstrings(file_path: Path) -> Dict[str, Any]:
    """提取Python文件的文档字符串"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        info = {
            "file": str(file_path),
            "module_docstring": ast.get_docstring(tree),
            "classes": [],
            "functions": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": []
                }
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "docstring": ast.get_docstring(item),
                            "args": [arg.arg for arg in item.args.args]
                        }
                        class_info["methods"].append(method_info)
                
                info["classes"].append(class_info)
            
            elif isinstance(node, ast.FunctionDef) and not any(
                isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
                if hasattr(parent, 'body') and node in getattr(parent, 'body', [])
            ):
                function_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "args": [arg.arg for arg in node.args.args]
                }
                info["functions"].append(function_info)
        
        return info
    
    except Exception as e:
        print(f"  ⚠️ 无法解析 {file_path}: {e}")
        return None

def generate_api_docs():
    """生成API文档"""
    print("📚 生成API文档...")
    
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print("  ❌ src目录不存在")
        return
    
    # 收集所有Python文件
    python_files = list(src_dir.rglob("*.py"))
    python_files = [f for f in python_files if not f.name.startswith('__')]
    
    api_docs = {
        "generated_at": datetime.now().isoformat(),
        "project": "KGRL",
        "modules": []
    }
    
    for py_file in python_files:
        print(f"  📄 处理: {py_file.relative_to(project_root)}")
        doc_info = extract_docstrings(py_file)
        if doc_info:
            api_docs["modules"].append(doc_info)
    
    # 保存API文档
    docs_dir = project_root / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    api_file = docs_dir / "api_reference.json"
    with open(api_file, 'w', encoding='utf-8') as f:
        json.dump(api_docs, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ API文档: {api_file}")
    
    # 生成Markdown版本
    md_file = docs_dir / "api_reference.md"
    generate_markdown_api_docs(api_docs, md_file)
    
    return api_docs

def generate_markdown_api_docs(api_docs: Dict[str, Any], output_file: Path):
    """生成Markdown格式的API文档"""
    print(f"  📝 生成Markdown: {output_file.name}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# KGRL API Reference\n\n")
        f.write(f"Generated at: {api_docs['generated_at']}\n\n")
        
        for module in api_docs["modules"]:
            file_path = Path(module["file"])
            module_name = file_path.stem
            
            f.write(f"## Module: {module_name}\n\n")
            f.write(f"**File:** `{file_path}`\n\n")
            
            if module["module_docstring"]:
                f.write(f"{module['module_docstring']}\n\n")
            
            # 类文档
            if module["classes"]:
                f.write("### Classes\n\n")
                for cls in module["classes"]:
                    f.write(f"#### {cls['name']}\n\n")
                    if cls["docstring"]:
                        f.write(f"{cls['docstring']}\n\n")
                    
                    if cls["methods"]:
                        f.write("**Methods:**\n\n")
                        for method in cls["methods"]:
                            args_str = ", ".join(method["args"])
                            f.write(f"- `{method['name']}({args_str})`")
                            if method["docstring"]:
                                f.write(f": {method['docstring']}")
                            f.write("\n")
                        f.write("\n")
            
            # 函数文档
            if module["functions"]:
                f.write("### Functions\n\n")
                for func in module["functions"]:
                    args_str = ", ".join(func["args"])
                    f.write(f"#### {func['name']}({args_str})\n\n")
                    if func["docstring"]:
                        f.write(f"{func['docstring']}\n\n")
            
            f.write("---\n\n")

def generate_experiment_docs():
    """生成实验文档"""
    print("\n🧪 生成实验文档...")
    
    project_root = Path(__file__).parent.parent.parent
    experiments_dir = project_root / "experiments"
    
    if not experiments_dir.exists():
        print("  ❌ experiments目录不存在")
        return
    
    docs_dir = project_root / "docs" / "experiments"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成实验概览
    experiment_overview = {
        "generated_at": datetime.now().isoformat(),
        "experiments": []
    }
    
    # 扫描实验脚本
    experiment_files = list(experiments_dir.rglob("*.py"))
    experiment_files = [f for f in experiment_files if "experiment" in f.name.lower()]
    
    for exp_file in experiment_files:
        print(f"  📊 处理实验: {exp_file.relative_to(project_root)}")
        
        exp_info = extract_docstrings(exp_file)
        if exp_info:
            experiment_overview["experiments"].append({
                "name": exp_file.stem,
                "file": str(exp_file.relative_to(project_root)),
                "description": exp_info.get("module_docstring", ""),
                "classes": len(exp_info.get("classes", [])),
                "functions": len(exp_info.get("functions", []))
            })
    
    # 保存实验文档
    exp_doc_file = docs_dir / "experiments_overview.json"
    with open(exp_doc_file, 'w', encoding='utf-8') as f:
        json.dump(experiment_overview, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 实验文档: {exp_doc_file}")
    
    return experiment_overview

def generate_config_docs():
    """生成配置文档"""
    print("\n⚙️ 生成配置文档...")
    
    project_root = Path(__file__).parent.parent.parent
    configs_dir = project_root / "configs"
    
    if not configs_dir.exists():
        print("  ❌ configs目录不存在")
        return
    
    docs_dir = project_root / "docs" / "configuration"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # 扫描配置文件
    config_files = list(configs_dir.rglob("*.yaml")) + list(configs_dir.rglob("*.json"))
    
    config_docs = {
        "generated_at": datetime.now().isoformat(),
        "configurations": []
    }
    
    for config_file in config_files:
        print(f"  ⚙️ 处理配置: {config_file.relative_to(project_root)}")
        
        try:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            else:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            
            config_info = {
                "name": config_file.stem,
                "file": str(config_file.relative_to(project_root)),
                "type": config_file.suffix,
                "keys": list(config_data.keys()) if isinstance(config_data, dict) else [],
                "structure": get_config_structure(config_data)
            }
            
            config_docs["configurations"].append(config_info)
        
        except Exception as e:
            print(f"    ⚠️ 无法解析配置文件: {e}")
    
    # 保存配置文档
    config_doc_file = docs_dir / "configuration_reference.json"
    with open(config_doc_file, 'w', encoding='utf-8') as f:
        json.dump(config_docs, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 配置文档: {config_doc_file}")
    
    return config_docs

def get_config_structure(data: Any, max_depth: int = 3, current_depth: int = 0) -> Any:
    """获取配置结构（限制深度避免过大）"""
    if current_depth >= max_depth:
        return "..."
    
    if isinstance(data, dict):
        return {k: get_config_structure(v, max_depth, current_depth + 1) 
                for k, v in list(data.items())[:10]}  # 限制键数量
    elif isinstance(data, list):
        if len(data) > 0:
            return [get_config_structure(data[0], max_depth, current_depth + 1)]
        return []
    else:
        return type(data).__name__

def generate_readme():
    """生成项目README"""
    print("\n📖 生成项目README...")
    
    project_root = Path(__file__).parent.parent.parent
    readme_file = project_root / "README_generated.md"
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("# KGRL - Knowledge Graph Reinforcement Learning\n\n")
        f.write(f"*Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        f.write("## Project Structure\n\n")
        f.write("```\n")
        f.write("KGRL/\n")
        
        # 生成目录结构
        for root, dirs, files in os.walk(project_root):
            # 跳过隐藏目录和常见的忽略目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            level = root.replace(str(project_root), '').count(os.sep)
            if level > 3:  # 限制深度
                continue
            
            indent = '│   ' * level
            f.write(f"{indent}├── {os.path.basename(root)}/\n")
            
            # 显示重要文件
            important_files = [f for f in files if f.endswith(('.py', '.yaml', '.json', '.md')) 
                             and not f.startswith('.')][:5]  # 限制文件数量
            
            for file in important_files:
                f.write(f"{indent}│   ├── {file}\n")
        
        f.write("```\n\n")
        
        f.write("## Quick Start\n\n")
        f.write("1. **Environment Setup**\n")
        f.write("   ```bash\n")
        f.write("   bash scripts/setup/install_dependencies.sh\n")
        f.write("   bash scripts/setup/setup_environment.sh\n")
        f.write("   ```\n\n")
        
        f.write("2. **Health Check**\n")
        f.write("   ```bash\n")
        f.write("   python scripts/maintenance/check_health.py\n")
        f.write("   ```\n\n")
        
        f.write("3. **Run Experiments**\n")
        f.write("   ```bash\n")
        f.write("   python scripts/run_baseline_comparison.py\n")
        f.write("   ```\n\n")
        
        f.write("## Documentation\n\n")
        f.write("- [API Reference](docs/api/api_reference.md)\n")
        f.write("- [Experiments Guide](docs/experiments/)\n")
        f.write("- [Configuration Reference](docs/configuration/)\n\n")
        
        f.write("## Maintenance\n\n")
        f.write("- Clean cache: `python scripts/maintenance/clean_cache.py`\n")
        f.write("- Backup results: `python scripts/maintenance/backup_results.py`\n")
        f.write("- Health check: `python scripts/maintenance/check_health.py`\n\n")
    
    print(f"  ✅ README: {readme_file}")
    return readme_file

def main():
    """主文档生成函数"""
    print("📚 KGRL文档生成工具")
    print("=" * 30)
    
    try:
        # 生成各类文档
        api_docs = generate_api_docs()
        experiment_docs = generate_experiment_docs()
        config_docs = generate_config_docs()
        readme_file = generate_readme()
        
        print("\n" + "=" * 30)
        print("🎉 文档生成完成!")
        print(f"📊 统计:")
        if api_docs:
            print(f"  - API模块: {len(api_docs['modules'])} 个")
        if experiment_docs:
            print(f"  - 实验脚本: {len(experiment_docs['experiments'])} 个")
        if config_docs:
            print(f"  - 配置文件: {len(config_docs['configurations'])} 个")
        print(f"  - README: {readme_file.name}")
    
    except Exception as e:
        print(f"❌ 文档生成失败: {e}")

if __name__ == "__main__":
    main()
