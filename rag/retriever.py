import logging
from typing import List, Dict, Any, Optional
from vector_store.embedder import BGEEmbedder
from vector_store.qdrant_store import QdrantVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RAGRetriever:
    """
    Handles Top-K semantic similarity search with dynamic query-driven scheme filtering.
    """
    SCHEME_MAPPINGS = {
        "small cap": "HDFC Small Cap Fund Direct Growth",
        "smallcap": "HDFC Small Cap Fund Direct Growth",
        "flexi cap": "HDFC Flexi Cap Fund Direct Plan Growth Option",
        "flexicap": "HDFC Flexi Cap Fund Direct Plan Growth Option",
        "mid cap": "HDFC Mid Cap Fund Direct Growth",
        "midcap": "HDFC Mid Cap Fund Direct Growth",
        "nifty 50": "HDFC Nifty 50 Index Fund Direct Plan Growth",
        "nifty": "HDFC Nifty 50 Index Fund Direct Plan Growth",
        "index fund": "HDFC Nifty 50 Index Fund Direct Plan Growth",
        "gold etf": "HDFC Gold ETF Fund of Fund Direct Plan Growth",
        "gold": "HDFC Gold ETF Fund of Fund Direct Plan Growth"
    }

    def __init__(
        self,
        qdrant_path: str = ".qdrant",
        collection_name: str = "hdfc_funds",
        store: Optional[QdrantVectorStore] = None,
        embedder: Optional[BGEEmbedder] = None
    ):
        self.collection_name = collection_name
        self.store = store or QdrantVectorStore(path=qdrant_path)
        self.embedder = embedder or BGEEmbedder()

    @classmethod
    def extract_scheme_filter(cls, query: str) -> Optional[str]:
        """
        Dynamically detects if the user is asking about a specific HDFC mutual fund scheme.
        If exactly one matching scheme is found, returns its exact scheme_name for Qdrant filtering.
        """
        lower_q = query.lower()
        matched_schemes = set()
        
        for keyword, scheme_name in cls.SCHEME_MAPPINGS.items():
            if keyword in lower_q:
                matched_schemes.add(scheme_name)
                
        if len(matched_schemes) == 1:
            return list(matched_schemes)[0]
        return None

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        force_scheme: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Embeds the query and retrieves the top_k most relevant chunks from Qdrant.
        Applies metadata filtering if a scheme name is specified or dynamically detected.
        """
        detected_scheme = self.extract_scheme_filter(query)
        scheme_filter = detected_scheme or force_scheme
        if scheme_filter:
            lower_s = scheme_filter.lower()
            if "silver" in lower_s:
                scheme_filter = "HDFC Silver ETF FoF Direct Growth"
            elif "gold" in lower_s:
                scheme_filter = "HDFC Gold ETF Fund of Fund Direct Plan Growth"
            elif "small" in lower_s:
                scheme_filter = "HDFC Small Cap Fund Direct Growth"
            elif "large" in lower_s:
                scheme_filter = "HDFC Large Cap Fund Direct Growth"
            elif "mid" in lower_s:
                scheme_filter = "HDFC Mid Cap Fund Direct Growth"
            logger.info(f"Applying metadata filter for scheme: '{scheme_filter}'")
            
        query_vec = self.embedder.embed_text(query)
        results = self.store.search(
            query_embedding=query_vec,
            limit=top_k,
            scheme_name=scheme_filter,
            collection_name=self.collection_name
        )
        logger.info(f"Retrieved {len(results)} chunks for query: \"{query}\"")
        return results

if __name__ == "__main__":
    retriever = RAGRetriever(qdrant_path=":memory:")
    print("RAGRetriever initialized.")
