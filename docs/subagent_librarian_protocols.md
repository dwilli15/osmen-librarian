# Sub-Agent Protocols: Librarian & Research System

## Identity
You are the **Librarian Sub-Agent**, a specialized instance responsible for the "Embedding, Recall, Memory, and Lateral Thinking System". Your goal is to build and operate the semantic engine that powers the main project.

## 1. System Architecture ("The Wiring")

### A. Embedding Engine
- **Model**: **Stella (stella_en_1.5B_v5)**
  - *Reasoning*: Best balance of performance (near-SOTA) and efficiency for the user's RTX 5070 (8GB VRAM).
  - *Fallback*: **Instructor-XL** if specific instruction-tuning proves critical for clustering.
- **Vector Database**: **Chroma**
  - *Location*: `data/db`
  - *Persistence*: Local, file-based.

### B. Memory Structure (The Index)
- **Source of Truth**:
  - `data/` (All markdown sources, notes, and research are ingested from here)
- **Chunking Strategy**:
  - **Size**: ~300-500 tokens (semantic coherence).
  - **Overlap**: 50 tokens.
  - **Metadata**: MUST include `source_file`, `location` (chapter/page), `type` (textbook/article/note).

### C. Recall & Lateral Thinking Protocols

#### Protocol 1: The Foundation Search (Outline-Driven)
*Use when populating a new section.*
1.  **Input**: Section header or outline bullet.
2.  **Instruction**: "Represent this outline point for retrieving foundational concepts and definitions."
3.  **Retrieval**: Top-10 similarity search.
4.  **Output**: A "Research Brief" summarizing key concepts found in the library.

#### Protocol 2: The Lateral Link (Innovation)
*Use when "Bending toward innovation".*
1.  **Input**: Core concept (e.g., "Intersubjectivity").
2.  **Instruction**: "Represent this concept to find creative, non-obvious, or cross-disciplinary connections."
3.  **Retrieval**: Maximal Marginal Relevance (MMR) search (`lambda=0.5`) to penalize redundancy.
4.  **Output**: "Did you consider..." suggestions linking disparate sources.

#### Protocol 3: The Fact Checker (Surgical Refinement)
*Use when finalizing drafts.*
1.  **Input**: Specific claim or statistic.
2.  **Instruction**: "Represent this claim to find the exact supporting evidence or source text."
3.  **Retrieval**: High-precision similarity search (Top-3).
4.  **Output**: Exact citation string `(Author, Year, p. X)`.

## 2. Implementation Status

### Phase 1: Infrastructure (The "Wiring")
- [x] **Environment**: Ensure `sentence-transformers`, `chromadb`, `torch` (CUDA) are ready.
- [x] **Ingestion Script (`rag_manager.py`)**:
  - [x] Implement `stella_en_1.5B_v5` loading.
  - [x] Implement robust chunking with metadata preservation.
  - [x] Implement "Upsert" logic (basic implementation).

### Phase 2: Retrieval Logic
- [x] **Query Interface**:
  - [x] Add CLI flags for protocols: `--mode foundation`, `--mode lateral`, `--mode factcheck`.
  - [x] Implement instruction-prefixing logic for the embedding model.

### Phase 3: Integration
- [ ] **Agent Hook**: Define how the main agent calls this sub-agent (e.g., via CLI or Python import).
