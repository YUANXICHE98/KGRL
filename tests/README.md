# KGRL 测试框架

本目录包含KGRL项目的所有测试代码，按测试类型分类组织。

## 📁 测试结构

```
tests/
├── README.md                    # 测试说明文档
├── unit/                        # 单元测试
│   ├── __init__.py
│   ├── test_agents.py          # Agent单元测试
│   ├── test_knowledge.py       # 知识图谱单元测试
│   ├── test_memory_agent.py    # 记忆Agent测试
│   ├── test_react_agent.py     # ReAct Agent测试
│   ├── test_memory_retrieval.py # 记忆检索测试
│   └── test_short_term_memory.py # 短期记忆测试
├── integration/                 # 集成测试
│   ├── __init__.py
│   ├── test_agent_kg.py        # Agent-KG集成测试
│   ├── test_memory_integration.py # 记忆集成测试
│   └── test_full_pipeline.py   # 完整pipeline测试
└── system/                      # 系统测试
    ├── __init__.py
    ├── test_framework.py        # 框架系统测试
    └── test_performance.py      # 性能测试
```

## 🧪 测试类型说明

### 单元测试 (Unit Tests)
测试单个组件的功能，确保每个模块独立工作正常。

- **test_agents.py**: 测试各种Agent的基本功能
- **test_knowledge.py**: 测试知识图谱的构建和查询
- **test_memory_*.py**: 测试记忆系统的各个组件

### 集成测试 (Integration Tests)
测试多个组件之间的协作，确保接口和数据流正确。

- **test_agent_kg.py**: 测试Agent与知识图谱的集成
- **test_memory_integration.py**: 测试记忆系统的集成
- **test_full_pipeline.py**: 测试完整的数据流程

### 系统测试 (System Tests)
测试整个系统的功能，确保端到端的工作流程。

- **test_framework.py**: 测试框架的整体功能
- **test_performance.py**: 测试系统性能和稳定性

## 🚀 运行测试

### 安装测试依赖
```bash
pip install pytest pytest-cov pytest-mock
```

### 运行所有测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

### 运行特定类型的测试
```bash
# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/

# 运行系统测试
python -m pytest tests/system/
```

### 运行特定测试文件
```bash
# 运行Agent测试
python -m pytest tests/unit/test_agents.py

# 运行知识图谱测试
python -m pytest tests/unit/test_knowledge.py

# 运行特定测试方法
python -m pytest tests/unit/test_agents.py::TestBaselineAgent::test_act
```

## 📊 测试覆盖率

### 目标覆盖率
- **核心组件**: >90%
- **工具函数**: >80%
- **实验代码**: >60%

### 查看覆盖率报告
```bash
# 生成HTML覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 🔧 测试配置

### pytest配置
在项目根目录创建 `pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### 测试环境变量
```bash
# 设置测试环境
export TESTING=true
export OPENAI_API_KEY="test-key"
```

## 📝 编写测试

### 测试基类
```python
import unittest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class BaseTestCase(unittest.TestCase):
    """测试基类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        pass
    
    def setUp(self):
        """测试设置"""
        pass
    
    def tearDown(self):
        """测试清理"""
        pass
```

### 测试命名规范
- 测试文件：`test_<component>.py`
- 测试类：`Test<ComponentName>`
- 测试方法：`test_<function_name>`

### 测试示例
```python
class TestBaselineAgent(BaseTestCase):
    """BaselineAgent测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.agent_config = {
            "model_name": "gpt-4o",
            "temperature": 0.7
        }
        self.agent = BaselineAgent("test_agent", self.agent_config)
    
    def test_act_with_valid_input(self):
        """测试正常输入的动作选择"""
        observation = "You are in a room."
        actions = ["look", "go north", "take key"]
        
        result = self.agent.act(observation, actions)
        
        self.assertIn(result, actions)
        self.assertIsInstance(result, str)
    
    def test_act_with_empty_actions(self):
        """测试空动作列表的处理"""
        observation = "You are in a room."
        actions = []
        
        result = self.agent.act(observation, actions)
        
        self.assertEqual(result, "look")  # 默认动作
```

## 🐛 调试测试

### 运行单个测试并显示详细输出
```bash
python -m pytest tests/unit/test_agents.py::TestBaselineAgent::test_act -v -s
```

### 使用调试器
```python
import pdb; pdb.set_trace()  # 在测试中添加断点
```

### 查看测试日志
```bash
python -m pytest tests/ --log-cli-level=DEBUG
```

## 📈 持续集成

### GitHub Actions配置
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: pytest tests/ --cov=src
```

## 🎯 测试最佳实践

1. **独立性**: 每个测试应该独立运行
2. **可重复性**: 测试结果应该一致
3. **快速性**: 单元测试应该快速执行
4. **清晰性**: 测试名称应该清楚表达测试内容
5. **覆盖性**: 重要功能应该有充分的测试覆盖

## 🔄 测试维护

- 定期运行测试确保代码质量
- 新功能开发时同步编写测试
- 重构代码时更新相关测试
- 监控测试覆盖率变化

这个测试框架为KGRL项目提供了完整的质量保证体系。
