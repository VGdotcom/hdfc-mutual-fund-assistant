import re
import logging
from typing import List, Optional
from scraper.models import SchemeInfo
from scraper.normalizer import DataNormalizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SemanticChunker:
    """
    Implements semantic and table-preserving chunking.
    Target: approx 300-500 tokens (~1200-2000 characters or ~400 words) with 50 token overlap.
    Enforces atomic table boundaries: tables (markdown '|' rows or structured profiles) are NEVER severed.
    """
    def __init__(self, target_words: int = 350, overlap_words: int = 40):
        # 350 words corresponds to approx 450 tokens in financial/legal English text
        self.target_words = target_words
        self.overlap_words = overlap_words

    @staticmethod
    def _is_table_block(text: str) -> bool:
        """Heuristic to detect if a text snippet represents a structured table or profile block."""
        if "| Financial Metric |" in text or "| **Expense Ratio** |" in text:
            return True
        lines = text.strip().split("\n")
        table_line_count = sum(1 for line in lines if line.strip().startswith("|") and line.strip().endswith("|"))
        return table_line_count >= 2 or "<table" in text.lower()

    def chunk_text(self, text: str, prefix_metadata: str = "") -> List[str]:
        """
        Chunks raw text into semantic segments while preserving table boundaries.
        """
        if not text:
            return []

        # If this entire block is a table or structured profile, keep it atomic!
        if self._is_table_block(text):
            return [f"{prefix_metadata} {text}".strip() if prefix_metadata and not text.startswith(prefix_metadata) else text]

        # Otherwise, split by double newlines (paragraphs) or sentences first
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_words = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If an individual paragraph inside text is a table, flush current words and add table atomically
            if self._is_table_block(para):
                if current_words:
                    chunk_str = " ".join(current_words)
                    if prefix_metadata and not chunk_str.startswith(prefix_metadata):
                        chunk_str = f"{prefix_metadata} {chunk_str}"
                    chunks.append(chunk_str.strip())
                    current_words = []
                chunks.append(f"{prefix_metadata} {para}".strip() if prefix_metadata else para)
                continue

            words = para.split()
            for word in words:
                current_words.append(word)
                if len(current_words) >= self.target_words:
                    chunk_str = " ".join(current_words)
                    if prefix_metadata and not chunk_str.startswith(prefix_metadata):
                        chunk_str = f"{prefix_metadata} {chunk_str}"
                    chunks.append(chunk_str.strip())
                    current_words = current_words[-self.overlap_words:] if self.overlap_words > 0 else []

        if current_words and (len(current_words) > self.overlap_words or not chunks):
            chunk_str = " ".join(current_words)
            if prefix_metadata and not chunk_str.startswith(prefix_metadata):
                chunk_str = f"{prefix_metadata} {chunk_str}"
            chunks.append(chunk_str.strip())

        return chunks

    def chunk_scheme_data(self, scheme: SchemeInfo) -> List[str]:
        """
        Takes a SchemeInfo object and returns a list of table-preserved, semantically chunked strings.
        """
        all_chunks = []
        
        # 1. First chunk MUST be the normalized structured profile table (Atomic)
        profile_table = DataNormalizer.format_metric_table(scheme)
        all_chunks.append(profile_table)
        
        # 2. Process all raw text chunks from scraper
        prefix = f"[{scheme.scheme_name}]"
        for raw_text in scheme.raw_text_chunks:
            cleaned = DataNormalizer.clean_text(raw_text)
            if len(cleaned) > 30:
                sub_chunks = self.chunk_text(cleaned, prefix_metadata=prefix)
                for sc in sub_chunks:
                    if sc not in all_chunks:
                        all_chunks.append(sc)
                        
        return all_chunks

if __name__ == "__main__":
    chunker = SemanticChunker()
    print("SemanticChunker initialized.")
