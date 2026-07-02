import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from vector_store.schema import DocumentChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class QdrantVectorStore:
    """
    Manages collection schema, indexing, and similarity retrieval in Qdrant.
    Supports persistent local storage (.qdrant/) or memory mode for testing.
    """
    DEFAULT_COLLECTION = "hdfc_funds"

    def __init__(self, path: Optional[str] = ".qdrant", location: Optional[str] = None):
        if location == ":memory:" or path == ":memory:":
            logger.info("Initializing in-memory Qdrant client...")
            self.client = QdrantClient(location=":memory:")
        else:
            logger.info(f"Initializing local Qdrant client at {path}...")
            self.client = QdrantClient(path=path)

    def create_collection_if_not_exists(self, collection_name: str = DEFAULT_COLLECTION, vector_size: int = 384):
        """Creates collection with Cosine similarity distance metric if it does not already exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        if not exists:
            logger.info(f"Creating Qdrant collection '{collection_name}' with vector size {vector_size}...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=rest.VectorParams(
                    size=vector_size,
                    distance=rest.Distance.COSINE
                )
            )
            # Create payload indexes for fast filtering
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="scheme_name",
                field_schema=rest.PayloadSchemaType.KEYWORD
            )
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="document_type",
                field_schema=rest.PayloadSchemaType.KEYWORD
            )
        else:
            logger.info(f"Collection '{collection_name}' already exists.")

    def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        collection_name: str = DEFAULT_COLLECTION
    ) -> int:
        """Upserts a batch of tagged DocumentChunk records and embeddings into Qdrant."""
        if not chunks or len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must be non-empty and of identical length.")

        self.create_collection_if_not_exists(collection_name=collection_name, vector_size=len(embeddings[0]))

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            # Use deterministic SHA256 chunk_id or integer ID
            point = rest.PointStruct(
                id=chunk.metadata.chunk_id,
                vector=vector,
                payload={
                    "text": chunk.text,
                    "scheme_name": chunk.metadata.scheme_name,
                    "document_type": chunk.metadata.document_type,
                    "source_url": chunk.metadata.source_url,
                    "last_updated": chunk.metadata.last_updated,
                    "chunk_index": chunk.metadata.chunk_index,
                    "chunk_id": chunk.metadata.chunk_id
                }
            )
            points.append(point)

        logger.info(f"Upserting {len(points)} points into collection '{collection_name}'...")
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        return len(points)

    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        scheme_name: Optional[str] = None,
        document_type: Optional[str] = None,
        collection_name: str = DEFAULT_COLLECTION
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search with optional metadata filtering by scheme_name or doc_type.
        """
        query_filter = None
        conditions = []
        
        if scheme_name:
            conditions.append(rest.FieldCondition(
                key="scheme_name",
                match=rest.MatchValue(value=scheme_name)
            ))
        if document_type:
            conditions.append(rest.FieldCondition(
                key="document_type",
                match=rest.MatchValue(value=document_type)
            ))
            
        if conditions:
            query_filter = rest.Filter(must=conditions)

        query_res = self.client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )
        results = query_res.points

        formatted_results = []
        for res in results:
            formatted_results.append({
                "score": res.score,
                "text": res.payload.get("text"),
                "scheme_name": res.payload.get("scheme_name"),
                "document_type": res.payload.get("document_type"),
                "source_url": res.payload.get("source_url"),
                "last_updated": res.payload.get("last_updated"),
                "chunk_id": res.payload.get("chunk_id")
            })
            
        return formatted_results

    def get_scheme_profile(self, scheme_name: str, collection_name: str = "hdfc_funds") -> Optional[Dict[str, Any]]:
        """Retrieves the atomic Fund Profile table chunk for a scheme."""
        try:
            scroll_res = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=rest.Filter(
                    must=[rest.FieldCondition(key="scheme_name", match=rest.MatchValue(value=scheme_name))]
                ),
                limit=100,
                with_payload=True
            )[0]
            for pt in scroll_res:
                payload = pt.payload or {}
                text = payload.get("text", "")
                if "# Fund Profile:" in text or "| Financial Metric |" in text:
                    return {
                        "score": 1.0,
                        "text": text,
                        "scheme_name": payload.get("scheme_name"),
                        "document_type": payload.get("document_type"),
                        "source_url": payload.get("source_url"),
                        "last_updated": payload.get("last_updated"),
                        "chunk_id": payload.get("chunk_id")
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch profile chunk for {scheme_name}: {e}")
        return None

if __name__ == "__main__":
    store = QdrantVectorStore(path=":memory:")
    print("QdrantVectorStore initialized in memory mode.")
