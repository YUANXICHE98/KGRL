#!/usr/bin/env python3
"""
KGRL测试运行器

按类别运行不同的测试套件：
- Agent测试：各种Agent类型的功能测试
- 实验测试：消融实验和对比实验测试
- 单元测试：基础组件测试
- 集成测试：系统集成测试
"""

import sys
import subprocess
import argparse
from pathlib import Path

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    print("⚠️  pytest未安装，将使用简化的测试运行器")

def run_agent_tests():
    """运行Agent测试"""
    print("🤖 运行Agent测试...")
    test_files = [
        "tests/agents/test_baseline_agent.py",
        "tests/agents/test_react_agent.py", 
        "tests/agents/test_unified_agent.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"运行 {test_file}")
            pytest.main([test_file, "-v"])
        else:
            print(f"⚠️  测试文件不存在: {test_file}")

def run_experiment_tests():
    """运行实验测试"""
    print("🔬 运行实验测试...")
    test_files = [
        "tests/experiments/test_ablation_study.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"运行 {test_file}")
            pytest.main([test_file, "-v"])
        else:
            print(f"⚠️  测试文件不存在: {test_file}")

def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    if Path("tests/unit").exists():
        pytest.main(["tests/unit/", "-v"])
    else:
        print("⚠️  单元测试目录不存在")

def run_integration_tests():
    """运行集成测试"""
    print("🔗 运行集成测试...")
    if Path("tests/integration").exists():
        pytest.main(["tests/integration/", "-v"])
    else:
        print("⚠️  集成测试目录不存在")

def run_system_tests():
    """运行系统测试"""
    print("🖥️  运行系统测试...")
    if Path("tests/system").exists():
        pytest.main(["tests/system/", "-v"])
    else:
        print("⚠️  系统测试目录不存在")

def run_framework_tests():
    """运行框架测试"""
    print("🏗️  运行框架测试...")
    framework_test = "framework/test_system.py"
    if Path(framework_test).exists():
        print(f"运行 {framework_test}")
        if HAS_PYTEST:
            pytest.main([framework_test, "-v"])
        else:
            # 直接运行Python文件
            subprocess.run([sys.executable, framework_test])
    else:
        print(f"⚠️  框架测试文件不存在: {framework_test}")

def run_all_tests():
    """运行所有测试"""
    print("🚀 运行所有测试...")
    run_framework_tests()
    run_agent_tests()
    run_experiment_tests()
    run_unit_tests()
    run_integration_tests()
    run_system_tests()

def main():
    parser = argparse.ArgumentParser(description="KGRL测试运行器")
    parser.add_argument(
        "test_type", 
        choices=["all", "agents", "experiments", "unit", "integration", "system", "framework"],
        help="要运行的测试类型"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    print(f"KGRL测试运行器 - 运行 {args.test_type} 测试")
    print("=" * 50)
    
    if args.test_type == "all":
        run_all_tests()
    elif args.test_type == "agents":
        run_agent_tests()
    elif args.test_type == "experiments":
        run_experiment_tests()
    elif args.test_type == "unit":
        run_unit_tests()
    elif args.test_type == "integration":
        run_integration_tests()
    elif args.test_type == "system":
        run_system_tests()
    elif args.test_type == "framework":
        run_framework_tests()
    
    print("=" * 50)
    print("✅ 测试完成!")

if __name__ == "__main__":
    main()
