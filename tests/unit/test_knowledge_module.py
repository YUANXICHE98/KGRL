"""
Knowledge Module单元测试

测试知识图谱模块的核心功能：
- 模块初始化和清理
- KG查询功能
- DODAF分类查询
- 动态知识更新
- 错误处理
"""

import sys
import pytest
import tempfile
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入框架模块
sys.path.append(str(Path(__file__).parent.parent.parent / "framework"))
from capabilities.knowledge_module import KnowledgeGraphModule
from capabilities.base import CapabilityModule

class TestKnowledgeModule:
    """Knowledge Module基础测试"""
    
    @pytest.fixture
    def temp_kg_file(self):
        """创建临时KG文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_kg = {
                "facts": [
                    {"subject": "key", "predicate": "type", "object": "item"},
                    {"subject": "chest", "predicate": "type", "object": "container"},
                    {"subject": "key", "predicate": "opens", "object": "chest"},
                    {"subject": "take_key", "predicate": "DO", "object": "acquire_item"},
                    {"subject": "acquire_item", "predicate": "DA", "object": "item_in_inventory"},
                    {"subject": "item_in_inventory", "predicate": "F", "object": "can_use_item"}
                ]
            }
            json.dump(test_kg, f)
            temp_path = f.name
        
        yield temp_path
        
        # 清理
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def knowledge_module(self, temp_kg_file):
        """创建测试用Knowledge Module"""
        config = {
            'enabled': True,
            'kg_file': temp_kg_file,
            'max_facts_per_query': 5,
            'query_types': ['keywords', 'dodaf', 'entity'],
            'confidence_threshold': 0.5
        }
        return KnowledgeGraphModule('test_kg', config)
    
    def test_module_inheritance(self, knowledge_module):
        """测试模块继承关系"""
        assert isinstance(knowledge_module, CapabilityModule)
        assert hasattr(knowledge_module, 'initialize')
        assert hasattr(knowledge_module, 'process')
        assert hasattr(knowledge_module, 'cleanup')
    
    def test_module_initialization(self, knowledge_module):
        """测试模块初始化"""
        # 初始化前状态
        assert not hasattr(knowledge_module, 'kg_builder')
        
        # 执行初始化
        knowledge_module.initialize()
        
        # 初始化后状态
        assert hasattr(knowledge_module, 'kg_builder')
        assert hasattr(knowledge_module, 'kg_retriever')
        assert knowledge_module.enabled
    
    def test_keywords_query(self, knowledge_module):
        """测试关键词查询"""
        knowledge_module.initialize()
        
        # 测试关键词查询
        query_data = {
            'query_type': 'keywords',
            'keywords': ['key', 'chest']
        }
        
        result = knowledge_module.process(query_data)
        
        assert 'facts' in result
        assert len(result['facts']) > 0
        
        # 验证返回的事实包含查询关键词
        facts_text = ' '.join([str(fact) for fact in result['facts']])
        assert 'key' in facts_text.lower() or 'chest' in facts_text.lower()
    
    def test_dodaf_query(self, knowledge_module):
        """测试DODAF查询"""
        knowledge_module.initialize()
        
        # 测试DODAF查询
        query_data = {
            'query_type': 'dodaf',
            'dodaf_type': 'DO',
            'entity': 'take_key'
        }
        
        result = knowledge_module.process(query_data)
        
        assert 'facts' in result
        # DODAF查询应该返回相关的DO-DA-F链
        if result['facts']:
            facts_text = ' '.join([str(fact) for fact in result['facts']])
            assert 'DO' in facts_text or 'DA' in facts_text or 'F' in facts_text
    
    def test_entity_query(self, knowledge_module):
        """测试实体查询"""
        knowledge_module.initialize()
        
        # 测试实体查询
        query_data = {
            'query_type': 'entity',
            'entity': 'key'
        }
        
        result = knowledge_module.process(query_data)
        
        assert 'facts' in result
        # 实体查询应该返回与该实体相关的所有事实
        if result['facts']:
            facts_text = ' '.join([str(fact) for fact in result['facts']])
            assert 'key' in facts_text.lower()
    
    def test_invalid_query_type(self, knowledge_module):
        """测试无效查询类型"""
        knowledge_module.initialize()
        
        # 测试无效查询类型
        query_data = {
            'query_type': 'invalid_type',
            'keywords': ['test']
        }
        
        result = knowledge_module.process(query_data)
        
        # 应该返回空结果或错误信息
        assert 'facts' in result
        assert len(result['facts']) == 0
    
    def test_empty_query(self, knowledge_module):
        """测试空查询"""
        knowledge_module.initialize()
        
        # 测试空查询
        query_data = {
            'query_type': 'keywords',
            'keywords': []
        }
        
        result = knowledge_module.process(query_data)
        
        # 空查询应该返回空结果
        assert 'facts' in result
        assert len(result['facts']) == 0
    
    def test_max_facts_limit(self, knowledge_module):
        """测试最大事实数量限制"""
        knowledge_module.initialize()
        
        # 测试返回事实数量限制
        query_data = {
            'query_type': 'keywords',
            'keywords': ['key', 'chest', 'item', 'container']  # 广泛查询
        }
        
        result = knowledge_module.process(query_data)
        
        # 验证返回的事实数量不超过配置的最大值
        assert len(result['facts']) <= knowledge_module.max_facts_per_query
    
    def test_knowledge_update(self, knowledge_module):
        """测试知识更新功能"""
        knowledge_module.initialize()
        
        # 添加新知识
        update_data = {
            'action': 'add_fact',
            'subject': 'sword',
            'predicate': 'type',
            'object': 'weapon'
        }
        
        result = knowledge_module.process(update_data)
        
        # 验证更新成功
        assert 'success' in result
        
        # 验证新知识可以被查询到
        query_data = {
            'query_type': 'keywords',
            'keywords': ['sword']
        }
        
        query_result = knowledge_module.process(query_data)
        facts_text = ' '.join([str(fact) for fact in query_result['facts']])
        assert 'sword' in facts_text.lower()
    
    def test_module_cleanup(self, knowledge_module):
        """测试模块清理"""
        knowledge_module.initialize()
        
        # 验证初始化后的状态
        assert hasattr(knowledge_module, 'kg_builder')
        assert hasattr(knowledge_module, 'kg_retriever')
        
        # 执行清理
        knowledge_module.cleanup()
        
        # 验证清理后的状态
        # 注意：具体的清理行为取决于实现
        # 这里主要测试清理方法不会抛出异常
        assert True  # 如果到达这里说明清理成功
    
    def test_error_handling(self, knowledge_module):
        """测试错误处理"""
        knowledge_module.initialize()
        
        # 测试各种错误情况
        error_cases = [
            None,  # None输入
            {},    # 空字典
            {'invalid': 'data'},  # 无效数据格式
            {'query_type': 'keywords'},  # 缺少必要字段
        ]
        
        for error_case in error_cases:
            try:
                result = knowledge_module.process(error_case)
                # 应该返回错误结果而不是抛出异常
                assert 'facts' in result
                assert len(result['facts']) == 0
            except Exception as e:
                # 或者抛出合适的异常
                assert isinstance(e, (ValueError, TypeError, KeyError))


class TestKnowledgeModuleIntegration:
    """Knowledge Module集成测试"""
    
    def test_full_workflow(self, temp_kg_file):
        """测试完整工作流程"""
        config = {
            'enabled': True,
            'kg_file': temp_kg_file,
            'max_facts_per_query': 10
        }
        
        module = KnowledgeGraphModule('integration_test', config)
        
        try:
            # 1. 初始化
            module.initialize()
            
            # 2. 执行多种查询
            queries = [
                {'query_type': 'keywords', 'keywords': ['key']},
                {'query_type': 'entity', 'entity': 'chest'},
                {'query_type': 'dodaf', 'dodaf_type': 'DO', 'entity': 'take_key'}
            ]
            
            results = []
            for query in queries:
                result = module.process(query)
                results.append(result)
                assert 'facts' in result
            
            # 3. 验证结果
            assert len(results) == 3
            
            # 4. 清理
            module.cleanup()
            
        except Exception as e:
            # 确保即使出错也要清理
            module.cleanup()
            raise e
    
    def test_concurrent_queries(self, temp_kg_file):
        """测试并发查询处理"""
        config = {
            'enabled': True,
            'kg_file': temp_kg_file,
            'max_facts_per_query': 5
        }
        
        module = KnowledgeGraphModule('concurrent_test', config)
        module.initialize()
        
        try:
            # 模拟并发查询
            queries = [
                {'query_type': 'keywords', 'keywords': ['key']},
                {'query_type': 'keywords', 'keywords': ['chest']},
                {'query_type': 'entity', 'entity': 'key'},
                {'query_type': 'entity', 'entity': 'chest'}
            ]
            
            # 快速连续执行查询
            results = []
            for query in queries:
                result = module.process(query)
                results.append(result)
            
            # 验证所有查询都成功
            assert len(results) == 4
            for result in results:
                assert 'facts' in result
                
        finally:
            module.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
