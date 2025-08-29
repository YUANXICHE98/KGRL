#!/usr/bin/env python3
"""
运行真实RAG实验
基于已有的Baseline数据，只运行RAG Agent部分
"""

import sys
import time
import json
from pathlib import Path
sys.path.append('.')

from experiments.complete_real_experiment import *

def run_rag_experiment_only():
    """只运行RAG Agent实验"""
    print("🧠 运行真实RAG Agent实验")
    print("=" * 60)
    print("基于已有的Baseline数据，只测试RAG Agent")
    
    # 创建环境
    env = TextWorldEnvironment('rag_only_exp', {
        'difficulty': 'easy',
        'max_episode_steps': 30
    })
    
    # 创建知识图谱
    print("\n📚 构建知识图谱...")
    kg = create_comprehensive_knowledge_graph()
    retriever = KnowledgeGraphRetriever(kg, 'rag_only_retriever')
    print(f"✅ 知识图谱构建完成: {len(kg.facts)} 个事实")
    
    # 创建RAG Agent
    print("🧠 创建RAG Agent...")
    rag_agent = RAGAgent('rag_real_test', {
        'model_name': 'gpt-4o',
        'use_local_model': False,
        'use_knowledge_graph': True,
        'use_react_reasoning': True,
        'temperature': 0.7,
        'max_tokens': 200,
        'max_kg_facts': 5
    })
    rag_agent.set_knowledge_retriever(retriever)
    print("✅ RAG Agent创建成功")
    
    # 运行RAG实验
    print(f"\n🔬 运行RAG Agent实验 (6 episodes)...")
    rag_results = run_single_agent_episodes(rag_agent, env, "RAG_LLM_Real", 6)
    
    # 加载已有的Baseline数据
    baseline_file = Path("results/real_rag_vs_baseline/data/real_experiment_results_20250829_121400.json")
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            existing_data = json.load(f)
        baseline_results = [r for r in existing_data if r['agent_type'] == 'Baseline_LLM_Real']
        print(f"✅ 加载已有Baseline数据: {len(baseline_results)} episodes")
    else:
        print("❌ 未找到已有Baseline数据，将只保存RAG结果")
        baseline_results = []
    
    # 保存完整对比数据
    print("\n💾 保存完整实验数据...")
    json_file, csv_file, all_results = save_experiment_data(baseline_results, rag_results)
    
    # 生成对比报告
    print("\n📊 实验结果对比:")
    if baseline_results:
        baseline_success = sum(1 for r in baseline_results if r['success']) / len(baseline_results)
        print(f"  Baseline Agent: {baseline_success:.1%} 成功率 ({len(baseline_results)} episodes)")
    
    rag_success = sum(1 for r in rag_results if r['success']) / len(rag_results)
    print(f"  RAG Agent: {rag_success:.1%} 成功率 ({len(rag_results)} episodes)")
    
    if baseline_results:
        improvement = rag_success - baseline_success
        print(f"  改进: {improvement:+.1%}")
        
        # 详细统计
        baseline_avg_steps = sum(r['total_steps'] for r in baseline_results) / len(baseline_results)
        rag_avg_steps = sum(r['total_steps'] for r in rag_results) / len(rag_results)
        
        baseline_avg_reward = sum(r['total_reward'] for r in baseline_results) / len(baseline_results)
        rag_avg_reward = sum(r['total_reward'] for r in rag_results) / len(rag_results)
        
        print(f"\n📈 详细对比:")
        print(f"  平均步数: Baseline {baseline_avg_steps:.1f} vs RAG {rag_avg_steps:.1f}")
        print(f"  平均奖励: Baseline {baseline_avg_reward:.3f} vs RAG {rag_avg_reward:.3f}")
    
    # RAG特定统计
    total_kg_queries = sum(r['kg_queries'] for r in rag_results)
    total_kg_hits = sum(r['kg_hits'] for r in rag_results)
    if total_kg_queries > 0:
        kg_hit_rate = total_kg_hits / total_kg_queries
        print(f"\n🧠 RAG Agent知识图谱使用:")
        print(f"  总查询: {total_kg_queries}")
        print(f"  总命中: {total_kg_hits}")
        print(f"  命中率: {kg_hit_rate:.2%}")
    
    print(f"\n✅ 真实RAG实验完成!")
    print(f"📁 数据文件: {json_file}")
    print(f"📊 CSV文件: {csv_file}")
    
    return json_file, csv_file

if __name__ == "__main__":
    print("🚀 真实RAG Agent实验")
    print("这将使用:")
    print("  ✅ 真实GPT-4o API调用")
    print("  ✅ 真实知识图谱检索")
    print("  ✅ 真实ReAct推理")
    print("  ✅ 与已有Baseline数据对比")
    
    confirm = input("\n确认开始RAG实验? (y/N): ").strip().lower()
    if confirm == 'y':
        run_rag_experiment_only()
    else:
        print("实验取消")
