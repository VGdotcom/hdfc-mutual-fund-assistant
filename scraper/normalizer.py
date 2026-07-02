import re
from typing import List, Dict, Any, Optional
import logging
from scraper.models import SchemeInfo

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DataNormalizer:
    @staticmethod
    def clean_text(text: str) -> str:
        """Removes excessive whitespace, special control characters, and normalizes quotes."""
        if not text:
            return ""
        # Remove ASCII control characters
        text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def refine_scheme_metrics(scheme: SchemeInfo) -> SchemeInfo:
        """Cleans and extracts precise numerical metrics from scraped Groww text strings."""
        text = f"{scheme.expense_ratio or ''} {scheme.fund_size or ''} {scheme.riskometer or ''} {scheme.benchmark or ''} {' '.join(scheme.raw_text_chunks[:5])}"
        
        # Extract NAV
        if not scheme.nav or scheme.nav == "₹01":
            nav_match = re.search(r'NAV:.*?₹\s*([\d,]+\.\d{2})', text) or re.search(r'₹\s*([\d,]+\.\d{2})', text)
            if nav_match:
                val = nav_match.group(1).strip().replace('₹', '')
                scheme.nav = f"₹{val}"
        
        # Extract Min SIP
        sip_match = re.search(r'Min\.\s*(?:for\s*)?SIP\s*([₹\d,]+)', text)
        if sip_match:
            val = sip_match.group(1).strip().replace('₹', '')
            scheme.min_sip = f"₹{val}"
            
        # Extract Fund Size (AUM)
        aum_match = re.search(r'Fund\s*size\s*(?:\(AUM\))?\s*([₹\d,.]+\s*Cr)', text)
        if aum_match:
            val = aum_match.group(1).strip().replace('₹', '')
            scheme.fund_size = f"₹{val}" if not val.startswith('₹') else val
            
        # Extract Expense Ratio
        if scheme.expense_ratio and ("NAV:" in scheme.expense_ratio or len(scheme.expense_ratio) > 15):
            exp_match = re.search(r'Cr\s+([\d.]+%)', scheme.expense_ratio) or re.search(r'(\d+(?:\.\d+)?)%', scheme.expense_ratio)
            if exp_match:
                scheme.expense_ratio = exp_match.group(1).strip()
                
        # Clean Riskometer
        name_lower = scheme.scheme_name.lower()
        if "gold" in name_lower or "silver" in name_lower:
            scheme.riskometer = "High Risk (Commodity / FoF)"
        elif any(k in name_lower for k in ["small", "mid", "large", "flexi", "nifty", "cap", "index"]):
            scheme.riskometer = "Very High Risk (Equity)"
            
        # Clean Benchmark
        if scheme.benchmark:
            scheme.benchmark = scheme.benchmark.replace("Scheme Information Document(SID)", "").strip()
            if scheme.benchmark.startswith("Fund "):
                scheme.benchmark = scheme.benchmark[5:].strip()
                
        return scheme

    @staticmethod
    def format_metric_table(scheme: SchemeInfo) -> str:
        """Creates a table-preserving markdown summary of key financial metrics for embedding."""
        scheme = DataNormalizer.refine_scheme_metrics(scheme)
        lines = [
            f"# Fund Profile: {scheme.scheme_name}",
            f"**Official Source URL:** {scheme.url}",
            f"**Last Verified:** {scheme.last_updated}",
            "",
            "| Financial Metric | Verified Value |",
            "| :--- | :--- |",
            f"| **Current NAV** | {scheme.nav or 'Not Available'} |",
            f"| **Expense Ratio** | {scheme.expense_ratio or 'Not Available'} |",
            f"| **Exit Load** | {scheme.exit_load or 'Nil / Not Available'} |",
            f"| **Minimum SIP Amount** | {scheme.min_sip or 'Not Available'} |",
            f"| **Fund Size / AUM** | {scheme.fund_size or 'Not Available'} |",
            f"| **Riskometer Classification** | {scheme.riskometer or 'Not Available'} |",
            f"| **Benchmark Index** | {scheme.benchmark or 'Not Available'} |",
            "",
            f"**Fund Managers:** {', '.join(scheme.fund_managers) if scheme.fund_managers else 'Not Listed'}"
        ]
        return "\n".join(lines)

    @staticmethod
    def normalize_scheme_chunks(scheme: SchemeInfo) -> List[str]:
        """Produces a clean list of semantic chunks with table boundaries preserved."""
        normalized_chunks = []
        
        # Chunk 1: The structured profile table (critical for metrics queries)
        profile_chunk = DataNormalizer.format_metric_table(scheme)
        normalized_chunks.append(profile_chunk)
        
        # Chunk 2..N: Cleaned paragraph chunks from webpage / documents
        for raw in scheme.raw_text_chunks:
            cleaned = DataNormalizer.clean_text(raw)
            if len(cleaned) > 30:
                # Attach context prefix so standalone chunk is self-contained
                contextual_chunk = f"[{scheme.scheme_name}] {cleaned}"
                if contextual_chunk not in normalized_chunks:
                    normalized_chunks.append(contextual_chunk)
                    
        return normalized_chunks
