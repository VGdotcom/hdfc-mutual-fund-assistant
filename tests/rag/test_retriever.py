import pytest
import uuid
from rag.retriever import RAGRetriever
from vector_store.qdrant_store import QdrantVectorStore
from vector_store.schema import DocumentChunk, ChunkMetadata
from vector_store.embedder import BGEEmbedder

@pytest.fixture
def test_retriever():
    store = QdrantVectorStore(path=":memory:")
    embedder = BGEEmbedder()
    
    # Populate memory store with 2 distinct schemes
    meta1 = ChunkMetadata(
        scheme_name="HDFC Small Cap Fund Direct Growth",
        document_type="Factsheet",
        source_url="https://groww.in/hdfc-small-cap",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "sc_chunk"))
    )
    chunk1 = DocumentChunk(text="Small cap fund expense ratio is 0.75%", metadata=meta1)
    
    meta2 = ChunkMetadata(
        scheme_name="HDFC Gold ETF Fund of Fund Direct Plan Growth",
        document_type="Factsheet",
        source_url="https://groww.in/hdfc-gold-etf",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "au_chunk"))
    )
    chunk2 = DocumentChunk(text="Gold ETF invests in physical gold bullion.", metadata=meta2)
    
    vec1 = embedder.embed_text(chunk1.text)
    vec2 = embedder.embed_text(chunk2.text)
    
    store.upsert_chunks([chunk1, chunk2], [vec1, vec2], collection_name="test_retriever")
    return RAGRetriever(store=store, embedder=embedder, collection_name="test_retriever")

def test_extract_scheme_filter():
    assert RAGRetriever.extract_scheme_filter("What is the expense ratio of Small Cap?") == "HDFC Small Cap Fund Direct Growth"
    assert RAGRetriever.extract_scheme_filter("Tell me about Nifty 50 Index Fund") == "HDFC Nifty 50 Index Fund Direct Plan Growth"
    assert RAGRetriever.extract_scheme_filter("What is mutual fund?") is None  # No scheme mentioned
    assert RAGRetriever.extract_scheme_filter("Compare small cap and gold etf") is None  # Multiple mentioned

def test_retrieve_with_dynamic_filter(test_retriever):
    # Query mentions Small Cap -> Should only retrieve small cap chunk!
    results = test_retriever.retrieve("What is the expense ratio for HDFC Small Cap?", top_k=2)
    assert len(results) == 1
    assert results[0]["scheme_name"] == "HDFC Small Cap Fund Direct Growth"
    assert "0.75%" in results[0]["text"]
    
def test_retrieve_without_filter(test_retriever):
    # Generic query without scheme name -> Retrieves top k across all schemes
    results = test_retriever.retrieve("What is the expense ratio and what does it invest in?", top_k=2)
    assert len(results) == 2
