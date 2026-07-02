import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from scraper.models import SchemeInfo

DocumentType = Literal["Factsheet", "KIM", "SID", "Groww Page", "Regulatory Guide"]

class ChunkMetadata(BaseModel):
    scheme_name: str
    document_type: str
    source_url: str
    last_updated: str
    chunk_index: int
    chunk_id: str

    @field_validator("document_type")
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        valid_types = {"Factsheet", "KIM", "SID", "Groww Page", "Regulatory Guide"}
        if v not in valid_types:
            raise ValueError(f"Invalid document_type '{v}'. Must be one of: {valid_types}")
        return v

class DocumentChunk(BaseModel):
    text: str
    metadata: ChunkMetadata

class MetadataTagger:
    @staticmethod
    def compute_chunk_id(scheme_name: str, doc_type: str, index: int, text: str) -> str:
        """Computes a deterministic UUID string for Qdrant indexing and deduplication."""
        raw_str = f"{scheme_name}_{doc_type}_{index}_{text}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_str))

    @classmethod
    def tag_chunks(
        cls,
        scheme: SchemeInfo,
        text_chunks: List[str],
        doc_type: str = "Groww Page",
        source_url: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Wraps raw text chunks into fully tagged DocumentChunk records with schema validation.
        """
        url = source_url or scheme.url
        timestamp = scheme.last_updated or datetime.now(timezone.utc).isoformat()
        
        tagged_records = []
        for i, text in enumerate(text_chunks):
            chunk_id = cls.compute_chunk_id(scheme.scheme_name, doc_type, i, text)
            meta = ChunkMetadata(
                scheme_name=scheme.scheme_name,
                document_type=doc_type,
                source_url=url,
                last_updated=timestamp,
                chunk_index=i,
                chunk_id=chunk_id
            )
            record = DocumentChunk(text=text, metadata=meta)
            tagged_records.append(record)
            
        return tagged_records

if __name__ == "__main__":
    print("MetadataTagger initialized.")
