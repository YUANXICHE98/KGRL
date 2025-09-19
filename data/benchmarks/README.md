# Benchmark数据集

本目录包含用于KGRL项目的各种benchmark数据集。

## 📁 目录结构

```
benchmarks/
├── alfworld/          # ALFWorld数据集
├── textworld/         # TextWorld数据集
├── scripts/           # 数据下载和预处理脚本
└── processed/         # 预处理后的数据
```

## 🎯 支持的Benchmark

### ALFWorld
- **描述**: 基于ALFRED的文本世界环境
- **用途**: 具身AI任务的文本版本
- **任务类型**: 导航、操作、规划

### TextWorld
- **描述**: 可配置的文本游戏环境
- **用途**: 强化学习和自然语言理解
- **任务类型**: 探索、解谜、对话

## 🚀 快速开始

1. 下载数据集：
```bash
cd data/benchmarks/scripts
./download_alfworld.sh
./download_textworld.sh
```

2. 预处理数据：
```bash
python preprocess_alfworld.py
python preprocess_textworld.py
```

## 📊 数据统计

| 数据集 | 任务数量 | 平均步数 | 复杂度 |
|--------|----------|----------|--------|
| ALFWorld | 25,000+ | 15-30 | 中-高 |
| TextWorld | 可配置 | 5-50 | 低-高 |
