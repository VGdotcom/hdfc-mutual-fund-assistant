import pytest
from bs4 import BeautifulSoup
from scraper.groww_scraper import GrowwScraper, HDFC_SCHEME_URLS
from scraper.models import SchemeInfo

def test_hdfc_scheme_urls_count():
    assert len(HDFC_SCHEME_URLS) == 5
    for url in HDFC_SCHEME_URLS:
        assert "groww.in/mutual-funds/hdfc-" in url

@pytest.mark.asyncio
async def test_extract_metric_defensive():
    html_sample = """
    <div class="fund-card">
        <span>Expense ratio</span>
        <span>0.75%</span>
    </div>
    <div class="fund-card">
        <p>Exit Load: 1% if redeemed within 1 year</p>
    </div>
    """
    soup = BeautifulSoup(html_sample, "html.parser")
    scraper = GrowwScraper()
    
    er = await scraper._extract_metric(soup, ["Expense ratio", "Expense Ratio"])
    assert er is not None
    assert "0.75%" in er
    
    el = await scraper._extract_metric(soup, ["Exit load", "Exit Load"])
    assert el is not None
    assert "1%" in el

@pytest.mark.asyncio
async def test_live_groww_scraper(tmp_path):
    """Live integration test to verify crawling Groww for all 5 HDFC schemes."""
    output_file = str(tmp_path / "test_schemes.json")
    # Test on just 1 scheme to be fast in unit test battery, or test all 5
    test_urls = [HDFC_SCHEME_URLS[0]]
    scraper = GrowwScraper(urls=test_urls, headless=True)
    
    result = await scraper.scrape_all(output_file=output_file)
    assert result.total_scraped == 1
    assert result.success_count == 1
    assert result.failure_count == 0
    
    scheme = result.schemes[0]
    assert "HDFC" in scheme.scheme_name.upper()
    assert scheme.url == test_urls[0]
    # Verify that we extracted clean text chunks
    assert len(scheme.raw_text_chunks) > 0
