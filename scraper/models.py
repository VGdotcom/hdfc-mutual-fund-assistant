from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

class SchemeInfo(BaseModel):
    scheme_name: str
    url: str
    nav: Optional[str] = None
    expense_ratio: Optional[str] = None
    exit_load: Optional[str] = None
    min_sip: Optional[str] = None
    fund_size: Optional[str] = None
    riskometer: Optional[str] = None
    benchmark: Optional[str] = None
    fund_managers: List[str] = Field(default_factory=list)
    document_links: Dict[str, str] = Field(default_factory=dict)
    raw_text_chunks: List[str] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ScrapeResult(BaseModel):
    total_scraped: int
    success_count: int
    failure_count: int
    schemes: List[SchemeInfo] = Field(default_factory=list)
    errors: Dict[str, str] = Field(default_factory=dict)

class DocumentInfo(BaseModel):
    scheme_name: str
    doc_type: str  # e.g., "Factsheet", "KIM", "SID"
    url: str
    file_path: str
    sha256_hash: str
    size_bytes: int
    last_downloaded: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DownloadResult(BaseModel):
    total_requested: int
    success_count: int
    failure_count: int
    documents: List[DocumentInfo] = Field(default_factory=list)
    errors: Dict[str, str] = Field(default_factory=dict)
