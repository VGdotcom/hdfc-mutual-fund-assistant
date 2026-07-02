import pytest
import httpx
import os
from scraper.pdf_downloader import PDFDownloader

def test_compute_sha256():
    downloader = PDFDownloader()
    content = b"test pdf content"
    sha = downloader.compute_sha256(content)
    assert len(sha) == 64
    assert isinstance(sha, str)

@pytest.mark.asyncio
async def test_download_mock_pdf(tmp_path):
    output_dir = str(tmp_path / "pdfs")
    downloader = PDFDownloader(output_dir=output_dir)
    
    mock_content = b"%PDF-1.4 mock pdf data for testing"
    
    # Create custom transport or test with httpx MockTransport if available, or test helper
    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(200, content=mock_content)
            
    async with httpx.AsyncClient(transport=MockTransport()) as client:
        doc_info = await downloader.download_file(
            client=client,
            url="https://example.com/mock-factsheet.pdf",
            scheme_name="HDFC Small Cap Fund",
            doc_type="Factsheet"
        )
        
    assert doc_info is not None
    assert doc_info.scheme_name == "HDFC Small Cap Fund"
    assert doc_info.doc_type == "Factsheet"
    assert doc_info.size_bytes == len(mock_content)
    assert os.path.exists(doc_info.file_path)
    with open(doc_info.file_path, "rb") as f:
        assert f.read() == mock_content
