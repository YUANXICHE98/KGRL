#!/usr/bin/env python3
"""
只运行RAG Agent实验
基于已有的Baseline结果，只测试RAG Agent
"""

import sys
sys.path.append('.')

from experiments.real_rag_vs_baseline import *

def run_rag_only_experiment():
    """只运行RAG Agent实验"""
    print("🧠 运行RAG Agent实验")
    print("=" * 50)
    
    # 创建实验记录器
    exp_logger = ExperimentLogger("real_rag_only")
    
    # 创建环境
    env = TextWorldEnvironment('rag_only', {
        'difficulty': 'easy',
        'max_episode_steps': 30
    })
    
    # 创建知识图谱
    print("📚 构建游戏知识图谱...")
    kg = create_game_knowledge_graph()
    retriever = KnowledgeGraphRetriever(kg, 'rag_retriever')
    print(f"✅ 知识图谱构建完成: {len(kg.facts)} 个事实")
    
    # 创建RAG Agent
    print("🧠 创建RAG Agent...")
    rag_agent = RAGAgent('rag_only', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 200,
        'max_kg_facts': 5,
        'kg_retrieval_method': 'semantic'
    })
    
    # 设置RAG Agent的知识检索器
    rag_agent.set_knowledge_retriever(retriever)
    print("✅ RAG Agent知识检索器设置完成")
    
    # 运行RAG实验
    print(f"\n🔬 运行RAG Agent实验 (8 episodes)...")
    run_agent_experiment(rag_agent, env, exp_logger, "RAG_LLM_Real", 8)
    
    # 保存结果
    print("\n📊 保存实验结果...")
    json_file, csv_file = exp_logger.save_results()
    
    # 生成报告
    print("📈 生成分析报告...")
    summary_report = exp_logger.generate_summary_report()
    
    print("\n" + "="*50)
    print("🎉 RAG Agent实验完成!")
    print("="*50)
    print(summary_report)
    
    print(f"\n📁 结果文件:")
    print(f"  数据: {json_file}")
    print(f"  CSV: {csv_file}")

if __name__ == "__main__":
    run_rag_only_experiment()
