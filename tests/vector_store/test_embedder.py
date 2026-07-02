import pytest
from vector_store.embedder import BGEEmbedder

@pytest.fixture(scope="module")
def embedder():
    return BGEEmbedder()

def test_embed_text(embedder):
    text = "HDFC Small Cap Fund Direct Growth has an expense ratio of 0.75%."
    vec = embedder.embed_text(text)
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(val, float) for val in vec)

def test_embed_batch(embedder):
    texts = [
        "What is the exit load for HDFC Gold ETF?",
        "Minimum SIP amount is Rs 100 per month.",
        "The fund manager is Mr. Chirag Setalvad."
    ]
    vecs = embedder.embed_batch(texts)
    assert len(vecs) == 3
    for vec in vecs:
        assert len(vec) == 384
