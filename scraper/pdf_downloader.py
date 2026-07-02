import asyncio
import hashlib
import httpx
import logging
import os
from typing import List, Dict, Any, Optional
from scraper.models import DocumentInfo, DownloadResult, SchemeInfo

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class PDFDownloader:
    def __init__(self, output_dir: str = "data/pdfs", timeout: int = 30):
        self.output_dir = output_dir
        self.timeout = timeout

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    async def download_file(self, client: httpx.AsyncClient, url: str, scheme_name: str, doc_type: str) -> Optional[DocumentInfo]:
        logger.info(f"Downloading {doc_type} for {scheme_name} from {url}...")
        try:
            response = await client.get(url, follow_redirects=True, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.content
            if len(content) == 0:
                logger.warning(f"Empty file content received from {url}")
                return None
                
            # Verify PDF header (unless it's an HTML/text guide)
            if not content.startswith(b"%PDF-") and "pdf" in url.lower():
                logger.warning(f"File downloaded from {url} does not have a valid PDF header (%PDF-)")
                
            sha256 = self.compute_sha256(content)
            
            # Safe filename
            safe_scheme_name = "".join(c if c.isalnum() else "_" for c in scheme_name).strip("_")
            scheme_dir = os.path.join(self.output_dir, safe_scheme_name)
            os.makedirs(scheme_dir, exist_ok=True)
            
            file_path = os.path.join(scheme_dir, f"{doc_type.lower()}.pdf")
            with open(file_path, "wb") as f:
                f.write(content)
                
            logger.info(f"Successfully saved {doc_type} to {file_path} (Size: {len(content)} bytes, SHA256: {sha256[:8]}...)")
            return DocumentInfo(
                scheme_name=scheme_name,
                doc_type=doc_type,
                url=url,
                file_path=file_path,
                sha256_hash=sha256,
                size_bytes=len(content)
            )
        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            raise e

    async def download_from_schemes(self, schemes: List[SchemeInfo]) -> DownloadResult:
        documents = []
        errors = {}
        total_requested = 0
        
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
            tasks = []
            for scheme in schemes:
                for doc_type, url in scheme.document_links.items():
                    total_requested += 1
                    tasks.append(self.download_file(client, url, scheme.scheme_name, doc_type))
                    
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, res in enumerate(results):
                    if isinstance(res, Exception):
                        errors[f"Task_{i}"] = str(res)
                    elif res is not None:
                        documents.append(res)
                        
        result = DownloadResult(
            total_requested=total_requested,
            success_count=len(documents),
            failure_count=len(errors),
            documents=documents,
            errors=errors
        )
        return result

if __name__ == "__main__":
    # Example usage
    downloader = PDFDownloader()
    print("PDFDownloader initialized.")
