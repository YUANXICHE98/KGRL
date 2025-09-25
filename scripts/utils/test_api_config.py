#!/usr/bin/env python3
"""
测试API配置脚本
验证VimsAI API连接和可用模型
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.simple_config import get_config

def test_api_connection():
    """测试API连接"""
    print("🧪 测试VimsAI API配置")
    print("=" * 50)
    
    # 获取配置
    config = get_config()
    api_key = config.get_api_key()
    base_url = config.get_base_url()
    model = config.get('llm.model')
    
    print(f"📋 配置信息:")
    print(f"  - API密钥: {api_key[:10]}...{api_key[-4:]}")
    print(f"  - Base URL: {base_url}")
    print(f"  - 模型: {model}")
    print()
    
    # 测试API连接
    try:
        from openai import OpenAI
        
        print("🔗 测试API连接...")
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 发送测试请求
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Please respond with 'API connection successful' if you can see this message."}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API连接成功!")
        print(f"📝 响应: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        
        # 尝试备用URL
        print("\n🔄 尝试备用URL...")
        try:
            backup_url = "https://usa.vimsai.com/v1"
            print(f"  - 备用URL: {backup_url}")
            
            client = OpenAI(
                api_key=api_key,
                base_url=backup_url
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello! Please respond with 'Backup API connection successful' if you can see this message."}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ 备用API连接成功!")
            print(f"📝 响应: {result}")
            
            # 更新配置文件使用备用URL
            print(f"🔧 更新配置文件使用备用URL...")
            config.set('llm.base_url', backup_url)
            config.save()
            
            return True
            
        except Exception as backup_e:
            print(f"❌ 备用API也连接失败: {backup_e}")
            return False

def test_different_models():
    """测试不同模型"""
    print("\n🎯 测试不同模型...")
    print("=" * 50)
    
    config = get_config()
    api_key = config.get_api_key()
    base_url = config.get_base_url()
    
    # 常见的VimsAI支持的模型
    models_to_test = [
        "claude-3-5-sonnet-20241022",
        "claude-3-haiku-20240307", 
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo"
    ]
    
    working_models = []
    
    for model in models_to_test:
        print(f"\n🧪 测试模型: {model}")
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Hi"}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            print(f"  ✅ {model}: {result}")
            working_models.append(model)
            
        except Exception as e:
            print(f"  ❌ {model}: {str(e)[:100]}...")
    
    print(f"\n📊 可用模型总结:")
    print(f"  - 总测试: {len(models_to_test)} 个")
    print(f"  - 可用: {len(working_models)} 个")
    
    if working_models:
        print(f"  - 推荐模型: {working_models[0]}")
        
        # 更新配置使用第一个可用模型
        if working_models[0] != config.get('llm.model'):
            print(f"🔧 更新配置使用推荐模型: {working_models[0]}")
            config.set('llm.model', working_models[0])
            config.save()
    
    return working_models

def main():
    """主函数"""
    print("🚀 VimsAI API配置测试")
    print("=" * 60)
    
    # 测试基本连接
    connection_ok = test_api_connection()
    
    if connection_ok:
        # 测试不同模型
        working_models = test_different_models()
        
        print(f"\n🎉 配置测试完成!")
        print(f"✅ API连接正常")
        print(f"✅ 找到 {len(working_models)} 个可用模型")
        print(f"🔧 配置已自动优化")
        
    else:
        print(f"\n❌ 配置测试失败!")
        print(f"请检查:")
        print(f"  1. API密钥是否正确")
        print(f"  2. 网络连接是否正常") 
        print(f"  3. VimsAI服务是否可用")

if __name__ == "__main__":
    main()
