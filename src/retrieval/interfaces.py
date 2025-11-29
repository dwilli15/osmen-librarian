"""
Retrieval Interfaces.

Provides abstract base classes and protocols for retrieval implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence
from enum import Enum
import logging

logger = logging.getLogger("librarian.retrieval.interfaces")


class SearchMode(Enum):
    """Search mode for retrieval."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class DocumentChunk:
    """A chunk of document content with metadata."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    chunk_id: str = ""
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "chunk_id": self.chunk_id,
            "score": self.score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        """Create from dictionary."""
        return cls(
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            source=data.get("source", ""),
            chunk_id=data.get("chunk_id", ""),
            score=data.get("score", 0.0)
        )


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    query: str
    chunks: List[DocumentChunk]
    mode: SearchMode = SearchMode.SEMANTIC
    total_found: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "chunks": [c.to_dict() for c in self.chunks],
            "mode": self.mode.value,
            "total_found": self.total_found,
            "metadata": self.metadata
        }
    
    @property
    def top_chunk(self) -> Optional[DocumentChunk]:
        """Get highest scoring chunk."""
        if not self.chunks:
            return None
        return max(self.chunks, key=lambda c: c.score)
    
    @property
    def sources(self) -> List[str]:
        """Get unique sources."""
        return list(set(c.source for c in self.chunks if c.source))


@dataclass
class RetrieverConfig:
    """Configuration for retriever."""
    # Vector store settings
    collection_name: str = "librarian_knowledge"
    persist_directory: str = "./data/db"
    
    # Embedding settings
    embedding_model: str = "dunzhang/stella_en_1.5B_v5"
    embedding_device: str = "cuda"
    trust_remote_code: bool = True
    
    # Retrieval settings
    default_k: int = 5
    max_k: int = 20
    min_score: float = 0.0
    
    # Search settings
    search_mode: SearchMode = SearchMode.SEMANTIC
    hybrid_alpha: float = 0.5  # Balance between semantic and keyword
    
    # Chunking settings (for ingestion)
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "embedding_model": self.embedding_model,
            "embedding_device": self.embedding_device,
            "default_k": self.default_k,
            "max_k": self.max_k,
            "min_score": self.min_score,
            "search_mode": self.search_mode.value,
            "hybrid_alpha": self.hybrid_alpha,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }


class RetrieverBase(ABC):
    """
    Abstract base class for retrievers.
    
    Provides standardized interface for:
    - Document retrieval (semantic, keyword, hybrid)
    - Document ingestion
    - Collection management
    """

    def __init__(self, config: Optional[RetrieverConfig] = None):
        """Initialize retriever with config."""
        self.config = config or RetrieverConfig()
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize retriever resources (async)."""
        pass

    @abstractmethod
    def initialize_sync(self) -> None:
        """Initialize retriever resources (sync)."""
        pass

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        k: int = 5,
        mode: Optional[SearchMode] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """
        Retrieve relevant documents.
        
        Args:
            query: Search query
            k: Number of results
            mode: Search mode (semantic/keyword/hybrid)
            filters: Metadata filters
        
        Returns:
            RetrievalResult with matching chunks
        """
        pass

    @abstractmethod
    def retrieve_sync(
        self,
        query: str,
        k: int = 5,
        mode: Optional[SearchMode] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """Synchronous retrieval."""
        pass

    @abstractmethod
    async def ingest(
        self,
        documents: Sequence[Dict[str, Any]],
        source: Optional[str] = None
    ) -> int:
        """
        Ingest documents into the retriever.
        
        Args:
            documents: List of document dicts with 'content' and 'metadata'
            source: Optional source identifier
        
        Returns:
            Number of chunks ingested
        """
        pass

    @abstractmethod
    def ingest_sync(
        self,
        documents: Sequence[Dict[str, Any]],
        source: Optional[str] = None
    ) -> int:
        """Synchronous ingestion."""
        pass

    @abstractmethod
    async def delete(
        self,
        filters: Dict[str, Any]
    ) -> int:
        """
        Delete documents matching filters.
        
        Args:
            filters: Metadata filters for deletion
        
        Returns:
            Number of documents deleted
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Get document count in collection."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check retriever health and status."""
        pass


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        ...
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        ...


class ChunkerProtocol(Protocol):
    """Protocol for document chunkers."""
    
    def chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """Chunk text into smaller pieces."""
        ...


class SimpleChunker:
    """Simple text chunker with overlap."""
    
    def chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """
        Chunk text into overlapping pieces.
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < text_len:
                # Look for sentence end within last 20% of chunk
                search_start = end - int(chunk_size * 0.2)
                for sep in ['. ', '.\n', '!\n', '?\n', '\n\n']:
                    pos = text.rfind(sep, search_start, end)
                    if pos > search_start:
                        end = pos + len(sep)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start <= 0 or end >= text_len:
                break
        
        return chunks
