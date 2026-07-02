import re
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ResponseFormatter:
    """
    Post-processing engine that enforces formatting rules:
    - Maximum 3 sentences truncation
    - Exact primary source URL citation injection
    - Mandatory regulatory footer stamping
    """

    @staticmethod
    def enforce_sentence_limit(text: str, max_sentences: int = 3) -> str:
        """
        Splits text into sentences while ignoring decimal points in financial figures (e.g. 0.75%).
        Truncates output to at most max_sentences.
        """
        if not text:
            return ""
        
        # Protect common abbreviations by temporarily replacing their periods
        protected = text.strip()
        abbrevs = ["Mr.", "Mrs.", "Dr.", "Ms.", "Rs.", "No.", "Ltd.", "Co.", "Inc.", "vs.", "e.g.", "i.e."]
        for i, abbr in enumerate(abbrevs):
            protected = protected.replace(abbr, f"__ABBR{i}__")
            
        # Split when a period is followed by whitespace and an alphanumeric character
        sentences = re.split(r'(?<=\.)\s+(?=[A-Za-z0-9])', protected)
        
        # Restore abbreviations
        restored = []
        for s in sentences:
            for i, abbr in enumerate(abbrevs):
                s = s.replace(f"__ABBR{i}__", abbr)
            restored.append(s)
        
        if len(restored) <= max_sentences:
            return text.strip()
            
        logger.info(f"Response exceeded {max_sentences} sentences ({len(restored)} detected). Truncating output.")
        trimmed = " ".join(restored[:max_sentences]).strip()
        if not trimmed.endswith('.'):
            trimmed += '.'
        return trimmed

    @classmethod
    def format_response(
        cls,
        llm_answer: str,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        is_refusal: bool = False,
        refusal_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formats the raw LLM or refusal answer into a complete structured response package.
        """
        if is_refusal:
            url = refusal_url or "https://www.amfiindia.com/investor-corner"
            footer = "Last updated from sources: AMFI Investor Education Portal"
            formatted_text = f"{llm_answer.strip()}\n\nPrimary Source: {url}\n\n{footer}"
            return {
                "answer": llm_answer.strip(),
                "citation": url,
                "footer": footer,
                "formatted_text": formatted_text,
                "is_refusal": True
            }

        # 1. Enforce 3-sentence limit
        trimmed_answer = cls.enforce_sentence_limit(llm_answer, max_sentences=3)

        # 2. Extract Primary Citation Link from top retrieved chunk
        top_url = "https://groww.in/mutual-funds"
        last_updated = "2026-07-01"
        
        if context_chunks and len(context_chunks) > 0:
            top_chunk = context_chunks[0]
            top_url = top_chunk.get("source_url", top_url)
            raw_date = top_chunk.get("last_updated", last_updated)
            # Clean ISO string to date (e.g. 2026-07-01T15:00:00Z -> 2026-07-01)
            last_updated = raw_date.split("T")[0] if "T" in raw_date else str(raw_date)

        footer = f"Last updated from sources: {last_updated}"
        formatted_text = f"{trimmed_answer}\n\nPrimary Source: {top_url}\n\n{footer}"

        return {
            "answer": trimmed_answer,
            "citation": top_url,
            "footer": footer,
            "formatted_text": formatted_text,
            "is_refusal": False
        }

if __name__ == "__main__":
    sample_text = "The expense ratio is 0.75% per annum. This fund invests in small cap stocks. It has strong growth potential. Exit load applies for early redemption. Minimum SIP is Rs 100."
    res = ResponseFormatter.format_response(sample_text, [{"source_url": "https://groww.in/hdfc-small-cap", "last_updated": "2026-07-01T12:00:00Z"}])
    print("Formatted:\n", res["formatted_text"])
