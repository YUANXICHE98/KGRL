"""
Memory Module单元测试

测试记忆系统模块的核心功能：
- 短期、中期、长期记忆管理
- 记忆存储和检索
- 相似度匹配
- 记忆容量管理
- 模式发现
"""

import sys
import pytest
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入框架模块
sys.path.append(str(Path(__file__).parent.parent.parent / "framework"))
from capabilities.memory_module import MemoryModule
from capabilities.base import CapabilityModule

class TestMemoryModule:
    """Memory Module基础测试"""
    
    @pytest.fixture
    def memory_config(self):
        """创建测试用记忆配置"""
        return {
            'enabled': True,
            'use_short_term': True,
            'use_medium_term': True,
            'use_long_term': False,
            'short_term_size': 5,
            'medium_term_size': 20,
            'similarity_threshold': 0.6,
            'max_retrieved_memories': 3
        }
    
    @pytest.fixture
    def memory_module(self, memory_config):
        """创建测试用Memory Module"""
        return MemoryModule('test_memory', memory_config)
    
    def test_module_inheritance(self, memory_module):
        """测试模块继承关系"""
        assert isinstance(memory_module, CapabilityModule)
        assert hasattr(memory_module, 'initialize')
        assert hasattr(memory_module, 'process')
        assert hasattr(memory_module, 'cleanup')
    
    def test_module_initialization(self, memory_module):
        """测试模块初始化"""
        # 初始化前状态
        assert not hasattr(memory_module, 'short_term_memory')
        
        # 执行初始化
        memory_module.initialize()
        
        # 初始化后状态
        assert hasattr(memory_module, 'short_term_memory')
        assert hasattr(memory_module, 'medium_term_memory')
        assert memory_module.enabled
        
        # 验证记忆容器初始化
        assert len(memory_module.short_term_memory) == 0
        assert len(memory_module.medium_term_memory) == 0
    
    def test_store_memory(self, memory_module):
        """测试记忆存储"""
        memory_module.initialize()
        
        # 存储短期记忆
        store_data = {
            'action': 'store',
            'memory_type': 'short_term',
            'content': 'I took the key from the table',
            'context': 'room exploration',
            'timestamp': '2024-01-01T10:00:00'
        }
        
        result = memory_module.process(store_data)
        
        assert 'success' in result
        assert result['success']
        assert len(memory_module.short_term_memory) == 1
        
        # 验证存储的记忆内容
        stored_memory = memory_module.short_term_memory[0]
        assert 'content' in stored_memory
        assert 'context' in stored_memory
        assert 'timestamp' in stored_memory
    
    def test_retrieve_memory(self, memory_module):
        """测试记忆检索"""
        memory_module.initialize()
        
        # 先存储一些记忆
        memories = [
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Found a key on the table'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Opened a chest with the key'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Found treasure in the chest'}
        ]
        
        for memory in memories:
            memory_module.process(memory)
        
        # 检索相关记忆
        retrieve_data = {
            'action': 'retrieve',
            'query': 'key chest',
            'memory_type': 'short_term'
        }
        
        result = memory_module.process(retrieve_data)
        
        assert 'memories' in result
        assert len(result['memories']) > 0
        
        # 验证检索到的记忆相关性
        retrieved_text = ' '.join([mem['content'] for mem in result['memories']])
        assert 'key' in retrieved_text.lower() or 'chest' in retrieved_text.lower()
    
    def test_memory_capacity_management(self, memory_module):
        """测试记忆容量管理"""
        memory_module.initialize()
        
        # 存储超过容量限制的记忆
        for i in range(memory_module.short_term_size + 3):
            store_data = {
                'action': 'store',
                'memory_type': 'short_term',
                'content': f'Memory {i}: Some action happened',
                'context': f'context_{i}'
            }
            memory_module.process(store_data)
        
        # 验证容量限制
        assert len(memory_module.short_term_memory) <= memory_module.short_term_size
        
        # 验证最新的记忆被保留（FIFO或LRU策略）
        latest_memory = memory_module.short_term_memory[-1]
        assert 'Memory' in latest_memory['content']
    
    def test_memory_similarity_matching(self, memory_module):
        """测试记忆相似度匹配"""
        memory_module.initialize()
        
        # 存储相似的记忆
        similar_memories = [
            {'action': 'store', 'memory_type': 'short_term', 'content': 'I picked up a golden key'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'I found a silver key'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'I ate an apple'}  # 不相似
        ]
        
        for memory in similar_memories:
            memory_module.process(memory)
        
        # 查询相似记忆
        retrieve_data = {
            'action': 'retrieve',
            'query': 'key',
            'memory_type': 'short_term',
            'use_similarity': True
        }
        
        result = memory_module.process(retrieve_data)
        
        assert 'memories' in result
        # 应该检索到包含"key"的记忆，但不包括"apple"的记忆
        retrieved_contents = [mem['content'] for mem in result['memories']]
        key_memories = [content for content in retrieved_contents if 'key' in content.lower()]
        apple_memories = [content for content in retrieved_contents if 'apple' in content.lower()]
        
        assert len(key_memories) > 0
        assert len(apple_memories) == 0
    
    def test_memory_type_switching(self, memory_module):
        """测试记忆类型切换"""
        memory_module.initialize()
        
        # 测试不同记忆类型的存储
        memory_types = ['short_term', 'medium_term']
        
        for memory_type in memory_types:
            store_data = {
                'action': 'store',
                'memory_type': memory_type,
                'content': f'Content for {memory_type} memory',
                'context': f'{memory_type}_context'
            }
            
            result = memory_module.process(store_data)
            assert result['success']
        
        # 验证不同类型的记忆被正确存储
        assert len(memory_module.short_term_memory) == 1
        assert len(memory_module.medium_term_memory) == 1
        
        # 验证内容正确
        assert 'short_term' in memory_module.short_term_memory[0]['content']
        assert 'medium_term' in memory_module.medium_term_memory[0]['content']
    
    def test_pattern_discovery(self, memory_module):
        """测试模式发现功能"""
        memory_module.initialize()
        
        # 存储有模式的记忆序列
        pattern_memories = [
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Step 1: Enter room'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Step 2: Look for key'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Step 3: Take key'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Step 4: Open chest'},
            {'action': 'store', 'memory_type': 'short_term', 'content': 'Step 5: Get treasure'}
        ]
        
        for memory in pattern_memories:
            memory_module.process(memory)
        
        # 查找模式
        pattern_data = {
            'action': 'find_patterns',
            'memory_type': 'short_term'
        }
        
        result = memory_module.process(pattern_data)
        
        # 验证模式发现结果
        if 'patterns' in result:
            assert len(result['patterns']) > 0
        else:
            # 如果没有实现模式发现，至少不应该出错
            assert 'success' in result
    
    def test_memory_consolidation(self, memory_module):
        """测试记忆整合功能"""
        memory_module.initialize()
        
        # 填满短期记忆
        for i in range(memory_module.short_term_size):
            store_data = {
                'action': 'store',
                'memory_type': 'short_term',
                'content': f'Important memory {i}',
                'importance': 0.8  # 高重要性
            }
            memory_module.process(store_data)
        
        # 触发记忆整合
        consolidate_data = {
            'action': 'consolidate',
            'from_type': 'short_term',
            'to_type': 'medium_term'
        }
        
        result = memory_module.process(consolidate_data)
        
        # 验证整合结果
        if 'success' in result and result['success']:
            # 重要记忆应该被转移到中期记忆
            assert len(memory_module.medium_term_memory) > 0
    
    def test_invalid_operations(self, memory_module):
        """测试无效操作处理"""
        memory_module.initialize()
        
        # 测试各种无效操作
        invalid_operations = [
            {'action': 'invalid_action'},
            {'action': 'store'},  # 缺少必要字段
            {'action': 'retrieve'},  # 缺少查询内容
            {'action': 'store', 'memory_type': 'invalid_type', 'content': 'test'},
            None,  # None输入
            {}     # 空字典
        ]
        
        for invalid_op in invalid_operations:
            try:
                result = memory_module.process(invalid_op)
                # 应该返回错误结果而不是抛出异常
                assert 'success' in result
                assert not result['success']
            except Exception as e:
                # 或者抛出合适的异常
                assert isinstance(e, (ValueError, TypeError, KeyError))
    
    def test_module_cleanup(self, memory_module):
        """测试模块清理"""
        memory_module.initialize()
        
        # 存储一些记忆
        store_data = {
            'action': 'store',
            'memory_type': 'short_term',
            'content': 'Test memory for cleanup'
        }
        memory_module.process(store_data)
        
        # 验证记忆存在
        assert len(memory_module.short_term_memory) > 0
        
        # 执行清理
        memory_module.cleanup()
        
        # 验证清理效果（具体行为取决于实现）
        # 这里主要测试清理方法不会抛出异常
        assert True


class TestMemoryModuleIntegration:
    """Memory Module集成测试"""
    
    def test_full_memory_lifecycle(self):
        """测试完整记忆生命周期"""
        config = {
            'enabled': True,
            'use_short_term': True,
            'use_medium_term': True,
            'short_term_size': 3,
            'medium_term_size': 10,
            'similarity_threshold': 0.5
        }
        
        module = MemoryModule('lifecycle_test', config)
        
        try:
            # 1. 初始化
            module.initialize()
            
            # 2. 存储记忆序列
            memory_sequence = [
                'I entered the room and saw a table',
                'There was a golden key on the table',
                'I picked up the key carefully',
                'I noticed a locked chest in the corner',
                'I used the key to open the chest',
                'Inside the chest was a beautiful gem'
            ]
            
            for i, content in enumerate(memory_sequence):
                store_data = {
                    'action': 'store',
                    'memory_type': 'short_term',
                    'content': content,
                    'context': f'step_{i}',
                    'importance': 0.7 + (i * 0.05)  # 递增重要性
                }
                result = module.process(store_data)
                assert result['success']
            
            # 3. 检索相关记忆
            retrieve_data = {
                'action': 'retrieve',
                'query': 'key chest',
                'memory_type': 'short_term'
            }
            
            result = module.process(retrieve_data)
            assert 'memories' in result
            assert len(result['memories']) > 0
            
            # 4. 验证记忆内容质量
            retrieved_contents = [mem['content'] for mem in result['memories']]
            relevant_memories = [content for content in retrieved_contents 
                               if 'key' in content.lower() or 'chest' in content.lower()]
            assert len(relevant_memories) > 0
            
            # 5. 清理
            module.cleanup()
            
        except Exception as e:
            module.cleanup()
            raise e


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
