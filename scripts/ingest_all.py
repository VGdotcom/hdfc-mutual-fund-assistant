import os
import asyncio
import logging
from typing import List, Optional
from scraper.groww_scraper import GrowwScraper
from scraper.models import SchemeInfo
from vector_store.chunker import SemanticChunker
from vector_store.schema import MetadataTagger, DocumentChunk
from vector_store.embedder import BGEEmbedder
from vector_store.qdrant_store import QdrantVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_ingestion_pipeline(
    schemes: Optional[List[SchemeInfo]] = None,
    qdrant_path: str = ".qdrant",
    collection_name: str = "hdfc_funds",
    store: Optional[QdrantVectorStore] = None
) -> int:
    """
    Executes the end-to-end Phase 2.4 ingestion pipeline:
    1. Scrapes HDFC schemes (if schemes not provided)
    2. Chunks text while preserving table boundaries
    3. Tags metadata with deterministic UUIDv5 IDs
    4. Generates 384-dimensional BGE embeddings
    5. Upserts into local Qdrant vector database
    """
    if os.path.exists(qdrant_path):
        import shutil
        logger.info(f"Removing old vector cache at {qdrant_path} for clean indexing...")
        shutil.rmtree(qdrant_path, ignore_errors=True)

    if schemes is None:
        if os.path.exists("data/schemes.json"):
            logger.info("Loading scheme data from data/schemes.json...")
            import json
            from scraper.normalizer import SchemeInfo
            with open("data/schemes.json", "r") as f:
                data = json.load(f)
                schemes_list = data.get("schemes", data) if isinstance(data, dict) else data
                schemes = [SchemeInfo(**item) for item in schemes_list]
            logger.info(f"Loaded {len(schemes)} schemes from disk.")
        else:
            logger.info("No scheme data provided. Initiating live Playwright scraping from Groww...")
            scraper = GrowwScraper()
            scrape_res = await scraper.scrape_all()
            schemes = scrape_res.schemes
            logger.info(f"Successfully scraped {len(schemes)} schemes.")

    if not schemes:
        logger.warning("No schemes to process. Exiting ingestion pipeline.")
        return 0

    chunker = SemanticChunker()
    embedder = BGEEmbedder()
    if store is None:
        store = QdrantVectorStore(path=qdrant_path)

    total_chunks_indexed = 0

    for scheme in schemes:
        logger.info(f"Processing scheme: {scheme.scheme_name}...")
        
        # 1. Chunking
        raw_chunks = chunker.chunk_scheme_data(scheme)
        logger.info(f"  Generated {len(raw_chunks)} table-preserved chunks.")
        
        # 2. Metadata Tagging
        tagged_chunks: List[DocumentChunk] = MetadataTagger.tag_chunks(
            scheme=scheme,
            text_chunks=raw_chunks,
            doc_type="Groww Page"
        )
        
        # 3. Embedding Generation
        texts_to_embed = [c.text for c in tagged_chunks]
        embeddings = embedder.embed_batch(texts_to_embed)
        
        # 4. Upserting to Qdrant
        count = store.upsert_chunks(
            chunks=tagged_chunks,
            embeddings=embeddings,
            collection_name=collection_name
        )
        total_chunks_indexed += count
        logger.info(f"  Successfully indexed {count} chunks for {scheme.scheme_name}.")

    logger.info(f"==> Ingestion Pipeline Complete! Total chunks indexed across {len(schemes)} schemes: {total_chunks_indexed}")
    return total_chunks_indexed

if __name__ == "__main__":
    asyncio.run(run_ingestion_pipeline())
