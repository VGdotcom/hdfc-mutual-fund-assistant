import pytest
import uuid
from vector_store.qdrant_store import QdrantVectorStore
from vector_store.schema import DocumentChunk, ChunkMetadata

@pytest.fixture
def memory_store():
    return QdrantVectorStore(path=":memory:")

def test_create_and_upsert(memory_store):
    meta1 = ChunkMetadata(
        scheme_name="HDFC Small Cap Fund Direct Growth",
        document_type="Factsheet",
        source_url="https://groww.in/hdfc-small-cap",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "chunk1"))
    )
    chunk1 = DocumentChunk(text="Expense ratio is 0.75%", metadata=meta1)
    
    meta2 = ChunkMetadata(
        scheme_name="HDFC Gold ETF Fund of Fund Direct Plan Growth",
        document_type="Factsheet",
        source_url="https://groww.in/hdfc-gold-etf",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "chunk2"))
    )
    chunk2 = DocumentChunk(text="Exit load is Nil if redeemed after 1 year", metadata=meta2)
    
    # Mock 384-dim vectors
    vec1 = [0.1] * 384
    vec2 = [-0.1] * 384
    
    count = memory_store.upsert_chunks([chunk1, chunk2], [vec1, vec2], collection_name="test_collection")
    assert count == 2

def test_search_with_filtering(memory_store):
    # Setup 2 chunks from different schemes
    meta1 = ChunkMetadata(
        scheme_name="HDFC Small Cap Fund Direct Growth",
        document_type="Groww Page",
        source_url="https://groww.in/hdfc-small-cap",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "sc_1"))
    )
    chunk1 = DocumentChunk(text="Small cap companies carry higher growth potential.", metadata=meta1)
    
    meta2 = ChunkMetadata(
        scheme_name="HDFC Silver ETF FOF Direct Growth",
        document_type="Groww Page",
        source_url="https://groww.in/hdfc-silver-etf",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "ag_1"))
    )
    chunk2 = DocumentChunk(text="Silver ETF invests in physical silver bullion.", metadata=meta2)
    
    # Simple vectors where vec1 is close to query_vec
    vec1 = [1.0] + [0.0] * 383
    vec2 = [0.0] + [1.0] + [0.0] * 382
    query_vec = [0.9] + [0.1] + [0.0] * 382
    
    memory_store.upsert_chunks([chunk1, chunk2], [vec1, vec2], collection_name="test_filter")
    
    # Search without filter
    res = memory_store.search(query_vec, limit=2, collection_name="test_filter")
    assert len(res) == 2
    assert res[0]["scheme_name"] == "HDFC Small Cap Fund Direct Growth"
    
    # Search WITH filter for Silver ETF
    res_filtered = memory_store.search(query_vec, limit=2, scheme_name="HDFC Silver ETF FOF Direct Growth", collection_name="test_filter")
    assert len(res_filtered) == 1
    assert res_filtered[0]["scheme_name"] == "HDFC Silver ETF FOF Direct Growth"
    assert "silver bullion" in res_filtered[0]["text"]
