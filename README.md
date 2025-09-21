<div align="center">
<h1>🍳食谱问答系统 CookRAG </h1>
<p>
<img src="https://img.shields.io/badge/Python-3.12%2B-blue" alt="Python版本">
<img src="https://img.shields.io/badge/RAG-Markdown-orange" alt="RAG类型">
<img src="https://img.shields.io/badge/VectorStore-FAISS-yellow" alt="向量存储">
<img src="https://img.shields.io/badge/LLM-Kimi-lightgrey" alt="LLM支持">
</p>
</div>

## 🎯 项目目标与定位

本项目旨在在实践中巩固学习和理解RAG（Retrieval-Augmented Generation，检索增强生成）技术。在接触如 [Dify](https://dify.ai/)、[RAGFlow](https://github.com/infiniflow/ragflow) 这类高度封装的RAG框架之前，通过本项目的源码和实践，可以：

*   **熟悉RAG核心组件**：亲身体验文本加载、切分、向量化、向量存储与检索（本项目使用FAISS）、大模型集成等关键环节。
*   **理解RAG基本流程**：从底层脚本层面观察数据如何在RAG系统中流转和处理。
*   **进行初步优化与测试**：尝试调整参数、替换模型、优化提示词等，直观感受不同策略对结果的影响。

掌握这些基础后，能更有的放矢地使用高级RAG框架的API进行针对性调优或定制开发。

## 🔧 系统架构

```mermaid
graph TD
    subgraph "用户交互层"
        A[用户输入查询] --> B{查询类型判断}
        B --> |列表查询| C[列表模式]
        B --> |详细查询| D[详细模式]
        B --> |一般查询| E[基础模式]
    end
    
    subgraph "数据准备模块 (DataPreparationModule)"
        F[Markdown文档加载] --> G[元数据增强]
        G --> H[Markdown结构感知分块]
        H --> I[父子文档映射建立]
        I --> J[文档统计信息生成]
    end
    
    subgraph "索引构建模块 (IndexConstructionModule)"
        K[BGE-small-zh-v1.5嵌入模型] --> L[文档向量化]
        L --> M[FAISS向量索引构建]
        M --> N[索引持久化存储]
    end
    
    subgraph "检索优化模块 (RetrievalOptimizationModule)"
        O[向量检索器] --> P[混合检索策略]
        Q[BM25检索器] --> P
        P --> R[RRF重排序算法]
        R --> S[元数据过滤]
        S --> T[最终检索结果]
    end
    
    subgraph "生成集成模块 (GenerationIntegrationModule)"
        U[查询路由分类] --> V{路由类型}
        V --> |list| W[智能查询重写]
        V --> |detail/general| X[查询重写]
        W --> Y[KimiLLM生成]
        X --> Y
        Y --> Z[流式/普通输出]
    end
    
    subgraph "系统主控制器 (RecipeRAGSystem)"
        AA[系统初始化] --> BB[知识库构建]
        BB --> CC[交互式问答循环]
        CC --> DD[结果输出]
    end
    
    %% 数据流向
    F --> K
    H --> O
    H --> Q
    A --> U
    T --> Y
    Y --> DD
    
    %% 配置管理
    EE[RAGConfig配置] --> AA
    EE --> K
    EE --> Y
    
    %% 存储层
    FF[FAISS向量库] --> M
    GG[文档元数据] --> G
    HH[父子映射关系] --> I
```

## 🚀 使用方法

### 环境准备

1.  **创建并激活虚拟环境**:
    ```bash
    conda create -n cookRAG python=3.12.7
    conda activate cookRAG
    ```
2.  **安装依赖项**:
    ```bash
    cd normRAG
    pip install -r requirements.txt
    ```
3.  **配置Kimi API密钥**:
    在电脑“设置”中

### 启动服务

```bash
python main.py
```
