import asyncio
import json
import logging
import os
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser
from scraper.models import SchemeInfo, ScrapeResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HDFC_SCHEME_URLS = [
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
]

class GrowwScraper:
    def __init__(self, urls: Optional[List[str]] = None, headless: bool = True):
        self.urls = urls or HDFC_SCHEME_URLS
        self.headless = headless

    async def _extract_metric(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[str]:
        """Defensive metric extraction by searching for text labels and getting sibling/associated value."""
        for kw in keywords:
            # Find elements containing keyword (case-insensitive)
            elem = soup.find(lambda tag: tag.name in ["div", "span", "td", "p", "h3", "h4"] and kw.lower() in tag.get_text(" ").lower() and len(tag.get_text(" ").strip()) < 50)
            if elem:
                # Check next sibling or parent's next text
                parent = elem.parent
                if parent:
                    text = parent.get_text(" ", strip=True)
                    # Clean up label from text if possible
                    val = re.sub(r'(?i)' + re.escape(kw) + r'\s*[:\-]?\s*', '', text).strip()
                    if val and len(val) < 100:
                        return val
        return None

    async def _extract_scheme_data(self, page: Page, url: str) -> SchemeInfo:
        logger.info(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait a couple seconds for client-side hydration
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        # 1. Scheme Name
        title_elem = soup.find("h1")
        scheme_name = title_elem.get_text(strip=True) if title_elem else url.split("/")[-1].replace("-", " ").title()
        
        # 2. Extract specific financial metrics defensively
        expense_ratio = await self._extract_metric(soup, ["Expense ratio", "Expense Ratio"])
        exit_load = await self._extract_metric(soup, ["Exit load", "Exit Load"])
        min_sip = await self._extract_metric(soup, ["Min. SIP", "Minimum SIP", "Min SIP"])
        fund_size = await self._extract_metric(soup, ["Fund size", "AUM", "Asset Size"])
        riskometer = await self._extract_metric(soup, ["Risk", "Riskometer"])
        benchmark = await self._extract_metric(soup, ["Benchmark", "Index"])
        
        # 3. Extract fund managers
        fund_managers = []
        fm_sections = soup.find_all(lambda tag: tag.name in ["div", "span", "p", "a"] and "fund manager" in tag.get_text().lower())
        for sec in fm_sections:
            text = sec.get_text(strip=True)
            if len(text) > 3 and len(text) < 80 and text.lower() not in ["fund manager", "fund managers", "fund management"]:
                if text not in fund_managers:
                    fund_managers.append(text)
                    
        # 4. Extract PDF / Document links if present
        doc_links = {}
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            text = a_tag.get_text(strip=True).lower()
            if "factsheet" in text or "factsheet" in href.lower():
                doc_links["Factsheet"] = href if href.startswith("http") else f"https://groww.in{href}"
            elif "kim" in text or "key information" in text:
                doc_links["KIM"] = href if href.startswith("http") else f"https://groww.in{href}"
            elif "sid" in text or "scheme information" in text:
                doc_links["SID"] = href if href.startswith("http") else f"https://groww.in{href}"

        # 5. Extract clean text chunks for vector indexing
        raw_chunks = []
        for p in soup.find_all(["p", "div", "li"]):
            text = p.get_text(" ", strip=True)
            # Filter out tiny snippets or huge javascript blocks
            if len(text) > 40 and len(text) < 1000 and "{" not in text and "function(" not in text:
                if text not in raw_chunks:
                    raw_chunks.append(text)
                    
        return SchemeInfo(
            scheme_name=scheme_name,
            url=url,
            expense_ratio=expense_ratio,
            exit_load=exit_load,
            min_sip=min_sip,
            fund_size=fund_size,
            riskometer=riskometer,
            benchmark=benchmark,
            fund_managers=fund_managers[:5],
            document_links=doc_links,
            raw_text_chunks=raw_chunks[:20]  # Store top clean text chunks
        )

    async def scrape_all(self, output_file: str = "data/schemes.json") -> ScrapeResult:
        logger.info(f"Starting Groww scraper for {len(self.urls)} HDFC schemes...")
        schemes = []
        errors = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            for url in self.urls:
                try:
                    info = await self._extract_scheme_data(page, url)
                    from scraper.normalizer import DataNormalizer
                    info = DataNormalizer.refine_scheme_metrics(info)
                    schemes.append(info)
                    logger.info(f"Successfully scraped: {info.scheme_name} | Expense Ratio: {info.expense_ratio} | NAV: {info.nav}")
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {str(e)}")
                    errors[url] = str(e)
                    
            await browser.close()
            
        result = ScrapeResult(
            total_scraped=len(self.urls),
            success_count=len(schemes),
            failure_count=len(errors),
            schemes=schemes,
            errors=errors
        )
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        logger.info(f"Scraper completed. Saved results to {output_file}")
        return result

if __name__ == "__main__":
    scraper = GrowwScraper()
    asyncio.run(scraper.scrape_all())
