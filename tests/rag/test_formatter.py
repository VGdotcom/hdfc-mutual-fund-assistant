import pytest
from rag.formatter import ResponseFormatter

def test_enforce_sentence_limit():
    text = (
        "The expense ratio of HDFC Small Cap is 0.75% per annum. "
        "It invests in high growth equities. "
        "The fund manager is Mr. Chirag Setalvad. "
        "Exit load is 1% if redeemed within 1 year. "
        "Minimum SIP amount is Rs 100."
    )
    trimmed = ResponseFormatter.enforce_sentence_limit(text, max_sentences=3)
    assert "0.75% per annum." in trimmed
    assert "Mr. Chirag Setalvad." in trimmed
    assert "Exit load is 1%" not in trimmed
    assert "Minimum SIP" not in trimmed

def test_format_normal_response():
    llm_answer = "The expense ratio is 0.75%. This is a direct growth scheme. It has high liquidity."
    chunks = [
        {
            "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "last_updated": "2026-07-01T15:30:00Z",
            "scheme_name": "HDFC Small Cap Fund Direct Growth"
        }
    ]
    
    res = ResponseFormatter.format_response(llm_answer, context_chunks=chunks)
    assert res["is_refusal"] is False
    assert res["citation"] == "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
    assert res["footer"] == "Last updated from sources: 2026-07-01"
    assert "Primary Source: https://groww.in" in res["formatted_text"]
    assert "Last updated from sources: 2026-07-01" in res["formatted_text"]

def test_format_refusal_response():
    refusal_msg = "I am an AI assistant designed to provide factual scheme information. Strictly no investment advice can be provided."
    res = ResponseFormatter.format_response(
        llm_answer=refusal_msg,
        is_refusal=True,
        refusal_url="https://www.amfiindia.com/investor-corner"
    )
    assert res["is_refusal"] is True
    assert res["citation"] == "https://www.amfiindia.com/investor-corner"
    assert "Primary Source: https://www.amfiindia.com/investor-corner" in res["formatted_text"]
    assert "AMFI Investor Education Portal" in res["footer"]
