import pytest
import re
from rag.llm_client import GroqLLMClient

@pytest.fixture
def mock_llm_client():
    return GroqLLMClient(mock_mode=True)

def test_format_context(mock_llm_client):
    chunks = [
        {"text": "Expense ratio is 0.75%", "scheme_name": "HDFC Small Cap Fund Direct Growth", "document_type": "Factsheet"},
        {"text": "Exit load is 1% if redeemed within 1 year", "scheme_name": "HDFC Small Cap Fund Direct Growth", "document_type": "KIM"}
    ]
    formatted = mock_llm_client._format_context(chunks)
    assert "[Chunk 1 | HDFC Small Cap Fund Direct Growth (Factsheet)]:" in formatted
    assert "Expense ratio is 0.75%" in formatted
    assert "[Chunk 2 | HDFC Small Cap Fund Direct Growth (KIM)]:" in formatted

@pytest.mark.asyncio
async def test_generate_answer_mock_with_context(mock_llm_client):
    query = "What is the expense ratio of HDFC Small Cap?"
    chunks = [{"text": "The expense ratio is 0.75% per annum.", "scheme_name": "HDFC Small Cap"}]
    
    answer = await mock_llm_client.generate_answer(query, chunks)
    assert len(answer) > 0
    assert "0.75%" in answer or "official scheme" in answer
    # Verify sentence count constraint in mock output (splitting by period followed by whitespace or end of string)
    sentences = [s.strip() for s in re.split(r'\.\s+|\.$', answer) if s.strip()]
    assert len(sentences) <= 3

@pytest.mark.asyncio
async def test_generate_answer_mock_empty_context(mock_llm_client):
    query = "What is the exit load?"
    answer = await mock_llm_client.generate_answer(query, [])
    assert answer == "I do not have sufficient information in the official scheme documents to answer this question."
