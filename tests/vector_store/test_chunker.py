from vector_store.chunker import SemanticChunker
from scraper.models import SchemeInfo
from scraper.normalizer import DataNormalizer

def test_is_table_block():
    table_str = """
    | Financial Metric | Value |
    | :--- | :--- |
    | Expense Ratio | 0.75% |
    """
    assert SemanticChunker._is_table_block(table_str) is True
    
    prose_str = "This is just a normal paragraph describing the mutual fund objectives without any table rows."
    assert SemanticChunker._is_table_block(prose_str) is False

def test_table_preservation_atomic():
    chunker = SemanticChunker(target_words=20, overlap_words=5)
    table_str = """| **Expense Ratio** | 0.75% |
| **Exit Load** | 1% if redeemed within 1 year |
| **Minimum SIP Amount** | Rs. 100 |
| **Fund Size / AUM** | Rs. 5000 Cr |
| **Riskometer Classification** | Very High |
| **Benchmark Index** | BSE 250 SmallCap TRI |"""
    
    # Even though target_words is 20, the table block should NOT be split!
    chunks = chunker.chunk_text(table_str)
    assert len(chunks) == 1
    assert "| **Expense Ratio** | 0.75% |" in chunks[0]
    assert "| **Benchmark Index** | BSE 250 SmallCap TRI |" in chunks[0]

def test_chunk_text_overlap():
    chunker = SemanticChunker(target_words=10, overlap_words=3)
    prose = "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10 Word11 Word12 Word13 Word14 Word15"
    chunks = chunker.chunk_text(prose)
    assert len(chunks) > 1
    # Check overlap: end words of chunk 0 should appear at start of chunk 1
    chunk0_words = chunks[0].split()
    chunk1_words = chunks[1].split()
    assert chunk0_words[-1] in chunk1_words[:4]

def test_chunk_scheme_data():
    scheme = SchemeInfo(
        scheme_name="HDFC Gold ETF Fund of Fund Direct Plan Growth",
        url="https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
        expense_ratio="0.50%",
        raw_text_chunks=["An investment objective paragraph that explains how the fund invests in physical gold and gold ETFs."]
    )
    chunker = SemanticChunker()
    chunks = chunker.chunk_scheme_data(scheme)
    assert len(chunks) == 2
    # First chunk is the atomic profile table
    assert "| **Expense Ratio** | 0.50% |" in chunks[0]
    # Second chunk is the contextualized raw text
    assert "[HDFC Gold ETF Fund of Fund Direct Plan Growth]" in chunks[1]
    assert "invests in physical gold" in chunks[1]
