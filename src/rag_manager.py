import os
import sys
import glob
import argparse
import json
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from lateral_thinking import LateralEngine, Context7

# Configuration
# Using a relative path for portability within the project structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PERSIST_DIRECTORY = os.path.join(DATA_DIR, "db")

# Source Directories
SOURCE_DIRECTORIES = [
    DATA_DIR
]

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

# Model Configuration
# Stella 1.5B v5 - High performance local model
MODEL_NAME = "dunzhang/stella_en_1.5B_v5"
# User requested CUDA 12.8 support, defaulting to CUDA
DEFAULT_DEVICE = "cuda"

class StellaEmbeddings(Embeddings):
    def __init__(self, model_name, device="cpu", **kwargs):
        print(f"Loading Stella model: {model_name} on {device}...")
        self.model = SentenceTransformer(model_name, trust_remote_code=True, device=device, **kwargs)
        self.normalize = True

    def embed_documents(self, texts):
        # Batching is handled by SentenceTransformer, but we can also rely on Chroma's batching
        embeddings = self.model.encode(texts, normalize_embeddings=self.normalize)
        return embeddings.tolist()

    def embed_query(self, text):
        embedding = self.model.encode(text, normalize_embeddings=self.normalize)
        return embedding.tolist()

def get_embedding_function(device=None):
    if device is None:
        device = DEFAULT_DEVICE
    return StellaEmbeddings(MODEL_NAME, device=device)

def get_files(source_dirs):
    files = []
    for dir_path in source_dirs:
        if os.path.exists(dir_path):
            files.extend(glob.glob(os.path.join(dir_path, "**/*.md"), recursive=True))
    return files

def load_documents(files):
    documents = []
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Metadata Extraction
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                filename = os.path.basename(file_path)
                
                # Determine type based on directory or filename
                doc_type = "unknown"
                if "syllabus" in filename.lower():
                    doc_type = "admin"
                elif filename.endswith(".md"):
                    doc_type = "source"
                
                meta = {
                    "source": filename,
                    "path": rel_path,
                    "type": doc_type
                }
                documents.append(Document(page_content=content, metadata=meta))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return documents

def ingest_data(force=False, device=None):
    print(f"Starting ingestion process...")
    print(f"Persist Directory: {PERSIST_DIRECTORY}")
    
    # Initialize Embedding Function
    embedding_function = get_embedding_function(device=device)
    
    # Load Documents
    files = get_files(SOURCE_DIRECTORIES)
    print(f"Found {len(files)} files.")
    documents = load_documents(files)
    
    if not documents:
        print("No documents found to ingest.")
        return

    # Chunking
    print("Chunking documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    # Lateral Enrichment
    print("Enriching chunks with Lateral Context7...")
    lateral_engine = LateralEngine()
    enriched_chunks = []
    for chunk in chunks:
        enriched_chunks.append(lateral_engine.enrich_document(chunk))
    chunks = enriched_chunks

    # Indexing
    print("Indexing to ChromaDB...")
    
    if force and os.path.exists(PERSIST_DIRECTORY):
        print("Force flag set. Removing existing database...")
        import shutil
        shutil.rmtree(PERSIST_DIRECTORY)

    # Initialize vector store with the first batch or empty
    vector_store = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedding_function
    )

    # Batch processing
    BATCH_SIZE = 10
    total_chunks = len(chunks)
    print(f"Processing {total_chunks} chunks in batches of {BATCH_SIZE}...")

    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        print(f"  - Processing batch {i // BATCH_SIZE + 1}/{(total_chunks + BATCH_SIZE - 1) // BATCH_SIZE} (Chunks {i} to {min(i + BATCH_SIZE, total_chunks)})...")
        vector_store.add_documents(documents=batch)
        
    print("Ingestion complete.")

class ContextWeaver:
    """
    Implements the 'Lateral Thinking' engine by weaving together
    direct focus results with broader contextual 'shadow' results.
    """
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def weave(self, query_text, k=5):
        # 1. Focus Vector (The Direct Query)
        # Instruction: "Represent this specific question for precise retrieval."
        focus_query = f"Represent this specific question for precise retrieval: {query_text}"
        focus_results = self.vector_store.similarity_search(focus_query, k=k)

        # 2. Shadow Vector (The Context/Implication)
        # Instruction: "Represent the broad context, themes, and implications of this concept."
        shadow_query = f"Represent the broad context, themes, and implications of this concept: {query_text}"
        # Use MMR to find diverse, non-obvious connections
        shadow_results = self.vector_store.max_marginal_relevance_search(
            shadow_query, k=k, fetch_k=k*4, lambda_mult=0.3 # Lower lambda = more diversity
        )

        # 3. Weave Results (Interleave)
        # Strategy: 2 Focus, 1 Shadow, 2 Focus, 1 Shadow...
        woven_results = []
        focus_idx, shadow_idx = 0, 0
        
        seen_content = set()

        while len(woven_results) < k:
            # Add Focus (Priority)
            if focus_idx < len(focus_results):
                doc = focus_results[focus_idx]
                if doc.page_content not in seen_content:
                    doc.metadata["retrieval_layer"] = "focus"
                    woven_results.append(doc)
                    seen_content.add(doc.page_content)
                focus_idx += 1
            
            # Add Shadow (Context) - Every 3rd item or if focus runs out
            if (len(woven_results) % 3 == 2 or focus_idx >= len(focus_results)) and shadow_idx < len(shadow_results):
                doc = shadow_results[shadow_idx]
                if doc.page_content not in seen_content:
                    doc.metadata["retrieval_layer"] = "shadow_context"
                    woven_results.append(doc)
                    seen_content.add(doc.page_content)
                shadow_idx += 1
            
            # Break if both exhausted
            if focus_idx >= len(focus_results) and shadow_idx >= len(shadow_results):
                break
                
        return woven_results[:k]

def query_knowledge_base(query_text, mode="foundation", device=None):
    print(f"Querying ({mode}): {query_text}")
    
    embedding_function = get_embedding_function(device=device)
    vector_store = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding_function)
    
    results = []
    
    if mode == "foundation":
        # Protocol 1: Outline-Driven / General
        # Instruction: "Represent this outline point for retrieving foundational concepts and definitions."
        # Note: Stella might handle instructions differently, but we'll prepend for semantic clarity if model supports it.
        # For Stella v5, prompts are often implicit or handled via specific prompt templates if using the s2p/p2p logic.
        # We will stick to direct queries for now unless we implement the specific prompt templates.
        # Adding a prefix manually to the query text:
        enhanced_query = f"Represent this outline point for retrieving foundational concepts and definitions: {query_text}"
        docs = vector_store.similarity_search(enhanced_query, k=10)
        results = docs

    elif mode == "lateral":
        # Protocol 2: Lateral Link (Innovation) via LateralEngine
        lateral_engine = LateralEngine(vector_store=vector_store)
        results = lateral_engine.weave_results(query_text, k=5)

    elif mode == "factcheck":
        # Protocol 3: Fact Checker
        # Instruction: "Represent this claim to find the exact supporting evidence or source text."
        enhanced_query = f"Represent this claim to find the exact supporting evidence or source text: {query_text}"
        docs = vector_store.similarity_search(enhanced_query, k=3)
        results = docs
        
    else:
        print(f"Unknown mode: {mode}. Defaulting to similarity search.")
        docs = vector_store.similarity_search(query_text, k=5)
        results = docs

    # Output JSON for Agent
    output_data = []
    for doc in results:
        output_data.append({
            "content": doc.page_content,
            "metadata": doc.metadata
        })
    
    # print(json.dumps(output_data, indent=2)) # Deprecated for library usage
    return output_data

def get_vector_store(device=None):
    """Returns the Chroma vector store instance."""
    embedding_function = get_embedding_function(device=device)
    return Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding_function)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Librarian Sub-Agent RAG Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents into the vector database")
    ingest_parser.add_argument("--force", action="store_true", help="Force re-indexing")
    ingest_parser.add_argument("--device", type=str, default="cuda", help="Device to use (cpu, cuda)")

    # Query Command
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument("text", type=str, help="Query text")
    query_parser.add_argument("--mode", type=str, default="foundation", choices=["foundation", "lateral", "factcheck"], help="Retrieval mode")
    query_parser.add_argument("--device", type=str, default="cuda", help="Device to use (cpu, cuda)")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest_data(force=args.force, device=args.device)
    elif args.command == "query":
        results = query_knowledge_base(args.text, mode=args.mode, device=args.device)
        print(json.dumps(results, indent=2))
    else:
        parser.print_help()
