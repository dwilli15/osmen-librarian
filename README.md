# OsMEN Librarian

<p align="center">
  <strong>🧠 Semantic Memory & Lateral Thinking Engine for the OsMEN Ecosystem</strong>
</p>

<p align="center">
  <a href="https://github.com/dwilli15/OsMEN"><img src="https://img.shields.io/badge/OsMEN-Multi--Agent%20Platform-blue?style=for-the-badge" alt="OsMEN Platform"></a>
  <a href="#"><img src="https://img.shields.io/badge/Version-2.0.0-green?style=for-the-badge" alt="Version 2.0.0"></a>
  <a href="#"><img src="https://img.shields.io/badge/Tests-69%20Passing-brightgreen?style=for-the-badge" alt="Tests Passing"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="https://github.com/dwilli15/OsMEN"><img src="https://img.shields.io/badge/Part%20of-OsMEN-ff6b6b?style=flat-square" alt="Part of OsMEN"></a>
  <a href="#"><img src="https://img.shields.io/badge/LangGraph-Powered-purple?style=flat-square" alt="LangGraph"></a>
  <a href="#"><img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-orange?style=flat-square" alt="ChromaDB"></a>
  <a href="#"><img src="https://img.shields.io/badge/License-Apache%202.0-lightgrey?style=flat-square" alt="License"></a>
</p>

---

> **Part of the [OsMEN (OS Management and Engagement Network)](https://github.com/dwilli15/OsMEN) multi-agent ecosystem**

A production-ready RAG (Retrieval-Augmented Generation) system featuring **lateral thinking**, **multi-mode retrieval**, and **LangGraph orchestration**. Designed as both a **standalone knowledge management tool** and a **core dependency** of the OsMEN agent framework.

## 🔗 OsMEN Ecosystem

| Project | Description | Link |
|---------|-------------|------|
| **OsMEN** | Multi-agent orchestration platform | [github.com/dwilli15/OsMEN](https://github.com/dwilli15/OsMEN) |
| **OsMEN Librarian** | RAG & lateral thinking engine (this repo) | You are here |

---

## ✨ Key Features

### 🎯 Three Retrieval Modes

| Mode | Purpose | Algorithm |
|------|---------|-----------|
| **Foundation** | Populate new sections with core concepts | Top-K Cosine Similarity |
| **Lateral** | Cross-disciplinary creative connections | MMR (λ=0.5) diversity |
| **Factcheck** | High-precision citation verification | Top-3 precision search |

### 🧠 LangGraph Orchestration

- **StateGraph** pattern with 15-field `AgentState`
- Conditional routing based on query mode
- Human-in-the-loop (HITL) interrupt support
- Checkpointing for conversation persistence

### 🔧 DeepAgents Middleware

- Pluggable tool injection via `MiddlewareStack`
- Filesystem operations, todo management, subagent spawning
- Lifecycle hooks (pre/post invoke)

### 🤖 Specialized Subagents

- **FactChecker** - Citation verification
- **LateralResearcher** - Cross-disciplinary exploration
- **Summarizer** - Document compression
- **Executor** - Sandboxed code execution

### 📊 Production Features

- OpenAI Assistants API compatibility
- FastAPI server with full REST endpoints
- CLI with rich terminal output
- LangSmith/Langfuse tracing integration
- MCP (Model Context Protocol) server

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- 8GB+ RAM (16GB recommended for GPU)
- NVIDIA GPU with CUDA (optional but recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/dwilli15/osmen-librarian.git
cd osmen-librarian

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### GPU Support (Recommended)

> ⚠️ **CRITICAL**: Default installation is CPU-only. For NVIDIA GPU acceleration:

```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### Ingest Documents

```bash
# Ingest all markdown files from data/
python -m src.cli ingest ./data --recursive
```

### Query Your Knowledge Base

```bash
# Foundation mode - core concepts
python -m src.cli query "What is intersubjectivity?" --mode foundation

# Lateral mode - creative connections
python -m src.cli query "therapeutic alliance" --mode lateral

# Factcheck mode - precise citations
python -m src.cli query "attachment theory statistics" --mode factcheck
```

### Start the API Server

```bash
python -m src.cli serve --port 8000
# API available at http://localhost:8000
# OpenAPI docs at http://localhost:8000/docs
```

---

## 📁 Project Structure

```
osmen-librarian/
├── src/
│   ├── graph.py              # LangGraph orchestration
│   ├── memory.py             # Checkpointer factory
│   ├── store.py              # CompositeStore routing
│   ├── tracing.py            # Observability layer
│   ├── cli.py                # Command-line interface
│   ├── app.py                # FastAPI application
│   ├── mcp_server.py         # MCP server with Assistants tools
│   ├── rag_manager.py        # Core RAG engine
│   │
│   ├── middleware/           # DeepAgents middleware
│   │   ├── base.py           # AgentMiddleware, MiddlewareStack
│   │   ├── filesystem.py     # File operations
│   │   ├── todo.py           # Todo management
│   │   ├── subagent.py       # Delegation tools
│   │   └── hitl.py           # Human-in-the-loop
│   │
│   ├── subagents/            # Specialized agents
│   │   ├── base.py           # SubagentBase, registry
│   │   ├── fact_checker.py   # Citation verification
│   │   ├── lateral_researcher.py
│   │   ├── summarizer.py     
│   │   └── executor.py       
│   │
│   ├── retrieval/            # Retriever implementations
│   │   ├── interfaces.py     # RetrieverBase, DocumentChunk
│   │   └── chroma.py         # ChromaRetriever
│   │
│   ├── assistants/           # OpenAI Assistants API
│   │   ├── schema.py         # Data models
│   │   └── storage.py        # Backends
│   │
│   └── tests/                # Test suite
│       ├── test_middleware.py
│       ├── test_subagents.py
│       ├── test_retrieval.py
│       └── test_integration.py
│
├── data/                     # Knowledge base documents
│   └── db/                   # ChromaDB persistence
│
├── docs/                     # Documentation
│   └── subagent_librarian_protocols.md
│
├── pyproject.toml           # Project configuration
├── requirements.txt         # Dependencies
└── .env.example             # Environment template
```

---

## 🔌 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status |
| `/query` | POST | RAG query |
| `/ingest` | POST | Document ingestion |

### Assistants API (OpenAI-compatible)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/assistants` | GET/POST | List/create assistants |
| `/assistants/{id}` | GET/DELETE | Assistant operations |
| `/threads` | POST | Create conversation thread |
| `/threads/{id}` | GET | Get thread with messages |
| `/threads/{id}/messages` | POST | Add message |
| `/threads/{id}/runs` | POST | Execute with assistant |

### Graph Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/graph/invoke` | POST | Direct LangGraph invocation |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest src/tests/test_retrieval.py -v
```

**Test Status**: 69 passed, 3 skipped ✅

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LIBRARIAN_DATA_DIR` | Knowledge base location | `./data` |
| `LIBRARIAN_DB_PATH` | ChromaDB persistence | `./data/db` |
| `LIBRARIAN_EMBEDDING_MODEL` | Embedding model | `dunzhang/stella_en_1.5B_v5` |
| `LANGSMITH_API_KEY` | LangSmith tracing (optional) | - |
| `LANGSMITH_PROJECT` | LangSmith project name | `librarian` |

### Embedding Model

Default: **Stella 1.5B** (`dunzhang/stella_en_1.5B_v5`)
- Near-SOTA performance
- Optimized for RTX 3060+ (8GB VRAM)
- Fallback: CPU mode with reduced speed

---

## 🔗 Integration with OsMEN

### As a Standalone Tool

```python
from src.retrieval import ChromaRetriever
from src.graph import compile_graph, AgentState

# Initialize retriever
retriever = ChromaRetriever(persist_dir="./data/db")

# Compile graph with checkpointing
graph = compile_graph(retriever=retriever)

# Execute query
result = graph.invoke({
    "query": "therapeutic alliance",
    "mode": "lateral"
})
```

### As an OsMEN Dependency

```python
# In OsMEN agent configuration
from osmen_librarian import ChromaRetriever, compile_graph

# The Librarian becomes a specialized subagent
knowledge_agent = compile_graph(
    retriever=ChromaRetriever(persist_dir="/path/to/knowledge"),
    checkpointer=osmen_checkpointer
)
```

---

## 📚 Documentation

- [Implementation Status](./implementation_status.md) - Detailed module tracking
- [Subagent Protocols](./docs/subagent_librarian_protocols.md) - RAG retrieval protocols
- [Agent Setup](./AGENT_SETUP.md) - Automated setup instructions
- [OsMEN Documentation](https://github.com/dwilli15/OsMEN) - Parent project docs

---

## 🗺️ Roadmap

### ✅ Completed (v2.0)
- [x] LangGraph orchestration
- [x] Three retrieval modes
- [x] Middleware architecture
- [x] Subagent framework
- [x] Assistants API compatibility
- [x] FastAPI server
- [x] CLI interface
- [x] 69 passing tests

### 🚧 Planned
- [ ] Docker containerization
- [ ] Multi-user support
- [ ] Web UI dashboard
- [ ] Plugin system for custom retrievers
- [ ] Full OsMEN integration package

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [ChromaDB](https://github.com/chroma-core/chroma) - Vector database
- [Sentence-Transformers](https://www.sbert.net/) - Embeddings
- [FastAPI](https://fastapi.tiangolo.com/) - API framework

Part of the **[OsMEN](https://github.com/dwilli15/OsMEN)** multi-agent ecosystem.

---

<p align="center">
  <strong>🧠 Knowledge is power. Lateral thinking is innovation.</strong>
</p>

<p align="center">
  <a href="https://github.com/dwilli15/OsMEN">⬅️ Back to OsMEN</a>
</p>
