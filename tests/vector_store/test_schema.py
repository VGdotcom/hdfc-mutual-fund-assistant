import pytest
from pydantic import ValidationError
from vector_store.schema import ChunkMetadata, DocumentChunk, MetadataTagger
from scraper.models import SchemeInfo

def test_chunk_metadata_validation():
    # Valid metadata
    meta = ChunkMetadata(
        scheme_name="HDFC Small Cap Fund Direct Growth",
        document_type="Factsheet",
        source_url="https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id="abc123hash"
    )
    assert meta.document_type == "Factsheet"
    
    # Invalid document_type should raise ValidationError
    with pytest.raises(ValidationError):
        ChunkMetadata(
            scheme_name="HDFC Small Cap Fund",
            document_type="InvalidDocType",
            source_url="https://example.com",
            last_updated="2026-07-01T15:00:00Z",
            chunk_index=0,
            chunk_id="hash123"
        )

def test_compute_chunk_id():
    id1 = MetadataTagger.compute_chunk_id("HDFC Fund", "Groww Page", 0, "sample text")
    id2 = MetadataTagger.compute_chunk_id("HDFC Fund", "Groww Page", 0, "sample text")
    id3 = MetadataTagger.compute_chunk_id("HDFC Fund", "Groww Page", 1, "sample text")
    
    assert len(id1) == 36
    assert id1 == id2  # Deterministic
    assert id1 != id3  # Different index produces different ID

def test_tag_chunks():
    scheme = SchemeInfo(
        scheme_name="HDFC Mid Cap Fund Direct Growth",
        url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        expense_ratio="0.80%"
    )
    raw_chunks = [
        "| **Expense Ratio** | 0.80% |",
        "[HDFC Mid Cap Fund Direct Growth] This is paragraph 1 about mid cap investing."
    ]
    
    tagged = MetadataTagger.tag_chunks(scheme, raw_chunks, doc_type="Groww Page")
    assert len(tagged) == 2
    
    chunk0 = tagged[0]
    assert isinstance(chunk0, DocumentChunk)
    assert chunk0.text == raw_chunks[0]
    assert chunk0.metadata.scheme_name == "HDFC Mid Cap Fund Direct Growth"
    assert chunk0.metadata.document_type == "Groww Page"
    assert chunk0.metadata.source_url == scheme.url
    assert chunk0.metadata.chunk_index == 0
    assert len(chunk0.metadata.chunk_id) == 36
