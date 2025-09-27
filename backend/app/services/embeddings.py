from typing import List
from openai import OpenAI
from app.core.config import settings
from app.services.embedding_cache import embedding_cache
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Handles embedding generation using OpenAI with caching"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text with caching"""
        # Check cache first
        cached = embedding_cache.get(text, self.model)
        if cached:
            return cached
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            embedding_cache.set(text, self.model, embedding)
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with caching"""
        # Check cache for all texts
        cache_results = embedding_cache.get_batch(texts, self.model)
        
        # Separate cached and uncached
        uncached_texts = [t for t, emb in cache_results.items() if emb is None]
        
        if not uncached_texts:
            # All cached!
            logger.info(f"All {len(texts)} embeddings retrieved from cache")
            return [cache_results[t] for t in texts]
        
        logger.info(f"Cache hit: {len(texts) - len(uncached_texts)}/{len(texts)}, generating {len(uncached_texts)} new embeddings")
        
        try:
            # Generate embeddings for uncached texts
            response = self.client.embeddings.create(
                model=self.model,
                input=uncached_texts,
                encoding_format="float"
            )
            
            # Extract embeddings
            new_embeddings = {text: data.embedding for text, data in zip(uncached_texts, response.data)}
            
            # Cache new embeddings
            embedding_cache.set_batch(new_embeddings, self.model)
            
            # Combine cached and new embeddings in original order
            result = []
            for text in texts:
                if cache_results[text] is not None:
                    result.append(cache_results[text])
                else:
                    result.append(new_embeddings[text])
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

embedding_service = EmbeddingService()