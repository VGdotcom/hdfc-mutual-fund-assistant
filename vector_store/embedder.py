import logging
from typing import List
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class BGEEmbedder:
    """
    Lightweight, high-performance BGE embedding generator using FastEmbed.
    Model: BAAI/bge-small-en-v1.5 (384 dimensions).
    """
    MODEL_NAME = "BAAI/bge-small-en-v1.5"
    VECTOR_DIM = 384

    def __init__(self, model_name: str = MODEL_NAME):
        logger.info(f"Initializing BGEEmbedder with model: {model_name}...")
        self.model = TextEmbedding(model_name=model_name)

    def embed_text(self, text: str) -> List[float]:
        """Generates a 384-dimensional embedding vector for a single text string."""
        if not text.strip():
            return [0.0] * self.VECTOR_DIM
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates embedding vectors for a batch of text strings efficiently."""
        if not texts:
            return []
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings_gen = self.model.embed(texts, batch_size=batch_size)
        return [emb.tolist() for emb in embeddings_gen]

if __name__ == "__main__":
    embedder = BGEEmbedder()
    vec = embedder.embed_text("HDFC Small Cap Fund Expense Ratio is 0.75%")
    print(f"Generated vector of dimension: {len(vec)}")
