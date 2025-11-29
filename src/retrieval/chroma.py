"""
ChromaDB Retriever Implementation.

Provides ChromaDB-based vector store retrieval with:
- Stella embeddings (CUDA accelerated)
- Semantic similarity search
- Document ingestion and management
"""

from typing import Any, Dict, List, Optional, Sequence
import logging
import os
import asyncio

from .interfaces import (
    RetrieverBase,
    RetrieverConfig,
    RetrievalResult,
    DocumentChunk,
    SearchMode,
    SimpleChunker,
)

logger = logging.getLogger("librarian.retrieval.chroma")

# Lazy imports for heavy dependencies
_chromadb = None
_embeddings = None


def _get_chromadb():
    """Lazy load chromadb."""
    global _chromadb
    if _chromadb is None:
        import chromadb
        _chromadb = chromadb
    return _chromadb


def get_embedding_model(config: RetrieverConfig):
    """
    Get or create embedding model.
    
    Uses HuggingFace embeddings with Stella model.
    """
    global _embeddings
    if _embeddings is not None:
        return _embeddings
    
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        
        model_kwargs = {"device": config.embedding_device}
        if config.trust_remote_code:
            model_kwargs["trust_remote_code"] = True
        
        _embeddings = HuggingFaceEmbeddings(
            model_name=config.embedding_model,
            model_kwargs=model_kwargs,
            encode_kwargs={"normalize_embeddings": True}
        )
        
        logger.info(
            f"Loaded embedding model {config.embedding_model} "
            f"on {config.embedding_device}"
        )
        return _embeddings
        
    except Exception as e:
        logger.error(f"Failed to load embeddings: {e}")
        raise


class ChromaRetriever(RetrieverBase):
    """
    ChromaDB-based retriever implementation.
    
    Features:
    - Persistent vector storage
    - Stella embeddings (1.5B params, GPU)
    - Semantic similarity search
    - Metadata filtering
    """

    def __init__(self, config: Optional[RetrieverConfig] = None):
        super().__init__(config)
        self._client = None
        self._collection = None
        self._embeddings = None
        self._chunker = SimpleChunker()

    async def initialize(self) -> None:
        """Initialize async (wraps sync)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.initialize_sync)

    def initialize_sync(self) -> None:
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return
        
        chromadb = _get_chromadb()
        
        # Ensure directory exists
        persist_dir = self.config.persist_directory
        os.makedirs(persist_dir, exist_ok=True)
        
        # Create persistent client
        self._client = chromadb.PersistentClient(path=persist_dir)
        
        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embeddings
        self._embeddings = get_embedding_model(self.config)
        
        self._initialized = True
        logger.info(
            f"ChromaRetriever initialized: "
            f"collection={self.config.collection_name}, "
            f"docs={self._collection.count()}"
        )

    def _ensure_initialized(self):
        """Ensure retriever is initialized."""
        if not self._initialized:
            self.initialize_sync()

    async def retrieve(
        self,
        query: str,
        k: int = 5,
        mode: Optional[SearchMode] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """Async retrieval."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.retrieve_sync(query, k, mode, filters)
        )

    def retrieve_sync(
        self,
        query: str,
        k: int = 5,
        mode: Optional[SearchMode] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """
        Retrieve documents using semantic search.
        
        Args:
            query: Search query
            k: Number of results
            mode: Search mode (semantic default)
            filters: Metadata filters
        
        Returns:
            RetrievalResult with matching chunks
        """
        self._ensure_initialized()
        
        k = min(k, self.config.max_k)
        mode = mode or self.config.search_mode
        
        try:
            # Generate query embedding
            query_embedding = self._embeddings.embed_query(query)
            
            # Build query params
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": k
            }
            
            if filters:
                query_params["where"] = filters
            
            # Execute query
            results = self._collection.query(**query_params)
            
            # Parse results
            chunks = []
            if results and results.get("documents"):
                documents = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                ids = results.get("ids", [[]])[0]
                
                for i, doc in enumerate(documents):
                    # Convert distance to similarity score
                    # Chroma uses L2 or cosine distance
                    distance = distances[i] if distances else 0
                    score = 1 - distance if distance < 1 else 1 / (1 + distance)
                    
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    chunk_id = ids[i] if i < len(ids) else f"chunk_{i}"
                    
                    chunk = DocumentChunk(
                        content=doc,
                        metadata=metadata,
                        source=metadata.get("source", ""),
                        chunk_id=chunk_id,
                        score=score
                    )
                    chunks.append(chunk)
            
            # Sort by score descending
            chunks.sort(key=lambda c: c.score, reverse=True)
            
            # Filter by minimum score
            if self.config.min_score > 0:
                chunks = [c for c in chunks if c.score >= self.config.min_score]
            
            return RetrievalResult(
                query=query,
                chunks=chunks,
                mode=mode,
                total_found=len(chunks),
                metadata={"k": k, "filters": filters}
            )
            
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return RetrievalResult(
                query=query,
                chunks=[],
                mode=mode,
                metadata={"error": str(e)}
            )

    async def ingest(
        self,
        documents: Sequence[Dict[str, Any]],
        source: Optional[str] = None
    ) -> int:
        """Async ingestion."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.ingest_sync(documents, source)
        )

    def ingest_sync(
        self,
        documents: Sequence[Dict[str, Any]],
        source: Optional[str] = None
    ) -> int:
        """
        Ingest documents with chunking.
        
        Args:
            documents: List of {"content": str, "metadata": dict}
            source: Optional source name
        
        Returns:
            Number of chunks ingested
        """
        self._ensure_initialized()
        
        all_chunks = []
        all_metadata = []
        all_ids = []
        
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {}).copy()
            
            if source:
                metadata["source"] = source
            
            # Chunk the content
            chunks = self._chunker.chunk(
                content,
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap
            )
            
            for j, chunk in enumerate(chunks):
                chunk_id = f"{source or 'doc'}_{i}_{j}"
                all_chunks.append(chunk)
                all_metadata.append(metadata)
                all_ids.append(chunk_id)
        
        if not all_chunks:
            return 0
        
        try:
            # Generate embeddings
            embeddings = self._embeddings.embed_documents(all_chunks)
            
            # Add to collection
            self._collection.add(
                documents=all_chunks,
                embeddings=embeddings,
                metadatas=all_metadata,
                ids=all_ids
            )
            
            logger.info(f"Ingested {len(all_chunks)} chunks from {len(documents)} docs")
            return len(all_chunks)
            
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            return 0

    async def delete(self, filters: Dict[str, Any]) -> int:
        """Async deletion."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._delete_sync(filters)
        )

    def _delete_sync(self, filters: Dict[str, Any]) -> int:
        """Delete documents matching filters."""
        self._ensure_initialized()
        
        try:
            # Get matching IDs first
            results = self._collection.get(where=filters)
            ids = results.get("ids", [])
            
            if ids:
                self._collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents")
                return len(ids)
            return 0
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return 0

    def count(self) -> int:
        """Get document count."""
        self._ensure_initialized()
        return self._collection.count()

    def health_check(self) -> Dict[str, Any]:
        """Check retriever health."""
        try:
            self._ensure_initialized()
            
            return {
                "status": "healthy",
                "collection": self.config.collection_name,
                "document_count": self._collection.count(),
                "persist_directory": self.config.persist_directory,
                "embedding_model": self.config.embedding_model
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Module-level retriever instance
_retriever: Optional[ChromaRetriever] = None


def get_retriever(config: Optional[RetrieverConfig] = None) -> ChromaRetriever:
    """
    Get or create the default retriever instance.
    
    Args:
        config: Optional configuration
    
    Returns:
        Initialized ChromaRetriever
    """
    global _retriever
    
    if _retriever is None:
        _retriever = ChromaRetriever(config)
        _retriever.initialize_sync()
    
    return _retriever


def reset_retriever():
    """Reset the global retriever instance."""
    global _retriever
    _retriever = None
