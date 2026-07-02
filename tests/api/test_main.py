import pytest
from fastapi.testclient import TestClient
import uuid
from api.main import app
import api.main as main_mod
from rag.retriever import RAGRetriever
from rag.llm_client import GroqLLMClient
from vector_store.qdrant_store import QdrantVectorStore
from vector_store.schema import DocumentChunk, ChunkMetadata
from vector_store.embedder import BGEEmbedder

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_rag_engine():
    # Setup in-memory Qdrant and Mock LLM for API unit testing
    store = QdrantVectorStore(path=":memory:")
    embedder = BGEEmbedder()
    
    meta = ChunkMetadata(
        scheme_name="HDFC Small Cap Fund Direct Growth",
        document_type="Factsheet",
        source_url="https://groww.in/hdfc-small-cap",
        last_updated="2026-07-01T15:00:00Z",
        chunk_index=0,
        chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "api_sc_chunk"))
    )
    chunk = DocumentChunk(text="The expense ratio of HDFC Small Cap Fund is 0.75% per annum.", metadata=meta)
    vec = embedder.embed_text(chunk.text)
    store.upsert_chunks([chunk], [vec], collection_name="hdfc_funds")
    
    main_mod.retriever = RAGRetriever(store=store, embedder=embedder, collection_name="hdfc_funds")
    main_mod.llm_client = GroqLLMClient(mock_mode=True)
    yield

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["qdrant_status"] == "connected"

def test_list_schemes_endpoint():
    response = client.get("/api/v1/schemes")
    assert response.status_code == 200
    schemes = response.json()
    assert len(schemes) == 5
    assert "HDFC Small Cap Fund Direct Growth" in schemes

def test_chat_endpoint_allowed_query():
    payload = {"query": "What is the expense ratio of HDFC Small Cap Fund?"}
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] is False
    assert len(data["answer"]) > 0
    assert "https://groww.in/hdfc-small-cap" in data["citation"]
    assert "Last updated from sources" in data["footer"]
    assert data["retrieved_chunks_count"] >= 1

def test_chat_endpoint_blocked_advisory_query():
    payload = {"query": "Should I invest in HDFC Small Cap right now?"}
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] is True
    assert "https://www.amfiindia.com/investor-corner" in data["citation"]
    assert data["retrieved_chunks_count"] == 0
