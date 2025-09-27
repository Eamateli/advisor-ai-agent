from typing import List, Optional, Dict
import hashlib
import json
import redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Cache embeddings in Redis to reduce API costs"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False
            )
            self.ttl = 60 * 60 * 24 * 30  # 30 days
            self.enabled = True
            logger.info("Embedding cache initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis not available, caching disabled: {e}")
            self.redis_client = None
            self.enabled = False
    
    def _generate_cache_key(self, text: str, model: str) -> str:
        """Generate a unique cache key for text + model combination"""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return f"embedding:{model}:{text_hash}"
    
    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding if available"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(text, model)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                embedding = json.loads(cached_data)
                logger.debug(f"Cache HIT for text: {text[:50]}...")
                return embedding
            
            logger.debug(f"Cache MISS for text: {text[:50]}...")
            return None
        
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            return None
    
    def set(self, text: str, model: str, embedding: List[float]):
        """Cache an embedding"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(text, model)
            cached_data = json.dumps(embedding)
            
            self.redis_client.setex(
                cache_key,
                self.ttl,
                cached_data
            )
            
            logger.debug(f"Cached embedding for text: {text[:50]}...")
        
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
    
    def get_batch(self, texts: List[str], model: str) -> Dict[str, Optional[List[float]]]:
        """Get multiple cached embeddings at once"""
        if not self.enabled or not self.redis_client:
            return {text: None for text in texts}
        
        try:
            cache_keys = [self._generate_cache_key(text, model) for text in texts]
            
            pipe = self.redis_client.pipeline()
            for key in cache_keys:
                pipe.get(key)
            cached_values = pipe.execute()
            
            results = {}
            for text, cached_data in zip(texts, cached_values):
                if cached_data:
                    results[text] = json.loads(cached_data)
                else:
                    results[text] = None
            
            hits = sum(1 for v in results.values() if v is not None)
            logger.debug(f"Batch cache: {hits}/{len(texts)} hits")
            
            return results
        
        except Exception as e:
            logger.error(f"Error in batch cache read: {e}")
            return {text: None for text in texts}
    
    def set_batch(self, embeddings: Dict[str, List[float]], model: str):
        """Cache multiple embeddings at once"""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            pipe = self.redis_client.pipeline()
            
            for text, embedding in embeddings.items():
                cache_key = self._generate_cache_key(text, model)
                cached_data = json.dumps(embedding)
                pipe.setex(cache_key, self.ttl, cached_data)
            
            pipe.execute()
            logger.debug(f"Batch cached {len(embeddings)} embeddings")
        
        except Exception as e:
            logger.error(f"Error in batch cache write: {e}")

embedding_cache = EmbeddingCache()