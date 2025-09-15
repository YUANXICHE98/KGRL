# **认知脚手架：知识图谱作为大语言模型驱动智能体记忆架构的研究**

## **第一部分：大语言模型智能体对结构化记忆的迫切需求**

将知识图谱（Knowledge Graphs, KGs）与大语言模型（Large Language Models, LLMs）驱动的智能体（Agent）相结合，并非仅仅是一种增量式的技术改良，而是在智能体认知能力发展道路上一个必要的进化步骤。本章节旨在深入阐述独立LLM在认知层面固有的局限性，并论证为何知识图谱能够提供一种传统记忆范式（如向量数据库）无法完全复现的结构化解决方案。

### **1.1 独立大语言模型的认知缺陷**

尽管LLM在自然语言处理任务中展现了卓越的能力，但其作为智能体核心时，暴露出一系列深刻的认知缺陷，这些缺陷构成了引入外部结构化记忆的根本动因。

#### **1.1.1 幻觉问题：可靠性的基石动摇**

LLM的核心机制是通过在海量文本数据上进行统计训练，学习词语和短语之间的模式与关联，以理解并生成类人文本 1。然而，这种概率性的生成方式导致了一个广为人知的顽疾——幻觉（Hallucination）。模型可能生成听起来极为合理但实际上与事实不符、不存在或不相关的内容 1。对于需要在现实世界中执行任务、依赖事实准确性的智能体而言，幻觉是其可靠性的致命弱点。一个无法区分事实与虚构的智能体，在任何关键应用场景中都是不可接受的。

#### **1.1.2 缺乏可验证的推理过程**

LLM的推理过程是隐式的，深藏于其数以亿计的参数构成的“黑箱”之中。这使得其决策路径难以被解释、验证或调试 2。当智能体给出一个结论或执行一个动作时，我们无法轻易追溯其背后的逻辑链条。这种不透明性在金融、医疗、法律等高风险领域是不可接受的。智能体的行为必须是可信、可追溯的，而LLM内在的“黑箱”特性恰恰与此背道而驰。

#### **1.1.3 静态的内部知识与实时性缺失**

LLM的知识库主要来源于其预训练数据，这意味着其知识在模型训练完成的那一刻便基本被“冻结”。它无法轻易地吸收实时信息，或在不进行昂贵的再训练或微调的情况下适应全新的、领域特定的知识 2。对于需要与动态环境交互、处理最新信息的智能体而言，这是一个根本性的限制。智能体必须能够持续学习和更新其对世界的认知，而静态的内部知识库使其无法满足这一要求。

#### **1.1.4 有限的上下文与推理视野**

尽管现代LLM的上下文窗口（Context Window）在不断扩大，但它本质上仍然是有限的。对于需要跨越长时程、连接大量分散信息点才能完成的复杂推理任务，LLM常常会力不从心 3。智能体在执行复杂任务时，往往需要整合来自不同时间、不同来源的信息片段，进行多步推理（Multi-hop Reasoning）。有限的上下文窗口限制了其进行这种长链条、复杂逻辑推理的能力。

### **1.2 传统记忆范式的局限性**

为了弥补LLM的上述缺陷，研究界提出了以检索增强生成（Retrieval-Augmented Generation, RAG）为代表的外部记忆机制。其中，基于向量数据库的RAG是目前最主流的方案。然而，这种范式在解决旧问题的同时，也引入了新的、更深层次的局限性。

#### **1.2.1 “文本块袋子”问题：关系的缺失**

标准的向量RAG将外部知识源（如文档库）切分成独立的文本块（Chunks），并将其嵌入到向量空间中。当智能体需要信息时，系统通过语义相似度检索最相关的文本块，并将其注入LLM的提示（Prompt）中 3。这种方法的本质是将记忆视为一个“文本块的袋子”（Bag of Chunks）。它擅长找到语义上相似的孤立信息，却完全忽略了信息块之间固有的、显式的关系 3。知识不仅仅是事实的堆砌，更是事实之间相互关联形成的有机网络。向量RAG丢失了这种至关重要的结构。

#### **1.2.2 多步推理的失败：无法“连接点滴”**

由于向量RAG缺乏对事实之间如何连接的感知，它在处理需要跨越多个信息点进行综合推理的复杂问题时表现不佳 3。例如，回答“A公司的CEO投资的B公司，其主要竞争对手是哪家公司？”这类问题，需要首先找到A公司的CEO，然后查询其投资组合找到B公司，最后再查找B公司的竞争对手。这个过程需要沿着实体间的关系链条进行“多步”跳转。向量RAG一次性检索出的语义相似文本块，很可能无法完整覆盖整个推理链，导致智能体无法“连接点滴”，从而无法给出准确答案。

#### **1.2.3 上下文的碎片化**

将文档切分成块的过程本身就存在风险，它可能人为地割裂了完整的上下文。一个被检索出的文本块可能提到了某个关键实体，但却缺失了定义该实体或解释其重要性的上下文信息 3。当这些碎片化的信息被提供给LLM时，可能会误导其判断，产生不完整甚至错误的回答。

综上所述，问题的核心症结已然清晰：当前智能体面临的挑战并非源于信息的匮乏，而是结构（Structure）的缺失。LLM的内部知识是隐式和联想式的，而向量RAG提供的外部记忆本质上仍是扁平、非结构化的文本。从这一困境中可以推导出一个必然的结论：仅仅向LLM提供更多的非结构化文本是治标不治本的。智能体认知能力的下一次飞跃，要求我们为其提供一个结构化的“认知脚手架”，使其能够在这个框架之上进行可靠的导航和逻辑推理。知识图谱，作为一种显式表示实体及其关系的数据结构 1，恰好为构建这样的脚手架提供了理论与实践的基础。这标志着智能体记忆架构从概率性联想向显式、可验证的关系逻辑的根本性转变。

## **第二部分：知识图谱与智能体框架的集成架构蓝图**

本章节将深入剖析将知识图谱集成到智能体系统中的主要技术范式。我们将从基于检索的方法开始，逐步过渡到更深层次的集成模式，为理解知识图谱与LLM在实践中如何协同工作提供一个清晰的分类学框架。

### **2.1 图谱检索增强生成（GraphRAG）：上下文丰富性的飞跃**

图谱检索增强生成（GraphRAG）是传统向量RAG的直接演进，它通过将知识图谱作为核心数据源，从根本上改变了信息检索的性质和质量。

#### **2.1.1 核心机制**

GraphRAG的核心思想是用知识图谱替代或补充向量存储，作为检索的主要对象 6。当智能体接收到用户查询时，系统不再是检索孤立的文本块，而是从图谱中检索与查询相关的子图、路径、或围绕核心实体的结构化摘要信息。这意味着检索结果本身就包含了实体间的关系，是一种结构化的上下文。

#### **2.1.2 卓越的上下文供给**

通过检索互联的信息，GraphRAG为LLM提供了一个远比传统RAG丰富和全面的上下文环境。这个上下文不仅包含事实本身，还包括了相关的实体、文档以及这些元素之间的结构性关系 6。例如，在查询一个公司时，GraphRAG不仅能返回该公司的描述，还能一并提供其创始人、投资方、合作伙伴和竞争对手等关联信息。这种整体性的上下文直接缓解了向量RAG导致的上下文碎片化问题，使LLM能够基于更完整的信息图景进行回答。

#### **2.1.3 增强的可解释性与信任度**

由于GraphRAG检索到的是结构化的图谱数据，智能体生成答案的依据可以被清晰地追溯到图谱中的具体实体和关系 6。这为答案的生成过程提供了一条透明的审计路径。用户或开发者可以明确地看到“智能体是因为在图谱中发现了‘实体A’通过‘关系R’连接到‘实体B’，才得出了这个结论”。这种可解释性对于需要高可靠性和合规性的企业级应用至关重要，它将智能体的回答从一个概率性的“黑箱”输出，转变为一个有据可查、值得信赖的结论。

### **2.2 智能体工具调用：LLM作为图谱上的推理引擎**

在这种更主动的集成模式中，知识图谱不再仅仅是一个被动的数据源，而是智能体可以主动交互和操作的“工具”。

#### **2.2.1 智能体-工具范式**

该模型为LLM配备了一套可以与外部世界交互的“工具集”（Tool Set） 6。其中，一个至关重要的工具就是查询知识图谱的能力。智能体框架，如LangChain或Google Gen AI Toolbox，允许开发者定义这些工具，包括其名称、功能描述、输入参数和输出格式 6。

#### **2.2.2 从自然语言到图谱查询**

智能体的核心任务转变为一个多阶段的认知过程。首先，LLM分析用户的自然语言问题，理解其意图。然后，它自主地制定一个解决问题的计划。如果计划的某一步需要从知识图谱中获取信息，LLM会利用其强大的语言理解和代码生成能力，将自然语言的需求转换成一种形式化的图谱查询语言，例如用于Neo4j的Cypher查询语句 5。这一步是整个架构的关键，它要求LLM不仅理解语言，还要理解图谱的模式（Schema）和查询语法。

#### **2.2.3 迭代式交互与推理**

智能体的交互过程是动态和迭代的。它可以执行一次图谱查询，获取结构化的结果，然后对这些结果进行分析。基于初步的发现，它可能会决定需要进一步的信息，从而自主地构建并执行第二次、第三次查询 6。这种迭代循环的能力，使得智能体能够像人类专家一样，在知识图谱上进行探索性的、多步骤的复杂推理。一个具体的例子是在软件仓库问答系统中，智能体通过生成一系列Cypher查询，来回答关于代码提交、问题（issues）和文件之间复杂关系的问题 5。

### **2.3 知识增强的监督式微调（KG-SFT）：将结构内化于模型**

这是一种更深层次的集成策略，其目标并非在推理时查询图谱，而是将图谱的结构化知识直接“注入”并内化到LLM的参数中。

#### **2.3.1 核心原理**

知识增强的监督式微调（Knowledge Graph-Enhanced Supervised Fine-Tuning, KG-SFT）的核心是利用知识图谱来生成高质量、富含结构化逻辑的训练数据，然后用这些数据对LLM进行监督式微调（SFT） 9。

#### **2.3.2 超越表层模式学习**

传统的SFT通常使用简单的“问题-答案”（Q\&A）对作为训练数据。这种方式的一个弊端是，LLM可能只是学会了Q\&A的表层语言模式（如输出格式），而没有真正理解背后知识的内在逻辑和关联 9。KG-SFT通过以下方式克服了这一缺陷：对于每一个Q\&A对，它利用知识图谱生成一个结构化的解释，这个解释清晰地展示了答案是如何通过图谱中的实体和关系推导出来的。通过学习这些“问题-答案-解释”三元组，LLM被迫去理解和掌握知识点之间的相关性和逻辑关系，而不仅仅是记忆孤立的事实。

#### **2.3.3 在低资源领域的效能**

KG-SFT在知识密集型且数据稀疏的领域（例如特定的医学或科学领域）尤为有效 9。在这些领域，获取大量高质量的标注数据成本极高。通过利用现有的知识图谱，可以自动化地生成大量高质量的合成训练数据。实验证明，这种方法能够显著提升LLM在知识召回、推理和迁移方面的能力，在低数据场景下，准确率提升最高可达18.1%，平均提升8.7% 9。

这三种架构并非相互排斥，而是代表了一个“认知委托”的连续光谱。GraphRAG将**信息检索**的任务委托给图谱。智能体工具调用则更进一步，将**结构化查询的制定与执行**委托给LLM。而KG-SFT则试图将图谱的**关系逻辑**本身内化到LLM的核心参数中。从实践角度看，这揭示了一个关键的设计权衡：如果目标是为智能体提供可靠的事实依据，GraphRAG简单而有效；如果任务需要动态、探索性的推理能力，智能体工具调用模式更为强大，但需要应对LLM推理错误的风险；如果目标是构建一个在特定领域具有深度内置知识的专用模型，KG-SFT则是最佳选择。因此，架构的选择并非技术优劣问题，而是取决于智能体需要解决的具体任务和期望达成的认知目标。

## **第三部分：知识图谱作为智能体记忆的认知架构**

本章节将探讨一个更为深刻的观念转变：不再将知识图谱仅仅视为一个外部数据库，而是将其 conceptualize 为一个功能上模拟人类认知记忆系统的复杂架构。这种视角为设计更高级、更具适应性的智能体行为提供了理论基础。

### **3.1 语义记忆：一个稳定的世界知识库**

在认知科学中，语义记忆（Semantic Memory）指的是我们对世界的一般性、事实性知识的记忆，例如“巴黎是法国的首都”或“鸟会飞”。在智能体架构中，知识图谱完美地扮演了这一角色。

#### **3.1.1 定义**

知识图谱作为智能体的长期、稳定的语义记忆库，以结构化的形式存储了关于世界实体及其相互关系的客观事实 10。这构成了智能体对世界的“教科书式”的知识基础，是其进行推理和决策的静态背景。

#### **3.1.2 应用**

大多数基于知识图谱的问答系统和GraphRAG应用，其核心都是利用图谱作为语义记忆。在这些应用中，智能体查询一个预先构建好的、变化缓慢的知识图谱，以获取关于公司关系、科学概念、API文档结构等领域的精确事实 6。这个图谱为智能体提供了一个坚实、可靠的“事实地面”，有效减少了依赖LLM内部知识可能产生的幻觉。

### **3.2 情景记忆：记录智能体的“亲身经历”**

这是将知识图谱用作智能体记忆的一个革命性创新。它借鉴了人类的情景记忆（Episodic Memory）概念，即对个人特定经历、事件及其发生时间、地点的记忆。

#### **3.2.1 一种新范式**

在这种范式下，知识图谱不再是静态的，而是由智能体在与环境的交互过程中动态地、从零开始构建和更新的 10。它成为了智能体“亲身经历”的日志。

#### **3.2.2 AriGraph中的实现机制**

AriGraph框架是这一范式的杰出代表。在其设计中，智能体在与环境交互的每一个时间步（time step），都会在记忆图谱中创建新的“情景顶点”（episodic vertices）和“情景边”（episodic edges） 10。情景顶点代表一个具体的观察或动作（例如，“我在厨房看到了一个苹果”），而情景边则将这个情景顶点与相关的语义概念（如“厨房”、“苹果”）以及时间信息连接起来。通过这种方式，

AriGraph构建了一个富含时间维度的、记录智能体完整交互历史的结构化记忆。

#### **3.2.3 功能**

这种情景记忆使得智能体能够进行远超简单事实检索的复杂认知活动。它能够推理事件的先后顺序，理解因果关系（例如，“因为我打开了冰箱，所以我看到了苹果”），并能通过回忆过去的相似经历来为当前决策提供参考。这标志着智能体从一个只能查询事实的系统，向一个能够从自身经验中学习的系统转变。

### **3.3 知识图谱作为动态世界模型**

当语义记忆和情景记忆在一个统一的知识图谱架构中被结合时，这个图谱就升华为一个全面的“世界模型”（World Model）。

#### **3.3.1 定义**

世界模型是智能体对其所处环境以及自身在该环境中所处位置的一个结构化的内部表征 11。它不仅包含了关于世界的静态事实（语义记忆），也包含了世界如何随时间变化以及智能体自身与之交互的历史（情景记忆）。

#### **3.3.2 从观察到结构**

智能体主动地构建这个世界模型。它通过解析非结构化的环境观察（例如，在文本游戏中读到的一段描述文字），提取出结构化的语义三元组（主体, 关系, 客体，如 (厨房, 包含, 冰箱)），然后将这些三元组实时地整合进其记忆图谱中 10。这个过程是一个持续的、将感官输入转化为结构化知识的过程。

#### **3.3.3 赋能规划与探索**

这个动态构建的世界模型不仅用于信息回忆，更是智能体进行高级规划和探索的关键工具。智能体可以主动查询自己的记忆图谱来：

* **识别未探索的路径**：通过查询图中哪些“房间”的“出口”尚未被访问过。
* **理解物体间的复杂关系**：例如，要完成“做饭”任务，需要哪些“食材”和“厨具”，以及它们当前分别在哪些“位置”。
* **制定复杂计划**：基于对环境的结构化理解，智能体可以制定出一系列逻辑连贯的动作，来达成一个远期目标。

这种能力是那些只能依赖扁平、非结构化的历史记录（如完整的对话历史或滚动摘要）的智能体所无法企及的 11。

从根本上看，情景记忆的引入标志着智能体角色的深刻转变。一个只拥有静态语义知识图谱的智能体，可以被认为是一个知识渊博的“信息处理器”。然而，当智能体开始构建和利用动态的、包含个人经历的情景知识图谱时，它便拥有了“个人历史”，并获得了从这段历史中学习的能力。这使其从一个被动的处理器，转变为一个主动的“学习实体”。这一转变是从“知识增强生成”（Knowledge-Augmented Generation）到“知识驱动认知”（Knowledge-Driven Cognition）的范式跃迁，是通往更通用、更自主智能的关键一步。

## **第四部分：实证验证与应用框架**

本章节将前述的抽象概念与具体的、有证据支持的案例研究相结合。我们将深入剖析几个代表性的框架，分析它们的架构、性能表现以及它们为该领域带来的独特见解。

### **4.1 案例研究：AriGraph与Ariadne智能体**

#### **4.1.1 背景**

AriGraph是为一个名为Ariadne的智能体设计的记忆系统，该智能体旨在解决复杂的交互式文本游戏（如TextWorld环境）中的任务 11。这些文本游戏是评估智能体推理、规划和记忆能力的绝佳基准，因为它们要求智能体理解自然语言描述，构建对虚拟世界的心理模型，并执行一系列动作以达成目标。

#### **4.1.2 架构**

AriGraph的核心特征是其作为智能体外部记忆的动态性。这个知识图谱是“从零开始”（from scratch）构建的，随着智能体的探索而不断增长。其架构精妙地集成了两种记忆类型 10：

* **语义知识图谱**：存储关于游戏世界中实体及其关系的静态事实（例如，“钥匙”可以“打开”“箱子”）。
* **情景图谱**：通过“情景顶点”和“情景边”记录智能体在特定时间点的动作和观察，形成一条结构化的时间轨迹。

#### **4.1.3 性能表现**

实证结果极具说服力。搭载了AriGraph记忆系统的Ariadne智能体，在多项任务（包括复杂的烹饪和寻宝任务）中的表现“显著超越了所有现有的基线方法” 11。这些基线方法包括了依赖完整历史记录、滚动摘要以及标准向量RAG等非结构化记忆的智能体。这一压倒性的优势为结构化、情景化的记忆架构的优越性提供了强有力的经验证据。

### **4.2 案例研究：软件仓库领域的特定问答系统**

#### **4.2.1 问题**

软件仓库（如GitHub项目）包含了海量的结构化数据，如代码提交（commits）、问题报告（issues）、文件变更等。从中提取有价值的见解通常耗时且需要深厚的技术背景 5。构建一个能用自然语言回答相关问题的智能体具有巨大的应用价值。

#### **4.2.2 架构**

研究人员设计了一个两阶段的系统 5：

1. **知识图谱构建器（Knowledge Graph Constructor）**：此模块负责从软件仓库中提取数据，并将其建模为一个结构化的知识图谱。图中的节点可以是提交、问题、文件、开发者等，边则表示它们之间的关系（如“某开发者”“提交了”“某次commit”，“某commit”“修复了”“某个issue”）。
2. **交互循环（Interaction Loop）**：当用户提出自然语言问题时，系统使用一个强大的LLM（如GPT-4o）作为“推理引擎”，将问题翻译成图谱查询语言（Cypher）。该查询随后在图谱上执行，返回结构化数据，最后由LLM将这些数据整合成自然语言答案返回给用户。

#### **4.2.3 发现与局限**

该系统的初步实现取得了65%的准确率，但在处理需要多步推理的复杂问题时表现不佳 8。通过对失败案例的深入分析，研究人员发现，最主要的瓶颈在于LLM在生成正确、复杂查询时的

**推理能力**。LLM在建模关系、进行算术逻辑或应用属性过滤时会犯错 8。然而，通过引入精心设计的提示工程技术，特别是“少样本思维链”（Few-shot Chain-of-Thought, CoT）提示，系统的整体准确率被显著提升至84% 5。这个案例清晰地表明，虽然LLM是强大的工具使用者，但它们需要明确的指导和“脚手架”才能高效、可靠地与结构化工具（如知识图谱）进行交互。

### **4.3 新兴范式：思维知识图谱（KGoT）**

#### **4.3.1 动机**

尽管LLM功能强大，但在解决复杂任务时，其高昂的API调用成本和在长链条推理中可能出现的失败，是推广应用的主要障碍 15。

#### **4.3.2 核心思想**

思维知识图谱（Knowledge Graph of Thoughts, KGoT）提出了一种创新的解决方案。它不再完全依赖LLM内部隐式的、线性的思维链（Chain-of-Thought）来进行推理，而是将**推理过程本身外化（externalize）为一个动态构建的知识图谱** 15。在这个架构中，LLM的角色从执行整个推理过程，转变为在一个外部的、显式的结构化知识图谱上进行“思考”——即填充和查询这个推理图谱。每一步的思考成果（一个中间结论）都成为图谱中的一个节点，思考步骤之间的逻辑关系则成为边。

#### **4.3.3 优势**

这种方法带来了显著的好处。首先，它极大地降低了运营成本。通过使用更小、更便宜的模型（如GPT-4o mini）来执行填充和查询图谱的子任务，而不是用最昂贵的模型（如GPT-4o）来执行完整的长链条推理，任务执行成本可以实现数量级的下降（例如，在一个基准测试中从187美元降至约5美元），同时保持很高的成功率 15。其次，由于整个推理过程被明确地记录在知识图谱中，系统的透明度和可验证性得到了极大提升，这有助于减少由LLM内部偏见导致的问题。

### **4.4 架构对比分析**

为了清晰地总结和对比上述框架，下表从多个关键维度对它们进行了分析。

| 表1：基于知识图谱的LLM智能体记忆架构对比分析 |
| :------------------------------------------- |
| **架构**                               |
| **GraphRAG**                           |
| **软件仓库问答系统**                   |
| **AriGraph**                           |
| **KGoT**                               |

这张表格的价值在于，它将复杂的案例研究提炼成一个简洁、结构化的决策辅助工具。通过审视表格中的不同维度，研究人员和实践者可以迅速把握不同架构的本质区别、适用场景和固有权衡。例如，一个需要为静态企业知识库构建问答机器人的开发者，可能会发现GraphRAG是最佳起点。而一个致力于构建能在复杂虚拟环境中学习和适应的通用智能体的研究者，则必须关注AriGraph所代表的动态、情景记忆范式。这张表格清晰地勾勒出了当前应用框架的版图，并揭示了它们各自的优势与挑战。

## **第五部分：图谱赋能的智能体能力系统性分类**

本章节将采用一种系统化的方法，借鉴近期的综述性研究成果 16，对知识图谱结构如何具体地增强智能体的各项核心功能进行分类。这为理解知识图谱在智能体认知循环中扮演的多方面角色提供了一个全面的框架。

### **5.1 增强规划与推理能力**

规划与推理是智能体核心认知功能的中枢。知识图谱通过提供结构化的信息和思维框架，极大地提升了智能体在这方面的表现。

#### **5.1.1 任务分解**

对于复杂的宏大任务，智能体需要将其分解为一系列更小、可管理的子任务。图谱结构，特别是任务依赖图（Task Dependency Graphs），能够清晰地表示这些子任务以及它们之间的先后依赖关系 17。这使得智能体能够进行更有效的全局规划，理解任务各部分之间的逻辑联系，避免陷入局部最优或逻辑死循环。

#### **5.1.2 结构化推理**

知识图谱为智能体的推理过程提供了外部的、结构化的知识支撑，这在各种问答系统中已得到验证。更前沿的概念，如“思维图谱”（Graph of Thoughts），则更进一步，主张将LLM的整个推理过程组织成一个图状网络，而不是传统的线性“思维链” 17。在这种模式下，每个“想法”或中间结论都是图中的一个节点，智能体可以探索多个并行的推理路径，并在需要时对它们进行聚合或剪枝，从而实现更灵活、更强大的推理能力。

### **5.2 改进执行与环境交互**

智能体的能力最终体现在与环境的有效交互上。知识图谱通过构建环境的结构化模型，为智能体的感知和行动提供了坚实的基础。

#### **5.2.1 场景理解**

对于具身智能体（Embodied Agents），如机器人或自动驾驶汽车，理解物理环境至关重要。场景图（Scene Graphs）是一种特殊的知识图谱，它能够捕捉环境中物体之间的空间和语义关系（例如，“沙发”在“客厅”里，“台灯”在“桌子”上） 17。这种结构化的场景表征，使得智能体能够更有效地感知环境，并基于这种理解进行交互。

#### **5.2.2 指导行动**

如AriGraph案例所示，智能体在其知识图谱内部构建的世界模型，是其做出明智行动决策的基础 11。通过查询这个内部模型，智能体可以评估不同行动方案的潜在后果，选择最优路径，这种基于结构化理解的决策远比基于当前感官输入的反应式行为更为高级和有效。

### **5.3 革新记忆操作**

知识图谱从根本上改变了智能体存储和检索记忆的方式，使其更接近人类的联想记忆模式。

#### **5.3.1 高级检索**

基于图谱的RAG（GraphRAG）允许进行远比传统向量搜索更精确、更具上下文感知能力的检索。智能体可以利用图中的路径和子图结构来检索信息 17。例如，它可以检索“连接两个特定实体最短路径上的所有节点”，或者“某个实体周围两跳范围内的所有邻居”。这种检索方式能够返回高度相关且结构化的信息簇，而非零散的文本块。

#### **5.3.2 动态维护**

高级智能体必须能够持续学习。知识图谱提供了一个理想的框架来实现记忆的动态维护。当智能体遇到新信息或发现旧知识有误时，它可以直接在图谱上进行更新、添加或删除节点和边 17。这确保了智能体的知识库能够与时俱进，保持其准确性和相关性。

### **5.4 构建多智能体协作结构**

在多智能体系统（Multi-Agent Systems）中，有效的协作是成功的关键。知识图谱可以用来建模和优化智能体之间的交互。

#### **5.4.1 协作拓扑**

图谱可以用来表示多智能体系统中的通信模式和依赖关系 16。图中的节点是智能体，边则代表它们之间的通信信道或任务依赖。通过分析和优化这个“协作拓扑图”，可以设计出更高效的通信协议，减少不必要的通信开销，确保关键信息能够在正确的智能体之间及时传递，从而提升整个系统的协同性能。

通过这一系统性的分类，我们可以得出一个更深层次的结论：知识图谱在智能体架构中的角色远非单一的“记忆库”。它根据智能体当前所处的认知环节，扮演着不同的功能角色。在规划阶段，它是一个**任务规划器**；在感知阶段，它是一个**环境感知模型**；在信息检索阶段，它是一个**高级索引**；在多智能体协作中，它又成为一个**通信骨架**。正是这种多功能性，使得图谱范式成为构建下一代复杂、高级智能体的一个极其强大和通用的基础。这表明，知识图谱不应被视为智能体的一个附加组件，而应被视为其整个“感知-规划-行动”认知循环的 foundational data structure，是智能体设计的核心架构原则之一。

## **第六部分：内在挑战与操作障碍**

尽管将知识图谱作为智能体记忆架构展现出巨大的潜力，但在实现其广泛应用之前，必须正视并克服一系列严峻的理论和实践挑战。本章节将对这些障碍进行批判性和现实性的评估。

### **6.1 LLM的推理瓶颈**

将LLM作为连接自然语言与结构化知识图谱的桥梁，是当前主流架构的核心，但这恰恰也是最脆弱的一环。

#### **6.1.1 查询生成失败**

软件仓库问答系统的案例研究为我们提供了确凿的证据：LLM在将复杂、多步的自然语言问题转化为语法正确且语义恰当的图谱查询时，常常会遇到困难 8。这已成为系统主要的失败点。具体问题包括：对图谱中的关系类型理解错误、在查询中构建了错误的算术或逻辑运算、错误地应用了属性过滤器或日期格式等 8。这些看似微小的错误，都可能导致查询失败或返回完全错误的结果。

#### **6.1.2 对“脚手架”的依赖**

为了克服LLM的推理缺陷，研究人员不得不采用更复杂的提示工程技术，如少样本思维链（Few-shot CoT） 8。虽然这能显著提高性能，但它也增加了系统的复杂性和脆弱性。这种“脚手架”并非万无一失，其效果依赖于精心挑选的样本，并且可能无法泛化到所有类型的查询。这表明，我们目前仍然是在“引导”而非“驾驭”LLM的结构化推理能力。

### **6.2 动态性与维护难题**

对于需要在动态环境中运行并持续学习的智能体，其记忆图谱的维护面临着巨大的数据工程挑战。

#### **6.2.1 可扩展性与延迟**

随着智能体经验的积累，其记忆知识图谱的规模会迅速膨胀。在庞大的图谱上保证低延迟的查询执行，是一个重大的工程挑战 4。对于需要实时与用户或环境交互的智能体而言，毫秒级的响应至关重要，任何显著的查询延迟都可能导致智能体行为失常。

#### **6.2.2 实时更新与一致性**

在动态环境中，知识图谱必须能够处理流式的数据更新。这引入了一系列复杂的数据库问题，如处理潜在的数据写入冲突、保证事务的原子性和隔离性，以及确保智能体在任何时刻查询到的都是一个逻辑上一致的知识快照 2。这些问题在传统的分布式数据库领域已经研究了几十年，将这些解决方案高效地应用到智能体的记忆系统中，并非易事。

#### **6.2.3 时间动态性建模**

世界是随时间变化的，实体和关系并非永恒不变。例如，一个人的职位会改变，公司的总部会搬迁。在知识图谱中有效地建模时间维度，并支持对历史状态的查询（例如，“查询A公司在2023年的CEO是谁？”），是一个非常复杂但至关重要的问题 4。大多数简单的图模型并未很好地解决这一挑战。

### **6.3 系统复杂性与成本**

将LLM、知识图谱和智能体框架集成为一个协同工作的系统，其复杂性和成本远高于部署一个独立的LLM。

#### **6.3.1 构建与策管**

无论是从现有数据批量构建，还是由智能体动态生成，创建一个高质量、无噪音的知识图谱都需要巨大的投入 2。虽然可以利用LLM来辅助自动化知识提取，但其输出的准确性需要得到验证，这往往又需要引入“人在回路”（human-in-the-loop）的审核，从而增加了成本和时间。

#### **6.3.2 集成开销**

设计、部署和维护一个包含LLM、图数据库、智能体逻辑控制器等多个组件的混合系统，对开发团队的技术栈提出了更高的要求。系统的稳定性、各组件间的通信效率以及端到端的监控和调试，都比单一模型系统要复杂得多。

深入分析这些挑战，可以发现该领域面临的困境是一场“双线作战”。一条战线是**人工智能问题**：如何提升LLM在结构化数据上的推理和逻辑能力，使其成为一个更可靠的“工具使用者”。另一条战线是**数据工程问题**：如何构建可扩展、高并发、支持实时更新并保证一致性的高性能图数据基础设施。这两条战线上的进展是相互依存、相互制约的。一个拥有完美结构化推理能力的LLM，如果其记忆库是一个缓慢、不一致的知识图谱，那么它的能力也无从发挥。反之，一个拥有完美实时性能的图数据库，如果与之交互的LLM无法生成正确的查询，那么这个数据库的潜力也将被埋没。因此，智能体认知能力的未来突破，将取决于人工智能和数据工程这两个领域协同演化的步伐。任何一条战线的滞后，都将成为整个系统的瓶颈。

## **第七部分：未来轨迹：迈向协同与自我完善的系统**

本章将综合前述分析，对该领域未来的研究与发展轨迹进行展望。核心趋势将是从当前的单向辅助关系，演变为LLM与知识图谱之间真正的共生与协同，最终形成能够自我完善的智能系统。

### **7.1 协同循环：构建自我“大脑”的智能体**

#### **7.1.1 从知识消费者到创造者**

未来的终极愿景是构建一个良性循环：LLM智能体不仅*使用*知识图谱，更能主动地*构建、策管和精炼*知识图谱。可以设想，部署成群的智能体去阅读海量的非结构化文本（如科学文献、新闻报道、网页），自动识别新的实体和关系，并自主地将这些新知识填充和更新到一个中心的知识图谱中 16。这将创造一个能够自我迭代、自我完善的全球知识库。

#### **7.1.2 双向增强的共生关系**

这种模式形成了一种真正的共生关系。一方面，知识图谱为LLM提供了可验证的事实基础，锚定了其输出，减少了幻觉 2。另一方面，LLM强大的语义理解和生成能力，为大规模、自动化地构建和维护知识图谱提供了前所未有的动力 2。知识图谱使LLM更“聪明”，而LLM使知识图谱更“庞大”和“新鲜”。

### **7.2 智能体神经图数据库（Agentic NGDBs）**

#### **7.2.1 下一个前沿**

这是一个新兴且极具前瞻性的概念，它提议将图神经网络（Graph Neural Networks, GNNs）直接集成到图数据库的内核中，创造出一种具备原生推理能力的数据库系统，即神经图数据库（Neural Graph Databases, NGDBs） 19。这种数据库不仅能存储事实，还能通过GNN对图中缺失的链接进行预测，或对节点的属性进行推断。

#### **7.2.2 智能体化控制**

“智能体神经图数据库”（Agentic NGDB）则更进一步。它设想了一种可以被智能体直接控制和修改的数据库 19。智能体不仅能对数据执行创建、读取、更新、删除（CRUD）操作，甚至可能直接在模型的潜在空间（latent space）中进行编辑，从而在基础设施层面实现真正的自我改进。这模糊了程序和数据之间的界限。

### **7.3 开放的研究问题与机遇**

该领域依然充满了待解的难题和广阔的探索空间。

* **泛化能力**：在一个特定领域（如一个游戏环境）中，通过与环境交互构建了记忆图谱的智能体，如何能将其学到的知识或学习策略迁移到全新的、未见过的领域？
* **多模态知识图谱**：如何将当前的架构从纯文本扩展，把视觉、听觉等其他模态的感官信息也整合到智能体的世界模型知识图谱中？
* **推理与检索的权衡**：将推理过程外化到图谱中（如KGoT）与提升LLM自身在图谱上进行推理的能力（如智能体工具调用），这两种路径之间的根本性权衡是什么？这仍然是未来架构设计的核心辩论点。
* **可扩展性与成本效益**：开发新的算法、数据结构和系统架构，以解决第六部分中提到的可扩展性、延迟和维护成本等操作性障碍，是使这些强大系统变得更实用、更易于普及的关键。

综观全局，该领域的长期发展轨迹，是指向“智能体”与其“记忆”之间界限的消融。在未来的系统中，例如设想的智能体神经图数据库，记忆系统本身将变得智能化和主动化，具备自我修改和原生推理的能力。知识图谱将从一个被智能体查询的被动数据库，演变为一个与智能体共同思考、共同进化的主动认知伙伴。未来的终极形态，可能不再是一个LLM*拥有*一个知识图谱记忆，而是一个统一的、动态的、自我完善的神经-符号认知架构，其中知识的表示、学习和推理是这个智能记忆结构不可分割的内在功能。

#### **Works cited**

1. \[2311.07914\] Can Knowledge Graphs Reduce Hallucinations in ..., accessed September 5, 2025, [https://ar5iv.labs.arxiv.org/html/2311.07914](https://ar5iv.labs.arxiv.org/html/2311.07914)
2. Practices, opportunities and challenges in the fusion of knowledge graphs and large language models \- ResearchGate, accessed September 5, 2025, [https://www.researchgate.net/publication/393725907\_Practices\_opportunities\_and\_challenges\_in\_the\_fusion\_of\_knowledge\_graphs\_and\_large\_language\_models](https://www.researchgate.net/publication/393725907_Practices_opportunities_and_challenges_in_the_fusion_of_knowledge_graphs_and_large_language_models)
3. How to Improve Multi-Hop Reasoning With Knowledge Graphs and LLMs \- Neo4j, accessed September 5, 2025, [https://neo4j.com/blog/genai/knowledge-graph-llm-multi-hop-reasoning/](https://neo4j.com/blog/genai/knowledge-graph-llm-multi-hop-reasoning/)
4. Building AI Agents with Knowledge Graph Memory: A Comprehensive Guide to Graphiti | by Saeed Hajebi | Medium, accessed September 5, 2025, [https://medium.com/@saeedhajebi/building-ai-agents-with-knowledge-graph-memory-a-comprehensive-guide-to-graphiti-3b77e6084dec](https://medium.com/@saeedhajebi/building-ai-agents-with-knowledge-graph-memory-a-comprehensive-guide-to-graphiti-3b77e6084dec)
5. Synergizing LLMs and Knowledge Graphs: A Novel Approach to Software Repository-Related Question Answering \- arXiv, accessed September 5, 2025, [https://arxiv.org/html/2412.03815v1](https://arxiv.org/html/2412.03815v1)
6. Building AI Agents With the Google Gen AI Toolbox and Neo4j ..., accessed September 5, 2025, [https://medium.com/neo4j/building-ai-agents-with-the-google-gen-ai-toolbox-and-neo4j-knowledge-graphs-86526659b46a](https://medium.com/neo4j/building-ai-agents-with-the-google-gen-ai-toolbox-and-neo4j-knowledge-graphs-86526659b46a)
7. LLM Agents are simply Graph — Tutorial For Dummies : r/LocalLLaMA \- Reddit, accessed September 5, 2025, [https://www.reddit.com/r/LocalLLaMA/comments/1jf68qs/llm\_agents\_are\_simply\_graph\_tutorial\_for\_dummies/](https://www.reddit.com/r/LocalLLaMA/comments/1jf68qs/llm_agents_are_simply_graph_tutorial_for_dummies/)
8. Synergizing LLMs and Knowledge Graphs: A Novel Approach to Software Repository-Related Question Answering \- arXiv, accessed September 5, 2025, [https://arxiv.org/pdf/2412.03815?](https://arxiv.org/pdf/2412.03815)
9. KNOWLEDGE GRAPH FINETUNING ENHANCES KNOWL- EDGE MANIPULATION IN LARGE LANGUAGE MODELS \- ICLR Proceedings, accessed September 5, 2025, [https://proceedings.iclr.cc/paper\_files/paper/2025/file/e44337573fcac83f219c8effa4ebf90d-Paper-Conference.pdf](https://proceedings.iclr.cc/paper_files/paper/2025/file/e44337573fcac83f219c8effa4ebf90d-Paper-Conference.pdf)
10. \[Literature Review\] AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents \- Moonlight, accessed September 5, 2025, [https://www.themoonlight.io/en/review/arigraph-learning-knowledge-graph-world-models-with-episodic-memory-for-llm-agents](https://www.themoonlight.io/en/review/arigraph-learning-knowledge-graph-world-models-with-episodic-memory-for-llm-agents)
11. AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents, accessed September 5, 2025, [https://www.researchgate.net/publication/382066150\_AriGraph\_Learning\_Knowledge\_Graph\_World\_Models\_with\_Episodic\_Memory\_for\_LLM\_Agents](https://www.researchgate.net/publication/382066150_AriGraph_Learning_Knowledge_Graph_World_Models_with_Episodic_Memory_for_LLM_Agents)
12. Using Graphs to Improve the Interpretability of API Documentation for BIM Authoring Software. \- mediaTUM, accessed September 5, 2025, [https://mediatum.ub.tum.de/doc/1769403/1769403.pdf](https://mediatum.ub.tum.de/doc/1769403/1769403.pdf)
13. AIRI-Institute/AriGraph \- GitHub, accessed September 5, 2025, [https://github.com/AIRI-Institute/AriGraph](https://github.com/AIRI-Institute/AriGraph)
14. AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents, accessed September 5, 2025, [https://huggingface.co/papers/2407.04363](https://huggingface.co/papers/2407.04363)
15. 1 Introduction \- arXiv, accessed September 5, 2025, [https://arxiv.org/html/2504.02670v2](https://arxiv.org/html/2504.02670v2)
16. Graphs Meet AI Agents: Taxonomy, Progress, and Future Opportunities \- arXiv, accessed September 5, 2025, [https://arxiv.org/html/2506.18019v1](https://arxiv.org/html/2506.18019v1)
17. Graphs Meet AI Agents: Taxonomy, Progress, and Future Opportunities | alphaXiv, accessed September 5, 2025, [https://www.alphaxiv.org/overview/2506.18019v1](https://www.alphaxiv.org/overview/2506.18019v1)
18. From Data to Decisions: How Knowledge Graphs Are Becoming the Brain of the Modern Enterprise | by Adnan Masood, PhD. \- Medium, accessed September 5, 2025, [https://medium.com/@adnanmasood/from-data-to-decisions-how-knowledge-graphs-are-becoming-the-brain-of-the-modern-enterprise-1c3419375501](https://medium.com/@adnanmasood/from-data-to-decisions-how-knowledge-graphs-are-becoming-the-brain-of-the-modern-enterprise-1c3419375501)
19. Top Ten Challenges Towards Agentic Neural Graph Databases \- arXiv, accessed September 5, 2025, [https://arxiv.org/pdf/2501.14224?](https://arxiv.org/pdf/2501.14224)
20. Knowledge Graphs as Context Sources for LLM-Based Explanations of Learning Recommendations \- Semantic Scholar, accessed September 5, 2025, [https://www.semanticscholar.org/paper/Knowledge-Graphs-as-Context-Sources-for-LLM-Based-Abu-Rasheed-Weber/182921694e351be521fa895e6741287a1a1cbc78](https://www.semanticscholar.org/paper/Knowledge-Graphs-as-Context-Sources-for-LLM-Based-Abu-Rasheed-Weber/182921694e351be521fa895e6741287a1a1cbc78)



下面是关于最近（近两年及正在做的）在 “KG agent / KG + RL / KG + agent + LLM” 方向的一些代表性研究工作 + 实现思路，以及它们和你的思路相比、可以借鉴／差异的地方。

---

## 近期代表性工作列表

| 名称                                                                                                   | 出处 / 年份                                                                                                                                                        | 核心思路／贡献                                                                                                                                                                                                                                                                                                                                       | 和你思路的关联／差别                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Graphs Meet AI Agents: Taxonomy, Progress, and Future**                                        | arXiv, 2025 ([arXiv](https://arxiv.org/html/2506.18019v1?utm_source=chatgpt.com "Graphs Meet AI Agents: Taxonomy, Progress, and Future ..."))                            | 一个Survey／Taxonomy，系统梳理 graph 技术如何赋能 AI agent：在规划 (planning)、执行 (execution)、记忆 (memory)、多 agent 协作等方面。对你理解 KG + agent + RL + LLM 的定位有启发作用。 ([arXiv](https://arxiv.org/html/2506.18019v1?utm_source=chatgpt.com "Graphs Meet AI Agents: Taxonomy, Progress, and Future ..."))                                   | 很贴近你的整体设想：graph 提供结构化知识 + agent 做决策 + RL 或者策略搜索；可以帮助定义 agent 功能边界（比如哪些是 memory，哪些是检索/更新等）                                                                                                                      |
| **AgREE: Agentic Reasoning for Knowledge Graph …**                                              | arXiv, 2025 ([arXiv](https://arxiv.org/html/2508.04118v1?utm_source=chatgpt.com "AgREE: Agentic Reasoning for Knowledge Graph ..."))                                     | 一个框架：动态构建新的 KG 三元组，对新出现的实体（emerging entities）做策略性的搜索 + action planning 来扩展知识图谱，而不仅是静态查询。 ([arXiv](https://arxiv.org/html/2508.04118v1?utm_source=chatgpt.com "AgREE: Agentic Reasoning for Knowledge Graph ..."))                                                                                          | 和你设想的 “KG 更新 + 检索（Retrieve + Update）” 很近；你可以参考其“动态构建三元组 + agent 搜索结构”部分来设计你的 “updater”模块或“更新策略”                                                                                                                |
| **KG-Agent: An Efficient Autonomous Agent Framework for Complex Reasoning over Knowledge Graph** | ACL 2025 (实作 + 框架) ([ACL Anthology](https://aclanthology.org/2025.acl-long.468/?utm_source=chatgpt.com "KG-Agent: An Efficient Autonomous Agent Framework for ...")) | 提出一个小型 LLM + 多功能工具箱 + KG executor + 气味 memory 的系统，LLM 主动作出决策(edge 检索、工具调用、内存更新)直到完成 KG 上的复杂推理。使用 code-based 指令 + fine-tune 少量数据。 ([arXiv](https://arxiv.org/abs/2402.11163?utm_source=chatgpt.com "KG-Agent: An Efficient Autonomous Agent Framework for Complex Reasoning over Knowledge Graph")) | 与你设想中 LLM + KG agent 很接近：但是这个更多偏向于推理问答任务 (“复杂问题解答”)，不一定考虑环境交互、RL 的 reward/shaping。你的思路中 RL 智能体主导动作决策 + KG 特征 + 环境（TextWorld/ALFWorld）有更多交互性，可借鉴其 “决策 loop” + memory + executor 设计 |
| **A reinforcement learning-based knowledge graph driver**                                        | 2025 ([科学直接](https://www.sciencedirect.com/science/article/pii/S2352711025000457?utm_source=chatgpt.com "A reinforcement learning-based knowledge graph driver"))    | 用 RL agent 来帮助识别 KG 中缺失的 link，通过路径发现 (path search) 在 KG 中连接两个节点，目的是图补全 / 链接预测类型的任务。 ([科学直接](https://www.sciencedirect.com/science/article/pii/S2352711025000457?utm_source=chatgpt.com "A reinforcement learning-based knowledge graph driver"))                                                             | 差不多是 KG 更新 /补全部分，可以用作 “KG 更新/updater”那里；但可能没有 LLM 作为 baseline 或任务抓取者的角色，也可能交互性 /环境交互较弱                                                                                                                           |
| **REKG-MCTS: Reinforcing LLM Reasoning on Knowledge Graphs**                                     | ACL Findings 2025 ([ACL Anthology](https://aclanthology.org/2025.findings-acl.484.pdf?utm_source=chatgpt.com "REKG-MCTS: Reinforcing LLM Reasoning on Knowledge ..."))   | 在 LLM + KG 上做推理强化：结合蒙特卡洛树搜索 (MCTS) 与 KG 来辅助 LLM 的 reasoning，让结构化的路径搜索 /策略搜索辅助 LLM 作答。 ([ACL Anthology](https://aclanthology.org/2025.findings-acl.484.pdf?utm_source=chatgpt.com "REKG-MCTS: Reinforcing LLM Reasoning on Knowledge ..."))                                                                        | 非常契合“检索 + 决策”的部分；你可以把这种策略用于你的 RAG/ReAct 控制器里 “retriever + planner” 部分；但可能 RL 插手路径探索的力度不够、或者没有完整的更新 KG 的机制                                                                                             |

---

## 趋势＋可借鉴的研究方向

从这些工作中，可以总结一些趋势 /较新方向，对你设计智能体 + RAG/ReAct + KG 更新 /检索结合很有参考：

1. **动态知识图谱构建**
   不再只用已有静态 KG，而是 agent 在运行过程中能检测哪些实体／边“缺失”或“新出现”，然后主动更新。AgREE 是一个例子。这个部分你可以设计“updater policy +置信度 / evidence 收集 +更新消歧义”。
2. **agent + 工具 + memory 的循环决策机制**
   像 KG-Agent 那样，小型 LLM + 执行器 (executor) + memory。这种循环结构（decision → retrieve/path搜索 →更新 memory/KG →下一步）对于你要做 RL 智能体控制检索与更新也很重要。
3. **路径搜索 /策略搜索 /规划在 KG 中的结合**
   用 MCTS / beam search /路径走动的方法来辅助 LLM 或辅助 RL 制定决策路径。例如 REKG-MCTS。这样可以把检索做得更有目的性，不只是纯 recall，而是“为后续动作（更新／选择）做准备”。
4. **少样本／效率优化**
   如 KG-Agent 用少量 fine-tune 样本 +小 LLM 达到不错效果。这是你设计 baseline vs RL 智能体对比时，可以控制样本量或者调参样本量，对照研究的一个维度。
5. **奖励函数中加入结构 /证据／一致性指标**
   在 RL 智能体中，不只是纯粹任务正确率，还要把 KG 中的结构性 /路径长度 /更新质量 /查询效率 /检索延迟等纳入 reward shaping。
6. **门控机制 /阈值 + 模式切换（联合 vs 分离检索/更新）**
   有些工作里检索和更新是耦合的，有的是先检索再更新，或只在满足某些置信度或证据时才更新。你这种思路中“联合 vs 解耦”部分，就可以从这些工作中找参考。

---

## 可深入阅读的几篇建议

若要对比、吸收细节实作，我推荐你重点读下面这些，并思考它们的模块接口／决策循环怎样做的：

* **KG-Agent: An Efficient Autonomous Agent Framework for Complex Reasoning over Knowledge Graph** — 理解它的决策 loop, memory/工具箱/executor 接口设计。 ([arXiv](https://arxiv.org/abs/2402.11163?utm_source=chatgpt.com "KG-Agent: An Efficient Autonomous Agent Framework for Complex Reasoning over Knowledge Graph"))
* **AgREE: Agentic Reasoning for Knowledge Graph** — 新实体的动态三元组构建 + action planning + agent 搜索策略。 ([arXiv](https://arxiv.org/html/2508.04118v1?utm_source=chatgpt.com "AgREE: Agentic Reasoning for Knowledge Graph ..."))
* **REKG-MCTS: Reinforcing LLM Reasoning on Knowledge Graphs** — support 检索 +路径搜索辅助的方式，如何和 LLM 互动。 ([ACL Anthology](https://aclanthology.org/2025.findings-acl.484.pdf?utm_source=chatgpt.com "REKG-MCTS: Reinforcing LLM Reasoning on Knowledge ..."))
