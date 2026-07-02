from scraper.normalizer import DataNormalizer
from scraper.models import SchemeInfo

def test_clean_text():
    raw = "   This is a   test   with \x00 control chars and   extra whitespace.  "
    cleaned = DataNormalizer.clean_text(raw)
    assert cleaned == "This is a test with control chars and extra whitespace."

def test_format_metric_table():
    scheme = SchemeInfo(
        scheme_name="HDFC Small Cap Fund Direct Growth",
        url="https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        expense_ratio="0.75%",
        exit_load="1% if redeemed within 1 year",
        min_sip="Rs. 100",
        fund_managers=["Chirag Setalvad"]
    )
    table_str = DataNormalizer.format_metric_table(scheme)
    assert "| **Expense Ratio** | 0.75% |" in table_str
    assert "| **Exit Load** | 1% if redeemed within 1 year |" in table_str
    assert "Chirag Setalvad" in table_str

def test_normalize_scheme_chunks():
    scheme = SchemeInfo(
        scheme_name="HDFC Mid Cap Fund Direct Growth",
        url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        expense_ratio="0.80%",
        raw_text_chunks=["  Some raw info about the fund investment objective.  "]
    )
    chunks = DataNormalizer.normalize_scheme_chunks(scheme)
    assert len(chunks) == 2
    assert "# Fund Profile: HDFC Mid Cap Fund Direct Growth" in chunks[0]
    assert "[HDFC Mid Cap Fund Direct Growth] Some raw info about the fund investment objective." in chunks[1]
