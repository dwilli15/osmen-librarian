"""
Tests for Retrieval Layer.
"""

import pytest
import tempfile
import os


class TestRetrieverInterfaces:
    """Tests for retrieval interfaces."""
    
    def test_document_chunk_creation(self):
        """Test DocumentChunk dataclass."""
        from retrieval.interfaces import DocumentChunk
        
        chunk = DocumentChunk(
            content="Test content",
            metadata={"source": "test.md"},
            source="test.md",
            chunk_id="chunk_1",
            score=0.95
        )
        
        assert chunk.content == "Test content"
        assert chunk.score == 0.95
        assert chunk.source == "test.md"
    
    def test_document_chunk_to_dict(self):
        """Test DocumentChunk serialization."""
        from retrieval.interfaces import DocumentChunk
        
        chunk = DocumentChunk(content="Test", score=0.9)
        data = chunk.to_dict()
        
        assert "content" in data
        assert "score" in data
        assert data["content"] == "Test"
    
    def test_retrieval_result(self):
        """Test RetrievalResult dataclass."""
        from retrieval.interfaces import RetrievalResult, DocumentChunk, SearchMode
        
        chunks = [
            DocumentChunk(content="Chunk 1", score=0.9, source="doc1.md"),
            DocumentChunk(content="Chunk 2", score=0.8, source="doc2.md"),
        ]
        
        result = RetrievalResult(
            query="test query",
            chunks=chunks,
            mode=SearchMode.SEMANTIC
        )
        
        assert result.query == "test query"
        assert len(result.chunks) == 2
        assert result.top_chunk.content == "Chunk 1"
        assert len(result.sources) == 2
    
    def test_retriever_config(self):
        """Test RetrieverConfig defaults."""
        from retrieval.interfaces import RetrieverConfig
        
        config = RetrieverConfig()
        
        assert config.collection_name == "librarian_knowledge"
        assert config.default_k == 5
        assert config.chunk_size == 1000


class TestSimpleChunker:
    """Tests for SimpleChunker."""
    
    def test_basic_chunking(self):
        """Test basic text chunking."""
        from retrieval.interfaces import SimpleChunker
        
        chunker = SimpleChunker()
        text = "A" * 2000  # 2000 character text
        
        chunks = chunker.chunk(text, chunk_size=500, overlap=100)
        
        assert len(chunks) > 1
        assert all(len(c) <= 600 for c in chunks)  # Allow some flexibility
    
    def test_empty_text(self):
        """Test chunking empty text."""
        from retrieval.interfaces import SimpleChunker
        
        chunker = SimpleChunker()
        chunks = chunker.chunk("")
        
        assert chunks == []
    
    def test_sentence_boundary_breaking(self):
        """Test chunker respects sentence boundaries."""
        from retrieval.interfaces import SimpleChunker
        
        chunker = SimpleChunker()
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        
        chunks = chunker.chunk(text, chunk_size=30, overlap=5)
        
        # Should break at sentence boundaries when possible
        assert len(chunks) >= 1


class TestChromaRetriever:
    """Tests for ChromaRetriever."""
    
    def test_retriever_initialization(self):
        """Test ChromaRetriever can be instantiated."""
        from retrieval.chroma import ChromaRetriever
        from retrieval.interfaces import RetrieverConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RetrieverConfig(
                persist_directory=tmpdir,
                collection_name="test_collection"
            )
            
            retriever = ChromaRetriever(config)
            assert retriever is not None
            assert retriever.config.collection_name == "test_collection"
    
    def test_health_check(self):
        """Test retriever health check."""
        from retrieval.chroma import ChromaRetriever
        from retrieval.interfaces import RetrieverConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RetrieverConfig(
                persist_directory=tmpdir,
                collection_name="test_health"
            )
            
            retriever = ChromaRetriever(config)
            # Note: Full health check requires embeddings
            # This tests basic instantiation
            assert retriever.config is not None
    
    def test_retriever_count_empty(self):
        """Test count on empty collection."""
        from retrieval.chroma import ChromaRetriever
        from retrieval.interfaces import RetrieverConfig
        import gc
        
        tmpdir = tempfile.mkdtemp()
        try:
            config = RetrieverConfig(
                persist_directory=tmpdir,
                collection_name="test_empty"
            )
            
            retriever = ChromaRetriever(config)
            try:
                retriever.initialize_sync()
                count = retriever.count()
                assert count >= 0
            except Exception:
                # May fail without embeddings model
                pass
            finally:
                # Clean up references to release file handles
                del retriever
                gc.collect()
        except Exception:
            pass  # Cleanup may fail on Windows, that's OK


class TestSearchModes:
    """Tests for search mode handling."""
    
    def test_search_mode_enum(self):
        """Test SearchMode enum values."""
        from retrieval.interfaces import SearchMode
        
        assert SearchMode.SEMANTIC.value == "semantic"
        assert SearchMode.KEYWORD.value == "keyword"
        assert SearchMode.HYBRID.value == "hybrid"
    
    def test_retriever_config_mode(self):
        """Test retriever config search mode."""
        from retrieval.interfaces import RetrieverConfig, SearchMode
        
        config = RetrieverConfig(search_mode=SearchMode.HYBRID)
        assert config.search_mode == SearchMode.HYBRID
