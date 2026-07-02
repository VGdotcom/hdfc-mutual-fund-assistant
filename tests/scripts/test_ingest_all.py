import pytest
from scraper.models import SchemeInfo
from scripts.ingest_all import run_ingestion_pipeline
from vector_store.qdrant_store import QdrantVectorStore
from vector_store.embedder import BGEEmbedder

@pytest.mark.asyncio
async def test_run_ingestion_pipeline_memory():
    # Provide mock scheme data to test ingestion deterministically without internet/Playwright
    mock_scheme1 = SchemeInfo(
        scheme_name="HDFC Small Cap Fund Direct Growth",
        url="https://groww.in/hdfc-small-cap",
        expense_ratio="0.75%",
        raw_text_chunks=["An objective paragraph describing small cap investments with strong growth potential."]
    )
    mock_scheme2 = SchemeInfo(
        scheme_name="HDFC Gold ETF Fund of Fund Direct Plan Growth",
        url="https://groww.in/hdfc-gold-etf",
        expense_ratio="0.50%",
        raw_text_chunks=["Invests primarily in physical gold and domestic gold ETFs."]
    )
    
    store = QdrantVectorStore(path=":memory:")
    
    total_indexed = await run_ingestion_pipeline(
        schemes=[mock_scheme1, mock_scheme2],
        collection_name="test_ingest",
        store=store
    )
    
    assert total_indexed == 4  # 2 schemes * (1 profile table + 1 text chunk) = 4 chunks
    
    # Now verify retrieval accuracy from memory store!
    embedder = BGEEmbedder()
    
    query_vec = embedder.embed_text("What is the expense ratio of HDFC Small Cap?")
    results = store.search(query_vec, limit=2, collection_name="test_ingest")
    
    assert len(results) > 0
    assert any("0.75%" in hit["text"] for hit in results)
    assert any("HDFC Small Cap Fund Direct Growth" == hit["scheme_name"] for hit in results)
