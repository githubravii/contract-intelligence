from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()