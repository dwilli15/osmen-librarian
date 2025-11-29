# OsMEN Librarian - Agent Setup Guide

> **Part of the [OsMEN](https://github.com/dwilli15/OsMEN) multi-agent ecosystem**

This guide is for AI agents setting up the OsMEN Librarian for the first time.

## Quick Setup (5 minutes)

### Step 1: Clone and Navigate

```bash
git clone https://github.com/dwilli15/osmen-librarian.git
cd osmen-librarian
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: GPU Support (Recommended)

If you have an NVIDIA GPU with CUDA:

```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

Replace `cu124` with your CUDA version (cu118, cu121, etc.).

### Step 5: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your preferences. Most defaults work out of the box.

### Step 6: Verify Installation

```bash
python -c "from src.rag_manager import RAGManager; print('✅ Installation successful')"
```

### Step 7: Ingest Sample Data

```bash
python -m src.cli ingest ./data --recursive
```

### Step 8: Test Query

```bash
python -m src.cli query "What is the main concept here?" --mode foundation
```

---

## Test Suite Verification

Run the full test suite to verify everything works:

```bash
pytest -v
```

Expected result: **69 passed, 3 skipped**

---

## Common Issues

### CUDA Not Available

If GPU is not detected:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

Ensure you installed the CUDA-enabled PyTorch, not the CPU version.

### Import Errors

Make sure your virtual environment is activated:
```bash
# Check current Python
which python  # Linux/Mac
where python  # Windows
```

### ChromaDB Errors

If ChromaDB fails to initialize:
```bash
rm -rf ./data/db  # Clear existing DB
python -m src.cli ingest ./data --recursive  # Re-ingest
```

---

## Integration with OsMEN

When integrating with the main OsMEN platform:

```python
from osmen_librarian import ChromaRetriever, compile_graph

# Create the Librarian agent
librarian = compile_graph(
    retriever=ChromaRetriever(persist_dir="./data/db")
)

# Use in OsMEN orchestration
result = librarian.invoke({
    "query": "your query",
    "mode": "lateral"  # foundation, lateral, or factcheck
})
```

---

## Resources

- [README.md](./README.md) - Full documentation
- [Implementation Status](./implementation_status.md) - Module details
- [OsMEN Platform](https://github.com/dwilli15/OsMEN) - Parent project
